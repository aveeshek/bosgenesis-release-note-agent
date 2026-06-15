import json
import urllib.error
from types import SimpleNamespace

from grna.analyzers.inventory import RepositoryInventoryAnalyzer
from grna.analyzers.readiness import (
    ReadinessAnalyzer,
    analyze_documentation_coverage,
    analyze_security_scan,
)
from grna.config import AppConfig
from grna.llm.readiness_reasoning import (
    READINESS_REASONING_SCHEMA,
    OllamaHttpChatModel,
    build_readiness_reasoning,
)


def test_documentation_coverage_counts_python_docstrings(tmp_path) -> None:
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    (source_dir / "app.py").write_text(
        '"""module docs"""\n\n'
        "class Service:\n"
        '    """service docs"""\n'
        "    def run(self):\n"
        '        """run docs"""\n'
        "        return True\n\n"
        "def documented():\n"
        '    """function docs"""\n'
        "    return True\n\n"
        "def missing():\n"
        "    return False\n",
        encoding="utf-8",
    )
    inventory = RepositoryInventoryAnalyzer().analyze(tmp_path)

    coverage = analyze_documentation_coverage(tmp_path, inventory)

    assert coverage.documentable_symbols == 5
    assert coverage.documented_symbols == 4
    assert coverage.coverage_percent == 80.0
    assert coverage.evidence_paths == ("src/app.py",)


def test_security_scan_reports_sanitized_findings_and_controls(tmp_path) -> None:
    source_dir = tmp_path / "src"
    workflow_dir = tmp_path / ".github" / "workflows"
    source_dir.mkdir()
    workflow_dir.mkdir(parents=True)
    (source_dir / "danger.py").write_text(
        "import subprocess\n"
        "TOKEN = 'super-secret-token-value'\n"
        "subprocess.run(cmd, shell=True)\n",
        encoding="utf-8",
    )
    (workflow_dir / "codeql.yml").write_text(
        "uses: github/codeql-action/init@v3\n",
        encoding="utf-8",
    )
    (tmp_path / "SECURITY.md").write_text("# Security\n", encoding="utf-8")
    inventory = RepositoryInventoryAnalyzer().analyze(tmp_path)

    scan = analyze_security_scan(tmp_path, inventory)

    assert scan.scanned_files == 2
    assert "CodeQL workflow" in scan.controls
    assert "SECURITY.md" in scan.controls
    assert {finding.rule_id for finding in scan.findings} == {
        "secret.assignment",
        "danger.shell_true",
    }
    assert all(
        "super-secret-token-value" not in finding.redacted_snippet
        for finding in scan.findings
    )
    assert scan.score < 4.0


def test_readiness_analyzer_uses_real_docs_and_safety_scores(tmp_path) -> None:
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    (source_dir / "service.py").write_text(
        "class Service:\n"
        '    """service docs"""\n'
        "    def run(self):\n"
        "        return True\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    inventory = RepositoryInventoryAnalyzer().analyze(tmp_path)

    result = ReadinessAnalyzer(AppConfig()).analyze(
        tmp_path,
        inventory,
        technology=SimpleNamespace(findings=()),
        documentation=SimpleNamespace(documents=(object(),)),
        interfaces=SimpleNamespace(interfaces=(SimpleNamespace(interface_type="http_route"),)),
        test_coverage=SimpleNamespace(test_sources=()),
    )
    scores = {score.dimension: score for score in result.scores}

    assert scores["Documentation coverage"].score != 3.8
    assert scores["Security scan"].score != 3.8
    assert result.llm_reasoning.status == "disabled"


class _FakeModel:
    def invoke(self, prompt: str) -> str:
        assert "Deterministic readiness evidence" in prompt
        return """
        ```json
        {
          "findings": [
            {
              "dimension": "Documentation coverage",
              "suggested_score": 4.5,
              "confidence": 0.91,
              "rationale": "Docstrings cover the main service surface.",
              "evidence_refs": ["src/service.py"]
            }
          ],
          "warnings": []
        }
        ```
        """


class _RepairableFakeModel:
    def __init__(self) -> None:
        self.calls = 0

    def invoke(self, prompt: str) -> str:
        self.calls += 1
        if self.calls == 1:
            return "Here is the answer: not-json"
        assert "previous readiness response was invalid JSON" in prompt
        return (
            '{"findings":[{"dimension":"Security scan","suggested_score":3.4,'
            '"confidence":0.92,"rationale":"No high severity findings were present.",'
            '"evidence_refs":[".github/workflows/test.yml","missing/path.py"]}],'
            '"warnings":[]}'
        )


def test_readiness_reasoning_accepts_bounded_structured_gemma_output() -> None:
    result = build_readiness_reasoning(
        config=AppConfig(enable_llm_reasoning=True, llm_minimum_confidence=0.85),
        deterministic_summary={"scores": []},
        model=_FakeModel(),
    )

    assert result.status == "generated"
    assert result.findings[0].dimension == "Documentation coverage"
    assert result.findings[0].suggested_score == 4.5


def test_readiness_reasoning_repairs_invalid_json_and_filters_evidence_refs() -> None:
    model = _RepairableFakeModel()

    result = build_readiness_reasoning(
        config=AppConfig(enable_llm_reasoning=True, llm_minimum_confidence=0.85),
        deterministic_summary={
            "security_scan": {
                "evidence_paths": [".github/workflows/test.yml"],
            }
        },
        model=model,
    )

    assert model.calls == 2
    assert result.status == "generated"
    assert result.warnings == ("llm_readiness_reasoning_repaired_structured_output",)
    assert result.findings[0].dimension == "Security scan"
    assert result.findings[0].evidence_refs == (".github/workflows/test.yml",)


class _FakeHttpResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def test_ollama_http_model_requests_schema_json_mode(monkeypatch) -> None:
    captured: list[dict] = []

    def fake_urlopen(request, timeout):
        captured.append(json.loads(request.data.decode("utf-8")))
        return _FakeHttpResponse(
            {
                "response": json.dumps(
                    {
                        "findings": [
                            {
                                "dimension": "Security scan",
                                "suggested_score": 3.4,
                                "confidence": 0.9,
                                "rationale": "No high severity findings were detected.",
                                "evidence_refs": ["security_scan"],
                            }
                        ],
                        "warnings": [],
                    }
                )
            }
        )

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    content = OllamaHttpChatModel(
        model="gemma4:26b",
        base_url="http://ollama:11434",
    ).invoke("Return JSON")

    assert json.loads(content)["findings"][0]["dimension"] == "Security scan"
    assert captured[0]["format"] == READINESS_REASONING_SCHEMA
    assert captured[0]["options"]["temperature"] == 0.2


def test_ollama_http_model_falls_back_to_plain_json_mode_on_schema_rejection(
    monkeypatch,
) -> None:
    formats: list[object] = []

    def fake_urlopen(request, timeout):
        payload = json.loads(request.data.decode("utf-8"))
        formats.append(payload["format"])
        if len(formats) == 1:
            raise urllib.error.HTTPError(
                url="http://ollama:11434/api/generate",
                code=400,
                msg="unsupported format schema",
                hdrs=None,
                fp=None,
            )
        return _FakeHttpResponse({"response": '{"findings":[],"warnings":[]}'})

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    content = OllamaHttpChatModel(
        model="gemma4:26b",
        base_url="http://ollama:11434",
    ).invoke("Return JSON")

    assert json.loads(content) == {"findings": [], "warnings": []}
    assert formats == [READINESS_REASONING_SCHEMA, "json"]

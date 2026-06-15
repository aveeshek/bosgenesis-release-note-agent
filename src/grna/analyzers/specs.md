# Analyzers Module Specification

## Intent

Convert repository files, documentation, configuration, tests, coverage, and Git history into normalized evidence-backed analytics.

## Role

- Define the analyzer interface and execution contract.
- Provide analyzers for inventory, technology, intent, features, interfaces, code, tests, coverage, commits, specs, and dependencies.
- Return structured findings with confidence and evidence references.
- Separate implemented evidence from inferred conclusions.

## Inputs

- Analyzer context containing job ID, repository path, file inventory, Git metadata, config, and storage adapters.
- Evidence items produced by previous analyzer stages.
- Optional LLM summarization services through guarded interfaces.

## Outputs

- Analyzer result objects.
- Evidence items.
- Warnings and known gaps.
- Analytics fragments for the final analytics bundle.

## Expected Analyzer Types

- Inventory analyzer implemented in `inventory.py`.
- Technology analyzer implemented in `technology.py`.
- Intent analyzer.
- Feature analyzer.
- Interface analyzer implemented in `interfaces.py`.
- Code analyzer implemented in `code_structure.py`.
- Test and coverage analyzer implemented in `test_coverage.py`.
- Commit analyzer implemented in `commits.py`.
- Spec and documentation analyzer implemented in `documentation.py`.
- Release readiness analyzer implemented in `readiness.py`.
- Dependency analyzer.

## Design Rules

- Each analyzer must be independently runnable and testable.
- Analyzers must not execute scanned repository code.
- Findings must include confidence and evidence paths where possible.
- Unsupported languages or missing evidence must produce gaps, not fabricated conclusions.
- Analyzer failures should be isolated when possible so the job can continue with partial results.

## Implemented Inventory Analyzer Contract

- Input: a resolved repository directory path.
- Output: `RepositoryInventory` containing deterministic `InventoryFile` records sorted by repository-relative path.
- Skips: `.git`, virtual environments, dependency folders, cache folders, and generated build outputs.
- Categories: `source`, `test`, `docs`, `config`, `ci`, `deployment`, `coverage`, `binary`, and `other`.
- Important file detection includes README, SPEC, HLD, LLD, Dockerfile, Helm chart/value files, Kubernetes/deployment manifests, and coverage reports.
- Summary fields include total file count, total size, per-category counts, skipped directories, and important file paths.
- The analyzer computes SHA-256 checksums for included files and never imports or executes scanned repository code.

## Implemented Technology Analyzer Contract

- Input: a resolved repository directory path plus `RepositoryInventory`.
- Output: `TechnologyInventory` with findings, unknowns, and per-language file counts.
- Language detection is extension-based and produces file-count details.
- Python packaging detection reads `pyproject.toml` and `requirements.txt`.
- Tool/framework detection covers FastAPI, MCP, Pydantic, pytest, Ruff, Docker, Helm, Kubernetes, and GitHub Actions.
- Each `TechnologyFinding` includes category, confidence, evidence paths, and available evidence IDs.
- Repositories with no recognized source extensions emit an explicit `Unknown language` finding instead of silently omitting language data.

## Implemented Documentation Analyzer Contract

- Input: a resolved repository directory path plus `RepositoryInventory`.
- Output: `DocumentationInventory` with detected documents, project intent, and documentation gaps.
- Detects README, SPEC, HLD, LLD, docs folder files, ADRs, and module-level `specs.md`.
- Extracts Markdown and simple RST headings in source order.
- Summaries come from the first meaningful prose paragraph and are kept concise.
- Project intent is marked `stated` when sourced from README/SPEC prose, `inferred` when only titles are available, and `unavailable` when no readable documentation exists.
- Missing README, SPEC, HLD, LLD, ADR, and module-level specs are reported as explicit gaps.

## Implemented Commit Analyzer Contract

- Input: a Git repository path plus optional `from_ref`, `to_ref`, and max commit count.
- Output: `CommitAnalysis` with commit records, authors, date range, changed files, category counts, hotspots, and risky areas.
- Reads commit history with Git CLI only; it does not execute repository code.
- Captures SHA, author, author email, authored timestamp, subject, changed files, and tags pointing at each commit.
- Categorizes conventional commits and limited keyword heuristics; uncategorized commits remain explicitly `uncategorized`.
- Hotspots and risky areas are derived from changed-file frequency and high-sensitivity paths such as config, deployment, CI, and source directories.

## Implemented Code Structure Analyzer Contract

- Input: a resolved repository directory path plus `RepositoryInventory`.
- Output: `CodeStructureAnalysis` with Python module summaries, directory summaries, entrypoints, and partial-analysis gaps.
- Parses Python files using `ast` and never imports scanned modules.
- Extracts module name, lines of code, classes, functions, imports, public surfaces, and entrypoint markers.
- Detects Python `__main__`, FastAPI app assignment, and common CLI decorator entrypoints when evidence exists.
- Unsupported source extensions are reported as explicit gaps instead of blocking Python analysis.

## Implemented Interface Analyzer Contract

- Input: a resolved repository directory path plus `RepositoryInventory`.
- Output: `InterfaceAnalysis` with interface findings and recommendations.
- Detects FastAPI-style route decorators, CLI command decorators, MCP tool decorators, environment-variable reads, config files, and generated artifact/report path literals.
- Each finding includes interface type, direction, evidence path, confidence, and available evidence ID.
- Missing explicit route, CLI, MCP, or environment contracts are reported as recommendations.
- The analyzer remains read-only and uses AST/string scanning only.

## Implemented Test and Coverage Analyzer Contract

- Input: a resolved repository directory path plus `RepositoryInventory`.
- Output: `TestCoverageAnalysis` with test source files, parsed test reports, parsed coverage reports, and explicit gaps.
- Detects test source files from the inventory's `test` category.
- Parses pytest/JUnit-style XML test reports when report files exist.
- Parses `coverage.xml`/Cobertura-style XML, `lcov.info`, and JaCoCo XML where practical.
- Coverage is reported only from report evidence; the analyzer does not infer coverage from test source presence.
- Missing test source, test report, and coverage report evidence are listed as explicit gaps.

## Implemented Release Readiness Analyzer Contract

- Input: a resolved repository directory path, `RepositoryInventory`, and the technology, documentation, interface, and test analyzer outputs.
- Output: `ReadinessAnalysis` with report-ready dimension scores, documentation coverage details, lightweight security scan details, optional LLM reasoning metadata, gaps, and warnings.
- Documentation coverage is evidence-driven: Python files are parsed with `ast` for module/class/function docstrings; JavaDoc/TSDoc/KDoc/PHPDoc-style comments are detected for supported non-Python source files using read-only text scanning.
- Security scanning is intentionally lightweight and read-only. It detects sanitized secret-like patterns, private key markers, unsafe shell execution, dynamic code execution, insecure TLS flags, `curl | sh`, broad permission changes, and unsafe pickle deserialization.
- Security findings must redact suspected secret values and include rule ID, severity, path, line, description, and a redacted snippet.
- Security posture also records basic controls such as `SECURITY.md`, Dependabot, CodeQL workflows, CI workflows, and dependency lockfiles.
- Optional Gemma/Ollama reasoning may provide advisory score suggestions for documentation coverage and security scan only; deterministic scores remain the primary source and LLM adjustment is bounded.

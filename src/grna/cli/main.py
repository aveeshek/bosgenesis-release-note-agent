"""Command-line interface for local release-note workflows."""

from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path

from grna.config import get_config
from grna.runtime import (
    GenerateNoteRequest,
    ScanPipelineRequest,
    analytics_from_file,
    evidence_from_file,
    run_end_to_end_scan,
    write_report_files,
)
from grna.runtime.pipeline import error_code, error_message
from grna.storage.local import LocalArtifactStore, LocalJsonJobStore


def main(argv: list[str] | None = None) -> int:
    """Run the CLI application."""

    parser = _build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "handler"):
        parser.print_help()
        return 2
    try:
        payload = args.handler(args)
    except Exception as exc:  # pragma: no cover - command-level behavior is tested.
        _emit_error(exc, json_output=getattr(args, "json_output", False))
        return 1
    _emit(payload, json_output=args.json_output)
    return 0


def _build_parser() -> ArgumentParser:
    parser = ArgumentParser(
        prog="grna",
        description="BOS Genesis Release Note Agent command-line interface.",
    )
    subcommands = parser.add_subparsers(dest="command")

    scan_parser = subcommands.add_parser("scan", help="Run a local end-to-end scan.")
    scan_parser.add_argument("repo_url", help="Public GitHub repository URL.")
    scan_parser.add_argument("--branch", default=None, help="Branch to scan.")
    scan_parser.add_argument("--tag", default=None, help="Tag to scan.")
    scan_parser.add_argument("--commit-sha", default=None, help="Commit SHA to scan.")
    scan_parser.add_argument(
        "--release-name",
        default=None,
        help="Release name shown in generated reports.",
    )
    scan_parser.add_argument(
        "--local-repo",
        type=Path,
        default=None,
        help="Clone a local Git repository fixture instead of the public URL.",
    )
    _add_output_format_option(scan_parser)
    _add_json_option(scan_parser)
    scan_parser.set_defaults(handler=_handle_scan)

    status_parser = subcommands.add_parser("status", help="Show local job status.")
    status_parser.add_argument("job_id", help="Local job ID.")
    _add_json_option(status_parser)
    status_parser.set_defaults(handler=_handle_status)

    generate_parser = subcommands.add_parser(
        "generate-note",
        help="Generate release-note artifacts from local analytics JSON.",
    )
    generate_parser.add_argument(
        "analytics_input",
        type=Path,
        help="Analytics JSON file produced by the analyzer pipeline.",
    )
    generate_parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path("release-note-output"),
        help="Directory where generated report files are written.",
    )
    generate_parser.add_argument("--title", default="Repository Release Notes")
    generate_parser.add_argument("--release-name", default="local")
    generate_parser.add_argument("--repository", default="local")
    generate_parser.add_argument(
        "--evidence",
        dest="evidence_input",
        type=Path,
        default=None,
        help="Optional evidence JSON file for appendix enrichment.",
    )
    _add_output_format_option(generate_parser)
    _add_json_option(generate_parser)
    generate_parser.set_defaults(handler=_handle_generate_note)

    return parser


def _add_output_format_option(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--format",
        "-f",
        dest="output_formats",
        action="append",
        default=None,
        choices=("markdown", "html", "pdf"),
        help="Output format to generate. Repeat for multiple formats.",
    )


def _add_json_option(parser: ArgumentParser) -> None:
    parser.add_argument(
        "--json",
        dest="json_output",
        action="store_true",
        help="Emit machine-readable JSON.",
    )


def _handle_scan(args: Namespace) -> dict:
    local_repo = args.local_repo.resolve() if args.local_repo else None
    if local_repo is not None and not local_repo.is_dir():
        raise ValueError(f"local repository does not exist or is not a directory: {local_repo}")
    return run_end_to_end_scan(
        ScanPipelineRequest(
            repo_url=args.repo_url,
            branch=args.branch,
            tag=args.tag,
            commit_sha=args.commit_sha,
            release_name=args.release_name,
            local_repo=local_repo,
            output_formats=tuple(args.output_formats or ["markdown", "html"]),
            runtime="cli",
        )
    )


def _handle_status(args: Namespace) -> dict:
    config = get_config()
    job_store = LocalJsonJobStore(config.job_root)
    artifact_store = LocalArtifactStore(config.artifact_root)
    job = job_store.get(args.job_id)
    return {
        "job": job.to_dict(),
        "artifacts": [
            artifact.to_dict()
            for artifact in artifact_store.list_artifacts(args.job_id)
        ],
    }


def _handle_generate_note(args: Namespace) -> dict:
    analytics_input = args.analytics_input.resolve()
    if not analytics_input.is_file():
        raise ValueError(f"analytics input does not exist or is not a file: {analytics_input}")
    evidence_input = args.evidence_input.resolve() if args.evidence_input else None
    if evidence_input is not None and not evidence_input.is_file():
        raise ValueError(f"evidence input does not exist or is not a file: {evidence_input}")

    analytics = analytics_from_file(analytics_input)
    evidence = evidence_from_file(evidence_input) if evidence_input else None
    output_dir = args.output_dir.resolve()
    written = write_report_files(
        GenerateNoteRequest(
            analytics=analytics,
            evidence=evidence,
            output_dir=output_dir,
            title=args.title,
            release_name=args.release_name,
            repository=args.repository,
            output_formats=tuple(args.output_formats or ["markdown", "html"]),
        )
    )
    return {
        "job_id": analytics.job_id,
        "output_dir": str(output_dir),
        "files": [str(path) for path in written],
    }


def _emit(payload: dict, *, json_output: bool) -> None:
    if json_output:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return
    if "job_id" in payload and "status" in payload:
        print(f"Job {payload['job_id']} {payload['status']} at stage {payload['stage']}.")
        for artifact in payload.get("artifacts", []):
            print(f"- {artifact['artifact_type']}: {artifact['path']}")
        return
    if "job" in payload:
        job = payload["job"]
        print(f"Job {job['job_id']} {job['status']} at stage {job['stage']}.")
        for artifact in payload.get("artifacts", []):
            print(f"- {artifact['artifact_type']}: {artifact['path']}")
        return
    print(json.dumps(payload, indent=2, sort_keys=True))


def _emit_error(exc: Exception, *, json_output: bool) -> None:
    payload = {
        "error_code": error_code(exc),
        "message": error_message(exc),
    }
    if json_output:
        print(json.dumps(payload, indent=2, sort_keys=True), file=sys.stderr)
    else:
        print(f"{payload['error_code']}: {payload['message']}", file=sys.stderr)


if __name__ == "__main__":
    sys.exit(main())

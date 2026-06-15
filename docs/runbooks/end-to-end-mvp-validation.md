# End-to-End MVP Validation

## Intent

Capture the Task T-024 validation run proving that the CLI can take a GitHub
repository URL, run the local MVP analysis pipeline, and generate human-readable
release-note artifacts.

## Validation Command

```powershell
$env:PYTHONPATH='src'
python -m grna.cli.main scan https://github.com/aveeshek/bosgenesis-mop-creation-agent `
  --local-repo data/workspaces/manual_bosgenesis_mop_creation_agent/repo `
  --release-name v0.1.0 `
  --format markdown `
  --format html `
  --format pdf `
  --json
```

The public GitHub URL is preserved as the report repository identity. The
`--local-repo` option was used for this validation because direct public clone
from the current Windows sandbox failed with `getaddrinfo() thread failed to
start`. The local repository used for the run is a clone of the same public
repository.

## Result

- Job ID: `scan_8a81dd990fb64f91a252f779936b9376`
- Status: `completed`
- Resolved commit SHA: `233631a6e7f9705b082e4253c26995088f4fcf4b`
- Evidence references in analytics bundle: `198`
- Analyzer warnings: `0`

## Generated Artifacts

- `data/artifacts/scan_8a81dd990fb64f91a252f779936b9376/analytics.json`
- `data/artifacts/scan_8a81dd990fb64f91a252f779936b9376/evidence.json`
- `data/artifacts/scan_8a81dd990fb64f91a252f779936b9376/fetch_metadata.json`
- `data/artifacts/scan_8a81dd990fb64f91a252f779936b9376/release-note.md`
- `data/artifacts/scan_8a81dd990fb64f91a252f779936b9376/release-note.html`
- `data/artifacts/scan_8a81dd990fb64f91a252f779936b9376/release-note.pdf`

The PDF artifact was verified to start with `%PDF-` and was generated from the
styled HTML report path.

## Evidence Review

The generated Markdown and HTML reports include evidence IDs for stated project
intent and technology findings. Missing evidence is reported explicitly rather
than hidden.

Observed gaps from the analytics bundle:

- Missing HLD documentation.
- Missing LLD documentation.
- No ADR documentation detected.
- No coverage report evidence detected.
- No module-level `specs.md` documentation detected.
- No pytest or JUnit test report evidence detected.
- Unsupported source extension for structure parsing: `.sh`.


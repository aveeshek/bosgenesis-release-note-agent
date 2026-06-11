# Utils Module Specification

## Intent

Provide small shared utilities that are stable, dependency-light, and safe to reuse across modules.

## Role

- Centralize path safety helpers.
- Provide hashing and checksum helpers.
- Provide Markdown and text helpers.
- Provide shell/subprocess wrappers if needed for controlled Git or rendering commands.
- Provide redaction helpers when not owned by a more specific module.

## Inputs

- Paths, text content, byte streams, command arguments, and structured values from other modules.

## Outputs

- Normalized paths.
- Hashes and checksums.
- Redacted text.
- Safe command results.
- Markdown-safe strings.

## Design Rules

- Utilities must remain small and generic.
- Do not hide business logic in utilities.
- Shell helpers must avoid string-built commands where possible.
- Path helpers must prevent traversal outside configured roots.
- Utility functions should be easy to unit test.


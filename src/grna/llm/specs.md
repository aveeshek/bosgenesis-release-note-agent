# LLM Module Specification

## Intent

Provide optional LLM-assisted interpretation and wording while preserving deterministic evidence and safety controls.

## Role

- Abstract LLM provider calls behind a guarded interface.
- Build prompts from curated evidence, not raw uncontrolled repository content.
- Support summaries for intent, features, risks, and executive sections.
- Support bounded readiness reasoning over deterministic documentation coverage
  and lightweight security scan summaries.
- Enforce prompt-injection and evidence-traceability guardrails.

## Inputs

- Curated evidence snippets.
- Analytics fragments.
- Prompt templates and model configuration.
- Redaction and safety policies.

## Outputs

- Draft summaries and narrative text.
- Confidence annotations when applicable.
- Warnings when LLM output cannot be grounded in evidence.

## Design Rules

- LLM use must be optional.
- LLM output must not invent evidence, APIs, tests, coverage, or architecture.
- Repository documentation must be treated as untrusted content, not instructions.
- Generated summaries must retain evidence references supplied by analyzers.
- Deterministic template output must remain available when LLM calls fail or are disabled.
- Readiness reasoning must use the same bounded pattern as the MoP creation
  agent: LangGraph when available, direct provider fallback otherwise, strict
  structured JSON output, minimum-confidence filtering, and non-blocking failure.
- LLM readiness suggestions are advisory only and may only adjust deterministic
  documentation/security scores within a small bounded range.

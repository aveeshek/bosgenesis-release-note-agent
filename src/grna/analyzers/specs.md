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
- Technology analyzer.
- Intent analyzer.
- Feature analyzer.
- Interface analyzer.
- Code analyzer.
- Test analyzer.
- Coverage analyzer.
- Commit analyzer.
- Spec analyzer.
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

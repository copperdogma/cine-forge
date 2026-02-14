# AGENTS.md

This file is the project-wide source of truth for agent behavior and engineering principles. It serves as both a core directive and a living memory for AI agents working on this codebase.

## Core Agent Mandates

- **Security First**: NEVER stage or commit secrets, API keys, or sensitive credentials.
- **Permissioned Actions**: NEVER run `git commit`, `git push`, or modify remotes without explicit user permission.
- **Verify, Don't Assume**: NEVER assume a library is available or a file has a specific content. Use `read_file` and dependency checks (`package.json`, `pyproject.toml`) to ground your work.
- **Immutability**: Versioned artifacts are immutable. NEVER mutate an existing version in place; always produce a new version with incremented metadata.
- **AI-First Engineering**: Prefer roles, prompts, and structured artifacts over rigid hard-coded business rules. Architecture should facilitate AI reasoning.
- **Definition of Done**: A task is complete ONLY when:
  1. Relevant tests pass (`make test-unit` minimum).
  2. Artifacts are produced and manually inspected for semantic correctness.
  3. Schema validation passes.
  4. The active story's work log is updated with evidence and next actions.

## General Agent Engineering Principles

- **Semantic Quality over Structural Validity**: A JSON that passes a schema but contains "UNKNOWN" or placeholder data is a failure. Assert semantic quality predicates in tests.
- **Boundary Awareness**: Code that works in a unit test can fail in a long-running service (due to state, cache, or import-time definitions). Validate through the service layer or API boundary.
- **Process Lifecycle**: Restart long-running backend/API processes after changing schemas or core logic. Hot-reloading is a tool, but a clean restart is the source of truth.
- **Regression Fixes start with Fixtures**: When a real-world run fails, capture the failing input as a deterministic test fixture BEFORE implementing the fix.
- **Conservative Heuristics**: When building classifiers (screenplay vs. prose), use weighted evidence and confidence scores. Favor "needs_review" over silent incorrectness.
- **Lineage Tracking**: Every transformation must record its upstream sources. Data without provenance is noise.
- **Context Traceability**: Every run must persist its full execution context (e.g., `runtime_params`, recipe fingerprints) in its core artifacts (`run_state.json`). Never leave the operator guessing which model or flag produced an outcome.

## Project Context (CineForge)

- **CineForge** is a film reasoning and production pipeline using immutable artifacts.
- **Core Stack**: Python 3.12+, Pydantic (schemas), YAML (recipes), React (UI).
- **Core Pattern**: Driver orchestrates Modules which consume/produce versioned Artifacts stored in an ArtifactStore.

## Operational Guide

### Common Driver Commands
- **Validate only**: `PYTHONPATH=src python -m cine_forge.driver --recipe configs/recipes/recipe-test-echo.yaml --dry-run`
- **Execute recipe**: `PYTHONPATH=src python -m cine_forge.driver --recipe configs/recipes/recipe-test-echo.yaml --run-id test-001`
- **Resume from stage**: `PYTHONPATH=src python -m cine_forge.driver --recipe configs/recipes/recipe-test-echo.yaml --start-from echo --run-id test-002`

### Deep Research
For multi-model research tasks, use the `deep-research` CLI tool.
- Workflow: `deep-research init <topic>` → write `research-prompt.md` → `deep-research run` → `deep-research format` → `deep-research final`
- Outputs go under `docs/research/`.

### Repo Map
- `src/cine_forge/driver/`: Orchestration runtime.
- `src/cine_forge/modules/`: Pipeline modules by stage.
- `src/cine_forge/schemas/`: Pydantic artifact schemas.
- `src/cine_forge/artifacts/`: Storage, versioning, and dependency graph.
- `src/cine_forge/operator_console/`: Backend API for the UI.
- `ui/operator-console-lite/`: React frontend.

## Agent Memory: AI Self-Improvement Log

Treat this section as a living memory. Entry format: `YYYY-MM-DD — short title`: summary plus explanation including file paths.

### Effective Patterns
- 2026-02-11 — Story-first implementation: Implement stories in dependency order and validate each with focused smoke checks.
- 2026-02-12 — FDX-first screenplay intake: detect Final Draft XML early and normalize to Fountain before AI routing.
- 2026-02-12 — Multi-output module validation: Resolve schema per artifact by explicit `schema_name` to avoid false failures.
- 2026-02-13 — Reflow tokenized PDF text: Reconstruct boundaries before classification to keep heuristics stable.
- 2026-02-13 — Cast-quality filters: Remove pronouns and derivative noise before ranking characters.
- 2026-02-14 — Cross-recipe artifact reuse via `store_inputs`: Downstream recipes declare `store_inputs: {input_key: artifact_type}` to resolve inputs from the artifact store instead of re-executing upstream stages. Validated against registered schemas, rejects stale/unhealthy artifacts, and included in stage fingerprints for cache correctness (`src/cine_forge/driver/recipe.py`, `src/cine_forge/driver/engine.py`, `configs/recipes/recipe-world-building.yaml`).

### Known Pitfalls
- 2026-02-11 — Hidden schema drift: adding output fields without schema updates can silently drop data.
- 2026-02-12 — Runtime-only inputs bypass cache: Include CLI params in stage fingerprints or reuse returns stale data.
- 2026-02-12 — CORS/Vite Port shifts: Allow localhost across local ports by regex to prevent "Failed to fetch".
- 2026-02-13 — Schema-valid placeholder outputs: Structurally valid but useless data must fail semantic quality gates.
- 2026-02-13 — Stale processes: Long-running API servers must be restarted after Pydantic schema changes.
- 2026-02-13 — Directory depth fragility: Discovery logic assuming fixed depth (e.g. `artifacts/{type}/{id}/`) fails on nested/folder-based types.
- 2026-02-13 — Project Directory Pollution: Reusing the same project directory for manual testing and user runs can lead to "ghost" artifacts appearing if cache reuse is not explicitly invalidated after recipe or input changes.
- 2026-02-13 — Deceptive "Zero-Second" Success: Mock models finish in microseconds, making a run appear to "pass" instantly while producing only stubs. Always verify `cost_usd` or `runtime_params` before declaring a high-fidelity success.

### Lessons Learned
- 2026-02-12 — Build the pipeline spine before AI modules: Land immutable store and graph first.
- 2026-02-13 — Patch shared dependencies in integration tests: Monkeypatching `pypdf` is more reliable than module-local helpers.
- 2026-02-13 — Validate the Service Layer: Passing a module test does not guarantee the UI can see or run it. Test through the `OperatorConsoleService` boundary.
- 2026-02-13 — Prefer Dynamic Discovery: UI services should scan folders for recipes/actions rather than hardcoding paths.
- 2026-02-13 — Ensure Cache Invalidation across Recipe Changes: When moving from a partial recipe (MVP) to a broader one (World Building) in the same project folder, verify that upstream artifacts are either explicitly forced to rerun or are strictly compatible with the new pipeline's expectations.

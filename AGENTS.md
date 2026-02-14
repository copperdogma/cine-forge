# AGENTS.md

This file is the project-wide source of truth for agent behavior in CineForge.

## Prime Directives

- Do not run `git commit`, `git push`, or modify remotes unless the user explicitly asks.
- Do not add, modify, or rely on GitHub Actions CI workflows unless the user explicitly requests it.
- This is an AI-first system: prefer prompt/role/artifact thinking over ad-hoc business rules.
- Immutability is mandatory: never mutate existing artifact versions in place.
- Inspect outputs, not only logs: correctness requires reviewing produced artifacts.

## Definition of Done

A task is not complete until all applicable items are true:

1. Relevant tests pass (`make test-unit` at minimum).
2. If artifacts are produced, artifact files exist and are manually inspected.
3. Schema validation passes for produced artifacts.
4. The active story's work log is updated with evidence and next actions.

## AI Self-Improvement Protocol (Critical)

Treat this file as a living memory. Update it when you learn.

- When you stumble, add an entry under `## Lessons Learned`.
- When you find a reliable technique, add it under `## Effective Patterns`.
- When you make a mistake, add it under `## Known Pitfalls` with symptom and correction.
- When a new repo convention emerges, document it under `## Project Conventions`.

Entry format:

- `YYYY-MM-DD — short title`: one-line summary plus a short explanation including file paths.

## Project Context

- CineForge is a film reasoning and production pipeline with immutable artifacts.
- Core stack: Python 3.12+, Pydantic schemas, YAML recipes, AI-driven module processing.
- Product specification: `docs/spec.md`
- Story plan and execution queue: `docs/stories.md`

## Architecture Overview

- Driver orchestrates modules from recipes.
- Modules consume and produce immutable, versioned artifacts.
- Artifact store tracks lineage, metadata, and dependency health.
- Roles represent AI personas with permissions/review responsibilities.
- Human interaction supports approve/reject, creative sessions, and direct edits.

## Pipeline Foundation Architecture (Story 002)

- `src/cine_forge/schemas/models.py` defines `ArtifactRef`, `ArtifactMetadata`, `ArtifactHealth`, `CostRecord`, and `Artifact`.
- `src/cine_forge/schemas/registry.py` provides schema registration, structured validation errors, and compatibility checks.
- `src/cine_forge/artifacts/store.py` persists immutable versioned snapshots and supports `list_versions`/`diff_versions`.
- `src/cine_forge/artifacts/graph.py` tracks upstream/downstream artifact dependencies and layer-1 stale propagation.
- `src/cine_forge/driver/` handles module discovery, recipe validation/toposort, stage execution, run state, and event logging.

## Common Driver Commands

- Validate only: `PYTHONPATH=src python -m cine_forge.driver --recipe configs/recipes/recipe-test-echo.yaml --dry-run`
- Execute recipe: `PYTHONPATH=src python -m cine_forge.driver --recipe configs/recipes/recipe-test-echo.yaml --run-id test-001`
- Resume from stage: `PYTHONPATH=src python -m cine_forge.driver --recipe configs/recipes/recipe-test-echo.yaml --start-from echo --run-id test-002`
- Mark instrumented run: `PYTHONPATH=src python -m cine_forge.driver --recipe configs/recipes/recipe-test-echo.yaml --instrument`

## Repo Map

- `src/cine_forge/driver/`: orchestration runtime
- `src/cine_forge/modules/`: pipeline modules by stage
- `src/cine_forge/schemas/`: Pydantic artifact schemas
- `src/cine_forge/artifacts/`: artifact storage/versioning/dependency machinery
- `src/cine_forge/roles/`: role definitions and prompt assets
- `configs/recipes/`: YAML pipeline recipes
- `tests/`: unit, integration, smoke test suites
- `skills/`: cross-agent skill definitions

## Development Workflow

- Use TDD where practical; at minimum, add/adjust tests with implementation.
- Prefer small, composable modules with explicit schema IO contracts.
- Keep recipes declarative; modules should be referenced by module id.
- Run `make test-unit` and `make lint` before declaring completion.
- Update active story files with acceptance progress and work notes.
- For UI work, manual browser verification is required before completion: interact with the real app (not only tests), validate desktop and mobile layouts, confirm key flows work end-to-end, and capture visual evidence (screenshots + brief notes) in the active story work log.

## Cross-Agent Notes

- Root `AGENTS.md` is the shared behavior contract across agents.
- Subdirectory `AGENTS.md` files are used for scoped guidance.
- Cursor and Codex read `AGENTS.md` natively.
- Claude Code should load this file through `CLAUDE.md` using `@AGENTS.md`.
- `.cursor/rules/` may be used only for Cursor-specific activation behavior not expressible here.
- `.codex/rules/` is execution policy only (allow/prompt/forbid), not behavior guidance.
- Skills in `skills/` are cross-platform and preferred for recurring workflows.

## Project Conventions

- Use `src/` layout to avoid accidental local-import behavior.
- Name module directories as `src/cine_forge/modules/{stage}/{module_id}/`.
- Keep artifact metadata explicit (intent, rationale, confidence, lineage, cost data).
- Keep generated outputs under `output/` and never commit them.

## Effective Patterns

- 2026-02-11 — Story-first implementation: Implement stories in dependency order and validate each with focused smoke checks.
- 2026-02-12 — FDX-first screenplay intake: detect Final Draft XML early and normalize to Fountain before AI routing to keep parser validation deterministic (`src/cine_forge/ai/fdx.py`, `src/cine_forge/modules/ingest/script_normalize_v1/main.py`).
- 2026-02-12 — Live AI tests must be cost-gated: keep real-model integration coverage behind explicit env toggles (`CINE_FORGE_LIVE_TESTS`, `OPENAI_API_KEY`) so default CI/local runs remain deterministic and free (`tests/integration/test_script_normalize_integration.py`).
- 2026-02-12 — Interop should include ingest, not just transform: when adding format interoperability (e.g., FDX), update source-format schema literals and ingest module support so integration tests can exercise true file-path intake (`src/cine_forge/schemas/models.py`, `src/cine_forge/modules/ingest/story_ingest_v1/main.py`).
- 2026-02-12 — Multi-output module validation should resolve schema per artifact: when a stage emits multiple artifact schemas, select validation schema by explicit `schema_name` or `artifact_type` to avoid false validation failures (`src/cine_forge/driver/engine.py`, `tests/unit/test_driver_engine.py`).
- 2026-02-12 — Stage-level lineage can include prior outputs when explicitly requested: use an artifact flag (`include_stage_lineage`) for aggregate artifacts like `scene_index` so dependency graphs capture sibling artifact edges without polluting all outputs (`src/cine_forge/driver/engine.py`, `src/cine_forge/modules/ingest/scene_extract_v1/main.py`).
- 2026-02-13 — Reflow tokenized PDF text before format classification: when PDF extraction emits one-token-per-line text, reconstruct heading/transition boundaries first so screenplay heuristics and downstream parsing stay stable (`src/cine_forge/modules/ingest/story_ingest_v1/main.py`, `tests/unit/test_story_ingest_module.py`).
- 2026-02-13 — Add semantic quality gates to end-to-end tests, not only schema/health checks: for screenplay pipelines, assert non-placeholder canonical text and scene-index realism (scene count/location constraints) so structurally valid but useless outputs fail fast (`tests/integration/test_mvp_recipe_smoke.py`, `src/cine_forge/modules/ingest/script_normalize_v1/main.py`).
- 2026-02-13 — Build replay fixtures from real failed runs: when UI/manual runs expose degradation, capture representative extracted text patterns in deterministic tests before tuning heuristics to prevent regression blind spots (`output/the_mariner/artifacts/raw_input/project/v1.json`, `tests/unit/test_story_ingest_module.py`).
- 2026-02-13 — Keep heading detection regex behavior consistent across ingest, normalization, and scene extraction: compact heading tolerance (`EXT.CITY...`) must be applied end-to-end or scene counts diverge between stages (`src/cine_forge/modules/ingest/story_ingest_v1/main.py`, `src/cine_forge/modules/ingest/script_normalize_v1/main.py`, `src/cine_forge/modules/ingest/scene_extract_v1/main.py`).
- 2026-02-13 — Apply cast-quality filters at extraction and config ranking layers: remove pronouns/structural tokens and derivative OCR noise (e.g., `ROSESWALLOWS` when `ROSE` exists) before assigning primary/supporting characters (`src/cine_forge/modules/ingest/scene_extract_v1/main.py`, `src/cine_forge/modules/ingest/project_config_v1/main.py`, `tests/unit/test_project_config_module.py`).

## Known Pitfalls

- 2026-02-11 — Hidden schema drift: adding output fields without schema updates can silently drop data after validation.
- 2026-02-12 — Runtime-only inputs can bypass cache invalidation: when adding CLI/runtime params that affect module outputs, include them in stage fingerprints (`src/cine_forge/driver/engine.py`) or reuse may return stale artifacts.
- 2026-02-12 — Live structured LLM schemas break on unresolved or untyped envelopes: Pydantic models used for strict JSON response format must call `model_rebuild()` when needed and avoid unconstrained `Any` fields, or OpenAI rejects `response_format` at runtime (`src/cine_forge/modules/ingest/script_normalize_v1/main.py`, `src/cine_forge/modules/ingest/project_config_v1/main.py`).
- 2026-02-12 — Reused run IDs can produce false integration results: API/integration tests that poll `output/runs/<run_id>/run_state.json` may read stale run-state from prior executions if run IDs are fixed; generate unique IDs per test invocation (`tests/integration/test_operator_console_integration.py`).
- 2026-02-12 — Local UI can fail with generic “Failed to fetch” when Vite changes port: CORS allowlists limited to `5173` break dev sessions if Vite auto-selects `5174+`; allow localhost/127.0.0.1 by regex across local ports and surface explicit backend-start guidance in frontend fetch errors (`src/cine_forge/operator_console/app.py`, `ui/operator-console-lite/src/api.ts`).
- 2026-02-12 — Project-switch overlays can block onboarding actions when no active project: if a drawer is mandatory at startup, render it inline (not modal) so primary create-project controls remain clickable (`ui/operator-console-lite/src/App.tsx`, `ui/operator-console-lite/src/styles.css`).
- 2026-02-13 — Schema-valid placeholder outputs can masquerade as success: mock normalization fallback emits parseable `UNKNOWN LOCATION` scenes that pass schema and many smoke checks unless tests assert semantic quality predicates (`src/cine_forge/modules/ingest/script_normalize_v1/main.py`, `tests/integration/test_mvp_recipe_smoke.py`).
- 2026-02-13 — PDF extraction can fail in a second mode beyond one-token-per-line: merged tokens like `EXT.CITYCENTRE- NIGHT` prevent line-start heading detection and can misclassify screenplay as prose unless heading regex/reflow handles missing delimiter spaces (`src/cine_forge/modules/ingest/story_ingest_v1/main.py`, `output/the_mariner/inputs/e916a3c2_The_Mariner.pdf`).
- 2026-02-13 — Stale Pydantic schemas in long-running processes: adding new format literals (e.g., `docx`) to Pydantic models will not be reflected in already-running API/service processes until they are restarted, causing validation failures despite correct code on disk (`src/cine_forge/schemas/models.py`, `src/cine_forge/operator_console/app.py`).

## Lessons Learned

- 2026-02-11 — Keep cross-agent instructions centralized in `AGENTS.md` and reference from tool-specific files to avoid divergence.
- 2026-02-12 — Build the pipeline spine before AI modules: landing immutable artifacts, schema validation, and deterministic graph invalidation first unblocks later stories with minimal rework (`src/cine_forge/artifacts/`, `src/cine_forge/schemas/`, `src/cine_forge/driver/`).
- 2026-02-12 — Heuristic prose tuning needs counterweights for list-heavy inputs: when increasing prose sensitivity for wrapped/public-domain text and PDF extraction noise, add explicit list-structure penalties so `notes` classification does not regress (`src/cine_forge/modules/ingest/story_ingest_v1/main.py`, `tests/unit/test_story_ingest_module.py`).
- 2026-02-12 — Use the repo virtualenv Python for verification commands: local/system `pytest` can be older than `pyproject.toml` minversion, so run `make test-unit PYTHON=.venv/bin/python` and `make lint PYTHON=.venv/bin/python` to keep checks reliable (`Makefile`, `.venv/`).
- 2026-02-13 — For driver-loaded ingest integration tests, patch shared dependencies instead of module-local helpers: monkeypatching `pypdf.PdfReader` is reliable across dynamic module loading, while patching `story_ingest_v1._extract_pdf_text` may not intercept all execution paths (`tests/integration/test_mvp_recipe_smoke.py`, `src/cine_forge/modules/ingest/story_ingest_v1/main.py`).
- 2026-02-13 — Restart long-running services after schema changes: Pydantic models are defined at import time; testing must include process-level lifecycle awareness to avoid "works in tests, fails in real life" discrepancies when schemas evolve (`src/cine_forge/schemas/`, `tests/integration/`).

# Changelog

## [2026-02-13] - Complete Story 007 MVP recipe smoke coverage and runtime parameter UX

### Added
- New Story 007 end-to-end recipe at `configs/recipes/recipe-mvp-ingest.yaml` with runtime placeholders for input/model/acceptance controls.
- New Story 007 fixture corpus under `tests/fixtures/` including screenplay/prose inputs and mocked AI response bundles for normalization, scene QA, and project config detection.
- New integration suite `tests/integration/test_mvp_recipe_smoke.py` covering mocked smoke, live-gated smoke, staleness propagation, and fixture integrity preflight checks.
- New CLI unit coverage in `tests/unit/test_driver_cli.py` for `--params-file` loading, `--param` override precedence, and non-mapping params-file rejection.

### Fixed
- Resolved live structured-output schema failures by rebuilding normalization envelope models and tightening project-config detected-field typing.
- Repaired mocked fixture regression by replacing empty per-scene fixture files with valid JSON and adding preflight validation to prevent recurrence.

### Changed
- Driver CLI now supports generic runtime parameter injection via `--param` and `--params-file`, with improved failure summaries and success output.
- Driver runtime now resolves `${...}` recipe placeholders before validation/execution and supports optional stage-level lineage aggregation for aggregate artifacts.
- Updated Story 007 docs/work-log status to Done and synchronized story index status in `docs/stories.md`.
- Added `smoke-test` and `live-test` Make targets and expanded README runbook docs for MVP smoke execution and artifact inspection.

## [2026-02-12] - Implement Story 006 project configuration module and confirmation flow

### Added
- New `project_config_v1` ingest module with AI-assisted project parameter detection, draft file output, confirmation modes (`--accept-config`, `--config-file`, `--autonomous`), and schema-validated draft/canonical artifact handling.
- New `ProjectConfig` and `DetectedValue` schemas, plus unit/integration coverage for schema validation, module behavior, and end-to-end project config persistence.
- New recipe `configs/recipes/recipe-ingest-extract-config.yaml` for ingest -> normalize -> scene extraction -> project config flow.
- New Story 019 scaffold at `docs/stories/story-019-human-interaction.md` to track deferred non-CLI interaction scope (web UI / Director chat).

### Changed
- Driver runtime now supports config confirmation flags, stage pause state (`paused`), and runtime fingerprint hashing of `input_file`/`config_file` contents for safer cache invalidation.
- Driver schema registry now includes `project_config`.
- Story tracking updates: Story 006 marked `Done` with completed acceptance/tasks/work-log evidence, and deferred interaction scope moved to Story 019.
- Added driver tests proving stale propagation for downstream artifacts when `project_config` changes.

## [2026-02-12] - Implement Story 005 scene extraction pipeline

### Added
- New `scene_extract_v1` ingest module with deterministic-first scene splitting, structured element extraction, provenance tracking, selective AI enrichment, and per-scene QA retry handling.
- New scene schemas (`Scene`, `SceneIndex`, and supporting models) in `src/cine_forge/schemas/scene.py`.
- New extraction recipe `configs/recipes/recipe-ingest-extract.yaml` chaining ingest -> normalize -> extract.
- New unit and integration coverage for scene schemas, extraction behavior, parser/fallback benchmarks, and end-to-end artifact persistence.
- New Story 005 parser evaluation note at `docs/research/story-005-scene-parser-eval.md`.

### Changed
- Driver schema registration now includes `scene` and `scene_index`.
- Driver multi-output validation now resolves schema per artifact (`schema_name`/`artifact_type`) to avoid cross-schema false failures.
- Story tracking updates: Story 005 marked `Done` in `docs/stories.md` and `docs/stories/story-005-scene-extraction.md`.
- Added AGENTS effective pattern documenting per-artifact schema selection for multi-output stages.

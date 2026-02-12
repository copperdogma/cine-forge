# Changelog

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

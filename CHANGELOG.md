# Changelog

## [2026-02-18] - Story 039 deferred evals, Gemini multi-provider fixes, and /deploy skill

### Added
- `/deploy` skill and canonical deployment runbook doc for repeatable production deploys (Story 037 follow-up).
- Three deferred promptfoo eval configs (location, prop, relationship) built and run across all 13 providers (Story 039).
- CalVer versioning (`YYYY.MM.DD`) derived from CHANGELOG.md; shown in sidebar footer and landing page.
- `/api/health` returns `version` field; `/api/changelog` serves full changelog as text.
- Clickable version badge opens changelog dialog in both AppShell and Landing page.
- UI smoke test added to `/deploy` skill (screenshots, console error check).

### Fixed
- Stale model defaults replaced after benchmarking revealed better-performing models per task (Story 039).
- Landing page version positioned in fixed bottom-left corner (matching sidebar pattern).

### Changed
- Trimmed `AGENTS.md` operational noise; moved deployment detail to dedicated doc.
- Story 038 marked done; Story 039 scope expanded to include deferred eval coverage.

---

## [2026-02-17] - Production deployment, Gemini support, Sonnet 4.6 benchmarks, and Story 037-038-047

### Added
- Deployed CineForge to production at `cineforge.copper-dog.com` on Fly.io with Let's Encrypt SSL, Cloudflare DNS, and a persistent 1GB volume (Story 037).
- Multi-provider LLM transport with Google Gemini support (`gemini-2.5-flash`, `gemini-2.5-pro`); backend now routes to Anthropic, OpenAI, or Google based on model ID prefix (Story 038).
- Story 045 (Entity Cross-Linking) and Story 046 (Theme System) draft files added to backlog.

### Fixed
- `PermissionError` crash on Fly.io when the volume `lost+found` directory was encountered during project discovery.
- Untracked `.claude/settings.local.json` from git and added it to `.gitignore`.

### Changed
- Benchmarked Sonnet 4.6 across all six promptfoo evals (character extraction, scene extraction, location, prop, relationship, config detection) against 12 other providers; updated model defaults in `src/cine_forge/schemas/models.py` with winning models per task (Story 047).

---

## [2026-02-16] - Conversational AI Chat, Entity-first Navigation, UI wiring, and pipeline performance

### Added
- Conversational AI Chat (Story 011f): full six-phase implementation including streaming AI responses, persistent chat thread, knowledge layer surfacing relevant artifacts into context, inline tool-use for running pipeline stages, smart suggestions, and lint cleanup.
- Entity-first navigation (Story 043): dedicated Character, Location, and Prop detail pages with cross-references; enriched sorting by narrative prominence; script-to-scene deep links; breadcrumbs; sticky sort/density preferences persisted to `project.json`.
- Story 041 (Artifact Quality Improvements) story file added; immediately implemented as Story 042 after renumbering.

### Fixed
- Wired all mock UI components to real backend APIs, replacing placeholder data with live artifact fetches (Story 042).
- Entity ID consistency across detail pages; breadcrumb navigation and artifact UX polish (Story 042).
- World-building cost explosion caused by unnecessary QA passes: hardcoded `skip_qa` and removed dead recipe references.
- Landing page now shows 5 most recent projects with timestamps and an expand/collapse toggle.

### Changed
- `ui/operator-console/` directory flattened to `ui/` — Story 043 done and directory structure simplified.
- Pipeline performance optimized (Story 040): reduced redundant AI calls, improved stage caching, and lowered median run cost.
- Chat-driven progress replaces polling: server-side chat events drive run state updates (Story 011e Phases 1.5–2.5).
- Project identity now uses URL slugs (`/projects/:slug`) rather than numeric IDs; chat state persisted server-side (Story 011e).

---

## [2026-02-15] - Operator Console production build, promptfoo benchmarking, and model selection

### Added
- Production Operator Console build (Story 011d): full React + shadcn/ui UI with file-first project creation, script-centric home page, story-centric navigation (Script / Scenes / Characters / Locations / World / Inbox), and chat panel as the primary interaction surface.
- Script-centric home page and chat panel Phase 1 implementation (Story 011e): chat replaces sidebar hints; Inbox is a filtered view of `needs_action` chat messages.
- promptfoo benchmarking tooling evaluation complete (Story 035): workspace structure, dual evaluation pattern (Python scorer + LLM rubric), cross-provider judge strategy, and pitfalls documented in `AGENTS.md`.
- Model Selection and Eval Framework (Story 036): character extraction eval across 13 providers; Opus 4.6 established as judge; winning models recorded per task.
- Claude Code skills wired up via `.claude/skills/` symlinks for agent discovery.

### Changed
- Story 011b Operator Console research and design decisions documented and complete.
- Story 011c phase summary and recommended order synced in story file.
- `AGENTS.md` updated with benchmarking workspace structure, eval catalog, model selection table, and lessons learned (promptfoo pitfalls: `max_tokens` trap, `---` separator trap, Gemini token budget).

---

## [2026-02-14] - World-building pipeline, Entity Relationship Graph, 3-Recipe Architecture, and UI routing

### Added
- High-fidelity world-building infrastructure: bible generation modules, resilient LLM retry logic with token escalation, and catch-and-retry on malformed JSON (`src/cine_forge/ai/llm.py`).
- Entity Relationship Graph module: AI-powered entity extraction, `needs_all` orchestration pattern, and selective per-entity re-runs.
- Basic UI visualization for the Entity Relationship Graph.
- 3-Recipe Architecture (Intake / Synthesis / Analysis): partitions pipeline into independently runnable segments with human-in-the-loop gates between expensive world-building steps.
- Continuity tracking foundation added alongside 3-Recipe Architecture.
- Resource-oriented routing foundation for Operator Console: identity in URL path, not search params.
- Stories 008 and 009 documented and marked done.

### Changed
- Enhanced Entity Graph with real AI extraction replacing stubs; selective re-run support added.
- `AGENTS.md`: added "No Implicit Commits" mandate; captured cross-recipe artifact reuse pattern via `store_inputs`; documented 3-Recipe Architecture lesson and resource-oriented UI principle.

---

## [2026-02-13] - Story 007c remediation, DOCX support, hot-reload, and bible module

### Added
- Semantic quality gates for degraded PDF ingestion: confidence scoring, anomaly detection, and remediation triggers to prevent schema-valid-but-useless artifacts (Story 007c).
- Unit and integration regression tests for Story 007c PDF quality remediation.
- DOCX ingestion support: `python-docx` based parser added to the ingest module; UI file picker now accepts `.docx` alongside `.pdf` and `.fountain`.
- Bible infrastructure and character bible module: `CharacterBible` schema, AI-driven extraction, and versioned artifact output.
- All missing story files (008–034) scaffolded with design foundations.

### Fixed
- Hot-reloading enabled for the Operator Console backend via `uvicorn --reload`; eliminates manual restarts during local development.

### Changed
- Story index (`docs/stories.md`) updated to reflect new stories and status changes.

---

## [2026-02-13] - Deliver Operator Console Lite and add MVP fidelity remediation story

### Added
- New Operator Console Lite backend service under `src/cine_forge/operator_console/` with project lifecycle, run start/state/events, artifact browsing, recent-project discovery, and input upload endpoints.
- New React + Vite UI under `ui/operator-console-lite/` with file-first project creation (drag/drop + file picker), run controls, runs/events inspection, artifact browser, and on-demand project switcher drawer.
- New test coverage:
  - `tests/unit/test_operator_console_api.py`
  - `tests/integration/test_operator_console_integration.py`
  - `ui/operator-console-lite/e2e/operator-console.spec.ts`
- New remediation planning story `docs/stories/story-007c-mvp-reality-remediation.md` to address real-run artifact fidelity issues discovered via UI-led validation.

### Fixed
- Resolved local dev CORS failures causing UI "Failed to fetch" by allowing localhost/127.0.0.1 origins across local ports in Operator Console API middleware.
- Improved artifact browser UX with explicit selected group/version highlighting and auto-selection of latest/single version.
- Stabilized Playwright test startup behavior in UI config for deterministic local runs.

### Changed
- Updated Story 007b acceptance/task wording to align with approved UX (`Project Switcher` replacing dedicated `Open Project` route while preserving open-existing-project functionality).
- Updated docs in `README.md` and story index in `docs/stories.md` for Operator Console flows and new 007c scope.
- Extended project guidance in `AGENTS.md` for mandatory manual UI verification and captured pitfalls from recent execution.
- Updated `.gitignore` for UI build/test artifacts (`*.tsbuildinfo`, `test-results/`, `playwright-report/`).

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

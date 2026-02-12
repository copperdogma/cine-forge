# Story 006: Project Configuration (Auto-Initialized)

**Status**: Done
**Created**: 2026-02-11
**Spec Refs**: 4.4 (Project Configuration), 2.5 (Human Control Modes), 2.7 (Cost Transparency / Budget Caps)
**Depends On**: Story 002 (pipeline foundation), Story 004 (canonical script — the text to analyze), Story 005 (scene extraction — provides character/location counts)

---

## Goal

Auto-detect project-level parameters from the canonical script and scene data, present them to the user as a draft configuration, allow the user to confirm or modify, and save the result as a canonical `project_config` artifact that every downstream role and module consults.

This is the project's "settings file" — genre, tone, format, duration, control mode, budget, etc. It is created once during ingestion and may be revised at any time. Every role reads it to align creative decisions with the user's intent.

This module is also the first module that requires **human interaction** — the draft config must be presented for confirmation before the pipeline proceeds. For the MVP, this is a simple CLI prompt (or a JSON file the user edits). The full interactive UI is a later story.

## Acceptance Criteria

### Auto-Detection from Script and Scene Data
- [x] Module reads the `canonical_script` artifact (the screenplay text) and the `scene_index` artifact (structured scene summary from Story 005).
- [x] AI analyzes the script and scene data to extract:
  - [x] **Project title**: inferred from the script's title page or opening, or from the most prominent heading.
  - [x] **Format**: short film, feature, series episode, music video, etc. Based on length, structure, and content.
  - [x] **Genre**: horror, comedy, drama, thriller, sci-fi, etc. May be multiple (e.g., "comedy-drama"). Based on tone, content, setting.
  - [x] **Tone**: dark and grounded, whimsical, surreal, gritty, etc. Based on dialogue style, action descriptions, narrative voice.
  - [x] **Estimated duration**: based on the page-count rule of thumb (~1 minute per page for screenplays) and scene count/complexity.
  - [x] **Cast size and primary characters**: from the scene index's `unique_characters` list. Implemented as a hybrid approach: AI draft values plus deterministic ranking from scene frequency and dialogue cues.
  - [x] **Number and nature of locations**: from the scene index's `unique_locations` list. AI categorizes (interior/exterior, practical/fantastical, etc.).
  - [x] **Target audience**: if inferable from content (e.g., children's content, mature themes). May be `null` if not confidently inferable.
- [x] Each auto-detected value includes a confidence score and brief rationale.
- [x] Detection uses the AI call wrapper and QA check from Story 004.

### User-Specified Parameters (Not Auto-Detected)
- [x] The following parameters are NOT auto-detected — they are presented with sensible defaults that the user confirms or overrides:
  - [x] **Aspect ratio**: default `16:9`, options include `2.39:1`, `4:3`, `1:1`, `9:16`, custom.
  - [x] **Production mode**: `ai_generated` (default for MVP), `irl`, `hybrid`.
  - [x] **Human control mode**: `autonomous`, `checkpoint` (default), `advisory`. Per spec 2.5.
  - [x] **Style pack selections**: per-role style pack assignments. Empty/default for MVP (style packs are Story 020).
  - [x] **Budget / cost cap**: optional per-project budget limit in USD. `null` = no cap. Per spec 2.7.
  - [x] **Default AI model**: which model to use for AI calls when not overridden per-module. Default `gpt-4o`.

### Human Confirmation Flow
- [x] The module produces a `draft_project_config` and presents it to the user for review.
- [x] **MVP interaction** (CLI-based):
  - [x] Print the draft config as formatted YAML/JSON to stdout.
  - [x] Write the draft to a file (`output/{project}/draft_config.yaml`) that the user can edit.
  - [x] The user either: (a) confirms as-is via CLI flag (`--accept-config`), or (b) edits the file and re-runs with `--config-file path/to/edited_config.yaml`.
  - [x] On confirmation, the draft becomes the canonical `project_config` artifact.
- [x] **Autonomous mode**: if human control mode is set to `autonomous` (e.g., via CLI flag `--autonomous`), the draft is auto-confirmed without human interaction. The AI's best guesses become the config.

### Project Config Artifact
- [x] Output artifact type: `project_config`.
- [x] Immutable and versioned like all artifacts. User edits later produce `project_config_v2`.
- [x] Changing the project config marks downstream artifacts as `stale` via the dependency graph (Story 002) — because creative decisions made under one config may not apply under another.
- [x] Every module and role that reads the project config declares a dependency on it.

### Schema
- [x] `ProjectConfig` Pydantic schema:
  ```python
  class DetectedValue(BaseModel):
      """An auto-detected configuration value."""
      value: Any
      confidence: float
      rationale: str
      source: Literal["auto_detected", "user_specified", "default"]

  class ProjectConfig(BaseModel):
      """Project-level configuration — the 'settings' for the entire production."""
      # Auto-detected
      title: str
      format: str                         # "short_film", "feature", "series_episode", "music_video", etc.
      genre: list[str]                    # May be multiple: ["comedy", "drama"]
      tone: list[str]                     # May be multiple: ["dark", "grounded"]
      estimated_duration_minutes: float | None
      primary_characters: list[str]
      supporting_characters: list[str]
      location_count: int
      locations_summary: list[str]        # Normalized location names
      target_audience: str | None

      # User-specified (with defaults)
      aspect_ratio: str                   # "16:9", "2.39:1", etc.
      production_mode: Literal["ai_generated", "irl", "hybrid"]
      human_control_mode: Literal["autonomous", "checkpoint", "advisory"]
      style_packs: dict[str, str]         # role_id → style_pack_id (empty for MVP)
      budget_cap_usd: float | None        # None = no cap
      default_model: str                  # Default LLM model for AI calls

      # Metadata
      detection_details: dict[str, DetectedValue]  # Per-field detection metadata
      confirmed: bool                     # False = draft, True = user-confirmed
      confirmed_at: str | None            # ISO timestamp of confirmation
  ```
- [x] Schema registered in the schema registry.
- [x] Structural validation (QA tier 1) passes on all outputs.

### Module Manifest
- [x] Module directory: `src/cine_forge/modules/ingest/project_config_v1/`
- [x] `module.yaml`:
  ```yaml
  module_id: project_config_v1
  stage: ingest
  description: "Auto-detects project parameters and produces a draft config for user confirmation."
  input_schemas: ["canonical_script", "scene_index"]
  output_schemas: ["project_config"]
  parameters:
    model:
      type: string
      required: false
      default: "gpt-4o"
      description: "LLM model for auto-detection."
    accept_config:
      type: boolean
      required: false
      default: false
      description: "Auto-confirm the draft config without human review."
    config_file:
      type: string
      required: false
      description: "Path to a user-edited config file to use instead of auto-detection."
  ```
- [x] `main.py` implementing the standard module contract.

### Testing
- [x] Unit tests for auto-detection (mocked AI):
  - [x] Feature-length screenplay → detected as "feature", appropriate genre/tone, ~90–120 min duration estimate.
  - [x] Short script (5 pages) → detected as "short_film", ~5 min duration.
  - [x] Comedy with clear comedic dialogue → genre includes "comedy".
  - [x] Multiple characters → correctly split into primary vs. supporting.
- [x] Unit tests for user confirmation flow:
  - [x] `--accept-config` flag → draft auto-confirmed, artifact saved.
  - [x] `--config-file` → user-edited values override auto-detected values, artifact saved.
  - [x] No flag and no config file → draft saved as unconfirmed, pipeline pauses.
- [x] Unit tests for schema validation:
  - [x] All fields present and correctly typed.
  - [x] `detection_details` includes rationale for each auto-detected field.
- [x] Integration test: canonical script + scene index → project config artifact in store with correct lineage.

## Design Notes

### Why a Separate Module (Not Part of Ingestion or Extraction)?

Project config depends on both the canonical script text (for title, tone, genre detection) and the scene index (for character counts, location counts, duration estimates). It runs after both are available. Keeping it as its own module:
- Allows re-running config detection without re-running ingestion or extraction.
- Makes the dependency explicit: config depends on script + scenes, not the other way around.
- Keeps Story 003 (ingestion) simple and non-AI.

### Config as a Canonical Artifact

The project config is not a side-channel settings file — it's a first-class versioned artifact in the artifact store. This means:
- Changes to the config produce new versions with full audit trail.
- Downstream artifacts that were created under `project_config_v1` become `stale` when `project_config_v2` is saved — because creative decisions (tone, genre, audience) may now be wrong.
- The user can see exactly when and why the config changed.

### Human Control Mode Affects Everything

The `human_control_mode` setting (`autonomous` / `checkpoint` / `advisory`) is one of the most important values in the config. It determines:
- Whether the pipeline pauses for human approval at review gates.
- Whether the Director role acts independently or waits for confirmation.
- Whether QA failures escalate to the user or are handled autonomously.

For MVP, `checkpoint` is the default — the pipeline pauses at major transitions. `autonomous` mode is available for users who want hands-off operation. `advisory` mode (AI suggests, human decides everything) is supported but less tested in MVP.

### What This Story Does NOT Include

- **Style pack integration** — style packs are Story 020. The `style_packs` field exists in the schema but is empty for MVP.
- **Budget enforcement** — the `budget_cap_usd` field exists and is saved, but actual enforcement (pausing the pipeline when budget is exceeded) is Story 026. For MVP, it's informational only.
- **Interactive config editing** — web UI or chat-based config editing. MVP uses CLI + file editing.
  - Deferred to Story 019 (`docs/stories/story-019-human-interaction.md`).
- **Per-stage model selection** — the `default_model` field sets a global default. Per-module model overrides are handled by recipe parameters, not the config.

## Tasks

- [x] Define `ProjectConfig`, `DetectedValue` schemas in `src/cine_forge/schemas/`.
- [x] Register schemas in the schema registry.
- [x] Add/confirm schema-level literals and compatibility hooks required for `project_config` validation/versioning.
- [x] Create module directory: `src/cine_forge/modules/ingest/project_config_v1/`.
- [x] Write `module.yaml` manifest.
- [x] Implement auto-detection prompt: analyze canonical script text + scene index → extract project parameters with confidence.
- [x] Implement draft config generation: merge auto-detected values with user-specified defaults.
- [x] Implement user confirmation flow: print draft, write to file, accept via flag or edited file.
- [x] Implement `main.py`: load canonical_script + scene_index → AI auto-detection → merge with defaults → present draft → on confirmation, save as `project_config` artifact.
- [x] Wire runtime controls in driver CLI/runtime state (`--accept-config`, `--config-file`, `--autonomous`) and include config-affecting params in stage fingerprints to avoid stale cache reuse.
- [x] Ensure pause/resume behavior is explicit when config remains unconfirmed (event log + run state).
- [x] Create test fixtures: sample canonical script + scene index (reuse from Story 005 fixtures).
- [x] Write unit tests for auto-detection (mocked AI).
- [x] Write unit tests for confirmation flow (accept flag, config file, no-flag pause).
- [x] Write unit tests for driver/runtime integration of config confirmation flags and fingerprint invalidation behavior.
- [x] Write integration test: full flow → project_config artifact in store.
- [x] Manually inspect produced `project_config` artifact payload in `output/` during verification and record evidence in work log.
- [x] Run `make test-unit` and `make lint` before closure; capture result summary in work log.
- [x] Update AGENTS.md with any lessons learned.

## Implementation Plan (2026-02-12)

1. Schema and registry foundation
- Add `DetectedValue` and `ProjectConfig` to `src/cine_forge/schemas/models.py` with explicit field constraints and source attribution.
- Register schema in `src/cine_forge/schemas/registry.py` and add compatibility assertions in schema tests.

2. Module scaffold and detection pipeline
- Create `src/cine_forge/modules/ingest/project_config_v1/` with `module.yaml` and `main.py`.
- Implement extraction inputs from `canonical_script` + `scene_index` and AI call wrapper usage matching Story 004 patterns.
- Build deterministic defaults for user-specified values and generate `detection_details` for trust/auditability.

3. Confirmation and runtime behavior
- Implement draft persistence to `output/{project}/draft_config.yaml` and stdout preview for CLI UX.
- Support confirmation paths: `--accept-config`, `--config-file`, and autonomous auto-confirm behavior.
- Ensure unconfirmed state pauses downstream progression cleanly with clear event/run-state signaling.

4. Test and verification pass
- Add unit coverage for detection heuristics/mapping, confirmation paths, and schema validation.
- Add integration coverage for canonical input to stored `project_config` artifact with lineage checks.
- Execute `make test-unit` and `make lint`, then manually inspect generated artifact payload and log evidence.

## Notes

- This is a relatively lightweight AI module — a single AI call to analyze the script and produce a config. No long document concerns (the AI reads the script, it doesn't edit it). No chunking needed.
- The user confirmation step is the first place the pipeline "pauses" for human input. Keep the CLI interaction minimal and clear — the user should understand exactly what they're confirming and how to change values.
- The `detection_details` field (per-field confidence and rationale) is important for trust — the user should see why the AI thinks this is a "horror comedy" and be able to correct it if wrong.
- For the MVP smoke test (Story 007), the `--accept-config` flag allows fully automated end-to-end runs without human interaction. This is essential for CI/testing.

## Work Log

(entries will be added as work progresses)

### 20260212-1543 — Story checklist and structure audit
- **Result:** Success.
- **Notes:** Verified `docs/stories/story-006-project-configuration.md` includes required sections and an existing checkbox-based `## Tasks` list; no structural gaps blocked story execution.
- **Next:** Expand tasks to capture runtime/fingerprint/testing obligations so the checklist is implementation-complete.

### 20260212-1543 — Expanded task checklist for execution readiness
- **Result:** Success.
- **Notes:** Updated task list with actionable items for driver runtime flags, cache-fingerprint safety, pause/resume behavior, manual artifact inspection, and required verification commands (`make test-unit`, `make lint`).
- **Next:** Draft an ordered implementation plan tied to concrete files and verification flow.

### 20260212-1543 — Added phased implementation plan for Story 006
- **Result:** Success.
- **Notes:** Added `## Implementation Plan (2026-02-12)` covering schema/registry work, module scaffold, confirmation flow/runtime integration, and test/verification sequencing.
- **Next:** Start implementation in schema and module files, then execute test/lint and artifact inspection evidence capture.

### 20260212-1552 — Implemented schema, module, and driver support for project config
- **Result:** Success.
- **Notes:** Added `ProjectConfig` + `DetectedValue` schemas (`src/cine_forge/schemas/models.py`, `src/cine_forge/schemas/__init__.py`), implemented new module `src/cine_forge/modules/ingest/project_config_v1/` (`module.yaml`, `main.py`), registered `project_config` in driver schema registry, added CLI runtime flags (`--accept-config`, `--config-file`, `--autonomous`), and added pause-stage support with `stage_paused` event/run-state updates in `src/cine_forge/driver/engine.py` + `src/cine_forge/driver/state.py`.
- **Next:** Land comprehensive tests and verify cache/runtime behavior plus integration lineage.

### 20260212-1552 — Added story-specific unit/integration coverage
- **Result:** Success.
- **Notes:** Added unit tests for schema and module behavior (`tests/unit/test_project_config_schema.py`, `tests/unit/test_project_config_module.py`), extended driver tests for `project_config` schema registration, runtime config file fingerprint invalidation, and pause behavior (`tests/unit/test_driver_engine.py`), and added integration flow test + recipe (`tests/integration/test_project_config_integration.py`, `configs/recipes/recipe-ingest-extract-config.yaml`).
- **Next:** Execute required verification commands and inspect persisted artifacts.

### 20260212-1552 — Verification run, lint/test pass, and artifact inspection evidence
- **Result:** Success.
- **Notes:** Executed `make test-unit PYTHON=.venv/bin/python` (94 passed, 16 deselected) and `make lint PYTHON=.venv/bin/python` (all checks passed). Ran driver execution for artifact inspection: `PYTHONPATH=src .venv/bin/python -m cine_forge.driver --recipe configs/recipes/recipe-ingest-extract-config.yaml --run-id story006-verify --force`. Manually inspected `output/project/artifacts/project_config/project/v3.json` confirming `confirmed=true`, `detection_details` rationale/source metadata, and lineage references to `canonical_script` + `scene_index`; confirmed draft file emission at `output/project/draft_config.yaml`.
- **Next:** Story ready for handoff/closure; proceed to Story 007 recipe smoke consolidation.

### 20260212-1602 — Closed post-validation gaps for draft semantics and dependency evidence
- **Result:** Success.
- **Notes:** Updated `project_config_v1` so unconfirmed output persists as `draft_project_config` (schema-validated via `schema_name=project_config`) while confirmed output persists as canonical `project_config` (`src/cine_forge/modules/ingest/project_config_v1/main.py`). Replaced primary/supporting character split with weighted ranking based on scene frequency + dialogue cue counts. Added/updated tests for draft artifact type behavior, ranking rationale, and downstream stale propagation when `project_config` changes (`tests/unit/test_project_config_module.py`, `tests/unit/test_driver_engine.py`).
- **Next:** Re-run verification commands and confirm no remaining Story 006 gaps.

### 20260212-1602 — Re-validation after gap fixes
- **Result:** Success.
- **Notes:** Executed targeted tests plus required suite checks: `PYTHONPATH=src .venv/bin/python -m pytest -m unit tests/unit/test_project_config_module.py tests/unit/test_driver_engine.py` (20 passed), `PYTHONPATH=src .venv/bin/python -m pytest -m integration tests/integration/test_project_config_integration.py` (1 passed), `make test-unit PYTHON=.venv/bin/python` (95 passed, 16 deselected), and `make lint PYTHON=.venv/bin/python` (all checks passed).
- **Next:** Story 006 implementation and validation are complete; handoff ready.

### 20260212-1616 — Synced acceptance checklist and finalized implementation interpretation
- **Result:** Success.
- **Notes:** Updated Acceptance Criteria checkboxes to reflect completed implementation and test evidence. Recorded the chosen interpretation for character classification: hybrid behavior where AI detection is combined with deterministic ranking by scene frequency and dialogue cues (`src/cine_forge/modules/ingest/project_config_v1/main.py`).
- **Next:** Optional final pass: re-run Story 006 review rubric and proceed to Story 007.

### 20260212-1617 — Moved deferred interaction-mode scope to Story 019
- **Result:** Success.
- **Notes:** Removed the deferred “Future interaction modes” acceptance checkbox from Story 006 and moved that scope to a newly created Story 019 file (`docs/stories/story-019-human-interaction.md`), including explicit project-config interactive editing requirements for web UI / Director chat flows.
- **Next:** Keep Story 006 focused on MVP CLI behavior; schedule Story 019 for non-CLI interaction implementation.

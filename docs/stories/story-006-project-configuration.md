# Story 006: Project Configuration (Auto-Initialized)

**Status**: To Do
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
- [ ] Module reads the `canonical_script` artifact (the screenplay text) and the `scene_index` artifact (structured scene summary from Story 005).
- [ ] AI analyzes the script and scene data to extract:
  - [ ] **Project title**: inferred from the script's title page or opening, or from the most prominent heading.
  - [ ] **Format**: short film, feature, series episode, music video, etc. Based on length, structure, and content.
  - [ ] **Genre**: horror, comedy, drama, thriller, sci-fi, etc. May be multiple (e.g., "comedy-drama"). Based on tone, content, setting.
  - [ ] **Tone**: dark and grounded, whimsical, surreal, gritty, etc. Based on dialogue style, action descriptions, narrative voice.
  - [ ] **Estimated duration**: based on the page-count rule of thumb (~1 minute per page for screenplays) and scene count/complexity.
  - [ ] **Cast size and primary characters**: from the scene index's `unique_characters` list. AI identifies which are primary vs. supporting based on scene frequency and dialogue volume.
  - [ ] **Number and nature of locations**: from the scene index's `unique_locations` list. AI categorizes (interior/exterior, practical/fantastical, etc.).
  - [ ] **Target audience**: if inferable from content (e.g., children's content, mature themes). May be `null` if not confidently inferable.
- [ ] Each auto-detected value includes a confidence score and brief rationale.
- [ ] Detection uses the AI call wrapper and QA check from Story 004.

### User-Specified Parameters (Not Auto-Detected)
- [ ] The following parameters are NOT auto-detected — they are presented with sensible defaults that the user confirms or overrides:
  - [ ] **Aspect ratio**: default `16:9`, options include `2.39:1`, `4:3`, `1:1`, `9:16`, custom.
  - [ ] **Production mode**: `ai_generated` (default for MVP), `irl`, `hybrid`.
  - [ ] **Human control mode**: `autonomous`, `checkpoint` (default), `advisory`. Per spec 2.5.
  - [ ] **Style pack selections**: per-role style pack assignments. Empty/default for MVP (style packs are Story 020).
  - [ ] **Budget / cost cap**: optional per-project budget limit in USD. `null` = no cap. Per spec 2.7.
  - [ ] **Default AI model**: which model to use for AI calls when not overridden per-module. Default `gpt-4o`.

### Human Confirmation Flow
- [ ] The module produces a `draft_project_config` and presents it to the user for review.
- [ ] **MVP interaction** (CLI-based):
  - [ ] Print the draft config as formatted YAML/JSON to stdout.
  - [ ] Write the draft to a file (`output/{project}/draft_config.yaml`) that the user can edit.
  - [ ] The user either: (a) confirms as-is via CLI flag (`--accept-config`), or (b) edits the file and re-runs with `--config-file path/to/edited_config.yaml`.
  - [ ] On confirmation, the draft becomes the canonical `project_config` artifact.
- [ ] **Autonomous mode**: if human control mode is set to `autonomous` (e.g., via CLI flag `--autonomous`), the draft is auto-confirmed without human interaction. The AI's best guesses become the config.
- [ ] **Future interaction modes** (not this story): web UI, interactive chat with the Director, etc.

### Project Config Artifact
- [ ] Output artifact type: `project_config`.
- [ ] Immutable and versioned like all artifacts. User edits later produce `project_config_v2`.
- [ ] Changing the project config marks downstream artifacts as `stale` via the dependency graph (Story 002) — because creative decisions made under one config may not apply under another.
- [ ] Every module and role that reads the project config declares a dependency on it.

### Schema
- [ ] `ProjectConfig` Pydantic schema:
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
- [ ] Schema registered in the schema registry.
- [ ] Structural validation (QA tier 1) passes on all outputs.

### Module Manifest
- [ ] Module directory: `src/cine_forge/modules/ingest/project_config_v1/`
- [ ] `module.yaml`:
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
- [ ] `main.py` implementing the standard module contract.

### Testing
- [ ] Unit tests for auto-detection (mocked AI):
  - [ ] Feature-length screenplay → detected as "feature", appropriate genre/tone, ~90–120 min duration estimate.
  - [ ] Short script (5 pages) → detected as "short_film", ~5 min duration.
  - [ ] Comedy with clear comedic dialogue → genre includes "comedy".
  - [ ] Multiple characters → correctly split into primary vs. supporting.
- [ ] Unit tests for user confirmation flow:
  - [ ] `--accept-config` flag → draft auto-confirmed, artifact saved.
  - [ ] `--config-file` → user-edited values override auto-detected values, artifact saved.
  - [ ] No flag and no config file → draft saved as unconfirmed, pipeline pauses.
- [ ] Unit tests for schema validation:
  - [ ] All fields present and correctly typed.
  - [ ] `detection_details` includes rationale for each auto-detected field.
- [ ] Integration test: canonical script + scene index → project config artifact in store with correct lineage.

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
- **Per-stage model selection** — the `default_model` field sets a global default. Per-module model overrides are handled by recipe parameters, not the config.

## Tasks

- [ ] Define `ProjectConfig`, `DetectedValue` schemas in `src/cine_forge/schemas/`.
- [ ] Register schemas in the schema registry.
- [ ] Create module directory: `src/cine_forge/modules/ingest/project_config_v1/`.
- [ ] Write `module.yaml` manifest.
- [ ] Implement auto-detection prompt: analyze canonical script text + scene index → extract project parameters with confidence.
- [ ] Implement draft config generation: merge auto-detected values with user-specified defaults.
- [ ] Implement user confirmation flow: print draft, write to file, accept via flag or edited file.
- [ ] Implement `main.py`: load canonical_script + scene_index → AI auto-detection → merge with defaults → present draft → on confirmation, save as `project_config` artifact.
- [ ] Create test fixtures: sample canonical script + scene index (reuse from Story 005 fixtures).
- [ ] Write unit tests for auto-detection (mocked AI).
- [ ] Write unit tests for confirmation flow (accept flag, config file, no-flag pause).
- [ ] Write integration test: full flow → project_config artifact in store.
- [ ] Update AGENTS.md with any lessons learned.

## Notes

- This is a relatively lightweight AI module — a single AI call to analyze the script and produce a config. No long document concerns (the AI reads the script, it doesn't edit it). No chunking needed.
- The user confirmation step is the first place the pipeline "pauses" for human input. Keep the CLI interaction minimal and clear — the user should understand exactly what they're confirming and how to change values.
- The `detection_details` field (per-field confidence and rationale) is important for trust — the user should see why the AI thinks this is a "horror comedy" and be able to correct it if wrong.
- For the MVP smoke test (Story 007), the `--accept-config` flag allows fully automated end-to-end runs without human interaction. This is essential for CI/testing.

## Work Log

(entries will be added as work progresses)

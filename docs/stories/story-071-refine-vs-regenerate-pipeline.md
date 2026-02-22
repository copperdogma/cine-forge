# Story 071 — Refine vs. Regenerate Pipeline Modes

**Priority**: Medium
**Status**: Pending
**Phase**: Cross-Cutting
**Spec Refs**: spec.md §2.1 (Immutability), §2.2 (Versioning)
**Depends On**: None (builds on existing `ArtifactStore`, `store_inputs_all`, and `world_building` recipe infrastructure)

## Goal

Currently, re-running the `world_building` recipe always extracts entities from scratch, discarding any user edits that had been made to character, location, or prop bibles. This story adds a **Refine mode** as an alternative to the existing **Regenerate mode**, where the pipeline passes the latest artifact version of each entity bible back to the LLM alongside the current script — enabling incremental, edit-preserving updates rather than wholesale replacement. CineForge's immutability guarantee (every run writes a new version) ensures no data is ever truly lost; Refine mode simply makes the AI a better collaborator by honoring existing work. The story also adds a version history browser to the UI so users can inspect, compare, and restore any prior version.

## Acceptance Criteria

- [ ] A `pipeline_mode` parameter (`regenerate` | `refine`) can be passed to `start_run` via the API. It defaults to `regenerate` to preserve current behavior.
- [ ] In `refine` mode, the `entity_discovery_v1`, `character_bible_v1`, `location_bible_v1`, and `prop_bible_v1` modules receive the latest stored artifact data for each entity as an additional input (`prior_character_bibles`, `prior_location_bibles`, `prior_prop_bibles`).
- [ ] Each bible extraction module uses a distinct **refine prompt** when prior artifact data is present: "Given this existing profile, update it based on the current script. Preserve user edits where the script does not contradict them."
- [ ] In refine mode, the `entity_discovery` stage seeds its incremental pass with entity names from the prior bibles, preventing existing entities from being dropped by the discovery pass.
- [ ] Every refine-mode run still produces a new artifact version (vN+1) — it does NOT mutate existing artifacts.
- [ ] The `stage_fingerprint` for bible stages in refine mode incorporates the prior artifact refs, ensuring the stage cache is correctly invalidated when prior artifacts change.
- [ ] The UI exposes a **"Run Mode"** toggle (Regenerate / Refine) on the run launch dialog.
- [ ] The UI has a **version history panel** on artifact detail pages that lists all versions, shows the health of each, and allows the user to diff two versions side-by-side (using the existing `diff_versions` method on `ArtifactStore`).
- [ ] A diff API endpoint exists: `GET /api/projects/{project_id}/artifacts/{artifact_type}/{entity_id}/diff?from_version=N&to_version=M`.
- [ ] Unit tests cover: (a) that refine mode injects prior artifact data into module inputs, (b) that the refine prompt is used, (c) that regenerate mode is unaffected.

## Out of Scope

- Selective entity refine (e.g., "only refine MARINER, regenerate all others") — too complex for this story.
- User-editable bible fields in the UI (that is a separate editor story).
- Refine mode for non-bible artifact types (e.g., `scene`, `canonical_script`).
- Auto-detecting whether a user made edits (treat all existing artifacts as "user-vetted" for refine purposes).
- A separate `recipe-world-building-refine.yaml` — the mode is passed as a runtime parameter to the existing recipe.

## AI Considerations

Refine mode **is fundamentally an LLM prompt engineering problem**. The distinction between regenerate and refine only matters because of how the LLM is instructed:

- **Regenerate prompt** (current): "You are a character analyst. Extract a master definition for character: {name}. Return JSON matching CharacterBible schema." — pure extraction from the script with no prior context.
- **Refine prompt** (new): "You are a character analyst. Below is an existing character profile that may contain user edits or corrections. Update it based on the current script. Where the script confirms or expands on existing content, keep or extend it. Where the script contradicts existing content, update it. Do NOT discard information without script evidence." — guided incremental update.

The risk of the refine prompt is **anchoring**: the model may preserve stale data because it was in the prior artifact. Mitigation: include the full script context (not just diffs), and explicitly instruct the model that script evidence takes precedence over the prior artifact. The QA pass remains important in refine mode to catch anchoring failures.

Entity discovery in refine mode also benefits from the prior artifact lists: the discovery module already partially supports this via `store_inputs_all` bootstrapping (see `entity_discovery_v1/main.py` lines 60–74, which seeds `current_list` from existing bibles). Refine mode simply makes this the default behavior instead of a fallback.

The LLM judge in the eval suite should specifically test: does the refined output preserve a deliberate user correction (e.g., name change) while still integrating new script evidence? This is the core quality signal.

## Tasks

- [ ] **Backend: Add `pipeline_mode` to `start_run` API request and `runtime_params`**
  - Add `pipeline_mode: Literal["regenerate", "refine"] = "regenerate"` to `RunStartRequest` in `src/cine_forge/api/models.py`
  - Thread `pipeline_mode` into `runtime_params` in `OperatorConsoleService.start_run` (`src/cine_forge/api/service.py`)

- [ ] **Recipe: Add `store_inputs_all` for prior bibles to bible extraction stages in `recipe-world-building.yaml`**
  - `character_bible` stage: add `store_inputs_all: {prior_character_bibles: character_bible}`
  - `location_bible` stage: add `store_inputs_all: {prior_location_bibles: location_bible}`
  - `prop_bible` stage: add `store_inputs_all: {prior_prop_bibles: prop_bible}`
  - These map to the `store_inputs_all` resolver in `DriverEngine._collect_inputs` (`src/cine_forge/driver/engine.py` lines 1026–1049), which already handles empty lists gracefully for bootstrapping

- [ ] **Module: `character_bible_v1` — support refine mode**
  - `_extract_inputs` (`src/cine_forge/modules/world_building/character_bible_v1/main.py` line 281) already extracts inputs by duck-typing. Extend to detect `prior_character_bibles` list.
  - Add `_build_refine_prompt(char_name, entry, canonical_script, scene_index, prior_bible)` that includes the prior `CharacterBible` JSON in the context.
  - In `run_module`, check `params.get("pipeline_mode") == "refine"` and route per-entity to refine prompt when a prior bible for that entity slug is found in `prior_character_bibles`.

- [ ] **Module: `location_bible_v1` — support refine mode** (same pattern as character)
  - File: `src/cine_forge/modules/world_building/location_bible_v1/main.py`

- [ ] **Module: `prop_bible_v1` — support refine mode** (same pattern as character)
  - File: `src/cine_forge/modules/world_building/prop_bible_v1/main.py`

- [ ] **Module: `entity_discovery_v1` — honor `pipeline_mode` param**
  - The module already seeds `current_list` from existing bibles (`src/cine_forge/modules/world_building/entity_discovery_v1/main.py` lines 60–74). In refine mode, make this seeding mandatory rather than opportunistic, and update the discovery prompt to say "EXISTING / USER-VETTED LIST: Do NOT remove these unless you have strong evidence they do not appear in the script at all."

- [ ] **Backend: Add diff endpoint**
  - Add `GET /api/projects/{project_id}/artifacts/{artifact_type}/{entity_id}/diff` with `from_version` and `to_version` query params to `src/cine_forge/api/app.py`
  - Wire to `ArtifactStore.diff_versions` (`src/cine_forge/artifacts/store.py` line 204)
  - Add service method `diff_artifact_versions` in `src/cine_forge/api/service.py`

- [ ] **UI: Run mode toggle**
  - Add a "Run Mode" radio/segmented control (Regenerate / Refine) to the run launch dialog (wherever `start_run` is invoked in the UI — check `ui/src/pages/ProjectRun.tsx` or wherever the run form lives)
  - Wire to the `pipeline_mode` field in the `RunStartRequest` payload

- [ ] **UI: Version history browser on artifact detail pages**
  - The API already exposes `GET /api/projects/{project_id}/artifacts/{artifact_type}/{entity_id}` → `list[ArtifactVersionSummary]` (see `src/cine_forge/api/app.py` line 268)
  - Add a "Version History" section to `ui/src/pages/ArtifactDetail.tsx` (or `EntityDetailPage.tsx`) that lists all versions with health badges and timestamps
  - Add a diff viewer pane using the new diff endpoint — show added/changed/removed fields between any two selected versions
  - Use existing `HealthBadge` (`ui/src/components/HealthBadge.tsx`) for per-version health display

- [ ] **Tests: Unit coverage for refine mode**
  - Test that when `pipeline_mode=refine` and `prior_character_bibles` is non-empty, `character_bible_v1` routes to the refine prompt path
  - Test that when `pipeline_mode=regenerate` (or not set), behavior is identical to current
  - Test that `entity_discovery_v1` seeds from prior bibles in refine mode and uses the updated discovery prompt

- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint` and `pnpm --dir ui run build`
  - [ ] Duplication gate: `pnpm --dir ui run lint:duplication`
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Refine mode only writes new versions (vN+1). Prior versions are never mutated. `propagate_stale_for_new_version` in `DependencyGraph` automatically marks dependents of superseded versions as stale. No data loss path exists.
  - [ ] **T1 — AI-Coded:** Prompt templates are plain strings, easy to inspect and iterate on. Mode switching is a single `pipeline_mode` param — another AI session can understand and modify it.
  - [ ] **T2 — Architect for 100x:** Using `store_inputs_all` (already implemented) rather than a bespoke prior-artifact resolver. No new infrastructure beyond what exists.
  - [ ] **T3 — Fewer Files:** Refine prompt is co-located in the existing module file, not a separate file. Mode routing is a small branch in `run_module`, not a new module.
  - [ ] **T4 — Verbose Artifacts:** Refine-mode artifact metadata should annotate `"pipeline_mode": "refine"` and `"prior_version": N` in the `annotations` dict so the lineage is self-describing.
  - [ ] **T5 — Ideal vs Today:** The ideal is an AI that automatically detects what changed in the script and updates only affected entities. Today's version is simpler: pass the full prior artifact and let the model decide what to preserve. This is the correct first step.

## Files to Modify

- `src/cine_forge/api/models.py` — add `pipeline_mode` field to `RunStartRequest`
- `src/cine_forge/api/service.py` — thread `pipeline_mode` through `start_run` into `runtime_params`; add `diff_artifact_versions` service method
- `src/cine_forge/api/app.py` — add diff endpoint `GET /api/projects/{project_id}/artifacts/{artifact_type}/{entity_id}/diff`
- `configs/recipes/recipe-world-building.yaml` — add `store_inputs_all` for prior bibles to `character_bible`, `location_bible`, `prop_bible` stages
- `src/cine_forge/modules/world_building/character_bible_v1/main.py` — add refine prompt and mode-aware routing
- `src/cine_forge/modules/world_building/location_bible_v1/main.py` — same
- `src/cine_forge/modules/world_building/prop_bible_v1/main.py` — same
- `src/cine_forge/modules/world_building/entity_discovery_v1/main.py` — strengthen seeding logic for refine mode
- `ui/src/pages/ArtifactDetail.tsx` (or `EntityDetailPage.tsx`) — version history panel + diff viewer
- `ui/src/pages/ProjectRun.tsx` (or run launch dialog) — run mode toggle
- `tests/` — new unit tests for refine mode routing in all three bible modules

## Notes

**How `store_inputs_all` works today (already implemented):** `RecipeStage.store_inputs_all` (defined in `src/cine_forge/driver/recipe.py` line 26) instructs the engine to load the latest healthy artifact of a given type for every known entity and pass the full list to the module as `inputs[input_key]`. The resolver is in `DriverEngine._collect_inputs` (`src/cine_forge/driver/engine.py` lines 1026–1049). This already returns an empty list when no prior artifacts exist (the "bootstrapping from nothing" case, noted in a comment at line 1030), making refine and regenerate identical on a fresh project.

**Entity identity in refine mode:** The module must match prior bibles to current candidates by entity slug (`_slugify(entity_name)`) to find the right prior artifact. This slug is already the `entity_id` stored in the artifact — e.g., `character_mariner` → slug `mariner`. See `character_bible_v1` `_slugify` at line 644 and the entity_id passed to `save_artifact` at line 243.

**Version browser API surface:** `ArtifactVersionSummary` already exists in `src/cine_forge/api/models.py` (line 72) and `list_artifact_versions` is already implemented in `src/cine_forge/api/service.py` (line 702) and exposed at `GET /api/projects/{project_id}/artifacts/{artifact_type}/{entity_id}` (app.py line 268). The version browser UI just needs to call this existing endpoint and render results. The diff viewer needs a new endpoint wired to `ArtifactStore.diff_versions` (store.py line 204), which already returns a structured `{path: {kind, from, to}}` dict.

**Stage fingerprint correctness:** When prior bible artifacts are used as `store_inputs_all`, their refs are already included in the `stage_fingerprint` via `upstream_refs` (see `_build_stage_fingerprint` at engine.py line 1228 and `_collect_inputs` returning lineage refs for `store_inputs_all` at line 1047). No additional work needed for cache correctness.

**Open question:** Should refine mode be per-entity-type or all-or-nothing? E.g., "refine characters but regenerate locations." Deferred to a follow-up — for now, `pipeline_mode` applies to all entity types uniformly.

## Plan

{Written by build-story Phase 2 — per-task file changes, impact analysis, approval blockers,
definition of done}

## Work Log

{Entries added during implementation — YYYYMMDD-HHMM — action: result, evidence, next step}

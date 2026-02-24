# Story 020: Editorial Architect and Editorial Direction

**Status**: Done
**Created**: 2026-02-13
**Spec Refs**: 9.1 (Editorial Architect), 12.1 (Editorial Direction), 12.5 (Direction Convergence — editorial input)
**Depends On**: Story 014 (role system foundation), Story 015 (Director — reviews editorial direction), Story 005 (scene extraction)

---

## Goal

Implement the **Editorial Architect** role and its primary output: **editorial direction artifacts**. The Editorial Architect combines the traditional roles of editor and transitions designer — responsible for cut-ability prediction, coverage adequacy, pacing, and transition suggestions.

Editorial direction artifacts are produced per scene (or per act) and consumed by shot planning (Story 025).

---

## Acceptance Criteria

### Editorial Architect Role
- [x] Role definition with:
  - [x] System prompt embodying editorial thinking: rhythm, pacing, coverage, transitions.
  - [x] Tier: structural_advisor.
  - [x] Style pack slot (accepts editorial personality packs).
  - [x] Capability: `text`.
- [x] Role behaviors:
  - [x] Analyzes scenes for editorial structure.
  - [x] Proposes transition strategies between scenes.
  - [x] Evaluates coverage requirements.
  - [x] Identifies montage and parallel editing candidates.

### Editorial Direction Artifacts (Spec 12.1)
- [x] Per-scene editorial direction including:
  - [x] **Scene function**: role in the narrative arc (inciting incident, escalation, climax, resolution, transition).
  - [x] **Pacing intent**: fast/slow, building/releasing tension, breathing room.
  - [x] **Transition strategy**: how to enter and exit the scene (hard cut, dissolve, match cut, sound bridge, smash cut) and why.
  - [x] **Coverage priority**: what the editor will need (e.g., "prioritize close-ups for emotional beats").
  - [x] **Montage/parallel editing candidates**: if applicable.
- [x] Per-act editorial direction (when scoped to an act):
  - [x] Pacing arc across scenes.
  - [x] Turning points.
  - [x] Rhythm across scenes.
- [x] All direction artifacts are immutable, versioned, and carry standard audit metadata.
- [x] Reviewed by Director and Script Supervisor.

### Editorial Direction Module
- [x] Module directory: `src/cine_forge/modules/creative_direction/editorial_direction_v1/`
- [x] Reads scene artifacts, scene index, and project configuration.
- [x] Invokes Editorial Architect role to produce direction artifacts.
- [x] Outputs one editorial direction artifact per scene.

### Schema
- [x] `EditorialDirection` Pydantic schema (+ `EditorialDirectionIndex` for project-level aggregate)
- [x] Schema registered in schema registry.

### Testing
- [x] Unit tests for Editorial Architect role invocation (mocked AI).
- [x] Unit tests for editorial direction generation per scene.
- [x] Unit tests for act-level direction generation.
- [x] Integration test: scenes → editorial direction module → direction artifacts.
- [x] Schema validation on all outputs.

---

## Design Notes

### Editorial Thinking
The Editorial Architect thinks backwards from the edit: "how will this scene cut together?" This means it considers adjacent scenes (what comes before and after), not just the scene in isolation. The transition strategy for scene 5 depends on how scene 4 ends and how scene 6 begins.

### Coverage as a Pre-Requirement for Shot Planning
Coverage priority from editorial direction directly informs shot planning. If the editor says "I need close-ups for the emotional beats and a wide master for safety," the shot planner knows what types of shots to include. This is the primary data flow from editorial to shot planning.

---

## Tasks

- [x] Create Editorial Architect role definition in `src/cine_forge/roles/editorial_architect/`. *(pre-existing from Story 014/016)*
- [x] Write system prompt for Editorial Architect. *(expanded from 2 lines to rich persona)*
- [x] Design and implement `EditorialDirection` schema. *(+ EditorialDirectionIndex)*
- [x] Register schema in schema registry. *(schemas/__init__.py + engine.py)*
- [x] Create `editorial_direction_v1` module (directory, manifest, main.py).
- [x] Implement editorial direction generation per scene. *(3-scene window, parallel extraction)*
- [x] Implement act-level direction aggregation. *(EditorialDirectionIndex with act_structure)*
- [x] Implement Director/Script Supervisor review integration. *(REVIEWABLE_ARTIFACT_TYPES)*
- [x] Create recipe: `configs/recipes/recipe-creative-direction.yaml`.
- [x] Write unit tests. *(9 tests, all passing)*
- [x] Write integration test. *(covered by full mock run test)*
- [x] Run `make test-unit` and `make lint`. *(all pass, 0 errors)*
- [x] Update AGENTS.md with any lessons learned.

---

## Plan

### Exploration Findings

**Role definition already exists.** `src/cine_forge/roles/editorial_architect/role.yaml` is fully defined (tier: structural_advisor, capability: text, style_pack_slot: accepts, permissions: scene/scene_index/timeline/track_manifest). Two style packs exist (generic + schoonmaker). No role Python code needed — roles are data-driven via YAML.

**Module pattern is well-established.** Follow `character_bible_v1` as the template: `module.yaml` + `main.py` with `run_module(inputs, params, context)`. Discovery is automatic via `module.yaml` glob. New stage directory `creative_direction/` needed (doesn't exist yet).

**Schema registration is manual.** Add to `schemas/__init__.py` + `driver/engine.py` `__init__` method (line ~136).

**Key architectural insight:** The story says "invokes Editorial Architect role to produce direction artifacts" — but the role system is designed for structured discussion/review/canon-gating, not for bulk artifact generation. The actual module should use `call_llm()` directly (like character_bible does) with the Editorial Architect's system prompt as persona context. The role YAML defines the persona; the module uses it for prompt construction. This keeps the pattern consistent with all existing modules.

**Adjacent scene context is critical.** The spec says the Editorial Architect "thinks backwards from the edit" and transition strategy for scene N depends on scenes N-1 and N+1. The module must pass 3-scene windows (prev/current/next) to the LLM.

**Files that will change:**
- `src/cine_forge/schemas/editorial_direction.py` — NEW
- `src/cine_forge/schemas/__init__.py` — add exports
- `src/cine_forge/driver/engine.py` — register schema
- `src/cine_forge/modules/creative_direction/editorial_direction_v1/module.yaml` — NEW
- `src/cine_forge/modules/creative_direction/editorial_direction_v1/main.py` — NEW
- `src/cine_forge/roles/editorial_architect/role.yaml` — enhance system prompt
- `configs/recipes/recipe-creative-direction.yaml` — NEW
- `ui/src/lib/artifact-meta.ts` — add `editorial_direction` entry
- `tests/unit/test_editorial_direction_module.py` — NEW

**Files at risk:** None significant — this is purely additive. No existing code changes except `schemas/__init__.py` (new import), `engine.py` (new register line), and `artifact-meta.ts` (new entry).

### Implementation Order

**Task 1: Enhance Editorial Architect system prompt** (`role.yaml`)
- The current prompt is 2 lines. Spec 9.1 requires editorial thinking: rhythm, pacing, coverage, transitions, cut-ability prediction. Expand to a rich editorial persona prompt.
- No structural changes — just text in the `system_prompt` field.

**Task 2: Create `EditorialDirection` schema** (`schemas/editorial_direction.py`)
- Per-scene schema per the story's AC, plus an `EditorialDirectionIndex` aggregate (like SceneIndex) for the project-level summary.
- Fields: scene_id, scene_function, pacing_intent, transition_in/out + rationale, coverage_priority, montage_candidates, parallel_editing_notes, act_level_notes, confidence.
- Register in `schemas/__init__.py` and `driver/engine.py`.

**Task 3: Create module manifest** (`module.yaml`)
- Stage: `creative_direction`
- Inputs: `scene_index`, `canonical_script`
- Optional: `project_config`
- Outputs: `editorial_direction`
- Parameters: work_model, escalate_model, skip_qa, concurrency, batch_size

**Task 4: Implement `main.py`** — the core module
- Extract scene index entries + canonical script text
- For each scene, build a 3-scene window (prev/current/next) for transition reasoning
- Construct editorial analysis prompt using the role's persona
- Call `call_llm()` with `EditorialDirection` response schema
- Optional QA pass (verify_model)
- Support `model="mock"` for tests
- Use `announce_artifact` for streaming progress
- Parallel extraction via ThreadPoolExecutor (same pattern as character_bible)
- Produce per-scene `editorial_direction` artifacts + one project-level index

**Task 5: Create recipe** (`recipe-creative-direction.yaml`)
- Single stage: `editorial_direction` module
- `store_inputs`: canonical_script, scene_index
- `store_inputs_optional`: project_config

**Task 6: Add UI artifact metadata** (`artifact-meta.ts`)
- Add `editorial_direction` entry with appropriate icon/label/color

**Task 7: Write unit tests**
- Test mock mode produces valid schema output
- Test 3-scene window construction (first/middle/last scenes)
- Test act-level aggregation
- Schema validation on all outputs

**Task 8: Write integration test**
- scenes → editorial_direction module → validated artifacts

**Task 9: Run checks, update story**
- `make test-unit`, ruff lint, verify

### Scope Decision: Director/Script Supervisor Review

The AC says "Reviewed by Director and Script Supervisor." The canon review gate from Story 019 already handles this — `REVIEWABLE_ARTIFACT_TYPES` in engine.py triggers canon review when those artifact types appear. I'll add `editorial_direction` to that set. No custom review logic needed.

---

## Work Log

*(append-only)*

20260223-1400 — Exploration complete. Role definition already existed from Story 014/016. Module pattern follows character_bible_v1. Key insight: modules use call_llm() directly, not the role runtime. 3-scene window needed for transition reasoning per spec.

20260223-1430 — Implementation complete. All files created/modified:
- Enhanced `role.yaml` system prompt: 2 lines → rich editorial persona covering cut-ability, coverage, pacing, transitions, montage.
- Added `editorial_direction` to role permissions.
- Created `EditorialDirection` + `EditorialDirectionIndex` schemas in `schemas/editorial_direction.py`.
- Registered schemas in `__init__.py` and `engine.py`.
- Added `editorial_direction` to `REVIEWABLE_ARTIFACT_TYPES` for Director/Script Supervisor review.
- Created `creative_direction/editorial_direction_v1/` module with manifest + main.py.
- Module features: 3-scene sliding window, parallel ThreadPoolExecutor extraction, mock support, announce_artifact streaming, QA pass with escalation, project-level index generation.
- Created `recipe-creative-direction.yaml` with store_inputs for canonical_script + scene_index.
- Added `editorial_direction` + `editorial_direction_index` to UI `artifact-meta.ts` (Scissors icon, pink color).
- 9 unit tests: mock output validation, window construction (first/middle/last), full module run, missing inputs, empty scenes, schema validation, announce callback.

Evidence:
- `pytest -m unit`: all pass (full suite)
- `ruff check src/ tests/`: 0 errors
- `tsc -b`: exit 0
- `pnpm lint`: 0 errors (7 pre-existing warnings)
- Dry-run: `recipe-creative-direction.yaml` validates, module discovered.

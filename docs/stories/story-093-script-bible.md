# Story 093: Script Bible Artifact

**Status**: Done
**Created**: 2026-02-27
**Source**: ADR-003, Decisions #1/#11/#14 (story-lane always runs on import), #12 (script bible artifact)
**Spec Refs**: 4.5 (Script Bible), 4.6 (Two-Lane Architecture)
**Ideal Refs**: R1 (story understanding), R8 (production artifacts)
**Depends On**: Story 003 (story ingestion), Story 004 (script normalization)

---

## Goal

Add a **script bible** as the first artifact derived from the script, sitting between ingestion and entity extraction. The script bible captures the high-level story understanding: logline, synopsis, act structure, themes, and narrative arc. This is a story-lane artifact — cheap, always generated on import.

## Why (Ideal Alignment)

The Ideal says CineForge must understand the story completely (R1). Currently the pipeline jumps from raw script to scene extraction and entity extraction. The script bible fills the gap — it captures the macro-level story understanding that informs everything downstream. Every concern group, every role, every creative decision references "what is this story about?" The script bible is that answer.

The project IS the story (ADR-003 Decision #12). The script bible is the story's identity document.

## Acceptance Criteria

- [x] Script bible generated automatically on script import (story-lane, always runs)
- [x] Contains: logline, synopsis (1-3 paragraphs), act structure (acts and turning points), themes, narrative arc, genre/tone confirmation
- [x] Stored as immutable versioned artifact
- [x] Script revision triggers script bible re-generation with entity reconciliation (R15)
- [x] All downstream roles and concern groups can reference the script bible
- [x] Schema validated
- [x] Script page header displays script bible: logline as subtitle, genre/tone as badges, expandable panel for full synopsis, act structure, themes, arc, and conflict

---

## Tasks

- [x] **T1: ScriptBible schema** — Create `src/cine_forge/schemas/script_bible.py` with Pydantic model. Fields: logline, synopsis, act_structure (list of acts with turning points), themes (list with scene refs), narrative_arc, genre_tone, protagonist_journey, central_conflict.
- [x] **T2: Schema registration** — Export from `schemas/__init__.py`, register in `driver/engine.py`.
- [x] **T3: Module scaffold** — Create `src/cine_forge/modules/ingest/script_bible_v1/` with `module.yaml`, `main.py`, `__init__.py`. Single LLM call: canonical_script → ScriptBible. Model: Sonnet (cheap, fast).
- [x] **T4: Recipe integration** — Add `script_bible` stage to `recipe-ingest-extract.yaml` after `normalize`, parallel with `breakdown_scenes`.
- [x] **T5: Pipeline graph** — Add `script_bible` node to `pipeline/graph.py` in the `script` phase. Add to `NODE_FIX_RECIPES`.
- [x] **T6: UI artifact metadata** — Add `script_bible` entry to `ui/src/lib/artifact-meta.ts`.
- [x] **T7: API endpoint** — Generic artifact endpoints serve script_bible automatically. Added `useScriptBible` hook in `ui/src/lib/hooks.ts`.
- [x] **T8: Script page header redesign** — Logline as subtitle, genre/tone badges, collapsible ScriptBiblePanel with synopsis, acts, themes, conflict, journey, arc, setting.
- [x] **T9: Unit tests** — 7 tests: mock happy path, metadata, cost, announce callback, empty/missing input errors, schema round-trip.
- [x] **T10: Static verification** — Ruff, pytest (351 passed), tsc, pnpm build all pass.
- [x] **T11: Runtime smoke test** — Module produces valid ScriptBible from store canonical_script. Schema registered in engine. Pipeline graph includes script_bible node.

## Plan

### Architecture

The script bible is a **story-lane artifact** — cheap, always generated on import. It sits logically between normalization and entity extraction per spec §4.6.

**Data flow:**
```
normalize (canonical_script) ──┬──→ script_bible_v1 → script_bible artifact
                               └──→ scene_breakdown_v1 → scene/scene_index artifacts
```

script_bible and scene_breakdown run in **parallel** — both consume canonical_script, neither depends on the other. The script bible becomes available for downstream consumption by scene_analysis (world_building recipe) and all concern groups.

### Files Changed

| File | Action | What |
|------|--------|------|
| `src/cine_forge/schemas/script_bible.py` | **NEW** | ScriptBible Pydantic model |
| `src/cine_forge/schemas/__init__.py` | EDIT | Export + __all__ |
| `src/cine_forge/driver/engine.py` | EDIT | `schemas.register("script_bible", ScriptBible)` |
| `src/cine_forge/modules/ingest/script_bible_v1/module.yaml` | **NEW** | Module manifest |
| `src/cine_forge/modules/ingest/script_bible_v1/main.py` | **NEW** | Module entry point |
| `src/cine_forge/modules/ingest/script_bible_v1/__init__.py` | **NEW** | Empty init |
| `configs/recipes/recipe-ingest-extract.yaml` | EDIT | Add script_bible stage |
| `src/cine_forge/pipeline/graph.py` | EDIT | New node + phase + fix recipe |
| `ui/src/lib/artifact-meta.ts` | EDIT | Display metadata |
| `src/cine_forge/api/routers/*.py` | EDIT | Script bible API endpoint (if needed) |
| `ui/src/pages/ScriptPage.tsx` (or equivalent) | EDIT | Header redesign: logline subtitle, genre/tone badges, expandable bible panel |
| `tests/unit/test_script_bible_module.py` | **NEW** | Unit tests |

### Schema Design

```python
class ActStructure(BaseModel):
    act_number: int
    title: str
    start_scene: str          # Scene heading or "Opening"
    end_scene: str             # Scene heading or "End"
    summary: str
    turning_points: list[str]

class ThematicElement(BaseModel):
    theme: str
    description: str
    evidence: list[str]        # Scene refs or quotes

class ScriptBible(BaseModel):
    title: str
    logline: str               # One sentence
    synopsis: str              # 1-3 paragraphs
    act_structure: list[ActStructure]
    themes: list[ThematicElement]
    narrative_arc: str         # Overall story shape description
    genre: str
    tone: str
    protagonist_journey: str   # Protagonist's transformation
    central_conflict: str
    setting_overview: str      # Time/place context
```

### LLM Strategy

Single Sonnet call with the full canonical script text. Structured output via `response_schema=ScriptBible`. QA pass optional (skip by default — the script bible is a synthesis artifact, not a classification task; structural validation is sufficient).

### Risk Assessment

- **Low risk**: No existing code changes semantics. All changes are additive.
- **AC4 (re-generation on revision)**: Handled by existing dependency graph — when canonical_script gets a new version, script_bible is marked stale. No new code needed for this.
- **AC5 (downstream reference)**: Downstream modules use `store_inputs: {script_bible: script_bible}`. No code change needed — the artifact just needs to exist in the store.

---

## Work Log

*(append-only)*

20260227 — Story created per ADR-003 propagation.
20260227 — Promoted to Pending with full tasks and plan.
20260227 — Implementation complete:
  - Schema: `src/cine_forge/schemas/script_bible.py` — ScriptBible, ActStructure, ThematicElement
  - Module: `src/cine_forge/modules/ingest/script_bible_v1/` — single Sonnet LLM call, mock support
  - Recipe: Added `script_bible` stage to `recipe-ingest-extract.yaml` parallel with `breakdown_scenes`
  - Pipeline graph: New `script_bible` node in `script` phase, `NODE_FIX_RECIPES` mapping
  - Driver: `ScriptBible` registered in `SchemaRegistry`
  - UI: `BookOpen` icon in artifact-meta.ts, `useScriptBible` hook, `ScriptBiblePanel` component
    in ProjectHome.tsx — logline as subtitle, genre/tone badges, expandable panel for full analysis
  - Tests: 7 unit tests, all 351 unit tests pass, ruff clean, tsc clean, pnpm build clean
  - Smoke: Module runs against real store data, schema validates, pipeline graph correct
20260227 — Bug fix: script_bible stage was added to wrong recipe (`recipe-ingest-extract.yaml`
  instead of `recipe-mvp-ingest.yaml`). Fixed — stage now in the correct production recipe.
20260227 — Recipe cleanup: Moved 4 legacy partial-ingest recipes (recipe-ingest-only,
  recipe-ingest-normalize, recipe-ingest-extract, recipe-ingest-extract-config) from
  `configs/recipes/` to `tests/fixtures/recipes/`. These were test fixtures masquerading
  as production recipes. Updated 7 test files. Also fixed stale `stages["extract"]`
  assertions in timeline/track tests → `stages["breakdown_scenes"]` (leftover from
  Story 062 rename). Ruff clean, 351 unit tests pass.
20260227 — Stage ordering: Single source of truth fix.
  - Problem: Three hardcoded stage-ordering systems (recipe YAML, `RECIPE_STAGE_ORDER`
    in constants.ts, `STAGE_DESCRIPTIONS` in chat-messages.ts) kept drifting apart.
  - Root cause: `json.dump(..., sort_keys=True)` in `_write_run_state` alphabetized
    the stages dict keys, destroying insertion order.
  - Fix: Added explicit `stage_order: list[str]` to `RunState` (state.py), populated
    from recipe stages in engine.py. Frontend reads it via API. Deleted hardcoded
    `RECIPE_STAGE_ORDER` from constants.ts. `getOrderedStageIds` now uses backend order.
  - Also added `script_bible` to `STAGE_DESCRIPTIONS` and `ARTIFACT_NAMES`.
  - Reordered recipe stages: `breakdown_scenes` before `script_bible` (fast before slow).
20260227 — ScriptBiblePanel UI polish:
  - Removed tone from header pill (tone is a full sentence, not badge-appropriate).
  - Added tone as italic text at top of expanded panel.
  - Constrained panel content width with `max-w-3xl`.
  - Bumped act structure text from `text-xs` to `text-sm`, improved spacing/padding.
  - Verified in browser — all sections render correctly.
20260227 — Final verification: 351 unit tests pass, ruff clean, tsc clean, pnpm build clean.

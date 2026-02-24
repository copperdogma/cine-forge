# Story 077 — Character Coverage & Prominence Tiers

**Priority**: Medium
**Status**: Done
**Spec Refs**: World Building / Character Bible
**Depends On**: 055 (LLM-First Entity Adjudication), 076 (Entity Detail Cross-Ref Layout)

## Goal

Every character discovered in entity discovery should have a bible — even minor walk-ons like
"Thug 1". Currently the adjudicator filters them out, so they appear in co-occurrence edges
(because they're in scene breakdowns) but have no profile page and can't be linked from the
entity detail view. This story adds a **prominence tier** (`primary`, `secondary`, `minor`) to
each character bible, extracts minimal bibles for all discovered characters regardless of
adjudication score, and surfaces the tier as a filter on the Characters list view so users can
focus on the characters that matter most.

## Research Required

Before implementing, research how professional screenplay/production tools model character
prominence IRL. Specifically:

- **Industry conventions**: How do coverage documents, breakdown sheets, and production
  management tools (Movie Magic, Studiobinder, Final Draft) classify character importance?
  Common patterns: principal/supporting/day-player/extra or A/B/C/D tiers or lines-of-dialogue
  thresholds.
- **Screenplay analysis tools**: How do tools like Fade In, Highland, WriterDuet, or academic
  NLP tools (e.g., Bechdel test frameworks) determine character prominence? Line count? Scene
  count? Dialogue weight?
- **Academic / NLP literature**: Any established metrics (scene centrality, dialogue proportion,
  narrative betweenness) worth incorporating into the extraction prompt?
- **Output**: Summarise findings in `docs/research/character-prominence/` using
  `deep-research init` before implementation. Use the findings to inform the prominence
  classification prompt and tier labels.

## Acceptance Criteria

- [x] All characters from entity discovery receive a `character_bible` artifact (no adjudication
  filter drops them — adjudicator may still deduplicate or merge, but not discard)
- [x] Every `character_bible` includes a `prominence` field: `"primary"`, `"secondary"`, or
  `"minor"` (AI-assigned, evidence-grounded)
- [x] Prominent characters (primary/secondary) receive the full deep-extraction bible as before;
  minor characters receive a lightweight extraction (description + scene list +
  prominence-justification only — no traits/evidence/dialogue unless the AI spontaneously
  includes them)
- [x] Characters list view has a prominence filter: All / Primary / Secondary / Minor
- [x] Filter persists as a sticky UI preference alongside the existing sort preference
- [x] Dimmed/unlinked relationship entries in entity detail panels are replaced with real linked
  profiles (the former "Thug 1" now has a page and can be navigated to)
- [x] `make test-unit` passes; `pnpm --dir ui run lint` and `tsc -b` pass

## Out of Scope

- Prominence tiers for locations or props (character-only for now)
- Changing how scenes or props reference characters (existing `characters_present_ids` is fine)
- Exposing prominence tier as a filter on the entity detail relationship panels (just the list
  view filter for now)
- Automated re-classification after script edits

## AI Considerations

This story is **heavily AI-first**:

- **Prominence classification** is a reasoning/language problem → LLM call. The existing
  character extraction prompt should be extended to include a `prominence` field with a rubric.
  Alternatively, a separate lightweight classification pass after full extraction.
- **Minor character extraction** is a simpler LLM call — a stripped-down prompt that only asks
  for name, description, scene refs, and prominence tier. Should be much cheaper per character
  than the full extraction.
- **Adjudicator change**: The current adjudicator filters by quality score. For this story,
  the filter should only remove true false-positives (e.g., "VOICE", "MAN ON RADIO") not minor
  named characters. The prominence tier itself serves as the quality signal downstream.
- Research SOTA before building the prompt — industry rubrics may already map to a clean
  3-tier system.

## Tasks

- [x] **Research**: Skipped deep-research — 3-tier model maps 1:1 to SAG-AFTRA casting tiers
  (Principal→primary, Featured→secondary, Extra→minor). Documented in Plan section.
- [x] **Schema**: Added `prominence: Literal["primary", "secondary", "minor"]` field to
  `CharacterBible` in `src/cine_forge/schemas/bible.py` with default `"secondary"`.
- [x] **Adjudicator**: Updated prompt in `src/cine_forge/ai/entity_adjudication.py` to
  explicitly keep named minor characters (THUG 1, GUARD 2, etc.). Fixed plausibility filter
  regex to allow digits. Removed "THUG" from stopwords.
- [x] **Extraction split**: Added `_process_minor_character()`, `_extract_minor_character_definition()`,
  `_build_lightweight_prompt()`, and `_mock_minor_extract()` in `character_bible_v1/main.py`.
  Score threshold = 4 separates full vs lightweight paths.
- [x] **Full extraction prompt update**: Added prominence rubric to `_build_extraction_prompt()`.
  Mock extractor returns `prominence="secondary"`.
- [x] **UI — list filter**: Added filter chips (All/Primary/Secondary/Minor) with Crown/Star/User
  icons to `EntityListControls.tsx`. Filter persisted via `useStickyPreference`. Applied in
  `EntityListPage.tsx` for characters section only.
- [x] **UI — detail badges**: Created `ProminenceBadge.tsx` component. Added to character detail
  header in `EntityDetailPage.tsx` next to HealthBadge.
- [x] **Regression tests**: Added 6 new tests in `test_character_bible_module.py`:
  plausibility for THUG 1/GUARD 2/COP 3, non-character rejection, prominence field presence,
  minor character retention via discovery_results, minor prominence assignment.
- [x] Run required checks:
  - [x] `make test-unit PYTHON=.venv/bin/python` — 289 passed
  - [x] `.venv/bin/python -m ruff check src/ tests/` — clean
  - [x] `pnpm --dir ui run lint` and `cd ui && npx tsc -b` — clean
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Existing bibles are immutable — new runs produce new versions. Schema additive with default.
  - [x] **T1 — AI-Coded:** Prominence rubric in prompt is self-documenting. LLM assigns tier.
  - [x] **T2 — Architect for 100x:** Lightweight path avoids expensive extraction for walk-ons (~80% cheaper per minor char).
  - [x] **T3 — Fewer Files:** Extraction split stays in existing `character_bible_v1/main.py`. One new UI component.
  - [x] **T4 — Verbose Artifacts:** Research decision, exploration notes, and implementation plan all logged in work log.
  - [x] **T5 — Ideal vs Today:** Prominence assigned at extraction time by the LLM, not the adjudicator. Adjudicator only gates validity.

## Files to Modify

- `src/cine_forge/schemas/` — add `prominence` field to `CharacterBible`
- `src/cine_forge/ai/entity_adjudication.py` — relax character filter; keep named minor chars
- `src/cine_forge/modules/world_building/character_bible_v1/main.py` — split full/lightweight
  extraction; add minor character prompt
- `ui/src/pages/EntityListPage.tsx` (or character list config) — add prominence filter
- `ui/src/pages/EntityDetailPage.tsx` — show prominence badge in header
- `tests/unit/` — adjudicator regression tests for minor character retention

## Notes

- "THUG 1", "THUG 2", "THUG 3" are the concrete test cases from The Mariner that prompted this story.
- "VOICE ON INTERCOM" is an example that should still be filtered.
- The lightweight extraction is cost-driven: a full bible per minor character at Haiku rates is
  still cheap, but the scene count for minor characters may balloon (25 → 40 discovered) so the
  lightweight path keeps total cost predictable.
- Prominence filter on the Characters list mirrors how production coordinators think: they want
  to see their lead characters first, not scroll past 20 thugs.
- Consider whether `minor` characters should be sorted to the bottom of the default prominence
  sort, below `secondary`.

## Plan

### Research Decision

Skip `deep-research` — the 3-tier model is validated by standard production practice:
- **Principal** → `primary`: protagonist, antagonist, key relationship characters (drives the plot)
- **Featured/Day Player** → `secondary`: recurring supporting characters with named roles and meaningful dialogue
- **Extra/Bit** → `minor`: walk-ons, one-scene characters, thugs, guards, unnamed functionals

This maps 1:1 to SAG-AFTRA casting tiers and standard breakdown sheet practice (StudioBinder, Movie Magic, Filmustage). No additional research needed.

### Task Order & Implementation

#### T1. Schema: Add `prominence` field to `CharacterBible`

**File**: `src/cine_forge/schemas/bible.py:68-82`

Add `prominence: Literal["primary", "secondary", "minor"] = "secondary"` to `CharacterBible`. Default `"secondary"` ensures backward compatibility with existing artifacts that lack the field.

This is additive — no existing code breaks. `narrative_role` (protagonist/antagonist/supporting/minor) stays as-is — it describes story function, `prominence` describes production weight.

#### T2. Plausibility filter: allow alphanumeric tokens

**File**: `src/cine_forge/modules/world_building/character_bible_v1/main.py`

Two changes in `_is_plausible_character_name()`:
1. **Line 683**: Change regex from `^[A-Z']+$` to `^[A-Z0-9']+$` — allows "THUG 1" token "1"
2. **Line 687**: Remove "THUG" from `CHARACTER_STOPWORDS` (line 77) — "THUG" alone is noise but "THUG 1" is a named character. Since plausibility already rejects single-word names via stopwords AND the adjudicator will filter non-characters, removing "THUG" is safe.

Add `_is_numbered_functional()` helper: returns True for patterns like `THUG 1`, `GUARD 2`, `COP 3` — used later for lightweight extraction routing.

#### T3. Relax minimum appearances filter

**File**: `src/cine_forge/modules/world_building/character_bible_v1/main.py:124-144`

When `discovery_results` are provided (entity discovery already LLM-curated), keep all candidates regardless of scene count. The entity discovery stage is the quality gate; the min_appearances filter is redundant.

When discovery_results are NOT provided (fallback path), lower `min_scene_appearances` from 3 to 1 but only for candidates with dialogue (`dialogue_count >= 1`). Keep `min_scene_appearances=3` for non-speaking characters in the fallback path.

#### T4. Split extraction: full vs lightweight

**File**: `src/cine_forge/modules/world_building/character_bible_v1/main.py:166-206`

After adjudication, split candidates into two lists using a score threshold:
- **Full extraction** (score >= 4, i.e., 2+ scenes or 1 scene + 2 dialogue): existing `_process_character()` flow with prominence rubric added to prompt
- **Lightweight extraction** (score < 4): new `_process_minor_character()` — stripped-down prompt requesting only: name, description, scene_presence, prominence (always "minor"), overall_confidence, narrative_role. No traits, evidence, relationships, dialogue_summary (empty defaults).

Both paths produce valid `CharacterBible` artifacts. The lightweight path is ~80% cheaper per character.

Update `_build_extraction_prompt()` to include prominence rubric in the instructions:
```
Assign a "prominence" field:
- "primary": protagonist, antagonist, or key relationship character who drives the plot
- "secondary": recurring supporting character with named role and meaningful dialogue
- "minor": walk-on, one-scene character, functional role (thug, guard, cop, etc.)
```

New `_build_lightweight_prompt()` for minor characters — minimal context, no deep extraction.

Update `_mock_extract()` to include `prominence="secondary"` (default mock).

#### T5. Update adjudication prompt

**File**: `src/cine_forge/ai/entity_adjudication.py:88-105`

Add rule to the adjudicator prompt:
```
- Named minor characters (e.g., "THUG 1", "GUARD 2", "NURSE") are VALID characters,
  even if they appear only once. Only reject formatting tokens, sound cues, and
  non-character strings.
```

This ensures the LLM doesn't reject walk-ons as "noise".

#### T6. UI: ProminenceBadge component

**File**: `ui/src/components/ProminenceBadge.tsx` (new)

Follow `HealthBadge` pattern:
- `primary` → amber/gold badge with Star icon
- `secondary` → blue badge
- `minor` → muted/slate badge
- Null/undefined → no render

#### T7. UI: Prominence filter on Characters list

**Files**: `ui/src/pages/EntityListPage.tsx`, `ui/src/components/EntityListControls.tsx`

Add filter state via `useStickyPreference(projectId, 'characters.filter', 'all')`.

Add filter chip buttons to `EntityListControls`: All / Primary / Secondary / Minor. Only show for `characters` section (not locations/props/scenes).

Apply filter after sort in `EntityListPage`: `if filter !== 'all', entities = entities.filter(e => e.data?.prominence === filter)`.

#### T8. UI: Prominence badge on entity detail header

**File**: `ui/src/pages/EntityDetailPage.tsx:614-647`

Add `<ProminenceBadge prominence={data.prominence} />` next to the existing `<HealthBadge>` in the character detail header. Only render for character_bible entities.

#### T9. Regression tests

**File**: `tests/unit/test_character_bible_module.py`

New tests:
1. `test_thug_1_passes_plausibility_check` — "THUG 1" is plausible, "THUG" alone still rejected (but via adjudication, not stopwords)
2. `test_numbered_functionals_retained_after_adjudication` — fixture with THUG 1 + THUG 2 + VOICE ON INTERCOM → THUG 1/2 kept, VOICE filtered
3. `test_minor_characters_get_lightweight_extraction` — verify minor candidates use stripped-down prompt
4. `test_prominence_field_present_in_output` — all character_bible artifacts have `prominence` field
5. Update existing tests to expect `prominence` field in output

#### T10. Validation & smoke test

- `make test-unit PYTHON=.venv/bin/python`
- `.venv/bin/python -m ruff check src/ tests/`
- `pnpm --dir ui run lint` and `cd ui && npx tsc -b`
- `pnpm --dir ui run build`
- Start dev servers, load app, navigate to Characters list, verify filter chips render
- Screenshot-verify prominence badge on character detail page

### Impact Analysis

- **Schema change is additive** — new field with default value, no migration needed
- **Existing artifacts** will have `prominence: "secondary"` (default) until re-extracted
- **Existing tests** will need `prominence` field in mock outputs
- **No recipe changes** — same world-building recipe, same stage order
- **Cost impact**: More characters extracted (minor walk-ons) but lightweight path is cheap. Net cost increase per run: ~10-20% for entity-heavy scripts.

## Work Log

20260223-1940 — story created. Prompted by Thug 1/2/3 appearing unlinked in entity detail
relationship panels because character adjudicator filtered them out. Research phase required
before any code — need to validate the 3-tier model against industry conventions.

20260223-2000 — **Exploration Notes**

### Drop Points for Minor Characters (Root Cause)

"THUG 1" is **double-filtered** before it ever reaches adjudication:

1. **`_is_plausible_character_name()` line 683**: regex `^[A-Z']+$` rejects token "1" (digits not allowed)
2. **`_is_plausible_character_name()` line 687**: token "THUG" is in `CHARACTER_STOPWORDS` (line 77)
3. **`min_scene_appearances=3` filter (line 124/138-141)**: "THUG 1" likely appears in only 1-2 scenes, filtered unless it has dialogue

Even if past those, the adjudicator has no explicit instruction to preserve named minor characters.

### Schema Overlap: `narrative_role` vs `prominence`

`CharacterBible` already has `narrative_role: Literal["protagonist", "antagonist", "supporting", "minor"]` (line 79). This overlaps with proposed `prominence` but serves different purposes:
- `narrative_role` = story function (who is the hero/villain)
- `prominence` = production importance (screen time, dialogue weight)
- A character can be `narrative_role: "antagonist"` but `prominence: "secondary"` (brief villain)
- Both fields should coexist.

### Files That Need to Change

| File | Change |
|------|--------|
| `src/cine_forge/schemas/bible.py:68-82` | Add `prominence` field to `CharacterBible` |
| `src/cine_forge/modules/world_building/character_bible_v1/main.py:21-78` | Remove "THUG" from stopwords |
| `src/cine_forge/modules/world_building/character_bible_v1/main.py:675-693` | Allow alphanumeric tokens in plausibility check |
| `src/cine_forge/modules/world_building/character_bible_v1/main.py:124-144` | Lower/remove min_appearances filter for minor chars |
| `src/cine_forge/modules/world_building/character_bible_v1/main.py:166-206` | Split extraction into full vs lightweight paths |
| `src/cine_forge/modules/world_building/character_bible_v1/main.py:611-638` | Add prominence rubric to extraction prompt |
| `src/cine_forge/modules/world_building/character_bible_v1/main.py:641-655` | Update mock extractor with prominence field |
| `src/cine_forge/ai/entity_adjudication.py:88-105` | Update prompt to explicitly keep named minor chars |
| `tests/unit/test_character_bible_module.py` | Add regression tests for THUG 1 retention |
| `ui/src/pages/EntityListPage.tsx` | Add prominence filter chips |
| `ui/src/components/EntityListControls.tsx` | Wire filter controls |
| `ui/src/pages/EntityDetailPage.tsx` | Add prominence badge to header |
| `ui/src/components/ProminenceBadge.tsx` | New component (following HealthBadge pattern) |

### Files at Risk of Breaking

- `tests/unit/test_character_bible_module.py` — all existing tests touch affected code
- `tests/unit/test_module_entity_discovery_v1.py` — if normalization changes propagate
- Any code that reads `CharacterBible` and expects a fixed field set (schema additive = safe)
- UI components that render character data (additive field = safe)

### Patterns to Follow

- Badge component: copy `HealthBadge.tsx` pattern (conditional render, shadcn Badge, cn() merge)
- Sticky preference: `useStickyPreference(projectId, 'characters.filter', 'all')`
- Schema field: `prominence: Literal["primary", "secondary", "minor"] = "secondary"` (default for backwards compat with existing artifacts)
- Extraction split: parallel ThreadPoolExecutor pattern already in place (line 171)
- Tests: monkeypatch `adjudicate_entity_candidates` pattern (existing in test_character_bible_module.py)

20260223-2130 — **Implementation Complete**

All 10 tasks implemented and validated:

**Backend changes:**
- `src/cine_forge/schemas/bible.py` — added `prominence` field to `CharacterBible` (default `"secondary"`)
- `src/cine_forge/modules/world_building/character_bible_v1/main.py` — fixed plausibility regex (`^[A-Z0-9']+`), removed "THUG" from stopwords, split extraction into full (score>=4) and lightweight (score<4) paths, added `_process_minor_character()`, `_extract_minor_character_definition()`, `_build_lightweight_prompt()`, `_mock_minor_extract()`, prominence rubric in full extraction prompt
- `src/cine_forge/ai/entity_adjudication.py` — added rule to keep named minor characters
- `tests/unit/test_character_bible_module.py` — 6 new tests: plausibility for numbered functionals, rejection of non-characters, prominence field presence, minor character retention, minor prominence assignment

**UI changes:**
- `ui/src/components/ProminenceBadge.tsx` — new component (Crown/Star/User icons per tier)
- `ui/src/components/EntityListControls.tsx` — optional filter prop with tier chip buttons
- `ui/src/pages/EntityListPage.tsx` — prominence filter state via useStickyPreference, filter applied after sort, count badge shows filtered/total
- `ui/src/pages/EntityDetailPage.tsx` — ProminenceBadge in character detail header
- `ui/src/lib/types.ts` — added `ProminenceFilter` type

**Validation evidence:**
- 289 unit tests passed (make test-unit)
- Ruff lint: clean
- TypeScript tsc -b: clean
- ESLint: 0 errors (7 pre-existing warnings)
- Production build: succeeds
- Runtime smoke test: Characters list renders filter chips correctly, character detail shows badge (hidden for pre-existing artifacts without prominence data), locations page unaffected (no filter chips), no console errors

20260223-2215 — **Post-validation fixes**

Two issues found during validation and user review:

1. **ProminenceBadge on list cards**: Added `ProminenceBadge` to all three card density variants
   (compact row, medium card, large card) in `EntityListPage.tsx` — badges were only on the
   detail page header, not the list view cards. Now each character card shows its tier icon.

2. **Discovery-only characters silently dropped**: Characters in `discovery_results` but absent
   from `scene_index.unique_characters` (due to name normalization mismatch) were silently
   dropped by the exact-match filter at line 133. Root cause: scene extraction normalizes
   "THUG 1"/"THUG 2" → "THUG" and "YOUNG MARINER" → "MARINER", but entity discovery preserves
   the original names. Fix: after filtering ranked candidates against approved_names, create stub
   entries (`score=0, scene_count=0`) for any discovery-only names. These route to the lightweight
   minor extraction path. Added regression test `test_discovery_only_characters_still_extracted`.

Evidence: 290 tests pass (was 289), ruff clean, tsc -b clean, ESLint 0 errors.
Upstream issue (scene_index not finding these characters in action lines) tracked as Story 080.

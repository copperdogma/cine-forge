# Story 077 — Character Coverage & Prominence Tiers

**Priority**: Medium
**Status**: Pending
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

- [ ] All characters from entity discovery receive a `character_bible` artifact (no adjudication
  filter drops them — adjudicator may still deduplicate or merge, but not discard)
- [ ] Every `character_bible` includes a `prominence` field: `"primary"`, `"secondary"`, or
  `"minor"` (AI-assigned, evidence-grounded)
- [ ] Prominent characters (primary/secondary) receive the full deep-extraction bible as before;
  minor characters receive a lightweight extraction (description + scene list +
  prominence-justification only — no traits/evidence/dialogue unless the AI spontaneously
  includes them)
- [ ] Characters list view has a prominence filter: All / Primary / Secondary / Minor
- [ ] Filter persists as a sticky UI preference alongside the existing sort preference
- [ ] Dimmed/unlinked relationship entries in entity detail panels are replaced with real linked
  profiles (the former "Thug 1" now has a page and can be navigated to)
- [ ] `make test-unit` passes; `pnpm --dir ui run lint` and `tsc -b` pass

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

- [ ] **Research**: Run `deep-research init "character prominence tiers in screenwriting"` →
  edit prompt → run → synthesize findings into a short ADR-style decision in
  `docs/research/character-prominence/`. Define the 3-tier rubric we'll use.
- [ ] **Schema**: Add `prominence: Literal["primary", "secondary", "minor"]` field to
  `CharacterBible` Pydantic schema in `src/cine_forge/schemas/`.
- [ ] **Adjudicator**: Change the character adjudicator to only discard clearly-non-character
  strings (e.g., sound cues, generic VOICE entries). Keep all named characters regardless of
  score. Add `is_named` heuristic: strings containing only generic nouns (THUG, MAN, WOMAN)
  without a number suffix or distinctive identifier are candidates for discarding — but "THUG 1"
  is named enough to keep.
- [ ] **Extraction split**: In `character_bible_v1`, after adjudication, split characters into
  `full_extract` (primary/secondary) vs `lightweight_extract` (minor). Write a new
  `_extract_minor_character` function with a stripped-down prompt. Both paths still produce a
  valid `CharacterBible` with the `prominence` field populated.
- [ ] **Full extraction prompt update**: Add `prominence` field to the existing structured
  output schema for the full extraction path with a rubric:
  - `primary`: protagonist, antagonist, or key relationship characters — drive the plot
  - `secondary`: recurring supporting characters with named roles and meaningful dialogue
  - `minor`: walk-ons, one-scene characters, thugs, guards, unnamed functionals
- [ ] **UI — list filter**: Add prominence filter chips (All / Primary / Secondary / Minor) to
  the Characters list view (`EntityListPage` or the characters-specific config); persist with
  `useStickyPreference`
- [ ] **UI — detail badges**: Show the prominence tier as a small badge on the character detail
  page header (alongside the existing health badge), coloured by tier
- [ ] **Regression tests**: Add unit tests for the new adjudicator logic and the minor
  extraction path; add a test that verifies "THUG 1" is NOT filtered out
- [ ] Run required checks:
  - [ ] `make test-unit PYTHON=.venv/bin/python`
  - [ ] `.venv/bin/python -m ruff check src/ tests/`
  - [ ] `pnpm --dir ui run lint` and `cd ui && npx tsc -b`
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Existing bibles are immutable — new runs produce new versions
  - [ ] **T1 — AI-Coded:** Prominence rubric in prompt is self-documenting
  - [ ] **T2 — Architect for 100x:** Lightweight path avoids expensive extraction for walk-ons
  - [ ] **T3 — Fewer Files:** Extraction split stays in existing `character_bible_v1`
  - [ ] **T4 — Verbose Artifacts:** Research findings logged before any code
  - [ ] **T5 — Ideal vs Today:** Could prominence come from the adjudicator? Evaluate in research phase

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

## Work Log

20260223-1940 — story created. Prompted by Thug 1/2/3 appearing unlinked in entity detail
relationship panels because character adjudicator filtered them out. Research phase required
before any code — need to validate the 3-tier model against industry conventions.

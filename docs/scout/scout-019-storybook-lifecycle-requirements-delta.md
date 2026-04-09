# Scout 019 — storybook-lifecycle-requirements-delta

**Source:** `/Users/cam/Documents/Projects/Storybook/storybook`
**Scouted:** 2026-04-09
**Scope:** Storybook changes since Scout 017, limited to commits `6d1b5a6` and `ccdda3f` touching `/create-story`, the story template, and `/build-story` lifecycle requirements
**Previous:** Scout 017 (doc-web, Storybook, Dossier agent delta, 2026-03-31)
**Status:** Complete
**Alignment:** No local ADR directly governs this later lifecycle hardening. The closest local anchors are `docs/spec.md` `spec:11.1`, `docs/methodology-ideal-spec-compromise.md`, `docs/build-map.md`, and the already-landed Story 147 workflow contract.

## Findings

1. **`/create-story` and the story template should make blocked stories honest from minute zero** — HIGH value
   What: Storybook commits `6d1b5a6` and `ccdda3f` tightened story creation so `Blocked` is a real initial state, blocked stories must replace placeholder blocker text with concrete truth, and the visible `## Plan` must describe the unblock path or blocker reassessment work instead of stale "build now" steps.
   Us: CineForge already had `Blocked` status semantics and blocker sections, but `/create-story` and the template did not explicitly require the plan to pivot when a story starts blocked. That left room for contradictory story artifacts: honest blocker sections beside a stale implementation plan.
   Recommendation: **Adopt inline**
   Transfusion:
   Exemplar: Storybook commit hunks in `.agents/skills/create-story/SKILL.md` and `.agents/skills/create-story/templates/story.md` from `6d1b5a6` and `ccdda3f`
   Invariant: A blocked story must show blocker truth and the correct next move directly in the canonical artifact
   Adaptation: Keep CineForge's existing `Blocker Summary` / `Blocker Evidence` / `Unblock Condition` body-section contract because the local methodology compiler already reads those sections directly
   Proof target: `/create-story` plus the story template explicitly require concrete blocker text and an unblock-path plan whenever a story starts `Blocked`

2. **`/build-story` should treat blocked stories as first-class and rewrite stale plans when blocker truth wins** — HIGH value
   What: Storybook's later hardening makes `/build-story` read blocker truth before doing anything with a blocked story, stop unless the user explicitly asked for blocker reassessment, and rewrite stale "proceed now" plan text whenever the unblock condition is still unmet or a story becomes newly blocked during exploration/implementation.
   Us: CineForge's `/build-story` could mark a story `Blocked`, but it had no explicit blocked-entry behavior and no rule forcing stale plans to be rewritten when the blocker invalidated the old build path.
   Recommendation: **Adopt inline**
   Transfusion:
   Exemplar: Storybook commit hunks in `.agents/skills/build-story/SKILL.md` from `6d1b5a6` and `ccdda3f`
   Invariant: Blocked stories are health-flag truth until fresh evidence clears them; stale implementation plans are artifact drift
   Adaptation: Reuse CineForge's existing blocker-section names and keep the rest of CineForge's stricter methodology / verification flow intact
   Proof target: `/build-story` now reads blocker sections first, only continues on explicit reassessment with fresh evidence, and rewrites stale blocked-story plans before stopping

3. **Storybook's literal frontmatter blocker-field move should not be copied verbatim into CineForge** — LOW value
   What: Storybook now stores blocker truth in frontmatter fields and teaches the skills/template to write them there.
   Us: CineForge's `scripts/methodology-graph.js` and `tests/unit/test_methodology_graph.py` currently read blocker truth from the `Blocker Summary`, `Blocker Evidence`, and `Unblock Condition` body sections. Porting the Storybook syntax literally without the parser/test migration would create contract drift for no added value.
   Recommendation: **Skip** the literal syntax port and preserve the invariant in CineForge's existing body-section contract instead

## Approved

- [x] 1. Blocked-story honesty in `/create-story` + story template — Approved inline by user request on 2026-04-09 ("We definitely want these"). Evidence: `.agents/skills/create-story/SKILL.md` now requires concrete blocker sections plus an unblock-path plan for blocked stories; `.agents/skills/create-story/templates/story.md` now tells authors to replace `N/A` blocker placeholders and rewrite `## Plan` around the blocker truth.
- [x] 2. Blocked-story reassessment + stale-plan rewrite in `/build-story` — Approved inline by user request on 2026-04-09 ("We definitely want these"). Evidence: `.agents/skills/build-story/SKILL.md` now treats `Blocked` as a first-class incoming status, requires blocker-section review, stops unless reassessment was explicitly requested, and rewrites stale blocked-story plans when blocker truth still wins.

## Skipped / Rejected

- 3. Literal Storybook frontmatter blocker fields — skipped because CineForge's current methodology compiler already consumes the blocker body sections directly; porting the exact Storybook syntax here would be the wrong contract change for this repo

## Verification

- Reviewed Storybook commits `6d1b5a6` and `ccdda3f` plus their touched files:
  `.agents/skills/create-story/SKILL.md`,
  `.agents/skills/create-story/templates/story.md`,
  `.agents/skills/build-story/SKILL.md`
- Re-read CineForge `docs/spec.md` `spec:11.1`, `docs/methodology-ideal-spec-compromise.md`, `docs/build-map.md`, Story 147, and the local skill/template files before editing
- Ran `make skills-check` — passed (`skills-check: OK (31 skills, 31 gemini wrappers)`)
- Ran `git diff --check` — clean
- Re-read the modified CineForge files after editing to confirm the local adaptation stayed coherent with the existing blocker-section parser contract

## Evidence

- Source evidence:
  - `/Users/cam/Documents/Projects/Storybook/storybook/.agents/skills/create-story/SKILL.md`
  - `/Users/cam/Documents/Projects/Storybook/storybook/.agents/skills/create-story/templates/story.md`
  - `/Users/cam/Documents/Projects/Storybook/storybook/.agents/skills/build-story/SKILL.md`
  - Storybook commits `6d1b5a6` and `ccdda3f`
- CineForge files updated:
  - `.agents/skills/create-story/SKILL.md`
  - `.agents/skills/create-story/templates/story.md`
  - `.agents/skills/build-story/SKILL.md`
- Proof notes:
  - Finding 1 proof target met: blocked stories now have explicit guidance to replace placeholder blocker text and keep `## Plan` focused on the unblock path
  - Finding 2 proof target met: `/build-story` now treats blocked stories as health-flag truth until fresh evidence clears them and refuses to preserve stale blocked-story plans
  - Finding 3 adaptation held: CineForge kept its existing blocker-section contract instead of importing Storybook's frontmatter syntax mismatch

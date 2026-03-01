# Scout 004 — Storybook & Dossier (delta)

**Sources:** `/Users/cam/Documents/Projects/Storybook/storybook`, `/Users/cam/Documents/Projects/dossier`
**Scouted:** 2026-02-28
**Scope:** Changes since last scouts (both: 2026-02-28, Scout 003)
**Previous:** Scout 003 (Storybook & Dossier, 2026-02-28)
**Status:** Complete

## Findings

### Theme: Ideal Alignment Gates Across Story Lifecycle

Both repos independently evolved the same pattern: enforce Ideal alignment at every stage of the story lifecycle (create → triage → build → validate → done). CineForge adopted eval mismatch classification in Scout 003 but missed the Ideal alignment dimension.

---

1. **Explicit Draft STOP in `/build-story` step 1** — HIGH value
   What: Storybook's step 1 now says "If status is Draft, STOP — it needs detailed ACs and tasks before it can be built. Tell the user to promote it to Pending first (or promote it inline if they approve)."
   Us: CineForge says "Verify status is Pending or In Progress" — implicitly rejects Draft but doesn't provide the explicit stop + explanation + inline-promotion option.
   Recommendation: **Adopt inline**

2. **Read `docs/ideal.md` in `/build-story` step 3** — HIGH value
   What: Storybook's step 3 reads ideal.md FIRST, before spec refs and dependency stories. This grounds all exploration in the vision.
   Us: CineForge's step 3 reads "all spec refs, dependency stories, and referenced ADRs" — no mention of ideal.md.
   Recommendation: **Adopt inline**

3. **Ideal Alignment Gate (step 4) in `/build-story`** — HIGH value
   What: New step inserted before code exploration. 4-question gate:
   - Does this close an Ideal gap? → proceed
   - Does it move AWAY from the Ideal? → STOP
   - Does it build infrastructure for stages that don't exist yet? → flag premature
   - Does it optimize a shrinking limitation? → flag premature
   - If new AI compromise: note detection eval status
   Us: CineForge has no equivalent. Jumps from "Read context" to "Explore the codebase."
   Recommendation: **Adopt inline** — insert as new step 4, renumber subsequent steps

4. **Model selection pitfall in `/build-story` AI-first check** — HIGH value
   What: Storybook added to step 7: "If selecting a model: never pick from training data — query the provider's API or docs for current models and pricing. Cost differences can be 10-20x."
   Us: CineForge's step 6 says "Have you checked current SOTA?" but no concrete action item about querying APIs or pricing.
   Recommendation: **Adopt inline**

5. **Ideal alignment check in `/create-story` Conventions** — HIGH value
   What: 5-point pushback mechanism before writing the story file:
   - Does it close an Ideal gap? → proceed
   - Does it move AWAY from Ideal? → push back
   - Only optimizes a compromise without closing a gap? → flag low-value
   - "A story referencing a spec compromise is not automatically aligned"
   - If new AI compromise: note detection eval status
   Us: CineForge's Conventions say "Every story should trace back to an Ideal requirement or spec compromise" — no pushback mechanism, no distinction between gap-closing and compromise-entrenching.
   Recommendation: **Adopt inline**

6. **`ideal_refs` input + `status` input in `/create-story`** — MEDIUM value
   What: Storybook's create-story inputs include `ideal_refs` (which Ideal requirements this delivers) and `status` (Pending or Draft, with definitions).
   Us: CineForge has `spec_refs` but no `ideal_refs`. No explicit status input.
   Recommendation: **Adopt inline**

7. **Story Statuses section in `/create-story`** — MEDIUM value
   What: Explicit section defining Draft/Pending/In Progress/Done with clear descriptions.
   Us: CineForge has this in AGENTS.md but not in the create-story skill itself (agents might not see it).
   Recommendation: **Adopt inline**

8. **Ideal Alignment section in `/validate` report** — HIGH value
   What: New step 6 ("Check Ideal alignment — read relevant section of ideal.md") and report template section:
   ```
   ### Ideal Alignment
   - Moves toward Ideal: yes/no/partial
   - New compromises introduced: [list, with detection eval status]
   ```
   Us: CineForge's validate report has Findings/Checks/ACs/Grade/Next Steps — no Ideal section.
   Recommendation: **Adopt inline**

9. **Draft guard in `/mark-story-done`** — HIGH value
   What: New guardrail: "Never mark a Draft story as Done — it must be promoted to Pending and built via `/build-story` first."
   Us: CineForge's mark-story-done has no such guard.
   Recommendation: **Adopt inline**

10. **Read Ideal + Ideal scoring in `/triage-stories`** — HIGH value
    What: New step 2: "Read `docs/ideal.md` to ground scoring." Two new scoring dimensions: "Ideal alignment" (closes gaps vs. entrenches compromises) and "Simplification leverage" (unblocks future simplification across multiple compromises).
    Us: CineForge's triage-stories has 6 scoring dimensions but none about Ideal alignment.
    Recommendation: **Adopt inline**

11. **"Stale model selection" pitfall in AGENTS.md** — MEDIUM value
    What: Added to Known Pitfalls: "Never pick models from training data — query /v1/models and check current pricing. Cost differences can be 10-20x."
    Us: CineForge AGENTS.md has "Baseline = Best Model Only" principle but no concrete "stale model selection" pitfall with action items.
    Recommendation: **Adopt inline**

## Approved

### Inline (adopted)

- [x] 1. Draft STOP in `/build-story` step 1 — Added explicit STOP + explanation + inline-promotion option
- [x] 2. Read `docs/ideal.md` in `/build-story` step 3 — Added "Read ideal.md first" before spec refs
- [x] 3. Ideal Alignment Gate in `/build-story` — Inserted as new step 4 (4-question check), renumbered steps 5-15
- [x] 4. Model selection pitfall in `/build-story` step 7 — Added "never pick from training data" + API query action item
- [x] 5. Ideal alignment check in `/create-story` — Added 5-point pushback mechanism to Conventions
- [x] 6. `ideal_refs` + `status` inputs in `/create-story` — Added both inputs with descriptions
- [x] 7. Story Statuses section in `/create-story` — Added Draft/Pending/In Progress/Done definitions
- [x] 8. Ideal Alignment section in `/validate` — Added step 6 (Check Ideal alignment) + report template section
- [x] 9. Draft guard in `/mark-story-done` — Added "Never mark Draft story as Done" guardrail
- [x] 10. Read Ideal + scoring in `/triage-stories` — Added step 2 (Read Ideal), Ideal alignment + Simplification leverage scoring dimensions, renumbered steps 5-7
- [x] 11. "Stale model selection" pitfall in AGENTS.md — Added to Known Pitfalls with concrete action items

All items verified: step numbering sequential, guardrail references correct, skills synced (27 skills).

## Skipped / Rejected

(None — all findings adopted inline)

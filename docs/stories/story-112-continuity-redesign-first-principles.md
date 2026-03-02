# Story 112 — Continuity Tracking: First Principles Redesign

**Priority**: Medium
**Status**: Draft
**Ideal Refs**: R3 (perfect continuity tracking across narrative)
**Spec Refs**: Spec 6.4 (Asset States / Continuity)
**Depends On**: 092 (Continuity AI Detection — built the current implementation), 108 (Continuity UI Page — revealed the UX problems)

## Goal

Story 092 built a continuity tracker, but the implementation surfaced a deeper problem: we never clearly defined what "continuity" means for a screenplay tool. The current module tracks entity state (costume, physical build, emotional state, props) scene by scene — but this conflates two fundamentally different things that require completely different approaches:

1. **Script continuity** — what can be read and verified from the screenplay text alone: do wounds persist, do props survive their use, does a character's knowledge make sense given what they've learned, can they physically be in two places at once?
2. **Production continuity** — visual consistency between takes and shots: is the coffee cup still half-full, is the jacket still unbuttoned, is the blood smear on the same cheek? This is what a script supervisor tracks on set with a polaroid camera. A script cannot tell you this — and CineForge never will.

Story 092 built something in the middle: it tracks `physical_build`, `costume/wardrobe`, `emotional_state`, and `props_carried` at a level of detail that is half script-reasoning, half production prep. The result is a gap detector that fires false positives (physical_build refining from vague to detailed reads as a contradiction), a UI that can't explain why something is flagged, and an overall system that doesn't clearly answer: *what problem are we actually solving?*

Before fixing the implementation, we need to decide what this system is for.

## The Core Question

**What does continuity mean in a screenplay-only tool?**

A script can have perfect continuity (the Mariner logically always has blood after scene 4, the AirTag reappears exactly when it should) and the film version can be a visual disaster. Those are separate problems. CineForge reads scripts. The production continuity problem belongs to a human script supervisor on set.

So: what is *script-level* continuity? What can an AI actually detect by reading a screenplay? And is that useful enough to keep?

## Options

### Option A — Drop continuity as a feature
Character bibles already capture who characters are. Scene analysis captures what happens. The script supervisor handles production continuity on set. The remaining question is: does CineForge add value by tracking whether a wound from scene 3 shows up in scene 5? Is this a problem screenwriters actually have, or is it a solved problem that doesn't need AI?

Arguments for dropping: the false-positive rate is high, the genuine detection rate is unclear, character bibles + scene analysis already surface most of what matters.

### Option B — Narrow to genuine script-level continuity
Track only things that *can change within a script and matter narratively*. This is a much smaller, higher-confidence set:

- **Injuries and wounds**: a character stabbed in scene 4 should show injury in scene 5 unless time has passed
- **Death and incapacitation**: characters can't appear after dying without narrative explanation
- **Prop chain-of-custody**: if a character steals a key in scene 6, who has the key in scene 10? If a gun fires 6 bullets with no reload, it's empty
- **Knowledge and secrets**: a character can't act ignorant of something they learned earlier in the script (unless a compelling reason)
- **Spatial/temporal impossibility**: a character can't be in London at end of scene 3 and New York at start of scene 4 without travel time
- **Scripted costume changes**: when the script *explicitly* has a character change clothes (as a plot point), that should carry forward

This is a targeted set of *narrative* checks — things a reader or editor would catch by reading carefully. NOT: exact costume description, hair style, physical build, subtle emotional coloring, etc. Those are either stable (physical build doesn't change scene to scene) or too granular for text analysis.

### Option C — Keep current approach, fix the implementation
Keep tracking the current property set but fix:
- Gap detection condition 3 (value refinement ≠ contradiction — use semantic similarity, not string equality)
- Store the gap reason so the UI can explain it
- Categorize properties as `stable` (physical_build, tattoo) vs. `mutable` (injuries, props_carried, emotional_state) and only run gap detection on mutable ones

This fixes the immediate bugs but doesn't resolve the underlying question of whether we're solving a real problem at the right level of abstraction.

### Option D — Two parallel systems
- **Script continuity track** (Option B, derived from script text): narrative logic, prop tracking, knowledge states, spatial/temporal plausibility
- **Production prep track** (separate): costume details, prop descriptions, location descriptions — formatted as "things the art department and script supervisor will need to reference," not a continuity *checker* but a structured *reference*

The production prep track wouldn't try to detect gaps — it would just organize information. The script continuity track would be the only one making claims about what's correct or flagged.

## Research Questions (must answer before choosing an approach)

1. **Who uses script continuity tools and what do they actually flag?** Script supervisors use breakdown software, not AI. Do screenwriters actually re-read their own scripts checking for continuity? Or does this problem belong to the editor/development exec reading pass?

2. **What's the false-positive cost?** If 80% of gap flags are like the `physical_build` case (refinement, not contradiction), the system erodes trust and becomes noise. What's the threshold for useful vs. noise?

3. **What's the true positive rate?** Does Story 092's current implementation find real continuity errors in real screenplays? The Mariner example shows 23 gaps across 13 scenes — how many of those are genuine narrative problems a writer would want to fix vs. false positives from the gap detector?

4. **What CAN be detected reliably from text alone?** Injuries and deaths are high-confidence (explicit, scripted). Exact prop state is medium-confidence (depends on how meticulously the writer describes). Emotional state is low-confidence (often implicit). Costume detail is very low-confidence (production, not script).

5. **Is the Ideal's R3 ("perfect continuity") about script continuity or production continuity?** This matters for whether the current story chain is heading the right direction.

## Approach Evaluation

- **AI-only (LLM reads scenes, judges continuity)**: This is what Story 092 does. Works for unambiguous cases (death, explicit prop transfer) but hallucinates on ambiguous ones (emotional continuity, implicit costume state). High false-positive rate on complex, long scripts.
- **Hybrid (rule-based for high-confidence categories + LLM for complex judgment)**: Track injuries/deaths with deterministic rules (explicit keywords, injury vocabulary), use LLM only for nuanced changes. Reduces false positives on the stable-vs-mutable divide.
- **Pure code**: Not viable for semantic continuity — too much natural language ambiguity. Could work for spatial/temporal checks if scene headers include location and time markers.
- **Eval**: Needs a golden fixture of genuine continuity errors in a real screenplay (not just "gaps" as currently defined) and a separate golden fixture of clear non-errors to measure false positive rate. Neither currently exists.

## Acceptance Criteria

This is a **research + decision story**. Done means:

- [ ] Clear written decision on scope: what does CineForge mean by "continuity" and what specific categories of things will it track?
- [ ] The decision is grounded in evidence: manual audit of current gap flags in at least one real screenplay (the-mariner-60) to measure real vs. spurious gap rate
- [ ] `docs/ideal.md` R3 is reviewed and updated if the decision changes the scope of what "perfect continuity" means for CineForge
- [ ] `docs/spec.md` section 6.4 is updated to reflect the chosen definition
- [ ] If the decision is to redesign: a concrete plan for what the new module tracks, what schema changes are needed, and what the new gap detection logic looks like
- [ ] If the decision is to drop: Story 092 module is archived or removed, continuity_index/continuity_state artifact types are removed from the pipeline, Story 108 UI page is updated or removed, stories.md reflects the cancellation
- [ ] If the decision is Option D (two tracks): a story is created for the script continuity track and a separate story for the production prep reference

## Out of Scope

- Actually implementing the redesigned module (that's the follow-on story)
- Production continuity (shot-to-shot visual consistency) — this belongs to a human script supervisor on set, not a screenplay AI tool
- UI changes (Story 108 can be updated once the data model stabilizes)

## Tasks

- [ ] Manual audit: read the continuity_index and continuity_state artifacts for the-mariner-60 and classify every gap as genuine/spurious/ambiguous. Record what % of flagged scenes represent real narrative problems vs. false positives from the current implementation.
- [ ] Read `docs/ideal.md` R3 — determine whether the Ideal intends script-level or production-level continuity
- [ ] Research: what do professional script supervisors actually track vs. what do AI continuity tools claim to do? (Web research)
- [ ] Write a 1-page "Continuity Definition" decision doc in `docs/` capturing: what categories CineForge will track, what it will not track, and why
- [ ] Update `docs/ideal.md` R3 if needed to clarify scope
- [ ] Update `docs/spec.md` section 6.4 with the chosen definition and what the redesigned system produces
- [ ] Create the follow-on implementation story (or close 092/108 if dropping)

## Files to Modify

- `docs/ideal.md` — may need to clarify R3 scope
- `docs/spec.md` — section 6.4 update to reflect chosen definition
- `docs/` — new "continuity-definition.md" decision doc (or inline in spec)
- `docs/stories.md` — update status of related stories depending on decision
- Follow-on: `src/cine_forge/modules/world_building/continuity_tracking_v1/main.py` — redesign (if keeping)
- Follow-on: `src/cine_forge/schemas/continuity.py` — schema changes (if keeping)

## Notes

### Why the current gap detector fires false positives

Gap condition 3 compares property values as strings: if `prev_value != curr_value` and no `change_event` exists for that key, it's a gap. This conflates:
- **Contradiction**: `"uninjured" → "covered in blood"` (no change_event = real problem)
- **Elaboration**: `"Huge frame" → "Huge frame, built like a pro-wrestler, gray eyes, thick beard"` (more detail, not a change)
- **Stabilization**: properties like `physical_build` and `tattoo` should never be in the mutable set at all — they don't change scene to scene

The fix requires either (a) categorizing properties as stable vs. mutable before running gap detection, or (b) using semantic similarity to detect "same meaning, more detail" vs. "actually different." Both are valid approaches but neither is trivial.

### The gap reason is not stored

The backend computes `gaps: [scene_ids]` but doesn't store which condition triggered the flag or which property was the offending one. This means the UI can only say "gap" — it can't say "physical_build changed without explanation." This is a schema design problem: the gap reason should be a first-class field in `ContinuityState` (or a separate `gap_reasons` dict in `ContinuityIndex`).

### What a script supervisor actually tracks

From production knowledge: script supervisors track everything visible on camera between shots — prop positions, costume state (buttons, zips, tears), hair, makeup, actor positions, eye line, food/drink consumption, practical effects state. None of this can be derived from a script. What CAN be derived from a script:
- Scene-to-scene continuity of explicitly described physical changes (wounds, death)
- Prop chain-of-custody when scripts establish props explicitly
- Character presence/absence
- Narrative knowledge states
- Time/space plausibility (implied by scene headers)

### The "script could be perfect; film could be a mess" insight

This is a fundamental scope boundary. CineForge reads scripts. Script → production continuity is a different problem requiring computer vision (comparing frames), not NLP. The correct answer is: CineForge handles script continuity; a production tool (or human script supervisor) handles production continuity. These should never be mixed in the same system or the same "gap" flag.

## Plan

{Written by build-story Phase 2}

## Work Log

{Entries added during implementation}

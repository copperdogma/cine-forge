---
id: "185"
title: "Project Home Script Hierarchy and Supporting Surface Placement"
status: "Draft"
priority: "High"
ideal_refs:
  - "vision-level preference: Easy, fun, and engaging"
  - "R1 (story understanding)"
  - "R10 (playable assembly at every stage)"
  - "R12 (transparency & control)"
spec_refs:
  - "spec:2.5"
  - "spec:5.3"
  - "spec:5.5"
  - "spec:5.6"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "093"
  - "142"
  - "166"
  - "167"
category_refs:
  - "spec:2"
  - "spec:5"
  - "spec:10"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "api_service_and_operator_console"
roadmap_tags:
  - "project-home"
  - "script-home"
  - "information-architecture"
  - "surface-placement"
  - "ux-polish"
legacy_system: ""
---

# Story 185 — Project Home Script Hierarchy and Supporting Surface Placement

**Priority**: High
**Status**: Draft
**Ideal Refs**: vision-level preference: Easy, fun, and engaging; R1 (story understanding); R10 (playable assembly at every stage); R12 (transparency & control)
**Spec Refs**: spec:2.5, spec:5.3, spec:5.5, spec:5.6, spec:10.3
**ADR Refs**: ADR-002, ADR-003, and `docs/design/decisions.md` ("The screenplay is always the home page")
**Depends On**: Story 093, Story 142, Story 166, Story 167

## Goal

Capture and reconcile the discovered rationale behind the three supporting surfaces currently stacked above the screenplay on Project Home: Script Bible, Artifact Health, and Final Output. Each landed for a valid local reason, but together they now challenge the explicit design rule that the screenplay remains the home page's center of gravity and that secondary system surfaces do not displace it. This story first records that evidence, then drives the product conversation to decide which surfaces belong above the screenplay, below it, in secondary routes, or only in degraded/actionable states, and finally implements the chosen hierarchy.

## Acceptance Criteria

- [ ] The story records the current rationale for Script Bible, Artifact Health, and Final Output placement with direct references to Story 093, Story 142, Story 166, Story 167, and `docs/design/decisions.md`.
- [ ] A concrete product decision is captured for each of the three surfaces: whether it belongs above the screenplay, below it, on a secondary route, or only in degraded/actionable states.
- [ ] After implementation, Project Home again makes the screenplay the unmistakable primary content on desktop and mobile; secondary surfaces no longer crowd or mislead the above-script area.
- [ ] Any healthy-state surface that duplicates information already available in a better secondary route is removed or demoted rather than merely restyled.
- [ ] If the final decision changes a durable UI doctrine rather than only this page's implementation, the relevant decision docs are updated in the same story.
- [ ] Browser verification covers the chosen Project Home hierarchy on desktop and mobile using a representative project state with clean console output.

## Out of Scope

- Reworking the underlying Script Bible, Artifact Health, or Final Output artifact contracts
- Changing final-output assembly/validation semantics beyond what is strictly required by the chosen placement
- Broad navigation redesign outside Project Home and the immediately linked secondary routes it may rely on
- Inventing new system surfaces to solve crowding that can be fixed by demoting, removing, or relocating existing ones

## Approach Evaluation

- **Simplification baseline**: Start by removing or demoting non-essential healthy-state chrome before adding anything new. The likely best first move is quieter placement, not more UI. A healthy Artifact Health summary is the clearest removal candidate; Final Output and Script Bible should justify their prominence explicitly.
- **AI-only**: Wrong fit. This is an information-architecture and product-surface ownership decision, not a reasoning gap that a model call should arbitrate at runtime.
- **Hybrid**: Correct shape. Use repo evidence and the current surfaced route to drive a short product conversation, then implement the smallest coherent UI change that matches the decision.
- **Pure code**: Only after the placement decision is made. Coding first would just harden the current accidental stack.
- **Repo constraints / ADRs**: `docs/design/decisions.md` says the screenplay is always the home page and that run history, artifact health, and other secondary information should be accessible without displacing the script. ADR-002 still requires surfaced next-step clarity and honest downstream visibility. ADR-003 still supports a script-near Script Bible because the story is the identity document.
- **Existing patterns to reuse**: `ScriptBiblePanel` on Project Home, `FinalOutputCard`, Artifact Detail routes, the Artifacts browser, and any compact degraded-state warning pattern already used elsewhere in the shell. Prefer moving existing surfaces to better homes over inventing parallel summaries.
- **Eval**: No promptfoo or model benchmark is warranted. The discriminator is a representative browser pass: does the user immediately feel like they landed on their screenplay rather than a dashboard, while still retaining honest visibility into actionable system state?

## Tasks

- [ ] Turn the current exploration into a short decision brief inside this story: what each above-script surface is for, what problem it originally solved, and what route currently owns that problem best.
- [ ] Hold and record the product decision for Script Bible, Artifact Health, and Final Output placement: above-script, below-script, secondary route, or degraded/actionable-only.
- [ ] Implement the chosen hierarchy with the smallest coherent UI change, preferring removal, demotion, or focused extraction over adding more above-script UI.
- [ ] If the conversation changes a durable design rule rather than only this page's implementation, update `docs/design/decisions.md` in the same story.
- [ ] Add focused regression coverage for the chosen hierarchy or create the smallest practical UI test seam if none exists yet.
- [ ] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [ ] Run required checks for touched scope:
  - [ ] UI: `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
  - [ ] Backend only if API/data contracts are touched: `make test-unit PYTHON=.venv/bin/python` and `.venv/bin/python -m ruff check src/ tests/`
- [ ] If story metadata or decision docs change: `pnpm methodology:compile` and `pnpm methodology:check`
- [ ] If UI is touched: verify the changed flow with browser tools in desktop and mobile views when possible (screenshots + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [ ] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Workflow Gates

- [ ] Build complete: implementation finished, required checks run, and human summary shared
- [ ] Validation complete or explicitly skipped by user
- [ ] Story marked done via `/mark-story-done`

> If this story is later promoted from `Draft` to `Pending`, replace any stale decision-language in `## Plan` with the chosen surface ownership and implementation path.

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: `ui/src/pages/ProjectHome.tsx` currently owns the stacked above-script composition, but it is already oversized and should not absorb more branching. Any surviving above-script or below-script surfaces should live in focused components. `FinalOutputCard` should keep owning final-output-specific UI if that surface remains on home.
- **Data contracts**: Existing UI/API contracts likely already carry the needed truth: Script Bible artifact data, artifact-group health summaries, and final-output/validation state. This story should not invent a new backend summary model unless the chosen placement genuinely needs new typed data across the API boundary.
- **File sizes**: Current likely touch points are `ui/src/pages/ProjectHome.tsx` (`612`), `ui/src/components/FinalOutputCard.tsx` (`285`), `ui/src/pages/ArtifactDetail.tsx` (`648`), `ui/src/components/AppShell.tsx` (`844`), `ui/src/lib/health.ts` (`131`), and `docs/design/decisions.md` (`342`). The main structural pressure is on `ProjectHome`, `ArtifactDetail`, and `AppShell`, so the implementation should prefer extraction and relocation over growing those files further.
- **Decision context**: Reviewed `docs/ideal.md`, the relevant `docs/spec.md` sections, ADR-002, ADR-003, `docs/design/decisions.md`, Story 093, Story 142, Story 166, Story 167, and the current Project Home implementation.

## Files to Modify

- `docs/stories/story-185-project-home-script-hierarchy-and-supporting-surface-placement.md` — capture the rationale, decision, and evidence
- `ui/src/pages/ProjectHome.tsx` — current stacked supporting surfaces and likely extraction/demotion point (`612`)
- `ui/src/components/FinalOutputCard.tsx` — update or relocate the current Project Home final-output surface if it remains part of the chosen hierarchy (`285`)
- `ui/src/pages/ArtifactDetail.tsx` — only if the chosen decision moves one of these responsibilities more explicitly into Artifact Detail (`648`)
- `docs/design/decisions.md` — update only if the conversation changes or sharpens the durable page-hierarchy rule (`342`)
- `ui/tests/` or a new focused UI test file — add the smallest practical regression seam for the chosen hierarchy

## Redundancy / Removal Targets

- Any healthy-state Artifact Health surface on Project Home that duplicates better secondary routes
- Any above-script card stack that pushes the screenplay below the fold without earning that prominence
- Any copy or placement that makes Project Home feel like an admin/status dashboard instead of the story's primary working surface

## Notes

- Current Project Home stacks three secondary surfaces above the screenplay: `ScriptBiblePanel`, Artifact Health, and `FinalOutputCard`.
- The discovered rationale is real, but it is not one unified page philosophy:
  - **Story 093 (Script Bible)** put high-level story understanding near the screenplay because the script bible is the story's identity document and belongs close to the script.
  - **Story 142 (Artifact Health)** surfaced actionable health on the home route so onboarding does not end in hidden stale debt or vague failure.
  - **Story 166 and Story 167 (Final Output + trust)** used Project Home because it was the thinnest existing surfaced route for project-level playback/trust without route hunting.
- `docs/design/decisions.md` is the higher-order rule: the screenplay is always the home page; scenes detected, artifacts produced, run history, and artifact health are secondary information accessible through chat, nav pages, or inspectors, and none of it should displace the script.
- So the problem is not that these features are individually wrong. The problem is that several individually valid local decisions accumulated on the same surfaced route and now compete with the screenplay.
- Working hypothesis entering the conversation:
  - **Script Bible** has the strongest case to remain near the screenplay, but should stay compact.
  - **Artifact Health** likely belongs on the home route only when degraded/actionable.
  - **Final Output** needs surfaced discoverability, but that does not automatically justify living above the screenplay.

## Plan

### Exploration Summary

- Current repo truth:
  - `ui/src/pages/ProjectHome.tsx` places `ScriptBiblePanel`, Artifact Health, and `FinalOutputCard` ahead of the screenplay body.
  - Story 093 explicitly made the script bible part of the script page/header experience.
  - Story 142 made artifact health visible on the home route to keep initial intake honest.
  - Story 166 and Story 167 intentionally used Project Home as the thinnest surfaced route for final-output actionability and trust.
  - `docs/design/decisions.md` says the screenplay is always the home page and that secondary system information should not displace it.
- Conclusion: this is an accumulation problem, not a single bad feature decision.

### Ideal Alignment And Success Test

- This story closes a real Ideal gap in felt product quality: the current page can be technically honest while still feeling too much like a system dashboard.
- Success is not "more information visible." Success is that the top of Project Home again feels like the story's working surface while still keeping actionable support state honest and easy to reach.
- The key qualitative test: on load, does the user feel like they are looking at their screenplay first, with support surfaces helping from the side or at the right moments, rather than competing for the same vertical space?

### Conversation To Resolve

- Which surfaces, if any, deserve persistent above-script placement?
- Which surfaces should appear only when degraded, missing, blocked, or freshly actionable?
- Does Final Output belong on Project Home as a constant card, as a quieter below-script section, or as a secondary route/entry point?
- Does Script Bible stay as a compact context block, or should some of its detail move elsewhere?
- If Artifact Health is healthy, does it belong on Project Home at all?

### Structural Health Check

- `ProjectHome.tsx` is already `612` lines, so "just add another conditional and more layout logic" is the wrong default.
- `ArtifactDetail.tsx` (`648`) and `AppShell.tsx` (`844`) are also already large, so this story should not simply move all responsibility into another oversized file.
- The clean implementation path likely involves either removing surfaces from home or extracting a smaller composition seam.

### Implementation Order

1. Record the decision brief and final surface ownership in this story.
2. Implement the smallest coherent hierarchy change that matches that decision.
3. Verify both a healthy-state project and any still-actionable/degraded state the chosen design needs to handle.
4. Update decision docs only if the conversation materially sharpens the durable rule rather than merely applying it.

## Work Log

20260420-2234 — story-created: scaffolded Story 185 for the Project Home hierarchy question via the create-story workflow. Next step: replace the template with the discovered rationale and an honest decision-first scope.
20260420-2248 — rationale-captured: documented the current above-script stack and the source-story rationale for Script Bible (Story 093), Artifact Health (Story 142), and Final Output (Stories 166/167), then framed the story around reconciling those local decisions with the higher-order screenplay-home-page rule in `docs/design/decisions.md`. Evidence: reviewed `ui/src/pages/ProjectHome.tsx`, `docs/design/decisions.md`, and the four source stories. Next step: regenerate methodology outputs so Story 185 appears as a real planning artifact, then use the story as the decision record for the placement conversation.
20260504-2120 — routed-current-inbox-note: Story 196 routed the current `UI Plan` inbox note here. Evidence: the note asks for a comprehensive UI plan around script plus opinions producing scenes/shots, with an infinite-canvas/NLE mental model; Story 185 already owns the Project Home and broader surface-placement decision boundary, and Story 196 browser evidence shows the current Brick & Steel surfaced path is technically reachable but still carries information-architecture pressure. Next step: fold this note into the Story 185 product conversation before writing any new ADR or UI implementation.
20260504-2128 — validation-addendum: Story 196 validation reran the mobile browser packet and found the Brick & Steel mobile Home route loads without blank screen or browser errors, but does not expose `Start Scene Work` text. Evidence: `docs/reports/story-196-brick-steel-product-truth-scrub/browser/browser-summary.json` records the missing expected text on `home-mobile`; `characters-mobile.png`, `previz-mobile.png`, and `render-mobile.png` show the adjacent mobile surfaces are reachable. Next step: treat mobile Home scene-entry visibility as part of this UI hierarchy/surface-placement story rather than creating a duplicate follow-up.

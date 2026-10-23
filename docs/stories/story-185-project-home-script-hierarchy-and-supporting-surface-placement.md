---
id: "185"
title: "Project Home Script Hierarchy and Supporting Surface Placement"
status: "Done"
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
**Status**: Done
**Ideal Refs**: vision-level preference: Easy, fun, and engaging; R1 (story understanding); R10 (playable assembly at every stage); R12 (transparency & control)
**Spec Refs**: spec:2.5, spec:5.3, spec:5.5, spec:5.6, spec:10.3
**ADR Refs**: ADR-002, ADR-003, and `docs/design/decisions.md` ("The screenplay is always the home page")
**Depends On**: Story 093, Story 142, Story 166, Story 167

## Goal

Make Project Home feel like the screenplay's working surface on desktop and
mobile. Keep the story title, logline, and compact metadata near the script;
put full Script Bible and project-cut controls behind clear on-demand actions;
show a compact review alert only when artifacts actually need attention. Make
scene entry visible without opening chat. Apply the existing screenplay-first
design decision, preserving playback, validation, export, provenance, and
immutable artifacts.

## Acceptance Criteria

- [x] The story records the current rationale for Script Bible, Artifact Health, and Final Output placement with direct references to Story 093, Story 142, Story 166, Story 167, and `docs/design/decisions.md`.
- [x] A concrete product decision is captured for each of the three surfaces: whether it belongs above the screenplay, below it, on a secondary route, or only in degraded/actionable states.
- [x] After implementation, Project Home again makes the screenplay the unmistakable primary content on desktop and mobile; secondary surfaces no longer crowd or mislead the above-script area.
- [x] Any healthy-state surface that duplicates information already available in a better secondary route is removed or demoted rather than merely restyled.
- [x] If the final decision changes a durable UI doctrine rather than only this page's implementation, the relevant decision docs are updated in the same story.
- [x] Browser verification covers the chosen Project Home hierarchy on desktop and mobile using a representative project state with clean console output.

- [x] A visible Scenes action works on desktop and mobile without opening chat.
- [x] Project-cut counts do not label multiple clip artifacts as a count of rendered scenes.
- [x] On-demand story/cut panels open, close, and return focus without navigating away or changing artifacts.
- [x] Project-cut health distinguishes media awaiting review from failed validation without changing backend health or review requirements.

## Out of Scope

- Reworking the underlying Script Bible, Artifact Health, or Final Output artifact contracts
- Changing final-output assembly/validation semantics beyond what is strictly required by the chosen placement
- Broad navigation redesign outside Project Home and the immediately linked secondary routes it may rely on
- Inventing new system surfaces to solve crowding that can be fixed by demoting, removing, or relocating existing ones

## Approach Evaluation

- **Simplification baseline**: Start by removing or demoting non-essential healthy-state chrome before adding anything new. The likely best first move is quieter placement, not more UI. A healthy Artifact Health summary is the clearest removal candidate; Final Output and Script Bible should justify their prominence explicitly.
- **AI-only**: Wrong fit. This is an information-architecture and product-surface ownership decision, not a reasoning gap that a model call should arbitrate at runtime.
- **Hybrid**: Repo evidence, existing approved screenplay-first doctrine, and representative browser judgment settle placement. Runtime remains deterministic; no new human preference is needed for this conservative implementation.
- **Pure code**: Implement the recorded placement decision with existing components, APIs, and health semantics.
- **Repo constraints / ADRs**: `docs/design/decisions.md` says the screenplay is always the home page and that run history, artifact health, and other secondary information should be accessible without displacing the script. ADR-002 still requires surfaced next-step clarity and honest downstream visibility. ADR-003 still supports a script-near Script Bible because the story is the identity document.
- **Existing patterns to reuse**: `ScriptBiblePanel` on Project Home, `FinalOutputCard`, Artifact Detail routes, the Artifacts browser, and any compact degraded-state warning pattern already used elsewhere in the shell. Prefer moving existing surfaces to better homes over inventing parallel summaries.
- **Eval**: No promptfoo or model benchmark is warranted. The discriminator is a representative browser pass: does the user immediately feel like they landed on their screenplay rather than a dashboard, while still retaining honest visibility into actionable system state?

## Tasks

- [x] Turn the current exploration into a short decision brief inside this story: what each above-script surface is for, what problem it originally solved, and what route currently owns that problem best.
- [x] Hold and record the product decision for Script Bible, Artifact Health, and Final Output placement: above-script, below-script, secondary route, or degraded/actionable-only.
- [x] Implement the chosen hierarchy with the smallest coherent UI change, preferring removal, demotion, or focused extraction over adding more above-script UI.
- [x] If the conversation changes a durable design rule rather than only this page's implementation, update `docs/design/decisions.md` in the same story.
- [x] Add focused regression coverage for the chosen hierarchy or create the smallest practical UI test seam if none exists yet.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [x] Run required checks for touched scope:
  - [x] UI: `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
  - [x] Backend only if API/data contracts are touched: `make test-unit PYTHON=.venv/bin/python` and `.venv/bin/python -m ruff check src/ tests/` (not applicable: backend contracts unchanged)
- [x] If story metadata or decision docs change: `pnpm methodology:compile` and `pnpm methodology:check`
- [x] If UI is touched: verify the changed flow with browser tools in desktop and mobile views when possible (screenshots + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [x] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [x] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [x] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [x] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [x] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

> Placement decisions and authorization are recorded in `## Plan`; no additional product decision is pending.

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
- `ui/src/components/ProjectHomeHeader.tsx` and `ScriptBiblePanel.tsx` — focused Home composition and reused Bible content
- `ui/src/lib/health.ts` — distinguish review-needed and failed media validation
- `ui/src/components/PrevizPanel.tsx` (`952` before, `948` after) and `previz-panel-support.ts` — extract the existing summary before handling its new review-needed label
- `ui/tests/media-validation-health.test.ts` and captured fixture — real regression and coupled consumer truth
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

### Decision and authorization

Cam authorized continuing triage and fixes. The story's earlier request for a
product conversation is an agent-authored approach, with no recorded reserved
human preference or blocker. Existing `docs/design/decisions.md`, ADR-002, and
ADR-003 settle the screenplay-first rule. Apply that rule conservatively;
no durable doctrine change or new ADR is needed. The routed infinite-canvas /
NLE idea is not part of this change (the Ideal remains export-first).

| Surface | Decision | Existing reason preserved |
|---|---|---|
| Script Bible | Keep title/logline/genre near script; full analysis via a labeled dialog | Story093's script-near story identity |
| Artifact Health | Remove healthy-state card; compact actionable review alert links to Inbox | Story142's honest review/health semantics |
| Final Output | Clearly labeled Project Cut dialog reuses FinalOutputCard and detail/validation links | Stories166/167's accessible assembly/playback/trust |
| Scene entry | Visible Scenes action when scenes exist, including mobile | Existing scene routes, no chat dependency |

### Implementation and structural fit

1. First extract the title/header and Bible content from the 612-line
   `ProjectHome.tsx` into focused `ProjectHomeHeader.tsx` and
   `ScriptBiblePanel.tsx` components. Keep files below400 lines and functions
   focused; split current large FreshImportView into data/scroll helpers and
   composition before adding the new layout. `make check-size` ran before
   this plan. Do not move responsibilities into already-large AppShell (841)
   or ArtifactDetail (648).
2. Header owns these Home-specific disclosures, compact metadata, scene link,
   and existing export callback. Use existing Dialog accessibility/scroll
   patterns; dialogs must fit mobile, close with Escape/Close, and restore
   focus. Full supporting cards must not mount/display as persistent Home
   chrome. Reuse `actionableHealthGroups` unchanged and render a compact alert
   only for its nonempty result; no new business or AI decision logic.
3. Remove the obsolete Home card stack. Preserve normalized/raw screenplay,
   scene dividers, hash navigation, character/scene navigation, inline title
   editing, production-format link, and export. First extraction/decomposition
   reduces the old file instead of growing it.
4. Small coupled truth fix: baseline Brick & Steel's FinalOutputCard says
   `10/6 scenes rendered` because it counts clip artifact groups. Without
   changing assembly or adding heuristics, label that existing quantity as
   generated clips and display scene count separately. This is a text/variable
   naming correction in the 285-line card, not new assembly/model logic.
5. Coherent coupled truth repair discovered during representative cut verification: a valid local probe with semantic review skipped has backend needs_review, but shared media health labels it Validation Failed. Capture the actual group as a fixture before fixing the label; map needs_review to an amber Needs Review badge and preserve failed/current/pending semantics and attention filtering. This is a deterministic presentation mapping, not a new AI or backend decision.
6. Before adding the coupled new status to the oversized952-line PrevizPanel consumer, extract its existing playback-summary branching into the33-line previz-panel-support module. Then add explicit review-required guidance so the new shared label cannot fall through to ready. Keep other consumer behavior unchanged; do not grow the large panel or create another subsystem. A real-fixture consumer regression must fail before repair.
7. Validate with UI lint, build-mode TypeScript, build, existing UI tests,
   meaningful browser acceptance checks, and methodology compile/check.
   Backend/API/schema/AI behavior is unchanged; do not rerun backend suites or
   paid evaluations. Current evidence-manifest generation happens only after
   final canonical state settles, preserving old versions.

### Browser evidence and stop condition

Baseline current normal-driver Brick & Steel Home puts the screenplay at
717.5px on1600×1100 desktop and1105.75px on390×844 mobile (below mobile fold).
Screenshots and measurements are retained in
`docs/reports/story-185-project-home-hierarchy/` before any implementation.

Use that real degraded project plus healthy `brick-steel-full-retired-3`
(normal ingested script with six scenes and Script Bible, zero attention
items). Verify initial visible screenplay, no persistent healthy health/card
stack, working Scenes/Bible/Project Cut/Export actions, keyboard close/focus,
clean console, and mobile bounds. Preserve the actual browser acceptance
checks and result JSON; test geometry and user behavior, not source strings.
The old Story194 fixture has seeded canonical content and no uploaded input, so it is excluded from acceptance. Run the unchanged final_output recipe on real Brick inputs, with no semantic review model, for representative cut/detail/validation proof. This creates new immutable versions through the normal driver; it does not establish semantic media quality. No artifacts will be seeded or copied for acceptance. This targeted
pass does not reset full FP1 freshness. Stop when the screenplay is primary
and the existing supporting actions remain discoverable and truthful.

### Risks, ownership, and delegation

No new dependencies, public/schema contracts, model choice, paid run, commit,
push, or new persistent preference. Parent owns ProjectHome, story/state,
verification and integration. A bounded cheaper worker may own the disjoint
new header/Bible components and FinalOutputCard text; parent reviews output.
Existing unrelated dirty work, new inbox imports, and retained-media inventory
extras remain untouched. The older header's duplicate Script Bible type and
always-mounted healthy/card stack are removal targets.

## Work Log

20260420-2234 — story-created: scaffolded Story 185 for the Project Home hierarchy question via the create-story workflow. Next step: replace the template with the discovered rationale and an honest decision-first scope.
20260420-2248 — rationale-captured: documented the current above-script stack and the source-story rationale for Script Bible (Story 093), Artifact Health (Story 142), and Final Output (Stories 166/167), then framed the story around reconciling those local decisions with the higher-order screenplay-home-page rule in `docs/design/decisions.md`. Evidence: reviewed `ui/src/pages/ProjectHome.tsx`, `docs/design/decisions.md`, and the four source stories. Next step: regenerate methodology outputs so Story 185 appears as a real planning artifact, then use the story as the decision record for the placement conversation.
20260504-2120 — routed-current-inbox-note: Story 196 routed the current `UI Plan` inbox note here. Evidence: the note asks for a comprehensive UI plan around script plus opinions producing scenes/shots, with an infinite-canvas/NLE mental model; Story 185 already owns the Project Home and broader surface-placement decision boundary, and Story 196 browser evidence shows the current Brick & Steel surfaced path is technically reachable but still carries information-architecture pressure. Next step: fold this note into the Story 185 product conversation before writing any new ADR or UI implementation.
20260504-2128 — validation-addendum: Story 196 validation reran the mobile browser packet and found the Brick & Steel mobile Home route loads without blank screen or browser errors, but does not expose `Start Scene Work` text. Evidence: `docs/reports/story-196-brick-steel-product-truth-scrub/browser/browser-summary.json` records the missing expected text on `home-mobile`; `characters-mobile.png`, `previz-mobile.png`, and `render-mobile.png` show the adjacent mobile surfaces are reachable. Next step: treat mobile Home scene-entry visibility as part of this UI hierarchy/surface-placement story rather than creating a duplicate follow-up.

20261023-0858 — triage/exploration/plan: previous goal turn made concrete progress (Stories201/208 completed). Fresh direct triage facts and all five neutral lane packets show no ready story but real unmet product scope. Top three:185 screenplay-first Home,197 representative-reference fidelity, and a fresh FP1 walkthrough.185 wins now because current browser/API evidence confirms the hierarchy defect without a paid capability experiment: script begins717.5px desktop/1105.75px mobile and multiple clips are mislabeled as10/6 scenes. Existing design doctrine resolves conservative placement; no Cam-reserved preference is recorded. Source-story rationale093/142/166/167 and ADR-002/003 were reviewed; active scene-generation focus remains6/7 while this hold-state UX repair removes operational friction. Scope stays within185 and includes the small clip-count wording correction. Healthy/degraded project candidates recorded; no hand-seeded UI state. Next: extract focused header/Bible components, implement the chosen hierarchy, and verify on normal project state.

20261023-0909 — implementation/review: replaced the persistent Bible/health/cut stack with a compact header, labeled Bible/Cut dialogs, a Scenes action, and an actionable-only Inbox alert. Decomposed the612-line Home into focused data/scroll/render composition; Bible details and inline rename behavior remain intact. Corrected the clip-versus-scene label. Strong review caught a new pending-assembly dismissal race before acceptance; a persistent controller above the dialog now owns the mutation. Actual intercepted POST close/reopen retained the disabled button and recovered after an intercepted failure, with no backend run. Bounded primary-source research and applicability evidence are in docs/research/story-185-dialog-lifecycle.md. UI lint/build-mode TypeScript/build and21 existing UI tests passed; final focused extraction remains under review. Next: finish representative cut link/playback proof, record final validation, and close the owning architecture finding.

20261023-0909 — browser evidence: normal-driver degraded Brick & Steel and healthy Brick & Steel3 pass60 recorded Home/dialog checks across1600×1100 and390×844, with zero console errors. Degraded script starts330px desktop/462px mobile versus717.5/1105.75 baseline; healthy starts280.8/376px. Both new dialogs fit, retain content, close with Escape, and restore focus. Export remains reachable and closes; an exploratory stricter focus check exposed the existing controlled ExportModal returning focus to body, outside the new story/cut-panel focus criterion. Resizing an already-open desktop chat created its expected mobile modal; it was explicitly dismissed before initial Home acceptance. Mobile Scenes entry navigated to the six-scene list without chat. All project artifact-group inventories remained identical during inspection. The old Story194 fixture has seeded canonical input and no uploaded input, so Home correctly says no screenplay; it supplies no representative Home/cut evidence. Next: run the unchanged final_output recipe on real Brick inputs with no semantic model to inspect honest local-only validation and cut links.

20261023-0914 — representative-cut/truth-repair: unchanged final_output recipe completed on real Brick inputs via DriverEngine, creating final_output/project/v1 and media_validation/project/v1 for$0 with no semantic model. New cut honestly includes1 scene and omits5; deterministic decode/probe passed with no findings, semantic review skipped, backend needs_review. UI incorrectly labeled this Validation Failed. Captured the actual API group in ui/tests/fixtures/media-validation-needs-review.json before changing code; regression failed1/passed1 before repair. Expanded this story by the tightly coupled deterministic badge mapping and regression coverage, preserving backend health and review semantics. Strong review cleared the dialog/controller repair; final helpers are33/79/70/45/48lines. Next: verify corrected badge plus playback/detail/validation on desktop/mobile, then final gates and closure.

20261023-0922 — coupled-consumer-review: strong review found PrevizPanel matched only the old pending/failed labels, so the new shared Needs Review status fell through to ready. Before changing that oversized952-line component, extracted its existing playback-summary branch into the existing focused previz-panel-support module; changed its format helper import to a relative path for a normal node test seam. The consumer regression failed on actual review-needed fixture health, then passed after explicit review-required guidance. Missing/stale validation, failures, ready media, and incomplete clip priority are covered. PrevizPanel shrank rather than gained branching; other media-status consumers were searched and reviewed. Next: final UI gates and real Previz browser smoke on the unchanged representative substrate.

20261023-0925 — validation: final UI lint, build-mode TypeScript, production build and25UItests pass (existing large-chunk advisory only). Real cut and validation artifact schemas pass; native playback reached14.042667s/ended=true. Desktop/mobile cut dialogs preserve explicit1/6 partial coverage and local-only review status, working artifact/validation links, and correctClose/Escape focus. Desktop/mobile Scenes and script-divider navigation pass. The coupled Previzmapping regression and unchanged real8-player route pass without consoleerrors; no paidgeneration or judged/scoredAIevaluation occurred. Report and reproducible browseracceptance checks live in docs/reports/story-185-project-home-hierarchy/. FullFP1 remainsstale; existingExportfocus-to-body is recorded, outside the newBible/Cutfocus criterion. T0 artifacts unchanged duringinspection, later realdriveraddsimmutableversions; T1 focusedfunctions andworklog; T2 no newmodel/workflow; T3 Home216/header251/Bible111/cut352, new/extractedfunctions<100; T4 durable report/research; T5 removedsupportingstackperIdeal. Next: markdone, clear its ownedarchitecturefinding without resettingaudit/FP1dates, regenerateplanning and newcurrentcontractsnapshot, then resumeauthorizedtriage.

20261023-0926 — done: /validate and /mark-story-done close-now checks pass for the complete185scope; independent review cleared both persistentcontroller andsharedstatusconsumer changes. All acceptance/task/workflow gates have evidence above and in the report. Existing design doctrine is unchanged. Canonical state clears only the resolved Home placement finding; fullFP1/auditdates andactive6/7focus are preserved. Regenerate generatedviews and immutable currentcontract v23 for the newUIregressions andsettledstate; older snapshots stay untouched. No commit or push authorized. Next: continue the authorized /triage goal; /finish-and-push is available only if Cam later requests landing.

20261023-0930 — planning/evidence-closeout: canonical compiler correctly rejected the active UI campaign after all its linked stories becameDone. Independent ownerlookup confirmed156 was completedsetup and185/196/201 targetedpasses; createdDraft232 for the distinct overdueFP1cycle, linked it without resettingfreshness, and methodologycompile/check nowpass with onlyexistingdue warnings. Finalmanifestinventory inspection found the newUItest/fixture absent from the ledger explicitUIpaths; declaredboth and corrected the suite note to25tests. Immutablev23 retains its interim settledplanning snapshot; v24 captures the complete declaredUIcontracts. No oldsnapshot rewritten. Next: focusedledger/manifest validation then resumegoaltriage.

20261023-0933 — final-evidence: immutablecurrentv24 inventories995declaredcontracts includingnewUItest/fixture, bundle416e806c9cb50e08212198d52a73cf1d4ef63b499151113b05202cd871b439af. Ledger/manifestchecks pass;34focusedtests and final14-testmanifest rerun pass. FinalPrevizsummaryscreenshots were manuallyinspected inbothviewports; finalstrongreviewclearedconsumerfix. Worklogchangedaftercompile, so refreshgeneratedviews onceagainbeforehandoff; no canonicalstate orfrozenmanifestbytes change. Goalremainsactive.

---
id: "196"
title: "Brick & Steel Product Truth Scrub"
status: "Done"
priority: "High"
ideal_refs:
  - "vision-level preference: easy, fun, and engaging"
  - "R7 (generate -> react -> refine)"
  - "R8 (professional-grade production artifacts)"
  - "R10 (playable assembly at every stage)"
  - "R11 (production readiness per scene)"
  - "R12 (transparency & control)"
spec_refs:
  - "spec:5.3"
  - "spec:5.5"
  - "spec:5.6"
  - "spec:6.3"
  - "spec:6.4"
  - "spec:7.1"
  - "spec:10.3"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "139"
  - "180"
  - "191"
  - "192"
  - "193"
  - "194"
category_refs:
  - "spec:5"
  - "spec:6"
  - "spec:7"
  - "spec:10"
compromise_refs:
  - "C6"
input_coverage_refs: []
architecture_domains:
  - "api_service_and_operator_console"
  - "generation_and_visualization"
roadmap_tags:
  - "brick-steel"
  - "product-truth"
  - "ui-scout"
  - "inbox-scrub"
  - "scene-generation"
legacy_system: ""
---

# Story 196 - Brick & Steel Product Truth Scrub

**Priority**: High
**Status**: Done
**Ideal Refs**: easy/fun/engaging, R7, R8, R10, R11, R12
**Spec Refs**: spec:5.3, spec:5.5, spec:5.6, spec:6.3, spec:6.4, spec:7.1, spec:10.3
**ADR Refs**: ADR-002, ADR-003
**Depends On**: Story 139, Story 180, Story 191, Story 192, Story 193, Story 194

## Goal

Walk the current Brick & Steel production/local surfaced path and turn the large inbox batch into verified truth. Many notes likely became stale after Stories 139, 180, 191, 192, 193, and 194, but they should not be deleted from the inbox merely because related stories exist. This story produces an evidence matrix that marks each inbox symptom as fixed, stale, still live, or intentionally rehomed, and creates only focused follow-up stories for defects that still reproduce.

## Eval Ladder Context

- **Root Ideal need**: CineForge should feel like working with the story, not fighting stale status, hidden failures, or inscrutable generation surfaces.
- **Parent evidence**: Stories 139, 180, 191, 192, 193, and 194 each fixed part of the Brick & Steel operator path: black-screen recovery, scene entry clarity, final-render prompt truth, design-study lifecycle, render clip planning, and multi-clip previz/render execution.
- **Measured failure mode**: `docs/inbox.md` still contains raw user reports for black screens, keyframe discoverability, Open/Jump behavior, bad previz, final render quality, GPT-image completion/error visibility, exact dialogue, reference use, and broad eval/test gaps.
- **Child validation**: a current desktop/mobile product-truth report on Brick & Steel, plus a scrubbed inbox and any newly necessary focused follow-up stories.

## Acceptance Criteria

- [x] A report maps every Brick & Steel inbox symptom to current evidence: fixed/stale, still live, intentionally rehomed, or not reproducible with a clear reason.
- [x] The normal surfaced Brick & Steel scene path is exercised on desktop and mobile at least across Home, Characters, Scene Workspace Previz, Scene Workspace Render, and relevant artifact/detail links.
- [x] The pass specifically checks black-screen recovery, Open/Jump behavior, keyframe/animatic discoverability, GPT-image completion/error truth, exact-dialogue prompt truth, multi-clip previz/render visibility, and final-render/reference truth.
- [x] Any still-live defect becomes either a focused story, a work-log addition to an existing open story, or a clearly documented defer/discard decision. Do not leave verified defects only in the report.
- [x] `docs/inbox.md` is scrubbed after the notes are routed. It should not keep stale duplicates of story-owned defects.
- [x] The report distinguishes product-quality failures from provider/configuration failures and from already-fixed local-code issues.

## Out of Scope

- Fixing every discovered defect in this story. Small documentation or inbox cleanup is in scope; product/runtime fixes should become focused follow-up stories unless they are tiny and tightly coupled.
- Changing provider defaults, prompt strategies, or eval scoring without a separate eval-backed story.
- Treating this as the canonical full-pipeline UI scout unless the run also follows `docs/runbooks/full-pipeline-ui-manual-walkthrough.md` on the canonical fixture.
- Production secret remediation for xAI; Story 195 owns that.
- Duplicate Brick/Brick Braddock adjudication; Story 198 owns that unless the scout proves it is stale.
- Reference-pack / multi-view generation strategy; Story 197 owns that broader product-quality lane.

## Approach Evaluation

- **Simplification baseline**: Do nothing and assume prior stories fixed the notes. That is wrong because the inbox contains real production reports and some fixes were local, branch-specific, or partial.
- **AI-only**: Not sufficient. AI can summarize artifacts, but product truth requires actual UI/API/browser evidence.
- **Hybrid**: Best. Use deterministic API/browser checks plus human/AI inspection of screenshots, prompts, generated media metadata, and current artifact state.
- **Pure code**: Insufficient because the task is judgment-heavy product truth, not a known implementation bug.
- **Repo constraints / ADRs**: ADR-002 requires obvious next actions and honest preflight. ADR-003 says scene-workspace film elements are user-facing creative surfaces, not raw pipeline artifacts. The inbox is a queue, so routed items should be deleted.
- **Existing patterns to reuse**: `docs/ui-scout.md`, `docs/runbooks/full-pipeline-ui-manual-walkthrough.md`, Story 139 browser smoke patterns, Story 192 browser evidence packet, Story 194 Brick & Steel verification screenshots, and `docs/reports/story-*` evidence folders.
- **Eval**: No promptfoo eval unless the scrub confirms a maintained eval is stale or missing. The distinguishing evidence is a current UI/API/media inspection report.

## Tasks

- [x] Build a symptom inventory from the historical pre-triage inbox at `90a67ec^:docs/inbox.md`, grouped by black-screen/recovery, navigation/discoverability, design-study images, previz, render, keyframes, user edits, and eval/test coverage.
- [x] Re-check the exact current story/code surfaces for each likely owner before declaring a note fixed.
- [x] Run a desktop browser pass through the current Brick & Steel surfaced path and capture screenshots, console/page errors, API status, and route evidence.
- [x] Run a mobile spot check for the most relevant Scene Workspace path and any surface that looked risky on desktop.
- [x] Inspect current prompt/video/artifact detail for scene 001 where needed, especially final render and AI previz clip artifacts.
- [x] Produce `docs/reports/story-196-brick-steel-product-truth-scrub/triage-matrix.md` or equivalent with symptom-by-symptom disposition.
- [x] Create focused follow-up stories only for still-live defects that are not already owned. Prefer adding notes to existing stories when the ownership is genuinely the same.
- [x] Scrub `docs/inbox.md` only for current notes that this pass routes with preserved evidence; the original Brick & Steel batch was already deleted by the Story 195-199 triage commit and must be captured from Git history instead.
- [x] Check whether this pass makes any old docs or stale report claims redundant; update them or create a follow-up.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: N/A, no backend code changes
  - [x] Backend lint: N/A, no backend code changes
  - [x] UI: N/A, no UI code changes
- [x] If story metadata, report indexes, or methodology state changes: `pnpm methodology:compile` and `pnpm methodology:check`
- [x] If evals or goldens are changed: N/A, no evals or goldens changed
- [x] Browser verification: desktop and mobile evidence with clean console output or a documented blocker
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 - Data Safety:** Is the scrub capture-first before deleting inbox text?
  - [x] **T1 - AI-Coded:** Is each disposition concrete enough for a future agent?
  - [x] **T2 - Architect for 100x:** Did we avoid creating backlog for stale defects?
  - [x] **T3 - Fewer Files:** Did follow-ups reuse existing owners where possible?
  - [x] **T4 - Verbose Artifacts:** Is the evidence matrix complete?
  - [x] **T5 - Ideal vs Today:** Does the current surfaced path feel easier and more honest?

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: This is primarily evidence and routing. If tiny fixes are folded in, keep them in the existing owner: `use-run-progress` for black-screen behavior, Scene Workspace components for route visibility, design-study router/UI for GPT-image lifecycle, render adapter for prompt/media artifacts.
- **Data contracts**: No new schema should be introduced unless a still-live defect requires one in a follow-up story.
- **File sizes**: likely touched docs only. If code is touched, beware large watchpoints: `SceneWorkspacePage.tsx`, `GeneratedVideoPanel.tsx`, `PrevizPanel.tsx`, `render_adapter_v1/main.py`, and `api/service.py`.
- **Decision context**: ADR-002, ADR-003, Stories 139, 180, 191, 192, 193, 194, `docs/ui-scout.md`, and the pre-triage inbox.

## Files to Modify

- `docs/reports/story-196-brick-steel-product-truth-scrub/` - new evidence matrix and screenshots/summary references
- `docs/inbox.md` - remove routed/stale inbox items after the matrix captures them
- `docs/stories/story-196-brick-steel-product-truth-scrub.md` - work log
- New focused story files only for still-live defects discovered during the pass
- Code files only if a tiny tightly coupled fix is justified during the scrub

## Redundancy / Removal Targets

- Stale inbox notes for defects now owned by Stories 139, 180, 191, 192, 193, or 194.
- Duplicate story candidates for the same Scene Workspace render/previz truth.
- Any broad "the app is broken" note that can be replaced with a current, precise defect owner.

## Notes

- This story intentionally turns the raw inbox batch into current truth before coding.
- It should be the first product-truth pass after Story 194's multi-clip work if the next question is "what still feels broken on Brick & Steel?"
- If this run proves the canonical UI-scout cadence is also stale, create or run the canonical FP1 scout separately rather than mixing reports.

## Plan

1. Capture the exact original Brick & Steel inbox batch from `git show 90a67ec^:docs/inbox.md` into `docs/reports/story-196-brick-steel-product-truth-scrub/raw-inbox-90a67ec-parent.md`. Treat current `docs/inbox.md` separately because it now contains only the later UI Plan and xAI image-provider notes.
2. Launch the worktree API/UI against the existing primary-checkout Brick & Steel artifacts instead of copying output into this worktree. The API should use worktree code with `create_app(workspace_root=Path("/Users/cam/Documents/Projects/cine-forge"), enable_startup_dependency_checks=False)`, and the UI should run from this worktree with `CINE_FORGE_API_URL` pointed at that API.
3. Produce a route/evidence manifest before judgment: project summary, artifact-group counts, current scene 001 render/previz prompt/video/validation refs, character design-study state for Brick Braddock and Dick Steel, and current inbox contents.
4. Run the desktop product-truth path through `brick-steel-full-retired`: Home, Characters, Brick Braddock, Dick Steel, Scene Workspace `scene_001?tab=previz`, Scene Workspace `scene_001?tab=render`, and the relevant prompt/video/validation artifact detail links. Capture screenshots, console/page/HTTP errors, and DOM facts for the acceptance checks.
5. Run a mobile spot check for Home plus Scene Workspace Previz and Render, adding Characters/mobile only if the desktop pass shows a live design-study or navigation risk.
6. Build `triage-matrix.md` with one row per historical symptom and current note. Classify each as fixed/stale, live, rehomed, provider/config-only, not reproducible, or follow-up-needed, with exact route/artifact evidence.
7. Route still-live defects conservatively. Add notes to existing owners when ownership is already clear (Story 185 UI structure, Story 197 reference-pack/product-quality, Story 198 duplicate-character adjudication, Story 195 production xAI readiness). Create new stories only for live defects without a current owner. Do not start broad UI ADR work or xAI-image implementation in this story.
8. Scrub only the currently live inbox notes that the matrix has safely routed. The historical batch is already absent from `docs/inbox.md`, so the closeout is report-backed routing rather than a second deletion of that batch.
9. Verify according to touched scope: for docs/report/story-only edits run `pnpm methodology:compile`, `pnpm methodology:check`, `git diff --check`, and targeted link/search checks. If implementation code changes unexpectedly, add the relevant unit/lint/UI build checks and restart local services before browser verification.

## Work Log

20260430-1133 - story-created: created from approved inbox triage as the cleanup owner for stale and current Brick & Steel product notes. Evidence: current inbox batch plus related completed stories 139, 180, 191, 192, 193, and 194. Next step: `/build-story 196`.

20260504-2031 - exploration-plan: completed the build-story planning pass before implementation. Evidence: checkout is clean on `codex/story-196-brick-steel-product-truth-scrub`; Story 196 is still Pending; `make check-size` flags large UI/backend owners but the expected first slice is docs/report/inbox routing only; current `docs/inbox.md` contains only the later UI Plan and xAI image notes, while the original Brick & Steel batch is recoverable from `90a67ec^:docs/inbox.md`; the primary checkout has the representative `output/brick-steel-full-retired` artifacts, while this worktree has no `output/`; the current route owners are `ProjectHome`, `EntityListPage`, `EntityDetailPage`, `SceneWorkspacePage`, `PrevizPanel`, `GeneratedVideoPanel`, and `ArtifactDetail`. Decision: use worktree code against the primary checkout workspace root for browser truth, capture the historical inbox before any routing, and pause at the human implementation gate. Next step: user approval, then promote the story to In Progress and execute the report/browser pass.

20260504-2047 - implementation-start: plan approved. Promoted Story 196 to In Progress. Implementation will capture the historical Brick & Steel inbox, inspect the current primary-checkout Brick & Steel artifact state through this worktree's code, browser-check the surfaced Home/Characters/Scene Workspace/Artifact Detail path on desktop and mobile, and route current notes only after the matrix preserves evidence. Next step: create the report packet before any inbox cleanup.

20260504-2107 - build-complete: completed the product-truth scrub and left the story In Progress for validation. Evidence: captured the historical Brick & Steel inbox from `90a67ec^:docs/inbox.md`, captured the current inbox before routing, wrote `docs/reports/story-196-brick-steel-product-truth-scrub/evidence.md`, `triage-matrix.md`, `artifact-snapshot.json`, and browser screenshots/summary. The build browser pass checked 12 desktop/mobile routes with 0 blank screens, 0 console/page/HTTP errors, and 8 visible AI-previz plus 8 visible render videos on both desktop and mobile Scene Workspace checks. Current artifacts show exact clip-001 dialogue bullets, direct character reference inputs for all 8 render clips, completed Brick/Dick design studies, duplicate character truth still live for Story 198, and no scene-001 keyframe artifact. Routed the current UI Plan note to Story 185, routed the current xAI images note to Story 197, created Story 201 for the live keyframe-affordance warning, scrubbed `docs/inbox.md` to `No live items.`, and refreshed methodology state/generated views. Checks: `pnpm methodology:compile` passed with existing methodology warnings, `pnpm methodology:check` passed with outputs current, `git diff --check` passed, `py_compile` passed for the browser script, and both JSON report files parse. No product backend/UI code changed, so unit/lint/build suites were not run. Next step: `/validate 196`.

20260504-2127 - validation-complete: validated Story 196 and found no material implementation defects after tightening the evidence packet. Evidence reviewed: local diff, story acceptance criteria, ADR-002, ADR-003, `docs/design/decisions.md`, Ideal refs R7/R8/R10/R11/R12, spec refs 5.3/5.5/5.6/6.3/6.4/7.1/10.3, methodology state/graph/stories/build-map, `artifact-snapshot.json`, `triage-matrix.md`, and browser screenshots/summary. Validation reran the browser packet with an added mobile Characters route, producing 13 checked routes with 0 blank screens, 0 console/page/HTTP errors, 0 video-count mismatches, and 8 visible AI-previz plus 8 visible render videos on desktop and mobile Scene Workspace. The rerun also confirmed two non-fatal missing expected-text observations: generated-video detail does not show the literal `scene_render.mp4` filename despite rendering a video, and mobile Home does not expose `Start Scene Work`; the latter is now explicitly routed to Story 185. Fresh checks: `pnpm methodology:check`, `git diff --check`, browser script `py_compile`, and JSON parse checks passed. Backend/unit/lint and UI lint/type/build checks were not run because this diff changes docs/report/story/methodology surfaces only, not product backend/UI code. Recommendation: close now via `/mark-story-done 196`.

20260504-2135 - story-done: marked Story 196 Done after `/finish-and-push` invoked the close-out chain. Evidence: build and validation gates were complete; acceptance criteria and tasks were checked; the report packet captured historical/current inbox truth, 13-route desktop/mobile browser evidence, artifact snapshot, current follow-up owners, and inbox scrub state; no product backend/UI code changed; methodology, diff, JSON, and browser-script checks passed. Close-out also added the Story 196 changelog entry, reran `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` with 852 passed / 183 deselected / 1 known mark warning, and reran `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` with all checks passed. Remaining work is intentionally outside Story 196: Story 201 owns keyframe affordance truth, Story 198 owns duplicate character adjudication, Story 197 owns reference/image/provider visual fidelity, Story 185 owns UI hierarchy/mobile scene-entry visibility, and Story 199 owns casting/table-read shaping. Next step: `/check-in-diff`.

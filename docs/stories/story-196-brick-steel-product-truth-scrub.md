---
id: "196"
title: "Brick & Steel Product Truth Scrub"
status: "Pending"
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
**Status**: Pending
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

- [ ] A report maps every Brick & Steel inbox symptom to current evidence: fixed/stale, still live, intentionally rehomed, or not reproducible with a clear reason.
- [ ] The normal surfaced Brick & Steel scene path is exercised on desktop and mobile at least across Home, Characters, Scene Workspace Previz, Scene Workspace Render, and relevant artifact/detail links.
- [ ] The pass specifically checks black-screen recovery, Open/Jump behavior, keyframe/animatic discoverability, GPT-image completion/error truth, exact-dialogue prompt truth, multi-clip previz/render visibility, and final-render/reference truth.
- [ ] Any still-live defect becomes either a focused story, a work-log addition to an existing open story, or a clearly documented defer/discard decision. Do not leave verified defects only in the report.
- [ ] `docs/inbox.md` is scrubbed after the notes are routed. It should not keep stale duplicates of story-owned defects.
- [ ] The report distinguishes product-quality failures from provider/configuration failures and from already-fixed local-code issues.

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

- [ ] Build a symptom inventory from the pre-triage inbox, grouped by black-screen/recovery, navigation/discoverability, design-study images, previz, render, keyframes, user edits, and eval/test coverage.
- [ ] Re-check the exact current story/code surfaces for each likely owner before declaring a note fixed.
- [ ] Run a desktop browser pass through the current Brick & Steel surfaced path and capture screenshots, console/page errors, API status, and route evidence.
- [ ] Run a mobile spot check for the most relevant Scene Workspace path and any surface that looked risky on desktop.
- [ ] Inspect current prompt/video/artifact detail for scene 001 where needed, especially final render and AI previz clip artifacts.
- [ ] Produce `docs/reports/story-196-brick-steel-product-truth-scrub/triage-matrix.md` or equivalent with symptom-by-symptom disposition.
- [ ] Create focused follow-up stories only for still-live defects that are not already owned. Prefer adding notes to existing stories when the ownership is genuinely the same.
- [ ] Scrub `docs/inbox.md` once the matrix and stories preserve the routed truth.
- [ ] Check whether this pass makes any old docs or stale report claims redundant; update them or create a follow-up.
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python` if backend code changes
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/` if backend code changes
  - [ ] UI: `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` if UI code changes
- [ ] If story metadata, report indexes, or methodology state changes: `pnpm methodology:compile` and `pnpm methodology:check`
- [ ] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [ ] Browser verification: desktop and mobile evidence with clean console output or a documented blocker
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 - Data Safety:** Is the scrub capture-first before deleting inbox text?
  - [ ] **T1 - AI-Coded:** Is each disposition concrete enough for a future agent?
  - [ ] **T2 - Architect for 100x:** Did we avoid creating backlog for stale defects?
  - [ ] **T3 - Fewer Files:** Did follow-ups reuse existing owners where possible?
  - [ ] **T4 - Verbose Artifacts:** Is the evidence matrix complete?
  - [ ] **T5 - Ideal vs Today:** Does the current surfaced path feel easier and more honest?

## Workflow Gates

- [ ] Build complete: implementation finished, required checks run, and human summary shared
- [ ] Validation complete or explicitly skipped by user
- [ ] Story marked done via `/mark-story-done`

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

1. Capture the pre-scrub inbox text in the story report so deletion from `docs/inbox.md` is safe.
2. Walk the real Brick & Steel route and inspect current artifacts.
3. Build the disposition matrix and create follow-ups only for verified live defects.
4. Scrub the inbox and regenerate methodology surfaces.

## Work Log

20260430-1133 - story-created: created from approved inbox triage as the cleanup owner for stale and current Brick & Steel product notes. Evidence: current inbox batch plus related completed stories 139, 180, 191, 192, 193, and 194. Next step: `/build-story 196`.

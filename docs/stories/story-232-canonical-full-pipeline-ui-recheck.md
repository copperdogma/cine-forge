---
id: "232"
title: "Canonical Full-Pipeline UI Recheck"
status: "Blocked"
priority: "High"
ideal_refs:
  - "vision-level preference: Easy, fun, and engaging"
  - "R1 (story understanding)"
  - "R10 (playable assembly at every stage)"
  - "R12 (transparency & control)"
spec_refs:
  - "spec:5.6"
  - "spec:6"
  - "spec:7"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "156"
  - "185"
  - "201"
category_refs:
  - "spec:5"
  - "spec:6"
  - "spec:7"
compromise_refs: []
input_coverage_refs: []
architecture_domains: []
roadmap_tags:
  - "ui-product-truth"
  - "full-pipeline"
  - "canonical-fixture"
legacy_system: ""
---

# Story 232 — Canonical Full-Pipeline UI Recheck

**Priority**: High
**Status**: Blocked
**Ideal Refs**: Easy, fun, and engaging; R1; R10; R12
**Spec Refs**: spec:5.6; spec:6; spec:7
**ADR Refs**: ADR-002; ADR-003; docs/design/decisions.md
**Depends On**: 156; 185; 201

## Goal

Refresh the overdue FP1 product-truth walkthrough on a fresh project using the
canonical short screenplay. Establish the actual current surfaced boundary,
quality of guidance, and honest status on desktop plus mobile Home/Render.
Keep a dated Pass/Issues Found/Blocked report with exact evidence; a narrow
smoke or reused project must not masquerade as a fresh full walkthrough.

## Eval Ladder Context

FP1 is the existing full-path manual product-acceptance surface in spec:5.6,
not a new capability benchmark. Its latest full report is 2026-04-12, beyond
the 14-day cadence. Stories185/201 supplied targeted proof but expressly did
not refresh FP1. No new model comparison, scorer, or default decision is proposed.

## Acceptance Criteria

- [x] Freeze the runbook/fixture and bounded execution envelope before starting;
  resolve existing provider authority and declare maximum surfaced actions,
  estimated spend stop rules, and enforcement limitations before any paid portion.
  Record genuine access/spend blockers without bypassing them.
- [ ] A fresh project is created from open_frequency_short.fountain through
  normal surfaced intake, then follows the runbook's desktop route through the
  current honest scene-render boundary. No copied artifacts, seeded substrate,
  manual pipeline controls, or raw-artifact starting points count as acceptance.
- [x] Same-project mobile Home plus representative Render surface are inspected;
  screenshots, console errors, exact next actions, furthest reached boundary,
  and functional/polish/trust defects are recorded.
- [x] Dated report, docs/ui-scout.md and state.ui_scout agree on what actually
  ran. A blocked or incomplete run is labeled accordingly and never called Pass.
- [x] Concrete product defects link focused owning stories; historical reports
  remain intact. Stop after one bounded report rather than retrying to green.

## Out of Scope

- Model tournaments, default changes, broad UI redesign, or paid reruns without
  a predeclared execution envelope
- Treating Story185's local cut as fresh FP1 or silently refreshing its date
- Reopening the completed setup migration in156 or hiding new defects inside it

## Approach Evaluation

- **Simplification baseline**: Use the existing fixture, runbook and report
  template. A single model call cannot establish actual browser behavior.
- **AI-only**: Useful for observed UX judgment, insufficient without the real UI.
- **Hybrid**: Browser operation plus human-like judgment and deterministic
  route/console/provenance capture; reuse current installed tools.
- **Pure code**: Suitable for supporting checks, insufficient for calm/obvious UX.
- **Repo constraints / ADRs**: ADR-002 goal-oriented guidance, ADR-003 film
  elements, screenplay-first design doctrine, and representative-state rules.
- **Existing patterns to reuse**: Story156's established recurring lane,
  docs/ui-scout/report-template.md and the full-pipeline walkthrough runbook.
- **Eval**: One honest FP1 walkthrough; no scored AI eval. If scored evidence is
  later added, its registry/provenance/mismatch gates become required.

## Tasks

- [x] Resolve execution/spend authority, current browser capability for normal
  intake, provider availability and fresh-project naming; then promote only
  when genuinely ready. Fixture exists (3447 bytes); no fresh project is proven.
- [ ] Execute the exact surfaced desktop path, recording defects when observed.
- [x] Spot-check mobile Home/Render on the same normal project.
- [x] Preserve evidence and publish the bounded report into the existing lane.
- [x] Update scout index/state and any runbook boundary that truly changed.
- [x] Route defects into existing owning stories or a justified focused story.
- [x] Run methodology compile/check. No product suites for evidence-only work;
  any actual product fix must follow its owning story's proportional gates.
- [x] Search affected docs and remove stale current claims without deleting history.
- [x] Verify tenets: T0 immutable/capture-first; T1 inspectable handoff; T2 no new
  scaffold; T3 existing lane; T4 exact evidence; T5 filmmaker-first judgment.

## Workflow Gates

- [ ] Build complete: implementation finished, required checks run, and human summary shared
- [ ] Validation complete or explicitly skipped by user
- [ ] Story marked done via `/mark-story-done`

## Blocker Summary

The declared bounded media envelope cannot be checked from the current fresh
Render preflight: no clip count/cost is exposed before preparation and the
budget guard only pauses after a stage/wave. The run stopped before media,
not because of credentials or a provider failure. Full FP1 remains incomplete.

## Blocker Evidence

docs/ui-scout/2026-10-23-open-frequency-local.md and
docs/reports/story-229-canonical-ui/render-before.txt document the actual fresh
project, completed run-fae39865, USD5 UI thresholds, missing upfront media
estimate and precise unperformed steps. BudgetGuard.evaluate confirms the
after-stage/wave pause boundary. User approved existing OpenAI key reuse.

## Unblock Condition

Establish a declared, inspectable bounded media execution path through the
normal surfaced workflow, then reassess232 and continue with a new report.
Do not silently increase spend, fabricate a hard cap, or count targeted233
guidance verification as complete FP1. No credential decision is pending.

## Architectural Fit

- **Owner**: existing UI scouting/reporting lane, no new application owner.
- **Contracts**: existing project/API/artifact contracts; no schema additions.
- **Sizes**: evidence/state edits only. Run check-size if implementation emerges;
  oversized AppShell/SceneWorkspace/API files are not incidental cleanup targets.
- **Decision context**: current UI runbook, scout index, state and screenplay-first
  doctrine; Story156 established the process and explicitly retained it closed.

## Files to Modify

- docs/ui-scout/<date>-<fresh-project>-local.md — dated evidence report
- docs/ui-scout.md — current coverage and report index
- docs/methodology/state.yaml — actual FP1 result/freshness, no assumed Pass
- docs/runbooks/full-pipeline-ui-manual-walkthrough.md — only verified boundary changes
- This story — execution envelope, readiness, results and next actions

## Redundancy / Removal Targets

No new framework. Supersede stale current coverage through new dated evidence;
retain old reports and avoid duplicate UI campaign/setup stories.

## Notes

Canonical fixture: tests/fixtures/ingest_inputs/open_frequency_short.fountain.
The current runbook requires fresh /new intake, mvp_ingest from surfaced chat,
Home/Intent/Scenes/Characters/Locations/Inbox, scene_001 Shots/Storyboard/Render,
a surfaced current-scene render, then mobile Home/Render.

## Plan

The single bounded walkthrough has stopped at Render preflight and published an
honest blocked/partial report. Intake, complete mvp_ingest, desktop route sweep,
and same-project mobile Home/Render are proven. Actual media generation and
prompt/video/validation output remain unperformed. Do not proceed under the
invalidated assumption that a USD5 stage/wave threshold bounds the media stage.

Next, complete the targeted guidance repair233 without paid generation. Before
resuming232, establish an inspectable media work/spend envelope using the
existing surfaced workflow or a separately justified focused repair. Reassess
the blocker with that evidence, freeze a new envelope, and create a new report
for the actual rendered path. Preserve this report and the2026-04-12 last full
Pass. No credential provisioning or model comparison is required.

## Work Log

20261023-1048 — blocker reassessment: existing end_at/scene_scope/render_clip_ids provide a preparation/inspection substrate, but no surfaced bounded media route is established. Official current provider docs additionally confirm configured Veo3.1 preview retired2026-10-22, Sora/VideosAPI2026-09-24, default Imagen42026-08-17. Earlier discovery covered chat catalogs and did not qualify these endpoints.032 now owns omitted video costs and fail-before-unavailable/unpriced media;138 retains planning follow-up. Unblock still unmet: current supported provider transport plus inspectable work/spend are needed before normal paid continuation. No credential question remains, no media request was sent, and existing completed UI guidance/parser fixes do not constitute full FP1. Evidence: docs/research/story-032-media-accounting-2026-10-23.md.


20261023-0928 — created: Story185 closure left the active UI campaign referencing only terminal196/201/185. Compiler correctly rejected that stale ownership. A bounded owner search found156 was a completed setup story, while185/196/201 were targeted passes that did not reset FP1. Created this distinct dated walkthrough cycle, retained194-day stale freshness and14-day cadence, verified the3447-byte fixture, and left statusDraft because normal intake/provider/execution bounds are unproven. Next: include this owner in the active campaign and let the next authorized triage compare it with other actionable work.

20261023-0953 — readiness: User explicitly approved reusing the existing CineForge OpenAI key; no credential was created or changed. Live `/discover-models --check-new` queried all five configured catalogs successfully (output/story-232-model-discovery.txt), without inference or default changes. Normal `/` → New Project → `/new` opened the real file chooser. Read-only source trace found intake uses Sonnet4.6, breakdown uses Sonnet4.6, and scene render uses OpenAI text work plus Google image/video defaults. All required aliases are present; catalog access is proven, generation/billing is not. BudgetGuard pauses after stages/waves and cannot guarantee a strict per-call render ceiling. First execution envelope is only one canonical-fixture quick-scan, at most two provider attempts, 256 output tokens each, conservative USD0.10 bound for this 3447-byte ASCII fixture at published Sonnet4.6 pricing; no pipeline CTA or render is authorized by this initial envelope. Pricing source: https://platform.claude.com/docs/en/models/sonnet-4-6/overview ($3/$15 per million input/output tokens, checked today). Freeze a separate pipeline envelope before starting breakdown; inspect render preflight before allowing any media stage. No reruns or model comparisons. Next falsifiable check: the documented chooser can attach the actual fixture and surface a fresh project name.

20261023-0954 — plan: Normal file chooser successfully attached the canonical fixture and surfaced AI-detected Open Frequency, resolving the intake-readiness uncertainty. Promoted Draft to Pending. Refined the envelope criterion to require honest surfaced action bounds and spend/pause limitations rather than inventing a strict per-provider cap unsupported by the shipped app. Plan above limits this run to one intake, one breakdown, and at most one preflight-qualified current-scene render; no repeats. Existing user authorization covers this evidence collection. Next: compile Pending state, start execution, configure normal budget settings before the breakdown CTA.

20261023-0954 — execute: Pending compile passed; starting the approved normal UI evidence run. No product logic changes. Next: fresh project creation, surfaced budgets, single breakdown.

20261023-1007 — bounded-run: Fresh normal /new intake produced open-frequency; input hash matched canonical fixture. Surface Settings savedUSD5 project/run thresholds. One Break Down Script run-fae39865 completed all5 stages,4 scenes and Bible/config, app-estimatedUSD0.0809394 excluding intake scan. Desktop routes and same-project mobile Home/Render passed navigation/console/fit checks; media generation was not launched because its count/cost could not be qualified under the declared envelope. Published blocked/partial dated report, retained lastfullPass2026-04-12, and linked233 for three next-action defects. Artifact inspection additionally found PRE-DAWN split into location suffix Pre/timeDAWN (next ingest candidate) and unsupported American-country Bible assertion (model-wrong/non-runtime-blocking manual observation, no numeric eval). Marked232Blocked with explicit evidence/unblock condition; no stale proceed plan or pending credential question. Next: validate233 guidance and reassess a bounded media continuation separately.

20261023-1029 — follow-up:233 guidance and005 literal-heading repairs are independentlyvalidated/Done, with before/after evidence linked from the original report. Canonical ui_scout retains issues_found with232 as the remaining continuation owner. The latest frozen contractv26 and all targeted validations pass; no media was generated and full FP1 remains incomplete. ScriptBible country assertion is a separate non-runtime-blocking source-grounding candidate for existing093, not an adopted score. Saved app goal still reportsBlocked from the earlierkeyquestion; its tool cannotreactivate it. The user answer is recorded; no new credential decision is pending. Nextautomaticcontinuation requires the app Resume control, then reassess232 with an honest bounded surfaced plan.

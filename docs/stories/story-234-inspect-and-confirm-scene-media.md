---
id: "234"
title: "Inspect and Confirm Scene Media"
status: "Done"
priority: "High"
ideal_refs:
  - "R7 (generate -> react -> refine)"
  - "R8 (cost and quality choices)"
  - "R10 (playable assembly)"
  - "R11 (production readiness per scene)"
  - "R12 (transparency and control)"
spec_refs:
  - "spec:6.3"
  - "spec:7.1"
  - "spec:8.1"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "193"
  - "194"
  - "195"
  - "032"
category_refs:
  - "spec:6"
  - "spec:7"
  - "spec:8"
compromise_refs:
  - "C3"
  - "C6"
input_coverage_refs: []
architecture_domains:
  - "generation_and_visualization"
  - "api_service_and_operator_console"
roadmap_tags:
  - "scene-generation"
  - "operator-control"
  - "cost-transparency"
legacy_system: ""
---

# Story 234 — Inspect and Confirm Scene Media

**Priority**: High
**Status**: Done
**Ideal Refs**: R7, R8, R10, R11, R12
**Spec Refs**: spec:6.3, spec:7.1, spec:8.1
**ADR Refs**: ADR-002, ADR-003
**Depends On**: 193, 194, 195, 032

## Goal

Let an operator prepare a scene's Render or AI Previz clip plan, inspect the actual selected work and its known video cost, and explicitly confirm those reviewed inputs before video generation. Execution must not silently consume newer inputs or generate unreviewed references. This advances the active spec:6/spec:7 climb lane while retaining honest provider and cost limitations.

## Eval Ladder Context

- Parent: FP1 full-pipeline UI walkthrough (Story 232), still Blocked after October 23 provider/pricing/accounting evidence. The current UI has no separate review/confirm boundary; it starts the full recipe from scene and per-clip controls.
- Child: deterministic API/worker consumption tests plus representative normal-workflow desktop/mobile preparation and blocked inspection. These establish operator control, not media quality or full-pipeline success.
- No new model selection or capability comparison: pure execution authorization, provenance, request shaping, cost disclosure and UI orchestration. Do not pay for a model tournament to test identity or arithmetic.
- Rerun only the affected parent walkthrough portion after this slice. Successful live media and full-film acceptance remain contingent on provider qualification and credential readiness; Codex quota alone does not clear them.

## Acceptance Criteria

- [x] Render and AI Previz expose preparation ending at `render_clip_planning`, with explicit notice that planning may incur text-AI cost and no video submission during preparation.
- [x] Current-scene all-unit or selected-clip inspection creates an immutable typed execution-plan artifact without provider calls. It shows actual normalized durations, resolution, target identity, canonical sourced video estimate where available, exclusions and blockers. Unknown total cost remains unknown.
- [x] Both scene-wide and per-clip UI entry points require inspection and explicit confirmation; empty/loading/stale/blocked work cannot confirm. Saved outputs and their provenance remain inspectable.
- [x] Confirmation binds selected work, effective parameters, recipe/pack, input refs and content, optional absences and relevant mutable media selection/bytes. API rejects stale/conflicting plans before enqueue; worker validates actual resolved inputs before paid prerequisites and consumes the validated snapshot rather than fresh latest lookups.
- [x] Retired/unpriced provider, automatic-reference and uncertain-job replay guards remain effective. New automatic reference generation cannot occur after approval. Costs already incurred before any later failure remain recorded.
- [x] Preparation and confirmation are headless-capable through normal API and driver routes; run context records the execution plan. Single-clip and subset behavior is consistent between inspection and execution.
- [x] Focused regression/security/boundary checks pass; representative desktop and mobile browser paths have screenshots and clean console or a documented environment blocker. No seeded fixture is counted as product acceptance.

## Out of Scope

- All-scenes confirmation, budget reservations/hard dollar caps, invoice-grade total quotes, generalized crash recovery or paid-job reconciliation.
- Provider or model adoption/qualification, quality promotion, changes to creative planning prompts, and claiming FP1 completion.
- Story 138's broader profiles/model comparison framework. Existing provider-blocked states must be usable and honest within this slice.

## Approach Evaluation

- **Simplification baseline / pure code:** Existing recipes already support `end_at`; the adapter already shapes requests and resolves canonical video prices. Reuse that substrate and add one typed immutable approval boundary. Baseline call-site audit finds four direct paid-start paths and no reviewed-plan authority.
- **AI-only / hybrid:** Rejected for this boundary. Identity, permissions, arithmetic and provenance belong in code; another model cannot guarantee exact approved inputs and would add unnecessary cost and uncertainty. Creative planning remains in existing modules.
- **Repo constraints / ADRs:** ADR-002 specifies preflight summaries and plan-then-execute for expensive operations. ADR-003 keeps expensive film work on demand and compiled prompts read-only. Immutable artifacts and runtime context are existing repository contracts.
- **Alternatives:** A UI-only estimate is insufficient because the worker may load later inputs. An API-only digest check leaves a check/use race. A general transaction/reservation platform is larger than this current-scene workflow needs.
- **Patterns reused:** ArtifactStore, ArtifactRef, RuntimeParams, SceneExecutionScope, existing scene preflight, render unit selection/preparation, canonical VideoPrice and media receipts.
- **Eval:** Provider-free tests inject changes before enqueue and between approval/worker/use; inspect request equality and zero-call guards. Browser proof covers the surfaced same contract.

## Architectural Fit

- New focused schema/service own inspection and confirmation. Thin delegation in existing API/service/driver owners; no new responsibility piled into god objects.
- Typed Pydantic contracts come first: execution plan, source binding, selected unit and create-plan request/response. Frontend mirrors those contracts.
- `make check-size` baseline recorded at `/private/tmp/cineforge-triage-oct24-size.txt`: API models 645, orchestrator 668, service 1285, scene-actions 895, driver engine 1211, GeneratedVideoPanel 658, PrevizPanel 957, UI types 613. Extract UI cards/controllers before adding new behavior. Backend large owners receive only thin wiring; modified oversized methods require extraction before new logic.
- Shared preparation currently reloads latest refs and anticipated output versions. Approval digest excludes output counters but includes all consumed inputs; confirmed execution must consume a snapshot. Planning alone must not compile prompts or generate references.

## Files to Modify

- New `src/cine_forge/schemas/media_execution_plan.py`, focused services/resolver and API router — typed immutable plan authority.
- `schemas/runtime_params.py` (61), API models (645), orchestrator (668), service (1285), run-start preflight (59), schema/router registration — thin transport and early guard.
- Render adapter `main.py` (108), `unit_preparation.py` (123), `render_unit.py` (169), `resolved_inputs.py` (281), orchestration/transport helpers as needed — share actual unit shaping and consume approved frozen inputs.
- Driver CLI and focused headless helper — expose existing engine end boundary and plan creation/confirmation without UI.
- UI GeneratedVideoPanel (658), PrevizPanel (957), ScenePlanUnitSummary (328), focused shared inspection/controls/hook/API/types files — extracted ownership, no direct paid-start bypass.
- Focused backend/UI regression tests and this work log; methodology generated outputs after metadata changes.

## Tasks

- [x] Define schemas and freeze the API contract before parallel backend/UI consumption.
- [x] Share normalized unit selection/pricing, bind inputs and enforce API/worker consumption, including single-clip behavior and optional/mutable inputs.
- [x] Extract oversized UI responsibilities; implement prepare, inspect, select and confirm on both surfaces.
- [x] Add headless preparation/inspection/confirmation route and contextual provenance.
- [x] Remove obsolete direct paid-start handlers and misleading combined planning/generation copy.
- [x] Run proportional backend/unit/API/schema/security regression tests and Ruff; run UI tests, lint, TypeScript and production build. Preserve explicit acceptance and mandatory gates; reuse current unchanged evidence rather than blanket reruns.
- [x] Verify API health plus desktop/mobile normal-workflow preparation/inspection/blocked confirmation, inspect artifacts and console, record evidence.
- [x] Update related runbook/UI-scout and current contract manifest if touched inputs require it, preserving all historical manifests/evidence; compile methodology.
- [x] Central Tenets: T0 immutable evidence preserved; T1 focused readable owners; T2 bounded current-scene scope; T3 shared resolver/contracts; T4 live work log; T5 operator control toward the Ideal.

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

## Redundancy / Removal Targets

Remove the four direct full paid-run handlers from Render/AI Previz panels and duplicated control state. Keep one shared request-shaping/pricing implementation. Replace wording that conflates planning completion with generated media completion.

## Notes

- General problem class: optimistic concurrency / time-of-check to time-of-use in queued costly execution. [RFC 9110 §13.1.1](https://www.rfc-editor.org/rfc/rfc9110.html#section-13.1.1) documents conditional state checks; [CWE-367](https://cwe.mitre.org/data/definitions/367.html) explains why narrowing the interval or rechecking alone does not remove the race. Adopt an API precondition plus immutable consumed snapshot, not a latest-state check followed by latest-state reload. Local applicability test: mutate a dependency after approval and prove no unreviewed request can be submitted. External advice is a design basis, not local proof.
- Story boundary check: 193 owns clip-plan creation; 194 owns plan consumption/multi-clip output; 138 owns broad budget profiles and comparisons; 232 owns full-path acceptance. This story owns the operator approval boundary across API/worker/UI and does not silently claim those wider outcomes.
- Model sizing: factual health/inbox packets used Luna; exploration/UI use Sol high; expensive execution authorization/backend uses Astra high. An independent strategic reviewer requests Astra ultra; served identity is not independently verified.

## Plan

1. Finish typed contract first. Parent owns story/state/docs; backend lead owns backend/API/schema/tests/headless helper; UI worker owns `ui/`. Backend may delegate explicitly disjoint helper files to architecture worker. No concurrent ownership overlap.
2. Resolve effective inputs once through shared adapter logic. Snapshot/hash reviewed data; immutable execution-plan artifact excludes run IDs/timestamps/anticipated outputs. Guard API conflicts/staleness and worker consumption before any paid work. Never backfill new references after approval.
3. Extract existing large UI card/controller responsibilities. Replace direct scene/clip launch with current-scene preparation, backend inspection, selected subset review and explicit confirmation. Display blocker reasons and price exclusions inline on desktop/mobile.
4. Focused mutation tests before broader checks. API health and normal pipeline project browser proof; current provider blocker is an expected visible state, not a successful paid render. Keep prior saved media visible.
5. Independent validation/review, docs/evidence, canonical graph compilation and story closure through owning skills within the user's standing autonomous loop authorization. No commit or push in this resumed batch without a new request.

## Work Log

20261024-2152 — Exploration and plan: fresh five-lane triage selected the operator media review boundary over Script Bible grounding and Export focus. Verified current `end_at` substrate and missing CLI flag, four direct paid UI handlers, shared canonical price resolver, latest-ref reads and single-clip selection mismatch. Outcome sought is clear reviewed work before spending; no new provider proof is implied. Plan is authorized by Cam's resumed triage/build loop. Next: schema-first implementation and injected-change tests.

20261024-2157 — Strategic review: independent Astra ultra reviewer recommends continue with a strict current-scene seam, show known generation blockers before paid preparation, and return to another product defect when the bounded seam passes. Accepted. Describe approved inputs and scope, not a frozen final provider prompt because compilation is later. Review assessed supplied plan before the written story was complete; parent completed it before substantive implementation. First methodology compile rejected inline frontmatter arrays because the local parser expects block lists; converted syntax to the established story format, no semantic plan change. Next: validate generated graph and focused schema/worker boundary.

20261024-2158 — First runtime probe: isolated API8002/UI5176 serving the normal primary Open Frequency project exposed an existing AI-previz credential guard that blocked preparation despite end_at=render_clip_planning. Fixed the guard to respect selected stages; after a clean API restart the browser enabled preparation while retaining the missing-xAI generation blocker. Started normal current-scene preparation run-a7501f88; timeline/tracks/shot planning completed and clip planning is in progress. No video request is authorized or attempted by preparation. Browser also motivates preserving server readiness on the confirmed route, not trusting the UI alone. Next: inspect completed plan/artifacts and verify selected-cost disclosure on desktop/mobile.

20261024-2204 — Validation findings retained: first independent code review found preparation recovery losing end_at, inconsistent entity enumeration, hidden single-clip playback, and run-state publication after the approval guard. Accepted all four with direct path verification and focused regressions. A separate deterministic probe confirmed distinct approvals can target the same output version; bounded renderer execution serialization is necessary to preserve immutable outputs. Two actual normal preparation runs completed before video (scene1 previz estimate $0.2713494, scene2 render estimate $0.2312416), but both UI completion transitions hit a React composed-ref update loop. Initial HMR hypothesis was rejected by a frozen-code repeat. Story remains In Progress; failure evidence/research and repair boundaries are in docs/reports/story-234/review-findings.md. Next: fix these same-slice defects, rerun affected checks and the real browser transition.

20261024-2213 — Boundary and browser repair validated: accepted first-review fixes passed54 existing/shared driver/CLI/plan tests plus5 recovery/order/state tests and5 renderer-lock tests. A new real API→orchestrator→driver→renderer→persister test passed with only video generation stubbed, proving reference-only confirmation, selected scope, one-use claim, lineage and complete USD0.20 accounting. Relevant offline integration checks passed23. Broad offline unit run had2432passes/3failures: inherited frozen-provider byte mismatch, intentionally disabled dotenv fixture (correct configuration rerun7passes), and the newly added UI test missing ledger ownership (inventory corrected; final check pending). No live-video call.

20261024-2214 — Normal workflow transition now passes: narrow official Slot1.2.5 fix applied in isolated dependencies; primary dependency hashes unchanged. Fresh scene3 preparation run-70ed8443 produced8clips/58seconds, auto-inspected USD2.90 video-only, and kept chat/UI alive. Mobile390×844 selected one clip → USD0.40; empty selection and generation blockers prevent confirm; Render exposes retired provider and unknown estimate before planning. Desktop1440×1000/mobile screenshots and zero post-fix console errors retained. Total recorded text-preparation estimates USD0.7826238. Preserved original crash evidence and unscored planning mismatches; report is partial FP1 continuation, not media quality or full-pipeline acceptance. Next: second review, manifest identity, formal validation and closure.

20261024-2216 — Second findings-first review accepted three same-scope defects: approval narrowed the recipe past its existing validation stage; approved-run recovery queued a worker guaranteed to conflict with one-use scope; paused preparation was treated as successful terminal work. Chosen bounded repairs preserve scoped downstream validation, reject approved recovery before queueing with a fresh-inspection handoff, and classify preparation success separately from pause. The user should retain the same validation/trust signals after approval and receive an actionable pause state. Next: focused regressions, narrow independent recheck, then frozen manifest and closure assessment. No new recovery platform or provider campaign.

20261025 — Closeout resumed with explicit validate, check-in and push authority, then stop. Continuing strategic review had recommended closing this bounded story after the three lifecycle repairs; no new triage slice is authorized in this closeout. Reused source-backed TOCTOU reasoning still applies. Prior documentation write was not executed when automatic approval review could not run due to exhausted quota; no unsafe-action determination was made. Latest focused backend/driver/CLI run passes76tests. Next: final generated-output scoping tests, paused/no-op UI, contract manifest and landing.

20261025 — /validate and /mark-story-done: all seven acceptance criteria met within current-scene control scope; final report docs/reports/story-234/validation.md recommends Close now (gradeB).76focused backend tests plus2new selection cases,23relevant integration,35UI,45manifest/ledger tests and full Ruff/static/build gates pass. Reused broad unit/consumer evidence is documented; inherited frozen-provider mismatch remains non-runtime-blocking and byte-identical to base. Final bounded independent review found no material issue. Normal budget-pause check0calls/0cost correctly offers run Resume; original budget restored. Final manifestv33 preserves v32pre-lint snapshot and all historical bytes. Story marked Done; current explicit finish-and-push authority carries through commit/push, then stop. No live video, media-quality promotion or fullFP1pass.

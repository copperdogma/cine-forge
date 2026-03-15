# Story 031: Change Propagation (Semantic Impact Layer)

**Status**: Done
**Created**: 2026-02-13
**Spec Refs**: 2.3 (Revision and Change Propagation — Layer 2), 2.8 (QA — AI assessment)
**Depends On**: Story 002 (pipeline foundation — Layer 1 structural invalidation), Story 014 (role system — AI assessment roles), Story 010 (entity graph — dependency understanding)

---

## Goal

Implement **Layer 2 — Semantic Impact Assessment**: the AI-powered analysis that examines stale artifacts (flagged by Layer 1 structural invalidation from Story 002) and triages them. Each stale artifact is assessed: does it actually need revision given what changed, or is it still valid despite the upstream change?

Layer 1 (Story 002) is conservative — it marks everything downstream as stale. Layer 2 is intelligent — it understands what changed and evaluates whether each stale artifact is actually affected.

---

## Acceptance Criteria

### Semantic Impact Assessment
- [ ] AI-powered diff analysis:
  - [ ] Diffs the old and new versions of the changed artifact.
  - [ ] Examines each stale downstream artifact.
  - [ ] Triages each stale artifact into:
    - [ ] `needs_revision` — confirmed affected, with notes on what needs to change.
    - [ ] `confirmed_valid` — still correct despite upstream change.
- [ ] Assessment produces "needs work" annotations with:
  - [ ] Rationale (why does it need work?).
  - [ ] What specifically changed upstream.
  - [ ] Which role flagged it.
  - [ ] Suggested revision approach.
- [ ] Assessment is on-demand (not automatic) — user or Director triggers it.

### Health Status Transitions
- [ ] Artifact health now fully functional:
  - [ ] `valid` → `stale` (Layer 1, automatic).
  - [ ] `stale` → `needs_revision` (Layer 2, AI assessment).
  - [ ] `stale` → `confirmed_valid` (Layer 2, AI assessment).
  - [ ] `needs_revision` → `valid` (after revision and re-validation).
  - [ ] `confirmed_valid` → `valid` (acknowledged by user/Director).
- [ ] Manual override: user or Director can manually set status without AI assessment.
- [ ] Artifact APIs expose live graph health plus latest assessment or override provenance; they do not rely on stale snapshot metadata for current status.

### UI / UX
- [ ] Users can trigger scope preview and semantic assessment from the product UI without using direct API calls.
- [ ] Stale, needs-revision, and confirmed-valid states are understandable at a glance in shared health rendering.
- [ ] Artifact detail surfaces show the current health rationale, assessment provenance, and the relevant next actions (assess, acknowledge, or manually override).
- [ ] Inbox / home / artifact-list surfaces continue to surface items that need attention after assessment; `needs_revision` and `confirmed_valid` do not disappear into backend-only state.

### Impact Scope Analysis
- [ ] Before running full assessment, provide a quick scope preview:
  - [ ] How many artifacts are stale?
  - [ ] What types of artifacts are affected?
  - [ ] Estimated cost of running the assessment.
- [ ] User can choose to assess all, assess selectively, or skip assessment and manually triage.

### Assessment Module
- [ ] Module/utility for running semantic impact assessment.
- [ ] Configurable: which AI model to use, cost budget for assessment.
- [ ] Can run on a subset of stale artifacts (selective assessment).

### Schema
- [ ] `ImpactAssessment` Pydantic schema:
  ```python
  class ArtifactImpact(BaseModel):
      artifact_ref: ArtifactRef
      previous_health: Literal["stale"]
      assessed_health: Literal["needs_revision", "confirmed_valid"]
      rationale: str
      upstream_change_summary: str
      suggested_revision: str | None
      confidence: float
      assessing_role: str

  class ImpactAssessment(BaseModel):
      trigger_artifact_ref: ArtifactRef      # The artifact that changed
      trigger_diff_summary: str               # What changed
      assessments: list[ArtifactImpact]
      total_stale: int
      total_needs_revision: int
      total_confirmed_valid: int
      assessment_cost: CostRecord
  ```
- [ ] Schema registered in schema registry.

### Testing
- [ ] Unit tests for semantic impact assessment logic (mocked AI).
- [ ] Unit tests for health status transitions.
- [ ] Unit tests for scope preview.
- [ ] Unit tests for selective assessment.
- [ ] Integration test: change artifact → Layer 1 staleness → Layer 2 assessment → triaged health statuses.
- [ ] Schema validation on all outputs.

---

## Design Notes

### Layer 1 vs. Layer 2
Layer 1 is instant, free, and conservative: "something upstream changed, everything downstream might be affected." Layer 2 is slow, costs money, and intelligent: "I looked at what changed, and only these 3 of 15 stale artifacts actually need revision."

Most of the time, Layer 1 is sufficient — the user sees stale artifacts and manually decides what to re-run. Layer 2 is valuable when the change is small and the downstream graph is large (e.g., a minor script edit that affects 50+ downstream artifacts).

### Assessment Cost
Running Layer 2 on a large project could be expensive — every stale artifact gets an AI call. The scope preview and selective assessment features let the user control costs. Budget caps from Story 032 should also apply.

---

## Tasks

- [x] Design and implement `ImpactAssessment`, `ArtifactImpact` schemas.
- [x] Register schemas in schema registry.
- [x] Implement semantic impact assessment logic.
- [x] Implement health status transition management.
- [x] Implement scope preview (count, types, estimated cost).
- [x] Implement selective assessment (assess subset of stale artifacts).
- [x] Implement manual override for health status.
- [x] Wire into artifact store health tracking.
- [x] Persist impact assessment results immutably and surface live health/provenance through artifact APIs.
- [x] Implement the UI flow for previewing assessment scope, running assessment, and resolving assessed states.
- [x] Write unit tests.
- [x] Write integration test.
- [x] Run `make test-unit` and `make lint`.
- [x] Update AGENTS.md with any lessons learned.

---

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Architectural Fit

- **Owning class/module**: this should be a focused impact-assessment service plus a thin API router, not a driver recipe stage. The work is on-demand, selective, budget-aware, and closer to `services/intent_mood.py` than to a pipeline module.
- **Data contracts**: add a dedicated artifact schema for `ImpactAssessment` and API DTOs for preview / assess / override flows. `RoleContext.invoke()` is the wrong transport because Story 031 needs a custom structured response and potentially larger prompts.
- **File sizes**: `src/cine_forge/api/app.py` (1034), `src/cine_forge/api/service.py` (1025), and `tests/unit/test_api.py` (1238) are already oversized; keep them thin and create focused new files instead. Likely touch points that are still safe to extend directly: `src/cine_forge/artifacts/graph.py` (174), `src/cine_forge/artifacts/store.py` (252), `src/cine_forge/api/artifact_manager.py` (295), `src/cine_forge/api/models.py` (372), and `src/cine_forge/roles/runtime.py` (373).
- **Decision context consulted**: `docs/ideal.md` (R12, R14, R15), `docs/spec.md` §2.3, Story 002, Story 010, Story 014, ADR-002, `docs/design/decisions.md`, and `docs/retrofit-gaps.md`. No separate ADR currently defines semantic-impact persistence, so this story should stay inside existing artifact-store and API patterns rather than inventing a second state system.

## Files to Modify

- `src/cine_forge/schemas/impact.py` — new immutable impact-assessment artifact schema(s)
- `src/cine_forge/schemas/__init__.py` — export new schema types
- `src/cine_forge/driver/schema_registry.py` — register `impact_assessment`
- `src/cine_forge/artifacts/graph.py` — live health transitions and provenance summary storage
- `src/cine_forge/artifacts/store.py` — thin helpers if needed for saving assessments / decisions and reading live health
- `src/cine_forge/services/impact_assessment.py` — new semantic assessment + scope preview service
- `src/cine_forge/api/models.py` — request / response DTOs and live artifact-health response shape
- `src/cine_forge/api/artifact_manager.py` — assessment preview, run, override, and live-health read helpers
- `src/cine_forge/api/routers/impact.py` — new focused router
- `src/cine_forge/api/service.py` — thin delegators only
- `src/cine_forge/api/app.py` — router registration only
- `ui/src/components/HealthBadge.tsx` — shared semantics + tooltip copy for new health states
- `ui/src/pages/ArtifactDetail.tsx` — impact preview / assess / override workflow
- `ui/src/pages/ProjectArtifacts.tsx` — remove duplicate health rendering and surface actionable states coherently
- `ui/src/pages/ProjectInbox.tsx` — attention items for `stale`, `needs_revision`, and `confirmed_valid`
- `ui/src/pages/ProjectHome.tsx` — dashboard counts / copy for assessed states
- `ui/src/components/AppShell.tsx` — inbox badge counts stay aligned with ProjectInbox
- `ui/src/lib/types.ts` — API type support for live health details and impact endpoints
- `ui/src/lib/api/artifacts.ts` — impact request helpers
- `ui/src/lib/hooks/artifacts.ts` — impact mutations / query invalidation
- `tests/unit/test_artifact_store.py` or a new focused health test file — graph transition coverage
- `tests/unit/test_impact_assessment.py` — service-level assessment / preview tests
- `tests/unit/test_api_impact.py` — focused API coverage without growing `tests/unit/test_api.py`

## Redundancy / Removal Targets

- Any ad hoc graph-key parsing or one-off health mutations that bypass the dependency graph API
- Any attempt to force this into `RoleContext.invoke()` despite the existing direct-`call_llm` service pattern already fitting better
- Duplicate API logic in `app.py` or `service.py` that should live in a dedicated router / manager helper

## Plan

### Exploration Notes (2026-03-14)

**Ideal alignment**

- This story directly closes Ideal R15 and also improves R12 and R14. It is not premature infrastructure: Story 097 and any iterative artifact-editing flow need semantic change propagation to avoid turning every manual edit into permanent ambiguity.
- `docs/retrofit-gaps.md` does not mark this area as a shrinking compromise. The missing capability is still core product debt.

**Approach evaluation**

- **AI-only**: viable for the actual semantic judgment. During exploration, two live `call_llm` probes with `claude-sonnet-4-6` correctly separated a cosmetic rename from a motivation change:
  - spelling/name-only change with unaffected downstream visual-direction text → `confirmed_valid`
  - core motivation change with downstream performance text still grounded in the old motive → `needs_revision`
- **Pure code**: rejected. The repo already treats semantic story understanding as AI work, and Story 031 explicitly asks for reasoning about whether an artifact is still correct despite upstream change.
- **Hybrid**: best fit here. Deterministic code should handle stale-scope discovery, selective targeting, budget preview, persistence, and health transitions. AI should only decide semantic impact and produce rationale.

**Repo-fit / why this is the right shape here**

- The existing repo pattern for structured, non-trivial AI output is a focused service that calls `call_llm` directly with a custom Pydantic response schema (`src/cine_forge/services/intent_mood.py`, `src/cine_forge/modules/world_building/continuity_tracking_v1/main.py`). Reusing that pattern is better than extending `RoleContext.invoke()` just for one story.
- Story 002 already established that live health belongs to the dependency graph. Story 031 should extend that graph with richer live-health state and provenance, not create a second mutable status store elsewhere.
- The story's `ImpactAssessment` schema should be persisted as an immutable artifact. If the assessment only lives in the mutable graph JSON, we lose the reasoning history and violate the "nothing is ever lost" bar.
- Manual overrides should reuse the existing immutable `decision` artifact pattern where practical; the graph should keep only the current live summary plus a pointer back to the immutable source artifact.

**Structural health check**

- `make check-size` run during exploration. Relevant files and current line counts:
  - `src/cine_forge/artifacts/graph.py` — 174
  - `src/cine_forge/artifacts/store.py` — 252
  - `src/cine_forge/api/app.py` — 1034 (large; router include only)
  - `src/cine_forge/api/artifact_manager.py` — 295
  - `src/cine_forge/api/models.py` — 372
  - `src/cine_forge/api/service.py` — 1025 (large; delegators only)
  - `src/cine_forge/pipeline/graph.py` — 686 (large; avoid unless required)
  - `src/cine_forge/roles/runtime.py` — 373
  - `tests/unit/test_artifact_store.py` — 158
  - `tests/unit/test_pipeline_graph.py` — 593 (large; avoid if possible)
  - `tests/unit/test_api.py` — 1238 (large; do not keep adding coverage here)
- No new event type is required.
- New data crossing layer boundaries must be schema-first: artifact data goes in `src/cine_forge/schemas/impact.py`; API request/response contracts go in `src/cine_forge/api/models.py` before the router or manager uses them.

**Scope coherence adjustment**

- Small inline expansion folded into this story: artifact detail/list APIs must expose live graph health and provenance. Without that, Story 031 could persist decisions but still report stale snapshot metadata from the original artifact file.
- UI work is now folded into this story. The minimum coherent frontend slice is: shared health semantics, inbox/home/action counts, and artifact-detail controls for preview / assess / resolve. Leaving those out would create a backend-only feature that users cannot meaningfully operate.

### Task-by-Task Plan

#### Task 1 — Add immutable impact-assessment schemas and live graph health contract

- Create `src/cine_forge/schemas/impact.py` with `ArtifactImpact` and `ImpactAssessment`.
- Export the new schema via `src/cine_forge/schemas/__init__.py` and register `impact_assessment` in `src/cine_forge/driver/schema_registry.py`.
- Extend `src/cine_forge/artifacts/graph.py` with explicit helpers for:
  - reading current health plus provenance summary for one artifact
  - setting assessed health (`needs_revision` / `confirmed_valid`)
  - acknowledging or manually overriding back to `valid`
- Keep the dependency graph as the live-status source of truth, but store only summaries and source refs there. The full reasoning must live in immutable artifacts.
- Done when a caller can ask the graph for both current status and the source artifact or decision that established it.

#### Task 2 — Build the semantic assessment and scope-preview service

- Create `src/cine_forge/services/impact_assessment.py`.
- Implement deterministic scope preview:
  - find stale descendants for a trigger artifact
  - summarize count + artifact types
  - support selective assessment by filtering to requested refs
  - estimate cost deterministically from prompt-size heuristics plus `estimate_cost_usd`
- Implement AI assessment:
  - diff old vs new trigger artifact versions
  - assemble each stale downstream artifact's current payload and lineage context
  - call `call_llm` directly with a custom response schema
  - default to a continuity/canon role prompt, with configurable model and optional role override
- Persist the result as an immutable `impact_assessment` artifact, then update graph health summaries for the assessed artifacts.
- For manual override, reuse the existing immutable decision pattern where practical, then write the resulting live status back to the graph.
- Done when the service can preview a subset, assess a subset, and produce both an immutable artifact and updated live graph health.

#### Task 3 — Expose a headless/API trigger path without growing the large files

- Add `src/cine_forge/api/routers/impact.py` with focused endpoints for:
  - previewing assessment scope
  - running an assessment
  - manually overriding or acknowledging health
- Add request/response DTOs in `src/cine_forge/api/models.py` for preview, assessment, override, and live artifact-health details.
- Extend `src/cine_forge/api/artifact_manager.py` with impact helpers and update `read_artifact()` so artifact detail responses include live graph health/provenance instead of only the persisted snapshot metadata.
- Keep `src/cine_forge/api/service.py` to thin delegators and `src/cine_forge/api/app.py` to router registration only.
- Done when Story 031 is fully usable via API or direct service calls without any UI dependency.

#### Task 4 — Add the product UI for preview, assessment, and resolution

- Extend the shared `HealthBadge` component so `stale`, `needs_revision`, and `confirmed_valid` each have clear user-facing copy and optional rationale tooltips.
- Remove the local badge implementation from `ui/src/pages/ProjectArtifacts.tsx` and reuse the shared component everywhere.
- Add an impact-actions card to `ui/src/pages/ArtifactDetail.tsx` for latest artifact versions:
  - stale artifacts: preview scope, assess this artifact, assess all affected, manual triage buttons
  - needs_revision: show rationale and suggested revision plus manual "mark current" escape hatch
  - confirmed_valid: show rationale and acknowledgement action to clear the state to current
- Update Project Inbox, App Shell unread counts, and Project Home health summary so `needs_revision` and `confirmed_valid` remain visible as attention items after assessment.
- Keep the UI scoped to existing artifact surfaces; do not invent a separate impact dashboard.
- Done when the health lifecycle is usable from the browser without requiring direct API calls.

#### Task 5 — Add focused tests and post-build verification

- Add `tests/unit/test_impact_assessment.py` for:
  - preview count/type estimation
  - selective assessment
  - mocked AI classification into `needs_revision` vs `confirmed_valid`
  - immutable artifact persistence + graph update coupling
- Add focused graph tests in `tests/unit/test_artifact_store.py` or a new small companion file for health transition helpers and provenance lookup.
- Add `tests/unit/test_api_impact.py` for the new endpoints and for artifact-detail live-health overlays. Do not grow `tests/unit/test_api.py`.
- Add targeted frontend tests only if an existing local pattern is easy to extend; otherwise rely on browser verification plus type/lint/build checks for this pass.
- Required checks after implementation:
  - `make test-unit PYTHON=.venv/bin/python`
  - `.venv/bin/python -m ruff check src/ tests/`
  - `pnpm --dir ui run lint`
  - `cd ui && npx tsc -b`
  - `pnpm --dir ui run build`
- Runtime / behavioral verification after implementation:
  - run one cosmetic-change fixture and one semantic-change fixture through the service
  - confirm the first returns `confirmed_valid` and the second returns `needs_revision`
  - inspect the saved `impact_assessment` artifact and graph health details manually
- Browser verification plan:
  - open a project with at least one stale artifact
  - from artifact detail, preview impact scope, run an assessment, and confirm the state changes in-place
  - verify Project Inbox and Project Home counts reflect the new state
  - capture a screenshot and confirm no new console errors

### Impact Analysis

- **Could break**: artifact detail consumers if response shape changes carelessly; driver consumers if graph-health helpers regress existing stale semantics; pipeline/status UI if it implicitly assumes only `stale` is actionable.
- **Should stay untouched**: `src/cine_forge/pipeline/graph.py` unless testing proves current pipeline status output becomes misleading enough to block the story. That file is already large and should not absorb new logic speculatively.
- **No human-approval blocker identified**: no new dependency, no migration plan, and no public API compatibility obligation in this greenfield codebase.

## Work Log

*(append-only)*

20260314-2336 — exploration + planning: confirmed Story 031 aligns with Ideal R15/R12/R14 and is not premature; traced artifact graph, store, API manager/service/app, role runtime, and UI health consumers; ran `make check-size`; reviewed Story 002 / Story 010 / Story 014, ADR-002, `docs/design/decisions.md`, and `docs/retrofit-gaps.md`; exploration also included two live `call_llm` probes with `claude-sonnet-4-6` showing a simple semantic-assessment prompt can correctly separate a cosmetic rename (`confirmed_valid`) from a motivation change (`needs_revision`) at low single-call cost. Key risk found: artifact detail reads currently return snapshot metadata rather than live graph health, so live health/provenance exposure was folded into this story as a small required scope expansion. Next step: await human approval on the implementation plan before changing code.
20260315-0017 — implementation: added immutable `ImpactAssessment` / `ArtifactImpact` schemas and registered `impact_assessment`; extended graph/store live health helpers for structural invalidation, semantic assessment provenance, latest-ref lookups, and manual overrides; added `ImpactAssessmentService`, focused API routes/DTOs, and live-health overlay responses so artifact APIs expose graph truth instead of stale snapshot metadata. Frontend now uses shared health semantics across artifact list, inbox, app-shell badge counts, entity badges, and the artifact-detail impact workflow card; `ProjectHome` now surfaces the attention summary in the live `FreshImportView` route instead of a dormant alternate branch. Focused coverage landed in `tests/unit/test_impact_assessment.py`, `tests/unit/test_api_impact.py`, `tests/unit/test_artifact_store.py`, and `tests/unit/test_schema_registry.py`. Next step: finish runtime smoke and browser verification, then hand off to `/validate`.
20260315-0026 — verification + runtime smoke: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed (`540 passed, 125 deselected`); `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` passed; `pnpm --dir ui exec tsc -b` and `pnpm --dir ui run build` passed; `pnpm --dir ui run lint` reported only the existing fast-refresh warnings in `ui/src/components/StatusBadge.tsx`, `ui/src/components/ui/badge.tsx`, `ui/src/components/ui/button.tsx`, `ui/src/components/ui/tabs.tsx`, and `ui/src/lib/right-panel.tsx`. Runtime smoke used a seeded project `story-031-smoke` on `http://127.0.0.1:5174/story-031-smoke` against the local API on `http://127.0.0.1:8000` (`/api/health` returned `{\"status\":\"ok\",\"version\":\"2026.03.14-08\"}`). Browser verification confirmed: home shows live attention state, inbox badges reflect attention counts, artifact detail preview reported `2` pending stale artifacts with the expected types and cost, semantic assess transitioned the scene to `needs_revision` and the shot plan to `confirmed_valid`, and acknowledging the confirmed-valid shot plan reduced inbox/home attention from `2` to `1`. Playwright console check reported zero errors. Next step: run `/validate` and decide whether any residual risks remain before closure.
20260315-0034 — validation: re-ran required checks (`make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`, `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint`, `pnpm --dir ui exec tsc -b`, `pnpm --dir ui run build`, and targeted pytest for Story 031 files); all passed aside from the existing five React fast-refresh lint warnings outside this story’s scope. Browser validation on `story-031-smoke` reconfirmed the home attention card, the `needs_revision` artifact detail, and zero console errors; API smoke also confirmed selective assessment on fresh project `story-031-selective-validate` (assessing only the scene moved it to `needs_revision` while the shot plan remained `stale`). Validation findings remain: configurable assessment budget from the story AC is still unimplemented, ImpactAssessmentCard bypasses the repo’s required `useLongRunningAction`/OperationBanner + chat-timeline pattern for >1s actions, and `ProjectHome` still contains a dormant `AnalyzedView` branch with duplicated health-summary logic. Recommended next step: keep the story open, fix the long-running-action UX, and either implement the budget control or explicitly rescope that AC before `/mark-story-done`.
20260315-0051 — remediation + validation: added request-scoped `budget_cap_usd` support through preview/assess API contracts, service enforcement, and the artifact-detail UI; refactored assessment actions onto `useLongRunningAction` so the OperationBanner and chat timeline show active/completed impact work; removed the dormant `AnalyzedView` branch from `ProjectHome`; and added automated selective-assessment plus budget-cap coverage in `tests/unit/test_impact_assessment.py` and `tests/unit/test_api_impact.py`. Re-ran the full suite (`make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` → `544 passed, 125 deselected`; Ruff clean; `pnpm --dir ui exec tsc -b` clean; `pnpm --dir ui run build` clean; `pnpm --dir ui run lint` still only reports the existing five fast-refresh warnings; `pnpm --dir ui run lint:duplication` stayed under threshold at 1.95% duplicated lines). Browser smoke on `http://127.0.0.1:5174/story-031-selective-validate/artifacts/shot_plan/scene_001/1` confirmed the budget-cap preview warning (`$0.0051` estimate vs `$0.0001` cap), the live OperationBanner + chat entry while assessment was running, and the final `needs_revision` rationale after assessment; `http://127.0.0.1:5174/story-031-smoke` still showed the home attention card (`1 artifact need attention. 4 current.`), console errors remained at `0`, and `/tmp/story-031-home-fix.png` captured the home state. Next step: `/mark-story-done`.
20260315-0053 — completion: Story 031 closed after clean validation. Acceptance criteria are now satisfied end-to-end: semantic assessment persists immutable artifacts, live health/provenance flows through API/UI, request-scoped budget caps are enforced, selective assessment is covered automatically, and the browser smoke captured both the long-running operation feedback and the home/inbox attention states. Repository bookkeeping updated in `docs/stories.md` and `CHANGELOG.md`. Next step: `/check-in-diff`.
20260315-0106 — validation rerun reopened the story: re-ran the full required suite (`make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` → `544 passed, 125 deselected`; Ruff clean; targeted pytest for Story 031 paths → `24 passed`; `pnpm --dir ui run lint` still only reports the existing five fast-refresh warnings; `pnpm --dir ui exec tsc -b` clean; `pnpm --dir ui run build` clean) and repeated browser/API smoke against `http://127.0.0.1:5174/story-031-validate-rerun` with local API health `{"status":"ok","version":"2026.03.15-01"}`. Fresh validation found a medium-severity gap in the long-running-operation record: the impact assessment completion state is updated only in memory, so `output/story-031-validate-rerun/chat.jsonl` still persists `{"type":"ai_status","content":"Assessing artifact impact..."}` after success and a reload shows a misleading permanent record instead of the completed summary. Story status was reopened to `In Progress`, the done gate was unchecked, and the recommended next step is to persist long-running action completion/failure updates through the chat store/backend before rerunning `/validate`.
20260315-0903 — remediation + revalidation: extended `src/cine_forge/api/chat_store.py` so chat persistence replaces existing messages by stable ID instead of leaving stale state behind, added targeted regression coverage in `tests/unit/test_chat_store.py`, added `persistMessage()` to `ui/src/lib/chat-store.ts`, and updated `ui/src/lib/use-long-running-action.ts` so long-running status cards sync their final state to the backend after any custom success/failure formatting. Re-ran targeted checks (`tests/unit/test_chat_store.py`, `tests/unit/test_impact_assessment.py`, `tests/unit/test_api_impact.py` → `19 passed`), then the full suite (`make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` → `546 passed, 125 deselected`; Ruff clean; `pnpm --dir ui run lint` still only reports the existing five fast-refresh warnings; `pnpm --dir ui exec tsc -b` clean; `pnpm --dir ui run build` clean). Runtime smoke on a fresh seeded project `story-031-persist-validate3` confirmed the fix end-to-end: local API health returned `{"status":"ok","version":"2026.03.15-01"}`, artifact detail at `http://127.0.0.1:5174/story-031-persist-validate3/artifacts/shot_plan/scene_001/1` assessed successfully, `output/story-031-persist-validate3/chat.jsonl` now persisted `{"type":"ai_status_done","content":"Assessing artifact impact — complete: 1 artifact assessed, 0 need revision, 1 confirmed valid."}`, a full page reload preserved that completed summary in the chat panel, Playwright console errors remained `0`, and `/tmp/story-031-chat-persist-fix.png` captured the post-reload state. Next step: `/check-in-diff`.
20260315-1012 — post-close UI polish: fixed the artifact-detail version-history layout so wide health badges wrap inside the sidebar card instead of overflowing its border. `ui/src/pages/ArtifactDetail.tsx` now uses a wrapping header row for each version pill and allows the badge text to wrap cleanly in constrained space. Re-ran `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (`546 passed, 125 deselected`), `pnpm --dir ui run lint` (same five pre-existing fast-refresh warnings only), `pnpm --dir ui exec tsc -b`, and `pnpm --dir ui run build`. Browser verification on `http://127.0.0.1:5174/story-031-persist-validate3/artifacts/shot_plan/scene_001/1` showed the `Confirmed Valid` badge fully contained within the version-history card, console errors stayed at `0`, and `/tmp/story-031-version-history-wrap-fix-2.png` captured the corrected layout. Next step: `/check-in-diff`.
20260315-1021 — validation rerun after the version-history wrap fix: collected the full Story 031 local delta, re-read Ideal R12/R14/R15 plus spec §§2.3/2.8 and ADR-002 references, then re-ran the full check suite (`make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` → `546 passed, 125 deselected`; Ruff clean; targeted Story 031 pytest set → `33 passed`; `pnpm --dir ui run lint` still only reports the existing five fast-refresh warnings; `pnpm --dir ui exec tsc -b` clean; `pnpm --dir ui run build` clean). Browser validation on `http://127.0.0.1:5174/story-031-persist-validate3/artifacts/shot_plan/scene_001/1` reconfirmed the semantic-impact UI, showed the `Confirmed Valid` badge wrapped cleanly inside the version-history card with no overflow, and Playwright console errors stayed at `0`; `/tmp/story-031-validate-overflow-fix.png` captured the validated state. Validation is clean; left the `/mark-story-done` gate unchecked per workflow and the recommended next step is `/mark-story-done`.
20260315-1026 — completion: Story 031 is formally closed after the clean validation rerun on the version-history wrap fix. The required evidence remains green across the full suite (`make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` → `546 passed, 125 deselected`; Ruff clean; targeted Story 031 pytest set → `33 passed`; `pnpm --dir ui run lint` still only reports the existing five fast-refresh warnings; `pnpm --dir ui exec tsc -b` clean; `pnpm --dir ui run build` clean). Browser verification on `http://127.0.0.1:5174/story-031-persist-validate3/artifacts/shot_plan/scene_001/1` confirmed the semantic-impact workflow still behaves correctly and the `Confirmed Valid` badge remains fully contained inside the `Version History` card with zero console errors; `/tmp/story-031-validate-overflow-fix.png` captured the validated state. Next step: `/check-in-diff`.

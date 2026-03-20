# Story 131 — Preference Learning from User Choices

**Priority**: Medium
**Status**: Done
**Ideal Refs**: R13 (learn from user choices)
**Spec Refs**: spec:4.5 (Suggestion System), spec:1.6 (Metadata & Auditing), spec:9 (Memory & Collaboration)
**ADR Refs**: None found after search
**Depends On**: Story 017 (Suggestion and Decision Tracking)

## Goal

Give CineForge a first-class, transparent preference-learning loop. The system already records suggestions and decisions, but it does not yet treat user selections, rejections, and edits as reusable taste signals. This story defines the backlog home for capturing those signals, deriving a project-level preference profile, and making future suggestions measurably better without hiding what the system learned.

## Acceptance Criteria

- [x] V1 scope is explicit: design-study variant decisions (`selected_final`, `favorite`, `rejected`, `seed_for_variants`) produce typed preference signals linked to the originating round/image/prompt context and final user choice.
- [x] Preference signals are queryable at the project level and can be summarized into a transparent preference profile.
- [x] The user can inspect what the system believes it has learned and disable or clear that learning.
- [x] The first AI behavior that consumes preference learning is explicit and explainable: design-study prompt generation cites the learned-preference input it used or exposes an equivalent explanation path.
- [x] Because this changes AI behavior, implementation adds a lightweight targeted probe that proves preference signals are actually applied to the next design-study generation path.

## Out of Scope

- Cross-project or cross-user taste learning
- Fine-tuning models on exported training data
- Silent personalization with no user-visible audit trail
- Replacing the existing suggestion/decision artifact system

## Approach Evaluation

- **AI-only**: Not enough. We need deterministic capture of signals and provenance before any model summarizes them.
- **Hybrid**: Most likely. Deterministic signal capture plus either deterministic aggregation or AI-assisted summarization into a preference profile.
- **Pure code**: Plausible for v1 if the profile remains simple weighted counts, but pure heuristics may become brittle for nuanced taste patterns.
- **Repo constraints / ADRs**: AGENTS explicitly says preference learning is a first-class concept and `project.json`/project settings are the durable home for user preferences. Story 017 already gives us immutable suggestion/decision artifacts to build from; duplicating that data model would be wrong.
- **Existing patterns to reuse**: Story 017 suggestion and decision artifacts, `src/cine_forge/roles/suggestion.py`, `src/cine_forge/roles/runtime.py`, project settings UI, chat action flows.
- **Eval**: No existing preference-learning eval is registered. Implementation should add a lightweight targeted probe or promptfoo scenario to verify that captured signals actually bias later suggestions and that the explanation surface matches reality.

## Tasks

- [x] Define the minimal typed preference-signal and preference-profile contracts before wiring capture code.
- [x] Lock V1 signal sources to design-study variant decisions; explicitly defer generic chat/suggestion-action capture to follow-on work.
- [x] Implement project-level query/storage rules plus a transparent inspection surface for learned preferences.
- [x] Feed the derived profile into the design-study prompt/compiler path without hiding the source signals.
- [x] Add a lightweight deterministic probe that verifies preference signals influence later design-study generations and provenance.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` → `599 passed, 139 deselected, 1 pre-existing pytest mark warning`
  - [x] Backend lint: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` → clean
  - [x] UI (if touched): `pnpm --dir ui install --frozen-lockfile`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` → lint clean except 5 pre-existing React fast-refresh warnings in unrelated files, typecheck clean, build clean with the existing Vite chunk-size warning
- [x] If UI is touched: verify the changed flow with browser tools when possible (screenshot + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker.
- [x] Search all docs and update any related to what we touched.
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

## Architectural Fit

- **Owning class/module**: V1 should use a focused preference service and router, not overload the existing suggestion lifecycle. Design-study decisions are real user taste signals, but they are not `Suggestion` lifecycle transitions, so forcing them into `SuggestionManager` would be the wrong abstraction.
- **Data contracts**: A new typed `PreferenceSignal` and a derived `PreferenceProfile` are required before data crosses backend↔API↔UI boundaries. If signals are persisted as artifacts, register a schema-first `preference_signal` artifact type before wiring call sites.
- **File sizes**: `src/cine_forge/ai/image.py` (509, already large), `src/cine_forge/api/service.py` (1082, oversized), `src/cine_forge/api/models.py` (475), `src/cine_forge/roles/runtime.py` (471), `ui/src/lib/types.ts` (552, oversized), `ui/src/components/ProjectSettings.tsx` (449), `src/cine_forge/api/routers/design_study.py` (427). The plan should prefer new focused files and thin integration points over adding more inline logic to those large files.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/spec.md`, `docs/build-map.md`, Story 017, Story 119, `docs/design/decisions.md`, and ADR-003. No ADR currently defines the preference-learning data model.

## Files to Modify

- `src/cine_forge/schemas/preferences.py` or a new adjacent schema file — define `PreferenceSignal` / `PreferenceProfile`
- `src/cine_forge/schemas/__init__.py` — export new preference contracts
- `src/cine_forge/driver/schema_registry.py` — register `preference_signal` if persisted as an artifact
- `src/cine_forge/services/preferences.py` — query/aggregate/clear preference signals and derive a profile
- `src/cine_forge/api/models.py` — typed API contracts for profile response and settings payload
- `src/cine_forge/api/routers/preferences.py` — focused project preference-profile endpoints
- `src/cine_forge/api/app.py` — router registration only; avoid adding more inline endpoints
- `src/cine_forge/api/service.py` — thin project-summary/settings plumbing only
- `src/cine_forge/api/routers/design_study.py` — capture V1 signals from variant decisions and thread profile use into the design-study path
- `src/cine_forge/ai/image.py` — compile learned-preference context into the existing deterministic image-prompt path
- `ui/src/lib/types.ts` — frontend preference-profile and settings types
- `ui/src/lib/api/projects.ts` and/or a new focused `ui/src/lib/api/preferences.ts` — profile fetch / clear / toggle calls
- `ui/src/components/ProjectSettings.tsx` plus a new focused child section if needed — inspection, enable/disable, clear
- `ui/src/components/DesignStudySourcesPanel.tsx` — label learned-preference provenance cleanly
- `tests/unit/test_preferences.py` — preference aggregation / profile derivation coverage
- `tests/integration/test_api_design_study.py` — end-to-end probe for signal capture + next-round prompt consumption
- `docs/evals/registry.yaml` — only if the chosen probe is promoted into a tracked eval entry instead of staying a deterministic integration test

## Redundancy / Removal Targets

- Any ad hoc taste-memory experiments added outside the new focused preference service
- Any attempt to hide durable preference data in `ui_preferences` or local component state instead of project-backed settings / artifacts
- Any attempt to overload `Suggestion` artifacts to represent design-study variant choices when the underlying event is not a suggestion lifecycle transition

## Notes

This item already existed in `spec.md` and `docs/retrofit-gaps.md`; the inbox entry was a duplicate waiting for a real backlog home. The hard rule is transparency: hidden taste inference would move away from the Ideal.

## Plan

### Eval-First Gate

- **Probe to use**: extend the existing design-study integration path so one deterministic probe verifies the full loop:
  1. user records design-study decisions (`favorite`, `rejected`, `seed_for_variants`, `selected_final`)
  2. the backend persists typed preference signals and exposes a project-level profile
  3. the next design-study generation includes learned-preference context in the compiled prompt and `sources_used`
- **Baseline today**:
  - `rg -n "PreferenceSignal|PreferenceProfile|preference_signal|preference_profile|learned_preferences" src ui docs tests` returns hits only in this story file
  - `src/cine_forge/api/routers/design_study.py` has `0` preference-learning references; it only mutates image decisions and `visual_reference_image`
  - `src/cine_forge/ai/image.py` has no `learned_preferences` source entry in `build_image_prompt()`
  - Practical baseline score: `0/3` on {typed signal persisted, profile queryable, next-generation consumer present}
- **Candidate approaches**:
  - **AI-only**: have an LLM read raw design-study history and synthesize taste each time. Rejected for v1 because it creates a hidden trust surface, adds cost to every generation, and fails the inspect/disable/clear requirement unless we still build deterministic storage.
  - **Hybrid**: deterministic signal capture plus AI-authored profile summary. Plausible later if signal volume or nuance grows, but not justified yet because the initial capture surface is narrow and the existing prompt compiler is deterministic.
  - **Pure code**: deterministic signal capture, deterministic profile derivation, and deterministic prompt enrichment. Chosen for v1 because Story 119 already established deterministic prompt compilation as the repo’s preferred pattern for design-study context.
- **Test the simplest first**:
  - For this story, the simplest viable approach is not “one more LLM call”; it is deterministic prompt/profile plumbing on top of existing user decisions. The success criterion can be verified at the prompt/compiler boundary without model-comparison work.

### Repo-Fit / Optimality Evidence

- **Why this approach fits CineForge**:
  - [ideal.md](/Users/cam/.codex/worktrees/a3c9/cine-forge/docs/ideal.md) `R13` requires transparent project-level learning from user choices, not opaque personalization.
  - [docs/design/decisions.md](/Users/cam/.codex/worktrees/a3c9/cine-forge/docs/design/decisions.md) already says subjective outputs should use a variational loop where the user chooses, rejects, and regenerates. Design-study decisions are therefore the cleanest real signal surface already in the product.
  - Story 119 established the design-study prompt compiler as a deterministic assembly step in `src/cine_forge/ai/image.py`; extending that compiler with learned-preference context is more coherent than adding a parallel AI summarizer.
  - AGENTS requires project-scoped durable preferences in `project.json`, not `localStorage`, and warns against hidden taste inference. This plan keeps durable controls in project settings and durable history in artifacts.
- **Main alternatives rejected**:
  - Reusing `Suggestion` artifacts directly: wrong abstraction for design-study image decisions, which are not lifecycle transitions on AI-authored suggestions.
  - Generic chat-action capture in v1: broader than the current repo supports cleanly because there is no general suggestion-response API/UI surface yet.
  - LLM-summarized taste profile first: more magic, less transparency, and harder deterministic verification for no proven gain on the initial narrow scope.

### Structural Health Check

- `make check-size` findings relevant to this story:
  - `src/cine_forge/api/service.py` — `1082` lines
  - `src/cine_forge/api/app.py` — `1043` lines
  - `src/cine_forge/ai/image.py` — `509` lines
  - `src/cine_forge/api/models.py` — `475` lines
  - `src/cine_forge/roles/runtime.py` — `471` lines
  - `ui/src/lib/types.ts` — `552` lines
  - `ui/src/components/ProjectSettings.tsx` — `449` lines
  - `src/cine_forge/api/routers/design_study.py` — `427` lines
- **Plan implication**:
  - Add a new focused `preferences.py` service and `preferences.py` router instead of growing `api/service.py` or `api/app.py`
  - Keep `api/app.py` changes to router registration only
  - Keep `api/service.py` changes to thin project-summary/settings plumbing only
  - Avoid touching `RoleContext.invoke()` (`src/cine_forge/roles/runtime.py:239`) in v1; it is already a `115`-line method and design-study decisions do not require it
  - If the project-settings UI grows materially, extract a `ProjectPreferenceLearningSection.tsx` child instead of enlarging `ProjectSettings.tsx`
  - If a new artifact type is introduced, register it before any recipe/runtime code depends on it

### Implementation Sequence

#### Task 1: Schema-first preference foundation

- **Files**:
  - new `src/cine_forge/schemas/preferences.py`
  - `src/cine_forge/schemas/__init__.py`
  - `src/cine_forge/driver/schema_registry.py`
- **Changes**:
  - Define the minimum durable contracts:
    - `PreferenceSignal` — one immutable signal event, linked to project context and source decision
    - `PreferenceProfile` — derived project-level summary returned by the API
  - Keep the signal shape concrete and inspectable. Likely fields: signal id, source kind, entity type/id, decision kind, polarity, prompt/guidance excerpts, source image/round identifiers, and timestamps.
  - Register only `preference_signal` as an artifact if profile derivation stays computed-on-read.
- **Impact / risk**:
  - New cross-layer data requires schema-first discipline before API/UI wiring.
  - Over-designing the signal schema would make the story slower without adding user value.
- **Done when**:
  - The repo has a typed signal artifact contract and a typed profile response contract that other layers can import.

#### Task 2: Capture V1 signals from design-study decisions

- **Files**:
  - new `src/cine_forge/services/preferences.py`
  - `src/cine_forge/api/routers/design_study.py`
  - `tests/integration/test_api_design_study.py`
- **Changes**:
  - Add a focused preference service that can persist immutable signals and derive a project-level profile.
  - On design-study decision updates, emit signals for the V1 actions only:
    - positive: `selected_final`, `favorite`
    - negative: `rejected`
    - refinement request: `seed_for_variants` with optional guidance
  - Link signals to the concrete design-study context instead of inventing abstract taste taxonomies up front.
  - Keep toggles reversible by recording the new decision event and having profile derivation respect the latest effective decision per image.
- **Impact / risk**:
  - The current design-study state file is mutable and not enough for preference-history transparency by itself; the signal artifact is the durable audit layer.
  - Decision reversal semantics need care so the profile does not double-count stale choices.
- **Done when**:
  - A user design-study decision creates a durable signal artifact, and the integration test can prove it exists with the expected linked context.

#### Task 3: Expose project-level profile + durable controls

- **Files**:
  - `src/cine_forge/api/models.py`
  - new `src/cine_forge/api/routers/preferences.py`
  - `src/cine_forge/api/app.py`
  - `src/cine_forge/api/service.py`
  - `ui/src/lib/types.ts`
  - `ui/src/lib/api/projects.ts` and/or new `ui/src/lib/api/preferences.ts`
  - `ui/src/components/ProjectSettings.tsx` plus extracted child section if needed
- **Changes**:
  - Add a focused API to fetch the current project preference profile and clear its learned state.
  - Keep the durable enable/disable flag in project settings / `project.json`, surfaced in `ProjectSummary`.
  - Show the user what CineForge thinks it has learned, with the source signals or at least direct links/excerpts that explain the summary.
  - Provide explicit disable and clear actions.
- **Impact / risk**:
  - This changes public API contracts and project summary payloads.
  - `ui/src/lib/types.ts` and `ProjectSettings.tsx` are already large; prefer extraction instead of inlining another dense section.
- **Done when**:
  - The user can open project settings, inspect the learned profile, disable preference learning, and clear existing learned state.

#### Task 4: Consume the profile in the deterministic design-study prompt path

- **Files**:
  - `src/cine_forge/services/preferences.py`
  - `src/cine_forge/ai/image.py`
  - `src/cine_forge/api/routers/design_study.py`
  - `ui/src/components/DesignStudySourcesPanel.tsx`
  - `tests/integration/test_api_design_study.py`
- **Changes**:
  - Derive a small deterministic prompt context from the profile, for example:
    - favored cues / repeated positive guidance
    - avoided cues from rejections
    - recent variant-direction phrases that should bias the next round
  - Pass that into `build_image_prompt()` through a single path.
  - Add a provenance token such as `learned_preferences` to `sources_used` so the UI makes the behavior legible.
  - Keep the compiler deterministic; do not add an LLM summarization step here.
- **Impact / risk**:
  - `src/cine_forge/ai/image.py` is already `509` lines, so add helper functions rather than bloating `build_image_prompt()`.
  - The prompt enrichment must stay scoped and legible; dumping raw signal history into the prompt would be noisy and brittle.
- **Done when**:
  - The next design-study generation after recorded signals contains a deterministic learned-preference summary and exposes it via provenance.

#### Task 5: Verification, cleanup, and docs

- **Files**:
  - `tests/unit/test_preferences.py`
  - `tests/integration/test_api_design_study.py`
  - any touched docs/API typing files
- **Changes**:
  - Add focused unit coverage for signal reduction and profile derivation.
  - Extend the design-study integration test to prove the full story loop:
    1. capture decision signals
    2. read project profile
    3. generate again and see learned-preference prompt/provenance
  - Update docs/types for any new settings/API contracts.
  - Remove any abandoned local preference-state experiments if they become redundant.
- **Done when**:
  - The deterministic probe passes and there is no duplicate preference-learning path in the codebase.

### UI Verification Plan

- **Browser path**:
  1. Open an entity detail page with a design study.
  2. Mark one image `Favorite`, one `Reject` with guidance, and optionally one `Seed`.
  3. Open Project Settings and confirm the learned preference section shows a transparent summary plus disable / clear controls.
  4. Generate another design-study round and inspect the round’s sources panel for the learned-preference provenance label.
- **Fallback**:
  - If browser tooling is unavailable, use `docs/runbooks/browser-automation-and-mcp.md` and record the blocker in the work log.

### Recommended Scope Adjustment

- **Folded into this story**:
  - Narrow V1 to design-study variant decisions as the initial real signal surface.
  - Add a focused preference router/service instead of expanding the generic chat/suggestion stack.
- **Deferred follow-up (recommended, not included here)**:
  - Generic chat/suggestion-action capture across the broader project journal.
  - Relative effort: `M`
  - Reason: there is no existing general suggestion-response API/UI surface to hook cleanly, so absorbing that here would blur validation and inflate blast radius.

### Human Approval Blockers

- This plan introduces a new public API surface for preference profiles and a new persisted artifact type if signals are stored immutably.
- This plan intentionally does **not** touch `RoleContext.invoke()` or implement generic suggestion-button learning in v1. If you want the broader capture surface immediately, that is a larger scope increase.
- Verification environment note: the worktree still lacks a local `.venv`; the known working environment is `/Users/cam/Documents/Projects/cine-forge/.venv`.

## Work Log

20260313-1658 — triage: created from inbox item "AI preference learning from user choices". Existing homes checked: `spec.md` and `docs/retrofit-gaps.md` already tracked the gap, but no story existed. Next=`/build-story` when ready.
20260314 — backlog cleanup: promoted from `Draft` to `Pending`. The story now has a build-ready backlog home for the transparent preference-learning loop required by Ideal R13.
20260320-1023 — exploration: reviewed `docs/ideal.md` (R13, transparency, project-scoped taste), `docs/spec.md` (`spec:4.5`, `spec:1.6`, `spec:9`), `docs/build-map.md`, Story 017, Story 119, `docs/design/decisions.md`, and ADR-003; traced `src/cine_forge/{schemas/suggestion.py,roles/suggestion.py,roles/runtime.py,api/service.py,api/models.py,api/routers/design_study.py,ai/image.py}`, `ui/src/{components/ProjectSettings.tsx,components/DesignStudySection.tsx,components/DesignStudyImageCard.tsx,lib/types.ts,lib/api/projects.ts}`, and existing design-study/suggestion tests. Evidence: current code has no `PreferenceSignal` / `PreferenceProfile` implementation (`rg` hits only this story), `design_study.py` contains `0` preference-learning references, and `ai/image.py` has no `learned_preferences` provenance source. `make check-size` confirms the plan must avoid piling more logic into `api/service.py` (`1082`), `api/app.py` (`1043`), `ai/image.py` (`509`), `ui/src/lib/types.ts` (`552`), and `ProjectSettings.tsx` (`449`). Key decision: narrow V1 to design-study variant decisions as the first real preference-signal surface and use a focused preference router/service rather than overloading `SuggestionManager` or generic chat actions. Environment note: `.venv` is absent in this worktree; shared env exists at `/Users/cam/Documents/Projects/cine-forge/.venv`. Next=present the written plan for approval before implementation.
20260320-1111 — implementation + verification: landed schema-first preference learning with new `PreferenceSignal` / `PreferenceProfile` contracts, `PreferenceService`, focused preference-profile API routes, design-study decision capture, deterministic learned-preference prompt enrichment, project-backed enable/clear settings plumbing, and UI inspection controls in Project Settings. Evidence=targeted probe suite `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_preferences.py tests/unit/test_design_study.py tests/unit/test_api.py tests/integration/test_api_design_study.py -q` passed (`53 passed`); full backend suite `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed (`599 passed, 139 deselected, 1 pre-existing acceptance mark warning`); backend lint `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` was clean; UI checks required provisioning `ui/node_modules` via `pnpm --dir ui install --frozen-lockfile`, then `pnpm --dir ui run lint` passed with only 5 pre-existing React fast-refresh warnings in unrelated files, `cd ui && npx tsc -b` passed, and `pnpm --dir ui run build` passed with the existing Vite chunk-size warning. Runtime smoke=started backend with `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m uvicorn cine_forge.api.app:create_app --factory --host 127.0.0.1 --port 8000` and Vite with `pnpm --dir ui run dev --host 127.0.0.1 --port 4173`; `curl http://127.0.0.1:8000/api/health` returned `200 {"status":"ok","version":"2026.03.20-01"}`; seeded disposable project `output/story-131-smoke`; `GET /api/projects/story-131-smoke` and `GET /api/projects/story-131-smoke/preferences/profile` both returned `200` with the expected preference fields and cues. Browser verification on `http://127.0.0.1:4173/story-131-smoke/characters/mariner` confirmed the latest round sources panel shows `Learned Preferences` plus the applied learned-preference lines, Project Settings opens via `⌘,`, the new `Preferences` tab shows active cues/signals and the enable/disable + clear controls, and a live disable/enable toggle round-tripped through `PATCH /api/projects/story-131-smoke/settings` with `200` responses. Browser console had no errors/warnings beyond the standard React DevTools info message. Network log showed only `200` responses for the changed APIs, including `GET /preferences/profile` and `PATCH /settings`. Browser-tool note=Playwright initially failed because of a stale `mcp-chrome` profile process; killing only the orphaned Playwright-scoped Chrome session restored browser automation. Docs=updated this story and `docs/stories.md`; no eval registry change was needed because verification stayed as deterministic unit/integration coverage rather than a tracked promptfoo eval. Next=`/validate`.
20260320-1127 — validation: reviewed local delta, re-read Ideal R13 plus `spec:1.6`, `spec:4.5`, `spec:9`, `docs/build-map.md`, `docs/design/decisions.md`, and ADR-003, then reran the required validation suite against commit base `cd08734`. Evidence=`make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed (`599 passed, 139 deselected, 1 pre-existing pytest.mark.acceptance warning`); `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` passed; targeted probe suite `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_preferences.py tests/unit/test_design_study.py tests/unit/test_api.py tests/integration/test_api_design_study.py -q` passed (`53 passed`); `pnpm --dir ui run lint` passed with only the 5 pre-existing fast-refresh warnings in unrelated files; `cd ui && npx tsc -b` passed; `pnpm --dir ui run build` passed with the existing Vite chunk-size warning. Browser validation=restarted backend + Vite locally, verified `GET /api/projects/story-131-smoke/preferences/profile` and the entity page at `http://127.0.0.1:4173/story-131-smoke/characters/mariner`, confirmed the round-2 Sources panel exposes `Learned Preferences` plus the applied lines, opened Project Settings via `⌘,`, switched to the `Preferences` tab, captured screenshot `tmp/story-131-validate-preferences.png`, and verified live disable/enable toggles with success toasts and `PATCH /api/projects/story-131-smoke/settings => 200`. Console/network review found no app errors and only `200` responses for the touched endpoints. AI/eval note=no promptfoo eval exists for this narrow deterministic preference-learning path yet; validation used the story’s required targeted probe instead, so there were no scored mismatches to classify and no `docs/evals/registry.yaml` update was required. Outcome=no validation findings; story is clean for close-out. Next=`/mark-story-done`.
20260320-1135 — close-out: marked Story 131 done after confirming all workflow gates, tasks, acceptance criteria, validation evidence, doc updates, and tenet checks were complete. Evidence=story status is now `Done`, `docs/stories.md` no longer leaves Story 131 in a pending lane and marks the detailed row `Done`, and `CHANGELOG.md` now records the landed preference-learning slice under the 2026-03-20 release sequence. Next=`/check-in-diff`.

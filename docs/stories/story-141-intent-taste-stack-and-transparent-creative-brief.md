# Story 141 — Intent Taste Stack and Transparent Creative Brief

**Priority**: High
**Status**: Done
**Ideal Refs**: R6 (style and taste), R7 (iterative refinement), R12 (radical transparency), R17 (real-world assets as first-class inputs)
**Spec Refs**: spec:4.10.1 (Intent / Mood Layer), spec:4.10.2 (Look & Feel), spec:7.1 (Render Adapter Layer), spec:7.2 (User Asset Injection)
**ADR Refs**: ADR-003 (Film Elements / Intent-first creative surface), design context: `docs/design/decisions.md` (provenance visible on demand, story-centric navigation)
**Depends On**: Story 029 (User Asset Injection), Story 095 (Intent / Mood Layer), Story 119 (Design Study Prompt Compiler + Visual Reference Propagation), Story 120 (Production Format Setting)

## Goal

Turn Intent from a thin mood form into the real project-level taste stack. `production_format` should remain the base medium, but users also need explicit director / filmmaker anchors, film references, freeform look notes, and transparent use of uploaded mood-board assets from the existing project reference library. This story adds those richer upstream inputs and compiles them into a read-only creative brief, or equivalent transparent preview, that downstream image and video prompt builders can inspect and use. The user edits taste in Intent, sees what shaped the brief, and never has to chase hidden prompt logic or bounce back to Script for project-level visual direction.

## Acceptance Criteria

- [x] Intent round-trips a richer project-level taste contract: existing mood descriptors, reference films, presets, natural-language intent, and `production_format` remain intact, while new director / filmmaker anchors and freeform look notes (or an equivalently explicit typed taste surface) persist through backend and UI without regressions.
- [x] Intent clearly shows which active project references are contributing to the visual taste stack, especially `mood_board` and `style_reference` assets from the existing project reference library, and that participation is visible on the Intent surface rather than hidden in prompt code.
- [x] The system exposes a transparent, read-only compiled creative brief or equivalent preview that combines the active taste inputs: visual medium, mood descriptors, film/director anchors, look notes, and contributing project references. Operators can inspect both the compiled output and the upstream inputs that shaped it.
- [x] Design-study generation consumes that compiled brief or equivalent compiled context, and the existing sources panel continues to show honest provenance without regressing current source types such as `entity_bible`, composition refs, seed images, and learned preferences.
- [x] Render-adapter / video prompt compilation consumes the same compiled brief or equivalent upstream taste context, so image and video lanes stop diverging on project-level taste inputs.
- [x] Script remains breadcrumb-only for project-level visual taste. No new project-level editor is added to Script or hidden in generic settings.
- [x] Focused tests and a targeted prompt-quality probe cover the new brief path. If no registry-backed eval is appropriate, the story documents and runs a smaller deterministic + AI-judged probe instead of pretending structural tests alone are sufficient.

## Out of Scope

- Replacing Story 034 or building an in-app style-pack authoring flow
- Per-scene or per-entity versions of the richer taste stack; this story is project-level only and leaves existing scene overrides intact
- Full adoption by every visual consumer in one pass; primary downstream consumers are design-study image generation and render-adapter/video prompt compilation
- Raw prompt editing UI
- Auto-detecting the whole taste stack from the screenplay without user input

## Approach Evaluation

- **Simplification baseline**: First measure whether one Director / Visual Architect LLM call using the current Intent inputs plus active project references already produces a usable compiled brief for downstream prompt builders. That baseline is currently untested. Today the repo only appends raw `reference_films`, `natural_language_intent`, `look_and_feel`, and `project_config` fields inside prompt builders, and uploaded project references do not compile into one transparent brief.
- **AI-only**: Compile the brief on demand from Intent inputs and project references every time image or video generation runs. Pros: strongest chance of semantic interpretation for mood-board imagery. Cons: added latency and cost on every generation, plus hidden behavior unless the compiled output is surfaced or persisted.
- **Hybrid**: Store richer upstream taste inputs in typed schemas and UI, then compile a read-only brief or preview via AI when Intent changes or when generation starts. Downstream prompt builders consume that brief deterministically. This is the most likely fit because it keeps semantic interpretation where needed but preserves transparency and reuse.
- **Pure code**: Append more raw text fields and filenames directly into design-study and render-adapter prompts. Good for plumbing and provenance wiring, weak for mood-board semantics and likely too thin for the actual product gap.
- **Repo constraints / ADRs**: ADR-003 says Intent / Mood is the primary creative surface and prompts are read-only compiled artifacts. Story 120 explicitly deferred this exact follow-on. Story 119, Story 121, and Story 131 already define the prompt-compiler, composition-provenance, and preference-learning seams this story should extend instead of bypassing. Large-file pressure is real: `ui/src/pages/IntentMoodPage.tsx` is `660` lines, `src/cine_forge/ai/image.py` is `542`, `src/cine_forge/api/routers/design_study.py` is `503`, and `src/cine_forge/modules/generation/render_adapter_v1/main.py` is `1318`.
- **Existing patterns to reuse**: `IntentMood` schema and propagation service, `ProjectReferencesSection` / `ReferenceLibrarySection`, `build_image_prompt()`, `DesignStudySourcesPanel`, render-adapter prompt blocks, and the existing project reference purposes (`style_reference`, `mood_board`) already living on the Intent page.
- **Eval**: No existing registry entry directly measures Intent-side compiled taste briefs. Implementation should add deterministic schema / provenance tests plus a focused prompt-quality probe on one fixed project that compares current vs compiled-brief prompt outputs for both design-study and render-adapter consumers. Because this changes AI behavior, the probe should include an explicit judgment pass rather than only structural assertions.

## Tasks

- [x] Define the typed contract for richer Intent taste inputs before wiring UI or prompt changes. This likely means extending `IntentMood` with separate director / filmmaker anchors and freeform look notes, plus a typed compiled-brief schema or preview contract if the compiled brief crosses a layer boundary.
- [x] Measure the simplification baseline with a single compiled-brief probe using current Intent data plus active project references, and record whether an AI-only compile step is already sufficient.
- [x] Extract Intent API handling into a focused router / service seam and expose the read-only compiled-brief preview there instead of growing `src/cine_forge/api/app.py`.
- [x] Extend the Intent API / UI to edit the richer taste inputs and show which project references are actively feeding the visual brief. Extract focused child components instead of deepening the existing `IntentMoodPage.tsx`.
- [x] Implement the read-only compiled creative brief surface with provenance on Intent, grounded in the current taste stack and active project references.
- [x] Thread the compiled brief or equivalent compiled context into design-study prompt compilation and sources-panel provenance.
- [x] Snapshot the compiled brief preview anywhere downstream generation uses it so operators can inspect the exact compiled output, not only the upstream source badges.
- [x] Thread the same compiled brief or equivalent compiled context into render-adapter / video prompt compilation, extracting helpers instead of adding more inline prompt assembly to the existing oversized module.
- [x] Add focused regression coverage for schema/API round-tripping and prompt provenance, plus the targeted prompt-quality probe or documented evaluation path.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  - [x] Backend lint: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui install --frozen-lockfile`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If agent tooling or project instructions are touched: not applicable; no agent tooling or project instructions changed.
- [x] If evals or goldens are changed: not applicable; no registry-backed evals or goldens changed, and the story instead added a scoped probe at `docs/reports/story-141-creative-brief-probe-20260331.json`.
- [x] If UI is touched: verify the changed flow with browser tools when possible (screenshot + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
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

## Architectural Fit

- **Owning class/module**: Project-level taste inputs still belong to the Intent stack (`IntentMood` schema + Intent API/UI). The compiled brief should live in a new focused schema/service helper such as `creative_brief.py`, not as more ad hoc string concatenation inside `IntentMoodPage.tsx`, `build_image_prompt()`, or `render_adapter_v1/main.py`.
- **Data contracts**: Extend `IntentMood` or an adjacent typed contract for richer taste inputs. If the compiled brief crosses API or artifact boundaries, define a schema-first `VisualCreativeBrief` or equivalent preview contract before wiring consumers. Project-reference participation must stay typed and traceable rather than becoming hidden prompt text.
- **File sizes**: `make check-size` currently flags `src/cine_forge/modules/generation/render_adapter_v1/main.py` (`1318`), `src/cine_forge/api/app.py` (`1047`), `ui/src/pages/IntentMoodPage.tsx` (`660`), `ui/src/lib/types.ts` (`600`), `src/cine_forge/ai/image.py` (`542`), `src/cine_forge/api/routers/design_study.py` (`503`), `src/cine_forge/api/models.py` (`483`), and `src/cine_forge/schemas/concern_groups.py` (`466`). Any implementation plan that touches those files must extract rather than pile on.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/spec.md`, `docs/build-map.md`, ADR-003, `docs/design/decisions.md`, Story 095, Story 119, Story 120, and the current Intent / design-study / render-adapter seams. No newer ADR supersedes this area.

## Files to Modify

- `src/cine_forge/schemas/concern_groups.py` — extend `IntentMood` for richer taste inputs (`466`)
- `src/cine_forge/schemas/creative_brief.py` — new schema-first contract for the compiled visual taste brief
- `src/cine_forge/schemas/__init__.py` — export the compiled-brief schema for shared use
- `src/cine_forge/services/creative_brief.py` — shared deterministic compiler for preview + downstream consumers
- `src/cine_forge/services/intent_mood.py` — reuse or factor prompt-building logic for richer Intent compilation (`216`)
- `src/cine_forge/api/models.py` — typed request / response models for richer Intent inputs and compiled-brief preview (`483`)
- `src/cine_forge/api/routers/intent_mood.py` — extracted Intent router with get/save/suggest/propagate/preview handling
- `src/cine_forge/api/app.py` — thin router registration only; prefer extraction over growing the file (`1047`)
- `ui/src/lib/api/intent-mood.ts` — frontend types and API calls for richer Intent inputs / compiled brief (`105`)
- `ui/src/pages/IntentMoodPage.tsx` — host the richer taste stack via extracted child components, not more inline state (`660`)
- `ui/src/components/ProjectReferencesSection.tsx` — show project-reference participation in the taste stack (`19`)
- `ui/src/components/assets/ReferenceLibrarySection.tsx` — reuse existing reference-library seams for active mood-board participation rather than inventing a second uploader (`135`)
- `src/cine_forge/ai/image.py` — design-study consumer for the compiled brief or equivalent compiled context (`542`)
- `src/cine_forge/schemas/design_study.py` — snapshot the compiled brief preview used by each round
- `ui/src/components/DesignStudySourcesPanel.tsx` — provenance UI for the new brief input (`133`)
- `src/cine_forge/modules/generation/render_adapter_v1/main.py` — video prompt consumer, likely via extracted helper instead of more inline prompt assembly (`1318`)
- `src/cine_forge/modules/generation/render_adapter_v1/prompting.py` — add compiled-brief prompt section metadata without duplicating source tracking
- `tests/unit/test_creative_brief.py` — deterministic coverage for the shared compiler
- `tests/unit/test_design_study.py` — prompt / provenance coverage for the image lane
- `tests/unit/test_intent_mood.py` — richer Intent schema + API contract coverage
- `tests/integration/test_api_design_study.py` — end-to-end coverage for richer Intent inputs feeding design-study generation

## Redundancy / Removal Targets

- Ad hoc reliance on `reference_films` and `natural_language_intent` as the only project-level taste inputs in downstream prompt builders
- Any project-reference participation that only exists implicitly in filenames or lock state with no visible compiled-brief surface
- Any temptation to reintroduce project-level visual taste editing on Script instead of Intent
- Duplicate prompt-assembly fragments between design-study and render-adapter if a shared compiled-brief helper supersedes them

## Notes

- If we do not do this, Intent remains a partial implementation of ADR-003 and downstream image/video generation keeps relying on thin, divergent taste inputs.
- `ProjectReferencesSection` already gives the repo a real Intent-side home for uploaded `mood_board` and `style_reference` assets. This story should reuse that surface instead of inventing a second uploader or a second asset stack.
- Story 034 is related but not a dependency. This story is about using taste inputs transparently, not authoring reusable style-pack products.
- Because this changes AI behavior, deterministic tests alone are not enough. Per AGENTS.md, implementation should include an explicit judgment/probe step for the compiled brief quality.

## Plan

### Eval-first baseline

- **Probe target**: one fixed project-level taste sample compiled into a transparent brief, then reused by both downstream lanes. Success metric for the baseline probe is simple coverage of the required current inputs: visual medium, mood summary, reference anchors, project-reference participation, and operator-preview text.
- **Live model discovery**: `scripts/discover-models.py --summary` on 2026-04-01 UTC found current provider catalogs and confirmed `gpt-5.4`, `claude-sonnet-4-6`, and `claude-opus-4-6` are live options. This keeps the probe grounded in current availability instead of training-cutoff guesses.
- **AI-only capability baseline**: a single `gpt-5.4` call using current-style Intent inputs plus project-reference metadata produced a valid read-only brief with `5/5` required fields covered, `4.25s` latency, and estimated cost `~$0.0040`. Result: AI-only brief compilation is capable right now for text-visible inputs.
- **Current-code baseline**: the repo still has no shared creative-brief seam. Design-study prompt assembly reads `project_config` / `look_and_feel` / `intent_mood` directly and ignores project reference-library participation. Render-adapter reads `look_and_feel`, `intent_mood.natural_language_intent`, and generic injected assets, but it does not compile one reusable project-level taste brief and it does not preserve film/director/look-note taste inputs because those inputs do not exist yet.
- **Approach decision**:
  - **AI-only runtime compile**: rejected for this repo as the primary implementation. The probe proves capability, but current project references only expose filename / purpose / lock metadata. Without captioned or multimodal reference understanding, a runtime LLM compiler mostly paraphrases metadata while adding per-run latency and cost.
  - **Pure code / schema-first shared brief**: chosen. Store the richer taste surface in typed schemas, deterministically compile a transparent `VisualCreativeBrief`, and let both consumers reuse that same contract. This solves the actual product gap in this repo: typed upstream taste, visible reference participation, shared downstream context, and no hidden per-run AI branch.
  - **Hybrid follow-on**: keep the compiler contract open to richer AI-assisted reference interpretation later if project references gain captions or vision summaries. Do not build that speculative path into Story 141.
- **Implementation-time evaluation**: add deterministic compiler tests plus a small current-vs-new prompt-quality probe on one fixed fixture project. The probe should compare design-study and render-adapter outputs before/after the brief seam, then ask a strong judge model to classify whether the new prompts better preserve project-level taste and transparency. This is a local story probe, not a new registry-backed promptfoo eval.

### Repo-fit / optimality evidence

- **Ideal / ADR fit**: `docs/ideal.md` and ADR-003 make Intent the primary creative surface and compiled artifacts read-only. A typed taste stack plus transparent brief moves toward R6, R7, R12, and R17 without relocating project taste back into Script or hidden prompt code.
- **Story dependency fit**: Story 120 intentionally narrowed `production_format` to the base visual medium and deferred this richer taste stack. Story 119 created the design-study prompt-compiler seam. Story 141 should extend those seams rather than creating a second prompt path.
- **Current code constraints**:
  - project references already live on Intent through `ProjectReferencesSection`, so the right product home exists now
  - `src/cine_forge/services/injected_assets.py` and the asset-manifest APIs already expose project references cleanly enough to show participation by purpose/lock state
  - render-adapter already loads project/scene injected manifests, but only as generic resolved inputs; it still lacks a shared project-taste brief
  - design-study still does not consume project reference-library participation at all
- **Why the deterministic brief is better here**: current project references are metadata-only. A deterministic compiler can transparently combine `production_format`, Intent taste fields, and active `mood_board` / `style_reference` assets without paying runtime LLM cost for information the repo does not yet expose semantically.
- **Alternatives rejected**:
  - adding more raw string concatenation directly into `build_image_prompt()` and `render_adapter_v1/main.py` would deepen drift and keep image/video lanes divergent
  - persisting a new creative-brief artifact version on every Intent edit is premature for this slice; a shared typed compiler + read-only preview satisfies the story while keeping artifact churn down

### Structural health check

- `src/cine_forge/api/app.py` — `1047` lines. Do not add new Intent route logic inline; extract a dedicated router and keep `app.py` to `include_router(...)`.
- `ui/src/pages/IntentMoodPage.tsx` — `660` lines. Do not deepen this page; first implementation task on the UI side is extracting focused child components for the richer taste form and brief preview.
- `src/cine_forge/modules/generation/render_adapter_v1/main.py` — `1318` lines. Do not add more inline prompt assembly; add a helper seam and keep `main.py` to orchestration.
- `src/cine_forge/ai/image.py` — `542` lines. Do not keep growing raw context concatenation helpers; move compiled-brief formatting into a focused helper or shared service.
- `src/cine_forge/api/routers/design_study.py` — `503` lines. Keep router edits thin; move brief-loading logic into a shared service/helper.
- `src/cine_forge/api/models.py` — `483` lines and `src/cine_forge/schemas/concern_groups.py` — `466` lines. Both are still below the hard threshold, but schema additions should stay tight and schema-first.
- **Inter-layer contract rule**: the compiled brief crosses service↔API↔UI and service↔module boundaries, so create a schema-first contract before any consumer wiring.
- **Event rule**: no new event type is needed.

### Scope adjustments folded into this story

- **Small expansion (`S`)**: extract Intent endpoints into a new `src/cine_forge/api/routers/intent_mood.py` router instead of adding more logic to `src/cine_forge/api/app.py`. This is necessary adjacent work because Story 141 otherwise violates the file-size tenet while adding a new read-only preview endpoint.
- **Small expansion (`S`)**: snapshot the compiled brief preview on downstream outputs that use it. For design-study that means storing the exact brief preview used on each round, so the UI can show the compiled output and the source badges honestly rather than only showing upstream source tags.

### Task plan

1. **Schema-first richer Intent contract + shared brief contract**
   - Files: `src/cine_forge/schemas/concern_groups.py`, new `src/cine_forge/schemas/creative_brief.py`, `src/cine_forge/schemas/__init__.py`, `src/cine_forge/api/models.py`, `ui/src/lib/api/intent-mood.ts`
   - Change:
     - extend `IntentMood` with explicit filmmaker/director anchors and freeform look notes while keeping existing fields intact
     - define a typed `VisualCreativeBrief` contract plus typed project-reference participation entries
     - add API response models for the read-only brief preview
   - Impact / risk:
     - `tests/unit/test_intent_mood.py`, `tests/unit/test_concern_group_schemas.py`, and any consumer reading `IntentMood` need updates
     - keep scene-level override compatibility by making the new fields optional
   - Done looks like:
     - richer taste inputs round-trip through schema and API types
     - compiled-brief preview has a single typed contract used by UI and both downstream consumers

2. **Shared brief compiler + Intent API extraction**
   - Files: new `src/cine_forge/services/creative_brief.py`, `src/cine_forge/services/intent_mood.py`, new `src/cine_forge/api/routers/intent_mood.py`, `src/cine_forge/api/app.py`
   - Change:
     - create a deterministic brief compiler that accepts `project_config`, `IntentMood`, and project-level injected asset manifests
     - preserve transparent source participation: only `mood_board` and `style_reference` project assets become taste-stack entries, with purpose/lock/filename surfaced honestly
     - move existing Intent routes out of `app.py`, keep suggest/propagate behavior, and add a read-only project-level brief-preview endpoint
   - Impact / risk:
     - route extraction must not break existing `GET/POST /intent-mood`, `/suggest`, or `/propagate`
     - project reference filtering must not silently include unrelated purposes such as `temp_score`
   - Done looks like:
     - `app.py` only registers the router
     - the new preview endpoint returns the compiled brief plus upstream inputs/reference participation

3. **Intent UI extraction and preview surface**
   - Files: `ui/src/pages/IntentMoodPage.tsx`, new focused components under `ui/src/components/intent/` for the richer taste form and compiled-brief preview, `ui/src/components/ProjectReferencesSection.tsx`
   - Change:
     - extract page sections so `IntentMoodPage.tsx` stops being the only place where form state and rendering live
     - add explicit filmmaker/director anchors and look-notes editing
     - render a read-only creative-brief preview showing the compiled output plus the active `mood_board` / `style_reference` references contributing to it
   - Impact / risk:
     - the current save flow and warm-invitation / gate behavior must remain intact
     - scene `DirectionTab` queries `getIntentMood()` and must keep working after the response type expansion
   - Done looks like:
     - the Intent page exposes the richer taste inputs without adding more inline page complexity
     - operators can see which project references are contributing to the taste stack before generating anything downstream

4. **Design-study consumer migration to the shared brief**
   - Files: `src/cine_forge/ai/image.py`, `src/cine_forge/api/routers/design_study.py`, `src/cine_forge/schemas/design_study.py`, `ui/src/lib/api/design-study.ts`, `ui/src/components/DesignStudySourcesPanel.tsx`
   - Change:
     - stop passing raw project taste fields separately into `build_image_prompt()`; pass the shared compiled brief instead
     - snapshot the brief preview used for each round so the sources panel can show both the compiled output and the individual upstream source badges
     - keep existing provenance for `entity_bible`, directive, composition refs, learned preferences, and seed image
   - Impact / risk:
     - `src/cine_forge/api/routers/design_study.py` is already oversized, so only thin router edits are acceptable
     - regression risk is mostly around `DesignStudyRound` shape and UI rendering
   - Done looks like:
     - new rounds store and display the exact creative-brief preview used
     - prompt/source provenance remains honest and no existing source type disappears

5. **Render-adapter consumer migration to the shared brief**
   - Files: new helper under `src/cine_forge/modules/generation/render_adapter_v1/`, `src/cine_forge/modules/generation/render_adapter_v1/main.py`, `src/cine_forge/modules/generation/render_adapter_v1/prompting.py`, `tests/unit/test_render_adapter_module.py`, `tests/integration/test_render_adapter_integration.py`
   - Change:
     - compile the same `VisualCreativeBrief` from project-level taste inputs and project reference participation
     - add a dedicated creative-brief context block / prompt section instead of sprinkling more `intent_mood` string assembly inline
     - keep generic injected-asset handling for actual render inputs; the brief is additive project-level taste context, not a replacement for resolved media inputs
   - Impact / risk:
     - `render_adapter_v1/main.py` cannot absorb new inline logic safely; helper extraction is mandatory
     - prompt sources and completeness logic must stay stable
   - Done looks like:
     - render compilation sees the same project-level taste brief as design-study
     - image/video lanes stop diverging on project-level taste inputs

6. **Regression coverage + targeted prompt-quality probe**
   - Files: new `tests/unit/test_creative_brief.py`, `tests/unit/test_intent_mood.py`, `tests/unit/test_design_study.py`, `tests/integration/test_api_design_study.py`, `tests/unit/test_render_adapter_module.py`, optional new `tests/integration/test_api_intent_mood.py`, plus a small story-scoped probe script under `scripts/`
   - Change:
     - deterministic tests for round-trip, compiler output, project-reference filtering, and downstream snapshots
     - targeted prompt-quality probe comparing current vs new prompts on one fixed fixture for both design-study and render-adapter, then AI-judge the difference
   - Impact / risk:
     - if the probe shows better transparency but worse creative usefulness, the implementation needs correction before handoff
   - Done looks like:
     - deterministic tests pass
     - the prompt-quality probe is recorded in the work log with explicit result and judged disposition

### Redundancy / cleanup plan

- Remove or collapse raw project-taste prompt assembly paths once the compiled brief becomes the shared seam.
- Do not keep both the old raw `project_config` / `intent_mood` argument path and the new compiled-brief path in `build_image_prompt()`.
- Do not leave new preview logic embedded inside `IntentMoodPage.tsx`; keep the page thin once the extracted components land.
- Avoid duplicating project-reference filtering rules in multiple places; the compiled-brief service should own which purposes count as taste-stack inputs.

### UI verification plan

- Preferred browser path:
  - open `/:projectId/intent`
  - add filmmaker anchors and look notes
  - confirm project `mood_board` / `style_reference` assets appear in the brief participation surface
  - save and confirm the read-only brief preview updates
  - open an entity detail design-study screen and generate a round
  - confirm the sources panel shows the brief preview and the honest upstream source badges
- Render verification path:
  - run the render fixture flow or driver recipe with the seeded project
  - inspect the compiled render prompt artifact and confirm it contains the creative-brief section
- Browser tooling:
  - screenshot the Intent brief preview
  - screenshot the design-study sources panel after generation
  - capture console output and network success for the new preview endpoint
- Fallback:
  - if browser tools fail, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker plus manual route/API verification in the work log

### Human blockers

- No architectural blocker beyond approval to proceed with the two folded scope expansions above.
- Public API surface will grow by one read-only brief-preview endpoint and richer `IntentMood` fields. In this greenfield repo that is low risk and expected.

## Work Log

20260331-2157 — triage-inbox: processed the sole inbox item into Story 141 after `/triage` identified it as the highest-leverage live gap. Existing homes checked: Story 095 lands the base Intent surface, Story 119 lands design-study prompt compilation, and Story 120 intentionally deferred this richer taste-stack follow-on. Evidence reviewed: `docs/inbox.md`, `docs/ideal.md`, `docs/spec.md`, `docs/build-map.md`, ADR-003, Story 095, Story 119, Story 120, `ui/src/pages/IntentMoodPage.tsx`, `ui/src/components/ProjectReferencesSection.tsx`, `src/cine_forge/ai/image.py`, and `src/cine_forge/modules/generation/render_adapter_v1/main.py`. Next step: `/build-story` when ready.
20260331-2248 — exploration + planning: confirmed Story 141 still closes a live Ideal / spec gap and is not a shrinking-limit optimization; `docs/retrofit-gaps.md` is archived and defers to the current methodology docs. Reviewed ADR-003, `docs/design/decisions.md`, Stories 095/119/120, `src/cine_forge/{schemas/concern_groups.py,services/intent_mood.py,ai/image.py,api/app.py,api/models.py,api/routers/design_study.py,modules/generation/render_adapter_v1/{main.py,prompting.py},services/injected_assets.py}`, `ui/src/{pages/IntentMoodPage.tsx,components/ProjectReferencesSection.tsx,components/assets/ReferenceLibrarySection.tsx,components/DesignStudySourcesPanel.tsx,lib/api/{intent-mood.ts,design-study.ts}}`, and the existing design-study / render / intent tests. Structural findings: `api/app.py` (`1047`), `IntentMoodPage.tsx` (`660`), `render_adapter_v1/main.py` (`1318`), `ai/image.py` (`542`), and `api/routers/design_study.py` (`503`) cannot safely absorb more inline logic. Probe result: live model discovery succeeded, then a single `gpt-5.4` compiled-brief probe on current-style inputs achieved `5/5` coverage in `4.25s` at `~$0.004`, proving AI-only capability but also showing the repo still lacks semantic project-reference inputs beyond filename/purpose metadata. Chosen plan: schema-first deterministic shared brief, with AI reserved for the targeted prompt-quality probe instead of becoming a runtime dependency. Next step: human approval on the plan, including the small scoped expansions to extract an Intent router and snapshot the downstream brief preview.
20260331-2258 — implementation start: user approved the Story 141 plan by reinvoking `/build-story`. Story status moved to `In Progress`. First implementation slice is backend contract work: add the shared creative-brief schema/service, extract Intent routes out of `api/app.py`, and thread the preview seam into design-study and render consumers before touching the UI. Next step: land schema/service/router changes and update focused backend tests.
20260331-2306 — backend + consumer implementation: added `VisualCreativeBrief` / `CreativeBriefProjectReference`, extended `IntentMood` with `filmmaker_anchors` and `look_notes`, added the shared compiler in `src/cine_forge/services/creative_brief.py`, extracted the Intent router into `src/cine_forge/api/routers/intent_mood.py`, and removed the old inline Intent route block from `src/cine_forge/api/app.py`. Downstream consumers now read the shared brief instead of raw project taste fields: design-study stores `creative_brief_preview` on each round and render-adapter stores `creative_brief_preview` on each compiled render prompt while adding a dedicated `creative_brief` prompt section. Evidence: targeted Ruff passed after fixing one real syntax error in `render_adapter_v1/main.py`; targeted pytest for the new seam passed after replacing invalid fake JPEG bytes in integration fixtures with real generated JPEGs. Next step: finish the UI extraction, add the story-scoped probe, then run the full repo checks.
20260331-2315 — UI + probe implementation: extracted `ui/src/components/intent/{IntentTasteStackFields.tsx,CreativeBriefPreviewCard.tsx}` so `IntentMoodPage.tsx` stops carrying all richer taste UI inline, added the new creative-brief preview query and cache invalidation path, and updated `DesignStudySourcesPanel.tsx` to render the stored compiled brief plus active project references. Added deterministic compiler / API coverage in `tests/unit/test_creative_brief.py`, `tests/integration/test_api_intent_mood.py`, and the updated design-study/render tests. Added `scripts/story_141_creative_brief_probe.py` plus `scripts/README.md` note, then ran the probe and saved the artifact to `docs/reports/story-141-creative-brief-probe-20260331.json`. Probe evidence: deterministic checks show the new design-study prompt now carries filmmaker anchor, look notes, project-reference filename, and transparency cues that the legacy prompt missed; the new render-adapter compiler prompt carries all required taste signals while the legacy path missed visual medium, film/director anchors, and transparency cues. AI-judge evidence: `claude-opus-4-6` picked `new` for both lanes (`~28.86s`, `~$0.1566`) and called out only one minor tradeoff: the legacy image prompt surfaced genre/tone as separate lines, while the new path leans on mood descriptors and look notes instead.
20260331-2324 — full checks: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed (`630 passed, 141 deselected`), and `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` passed. UI checks were initially blocked because this worktree lacked `ui/node_modules`; installed deps with `pnpm --dir ui install --frozen-lockfile`, then `pnpm --dir ui run lint` passed with five pre-existing `react-refresh/only-export-components` warnings in unrelated shared UI files, `cd ui && npx tsc -b` passed, and `pnpm --dir ui run build` passed. Build output warning: Vite still reports large chunks (`dist/assets/index-a3ijKPVL.js` > 500 kB), but that warning predates this story and did not block the build. Next step: runtime smoke through the actual app and browser.
20260331-2331 — runtime smoke: restarted a stale backend listener on `127.0.0.1:8000`, confirmed `GET /api/health` returned `{"status":"ok","version":"2026.03.31-03"}`, then launched Vite on `http://127.0.0.1:5174`. Seeded a disposable project at `/tmp/cineforge-story141-smoke-QQjWDc` via the live API and local artifacts so the browser could exercise the real changed surfaces. API evidence before browser: `GET /api/projects/cineforge-story141-smoke-QQjWDc/intent-mood` returned the richer `filmmaker_anchors` / `look_notes` fields; `GET /api/projects/cineforge-story141-smoke-QQjWDc/intent-mood/creative-brief` returned the compiled brief with `project_references`; `GET /api/projects/cineforge-story141-smoke-QQjWDc/design-study/character_mariner` returned a round containing `creative_brief_preview`. Browser evidence: on `/:projectId/intent`, the page rendered the richer taste fields plus the compiled brief preview and active project references with no console errors; screenshot saved to `story-141-intent-page.png`. On `/:projectId/characters/mariner`, after seeding a minimal character bible manifest to satisfy the reference-library request, the console was clean and the Design Study sources panel rendered `Compiled creative brief` with the stored operator preview, summary lines, and active project references; screenshots saved to `story-141-design-study-sources.png` and `story-141-design-study-brief-panel.png`. Residual risk to validate next: the new image-prompt path no longer spells out genre/tone as separate lines, so `/validate` should decide whether mood descriptors + look notes are enough or whether genre/tone deserves explicit carry-through in the compiled brief.
20260401-0741 — validation: reran the full required check suite in this pass. `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed (`630 passed, 141 deselected`), `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` passed, the story-targeted pytest slice covering the creative-brief / intent / design-study / render seams passed, `pnpm --dir ui run lint` passed with the same five pre-existing `react-refresh/only-export-components` warnings in unrelated shared UI files, `cd ui && npx tsc -b` passed, and `pnpm --dir ui run build` passed with the same pre-existing chunk-size warning. Browser verification was rerun against a fresh disposable project at `/var/folders/8f/3nlcf3sj1s5bbk1g_3dt3djm0000gn/T/story141-validate-i6qzu0xv/story141-validate-ui`: `/:projectId/intent` rendered `Compiled Creative Brief` with `Robert Eggers` and active project references, `/:projectId/characters/mara` rendered the Design Study `Sources used` panel plus `Compiled creative brief`, and Playwright console output stayed free of warnings/errors on both routes. Fresh AI-probe evidence: `PYTHONPATH=src:. /Users/cam/Documents/Projects/cine-forge/.venv/bin/python scripts/story_141_creative_brief_probe.py --judge-model claude-opus-4-6` again preferred `new` for both design-study and render-adapter (`~22.63s`, `~$0.1479`) while repeating one non-runtime-blocking tradeoff: the legacy image prompt surfaced genre/tone as separate lines. Validation finding to carry into close-out: `src/cine_forge/ai/image.py` still keeps dead `_project_config_context()` / `_intent_mood_context()` helpers after the shared-brief refactor. Recommended next step: `/mark-story-done`; if we want to tighten the implementation first, the only meaningful follow-up is deciding whether genre/tone belongs explicitly in the shared brief and removing the now-unused helper functions.
20260401-0908 — close-out cleanup + completion: moved the story-scoped legacy prompt formatting into `scripts/story_141_creative_brief_probe.py`, removed the now-obsolete raw prompt helper path from `src/cine_forge/ai/image.py`, and reran the minimum close-out validation for that patch: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/ scripts/story_141_creative_brief_probe.py` passed, `PYTHONPATH=src:. /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_design_study.py tests/integration/test_api_design_study.py -q` passed, and the deterministic story probe still showed the new design-study/render prompt path preserving all required signals while improving transparency. Story 141 is now complete and marked done. Next step: `/check-in-diff`.

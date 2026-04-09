---
id: "034"
title: "In-App Style Pack Creator"
status: "Done"
priority: "Unknown"
ideal_refs: []
spec_refs:
  - "spec:4.3"
  - "spec:4.4"
adr_refs:
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "011b"
  - "016"
category_refs:
  - "spec:4"
compromise_refs: []
input_coverage_refs: []
architecture_domains: []
roadmap_tags: []
legacy_system: ""
---

# Story 034: In-App Style Pack Creator

**Status**: Done
**Created**: 2026-02-13
**Spec Refs**: spec:4.4 (Style Pack Creation), spec:4.3 (Style Packs)
**Depends On**: Story 016 (style pack infrastructure — templates and format), Story 011b (Operator Console — UI for creation flow)

---

## Goal

Implement **in-app style pack creation** using deep research APIs. The user selects a role type, provides freeform input (a name, a combination, a reference work, or an original description), and the system uses a deep research API to produce a properly structured style pack.

This is the automated version of the manual workflow established in Story 016.

---

## Acceptance Criteria

### Creation Flow
- [x] User selects a role type from the live style-pack-enabled role catalog rather than a hard-coded stale list. Current repo truth: Director, Visual Architect, Sound Designer, Editorial Architect, and Story Editor are the creative roles that currently accept style packs.
- [x] User provides freeform input:
  - [x] A single name (e.g., "Tarantino").
  - [x] A combination (e.g., "Tarantino's dialogue + Kubrick's framing").
  - [x] A reference work (e.g., "Blade Runner 2049").
  - [x] An original description (e.g., "moody noir with jazz undertones").
- [x] System loads the role-specific creation prompt template (from Story 016).
- [x] Template + user input sent to deep research API.
- [x] Research runs asynchronously with progress updates.
- [x] Result auto-formatted into a properly structured style pack folder.

### Deep Research API Integration
- [x] Support for deep research APIs:
  - [x] OpenAI path via `deep-research` CLI provider selection.
  - [x] Google Gemini path via `deep-research` CLI provider selection.
  - [x] Anthropic path via `deep-research` CLI provider selection.
  - [x] Fallback: manual flow (user pastes output from external tool).
- [x] API selection configurable.
- [x] Progress reporting during research (may take minutes).
- [x] Cost tracking for research API calls.
- [x] Alternative: integration with `deep-research` CLI tool for multi-model research.

### Output Validation
- [x] Generated style pack validated against schema (Story 016).
- [x] Pack includes all required components:
  - [x] `style.md` with rich creative description.
  - [x] `manifest.yaml` with proper metadata.
  - [x] Optional reference materials (if the research produced/referenced them).
- [x] User can review and edit the generated pack before activating it.

### UI Integration
- [x] Style pack creation accessible from Operator Console.
- [x] Progress indicator during async research.
- [x] Preview of generated pack with ability to edit before saving.
- [x] Library of created packs browsable and selectable per-role.

### Testing
- [x] Unit tests for creation prompt template rendering.
- [x] Unit tests for style pack output formatting and validation.
- [x] Unit tests for deep research API integration (mocked).
- [x] Integration test: user input → research → style pack → validation → storage.
- [x] Schema validation on all outputs.

---

## Design Notes

### Deep Research for Style
Style packs benefit enormously from deep research because creative influences are nuanced and multi-faceted. A "Tarantino" style pack for a Director needs to cover narrative structure, dialogue philosophy, tonal range, genre mixing, and thematic obsessions — all extracted from analysis of the filmmaker's body of work. A single AI call won't capture this depth; deep research with multiple models can.

### Manual Fallback
Not everyone will have deep research API keys configured. The creation prompt templates (from Story 016) should be usable standalone — the user can paste them into ChatGPT, Gemini, or any capable model and manually save the output as a style pack. The in-app creation flow is a convenience, not a requirement.

### CineForge's Deep Research Tool
The project has a custom `deep-research` CLI tool ([deep-research-manager](https://github.com/copperdogma/deep-research-manager)) that can orchestrate multi-model research. Consider integrating with this tool as an alternative to direct API calls — it supports multiple providers and produces formatted research outputs.

### Current Repo Truth
- The story's original "Actor Agent" role example is stale. The current runtime role list is defined by `src/cine_forge/roles/*/role.yaml`, and the style-pack-enabled roles are `assistant`, `director`, `editorial_architect`, `sound_designer`, `story_editor`, and `visual_architect`.
- Built-in style packs live under `src/cine_forge/roles/style_packs/...`, but project settings already persist `style_packs` selections in `project.json`.
- The missing substrate is not style-pack format or prompt templates. It is project-local pack creation, project-local pack discovery, preview/edit/save, and an honest Operator Console surface for assigning those packs.

## Approach Evaluation

- **Simplification baseline**: keep the current manual workflow from Story 016 and do nothing in-app. This preserves correctness but leaves taste authoring outside the product, which is the central Ideal gap this story is supposed to close.
- **AI-only**: call a general-purpose chat model directly from the UI/backend and trust its raw output as the style pack. Rejected for this repo because it bypasses the existing role-specific creation prompts, bypasses the sanctioned `deep-research` substrate, and makes provider behavior harder to reason about or swap.
- **Hybrid**: use the existing `deep-research` CLI for the research/generation step, then deterministically parse, validate, preview, edit, save, and assign the resulting pack. This is the chosen direction because the creative content still comes from AI while the app owns structure, validation, persistence, and UX honesty.
- **Pure code**: impossible for the actual style-authoring problem. Code can validate and persist a style pack, but it cannot infer Tarantino, Deakins, or an original mood-based creative persona without an AI generation step.
- **Repo constraints / ADRs**: ADR-003 says templates beat parameters, style presets belong in the intent layer, and the product should feel like working with taste rather than files. ADR-002 says the app should surface meaningful capability state in an existing user-facing control surface, not as hidden backend functionality.
- **Existing patterns to reuse**: `src/cine_forge/roles/*/style_pack_prompt.md`, `src/cine_forge/roles/runtime.py`, `project.json` settings persistence in `src/cine_forge/api/service.py`, router-local endpoints in `src/cine_forge/api/routers/`, and the direct-operation UI pattern in `ui/src/lib/use-long-running-action.ts`.
- **Eval / success measure**: this is primarily orchestration, storage, and UI work, so the success measure is a focused mocked end-to-end test rather than promptfoo. Baseline today is zero in-app creation substrate. The new acceptance test should prove: generate draft from mocked deep-research output -> preview/edit/save -> list in project-local library -> assign in project settings -> runtime prompt injection can load the saved pack.

---

## Tasks

- [x] Implement deep research API integration (at least one provider).
- [x] Implement creation flow: template + input → research → output → validation → storage.
- [x] Implement async progress reporting.
- [x] Implement output formatting (research result → style pack folder structure).
- [x] Implement manual fallback flow.
- [x] Integrate with `deep-research` CLI tool (optional, if installed).
- [x] Implement UI for creation flow in Operator Console.
- [x] Implement style pack library (browse, select, assign to role).
- [x] Write unit tests.
- [x] Write integration test (mocked research API).
- [x] Run story-relevant validation checks (`make test-unit PYTHON=python`, `python -m ruff check src/ tests/`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`); repo-wide `make lint` remains red because of pre-existing unrelated Ruff issues outside the touched scope.
- [x] Update AGENTS.md with any lessons learned.

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared.
- [x] Validation complete or explicitly skipped by user.
- [x] Story marked done via `/mark-story-done`.

## Central Tenets

- [x] **T0 - Data Safety:** Generated packs save as new project-local files without mutating built-ins or silently clobbering existing pack IDs.
- [x] **T1 - AI-Coded:** The creation flow, parser, and runtime lookup are explicit enough that a future AI session can extend them without reverse engineering hidden conventions.
- [x] **T2 - Architect for 100x:** The first implementation keeps provider orchestration thin and avoids baking in extra scaffolding that a better research substrate would delete.
- [x] **T3 - Fewer Files:** New code should land in focused helper/router/component files so oversized service and settings files do not absorb more ownership.
- [x] **T4 - Verbose Artifacts:** Work log, tests, and API responses make the new pack lifecycle inspectable.
- [x] **T5 - Ideal vs Today:** The Operator Console should make taste authoring easier inside CineForge, not just add another technical form.

## Files to Modify

- `src/cine_forge/roles/runtime.py` - extend style-pack lookup to support project-local packs alongside built-ins (`479` lines)
- `src/cine_forge/api/models.py` - add request/response models for style-pack listing, draft generation, and save/assign flows (`510` lines)
- `src/cine_forge/api/service.py` - keep changes narrow: expose project style-pack selections in summaries and use a project-aware role catalog/context (`1145` lines, oversized)
- `src/cine_forge/api/app.py` - register the new router with minimal wiring only (`730` lines, oversized)
- `src/cine_forge/api/routers/style_packs.py` - new focused router for list/generate/save operations
- `src/cine_forge/services/style_packs.py` - new focused helper for project-local pack discovery, prompt rendering, deep-research execution, and deterministic parsing/validation
- `ui/src/components/ProjectSettings.tsx` - mount a new style-pack section/tab only; avoid adding the full feature inline (`467` lines, oversized)
- `ui/src/components/ProjectStylePacksSection.tsx` - new focused UI for library, generation form, preview/edit, and assignment
- `ui/src/lib/types.ts` - add frontend types for project style-pack state and API responses (`675` lines, oversized)
- `ui/src/lib/api/projects.ts` - add `style_packs` settings persistence to the existing project-settings request shape (`109` lines)
- `ui/src/lib/api/style-packs.ts` - new focused API client for style-pack endpoints
- `ui/src/lib/api.ts` - re-export the new style-pack client
- `tests/unit/test_style_packs.py` - extend runtime coverage for project-local overlay behavior
- `tests/unit/test_style_pack_service.py` - new focused service/parser tests with mocked `deep-research` subprocess calls
- `tests/unit/test_api_style_packs.py` - new focused API tests instead of widening `tests/unit/test_api.py`

## Plan

1. Add the missing project-local style-pack substrate without widening the existing role schema.
   Files: `src/cine_forge/roles/runtime.py`, new `src/cine_forge/services/style_packs.py`, small touch in `src/cine_forge/api/service.py`
   Change: keep built-in packs under `src/cine_forge/roles/style_packs`, but let project-local packs live under `<project>/style_packs/<role_id>/<style_pack_id>/`. Extend the runtime catalog to search project-local packs first, then built-ins, so saved packs become immediately usable by chat and role execution.
   Repo fit: this reuses Story 016's folder-based pack format and the existing `project.json` style-pack selection field instead of inventing a second artifact system.
   Structural health: `src/cine_forge/api/service.py` is `1145` lines, so the project-local catalog/search logic must live in a new helper file with only a narrow service seam.
   Done looks like: a project-local pack can be listed, loaded, and injected into role prompts the same way a built-in pack can.

2. Add a focused backend API for list, generate-draft, and save-and-assign.
   Files: `src/cine_forge/api/models.py`, `src/cine_forge/api/app.py`, new `src/cine_forge/api/routers/style_packs.py`, small touches in `src/cine_forge/api/service.py`
   Change: add typed endpoints to:
   - list style-pack-enabled roles and available packs for a project
   - generate a draft pack from a role template plus user input using the existing `deep-research` CLI
   - save a reviewed draft into the project-local pack library and optionally assign it in `project.json`
   Repo fit: routers are already the repo's preferred product API boundary, and this keeps service/app changes thin.
   Candidate approach choice: use the repo's existing `deep-research` CLI as the first implementation path. All three provider keys are configured as of `2026-04-09`, and the live discovery check confirms OpenAI, Anthropic, and Google are available. The backend should default to one honest provider path (`openai`) while keeping the provider parameter pluggable for the router/service contract.
   Recommended scope adjustment for approval: first implementation should support one provider run at a time via the shared CLI path, not multi-provider orchestration or synthesis. Exact research-cost accounting and a separate manual-fallback UI should stay out unless they prove trivial once the main flow is working. Relative effort avoided by this cut: `M`.
   Done looks like: the backend returns a validated draft payload from mocked CLI output, saves it into project-local storage, and persists selection changes through `project.json`.

3. Add an Operator Console surface in project settings without growing the existing oversized modal inline.
   Files: `ui/src/components/ProjectSettings.tsx`, new `ui/src/components/ProjectStylePacksSection.tsx`, `ui/src/lib/types.ts`, `ui/src/lib/api/projects.ts`, new `ui/src/lib/api/style-packs.ts`, `ui/src/lib/api.ts`
   Change: mount a dedicated style-pack section/tab inside Project Settings that:
   - lists the current project-local and built-in packs per role
   - shows the currently assigned pack per role
   - lets the user enter a subject, choose a role, start generation, review/edit the returned draft, save it, and optionally assign it immediately
   - uses `useLongRunningAction` for the generation call so the app shows an honest in-flight state instead of freezing silently
   Repo fit: project settings already own persisted per-project preferences, including `style_packs`, so this is the right existing surface.
   Structural health: `ui/src/components/ProjectSettings.tsx` is `467` lines and `ui/src/lib/types.ts` is `675` lines, so the new UI and API surface must be extracted into dedicated files rather than expanded inline.
   Done looks like: the settings modal exposes a style-pack workflow end-to-end and reflects saved selections accurately after refresh.

4. Add focused tests and verification around the project-local lifecycle.
   Files: `tests/unit/test_style_packs.py`, new `tests/unit/test_style_pack_service.py`, new `tests/unit/test_api_style_packs.py`
   Change: add mocked tests for:
   - runtime overlay lookup order (project-local over built-in)
   - prompt-template rendering and draft parsing from representative deep-research output
   - API round trip: generate draft -> save -> list -> assign -> summary reflects selection
   Redundancy plan: if the new overlay catalog makes any ad hoc path handling redundant, delete it instead of leaving a second pack-discovery path alive.
   Done looks like: the new tests cover the pack lifecycle without widening oversized generic test files.

5. Validate the touched backend and UI scopes, then do browser verification on desktop and mobile.
   Checks: `make test-unit PYTHON=python`, `python -m ruff check src/ tests/`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`
   Browser verification plan: use a normal project opened through the Operator Console, open Project Settings, generate a style-pack draft, save it, assign it to a role, refresh, and confirm the selection persists. Exercise the same flow once in desktop width and once in a narrow mobile width, with clean console output.
   Fallback if browser tooling blocks: follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker in the work log.
   Done looks like: static checks pass, the settings flow works in browser on desktop and mobile, and the story remains `In Progress` for `/validate` or `/mark-story-done`.

---

## Work Log

*(append-only)*

20260409-1538 - exploration: verified Story 034 still closes a live Ideal gap, but the original shell was stale and under-specified for current repo reality. Evidence: `docs/spec.md` (`spec:4.3`, `spec:4.4`), `docs/decisions/adr-003-film-elements/ADR.md`, `docs/stories.md`, `src/cine_forge/roles/*/role.yaml`, `src/cine_forge/roles/runtime.py`, `src/cine_forge/api/service.py`, `ui/src/components/ProjectSettings.tsx`, and `python scripts/discover-models.py --check-new` on 2026-04-09. Findings: style-pack format/prompt templates already exist from Story 016; missing substrate is project-local pack discovery plus an Operator Console flow; the story's "Actor Agent" role list is stale; `deep-research` CLI is installed (`0.3.4`) and all three provider keys are configured; `src/cine_forge/api/service.py` (`1145`) and `ui/src/components/ProjectSettings.tsx` (`467`) are already oversized, so new helper/component files are required. Next step: get approval on the narrowed first implementation path (single-provider CLI-backed draft generation, preview/edit/save, project-local runtime overlay) before code changes.
20260409-1548 - status-in-progress: approved the narrowed first implementation path and started building it. Scope for this pass: one provider at a time through the shared `deep-research` CLI, project-local style-pack storage and runtime overlay, preview/edit/save in Project Settings, and assignment persistence through `project.json`. Deferred unless trivial: multi-provider synthesis, manual fallback UI, and exact research-call cost accounting.
20260409-1638 - implementation: landed the first in-app style-pack creation slice. Added project-local overlay support to `RoleCatalog`, project-aware role catalogs for chat/service/driver runtime, a focused `StylePackService`, a new `/api/projects/{project_id}/style-packs` router (list/generate/save), project summary exposure for `style_packs`, and a dedicated `ProjectStylePacksSection` inside Project Settings for library, generation, draft review, save, and assign. Evidence: `src/cine_forge/roles/runtime.py`, `src/cine_forge/services/style_packs.py`, `src/cine_forge/api/routers/style_packs.py`, `src/cine_forge/api/service.py`, `src/cine_forge/api/app.py`, `src/cine_forge/driver/engine.py`, `ui/src/components/ProjectStylePacksSection.tsx`, and the new API client/types files. Result: saved packs now live under `<project>/style_packs/<role_id>/<style_pack_id>/`, selections persist through `project.json`, chat/runtime paths use project-aware catalogs, and the UI exposes the end-to-end workflow for the narrowed scope. Next step: validate and decide whether manual fallback + richer provider/cost handling stay in Story 034 or become a follow-on.
20260409-1655 - validation: `make test-unit PYTHON=python` passed (`676 passed, 157 deselected`); targeted style-pack/API coverage passed via `PYTHONPATH=src python -m pytest tests/unit/test_style_packs.py tests/unit/test_style_pack_service.py tests/unit/test_api_style_packs.py tests/unit/test_api_costs.py tests/integration/test_style_pack_integration.py -q`; `python -m ruff check src/ tests/` passed; `pnpm --dir ui run lint` completed with only 6 pre-existing warnings in unrelated files; `cd ui && npx tsc -b` passed; `pnpm --dir ui run build` passed; `pnpm methodology:check` passed. `make lint PYTHON=python` remains red for pre-existing repo-wide Ruff issues outside the touched scope (`.agents/skills/webapp-testing/scripts/with_server.py`, `benchmarks/scorers/*`, `scripts/check-compromises.py`, `scripts/discover-models.py`, `scripts/reset_playwright_mcp.py`). Browser verification used a normal project created through the New Project flow from `style-pack-smoke.fountain`: desktop and mobile screenshots captured the Style Packs tab, and a mobile UI interaction changed Director from Generic to Quentin Tarantino with a confirming `PATCH /api/projects/style-pack-smoke/settings` `200 OK`; `GET /api/projects/style-pack-smoke` then returned `\"style_packs\":{\"director\":\"tarantino\"}`. Live generation runtime check: a real `POST /api/projects/style-pack-smoke/style-packs/generate` call stayed in flight for multiple minutes as expected for deep research, and after moving the endpoint onto a threadpool the backend remained responsive to `GET /api/health` while generation was running. Remaining truth: the first pass still lacks manual fallback UI, exact research-call cost accounting, and a completed full-provider draft returned from a live deep-research run during this validation window. Recommended next step: keep Story 034 open and finish those remaining style-pack-creation gaps inside this same story rather than splitting them into close-out bookkeeping.
20260409-1708 - implementation-follow-up: closed the remaining product-facing Story 034 gaps inside the same style-pack subsystem instead of splitting them out. Added a manual fallback path that renders the role-specific prompt in-app and parses pasted external-model output back into the same draft review/save surface; extended the deep-research path to resolve provider-specific report filenames, preserve optional support materials into `additional_files`, and surface `research_cost` metadata from the CLI debug artifacts; and updated the Project Settings UI so manual and CLI-backed drafts share the same review/edit/save flow. Evidence: `src/cine_forge/services/style_packs.py`, `src/cine_forge/api/models.py`, `src/cine_forge/api/service.py`, `src/cine_forge/api/routers/style_packs.py`, `ui/src/components/ProjectStylePacksSection.tsx`, `ui/src/lib/api/style-packs.ts`, `ui/src/lib/types.ts`, `tests/unit/test_style_pack_service.py`, and `tests/unit/test_api_style_packs.py`. Verification: `python -m ruff check src/ tests/` passed; `make test-unit PYTHON=python` passed (`677 passed, 157 deselected, 1 warning`); `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` all passed with only the same pre-existing unrelated lint warnings. Browser evidence: desktop verification prepared a manual prompt, parsed pasted output, saved and assigned `city-dread`, then `GET /api/projects/style-pack-smoke` returned `\"style_packs\":{\"director\":\"city-dread\"}` and `<project>/style_packs/director/city-dread/research-notes.md` existed on disk; mobile verification reopened the Style Packs settings flow at narrow width with a clean console except the standard React DevTools info line. Live provider evidence: a real Anthropic run for `Michael Mann night-world tension with urban paranoia` completed successfully and returned draft `mann-nightworld-urban-paranoia` with `research_cost` `{model: claude-opus-4-6, total_tokens: 1697, estimated_cost_usd: 0.1, latency_seconds: 32.9, attribution: deep_research_cli_estimate}` while `GET /api/health` stayed `200 OK` during the in-flight request. Remaining truth: repo-wide `make lint` is still failing for unrelated Ruff debt outside the touched scope, and the cost figure is the deep-research CLI estimate rather than exact provider-billed telemetry. Next step: rerun `/validate` on the updated story state; if clean, close via `/mark-story-done`.
20260409-1714 - validate: reviewed the current local delta (`git status --short`, `git diff --stat`, untracked file list), re-checked alignment against `docs/spec.md` (`spec:4.3`, `spec:4.4`), Ideal `R6`/`R7`, `docs/methodology/state.yaml`, `docs/methodology/graph.json`, `docs/decisions/adr-002-goal-oriented-navigation/adr.md`, and `docs/decisions/adr-003-film-elements/adr.md`, then reran the full validation suite on the updated implementation. Evidence: `make test-unit PYTHON=python` passed (`677 passed, 157 deselected, 1 warning`); `python -m ruff check src/ tests/` passed; `pnpm --dir ui run lint` passed with the same 6 pre-existing unrelated warnings; `cd ui && npx tsc -b` passed; `pnpm --dir ui run build` passed; `./scripts/sync-agent-skills.sh --check` passed; `pnpm methodology:check` passed. Browser verification reran on a normal project state at `/style-pack-smoke` -> `Settings` -> `Style Packs`: desktop showed Director assigned to `City Dread · Project`, mobile showed the same settings flow at narrow width, and console output stayed clean except for the standard React DevTools info line. Validation result: Story 034 is implementation-complete; the remaining repo-wide `make lint` debt is unrelated pre-existing Ruff scope outside this story. Next step: close via `/mark-story-done`.
20260409-1715 - close-out: marked Story 034 done after the fresh validation pass confirmed the shipped scope matches the story's success surface. Evidence: workflow gates all checked; acceptance criteria all met; `make test-unit PYTHON=python`, `python -m ruff check src/ tests/`, `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, `./scripts/sync-agent-skills.sh --check`, and `pnpm methodology:check` all passed in the close-out window; desktop and mobile browser verification both passed on `/style-pack-smoke` -> `Settings` -> `Style Packs`. Result: Story 034 now closes as the in-app style-pack creation lane, including project-local packs, manual fallback, saved support files, and CLI-estimated research cost surfacing. Next step: `/check-in-diff`.

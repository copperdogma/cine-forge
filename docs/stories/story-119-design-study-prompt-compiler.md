# Story 119 — Design Study Prompt Compiler + Visual Reference Propagation

**Priority**: Medium
**Status**: Done
**Updated**: 2026-03-15 — story closed after validation; handed to `/check-in-diff`.
**Spec Refs**: Film Lane (spec §267) — visual references flow forward into shot planning, storyboards, animatics
**Depends On**: Story 056 (Design Study — Done), Story 120 (Production Format Setting — for `production_format` field in prompt compiler)

## Goal

The current design study prompt is thin: it only reads the entity bible. A real prompt compiler should gather everything that influences how the entity looks — genre, tone, visual style direction, and emotional mood — and synthesize a richer, more coherent image prompt. Additionally, when the user marks an image as `selected_final`, that filename should be written back to the entity's bible manifest as a `visual_reference_image` field so downstream stages (storyboard generator, video previz) can find the canonical character/location/prop image without manual wiring.

Two deliverables:
1. **Prompt compiler** — At generation time, load project_config (`genre`, `tone`, `production_format`), look_and_feel creative direction, and intent_mood creative direction. Weave relevant context into the synthesized prompt. Record which sources were actually used in the `DesignStudyRound` so the UI can show them.
2. **Downstream propagation** — When `selected_final` is set (via the decide endpoint), update the entity's bible manifest `visual_reference_image` field. When deselected, clear it.

## Acceptance Criteria

- [x] Generating an image with an existing look_and_feel artifact incorporates visual style language into the prompt (visible in `prompt_used` field)
- [x] Generating an image with project_config available incorporates genre/tone/medium context into the prompt
- [x] `DesignStudyRound.sources_used` lists which context sources contributed (e.g. `["entity_bible", "look_and_feel", "project_config"]`)
- [x] Sources panel in `DesignStudySection.tsx` lists what inputs were used for each round
- [x] Setting `selected_final` on an image updates the entity's bible manifest with `visual_reference_image: filename`
- [x] Deselecting (toggle off) clears `visual_reference_image` from the bible manifest
- [x] All existing design study integration tests pass
- [x] New integration test: generate with mock look_and_feel → verify prompt contains style language

## Out of Scope

- Actual storyboard generation (separate story)
- Video previz generation
- Image model selection beyond what Story 056 provides (model picker UI already exists)
- Prompt compiler UI for manual editing of the synthesized prompt
- Seed image conditioning via API (Imagen 4 doesn't support image-to-image in the current API)

## Approach Evaluation

This is pure plumbing — no AI reasoning needed for the prompt compiler itself. The synthesis is deterministic: gather fields, concatenate with priority ordering, truncate if needed.

- **Pure code**: Read artifact store for look_and_feel + project_config + intent_mood, extract relevant fields (visual style, genre, tone, and production-medium keywords), append to bible-derived prompt. Simple string operations, no LLM call. This is almost certainly the right approach.
- **AI-assisted synthesis**: LLM takes the raw context objects and writes a unified visual brief. Higher quality but adds latency and cost to every generation call. Not justified when the downstream call (Imagen 4) is already ~15s.
- **Eval**: Manual inspection of generated images with/without context enrichment — does the enriched version look more consistent with the intended film style? No automated eval needed at this stage; visual quality is subjective. Document examples in the work log.

**Decision gate**: Start with pure code. If after 10+ real generations the prompts feel generic/inconsistent with the film direction, revisit AI-assisted synthesis.

## Tasks

- [x] Reuse the existing `DesignStudyRound.sources_used` contract and extend the prompt/compiler path so it records `look_and_feel`, `intent_mood`, and richer `project_config` context without introducing a second provenance field
- [x] Add `visual_reference_image: str | None = None` to `BibleManifest` and thread that optional field through `ArtifactStore.save_bible_entry()` so the selected-final choice can be persisted immutably as part of the canonical bible manifest
- [x] Extend `build_image_prompt()` in `src/cine_forge/ai/image.py` so it accepts `bible_data` + optional `project_config_data`, `look_and_feel_data`, and `intent_mood_data`
- [x] Update generate router to load project_config, look_and_feel, intent_mood from artifact store before calling prompt builder; populate `sources_used` on the round
- [x] Extract focused child components from `DesignStudySection.tsx` before adding new prompt-provenance UI so this story does not deepen an already-oversized file/component
- [x] Add "Sources used" display in `DesignStudySection.tsx` (collapsed per-round panels for the latest round and history)
- [x] Update decide router: when decision becomes `selected_final`, write `visual_reference_image` to bible manifest; when deselected, clear it
- [x] Add integration test: generate with mock look_and_feel → verify prompt contains style language
- [x] Add manifest-versioning coverage proving `selected_final` writes and clears `visual_reference_image` on successive bible manifest versions
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint` and `cd ui && npx tsc -b`
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

- **Owning class/module**: `src/cine_forge/ai/image.py` (prompt synthesis), `src/cine_forge/api/routers/design_study.py` (context loading + propagation)
- **Data contracts**: `DesignStudyRound.sources_used` already exists and should be extended, not reinvented. `BibleManifest` needs a schema-first optional `visual_reference_image: str | None`, and `ArtifactStore.save_bible_entry()` needs an explicit way to persist it when a new manifest version is written. No new event type is needed.
- **File sizes**: `src/cine_forge/ai/image.py` is 452 lines, `src/cine_forge/api/routers/design_study.py` is 427 lines, and `src/cine_forge/schemas/design_study.py` is 78 lines. `ui/src/components/DesignStudySection.tsx` started at 578 lines and was reduced to 399 lines by extracting focused child components during implementation; the two backend modules crossed the 400-line acknowledgement threshold but remain below the 600-line validation threshold.

## Files to Modify

- `src/cine_forge/schemas/bible.py` — add `visual_reference_image: str | None = None` to `BibleManifest`
- `src/cine_forge/artifacts/store.py` — extend `save_bible_entry()` so manifest-level fields such as `visual_reference_image` can be persisted without bypassing immutability
- `src/cine_forge/ai/image.py` — extend `build_image_prompt()` so it compiles bible + project-config + look-and-feel + intent-mood context through one deterministic path
- `src/cine_forge/api/routers/design_study.py` — load context before generation; update decide endpoint to propagate to bible manifest (298 lines)
- `src/cine_forge/services/injected_assets.py` — switch downstream entity-reference collection to the canonical bible-manifest `visual_reference_image` field
- `ui/src/components/DesignStudySection.tsx` — extract focused child components and add Sources display in generate area
- `ui/src/components/DesignStudyImageCard.tsx` — extracted image-card interaction surface so the section drops below the size threshold
- `ui/src/components/DesignStudySourcesPanel.tsx` — new component for prompt/source provenance display
- `tests/unit/test_design_study.py` — extend prompt-builder coverage for look-and-feel / intent-mood / project-config context
- `tests/unit/test_bible_infrastructure.py` — cover manifest persistence of `visual_reference_image`
- `tests/unit/test_injected_assets.py` — cover downstream visual-reference collection from the canonical bible-manifest field
- `tests/integration/test_api_design_study.py` — add context-enrichment test (232 lines)

## Notes

- `look_and_feel` and `intent_mood` artifacts may not exist for a project — gracefully degrade, just use bible + project_config
- The `sources_used` field on `DesignStudyRound` is display-only — it doesn't affect generation logic, only shows the user what fed the prompt
- For `visual_reference_image` propagation: check whether bible manifest schema already has a slot for this or needs a new optional field. If the schema doesn't have it, adding it is a small non-breaking change (optional field with `None` default).
- Priority ordering for prompt assembly: specific entity description (bible) > visual style (look_and_feel) > genre/tone/medium context (project_config) > emotional tone (intent_mood). More specific = higher priority = earlier in prompt.
- This is the foundation for storyboard generation consistency: the storyboard module will load `visual_reference_image` to use as a face/design reference when available.

## Plan

### Exploration Summary

- Story status is `Pending` and aligned with the Ideal: it improves R12 transparency (`prompt_used` + `sources_used`), strengthens R8/R11 downstream visual consistency via canonical reference propagation, and is the right foundation before Story 121 and higher-fidelity storyboard work.
- ADR / decision context consulted: `docs/ideal.md`, `docs/spec.md` prompt-compiler language, ADR-003, `docs/design/decisions.md` provenance guidance, Story 056, Story 120, and the current design-study backend/frontend code path.
- Exploration found two small required scope expansions that should stay inside this story:
  - `BibleManifest` + `ArtifactStore.save_bible_entry()` must grow an optional `visual_reference_image` path, otherwise the router cannot persist the canonical selection immutably.
  - `ui/src/components/DesignStudySection.tsx` is already 578 lines and the main component is >100 lines, so a focused extraction is required before adding new UI logic.
- Exploration also found one larger optional scope expansion that should **not** be silently absorbed: Story 119 talks about project `period`, but `ProjectConfig` does not currently have a first-class `period` field. Delivering true period-aware prompt compilation would require a broader schema + ingestion expansion.

### Eval-First Approach Gate

- **What eval?**
  - Unit eval: extend `tests/unit/test_design_study.py` so `build_image_prompt()` with mock `project_config`, `look_and_feel`, and `intent_mood` data must include representative context strings and the expected `sources_used` tags.
  - Integration eval: extend `tests/integration/test_api_design_study.py` so a mocked generate request with seeded `look_and_feel` / `intent_mood` / `project_config` artifacts proves the stored `prompt_used` and `sources_used` reflect those inputs.
  - Integration eval: extend the decide flow test so selecting and then clearing `selected_final` produces new bible manifest versions with `visual_reference_image` set/cleared.
- **Baseline**
  - Static baseline from exploration: current `build_image_prompt()` only accepts `project_config_data`; the router only loads project config; `BibleManifest` has no `visual_reference_image`; and `ArtifactStore.save_bible_entry()` has no manifest-level field for it. On the proposed evals, current code is effectively 0/2 on the new capabilities.
  - Runtime baseline is currently blocked in this worktree because the documented `.venv/bin/python` interpreter is missing, the system `python3` lacks project dependencies such as `pydantic`, and `pytest` is not installed there. Implementation should either use the intended project environment or bootstrap it before test execution.
- **Candidate approaches**
  - Pure code: deterministic prompt assembly from current artifacts plus immutable manifest propagation.
  - Hybrid: deterministic source selection, then one LLM call to rewrite those inputs into a unified visual brief.
  - AI-only: hand raw artifact payloads to an LLM and let it author the full prompt every time.
- **Chosen approach**
  - Pure code is the repo fit. Story 120 already introduced `build_image_prompt()` and `sources_used`; ADR-003 explicitly positions prompt compilation as stateless plumbing; and the UI already exposes `prompt_used`, which makes deterministic prompt composition auditable and testable.
  - Hybrid / AI-only are rejected here because they add latency and cost to every generation, weaken source attribution, and solve a problem the repo already models as deterministic prompt compilation.

### Structural Health Check

- `make check-size` result for touched files:
  - `ui/src/components/DesignStudySection.tsx` — 578 lines, already large; must be decomposed before adding more logic.
  - `src/cine_forge/ai/image.py` — 353 lines.
  - `src/cine_forge/api/routers/design_study.py` — 325 lines.
  - `src/cine_forge/artifacts/store.py` — 262 lines.
  - `tests/integration/test_api_design_study.py` — 243 lines.
  - `tests/unit/test_design_study.py` — 227 lines.
  - `src/cine_forge/schemas/bible.py` — 134 lines.
  - `ui/src/lib/api/design-study.ts` — 103 lines.
  - `src/cine_forge/schemas/design_study.py` — 78 lines.
- Method / function risks:
  - `DesignStudySection` is already an oversized function component. First UI task should extract the new provenance UI into a focused child component so this story reduces, rather than deepens, the oversized surface.
- Schema / contract checks:
  - New persisted boundary data is schema-first: `BibleManifest.visual_reference_image` before router/store usage.
  - `DesignStudyRound.sources_used` already exists in the schema and TS types; extend that existing contract instead of inventing a second provenance field.
  - No new event type is needed.

### Task-by-Task Plan

1. **Tighten the backend data contract for canonical visual references.**
   - Files: `src/cine_forge/schemas/bible.py`, `src/cine_forge/artifacts/store.py`, `tests/unit/test_bible_infrastructure.py`
   - Change: add optional `visual_reference_image` to `BibleManifest` and extend `ArtifactStore.save_bible_entry()` with an optional manifest-level argument so new manifest versions can persist it without bypassing the store.
   - Impact / risk: touches shared bible persistence, so tests must prove existing callers still work when the new arg is omitted.
   - Done looks like: bible manifests round-trip with or without `visual_reference_image`, and the store still writes immutable versioned manifests.

2. **Extend the prompt compiler with current-project context, not speculative schema.**
   - Files: `src/cine_forge/ai/image.py`, `tests/unit/test_design_study.py`
   - Change: extend `build_image_prompt()` to accept optional `look_and_feel_data` and `intent_mood_data` in addition to `project_config_data`; compile from the fields that exist today (`genre`, `tone`, `production_format`, `mood_descriptors`, `reference_films`, `natural_language_intent`, and relevant `LookAndFeel` fields such as lighting/color/composition/camera/costume/production-design notes).
   - Repo-fit evidence: this keeps Story 120’s deterministic prompt builder as the single compiler path.
   - Done looks like: unit tests show prompt text and `sources_used` tags change only when those artifacts are present.

3. **Refactor router context loading and keep generate/decide handlers focused.**
   - Files: `src/cine_forge/api/routers/design_study.py`, `tests/integration/test_api_design_study.py`
   - Change: add focused helpers to load the latest project-level artifact payload for `project_config`, `look_and_feel`, and `intent_mood`; use them in `generate_design_study()`. Add a focused helper for manifest propagation so `decide_design_study()` writes a new bible manifest version when `selected_final` changes.
   - Impact / risk: router currently only loads project config, so this is the main behavior change. Keep helper extraction in the router rather than spreading prompt-context loading into new services prematurely.
   - Done looks like: mocked integration tests prove `prompt_used` includes seeded look-and-feel language and that `selected_final` writes/clears `visual_reference_image` on successive manifest versions.

4. **Expose prompt provenance in the frontend without growing the oversized design-study component.**
   - Files: `ui/src/components/DesignStudySection.tsx`, `ui/src/components/DesignStudySourcesPanel.tsx`, `ui/src/lib/api/design-study.ts`
   - Change: extract a small provenance-focused child component and render a collapsed “Sources used” surface for each round (or the current round, depending on the final UX chosen) using the existing `sources_used` array.
   - Decision-context evidence: `docs/design/decisions.md` requires visible provenance on demand, not noisy always-on explanations.
   - Done looks like: the entity detail design-study UI shows source tags clearly without bloating `DesignStudySection.tsx` further, and the TS build passes.

5. **Verification and runtime smoke.**
   - Backend static: `make test-unit PYTHON=.venv/bin/python`, `.venv/bin/python -m ruff check src/ tests/`
   - UI static: `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`
   - Runtime / browser: start backend + UI, open `/:projectId/characters/:entityId` for an entity with a design study, trigger Generate, inspect the updated prompt provenance UI, then mark an image `Final` and toggle it off to verify the flow and console remain clean.
   - Fallback if browser tooling is unavailable: follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker in the work log.

### Redundancy / Cleanup Plan

- Do not create a second prompt-compilation path; keep `build_image_prompt()` as the single assembly function.
- Do not add a sidecar manifest updater that bypasses `ArtifactStore`; the canonical selection must flow through immutable manifest versions.
- Avoid hardcoded UI label duplication by centralizing `sources_used` label rendering in the extracted child component.
- If implementation reveals unused helper code from the pre-Story-119 prompt path, remove it in the same story rather than leaving dead branches behind.

### Approval Blockers / Questions For Human Gate

- **Project period scope**: the story text expects project `period`, but the current `ProjectConfig` schema has no such field. Recommendation: keep Story 119 scoped to the project-config fields that exist today (`genre`, `tone`, `production_format`) plus `look_and_feel` / `intent_mood`, and treat explicit `period` support as a separate follow-on if you want it. Relative effort for folding true `period` into this story: `M`.
- **Environment mismatch**: the documented `.venv/bin/python` is absent in this worktree, and system Python lacks project dependencies. Recommendation: unless you want a different interpreter, I’ll bootstrap/use the correct environment as part of implementation so the required checks can actually run.

## Work Log

20260303-1600 — story created: Design discussion with user during Story 056 browser testing — user wants prompt compiler (gather genre/style/mood context) and downstream propagation (selected_final → bible manifest). This is a Draft; needs design review before building.
20260314 — Backlog cleanup: promoted to Pending. Story 120 landed, the tasks/files are concrete, and this is the right foundation before Story 121 or storyboard-quality follow-ons.
20260315-1318 — exploration + planning: confirmed Story 119 still moves toward the Ideal (R12 transparency, R8/R11 downstream visual consistency) and is not listed as a shrinking compromise in `docs/retrofit-gaps.md`; reviewed ADR-003, `docs/design/decisions.md`, Story 056, Story 120, `src/cine_forge/{ai/image.py,api/routers/design_study.py,schemas/design_study.py,schemas/bible.py,artifacts/store.py}`, `ui/src/{components/DesignStudySection.tsx,lib/api/design-study.ts}`, and current tests. Key findings: `sources_used` and `build_image_prompt()` already landed in Story 120; router currently loads only `project_config`; `BibleManifest` and `ArtifactStore.save_bible_entry()` cannot yet persist `visual_reference_image`; `DesignStudySection.tsx` is already 578 lines and needs extraction before more UI logic; and the worktree is missing the documented `.venv`, so runtime baseline execution is blocked until the correct Python environment is available. Next step: human approval on the implementation plan, including whether to keep Story 119 scoped to current project-config fields or absorb a broader `period` schema expansion.
20260315-1340 — implementation start: user approved the scoped plan (current `project_config` fields only; no new `period` schema in this story). First task is backend contract work: add `visual_reference_image` to bible manifests and extend immutable manifest persistence so the design-study `selected_final` choice has a canonical downstream home. Next step: implement schema/store changes, then thread them through router/compiler/tests.
20260315-1456 — backend/compiler implementation: added `BibleManifest.visual_reference_image`, taught `ArtifactStore.save_bible_entry()` to persist or preserve that manifest field immutably, extended `build_image_prompt()` to compile `look_and_feel`, `project_config`, and `intent_mood` context into one deterministic prompt, refactored the design-study router to load those project-level artifacts before generation, persisted canonical visual references on `selected_final`, and switched injected-asset downstream reference collection to the bible-manifest field instead of reading `design_study_state.json` directly. Evidence: `src/cine_forge/{schemas/bible.py,artifacts/store.py,ai/image.py,api/routers/design_study.py,services/injected_assets.py}`, `tests/unit/{test_bible_infrastructure.py,test_design_study.py,test_injected_assets.py}`, `tests/integration/test_api_design_study.py`; targeted regression suite=`30 passed` across unit+integration design-study/injected-asset files. Next step: extract the UI provenance surface and verify the full stack.
20260315-1538 — UI extraction + provenance UX: extracted `DesignStudyImageCard.tsx` and `DesignStudySourcesPanel.tsx`, rewired `DesignStudySection.tsx` to render per-round sources panels for the latest round and history, grouped history by round instead of flattening it, and mirrored the backend's single-canonical-final rule in the optimistic UI update path. Structural result: `DesignStudySection.tsx` dropped from 578 lines to 398 lines, satisfying the file-size health constraint instead of worsening it. Evidence: `ui/src/components/{DesignStudySection.tsx,DesignStudyImageCard.tsx,DesignStudySourcesPanel.tsx}`. Next step: bootstrap the missing local env and run the required backend/UI checks.
20260315-1608 — static verification: bootstrapped the missing `.venv` with `pip install -e '.[dev]'` and installed `ui` dependencies with `pnpm install --dir ui --frozen-lockfile`, then ran `make test-unit PYTHON=.venv/bin/python` → `552 passed, 127 deselected, 1 pre-existing acceptance-mark warning`; `.venv/bin/python -m ruff check src/ tests/` → clean; `.venv/bin/python -m pytest tests/integration/test_api_design_study.py` → `5 passed`; `pnpm --dir ui run lint` → 0 errors with 5 pre-existing `react-refresh/only-export-components` warnings in unrelated files; `cd ui && npx tsc -b` → clean; `pnpm --dir ui run build` → clean with the existing Vite chunk-size warning. Next step: run a browser smoke against a live seeded project to verify the new sources panels and manifest propagation path.
20260315-1628 — runtime smoke: seeded `output/story-119-smoke` with a character bible, design-study state, and local JPEGs; started backend on `http://127.0.0.1:8000` and Vite on `http://127.0.0.1:5174`; confirmed `curl http://127.0.0.1:8000/api/health` → `{"status":"ok","version":"2026.03.15-01"}` and `GET /api/projects/story-119-smoke` returned the project summary. Browser verification on `http://127.0.0.1:5174/story-119-smoke/characters/mariner` showed the new latest-round sources panel (Round 2 badges: Entity Bible, Look & Feel, Project Config, Intent & Mood, User Guidance, Seed Image), expandable historical Round 1 sources, and no console errors beyond the standard React DevTools info message. Clicking `Final` on the latest image returned `POST /design-study/character_mariner/decide` 200 and created bible manifest v2 with `visual_reference_image=design_study_r2_img1.jpg`; clicking it again toggled back to pending, returned 200 again, and created bible manifest v3 with `visual_reference_image=None`. Network log for the live route showed only 200 responses for the project/artifact/design-study requests. Next step: hand off for `/validate` with the story left In Progress per protocol.
20260315-1902 — validation: reran the required checks on the implementation diff: `make test-unit PYTHON=.venv/bin/python` → `552 passed, 127 deselected, 1 pre-existing acceptance-mark warning`; `.venv/bin/python -m ruff check src/ tests/` → clean; `.venv/bin/python -m pytest tests/integration/test_api_design_study.py` → `5 passed`; `pnpm --dir ui run lint` → 0 errors with the same 5 pre-existing fast-refresh warnings in unrelated files; `cd ui && npx tsc -b` → clean; `pnpm --dir ui run build` → clean with the existing Vite chunk-size warning. Fresh browser validation on `http://127.0.0.1:5174/story-119-smoke/characters/mariner` confirmed the latest-round sources panel, expandable Round 1 sources, `Final` set/clear round-tripping through the live API with 200 responses, zero browser console errors, and immutable bible manifest versions `v4`/`v5` reflecting `visual_reference_image` set then cleared on the seeded smoke project. No relevant promptfoo or acceptance eval harness exists for this deterministic prompt-compilation path, so no eval registry update was required in this validation pass. Next step: `/mark-story-done`.
20260315-1912 — close-out: `/mark-story-done` confirmed the build and validation gates, all acceptance criteria and tasks are complete, and the story index/changelog now reflect the landed prompt compiler + canonical visual-reference propagation slice. Evidence remains the validated backend/UI/browser pass recorded above. Next step: `/check-in-diff`.

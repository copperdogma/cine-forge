---
id: "097"
title: "AI Artifact Editing"
status: "Done"
priority: "Unknown"
ideal_refs:
  - "R4 (creative conversation), R5 (full spectrum of involvement), R12 (transparency)"
spec_refs:
  - "spec:1.3"
  - "spec:4.10.7"
  - "spec:5.4"
adr_refs:
  - "ADR-003"
depends_on:
  - "014"
  - "019"
  - "031"
  - "083"
category_refs:
  - "spec:1"
  - "spec:4"
  - "spec:5"
compromise_refs: []
input_coverage_refs: []
architecture_domains: []
roadmap_tags: []
legacy_system: ""
---

# Story 097: AI Artifact Editing

**Status**: Done
**Created**: 2026-02-27
**Updated**: 2026-04-02
**Source**: ADR-003, Decision #4
**Spec Refs**: spec:1.3 (Revision and Change Propagation), spec:4.10.7 (Prompt Compilation Model — upstream editing mechanism), spec:5.4 (Human Interaction Model)
**Ideal Refs**: R4 (creative conversation), R5 (full spectrum of involvement), R12 (transparency)
**ADR Refs**: ADR-003 (film elements / upstream editing), Story 083 (assistant-only write-tool architecture)
**Depends On**: Story 014 (role system), Story 019 (human control modes), Story 031 (semantic change propagation), Story 083 (group chat architecture)

---

## Goal

Give CineForge a repo-fit conversational upstream-edit loop: when the user says "give the Mariner a moustache," chat proposes the correct upstream artifact edit, the edit is applied through the right persistence path with AI provenance, existing change propagation marks downstream artifacts stale, and any downstream compiled prompts can recompile from the updated canon.

## Why (Ideal Alignment)

The Ideal describes conversational iteration: "No, darker." "Give John slicked-back hair." "Drop the fedora." Each of these is an instruction to change an upstream artifact. Today, the AI can suggest changes but the user must navigate to the artifact and make the edit manually. This story closes that gap — the AI becomes the editing agent.

This is also essential for the read-only prompt model. Users can't edit prompts directly; instead, they tell the AI what to change, and the AI changes the right upstream artifact. Without this capability, the read-only prompt decision creates friction.

This story is not greenfield. The repo already has a partial chat proposal path plus a generic artifact-edit endpoint, but the current implementation stops short of a trustworthy AI-authored edit loop:
- `src/cine_forge/ai/chat.py` can already emit `propose_artifact_edit` confirmation buttons, but it only does shallow patching and ignores folder-backed bible content.
- `src/cine_forge/api/artifact_manager.py` can already create new artifact versions, but it hardcodes human provenance and routes every artifact through the generic `save_artifact()` path.
- `bible_manifest` edits are currently broken through that generic path: a quick repro on 2026-04-01 confirmed it writes `v2.json` inside the bible folder while the loader only recognizes `manifest_v*.json`, so the new version is not discoverable via normal artifact APIs.

The right build target is therefore not "invent AI artifact editing from scratch." It is "finish the existing chat proposal/edit path so it works for the actual canonical artifacts, records AI provenance honestly, and respects the repo's existing control-mode and write-tool architecture."

## Sequencing Note

Do not build this ahead of Story 031. Layer 1 stale-marking from Story 002 makes upstream edits technically possible, but Story 031 is what gives CineForge a coherent way to inspect and resolve the resulting downstream staleness.

Also do not reinterpret Story 031 as permission to auto-run semantic impact assessment on every edit. Story 031 explicitly made Layer 2 assessment on-demand. Story 097 should rely on automatic Layer 1 stale propagation and surface the existing Layer 2 actions when useful, not silently spend model budget on every artifact edit.

## Acceptance Criteria

- [x] Chat can propose human-reviewable upstream edits for supported canon artifacts instead of telling the user to hunt through artifact screens manually.
- [x] Supported first-slice artifacts include:
  - [x] Folder-backed character, location, and prop bibles via `bible_manifest` plus their canonical text/JSON master-definition content.
  - [x] Plain JSON artifacts already served cleanly by the generic artifact APIs, including `script_bible` and concern-group artifacts.
- [x] The user can approve or reject a proposed edit, and can revise the proposal by continuing the conversation instead of opening a separate manual editor.
- [x] Approved edits create new immutable artifact versions with honest AI provenance:
  - [x] `ArtifactMetadata.source` is not recorded as `human`.
  - [x] `ArtifactMetadata.producing_role` records the AI role responsible for the proposal.
  - [x] The originating chat message or equivalent chat reference is stored in metadata annotations.
  - [x] The rationale that justified the edit is preserved.
- [x] `bible_manifest` edits persist through the correct folder/manifest write path (`save_bible_entry` semantics), so new versions are discoverable through standard artifact browsing APIs.
- [x] Existing Layer 1 change propagation fires automatically on approval, marking downstream artifacts stale through the dependency graph. Story 031 semantic impact assessment remains available from the existing preview/assess flows and is not silently auto-run.
- [x] Control-mode behavior is coherent with Story 019:
  - [x] `checkpoint` and `advisory` require explicit human confirmation before an AI edit is applied.
  - [x] `autonomous` can apply a supported AI edit without an extra confirmation click, but the user still gets a visible chat/activity notification and a route to inspect the new artifact version.
- [x] Assistant-only write-tool architecture remains intact unless explicitly expanded: creative roles can still drive edit proposals through chat, but the assistant remains the write broker per Story 083.
- [x] Read-only compiled artifacts such as `render_prompt` remain non-editable with clear upstream-edit guidance.

## Out of Scope

- A new per-feature "ask / notify / silent" autonomy settings layer beyond the existing `human_control_mode` substrate from Story 019
- Giving every creative role direct write/proposal tools inside chat; Story 083's assistant-broker pattern remains the repo fit for this slice
- Arbitrary binary or reference-image mutation inside bible folders; first slice owns the canonical text/JSON content, not every file type
- Automatic semantic impact assessment after every edit
- Direct editing of compiled artifacts such as `render_prompt`

## Approach Evaluation

- **Simplification baseline**: partial implementation already exists. `propose_artifact_edit` in `src/cine_forge/ai/chat.py` can show a diff preview and `POST` to `/api/projects/{project_id}/artifacts/{artifact_type}/{entity_id}/edit`, but it only shallow-patches the current payload, ignores `bible_files`, and emits no AI provenance. The backend `edit_artifact()` path in `src/cine_forge/api/artifact_manager.py` always records `source="human"` and `producing_module="operator_console.manual_edit"`. On 2026-04-01, a direct repro confirmed that `save_artifact("bible_manifest", ...)` writes `v2.json` while bible-manifest discovery only reads `manifest_v*.json`, so the generic path is incorrect for folder-backed bibles.
- **AI-only**: reject. Letting the model blindly rewrite full artifact payloads is the wrong fit for folder-backed bibles, control-mode policy, and immutable provenance. AI should decide the content change, not own persistence semantics.
- **Hybrid**: best fit. Use the existing chat/LLM layer to decide what should change and produce the proposed new content, then use deterministic backend routing to validate permissions, choose the correct persistence path, write immutable versions, and record provenance.
- **Pure code**: reject. Natural-language edit intent such as "make him look older and more weathered" is not a deterministic patching problem.
- **Repo-fit evidence**:
  - ADR-003 makes prompts read-only compiled artifacts; upstream artifact editing is the intended mechanism.
  - Story 083 explicitly keeps write/proposal tools on the assistant while creative roles remain read-only in chat.
  - Story 019 already owns the project-level `human_control_mode` substrate; Story 089 is only the tone/detail selector (`guided` / `balanced` / `expert`) and is not the right autonomy dependency.
  - Story 031 explicitly made semantic impact assessment on-demand, so Story 097 should not invent silent auto-assessment.
- **Eval / measurement**: no promptfoo eval is required because this is mainly orchestration, persistence, and UI contract work. The minimum acceptance harness is focused regression coverage around: proposal generation, approval behavior by control mode, AI provenance recording, and the corrected `bible_manifest` versioning path.

## Tasks

- [x] Extract artifact-edit proposal and persistence helpers out of oversized owners before adding behavior.
  - [x] Move the artifact-edit chat logic out of `src/cine_forge/ai/chat.py` (2287 lines) into a focused helper/module.
  - [x] Keep `src/cine_forge/api/artifact_manager.py` (553 lines) thin by introducing a focused edit-routing helper instead of growing the class in place.
- [x] Extend the edit contract schema-first:
  - [x] Add optional AI provenance fields to the API request/response models before the UI or backend uses them.
  - [x] Thread matching frontend types through the chat action payload path.
- [x] Implement shared artifact-edit routing that supports both existing human edits and AI-applied edits:
  - [x] Keep plain JSON artifacts on the standard `save_artifact()` path.
  - [x] Route `bible_manifest` edits through `save_bible_entry()` semantics so new manifest versions are named and discoverable correctly.
  - [x] Preserve lineage and shared edit-policy enforcement for both human and AI paths.
- [x] Make chat proposal generation artifact-family aware:
  - [x] Load and diff canonical `bible_files` content for folder-backed bibles instead of only diffing manifest metadata.
  - [x] Keep read-only artifact restrictions intact.
  - [x] Validate that the requested artifact type is permitted for the acting role or brokered through the assistant.
- [x] Apply Story 019 control-mode behavior to chat-driven edits:
  - [x] `checkpoint` / `advisory`: confirmation button required.
  - [x] `autonomous`: apply immediately and append a visible inspection route for the new version.
- [x] Persist AI provenance honestly in artifact metadata and expose enough success detail for the user to inspect what happened.
- [x] Add focused regression coverage without enlarging the oversized generic API test file:
  - [x] Chat proposal tests
  - [x] Artifact-edit routing tests, including the discovered `bible_manifest` bug
  - [x] API tests for AI provenance and control-mode behavior in a dedicated test file
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI (if touched): `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`
- [x] If UI is touched: verify the changed flow with browser tools when possible (chat proposal -> apply -> artifact detail) and record the blocker if browser tooling is unavailable
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

- **Owning modules**: assistant-chat orchestration can stay in the existing chat surface, but artifact-edit proposal building should move into a focused helper instead of growing `src/cine_forge/ai/chat.py` further. Backend persistence routing should live in a focused edit helper used by `ArtifactManager`, not as more special cases spread across `app.py`, `service.py`, and chat code.
- **Data contracts**: the API/UI boundary already has `ArtifactEditRequest` / `ArtifactEditResponse`; extend those models rather than inventing an untyped side channel. Persist AI provenance in `ArtifactMetadata.producing_role` plus structured `annotations`, not only in free-form rationale text.
- **Structural health check**:
  - `make check-size` run on 2026-04-01.
  - Likely touched files and current line counts:
    - `src/cine_forge/ai/chat.py` — 2287 (large; extract first)
    - `src/cine_forge/api/artifact_manager.py` — 553 (large; extract first)
    - `src/cine_forge/api/service.py` — 1090 (large; keep as delegator only)
    - `src/cine_forge/api/app.py` — 715 (large; keep route thin)
    - `src/cine_forge/api/models.py` — 489
    - `src/cine_forge/artifacts/store.py` — 290
    - `ui/src/lib/types.ts` — 600 (large; acknowledge minimal changes or isolate new types)
    - `ui/src/components/chat/ChatMessageItem.tsx` — 268
    - `ui/src/components/chat/ActionButton.tsx` — 178
    - `tests/unit/test_api.py` — 1299 (large; do not grow further)
    - `tests/unit/test_chat_artifact_edits.py` — 29
  - No new event schema appears necessary.
  - New API/UI fields must be declared in Pydantic/TypeScript models before the implementation uses them.
- **Scope correction discovered during exploration**:
  - Small inline expansion to absorb now: fix the broken `bible_manifest` persistence path for artifact edits generally, not only for the AI path. Leaving human direct-edit behavior broken would keep two contradictory edit semantics for the same canonical artifact family.
  - Larger expansion not absorbed: per-feature edit autonomy settings beyond `human_control_mode`, or direct write tools for every creative role. Either would widen this story from `S` to `M`.

## Files to Modify

- `src/cine_forge/ai/chat.py` — thin integration only after extraction
- `src/cine_forge/ai/` new focused helper for artifact-edit proposal generation (new)
- `src/cine_forge/api/artifact_manager.py` — thin integration only after extraction
- `src/cine_forge/api/models.py` — edit-contract request/response fields
- `src/cine_forge/artifacts/store.py` or a new backend edit helper — correct `bible_manifest` persistence semantics
- `src/cine_forge/api/service.py` / `src/cine_forge/api/app.py` — delegator/route changes only if request models change
- `ui/src/components/chat/ChatMessageItem.tsx` — pass parent message context into confirm actions if needed for provenance
- `ui/src/components/chat/ActionButton.tsx` — send the richer edit payload and handle auto-apply success messaging
- `ui/src/lib/types.ts` — matching API/chat action types
- `tests/unit/test_chat_artifact_edits.py` — expand beyond read-only rejection
- `tests/unit/` new focused API/backend edit test file(s) instead of adding more cases to `tests/unit/test_api.py`

## Redundancy / Removal Targets

- The current shallow patch-only proposal logic in `src/cine_forge/ai/chat.py` once the focused helper lands
- Duplicate metadata builders that separately hardcode "human manual edit" vs "AI edit" semantics
- Any fallback path that still lets `bible_manifest` edits drift onto the generic `save_artifact()` naming convention

## Plan

### Exploration Notes (2026-04-01)

- **Ideal alignment**: this story directly closes the conversational upstream-edit gap identified by ADR-003. It is not premature infrastructure; the repo already has a partial proposal/apply loop that simply stops short of canon-safe AI editing.
- **Code paths traced**:
  - Chat proposal path: `src/cine_forge/ai/chat.py` (`propose_artifact_edit`, `_execute_propose_artifact_edit`)
  - Generic edit endpoint: `src/cine_forge/api/app.py`, `src/cine_forge/api/models.py`, `src/cine_forge/api/artifact_manager.py`
  - Persistence semantics: `src/cine_forge/artifacts/store.py`, `src/cine_forge/driver/artifact_persister.py`
  - Existing change propagation: `src/cine_forge/artifacts/graph.py`, `src/cine_forge/services/impact_assessment.py`
  - Frontend confirm-action path: `ui/src/components/chat/ActionButton.tsx`, `ui/src/components/chat/ChatMessageItem.tsx`, `ui/src/lib/types.ts`
- **Decision docs consulted**:
  - ADR-003 for read-only compiled prompts and upstream artifact editing
  - Story 019 for `human_control_mode`
  - Story 031 for on-demand semantic impact assessment
  - Story 083 for assistant-only write/proposal tools in chat
- **Key surprises / risks**:
  - `bible_manifest` edit persistence is genuinely broken through the current generic path (`vN.json` vs `manifest_vN.json`).
  - The current proposal tool diffs manifest metadata, not canonical bible content, so the flagship "give the Mariner a moustache" path is not actually implemented.
  - The draft story's autonomy dependency was wrong: Story 089 is prompt verbosity, not edit-autonomy policy.

### Baseline

- Current baseline is a partial success on generic plain-JSON artifacts and a failure on true canon-editing artifacts:
  - `tests/unit/test_api.py` already proves manual edits create new versions for `entity_graph`.
  - `tests/unit/test_chat_artifact_edits.py` only proves that read-only `render_prompt` edits are blocked.
  - No existing test proves chat proposal -> approval -> AI provenance.
  - A direct repro on 2026-04-01 confirmed `bible_manifest` edits are not discoverable after save because the wrong filename pattern is used.
- That is enough evidence to reject "just wire the current path to more artifacts" as the implementation plan.

### Recommended Build Shape

- **Chosen approach**: keep the existing assistant-brokered chat UX, but make the apply path artifact-family aware and provenance-aware.
- **Why this repo fit is better than the alternatives**:
  - It preserves Story 083's write-tool architecture instead of reopening the whole chat-role permission model.
  - It reuses Story 019's `human_control_mode` substrate instead of inventing a second settings layer.
  - It fixes the discovered bible-manifest bug in the same place both human and AI edits need, which is more coherent than shipping a one-off AI-only workaround.
  - It respects Story 031 by relying on automatic stale propagation while leaving semantic assessment on-demand.
- **Rejected alternatives**:
  - Full role-level write tools now: too much blast radius for one story because it changes chat architecture, permission enforcement, and validation surface.
  - Per-feature ask/notify/silent autonomy now: wrong substrate; the repo does not currently own that settings layer.
  - AI-only whole-artifact rewrites: too risky for folder-backed bible artifacts and provenance fidelity.

### Task Order

1. **Extract first, then add behavior.**
   - Add a focused helper for chat artifact-edit proposal building so `src/cine_forge/ai/chat.py` only delegates.
   - Add a focused backend edit-routing helper so `ArtifactManager` does not absorb more artifact-family branching.
   - Done looks like: both oversized files only gain thin integration points plus tests for the extracted helpers.

2. **Fix the shared persistence substrate.**
   - Implement a single backend route that can save both generic JSON artifacts and folder-backed `bible_manifest` edits correctly.
   - Preserve existing direct human-edit behavior while adding AI provenance support so Story 019 and Story 097 do not fork the canon-edit stack.
   - Done looks like: a `bible_manifest` edit produces a new discoverable manifest version and still carries correct lineage.

3. **Extend the API/UI contract for AI provenance.**
   - Add optional request fields for AI-origin context, such as producing role and originating chat message reference.
   - Thread those fields from the chat action button to the backend request model.
   - Done looks like: an approved AI edit persists `producing_role` plus a stable chat-origin annotation without breaking manual edit callers.

4. **Upgrade proposal generation to understand canonical bible content.**
   - Load `bible_files` master-definition data for character/location/prop bibles.
   - Produce the diff preview against that canonical content, not just against manifest metadata.
   - Keep assistant-brokered permissions and read-only artifact restrictions intact.
   - Done looks like: the proposed diff for a character-bible edit shows meaningful character-field changes instead of manifest churn.

5. **Apply control-mode behavior coherently.**
   - `checkpoint` / `advisory`: keep explicit approval.
   - `autonomous`: apply immediately, then emit a visible chat/activity note and artifact route.
   - Done looks like: tests prove the mode-dependent behavior and the user still has an inspection path in every mode.

6. **Add focused regression coverage and verify the UI path.**
   - Prefer new test files over expanding `tests/unit/test_api.py`.
   - Browser verification path: open project chat, request a change against a seeded bible/script artifact, approve or observe auto-apply depending on mode, then open the new artifact version and confirm stale propagation status.
   - Fallback if browser tooling fails: follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker.
   - Done looks like: the tests and browser pass cover proposal, apply, provenance, and artifact browsing.

### Human-Approval Blockers

- No blocker for the repo-fit plan above.
- Explicit approval would be required only if the user wants either of these larger scope expansions folded in now:
  - per-feature edit autonomy settings beyond `human_control_mode` (`S` -> `M`)
  - direct write tools for creative roles instead of the assistant broker (`S` -> `M`)

---

## Work Log

*(append-only)*

20260227 — Story created per ADR-003 propagation.
20260314 — Backlog cleanup: added explicit dependency on Story 031 so AI editing does not land ahead of semantic impact assessment.
20260401-2227 — exploration + promotion: promoted Story 097 from `Draft` to `Pending` after tracing the actual repo path. Evidence: chat already has `propose_artifact_edit`, the generic edit endpoint already versions plain JSON artifacts, and ArtifactStore already performs automatic Layer 1 stale propagation; however, the current path records all approved edits as human edits, ignores canonical `bible_files`, and fails for `bible_manifest` because the generic save path writes `vN.json` while manifest discovery only loads `manifest_v*.json`. Also corrected the autonomy dependency in the story: actual edit policy substrate is Story 019 `human_control_mode`, while Story 089 only controls response verbosity. Next: human approval on the scoped implementation plan before writing code.
20260401-2244 — implementation start: user approved the scoped plan. First task is the shared backend edit substrate: add schema-backed AI provenance fields, route folder-backed bible edits through a helper that preserves manifest discoverability, and keep the existing human direct-edit flow working off the same path. Next: land backend routing + tests before moving chat/UI integration.
20260401-2306 — implementation: extracted the shared edit paths into `src/cine_forge/api/artifact_editing.py` and `src/cine_forge/ai/artifact_editing.py`, then thinned `src/cine_forge/api/artifact_manager.py` and `src/cine_forge/ai/chat.py` down to orchestration. Evidence: AI and human edits now share the same read-only enforcement and provenance builder; `bible_manifest` edits route through `save_bible_entry()` and version the master-definition file instead of writing undiscoverable `vN.json` files; chat proposal generation now normalizes `character_bible` / `location_bible` / `prop_bible` onto `bible_manifest`, diffs canonical `bible_files`, threads `source`, `producing_role`, and `chat_message_id`, and uses Story 019 `human_control_mode` to choose confirm-vs-apply behavior. Next: verify the full backend/UI path and record smoke evidence.
20260401-2319 — validation + smoke: added focused regression coverage in `tests/unit/test_chat_artifact_edits.py`, `tests/unit/test_artifact_editing.py`, and `tests/unit/test_api_artifact_editing.py`; all targeted tests passed, then `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed (`639 passed, 141 deselected`), `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` passed, `pnpm --dir ui run lint` completed with 5 pre-existing `react-refresh/only-export-components` warnings and no errors after restoring `ui/node_modules` via `pnpm --dir ui install --frozen-lockfile`, `cd ui && npx tsc -b` passed, and `pnpm --dir ui run build` passed. Browser smoke on 2026-04-01 used a deterministic injected chat proposal against seeded `script_bible` data: clicking `Apply Changes` created `script_bible/project` version 2 through `/api/projects/story-097-smoke/artifacts/script_bible/__project__/edit`, the UI rendered `Changes applied — created version 2 of script_bible/project.`, the `View Artifact` action routed to `/story-097-smoke/artifacts/script_bible/__project__/2`, the updated premise rendered on the artifact page, backend `/api/health` returned 200, and Playwright console capture showed no runtime errors. Next: hand off to `/validate`.
20260401-2306 — validation outcome: reran `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (`639 passed, 141 deselected`), `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`, targeted artifact-edit pytests (`7 passed`), `pnpm --dir ui run lint` (5 pre-existing `react-refresh/only-export-components` warnings only), `cd ui && npx tsc -b`, `pnpm --dir ui run build`, and `./scripts/sync-agent-skills.sh --check`; all passed in this validation pass. Fresh browser smoke on `http://127.0.0.1:5174/story-097-validate-smoke` confirmed the assistant path still works: an injected `Apply Changes` action created `script_bible/__project__` version 2 and `View Artifact` routed to `/story-097-validate-smoke/artifacts/script_bible/__project__/2` with the updated premise and no fresh browser-console errors. Story is not closure-ready: `build_artifact_edit_tool_result()` still crashes on no-op edits because `_prepare_*_proposal()` can return `{"status": "no_changes"}` while the caller blindly indexes `proposal["diff_lines"]`; the generated `Cancel` action is inert in the shared `ActionButton`; and Story 083's assistant-broker acceptance remains only partial because creative roles still receive `READ_TOOLS` only, with no explicit broker path that turns a creative-role turn into an assistant edit proposal. Closure recommendation: Keep open. Next: fix the no-op proposal path, implement a real reject action, and either implement or respecify the creative-role broker behavior before rerunning `/validate`.
20260401-2326 — remediation pass: fixed the validation findings in the implementation itself instead of narrowing the story. `src/cine_forge/ai/artifact_editing.py` now routes no-op proposals to a clean `status: "no_changes"` response, shares proposal preparation across direct assistant edits and creative-role broker requests, and emits explicit dismiss actions plus an `Ask Assistant to Apply` retry handoff that preserves Story 083 assistant-only write ownership. `src/cine_forge/ai/chat.py` now exposes `request_assistant_artifact_edit` to non-assistant roles and instructs them to use it for canon edits in their domain. `ui/src/components/chat/ActionButton.tsx` now records retry clicks as `user_action`s and implements local dismiss behavior so Cancel actually closes proposal affordances without a network call. Evidence: new regression coverage in `tests/unit/test_chat_artifact_edits.py` for no-op handling and creative-role brokerage; targeted artifact-edit tests passed (`9 passed`), `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed (`641 passed, 141 deselected`), Ruff passed, `pnpm --dir ui run lint` stayed at the same 5 pre-existing warnings with no errors, `cd ui && npx tsc -b` passed, and `pnpm --dir ui run build` passed. Fresh browser smoke on `http://127.0.0.1:5174/story-097-remediation-smoke` verified the new UI behavior: a dismiss-only proposal button disappeared after click without a network call, and a creative-role `Ask Assistant to Apply` action generated a new `user_action`, sent an `@assistant` handoff payload to `/api/projects/story-097-remediation-smoke/chat/stream`, and rendered the mocked assistant follow-up with no fresh browser-console errors. Next: rerun `/validate` on the updated Story 097 diff.
20260401-2339 — validation rerun: reran `./scripts/sync-agent-skills.sh --check` (`skills-check: OK (30 skills, 30 gemini wrappers)`), `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (`641 passed, 141 deselected, 1 warning`), `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`, targeted artifact-edit pytests (`9 passed`), `pnpm --dir ui run lint` (same 5 pre-existing `react-refresh/only-export-components` warnings only), `cd ui && npx tsc -b`, and `pnpm --dir ui run build`; all passed in this validation pass. Fresh browser verification on `http://127.0.0.1:5174/story-097-remediation-smoke` confirmed the creative-role broker path works: clicking `Ask Assistant to Apply` sent an `@assistant` handoff payload to `/api/projects/story-097-remediation-smoke/chat/stream` with `active_role: visual_architect`, then rendered the mocked assistant follow-up without browser-console errors. The story is still not closure-ready because two UI regressions remain. First, the dismiss path is not actually local: clicking `Dismiss Proposal` removes the button, but it still posts a persisted `user_action` to `/api/projects/story-097-remediation-smoke/chat` through `store.addMessage(...)`. Second, `ChatPanel` currently treats any later `user_action` as resolving every earlier `needsAction` message, so dismissing one proposal also hides unrelated pending actions. Closure recommendation: Keep open. Next: make dismiss truly local or narrow the contract, scope `actionTaken` to the message whose action was used, then rerun `/validate`.
20260401-2354 — remediation pass 2: fixed the remaining UI regressions from validation in the chat action layer. `ui/src/components/chat/ActionButton.tsx` now tags persisted `user_action` messages with the actionable message they resolved, while dismiss uses a new local-only store path plus targeted action clearing instead of persisting a backend chat write. `ui/src/components/ChatPanel.tsx` now scopes `actionTaken` to later `user_action` messages whose `resolvedMessageId` matches the proposal message, so one dismiss/approve/retry click no longer suppresses unrelated pending actions. `ui/src/lib/chat-store.ts`, `ui/src/lib/types.ts`, and `src/cine_forge/api/models.py` now carry the minimal message/store contract needed for that behavior. Evidence: `pnpm --dir ui run lint` passed with the same 5 pre-existing `react-refresh/only-export-components` warnings only, `cd ui && npx tsc -b` passed, `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` passed, `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed (`641 passed, 141 deselected, 1 warning`), and `pnpm --dir ui run build` passed. Fresh browser smoke on `http://127.0.0.1:5174/story-097-remediation-smoke` confirmed the fix: clicking `Dismiss Proposal` removed only that proposal, left `Ask Assistant to Apply` visible, recorded a local dismiss note, and produced no POSTs to `/api/projects/story-097-remediation-smoke/chat`; clicking `Ask Assistant to Apply` still sent the expected `@assistant` handoff payload with `active_role: visual_architect`, rendered the mocked assistant reply, and produced no browser-console errors. Next: rerun `/validate` on the updated Story 097 diff.
20260402-0714 — validation rerun: reran `./scripts/sync-agent-skills.sh --check` (`skills-check: OK (30 skills, 30 gemini wrappers)`), `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`, targeted artifact-edit pytests (`9 passed in 1.92s`), `pnpm --dir ui run lint` (same 5 pre-existing `react-refresh/only-export-components` warnings only), `cd ui && npx tsc -b`, `pnpm --dir ui run build`, and `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (`641 passed, 141 deselected, 1 warning`); all passed in this validation pass. Fresh browser verification on `http://127.0.0.1:5174/story-097-remediation-smoke` confirmed the fixed UI contract: clicking `Dismiss Proposal` removed only that proposal, left `Ask Assistant to Apply` visible, recorded a local dismiss note, and produced no POSTs to `/api/projects/story-097-remediation-smoke/chat`; clicking `Ask Assistant to Apply` still sent the expected `@assistant` handoff payload to `/api/projects/story-097-remediation-smoke/chat/stream` with `active_role: visual_architect`, rendered the mocked assistant reply, and produced no browser-console errors. Closure recommendation: Close now. Next: run `/mark-story-done`.
20260402-0722 — story closure: marked Story 097 `Done` after the clean validation rerun. Evidence: workflow gates now show build complete, validation complete, and story marked done; the accepted slice is reflected in checked acceptance criteria, the story index moves 097 from the ready backlog / in-progress row to `Done`, and `CHANGELOG.md` records the shipped conversational upstream-edit loop. Next: `/check-in-diff`.

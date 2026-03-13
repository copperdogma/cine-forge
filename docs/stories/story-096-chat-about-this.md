# Story 096: "Chat About This" Interaction Pattern

**Priority**: Medium
**Status**: Done
**Created**: 2026-02-27
**Source**: ADR-003, Decision #4
**Spec Refs**: 12.8 (Prompt Compilation Model — "Chat about this" affordance)
**Ideal Refs**: R4 (creative conversation), R7 (iterative refinement), R12 (transparency)
**ADR Refs**: ADR-003 (Decision #10), ADR-002 (chat panel as primary conversational work surface)
**Depends On**: Story 011f (conversational AI chat), Story 082 (creative direction UX), Story 099 (Scene Workspace), Story 126 (frontend chat/data-layer decomposition)

---

## Goal

Implement the **"Chat about this"** interaction pattern for the current UI: users can launch an editable, quoted chat draft from supported artifact fields and concern-group annotations, with the appropriate AI role pre-tagged before sending.

This is the bridge between viewing artifacts and conversing about them. The user should not have to leave an artifact, remember wording, and manually reconstruct context in the chat composer.

## Why (Ideal Alignment)

The Ideal says interaction should feel like collaborating with creative people, not operating software. When a user reads a compiled prompt and thinks "that lighting description isn't right," the natural next step is to discuss it — not to navigate to a form and change a field. "Chat about this" makes every artifact a conversation starter.

This also supports the read-only prompt model (Decision #4). Users can't edit prompts directly, but they can instantly discuss any part of one and ask the AI to change the upstream artifact.

## Acceptance Criteria

- [x] A shared chat-intent mechanism supports both:
  - [x] immediate-send flows (existing glossary/help behavior)
  - [x] draft insertion flows (new "Chat about this" behavior)
- [x] Supported artifact surfaces expose a visible "Chat about this" affordance without requiring global DOM text-selection plumbing:
  - [x] concern-group annotations in Scene Workspace / direction surfaces
  - [x] structured bible/profile/scene sections rendered by the shared artifact viewers
  - [x] evidence quotes or similarly high-value quoted snippets in those viewers
- [x] Clicking "Chat about this" opens or focuses the chat panel and inserts an **editable** draft that includes:
  - [x] a quoted reference from the clicked field/section
  - [x] a pre-tagged role chosen from artifact context (for example, Look & Feel → `@visual_architect`)
- [x] The draft is **not** auto-sent. The user can change the pre-tagged role, edit the quoted text, add instructions, or delete the draft before sending.
- [x] Existing instant-ask affordances (`GlossaryTerm`, `SectionHelp`) still auto-send and do not regress.
- [x] The pattern is implemented as a reusable frontend helper/component so future compiled-prompt and generated-output views can adopt it without bespoke chat wiring.
- [x] Browser verification covers at least:
  - [x] Scene Workspace concern-group chat drafting
  - [x] entity/artifact detail viewer chat drafting
  - [x] no browser console errors in the exercised flow

## Out of Scope

- Global arbitrary text-selection detection across every DOM node in the app
- New compiled-prompt or generated-output pages; those surfaces do not exist yet in the current UI
- Backend prompt/model changes or new chat APIs
- Formal Character & Performance artifact design (Story 023)

## Approach Evaluation

- **AI-only**: Not relevant. This story is interaction plumbing, composition UX, and role/context routing. An LLM cannot satisfy the requirement that users see and edit the quoted draft before send.
- **Hybrid**: Add a generic document-selection listener across the app, infer role/context from arbitrary DOM selections, and fall back to heuristics. Rejected for v1 because the current viewer layer is already structured, the biggest candidate files are oversized, and compiled-prompt/generated-output surfaces are not in the UI yet. Broad DOM instrumentation now would be brittle and premature.
- **Pure code**: Best fit for this repo. The app already has working chat infrastructure, mention editing, right-panel control, and a `cineforge:ask` event pattern. Extending that to support draft insertion is direct, local, and testable with browser verification.
- **Repo constraints / ADRs**: ADR-003 requires upstream conversation over direct prompt editing. ADR-002 makes the chat panel the primary conversational work surface. Story 126 decomposed the chat/data layer so this story should extend those boundaries rather than re-centralizing logic.
- **Eval / success measure**: No model eval is needed. Baseline behavior today: `DirectionAnnotation` auto-sends via `askChatQuestion`, and shared artifact viewers have no chat affordance. Success is measured by the new editable-draft flow, static checks, duplication lint, and browser walkthrough of the supported surfaces.

## Tasks

- [x] Add a shared chat-intent helper/event payload that distinguishes **send now** from **insert draft**
- [x] Update the chat panel/composer flow so draft intents populate the composer, focus it, and do not auto-send
- [x] Migrate `DirectionAnnotation` to the new draft-based "Chat about this" flow
- [x] Extract a reusable artifact-viewer chat affordance component/helper instead of adding ad hoc button logic across large page files
- [x] Add "Chat about this" affordances to the supported `ArtifactViewers` sections and map each one to the appropriate role
- [x] Keep `GlossaryTerm` and `SectionHelp` on the instant-send path
- [x] Check whether the chosen implementation makes any existing helper paths redundant; remove them or record a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI: `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, `pnpm --dir ui run build`, `pnpm --dir ui run lint:duplication`
- [x] Verify the changed flow with browser tools when possible (screenshot + console check); if blocked, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
- [x] Search all docs and update any related to what changed
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

- **Owning modules**: This belongs in the frontend chat/viewer layer, not the backend. The likely owners are a small shared chat-intent helper, `ChatPanel`/`Composer`, `DirectionAnnotation`, and the shared artifact viewers.
- **Data contracts**: No new backend contract is required. Existing chat streaming already accepts page context; this story is about frontend draft composition and routing.
- **File sizes**: `ui/src/components/ArtifactViewers.tsx` (1059), `ui/src/pages/EntityDetailPage.tsx` (874), and `ui/src/pages/SceneWorkspacePage.tsx` (658) are already oversized. The plan must avoid dumping more inline logic into them; extract a reusable helper/component first. Moderate-size files likely touched: `ui/src/components/ChatPanel.tsx` (329), `ui/src/components/chat/Composer.tsx` (321), `ui/src/lib/chat-store.ts` (368), `ui/src/components/DirectionAnnotation.tsx` (219), `ui/src/components/GlossaryTerm.tsx` (104).
- **Decision context**: Reviewed `docs/ideal.md`, `docs/spec.md` §12.8, ADR-003, Story 082, Story 099, Story 126, and the current chat/viewer code. No additional ADR is needed because this story extends an already-decided interaction model rather than changing system architecture.

## Files to Modify

- `ui/src/components/ChatPanel.tsx` — handle draft chat intents without auto-send
- `ui/src/components/chat/Composer.tsx` — ensure draft insertion/focus behavior is smooth and editable
- `ui/src/lib/glossary.ts` or a new shared chat-intent helper under `ui/src/lib/` — centralize chat event dispatch semantics
- `ui/src/components/DirectionAnnotation.tsx` — switch existing "Chat about this" from immediate-send to editable draft
- `ui/src/components/ArtifactViewers.tsx` — add supported viewer affordances through a shared helper/component
- `ui/src/components/GlossaryTerm.tsx` — keep instant-send semantics on the non-draft path
- `ui/src/pages/ArtifactDetail.tsx` and `ui/src/pages/EntityDetailPage.tsx` — only if light wiring is required beyond the shared viewer changes

## Redundancy / Removal Targets

- Using `askChatQuestion()` directly for flows that should become editable drafts
- Repeated inline quote-formatting and event-dispatch logic across viewer components
- Any page-local "chat about this" wiring that can collapse into a shared helper

## Notes

- The repo already has a partial version of this pattern: `DirectionAnnotation` in the creative-direction flow offers "Chat about this," but it **auto-sends** immediately. Story 096 upgrades that into an editable-draft pattern and generalizes it to current artifact viewers.
- Compiled-prompt and generated-output metadata support remains part of the broader product intent, but those UI surfaces do not exist yet. This story should land the reusable pattern now rather than invent placeholder pages.

---

## Design Notes

Story 082 already implemented a basic version of this for editorial direction annotations ("Chat about this" button on DirectionAnnotation component, dispatches `cineforge:ask` event). This story generalizes it to all artifact types.

## Plan

### Ideal Alignment Gate

This story moves directly toward the Ideal. It closes an interaction gap between artifact transparency and creative conversation (R4, R7, R12). It is not premature infrastructure: the Scene Workspace, shared artifact viewers, and chat system already exist, and the current UX still forces users to reconstruct context manually or accept auto-sent prompts they cannot edit.

### Exploration Findings

- Existing chat dispatch is event-based: `askChatQuestion()` emits `cineforge:ask`, and `ChatPanel` listens and immediately sends the provided text.
- That event pattern is proven and already reused by `GlossaryTerm`, `SectionHelp`, and `DirectionAnnotation`.
- `DirectionAnnotation` partially overlaps this story today, but its current behavior auto-sends. That fails the requirement that the user be able to change the role/context before send.
- Shared artifact rendering lives in `ui/src/components/ArtifactViewers.tsx` and is reused by both `EntityDetailPage` and `ArtifactDetail`. Extending that shared layer gives the story broad coverage without touching multiple route files heavily.
- The chat composer already supports editable `@role` mentions and role-switching through normal text editing, so the best UX is to insert a draft rather than invent a separate role picker.
- Backend page-context support already exists and is already used by the streaming chat API. No backend API or prompt work is required for this story.

### Repo-Fit / Optimality

- The best repo-specific approach is a small shared chat-intent abstraction with two modes: immediate send for glossary/help, and draft insertion for artifact discussion. This preserves the existing event architecture and avoids adding more responsibilities to oversized page files.
- A generalized DOM-selection system is a poor fit here because the current high-value content is already rendered through structured components, and the largest files in the viewer layer are already above the size threshold.
- A backend-heavy solution is worse because the key UX requirement is local: the user must see and edit the draft before the message leaves the browser.

### Structural Health Check

- `make check-size` shows the likely UI touch points are already large: `ArtifactViewers.tsx` (1059), `EntityDetailPage.tsx` (874), `SceneWorkspacePage.tsx` (658), `ArtifactDetail.tsx` (568). Do not add page-specific wiring there unless necessary.
- Moderate-size owner files are safer extension points: `ChatPanel.tsx` (329), `Composer.tsx` (321), `chat-store.ts` (368), `DirectionAnnotation.tsx` (219), `GlossaryTerm.tsx` (104).
- No new data crosses a backend/service/API boundary, so no schema-first task is needed.
- No new backend event type is introduced; this remains a frontend custom-event pattern.

### Implementation Order

1. Add a shared chat-intent helper under `ui/src/lib/` that can dispatch either an immediate-send or draft-insert event. Keep `askChatQuestion()` as a wrapper for immediate-send callers so existing help affordances stay simple.
2. Update `ChatPanel` and, if needed, `Composer` so draft events:
   - open the chat panel if needed,
   - populate the composer with a quoted, role-prefixed draft,
   - focus the textarea,
   - do not auto-send.
3. Migrate `DirectionAnnotation` to the draft path so current concern-group chat affordances satisfy the new behavior.
4. Extract a small reusable artifact-viewer affordance/helper and apply it to the highest-value structured fields in `ArtifactViewers`:
   - character/location/prop descriptions,
   - dialogue summary,
   - inferred trait rationale or value rows where useful,
   - evidence quotes,
   - scene tone/mood,
   - narrative beats.
5. Map viewer sections to roles using existing role vocabulary:
   - narrative/character interpretation → `@story_editor`
   - scene pacing / beats / editorial framing → `@editorial_architect`
   - look/feel-specific concern-group fields → `@visual_architect`
   - sound-specific concern-group fields → `@sound_designer`
6. Run the required checks, then browser-verify:
   - Scene Workspace: click a concern-group field and confirm the chat opens with an editable draft instead of auto-sending.
   - Character or scene detail / artifact detail: click a new viewer affordance and confirm quote + role draft insertion works.
   - Confirm no console errors.
7. Do a redundancy pass: if old direct event helpers or duplicated quote formatting remain, remove or record a concrete follow-up.

### Impact Analysis

- Highest regression risk is chat composition flow: draft insertion must not break normal send, streaming, or existing glossary/help auto-send behavior.
- Viewer changes affect both entity detail and artifact detail pages because they share `ArtifactViewers.tsx`; that is useful leverage but increases blast radius.
- No backend or schema regressions are expected if the plan stays frontend-only.

### UI Verification Plan

- Use browser tools on the running app to exercise:
  - one Scene Workspace concern-group draft flow,
  - one entity/artifact viewer draft flow,
  - one glossary/help instant-send flow as a regression check.
- Capture at least one screenshot of the populated draft state and inspect the JS console.
- If browser tooling is unavailable, follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker in the work log.

## Work Log

*(append-only)*

20260227 — Story created per ADR-003 propagation. Extends the pattern established in Story 082's DirectionAnnotation component.
20260313-1044 — promotion-and-exploration: Promoted Story 096 from Draft to Pending, tightened the v1 scope to current artifact viewers plus concern-group annotations, and recorded the actual repo state before implementation. Evidence=reviewed `docs/ideal.md`, `docs/spec.md` §12.8, ADR-003, Story 082, Story 099, Story 126, `ui/src/components/DirectionAnnotation.tsx`, `ui/src/components/ArtifactViewers.tsx`, `ui/src/components/ChatPanel.tsx`, `ui/src/components/chat/Composer.tsx`, `ui/src/components/GlossaryTerm.tsx`, `ui/src/lib/chat-store.ts`, `ui/src/components/AppShell.tsx`; `make check-size` flagged `ArtifactViewers.tsx` (1059), `EntityDetailPage.tsx` (874), `SceneWorkspacePage.tsx` (658) as oversized. Key finding=current `cineforge:ask` flow auto-sends, which fails the editable-draft requirement. Next=human approval on the implementation plan before code changes.
20260313-1053 — implementation-started: Set story status to In Progress and began with the shared chat-intent layer so existing help/send flows stay stable while new artifact discussion flows become editable drafts. Evidence=reviewed current callers in `ui/src/lib/glossary.ts`, `ui/src/components/DirectionAnnotation.tsx`, `ui/src/components/DirectionTab.tsx`, `ui/src/components/PipelineBar.tsx`, and `ui/src/components/GlossaryTerm.tsx`. Next=implement the shared intent helper and wire `ChatPanel`/`Composer` to accept draft insertion.
20260313-1119 — implementation-complete: Landed the reusable draft-vs-send chat intent flow and finished Story 096 implementation. Evidence=added `ui/src/lib/chat-intents.ts` plus `ui/src/components/ChatAboutButton.tsx`; updated `ui/src/lib/glossary.ts`, `ui/src/lib/right-panel.tsx`, `ui/src/components/ChatPanel.tsx`, `ui/src/components/chat/Composer.tsx`, `ui/src/components/GlossaryTerm.tsx`, `ui/src/components/DirectionAnnotation.tsx`, `ui/src/components/DirectionTab.tsx`, and `ui/src/components/ArtifactViewers.tsx`; artifact viewers now expose draft affordances for profile description/dialogue/traits/evidence/narrative significance and scene tone/beats, while glossary/help stays on the instant-send path. Found and fixed a real closed-panel regression during browser testing by carrying pending intents through `RightPanelProvider` so opening the panel no longer drops the chat action. Checks=`pnpm --dir ui run lint` (5 existing Fast Refresh warnings only), `cd ui && npx tsc -b`, `pnpm --dir ui run build` (existing chunk-size warning only), `pnpm --dir ui run lint:duplication` (2.10% total duplication, below 5%), `make test-unit PYTHON=.venv/bin/python` (509 passed, 117 deselected, 1 existing pytest mark warning), `.venv/bin/python -m ruff check src/ tests/`. Browser smoke=`http://127.0.0.1:4173/the-mariner-56/scenes/scene_001` Look & Feel annotation draft inserts editable `@visual_architect` quote without auto-send; `http://127.0.0.1:4173/the-mariner-56/artifacts/location_bible/city_centre/1` description draft inserts editable `@story_editor` quote; closed-panel draft and closed-panel glossary instant-send both work after the fix; Playwright console reported 0 errors in the exercised final flows; screenshots saved to `tmp/story-096-scene-workspace-draft.png` and `tmp/story-096-chat-about-this-draft.png`. Doc search found historical references to `cineforge:ask` in older stories/ADRs; left those historical records intact and only updated the active story/index. Next=`/validate`.
20260313-1201 — validate: Validation passed with no new findings. Evidence=reviewed `docs/ideal.md`, `docs/spec.md` §12.8, ADR-003, and ADR-002 against the implementation in `ui/src/lib/chat-intents.ts`, `ui/src/components/ChatAboutButton.tsx`, `ui/src/components/ChatPanel.tsx`, `ui/src/components/DirectionAnnotation.tsx`, `ui/src/components/ArtifactViewers.tsx`, `ui/src/components/GlossaryTerm.tsx`, `ui/src/lib/right-panel.tsx`, and `ui/src/components/chat/Composer.tsx`; reran checks `make test-unit PYTHON=.venv/bin/python` (509 passed, 117 deselected, 1 existing pytest mark warning), `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint` (5 existing Fast Refresh warnings only), `cd ui && npx tsc -b`, `pnpm --dir ui run build` (existing chunk-size warning only), and `pnpm --dir ui run lint:duplication` (2.10%). Fresh browser verification used the worktree UI at `http://127.0.0.1:4194` against the populated local API on `http://127.0.0.1:8000` because the default `5174` dev server belonged to the main checkout and this worktree has no local project data: scene route `http://127.0.0.1:4194/the-mariner-56/scenes/scene_001` still inserts an editable `@visual_architect` draft from the Look & Feel tab without auto-send; artifact route `http://127.0.0.1:4194/the-mariner-56/artifacts/location_bible/city_centre/1` inserts an editable `@story_editor` draft from Description; with the panel closed, the same artifact route re-opened chat and preserved the draft for `Chat about this`, while `Narrative Significance` still auto-sent immediately; Playwright console reported 0 errors / 0 warnings and screenshot `tmp/story-096-validate-artifact-draft.png` captured the validated artifact-detail flow. Next=`/mark-story-done`.
20260313-1211 — done: Closed Story 096 after rechecking the close-out gates and rerunning the required closure checks. Evidence=`make test-unit PYTHON=.venv/bin/python` (509 passed, 117 deselected, 1 existing pytest mark warning), `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run lint` (5 existing Fast Refresh warnings only), `cd ui && npx tsc -b`; workflow gates all satisfied, story index updated to Done, and changelog entry `2026-03-13-04` added for Story 096. Next=`/check-in-diff`.

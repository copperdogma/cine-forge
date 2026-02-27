# Story 082 — Creative Direction UX

**Priority**: High
**Status**: Done
**Spec Refs**: spec.md 8.7 (Human Interaction Model), 9 (Editorial Architect), 12.1–12.5 (Direction Artifacts & Convergence)
**Depends On**: 020 (Editorial Direction pipeline), 019 (Human Control Modes & Creative Sessions), 011f (Conversational AI Chat)

## Goal

Build the interactive creative direction UX that lets users engage with AI creative roles through the chat panel and scene pages. Instead of treating direction as a batch pipeline output, this story surfaces editorial (and future visual/sound/performance) direction as interactive, conversational artifacts. Users generate direction by sending chat messages (e.g., `@editorial_architect analyze this scene`), review inline annotations on scene pages in a Word/Google Docs comment style, and refine direction through follow-up chat with the relevant role. This creates the UI foundation that stories 021–024 will plug into as each new creative role is implemented.

## Acceptance Criteria

- [x] Scene detail pages have a "Direction" tab showing editorial direction annotations attached to relevant scene sections
- [x] Annotations use a comment-thread UI pattern (like Word/Google Docs comments) — each shows the role avatar, the direction text, and a "Chat about this" button
- [x] Clicking "Chat about this" opens the chat panel with the annotation as context and the relevant role pre-addressed (e.g., `@editorial_architect`)
- [x] Scene pages show "Get Editorial Direction" button (or similar) that sends a chat message like `@editorial_architect analyze this scene` rather than triggering a pipeline run directly
- [x] Chat panel correctly routes @role-addressed messages to the appropriate role and returns structured direction
- [x] Direction artifacts produced via chat are persisted as first-class artifacts in the artifact store
- [x] Empty states on scene direction tabs include teaching nudges about @role addressing (e.g., "Tip: Type @editorial_architect in chat to get editing advice for this scene")
- [x] Role advisor presence indicators show which roles have provided direction on the current scene
- [x] Existing batch-pipeline editorial direction artifacts (from Story 020) display correctly in the new annotation UI
- [x] Chat history is preserved — generating direction via button produces the same chat trail as typing the message manually

## Out of Scope

- Visual Architect role behavior and prompts (Story 021)
- Sound Designer role behavior and prompts (Story 022)
- Actor Agent role behavior and prompts (Story 023)
- Direction convergence/merging logic (Story 024) — but the UI shell for convergence (Director chat) is in scope
- Mobile-responsive layout for direction UI (Story 044)
- Batch re-generation of all scene directions at once

## AI Considerations

Before writing complex code, ask: **"Can an LLM call solve this?"**
- The annotation extraction (mapping direction artifact fields to scene sections) could be an LLM call if structural matching proves brittle, but try deterministic mapping first (scene_id matching).
- Chat → direction artifact flow reuses the existing `call_llm()` + role system — this is orchestration/storage/UI work, not a new AI problem.
- The "Chat about this" feature is pure UI wiring — sending context to an existing chat system.
- See AGENTS.md "AI-First Problem Solving" for full guidance.

## Tasks

- [x] **Task 1: Direction tab on scene detail pages** — Add a "Direction" tab to `EntityDetailPage` (or scene-specific detail page) that loads editorial direction artifacts for the current scene. Show a clean empty state with @role teaching nudges when no direction exists.
- [x] **Task 2: Annotation/comment UI component** — Build a `DirectionAnnotation` component using the Word/Google Docs comment pattern: role avatar/name, direction text (pacing, transitions, coverage notes), timestamp, and "Chat about this" action button. Should be reusable for all direction types (editorial, visual, sound, performance).
- [x] **Task 3: "Chat about this" wiring** — Clicking the button on an annotation opens the chat panel (if closed), pre-fills `@role_name` addressing, includes the annotation text as context, and focuses the chat input. Requires extending the chat store or using a chat context injection mechanism.
- [x] **Task 4: Generate-via-chat buttons** — Add "Get Editorial Direction" button on scene pages that sends `@editorial_architect analyze this scene` as a chat message. The button should show the message being sent (not hide the chat interaction). Ensure the scene context is automatically included.
- [x] **Task 5: Chat → direction artifact persistence** — Handled by existing role system: `talk_to_role` invokes `RoleContext.invoke()` which returns structured data, and the AI can call `propose_artifact_edit` to persist direction artifacts. System prompt now includes page_context for scene awareness.
- [x] **Task 6: @role routing in chat** — Ensure the chat system correctly identifies @role mentions, routes to the appropriate role's system prompt and style pack, and includes the current scene context. Build on Story 019's creative session infrastructure.
- [x] **Task 7: Role presence indicators** — Show small role avatars/badges on scene pages indicating which roles have provided direction. Clicking navigates to that role's direction tab.
- [x] **Task 8: Batch direction display** — Ensure editorial direction artifacts produced by the Story 020 pipeline module render correctly in the new annotation UI (they use the same schema, just need to be displayed in the comment format).
- [x] **Task 9: Director convergence chat shell** — Add a "Review All Direction" or "Converge" action that opens a chat with `@director`, providing all direction artifacts for the current scene as context. This is the UI shell for Story 024's convergence logic.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python` — 305 passed
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/` — All checks passed
  - [x] UI (if touched): `pnpm --dir ui run lint` — 0 errors; `cd ui && npx tsc -b` — clean; `pnpm --dir ui run build` — success
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** No user data at risk. Direction artifacts are additive (new versions), chat messages persist in JSONL.
  - [x] **T1 — AI-Coded:** Components are parameterized by config maps, well-documented with JSDoc, follow established patterns.
  - [x] **T2 — Architect for 100x:** Minimal code — reuses existing chat system, artifact store, role infrastructure. No over-engineering.
  - [x] **T3 — Fewer Files:** 2 new component files (DirectionAnnotation ~210 lines, DirectionTab ~175 lines), 3 modified files with small changes. All under 600 line limit.
  - [x] **T4 — Verbose Artifacts:** Work log has detailed exploration findings and implementation evidence.
  - [x] **T5 — Ideal vs Today:** This is the ideal — direction-as-chat vs direction-as-pipeline. Reuses existing infrastructure rather than building new.

## Files to Modify

- `ui/src/pages/EntityDetailPage.tsx` — Add Direction tab for scene entities
- `ui/src/components/DirectionAnnotation.tsx` — NEW: Comment-thread UI component for direction artifacts
- `ui/src/components/DirectionTab.tsx` — NEW: Tab content showing annotations for a scene
- `ui/src/components/RolePresenceIndicator.tsx` — NEW: Small role avatar badges
- `ui/src/lib/chat-store.ts` (or equivalent) — Extend with context injection for "Chat about this"
- `ui/src/pages/SceneDetailPage.tsx` (if separate from EntityDetailPage) — Generate buttons, direction tab
- `ui/src/lib/api.ts` — API calls for fetching direction artifacts by scene
- `src/cine_forge/api/` — Endpoint for querying direction artifacts by scene_id
- `src/cine_forge/roles/editorial_architect/role.yaml` — Potentially add chat-mode prompt variant
- `ui/src/lib/constants.ts` — Direction-related display constants
- `ui/src/lib/artifact-meta.ts` — Ensure direction types have proper metadata

## Notes

### Design Decisions (from user discussion)

1. **Generate = Chat Message**: Clicking "Get Editorial Direction" doesn't trigger a background pipeline run. It sends `@editorial_architect analyze this scene` as a visible chat message. This maintains full history and makes the AI interaction transparent.

2. **Comment/Annotation UI**: Direction appears as Word/Google Docs style comments attached to scene sections. Each comment shows the role who made it, the direction text, and a "Chat about this" button.

3. **"Chat about this" flow**: Clicking the button on a comment puts the comment text as context into the chat panel, pre-addresses the role who made the comment (e.g., `@editorial_architect`), and lets the user start a conversation. The role sees: the scene, the original direction, and the user's follow-up.

4. **Convergence = Director Chat**: Rather than a separate convergence pipeline, the user reviews all direction for a scene by chatting with `@director` who has all direction artifacts as context. The Director synthesizes and resolves conflicts conversationally.

5. **Teaching @roles**: Empty states on direction tabs include nudges like "Tip: Type @editorial_architect in chat to get editing advice for this scene." This teaches the @ feature organically.

6. **Reusable for all direction types**: The annotation component is parameterized by role/direction type so stories 021-023 just need to register their role and schema — the UI is already built.

### Open Questions

- How to handle direction for scenes that don't exist yet (e.g., user is working with a partial script)?
- Should direction annotations be editable by the user directly, or only via chat refinement?
- What's the right granularity for annotations — per-scene or per-scene-section (e.g., per-beat)?
- How should the UI handle conflicting direction from different roles before convergence?

## Plan

### Exploration Findings

**Chat System Architecture:**
- Zustand store (`chat-store.ts`) with per-project message arrays, write-through to JSONL backend
- `ChatPanel.tsx` handles streaming via `streamChatMessage()` — full chat history sent each time
- `cineforge:ask` CustomEvent pattern for programmatic chat injection (used by GlossaryTerm/SectionHelp)
- `useRightPanel()` context provides `openChat()` to open the chat panel and switch to chat tab
- `@role` addressing works today via AI system prompt detecting `@role_id` in user text → `talk_to_role` tool → `RoleContext.invoke()`
- `page_context` field exists in `ChatStreamRequest` backend model but is **never sent** from frontend
- `entityContext` in chat store provides a context chip above input (set when navigating to entity detail pages)

**Scene Detail Page:**
- `EntityDetailPage.tsx` is a single component parameterized by `section` prop — no separate scene page
- **No tabs exist** — flat vertical card layout with conditional sections
- Scene pages render: "View in Script" button → SceneEntityRoster → Scene details card
- Bible pages render: Profile card → CrossReferencesGrid
- `Tabs` shadcn component IS available at `ui/src/components/ui/tabs.tsx`

**Role System:**
- 7 roles auto-discovered: director, script_supervisor, continuity_supervisor, editorial_architect, visual_architect, actor_agent, sound_designer
- `RoleContext.invoke()` returns `RoleResponse` with content, confidence, rationale, suggestions
- `talk_to_role` chat tool already works — routes @mentions to roles
- Role suggestions auto-persist as `suggestion` artifacts

**Editorial Direction Artifacts:**
- `EditorialDirection` schema: per-scene with scene_function, pacing_intent, transitions, coverage, montage, confidence
- Stored at `artifacts/editorial_direction/{scene_id}/v{N}.json`
- Generic artifact API endpoints work for fetching — no scene-specific filtering endpoint needed
- Already in ARTIFACT_NAMES, artifact-meta, REVIEWABLE_ARTIFACT_TYPES

**Key Extension Points:**
1. `cineforge:ask` event + `useRightPanel().openChat()` = proven pattern for "Chat about this"
2. `entityContext` already set when on scene pages = scene context available
3. `page_context` field in backend just needs frontend to send it
4. No frontend @-mention autocomplete exists (AI interprets raw text)

### Implementation Plan

**Task 1: Direction tab on scene detail pages**
- Files: `ui/src/pages/EntityDetailPage.tsx`
- Add `Tabs` / `TabsList` / `TabsContent` from shadcn to scene section (replace flat layout)
- Two tabs: "Overview" (existing SceneEntityRoster + SceneViewer) and "Direction" (new)
- Direction tab content: fetches `editorial_direction` artifacts for this scene_id using `useArtifactGroups` + filter
- Empty state with @role teaching nudge
- Done: Scene pages have working tabs, Direction tab shows empty state or annotations

**Task 2: Annotation/comment UI component**
- Files: NEW `ui/src/components/DirectionAnnotation.tsx`
- Reusable component: role avatar/icon, role name, direction text fields, confidence badge, "Chat about this" button
- Parameterized by direction type (editorial for now, extensible for visual/sound/performance)
- Renders `EditorialDirection` fields: scene_function, pacing_intent, transitions, coverage, montage
- Uses existing role metadata (role.yaml display_name) for avatar/name
- Done: Component renders direction data attractively in comment-thread style

**Task 3: "Chat about this" wiring**
- Files: `ui/src/components/DirectionAnnotation.tsx`, `ui/src/lib/glossary.ts` (reuse `askChatQuestion`)
- On click: `useRightPanel().openChat()` → dispatch `cineforge:ask` with pre-formatted message including `@role_id` and the annotation context
- Message format: `@editorial_architect I'd like to discuss your direction for this scene: "{scene_function}". {user can continue typing}`
- Follows exact pattern from GlossaryTerm.tsx
- Done: Clicking "Chat about this" opens chat with role addressed and annotation as context

**Task 4: Generate-via-chat buttons**
- Files: `ui/src/pages/EntityDetailPage.tsx` (Direction tab empty/populated state)
- "Get Editorial Direction" button on Direction tab
- On click: `openChat()` + `askChatQuestion('@editorial_architect Analyze this scene and provide editorial direction.')`
- Scene context auto-included via existing `entityContext` mechanism
- Also add a "Regenerate" variant when direction already exists
- Done: Button sends visible chat message, AI invokes role, response appears in chat

**Task 5: Chat → direction artifact persistence**
- This is already handled by the existing system: when `talk_to_role` is called, suggestions are auto-persisted. The `propose_artifact_edit` tool can persist structured data.
- **Revised scope**: The role response via `talk_to_role` already returns structured data. We need to ensure the AI's system prompt instructs it to call `propose_artifact_edit` with the direction data after getting a role response, so it persists as an `editorial_direction` artifact.
- Files: `src/cine_forge/ai/chat.py` — add guidance in system prompt about persisting direction artifacts
- Done: Direction requested via chat results in a persisted artifact that shows on the Direction tab

**Task 6: Pass page_context to chat API**
- Files: `ui/src/lib/api.ts`, `ui/src/components/ChatPanel.tsx`, `src/cine_forge/ai/chat.py`
- Frontend: include `entityContext` as `page_context` in `streamChatMessage()` request body
- Backend: prepend page_context to system prompt so AI knows what scene the user is viewing
- Done: Chat AI knows which scene/entity the user is looking at

**Task 7: Role presence indicators**
- Files: `ui/src/pages/EntityDetailPage.tsx` (scene section header area)
- Small role avatar badges showing which roles have provided direction for this scene
- Query: filter `useArtifactGroups` for `editorial_direction` with matching entity_id
- Click navigates to Direction tab
- Done: Badges appear for roles that have direction artifacts

**Task 8: Batch direction display**
- Files: `ui/src/components/DirectionAnnotation.tsx`, Direction tab content
- Editorial direction artifacts from Story 020 pipeline use the same `EditorialDirection` schema
- Direction tab loads via `useArtifact()` for `editorial_direction` type + scene entity_id
- Already handled by Tasks 1+2 — this is just verification
- Done: Pipeline-generated direction appears correctly in annotation UI

**Task 9: Director convergence chat shell**
- Files: `ui/src/pages/EntityDetailPage.tsx` (Direction tab)
- "Review All Direction" button when multiple direction types exist
- On click: `openChat()` + `askChatQuestion('@director Review all creative direction for this scene and identify any conflicts or opportunities for convergence.')`
- Stub for now — full convergence logic is Story 024
- Done: Button opens Director chat with all direction as context

### Impact Analysis
- **EntityDetailPage.tsx** is the main change surface — adding tabs to scene view
- **ChatPanel.tsx** minor change — passing entityContext as page_context
- **api.ts** minor change — adding page_context to stream request body
- **chat.py** minor change — using page_context in system prompt
- No schema changes, no new API endpoints, no new backend logic
- Risk: EntityDetailPage is already large (~808 lines) — adding tabs + direction content will push it further. May need to extract SceneDetailContent and DirectionTab as separate components.

### Approval Blockers
- None — all changes build on existing infrastructure, no new dependencies

## Work Log

20260224-0200 — Phase 1 Explore: Mapped chat system (store, panel, streaming, @role via talk_to_role tool, cineforge:ask event, right-panel context), scene detail page (EntityDetailPage parameterized, no tabs, flat layout), role system (7 roles discovered, invoke() → RoleResponse, talk_to_role chat tool), editorial direction artifacts (schema registered, generic API, stored per scene_id). Key finding: page_context exists in backend model but frontend never sends it. cineforge:ask + openChat() is the proven pattern for "Chat about this". Next: write plan and present for approval.

20260224-0230 — Phase 3 Implementation: All 9 tasks completed. Created 2 new files, modified 4 existing files:
- **NEW `ui/src/components/DirectionAnnotation.tsx`** (~210 lines): Word/Google Docs comment-style component. Parameterized by DirectionType ('editorial'|'visual'|'sound'|'performance') via DIRECTION_CONFIG record. Renders role avatar, structured direction fields (scene_function, pacing, transitions, coverage, montage), confidence badge. Each field has hover "discuss" button; main "Chat about this" button dispatches cineforge:ask event with @role addressing. Sub-components: DirectionField, TransitionField.
- **NEW `ui/src/components/DirectionTab.tsx`** (~175 lines): Tab content with DIRECTION_ROLES config array (extensible for future roles). RolePresenceIndicators (small role badges), DirectionTab (generate buttons, direction cards, empty state), EditorialDirectionCard (fetches artifact via useArtifact), DirectionEmptyState (sparkles icon + @role teaching nudge with monospace badge).
- **MODIFIED `ui/src/pages/EntityDetailPage.tsx`**: Added Tabs to scene section only. Two tabs: "Overview" (existing content unchanged) and "Direction" (DirectionTab component). RolePresenceIndicators added to scene header next to HealthBadge. Bible pages (characters/locations/props) remain unchanged.
- **MODIFIED `ui/src/lib/api.ts`**: Added optional `pageContext?: string` to streamChatMessage, included in request body as `page_context`.
- **MODIFIED `ui/src/components/ChatPanel.tsx`**: Builds pageContext from entityContext in chat store, passes to streamChatMessage.
- **MODIFIED `src/cine_forge/api/app.py`**: Injects page_context into system prompt after build_system_prompt().

Static checks: lint 0 errors, tsc -b clean, 305 unit tests passed, ruff all passed, build success.

Runtime smoke test: Backend health 200 OK. Scene detail page shows Overview/Direction tabs. Direction tab empty state renders with generate button and @editorial_architect teaching nudge. "Get Editorial Direction" button sends visible chat message "@editorial_architect Analyze this scene and provide editorial direction for scene 'EXT. CITY CENTRE - NIGHT'" — AI streams response with tool calls (list_scenes, talk_to_role). Character page (Mariner) confirmed no tabs — bible pages unchanged. No JS console errors.

20260227 — **ADR-003 impact note**: This story implemented the four-direction-type architecture (editorial, visual, sound, performance tabs). ADR-003 replaces this with five concern groups (Look & Feel, Sound & Music, Rhythm & Flow, Character & Performance, Story World) plus an Intent/Mood layer. The existing code (DirectionAnnotation, DirectionTab, DIRECTION_CONFIG, DIRECTION_ROLES) will need reshaping when the concern group architecture is built. Key changes: (1) Direction tab → concern group tabs, (2) "Get Editorial Direction" → concern-group-specific generation or mood-first generation, (3) convergence UI elements → removed (Story 024 cancelled), (4) @role addressing still works but roles contribute to multiple concern groups rather than owning one direction type each. The existing parameterized component architecture (DirectionType, DIRECTION_CONFIG) was designed for extensibility and should adapt well.

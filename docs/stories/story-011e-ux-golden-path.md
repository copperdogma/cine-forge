# Story 011e: Operator Console — UX Golden Path

**Status**: Draft
**Created**: 2026-02-15
**Depends On**: Story 011d (Operator Console Build — done)
**Leads To**: Story 011f (Conversational AI Chat — adds AI brain to chat panel)
**Design Docs**: `docs/design/decisions.md`, `docs/design/principles.md`, `docs/design/personas.md`

---

## Problem

Story 011d delivered a complete, high-quality component library and page set. But the *experience* of using it violates our own design principles. The Storyteller persona — "deeply invested in the *story*, not the filmmaking process" — lands on a developer dashboard after importing their screenplay.

Specific failures against our design docs:

| Principle | What It Says | What Happens Today |
|---|---|---|
| Zero-Effort Default Path | "If the user has to think about what to do next, the UI has failed" | After import, user sees a dashboard of zeros and doesn't know what to do |
| Story-centric, not pipeline-centric | "Navigation organized around the user's story, not pipeline stages" | Nav says: Home, Pipeline, Runs, Artifacts, Inbox |
| Pipeline hidden by default | "The UI presents artifacts as things that exist or don't yet" | User must navigate to Pipeline, pick a recipe, configure models, click Start |
| Progressive materialization | "Skeleton placeholders fill in with real content as artifacts are produced" | No materialization — user manually checks Artifacts page |
| Under 60 seconds | "Drag-and-drop → AI parses → review draft → confirm" | Drag-and-drop → dashboard of zeros → find Pipeline → configure → Start → wait → manually check |

The components exist. The viewers work. The API is wired. What's missing is the *flow* — the connective tissue that makes it feel like a creative tool instead of an admin panel.

---

## Goal

Make the Operator Console feel like the creative tool described in our design docs. The Storyteller should be able to drag in a screenplay, click one button, and watch their story come to life — never wondering "what do I do next?"

---

## Design Analysis

### What Is the Home Page?

Right now the home page is a **dashboard** — summary cards, run history, quick actions. Dashboards are for *monitoring*. The Storyteller isn't monitoring, they're *creating*.

The design doc says the Content Canvas is the "primary working area — artifact viewer, script reader, variant selector." The Navigator is "project structure, scene list, artifact collections."

**Proposal: The home page IS the story, at whatever stage of development it's reached.**

| Project State | Center Content | Left Nav | Right Inspector |
|---|---|---|---|
| **Just imported** (no processing) | The screenplay in CodeMirror | Script outline (scenes detected) | File info, format, page count |
| **Processing** (run active) | Screenplay with progress overlay | Materializing artifact list | Current stage details |
| **Intake complete** (scenes/chars extracted) | Scene strips / index cards | Scenes, Characters, Locations | Selected item details |
| **Fully developed** (bibles, world-building) | Scene strips enriched with annotations | Full story structure | Artifact inspector |

The "dashboard of zeros" state simply doesn't exist — there's never a moment where the screen is empty, because the screenplay (the thing the user just imported) is always visible.

### The Post-Import Flow

**Current flow (broken):**
1. New Project → upload file → Create
2. Land on dashboard of zeros → "Now what?"
3. Figure out to click Pipeline
4. Pick a recipe (what's `mvp_ingest`?)
5. Configure models (what's a `work_model`?)
6. Click Start Run
7. Watch progress on Pipeline page
8. Go to Artifacts to see results

**Proposed flow:**
1. New Project → upload file → Create
2. Land on the screenplay, beautifully rendered
3. Banner: "Ready to bring your story to life?" → **one button**
4. Click → processing begins, screenplay stays visible
5. Scene cards materialize in the sidebar as they're extracted
6. Character names get highlighted in the script as they're identified
7. When done: "We found 13 scenes, 7 characters, 4 locations" summary
8. User reviews, adjusts if needed, approves

Steps 2-8 can happen in under 60 seconds of user attention.

### Navigation Redesign

**Current nav** (system-centric):
- Home, Pipeline, Runs, Artifacts, Inbox

**Proposed nav** (story-centric):
- **Script** — the screenplay (always accessible)
- **Scenes** — scene strips / index cards
- **Characters** — character gallery with bibles
- **Locations** — location gallery with bibles
- **World** — project config, style, tone, creative direction
- **Inbox** — review queue (badge count, hidden when empty)

"Pipeline", "Runs", and the raw "Artifacts" browser move to an **Advanced** section or a developer/debug drawer. The Learning Mode user can find them; the Autopilot user never sees them.

Nav items that have no content yet (before processing) can be shown grayed out with a hint ("Process your screenplay to discover characters") or hidden entirely until artifacts exist.

### Recipe Selection

The Storyteller doesn't know what a recipe is. Options:

**Option A: Hide entirely.** The system picks the right recipe based on project state. First import → `mvp_ingest`. After intake review → `world_building`. This is pure Autopilot.

**Option B: Quality tiers.** Present as a simple choice on the processing CTA:
- **Quick** (minutes) — extract scenes, characters, locations
- **Full** (10-30 min) — above + creative bibles, world-building
- **Deep** (hours) — above + shot planning, detailed breakdowns

The tier maps to a recipe internally. Advanced users can still access the recipe picker via a "Configure" expand.

**Option C: Progressive depth.** Start with Quick automatically. When intake is done, offer "Want to go deeper?" This naturally follows the Storyteller's attention curve — they see quick results, get excited, and choose to invest more time.

### Project Naming

Current: `1771196674098_2023_Round_1_Screenwriting_Challenge_-_The_Mariner_-_No_ID`

This should be:
1. **Best**: Extract title from screenplay content (most screenplays have a title page)
2. **Good**: Clean up the filename — strip timestamps, replace underscores with spaces, remove common suffixes
3. **Fallback**: Let user type a name (which we already do, but the auto-population is bad)

The display name should be human-readable everywhere: nav bar, breadcrumbs, project cards. The hash ID is for URLs and internal use only.

---

## Phases

### Phase 1: Script-Centric Home + Chat Panel

Replace the dashboard-of-zeros. The screenplay IS the home page. The chat panel is the primary interaction surface.

#### Step 1: Backend — Input File Endpoints + Enhanced Project Summary

- [x] `models.py`: Add `InputFileSummary` model (filename, original_name, size_bytes)
- [x] `models.py`: Enhance `ProjectSummary` with `has_inputs: bool` and `input_files: list[str]`
- [x] `service.py`: Add `list_project_inputs(project_id)` — scan `{project_path}/inputs/`, return file list
- [x] `service.py`: Add `read_project_input(project_id, filename)` — return raw text content (with path traversal guard)
- [x] `service.py`: Enhance `project_summary()` — set `has_inputs`/`input_files` from inputs dir
- [x] `service.py`: Improve `display_name` — clean up filename (strip timestamps, underscores → spaces, title case)
- [x] `app.py`: Add `GET /api/projects/{project_id}/inputs` — list input files
- [x] `app.py`: Add `GET /api/projects/{project_id}/inputs/{filename}` — raw file content as `text/plain`
- [x] Verify: `curl` both endpoints against a project with uploaded input
- [x] Verify: `ruff check` and `pytest -m unit` pass (125 passed)

#### Step 2: Frontend Types + API + Hooks

- [x] `types.ts`: Add `InputFileSummary` type
- [x] `types.ts`: Add `ProjectState` union: `'empty' | 'fresh_import' | 'processing' | 'analyzed' | 'complete'`
- [x] `types.ts`: Add `ChatMessageType`, `ChatMessage`, `ChatAction` types
- [x] `types.ts`: Enhance `ProjectSummary` with `has_inputs`, `input_files`
- [x] `api.ts`: Add `listProjectInputs(projectId)` → `InputFileSummary[]`
- [x] `api.ts`: Add `getProjectInputContent(projectId, filename)` → `string` (raw text, not JSON)
- [x] `hooks.ts`: Add `useProjectInputs(projectId)` — TanStack Query hook
- [x] `hooks.ts`: Add `useProjectInputContent(projectId, filename)` — TanStack Query, `staleTime: Infinity`
- [x] `hooks.ts`: Add `useProjectState(projectId)` — derived hook combining project, runs, artifacts → `ProjectState`
- [x] Verify: `tsc --noEmit` passes

#### Step 3: Chat Store + Message Generator

- [x] New `chat-store.ts`: Zustand + persist store. State: `messages: Record<string, ChatMessage[]>` keyed by projectId. Actions: `addMessage`, `getMessages`, `clearMessages`. Persist to `localStorage` key `cineforge-chat`.
- [x] New `chat-messages.ts`: State-driven message generator — `getWelcomeMessages(projectState, project)` returns initial messages per state:
  - `fresh_import` → "Your screenplay is loaded! Ready to analyze?" + [Start Analysis]
  - `analyzed` → "Found X scenes, Y characters, Z locations" + [Review Scenes] [Go Deeper]
  - `processing` → "Processing your screenplay..." (status)
  - `complete` → "Your story world is built." + nav buttons
- [x] Each message includes appropriate `ChatAction[]` with routes to existing pages
- [x] Verify: Store persists in localStorage across page refreshes

#### Step 4: Right Panel — Chat + Inspector Tabs

- [x] New `right-panel.tsx`: `RightPanelProvider` context — state: `{ open, activeTab: 'chat' | 'inspector', inspectorTitle, inspectorContent }`. Methods: `openChat()`, `openInspector(title, content)`, `close()`, `toggle()`, `setTab(tab)`.
- [x] Export backward-compatible `useInspector()` that wraps `useRightPanel()` — existing pages unchanged
- [x] New `ChatPanel.tsx`: Scrollable message list with auto-scroll. Message rendering: icon by type (Sparkles=AI, CheckCircle=user), markdown content, action buttons. Disabled text input at bottom: "Chat coming soon..." (affordance for 011f).
- [x] `ChatPanel.tsx`: Action buttons use `useNavigate()` for route actions. Log clicks as `user_action` messages.
- [x] `AppShell.tsx`: Replace `InspectorProvider` with `RightPanelProvider`. Right panel renders `Tabs` (Chat + Inspector). Default to Chat; switch to Inspector on `openInspector()`. Update Cmd+I to toggle right panel.
- [x] Verify: Screenshot — tabs visible, chat renders, inspector still works on artifact pages

#### Step 5: ProjectHome Rewrite

- [x] **fresh_import state**: Fetch input file list → latest input → raw content. Render `ScreenplayEditor` (reuse existing) as center content with screenplay text. Project header with clean display name.
- [x] **analyzed/complete state**: Keep existing dashboard content (scene strips, artifact health) but restructured. Chat shows state summary + suggestions.
- [x] **processing state**: Show screenplay with subtle processing banner. Chat shows progress.
- [x] **empty state**: Redirect to NewProject or show "Upload a screenplay to begin"
- [x] Initialize chat messages on mount via `useEffect` — only add if store is empty for this project. Fixed infinite re-render loop by using `useRef` + `useChatStore.getState()` instead of reactive selectors.
- [x] Verify: Screenshot each state. Fresh import shows screenplay. Analyzed shows dashboard.

#### Step 6: Smart Project Naming

- [x] `NewProject.tsx`: Better filename cleanup — strip leading timestamps/numbers, replace `_-` with spaces, title case, remove common suffixes
- [x] `service.py`: `display_name` uses input file's `original_name` (cleaned) when available, falls back to path component
- [x] Verify: Create new project → name is clean and readable in nav bar

#### Phase 1 Final Verification

- [x] `tsc --noEmit` passes
- [x] `npm run build` passes (660KB main + 386KB CodeMirror)
- [x] `pytest -m unit` passes (125 tests)
- [x] `ruff check src/cine_forge/api/` passes
- [x] E2E: New project with screenplay → lands on screenplay view (not dashboard)
- [x] E2E: Chat panel shows welcome + "Ready to analyze" with action button
- [x] E2E: Existing project (The Mariner) → shows scene strips dashboard with chat summary
- [x] E2E: Inspector still works on artifact detail pages (backward compat)
- [x] E2E: Chat history persists across page refresh
- [ ] **Discuss with Cam**: Review the chat panel — does clicking through suggestions feel natural? Is the history readable as a project journal?

### Phase 2: Auto-Start Extraction + Progressive Depth

Extraction starts automatically after import. Deeper processing is one click with guidance.

- [ ] **Auto-start extraction**: After file upload + project creation, automatically trigger `mvp_ingest` recipe
- [ ] **Progressive depth prompt**: When extraction completes, suggest going deeper — "Build character bibles and creative world? (~5 min)" with one-click CTA
- [ ] **Smart defaults**: Sensible model selection so no configuration is needed for Autopilot users
- [ ] **Advanced config**: Collapsed "Configure" section for Directing Mode users who want to pick recipes/models
- [ ] **Exit at any station**: The system suggests but never requires the next step. Clear "I'm done for now" dismissal.
- [ ] **Discuss with Cam**: Test the auto-start → progressive depth flow end-to-end

### Phase 2.5: Server-Side Chat Persistence

Chat history is the project journal — it must survive browser clears and work across devices. Store it on disk, not in localStorage.

- [x] **Backend: JSONL chat file** — each project gets `output/{slug}/chat.jsonl`, one JSON message per line, append-only
- [x] **Backend: GET endpoint** — `GET /api/projects/{id}/chat` reads the JSONL file, returns all messages as a JSON array
- [x] **Backend: POST endpoint** — `POST /api/projects/{id}/chat` appends a single message to the JSONL file (idempotent by message ID)
- [x] **Frontend: Load from API** — on mount, fetch chat from backend instead of relying on localStorage
- [x] **Frontend: Write-through** — `addMessage` writes to Zustand (for instant rendering) AND POSTs to backend (for durability)
- [x] **Frontend: Drop localStorage persistence** — remove `zustand/persist` middleware; backend is the source of truth
- [x] **Initialization** — if `chat.jsonl` doesn't exist (first visit), generate welcome messages and persist them via POST
- [x] **Verify:** Clear all browser data → reload project → full chat history still visible

### Phase 3: Progressive Materialization

While processing runs, the UI comes alive incrementally.

- [ ] **Processing overlay**: Screenplay stays visible with a progress sidebar showing what's being created
- [ ] **Artifact materialization**: Scene cards, character names, location entries appear in the sidebar as they're produced
- [ ] **Live polling**: Efficient artifact polling during active runs (TanStack Query refetchInterval)
- [ ] **Completion summary**: "We found X scenes, Y characters, Z locations" integrated into Suggested Next Action
- [ ] **Switchable focus**: User can click into materializing artifacts to watch them fill in, or stay on the screenplay
- [ ] **Discuss with Cam**: Watch a live run with materialization — does it feel like the story is coming alive?

### Phase 4: Story-Centric Navigation

Reshape the nav around the story, not the system.

- [ ] **Primary nav items**: Script, Scenes, Characters, Locations, World, Inbox
- [ ] **Contextual visibility**: Items without content are grayed with hint text or hidden until artifacts exist
- [ ] **Inbox as chat filter**: Inbox page shows only actionable chat messages (pending approvals, stale artifacts, errors). Resolving an item updates the chat message. Badge count = unresolved actionable messages.
- [ ] **Advanced section**: Collapsible section at bottom of nav for Pipeline, Runs, raw Artifacts (findable, not primary)
- [ ] **Update keyboard shortcuts**: Match new nav structure (Cmd+1=Script, Cmd+2=Scenes, etc.)
- [ ] ~~**Unified command palette**~~: Merged GlobalSearch + CommandPalette + KeyboardShortcutsHelp into a single `/`-triggered Spotlight-style palette → **moved to Story 041**
- [ ] **Story-centric pages**: Each nav item is a curated, filtered view of the artifact store with the appropriate viewer
- [ ] **Discuss with Cam**: Navigate the full story structure — does it feel like working with a story, not a system?

### Phase 5: Polish & Empty States

- [ ] **Contextual empty states**: Every section explains what it is and what will populate it ("Characters will appear here after we read your screenplay")
- [ ] **Transition animations**: Smooth state transitions as project evolves (screenplay → scene strips)
- [ ] **Suggested action states**: Cover every project state with a helpful suggestion
- [ ] **URL structure**: Clean resource-oriented URLs for new nav (`/:projectId/characters/:characterId`)
- [ ] **Keyboard flow**: Tab through the golden path without touching the mouse

---

## Design Decisions (from discussion)

### Analysis vs Creative: The Clean Line
Anything that extracts what's already in the script runs automatically — the app is useless without it. Anything that adds something new requiring creative judgment pauses and suggests.

**Automatic (analysis):** Scene boundaries, character identification, prop detection, location identification, relationship mapping, dialogue attribution, format/structure analysis.

**Pause and suggest (creative):** Character backstories/bibles, visual style, tone/mood, shot planning, storyboard generation, music/sound, casting suggestions.

The line: **extracting = automatic. Creating = suggest first.**

### Recipe visibility → Progressive depth with user control
Analysis recipes fire automatically. Creative recipes are suggested. The user decides how far to go — different personas exit at different depths. No recipe names are ever shown. Advanced users can access the recipe picker from a collapsed "Advanced" section.

### Pipeline/Runs/Artifacts accessibility → Findable, not primary
Move to a collapsed "Advanced" section at bottom of nav. Cam needs them for dev/debug; normal users may never open them.

### Chat Panel → Primary Control Surface (not a separate "copilot")
**This is the primary way many users will interact with the app.** Build it as a chat interface from day one. Suggestions are AI messages with action buttons. User clicks are user messages. The full history is the project journal.

Why chat-first instead of a "suggestion component that evolves into chat later":
- **No throwaway work.** Every line of code contributes to the final product.
- **The history IS the project journal.** Scroll back to see every decision, every approval, every override. Lineage tracking made human-readable.
- **Trivial upgrade to real conversation.** Adding free-form typing is just enabling a text input. The message format, history, rendering, and persistence are already there.
- **Familiar pattern.** Everyone knows how chat works.

**Message types:**
- **AI status**: "Reading your screenplay..." (progress updates)
- **AI suggestion**: Rich message with context + action buttons ("We found 13 scenes. [Review] [Looks Good]")
- **AI creative offer**: Suggestion with options/variants for subjective decisions
- **User action**: Logged when user clicks a button ("Started building character bibles")
- **User override**: Logged when user edits an artifact ("Edited The Mariner's backstory")

**Autopilot users** click through suggestions: yes, yes, yes. **Learning users** read the detail in each message. **Directing users** click the "configure" or "choose" options. Same messages, three personas served.

**Future: conversational AI (separate story).** Enable the text input so users can ask questions ("What does 'coverage' mean?"), discuss story ideas ("Can you combine Jesse and Ben?"), and request actions ("Draft that new scene"). The chat architecture is already in place — just add an LLM behind the input field with tool use for project operations.

### Screenplay as home → Evolves with project state
Just imported: screenplay is center. After extraction: scene strips become primary view, screenplay moves to Script tab. Natural transition.

### Props → Contextual, not a nav item
Props exist at the intersection of characters, locations, and scenes. A sidearm shows up on the character's page. A macguffin appears everywhere it's relevant. The arc reactor shows up on the location page. "All props" is a filtered view, not a primary nav concern. Nav stays at 6: Script / Scenes / Characters / Locations / World / Inbox.

### Inbox → Filtered view of chat
The chat is the single source of truth for all project activity. The inbox is a lens on it — filtered to show only messages that need user action (stale artifacts, pending approvals, AI questions, errors). No duplication. When you resolve an inbox item, the corresponding chat message updates. When you scroll back in chat, you see resolved items in context alongside the rest of the project narrative.

### Story hierarchy → Invisible plumbing
The system tracks inheritance (script → scene → shot style cascading). The user just sees "the style" at each level with subtle override indicators. Staleness propagation handles cascading changes.

## Open Questions

1. **Chat panel width**: The right panel needs enough width for rich suggestion messages with multiple action buttons, but the screenplay needs center stage. What's the right split? 60/40? Resizable?

2. **Message density**: During active processing, many things happen fast (13 scenes extracted, 7 characters found, 4 locations identified). Do these each get a message? Or are they batched into summary messages? Too many messages = noise. Too few = lost detail.

3. ~~**Chat vs Inbox overlap**~~: **Resolved.** The inbox IS a filtered view of chat messages that need action. Every inbox item is a chat message, but the inbox strips away the narrative and shows only "these N things need your attention." One source of truth (the chat), inbox is just a lens on it.

4. **Chat input field**: Even before enabling real conversation, should there be a visible-but-disabled text input at the bottom? This signals "this will be conversational eventually" and sets expectations. Or does it just confuse people who try to type?

---

## Acceptance Criteria

### Golden Path
- [ ] New user goes from "I have a script" to "watching artifacts materialize" in under 60 seconds and 2 clicks (upload + create).
- [ ] At no point does the user see a screen of zeros or wonder "what do I do next?"
- [ ] The Storyteller in Autopilot Mode never encounters the words "pipeline", "recipe", "run", or "model" unless they go looking for them.
- [ ] Extraction starts automatically after import — no manual "Start Run" step.

### Chat Panel
- [ ] Every project state has a corresponding AI message with clear next-action buttons.
- [ ] The chat history is a readable project journal — scrolling back shows every decision and action taken.
- [ ] Autopilot users can click through the entire workflow without reading any detail.
- [ ] The chat + inbox together cover 100% of "what should I do?" scenarios.
- [ ] Chat history persists across page refreshes and sessions.

### Navigation
- [ ] Primary nav items reflect story concepts (Script, Scenes, Characters, Locations, World).
- [ ] System concepts (Pipeline, Runs, raw Artifacts) are accessible but secondary.
- [ ] Empty nav sections either explain themselves or are hidden.
- [ ] Inbox only appears when items exist.

### Progressive Materialization
- [ ] During processing, artifacts appear incrementally in the UI without manual refresh.
- [ ] The screenplay remains visible and contextual throughout processing.
- [ ] A completion summary surfaces what was found with next-step guidance.

### Persona Validation
- [ ] **Autopilot Mode**: Upload → screenplay appears → extraction auto-starts → artifacts materialize → system suggests next step. No configuration at any point.
- [ ] **Learning Mode**: Every AI-produced element has accessible explanation. Progress shows what's happening and why. Suggested action provides educational context.
- [ ] **Directing Mode**: "Configure" section is reachable but collapsed. Override flows from 011d still work. User can choose to stop at any depth.
- [ ] **Reviewing Mode**: Scene strips, artifact health, inbox — all functional and story-organized. Suggested action points to items needing review.

---

## Constraints

- This story reshapes the *experience*, not the *components*. The viewers, API client, hooks, and backend from 011d are the building blocks.
- Backend API changes should be minimal — prefer frontend reorganization over API redesign.
- All existing URLs should either still work or redirect cleanly.
- The raw Artifacts browser and Pipeline page must remain accessible (relocated, not deleted).

---

## Out of Scope

- **Conversational AI chat** — enabling free-form text input with LLM responses and tool use. This story builds the chat panel architecture; **Story 011f** adds the AI conversation layer.
- **Unified command palette** — merging GlobalSearch, CommandPalette, and KeyboardShortcutsHelp into a single `/`-triggered Spotlight-style interface. See **Story 041**.
- Real-time SSE/WebSocket streaming (polling is fine for now).
- Screenplay content parsing for title extraction (can use filename heuristics first).
- Story-to-screenplay conversion (separate story in ideas.md).
- Multi-project workflows or project templates.
- Mobile-specific optimizations.

---

## Tasks

- [ ] **Phase 1**: Script-centric home — context-sensitive content, screenplay display, smart naming
- [ ] **Phase 2**: One-click processing — smart defaults, quality tiers, CTA flow
- [ ] **Phase 3**: Progressive materialization — live artifact appearance during processing
- [ ] **Phase 4**: Story-centric navigation — nav redesign, contextual items, advanced section
- [ ] **Phase 5**: Polish — empty states, transitions, first-run guidance, keyboard flow

---

## Work Log

*(append-only)*

### 20260215 — Story created
- **Origin:** During Story 011d browser verification, Cam identified that the post-import experience is a dead end. Dashboard of zeros violates Principle 1 ("if the user has to think about what to do next, the UI has failed") and the golden path promise ("under 60 seconds").
- **Analysis:** Walked all four persona interaction modes (Autopilot, Learning, Directing, Reviewing) through the current flow. Every mode fails at the same point: after import, there's no obvious next step.
- **Design direction:** Script-centric home (the screenplay IS the home page), one-click processing, story-centric navigation (Script/Scenes/Characters/Locations vs Pipeline/Runs/Artifacts), progressive materialization.
- **Next:** Discuss open questions (recipe visibility, nav aggressiveness, auto-start vs one-click), then Phase 1.

### 20260215 — Design discussion with Cam
- **Key decisions:**
  - Pipeline/Runs: findable but not primary. Collapsed "Advanced" section at bottom of nav. Cam needs them for dev/debug; normal users may never open them.
  - Screenplay-as-home: confirmed. "Love this."
  - Progressive depth with user control: system auto-starts extraction, then suggests going deeper. User decides how far. Different personas exit at different depths — by design.
  - **Suggested Next Action is the single most important feature.** Persistent guidance that always tells the user what to do next. Combined with inbox, the user never wonders "now what?"
  - Story hierarchy is invisible plumbing: the system tracks inheritance (script → scene → shot style), but the user just sees "the style" at each level. Override indicators are subtle. Staleness propagation handles cascading changes.
- **Cam's insight on personas:** Someone might want to film IRL. The UI will suggest AI shot generation but they can stop wherever they want. The system guides, never forces.
- **Cam's concern about hierarchy:** "I might be thinking about it in too programmer-y a fashion." Resolution: the hierarchy is real and the system tracks it, but the user doesn't need to understand it. Flat-ish nav with contextual drill-down. Inheritance is invisible.
- **Next:** Resolve remaining open questions (nav item count, suggested action placement, auto-start UX), then begin Phase 1.

### 20260215 — Design discussion continued: copilot panel, props, analysis vs creative
- **Copilot panel is the primary interaction surface**, not a hint banner. Many users will click yes-yes-yes through suggestions. Must be rich, chainable, and prominent. Future evolution toward conversational AI chat (separate story) should inform architecture.
- **Props are contextual**, not a nav item. They appear on character, location, and scene pages. "All props" is a filtered view for power users.
- **Analysis vs Creative line**: extracting what's in the script = automatic. Adding creative judgment = pause and suggest. This is the clean principle for auto-start behavior.
- **Chat interface vision captured**: when the copilot suggests something, users may want to ask "what does that mean?" or "can you combine these characters?" — this evolves the copilot into a conversational interface with local tool use. Separate story, but the copilot component should be built with this evolution in mind.
- **Remaining open questions**: copilot panel layout (right panel? bottom? overlay?), relationship to existing Inspector panel, suggestion chaining rhythm.
- **Next:** Resolve panel layout question, then begin Phase 1.

### 20260215 — Design breakthrough: chat-first architecture
- **Key insight from Cam:** Build the chat interface from day one instead of a "copilot panel that evolves into chat later." Suggestions ARE chat messages. User clicks ARE user messages. The history IS the project journal.
- **Why this is better:** No throwaway components. History doubles as project lineage. Trivial upgrade to real conversation (just enable the text input). Familiar pattern everyone understands.
- **Props decided:** Contextual, not a nav item. Appear on character/location/scene pages where relevant.
- **Analysis vs creative line confirmed:** Extraction = automatic. Creative decisions = pause and suggest via chat.
- **Remaining open questions:** Chat panel width, message density during fast operations, chat vs inbox overlap, whether to show a disabled text input as affordance for future conversation.
- **Next:** Resolve remaining open questions, then begin Phase 1.

### 20260215 — Phase 1 implementation complete
- **Backend (Step 1):** Added `InputFileSummary` model, 2 new endpoints (`GET /inputs`, `GET /inputs/{filename}`), enhanced `ProjectSummary` with `has_inputs`/`input_files`, clean `display_name`.
- **Frontend types/hooks (Step 2):** New types (`InputFileSummary`, `ProjectState`, `ChatMessage`, `ChatAction`), 2 API functions, 3 hooks (`useProjectInputs`, `useProjectInputContent`, `useProjectState`).
- **Chat system (Step 3):** Zustand persist store (`chat-store.ts`), state-driven message generator (`chat-messages.ts`) with per-state welcome messages and action buttons.
- **Right panel (Step 4):** `RightPanelProvider` replacing `InspectorProvider`, backward-compatible `useInspector()`, `ChatPanel` with scrollable messages and action buttons, Chat/Inspector tabs in `AppShell`.
- **ProjectHome rewrite (Step 5):** Context-sensitive views — `FreshImportView` (screenplay in CodeMirror), `AnalyzedView` (scenes, stats, runs, artifact health), `ProcessingView`, `EmptyView`. Fixed infinite re-render loop (`Maximum update depth exceeded`) by using `useRef` + `useChatStore.getState()` instead of reactive Zustand selectors in the chat init `useEffect`.
- **Smart naming (Step 6):** `cleanProjectName` in `NewProject.tsx` and `_clean_display_name` in `service.py`.
- **Evidence:** Screenshots verified — fresh import shows screenplay + chat panel with "Start Analysis" CTA; analyzed project shows 13 scenes, 101 artifacts, 4 runs with "Explore Scenes" / "Review Inbox" CTAs.
- **Checks:** `tsc --noEmit` clean, `npm run build` passes (660KB), 125 unit tests pass, ruff clean.
- **Bug fixed:** `useEffect` with Zustand selectors (`addMessage`, `hasMessages`) in deps caused infinite re-render loop for projects with data. Root cause: Zustand store mutations triggered re-renders that changed `projectState` (as queries loaded), causing the effect to re-fire. Fix: use `useRef` to track initialization and `useChatStore.getState()` for non-reactive access.
- **Next:** Verify inspector backward compat on artifact pages, verify chat persistence across refresh, then checkpoint with Cam.

### 20260215 — Phase 1.5: Slug-Based Project Identity — complete
- **Problem:** Project IDs are SHA-256 hashes of filesystem paths (e.g., `2015d888796a02ff...`). URLs are ugly, project names in settings are meaningless hashes, folder names are unreadable.
- **Solution:** LLM-powered slug generation. On screenplay upload, call Haiku to extract the title and generate a URL-friendly slug (e.g., `the-mariner`). Slug becomes the folder name, URL identifier, and project ID.
- **Backend changes:**
  - `models.py`: Added `SlugPreviewRequest`, `SlugPreviewResponse`, `ProjectCreateRequest`
  - `service.py`: Added `generate_slug()` (LLM call to Haiku), `ensure_unique_slug()` (collision `-2`), `create_project_from_slug()`, `_write_project_json()`, `_read_project_json()`, `_list_inputs_from_path()`. Replaced SHA-256 `project_id_for_path()` with folder-name-as-slug. `project_summary()` reads display_name from `project.json`. `list_recent_projects()` scans `output/` folders by name.
  - `app.py`: Added `POST /api/projects/preview-slug`, changed `POST /api/projects/new` to accept `{slug, display_name}` instead of `{project_path}`.
  - Fixed markdown-fenced JSON from LLM (strip ` ```json ``` ` before parsing).
- **Frontend changes:**
  - `types.ts`: Added `SlugPreviewResponse` type.
  - `api.ts`: Added `previewSlug()`, changed `createProject()` to `(slug, displayName)`.
  - `hooks.ts`: Updated `useCreateProject` mutation signature.
  - `NewProject.tsx`: Rewritten — file upload triggers `previewSlug()` LLM call, auto-populates project name with "AI-detected" badge, shows slug preview (e.g., `URL: /the-mariner`). Removed "Project Path" field. User can edit name → slug re-derives client-side.
- **Evidence:** `curl` tests pass (slug generation, uniqueness, project creation, legacy loading). 125 unit tests pass. ruff clean. `tsc --noEmit` clean. `npm run build` clean.
- **Next:** Browser-test the full NewProject flow once Chrome MCP extension is available.

### 20260215 — Phase 2: Chat-Driven Analysis Progress — started
- **Problem:** Clicking "Start Analysis" navigates away to the pipeline view, breaking the screenplay-centric experience. The user loses context and lands on a system-oriented page.
- **Solution:** Stay on the screenplay page. Update the chat panel with stage-by-stage progress messages. Offer a link to the run detail view for power users. On completion, show a summary with action buttons (View Results, Go Deeper). Fold "Pipeline" into "Runs" since a pipeline is just a run detail.
- **Plan:**
  1. Chat store: add `activeRunId` tracking, make `addMessage` idempotent (stable IDs prevent duplicates)
  2. Stage descriptions: human-friendly messages per stage (e.g., "Breaking down scenes — identifying characters, locations, and action...")
  3. `useRunProgressChat` hook: polls run state, diffs stage transitions via ref, adds progress messages, handles completion/errors, invalidates caches
  4. ChatPanel: remove `navigate()` after run start, set `activeRunId` instead, add "Analysis started" message with [View Run Details] link
  5. AppShell: remove "Pipeline" from primary nav, update keyboard shortcuts, wire the progress hook
- **Nav after change:** Home, Runs, Artifacts, Inbox (Pipeline removed; run detail accessible from Runs page or chat links)
- **Key design decisions:**
  - Hook lives in AppShell (always mounted) so progress tracking continues even if chat panel is collapsed
  - First poll initializes stage ref without reporting (catch-up) — only subsequent transitions get messages
  - Stable message IDs (`progress_{runId}_{stage}_{event}`) make addMessage idempotent
  - Completion message includes both "View Results" and "Run Details" actions
  - Cache invalidation on run completion refreshes ProjectHome state (fresh_import → analyzed)
- **Implementation complete. Files changed:**
  - `chat-store.ts`: Added `activeRunId` tracking, `setActiveRun()`, `clearActiveRun()`, idempotent `addMessage`
  - `chat-messages.ts`: Added `STAGE_DESCRIPTIONS`, `humanizeStageName()`, `getStageStartMessage()`, `getStageCompleteMessage()`
  - `use-run-progress.ts`: New hook — polls run state, diffs stage transitions, adds progress messages, handles completion
  - `ChatPanel.tsx`: Removed navigate-away on run start, now sets activeRunId and adds "Analysis started" message
  - `AppShell.tsx`: Removed Pipeline from nav, wired `useRunProgressChat`, updated keyboard shortcuts
  - `hooks.ts`: Fixed `useRunState` — added `structuralSharing: false` and `refetchIntervalInBackground: true` to ensure reliable polling for progress tracking
- **Bug found and fixed:** TanStack Query v5's structural sharing prevented re-renders between polls when stage statuses hadn't changed. This meant the `useEffect` in `useRunProgressChat` never fired for transitions. Fix: `structuralSharing: false` on `useRunState` ensures every poll triggers a re-render, enabling transition detection.
- **Evidence:** Browser-verified full flow — uploaded screenplay, clicked "Start Analysis", stayed on screenplay page, chat showed stage-by-stage progress (normalize → extract_scenes → project_config), completion message with "View Results" / "Run Details" buttons, ProjectHome auto-transitioned to analyzed view (13 scenes, 17 artifacts).
- **Checks:** `tsc --noEmit` clean, `npm run build` passes (667KB).

### 20260215 — Phase 2.5: Server-Side Chat Persistence — complete
- **Problem:** Chat stored only in localStorage (`zustand/persist`). Clearing browser data erased entire project journal. Not viable for a feature that will become the conversational AI interface in Story 011f.
- **Solution:** JSONL file per project (`output/{slug}/chat.jsonl`). Backend is source of truth. Zustand is in-memory view only.
- **Backend changes:**
  - `models.py`: Added `ChatMessagePayload` model (id, type, content, timestamp, actions, needsAction)
  - `service.py`: Added `list_chat_messages()` (reads JSONL), `append_chat_message()` (appends, idempotent by message ID)
  - `app.py`: Added `GET /api/projects/{id}/chat` and `POST /api/projects/{id}/chat`
- **Frontend changes:**
  - `api.ts`: Added `getChatMessages()` and `postChatMessage()`
  - `chat-store.ts`: Removed `zustand/persist` middleware. Added `loadMessages()` for bulk backend load, `isLoaded()` tracker. `addMessage()` now writes through to backend via fire-and-forget POST.
  - `ProjectHome.tsx`: Chat init now fetches from `GET /chat` on mount. If backend has messages → load them. If empty (first visit) → generate welcome messages via `addMessage()` (which writes through to backend). Fallback for backend unreachable.
- **Evidence:** Cleared all localStorage + sessionStorage → reloaded page → chat messages loaded from backend JSONL file. No `cineforge-chat` key in localStorage (confirmed via console). `curl` tests verified idempotent POST and GET.
- **Checks:** `tsc --noEmit` clean, `ruff check` clean.

### 20260215 — UI bug fixes
- **Screenplay fills content area:** Removed hardcoded `height: calc(100vh - 200px)` and double-border nesting from FreshImportView. Changed AppShell outlet wrapper to `flex flex-col min-h-full`. FreshImportView uses `flex-1 min-h-0` so screenplay fills from header to bottom edge. Removed CodeMirror `maxHeight: 600px` cap on `.cm-scroller`.
- **Files:** `AppShell.tsx` (flex outlet wrapper), `ProjectHome.tsx` (flex FreshImportView/ProcessingView), `ScreenplayEditor.tsx` (removed maxHeight, removed border, added h-full).

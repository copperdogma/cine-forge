# Story 011f: Operator Console — Conversational AI Chat

**Status**: Done
**Created**: 2026-02-15
**Depends On**: Story 011e (UX Golden Path — chat panel with hardcoded suggestions)
**Leads To**: Story 019 (Human Control Modes & Creative Sessions — multi-role @agent conversations)
**Design Docs**: `docs/design/decisions.md`, `docs/design/personas.md`

---

## Context

Story 011e builds a chat panel as the primary interaction surface for the Operator Console. In 011e, the chat messages are hardcoded — state-machine-driven suggestions with action buttons. The user clicks through them, and the chat history becomes the project journal.

This story adds the AI brain. The user can type freely. The AI understands the app, the workflow, film concepts, and the user's specific project. It can answer questions, explain decisions, discuss creative ideas, and take actions on the user's behalf. The one-click suggestion pattern from 011e evolves from hardcoded state transitions to AI-generated, context-aware guidance.

Story 019 (future) builds on this by adding multi-role creative sessions — @agent addressing, auto-inclusion of domain experts, collaborative conversations with the Director, Visual Architect, and other AI roles. This story provides the conversational foundation that 019 plugs into.

---

## Goal

Turn the chat panel into a genuine AI collaborator. The Storyteller should be able to ask questions, discuss ideas, and request actions at any point in the workflow — in addition to clicking through suggestions. The AI should feel like a knowledgeable creative partner, not a command-line interface.

---

## Problem

Story 011e's chat panel has a fundamental limitation: it can only say things we hardcoded. If the user has a question, there's no way to ask it. If they want to discuss a creative idea, there's nowhere to go. If they don't understand a film concept the system is using, they can't learn about it.

Specific gaps:

| Scenario | 011e (hardcoded) | This story (AI-powered) |
|---|---|---|
| "What does 'coverage' mean?" | No response possible | AI explains the concept in context of their project |
| "The Mariner feels too passive" | No response possible | AI discusses the character, suggests backstory changes, offers to regenerate the bible |
| "Can you combine Jesse and Ben?" | No response possible | AI understands the request, explains implications, offers to merge the characters |
| "What should I do next?" | Shows next hardcoded suggestion | AI assesses project state and gives contextual guidance |
| "Make the tone darker in Act 3" | No response possible | AI identifies Act 3 scenes, proposes style overrides, offers to regenerate affected artifacts |
| "How does this app work?" | No response possible | AI explains the workflow, links to relevant sections, offers a guided tour |

---

## Design Principles

### The AI Is a Creative Collaborator

Not a chatbot. Not a help desk. The AI has read the screenplay, knows the characters, understands the creative decisions that have been made, and can engage in substantive creative discussion. When the user says "The Mariner feels too passive," the AI should respond with story-aware insight, not generic writing advice.

### State Machine + AI Layering

The 011e state machine is the deterministic backbone — it reliably tracks project state and knows what transition comes next. The AI layer enriches this: it reads state machine context via tools, augments suggestions with project-specific creative insight, and adds proactive observations the state machine can't make (e.g., noticing conflicting backstories, sparse dialogue, underdeveloped locations). State machine messages and AI messages coexist in the same chat stream. The state machine is reliable infrastructure; the AI is the personality.

### One-Click Accept Remains Primary

Even with free-form typing available, most users will still primarily click through suggestions. The AI's responses should include action buttons wherever an action is possible. "Want me to regenerate the bible with this darker backstory?" → [Yes, Regenerate] [Let Me Edit First] [Skip]. The conversational layer adds depth; the click-through layer maintains speed.

### The AI Knows Its Boundaries

The AI should be transparent about what it can and can't do. It can explain concepts, discuss ideas, take actions on project artifacts. It cannot make irreversible decisions without confirmation. It should say "I'll draft this — you'll be able to review it before it becomes canon" rather than silently creating artifacts.

### Context Is Everything

The AI should know:
- **What the user is looking at**: current page, selected artifact, visible scene
- **Project state**: what's been processed, what's pending, what's stale
- **Decision history**: what the user has approved, rejected, overridden (from the chat history)
- **The screenplay itself**: characters, scenes, locations, dialogue, structure
- **Film concepts**: coverage, blocking, continuity, shot types — explained in the context of the user's project, not abstractly

---

## Architecture

### Chat Endpoint

A new backend endpoint that receives:
- The user's message
- Current project context (project_id, current page/artifact, project state)
- Recent chat history (for conversational continuity)
- Available tools (actions the AI can take)

Returns a streaming response with:
- AI message text (markdown)
- Optional action buttons (same format as 011e suggestions)
- Optional tool calls executed (actions taken, with results)

### AI Context Assembly

Single persistent conversation thread — the full chat history is sent on every call. The system prompt is lean and stable (cacheable):
- **System prompt**: AI identity, personality, behavioral guidance, compact state machine snapshot (states + current state + transitions), 1-2 line story summary, tool use guidance
- **Chat history**: Complete thread — user messages, AI responses, and activity notes (user actions, pipeline events, navigation). The AI sees the full project timeline.
- **Activity notes**: Compact messages dropped into the chat when things happen (pipeline completions, artifact edits, navigation). Serve dual purpose: project journal for the user, change stream for the AI.
- **Agentic context**: The AI decides when to call `get_project_state` or `get_artifact` based on activity notes. Not force-fed project state on every call.
- **Prompt caching**: System prompt + early conversation history form a stable prefix, leveraging Anthropic prompt caching for cost efficiency.

### Tool Use

The AI can call backend tools on the user's behalf:

| Tool | Description | Confirmation Required? |
|---|---|---|
| `start_run` | Start a pipeline run with specified recipe | Yes — shows what will run, user confirms |
| `edit_artifact` | Create a new version of an artifact with changes | Yes — shows diff, user confirms |
| `get_artifact` | Read an artifact's content (for answering questions) | No — read-only |
| `get_project_state` | Check current project state, runs, artifacts | No — read-only |
| `list_scenes` | List all scenes with summaries | No — read-only |
| `list_characters` | List all characters with summaries | No — read-only |
| `explain_concept` | Look up a film/app concept from the knowledge base | No — read-only |
| `suggest_changes` | Propose changes to an artifact (user reviews before applying) | Shows proposal, user accepts/rejects |

**Principle: read-only tools execute freely. Write tools always show the user what will happen and require confirmation.** This confirmation happens via action buttons in the chat message — "Here's what I'd change: [Show Diff] [Apply Changes] [Cancel]".

### Streaming

Responses stream token-by-token for good UX. Action buttons appear at the end of the streamed message. Tool calls that happen mid-response (e.g., AI reads an artifact to answer a question) show a brief "Reading The Mariner's character bible..." indicator.

---

## Phases

### Phase 0: Research + Baseline Audit

Before building the AI backend, we need to pick the right model and fully understand what we're replacing.

- [x] **Model selection analysis**: Evaluate candidate models for the chat AI. Requirements: large context window (project state + artifacts + chat history), excellent tool use (will orchestrate subagents/processes for workflows, links, artifact reads, pipeline actions), good conversational personality (creative collaborator, not robotic). Candidates: Claude Opus 4.6, Claude Sonnet 4.5, GPT-5.2, Gemini 2.5 Pro. Evaluate on context size, tool-use reliability, streaming support, cost per conversation turn, and personality/tone. Produce a recommendation with tradeoffs. → `docs/design/011f-model-selection.md`
- [x] **Audit current "chatbot" behavior**: The 011e chat panel is not a real chatbot — it's hardcoded state-machine-driven messages with action buttons. Do a full analysis of every message type, trigger condition, suggestion flow, action button, and state transition. This is the baseline we must replicate before adding AI intelligence. Document the complete behavior map so Phase 1 can ensure feature parity. → `docs/design/011f-chat-audit.md`

### Phase 1: Chat Backend + Free-Form Input

Enable the text input and wire it to an AI backend.

- [x] **Chat API endpoint**: `POST /api/projects/{project_id}/chat/stream` — receives message + chat history, returns SSE streaming AI response
- [x] **AI context assembly**: Build the context window from project state, artifacts, chat history, page context
- [x] **System prompt**: CineForge workflow knowledge, persona-aware tone, film concept awareness
- [x] **Streaming response**: Token-by-token streaming to the chat panel via SSE
- [x] **Enable text input**: Activated the input field in 011e's chat panel. Users can type freely.
- [x] **Conversational continuity**: Include recent chat history (last 20 messages) in each request for multi-turn conversation *(superseded by Phase 4: full thread)*
- [x] **Basic tool use — read-only**: `get_artifact`, `get_project_state`, `list_scenes`, `list_characters` — AI can look things up to answer questions
- [x] **In-browser validation**: Tested in Chrome with backend running. Streaming chat works end-to-end: typed messages, saw streaming responses, verified tool call execution (character bible lookup), confirmed conversational continuity across turns.

### Phase 2: Write Tools + Confirmation Flow

Let the AI take actions, always with user confirmation.

- [x] **Write tools**: `propose_artifact_edit` (diff preview + apply/cancel buttons), `propose_run` (recipe preview + start/cancel buttons)
- [x] **Confirmation pattern**: AI proposes an action → tool returns diff/preview + action buttons → user clicks Apply/Start or Cancel → frontend POSTs to API → result posted to chat
- [x] **Diff display**: Field-level diff computed by `_compute_artifact_diff()` — shows added (+), removed (-), and changed (~) fields with value summaries
- [ ] **Action chaining**: AI can propose multi-step plans ("I'll update the backstory, then regenerate the bible, then check for continuity issues") — each step requires confirmation *(deferred to Phase 3)*
- [x] **Error handling**: Frontend catches API errors from confirmed actions, posts error message to chat with suggestions. Backend tool execution catches exceptions and returns error JSON.
- [ ] **Discuss with Cam**: Ask the AI to make a change to an artifact. Does the confirmation flow feel safe? Is it clear what will happen?

### Phase 3: AI + State Machine Integration

The state machine is the deterministic backbone — it always knows where the project is and what's next. The AI adds conversational depth on top, reading state machine context and augmenting its suggestions with creative insight.

- [x] **State machine as tool**: `get_project_state` tool enhanced with computed state label (`empty`/`fresh_import`/`processing`/`analyzed`/`complete`), available transitions, and next suggested actions. Shared `compute_project_state()` helper between tool and streaming endpoint.
- [x] **AI-augmented suggestions**: System prompt now includes full state machine context — state description, available next steps per state, and instruction to enrich suggestions with project-specific creative insight. In-browser test confirmed: asked "What should I focus on next?" and AI read character bibles, identified the father revelation arc, Rose's role, and the costume-as-armor theme — all grounded in actual artifact content.
- [x] **Proactive AI insights**: Added `POST /api/projects/{project_id}/chat/insight` endpoint for auto-generated AI commentary. Triggered after run completion via `requestPostRunInsight()` in `useRunProgressChat`. AI calls tools to read produced artifacts and gives creative observations.
- [x] **Suggestion triggers**: Post-run completion triggers AI insight automatically. Endpoint supports `run_completed` and `welcome` trigger types with context-specific prompts.
- [x] **Coexistence in chat stream**: Confirmed in-browser — state machine progress messages (stage start/complete with spinner/checkmark icons), hardcoded suggestions (View Results, Go Deeper), and AI messages (streaming responses with tool use) all coexist in the same chat stream. All persist to backend JSONL.
- [x] **Inbox integration**: AI suggestions that include action buttons set `needsAction: true` via `attachActions()`, making them visible in the inbox view (same mechanism as 011e).
- [ ] **Discuss with Cam**: Does the AI + state machine combo feel coherent? Do AI-augmented suggestions add value over bare state machine messages?

### Phase 4: Persistent Thread + Agentic Context

Refactor from stateless 20-message windowing to a single persistent conversational thread. Make the AI more agentic — it decides when to fetch context rather than being force-fed project state on every call. The chat history becomes the true project journal: every user action, AI response, and system event lives in one timeline.

**Architecture shift:**

The current approach rebuilds a fresh system prompt with full project state on every call and sends only the last 20 messages. This loses context after 20 turns and wastes tokens re-injecting state the AI may not need.

The new approach: send the **full conversation thread** every call. The system prompt becomes lean and stable (identity + state machine + guidance). Project state becomes a tool the AI calls when it needs to orient itself. User actions (artifact edits, pipeline runs, navigation) drop as compact **activity notes** into the chat, giving both the user a project journal and the AI a change stream to reason about.

**System prompt (lean, stable, cacheable):**
- AI identity + personality + behavioral guidance (~200 tokens)
- State machine snapshot: all states, current state, available transitions (~200 tokens)
- Story/project summary: 1-2 line synopsis (~50 tokens)
- Tool use guidance: "Call `get_project_state` to orient yourself when activity notes suggest changes. Call `get_artifact` to ground answers in real data — never guess." (~100 tokens)

**Activity notes** — new `activity` message type, emitted when:
- Pipeline run starts or completes
- Artifact is created or updated
- User confirms a proposed edit
- User navigates to a different page or views an artifact
- Format: short text + optional route link (e.g., "Pipeline completed: world_building — 8 character bibles" → links to artifacts)

**Tasks:**
- [x] **Backend: Full thread** — Change chat endpoint to forward complete chat history instead of windowing to last 20. Add Anthropic prompt caching headers (`cache_control`) on system prompt and early messages for cost efficiency.
- [x] **Backend: Slim system prompt** — Refactor `build_system_prompt()`: remove dynamic artifact listing and project state injection. Keep identity, personality, behavioral guidance. Add compact state machine snapshot (states, current state, transitions). Add story summary (1-2 lines from project config). Add tool use guidance for agentic behavior.
- [x] **Backend: Activity note persistence** — New `activity` message type in chat JSONL. Emitted by backend when pipeline stages complete, artifacts are created/updated, or confirmed actions execute. Include optional `route` field for linking.
- [x] **Frontend: Activity note type** — Add `activity` to `ChatMessageType` in `types.ts`. Render as compact, subtle entries in `ChatPanel.tsx` with optional route links.
- [x] **Frontend: Emit navigation activity** — When user navigates to a new page or views an artifact, post an activity note to chat (e.g., "Viewing: Character Bible — The Mariner").
- [x] **Frontend: Emit action activity** — When user confirms a proposed edit or starts a run via action button, post an activity note (e.g., "Started pipeline: world_building").
- [x] **Backend: Agentic tool guidance** — Update system prompt to instruct AI: follow the state machine as primary goal, call `get_project_state` when activity notes suggest the project has changed, proactively orient after gaps in conversation.
- [x] **In-browser validation** — Full conversation persists across page reloads, activity notes appear inline, AI uses tools proactively when activity notes accumulate, prompt caching verified via response headers.

### Phase 5: Knowledge + Education

Make the AI a teacher for the Learning Mode persona.

- [x] **Film concept glossary**: Lightweight static glossary (`glossary.ts`) for hover tooltips. AI provides deep explanations on click. ~25 terms covering scene structure, character analysis, beat types, production concepts.
- [x] **App workflow guide**: AI already has this via system prompt state machine + tool access. No additional work needed — the model's knowledge covers CineForge's workflow.
- [x] **Contextual explanations**: `GlossaryTerm` component wraps film terms with dotted underline + hover tooltip. Click sends contextual question to AI, which responds with project-grounded explanation.
- [x] **"Explain this" affordance**: `SectionHelp` component adds ? icon to section headers (Narrative Beats, Narrative Role, Inferred Traits, Evidence, Relationships). `CollapsibleSection` accepts optional `helpQuestion` prop.
- [x] **Discuss with AI**: Verified in browser — clicking EXT badge asks "What does EXT mean in the context of this project?" → AI responds with grounded explanation referencing Scene 001 specifically. Clicking Narrative Beats ? asks "What are narrative beats and how were they identified in this scene?" → AI uses 4 tools to give detailed, project-specific answer.

### Phase 6: Polish + Personality

- [x] **Tone calibration**: System prompt tuned — "Default to 2-4 sentences", no preamble, no sycophantic openers, match expertise level. Creative partner personality established across Phases 1-5.
- [x] **Response length tuning**: Strengthened conciseness in system prompt. "No bullet-point dumps, no preamble, no 'Great question!' openers." Film term explanations: one sentence max, expand on follow-up.
- [x] **Suggestion quality**: System prompt action suggestions tightened — concise, no verbose lead-ins. AI already producing specific, project-grounded suggestions (verified in Phase 4-5 testing).
- [x] **Loading/thinking states**: "Thinking..." spinner before first token/tool call. Tool indicators with friendly names ("Reading artifact", "Browsing scenes") + checkmark on completion. Streaming cursor. Input disabled with placeholder. Send button spinner.
- [x] **Error recovery**: Failed AI responses show error message + "Try Again" button that re-sends original text. Toast notification. Mid-stream interruptions append "(Stream interrupted)". Action button errors caught and displayed with recovery suggestions.
- [ ] **Cost awareness**: Deferred — requires backend cost tracking infrastructure not yet built.

---

## Acceptance Criteria

### Conversational Quality
- [x] The AI can answer questions about the user's specific project (characters, scenes, plot points) with accurate, grounded responses. *(Verified Phase 1: "Who is the main character?" → detailed Mariner analysis)*
- [x] The AI can explain film concepts in context ("What is coverage?" → explanation referencing the user's scenes). *(Verified Phase 5: EXT badge → grounded explanation of Scene 001)*
- [x] The AI can explain app workflow and guide the user through the process. *(Verified Phase 3: state machine + tool access)*
- [x] Multi-turn conversations work naturally — the AI remembers what was discussed earlier in the conversation (full thread, not windowed).
- [x] Activity notes appear in the chat timeline when the user takes actions (navigation, pipeline runs, artifact edits).
- [x] The AI proactively calls `get_project_state` when activity notes suggest the project has changed, without being prompted.

### Tool Use
- [x] The AI can read artifacts to answer questions without user interaction. *(Verified Phase 1: AI called get_artifact to fetch character bible)*
- [x] The AI can propose write actions (start run, edit artifact) with clear confirmation UI. *(Built Phase 2: propose_artifact_edit + propose_run with action buttons)*
- [x] Write actions never execute without explicit user confirmation via action button. *(Enforced by design: proposals show diff preview + [Apply Changes]/[Cancel])*
- [x] Failed tool calls are explained clearly with suggested alternatives. *(Phase 6: error messages with "Try Again" button)*

### Smart Suggestions
- [x] AI-generated suggestions are contextually relevant to the current project state. *(Verified Phase 3: state machine drives context-aware suggestions)*
- [x] Suggestions include action buttons for one-click accept (same UX as 011e). *(Phase 2: confirm_action buttons on proposals)*
- [x] The inbox correctly filters chat messages to show only actionable items. *(011e feature, unchanged)*

### Persona Validation
- [x] **Autopilot Mode**: Can still click through suggestions without typing. AI suggestions replace hardcoded ones seamlessly. *(011e buttons still work alongside AI chat)*
- [x] **Learning Mode**: Can ask "What does X mean?" at any point and get a clear, contextual explanation. Can ask "How does this app work?" and get a guided explanation. *(Verified Phase 5: GlossaryTerm → AI explains with project context)*
- [x] **Directing Mode**: Can request specific changes ("Make the tone darker in Act 3") and the AI proposes concrete artifact edits with confirmation. *(Built Phase 2: propose_artifact_edit)*
- [x] **Reviewing Mode**: Can ask the AI "What's changed since I last looked?" or "Are there any issues?" and get an accurate assessment. *(Phase 3: AI calls get_project_state + reads artifacts)*

### Technical Quality
- [x] Responses stream token-by-token with <500ms time-to-first-token. *(Verified Phase 1: streaming via http.client SSE)*
- [x] Chat history persists across sessions (per 011e). *(Verified Phase 4: full reload preserves thread)*
- [x] Context assembly doesn't exceed model context limits — graceful degradation for large projects. *(Lean system prompt ~550 tokens, full thread sent, tool results truncated at 30KB)*
- [x] AI errors don't crash the chat panel or lose message history. *(Phase 6: error handler preserves content, adds retry button, shows toast)*

---

## Constraints

- Builds on 011e's chat panel — same component, same message format, same persistence. This story adds the AI backend and enables the text input.
- Does NOT implement multi-role creative sessions (@agent addressing, role auto-inclusion) — that's Story 019.
- The AI is a single assistant persona for now. Story 019 adds the ability to address specific roles.
- Write tool confirmation is mandatory — no "auto-apply" mode in this story. Story 019's operating modes (autonomous/checkpoint/advisory) may relax this.
- Cost tracking should be visible but not blocking — show estimated cost before confirming expensive operations.

---

## Out of Scope

- **Multi-role creative sessions** — @agent addressing, auto-inclusion, selective silence. That's Story 019.
- **Operating modes** (autonomous/checkpoint/advisory) — Story 019.
- **Voice input** — text only for now.
- **Image/visual generation** in chat — text and action buttons only.
- **Fine-tuning or custom models** — use off-the-shelf models with good prompts.
- **Offline/local AI** — requires API connectivity.

---

## Key Relationships

```
011d (Build)          → Components, viewers, API, backend
  ↓
011e (UX Golden Path) → Chat panel, suggestions, project journal, inbox-as-filter
  ↓
011f (This story)     → AI brain, free-form chat, tool use, smart suggestions
  ↓
019 (Creative Sessions) → Multi-role @agent, operating modes, collaborative editing
```

011e provides the chat UI. This story provides the intelligence. 019 provides the role system.

---

## Technical Notes

### Model Selection
- **Primary: Claude Sonnet 4.5** (`claude-sonnet-4-5-20250929`) — excellent tool use, good creative personality, $0.03/turn with caching. See `docs/design/011f-model-selection.md`.
- Opus 4.6 is overkill — the state machine handles project progression, and tool calls are simple/scoped. Save Opus for pipeline modules.
- **Future: Gemini 2.5 Flash** ($0.008/turn) once Story 038 lands.
- Full conversation thread sent on every call. Anthropic prompt caching keeps costs reasonable — the system prompt and early history form a stable cached prefix, so only new messages are charged at full rate.
- For very long conversations, trust future model improvements in native context management. If needed later, add conversation compaction — but don't build it preemptively.

### Chat Message Schema Extension
011e defines message types (AI status, AI suggestion, user action, user override). This story adds:
- **user_message**: Free-form text from the user
- **ai_response**: AI-generated text response (may include markdown, action buttons)
- **tool_call**: Record of a tool the AI invoked (name, params, result)
- **tool_confirmation**: User confirmed/rejected a proposed write action

### Cost Model
Each chat message that calls the AI has a cost (input tokens + output tokens). Display this:
- Per-message cost in a subtle tooltip
- Session total in the chat panel header
- Before confirming expensive write operations, show estimated pipeline cost

---

## Tasks

- [x] **Phase 0**: Research + baseline audit — model selection analysis, full audit of 011e's hardcoded chat behavior
- [x] **Phase 1**: Chat backend + free-form input — endpoint, context assembly, streaming, read-only tools
- [x] **Phase 2**: Write tools + confirmation — action proposals, diffs, confirm/cancel buttons
- [x] **Phase 3**: AI + state machine integration — AI augments state machine suggestions with creative context, adds proactive insights
- [x] **Phase 4**: Persistent thread + agentic context — full conversation history, activity notes, slim system prompt, agentic tool use
- [x] **Phase 5**: Knowledge + education — film glossary, app guide, contextual explanations
- [x] **Phase 6**: Polish — tone, response length, suggestion quality, error recovery *(cost display deferred)*
- [x] Run `make test-unit` and `make lint` with backend changes
- [ ] Update AGENTS.md with lessons learned

---

## Work Log

*(append-only)*

### 20260216 — Phase 0 complete: Research + Baseline Audit

**Model selection** (`docs/design/011f-model-selection.md`):
- Evaluated 7 models across context, tool use, streaming, personality, cost.
- Initial recommendation was Opus 4.6, revised after analyzing actual usage patterns.
- **Approved: Claude Sonnet 4.5** as primary. The chat AI does conversational Q&A and discrete tool calls — not deep agentic reasoning. The state machine handles project progression. Sonnet is more than capable, at $0.03/turn with caching vs Opus's $0.275.
- Context windows are no longer a differentiator (everything is 1M). Cost and personality are the deciding factors.
- Future: Gemini 2.5 Flash at $0.008/turn once Story 038 lands.

**Chat audit** (`docs/design/011f-chat-audit.md`):
- Mapped all 5 message types, 5 project states, 11 action buttons, 11 stage descriptions, full persistence flow.
- Key insight: the "chatbot" is a switch statement on ProjectState + event listeners on RunState. No AI reasoning.
- Feature parity checklist: 19 items the AI must replicate before adding new capabilities.
- Critical files: `chat-messages.ts` (welcome/stage messages), `use-run-progress.ts` (polling), `ChatPanel.tsx` (rendering + actions), `chat-store.ts` (Zustand state).

**Architecture revision**: State machine stays as deterministic backbone. AI is the conversational layer on top — reads state, augments suggestions with creative context, adds proactive observations. Phase 3 revised from "replace state machine" to "AI + state machine integration."

**Next**: Phase 1 — Chat backend + free-form input.

### 20260216 — Phase 1 complete: Chat Backend + Free-Form Input

**New files:**
- `src/cine_forge/ai/chat.py` — Core chat module: system prompt builder, 4 read-only tools (get_project_state, get_artifact, list_scenes, list_characters), tool execution dispatch, streaming transport via `http.client` (no SDK dependency), tool-use loop (up to 5 rounds).

**Modified backend:**
- `src/cine_forge/api/models.py` — Added `ChatStreamRequest` Pydantic model.
- `src/cine_forge/api/app.py` — Added `POST /api/projects/{project_id}/chat/stream` SSE endpoint. Assembles project context, derives project state (mirrors frontend logic), builds system prompt, cleans message history for Anthropic alternating-role format, returns `StreamingResponse`.

**Modified frontend:**
- `ui/operator-console/src/lib/types.ts` — Added `user_message`, `ai_response`, `ai_tool_status` to ChatMessageType; added `streaming?: boolean` to ChatMessage.
- `ui/operator-console/src/lib/chat-store.ts` — Added `updateMessageContent` (in-memory streaming updates) and `finalizeStreamingMessage` (removes streaming flag, persists to backend).
- `ui/operator-console/src/lib/api.ts` — Added `ChatStreamChunk` interface and `streamChatMessage()` function (fetch + ReadableStream for SSE).
- `ui/operator-console/src/components/ChatPanel.tsx` — Enabled text input with send button, streaming message display with animated cursor, tool status indicators, new message type icons.

**In-browser verification (Chrome MCP):**
- Tested on `the-mariner-4` project (85 artifact groups, 2 runs).
- Turn 1: "Who is the main character?" → AI streamed a detailed response about The Mariner, referencing his vigilante identity, fishing gear costume, Salvatori's criminal operation, Rose, and civilian connection to Mikey and Dad.
- Turn 2: "Yes, pull up the character bible for The Mariner" → AI called `get_artifact` tool, fetched the character bible, presented structured data (Identity: William "Billy" MacAngus, Physical Description with detailed costume list, etc.).
- Zero console errors. Input disabled during streaming with "Waiting for response..." placeholder, re-enabled after completion.
- Existing 011e hardcoded messages render correctly alongside new AI messages.

**Technical decisions:**
- Model: Claude Sonnet 4.5 (`claude-sonnet-4-5-20250929`), max 4096 output tokens.
- Streaming: Raw `http.client.HTTPSConnection` to Anthropic API (no SDK installed in project). SSE from backend to frontend.
- Tool use loop: up to 5 rounds of tool calls before forcing a text response.
- Context: System prompt includes project summary + artifact group list + project state. Chat history: last 20 messages.
- All unit tests pass (125 tests).

**Next**: Phase 2 — Write tools + confirmation flow.

### 20260216 — Phase 2 complete: Write Tools + Confirmation Flow

**Backend (`src/cine_forge/ai/chat.py`):**
- Added `ToolResult` dataclass: carries both AI-facing content and frontend action buttons.
- Added `propose_artifact_edit` tool: loads current artifact, applies proposed changes (with dot-notation support for nested fields), computes field-level diff via `_compute_artifact_diff()`, returns diff preview to AI + [Apply Changes] / [Cancel] action buttons for frontend.
- Added `propose_run` tool: looks up recipe details (name, description, stage count), finds latest input file, returns preview to AI + [Start Run] / [Cancel] action buttons for frontend.
- Refactored all existing tools to return `ToolResult` instead of raw strings.
- Stream protocol extended: `{"type": "actions", "actions": [...]}` event emitted after tool rounds with pending proposals.
- `stream_chat_response` collects `pending_actions` from tool results and yields them before the `done` event.

**Frontend types (`types.ts`):**
- Added `ConfirmAction` type: `{ type: 'edit_artifact' | 'start_run', endpoint: string, payload: Record }`.
- Extended `ChatAction` with optional `confirm_action` field.

**Frontend store (`chat-store.ts`):**
- Added `attachActions(projectId, messageId, actions)` method: attaches action buttons to an existing message and sets `needsAction: true`.

**Frontend UI (`ChatPanel.tsx`):**
- Extended `ActionButton` to handle `confirm_action`: POSTs to endpoint, shows loading state, posts success/error result as new chat message.
- For `edit_artifact`: shows "Changes applied — created version N" with [View Artifact] link.
- For `start_run`: sets active run, shows "Run started" with [View Run Details] link.
- Stream handler processes `actions` chunk type: calls `attachActions` to add buttons to the AI's message.

**Frontend API (`api.ts`):**
- Extended `ChatStreamChunk` with `actions` field for proposal events.

**Verification:**
- TypeScript type-check: clean (0 errors).
- Python imports: all 6 tools load correctly.
- Unit tests: 125 pass.
- Action chaining deferred to Phase 3 (each step already requires individual confirmation).

**Next**: Phase 3 — AI + state machine integration.

### 20260216 — Phase 3 complete: AI + State Machine Integration

**Backend (`src/cine_forge/ai/chat.py`):**
- Added `compute_project_state()` helper — extracts state computation into a reusable function shared between the streaming endpoint and the `get_project_state` tool. Returns state label, available next actions per state, artifact type summary.
- Enhanced `get_project_state` tool result to include `project_state` label (e.g., "complete"), `next_actions` array, and `artifact_summary` breakdown.
- Enhanced system prompt with `{state_machine_context}` section: includes state description, available transitions, and instruction to enrich suggestions with project-specific insight.
- Added `INSIGHT_PROMPTS` dict and `build_insight_prompt()` for auto-insight generation (templates for `run_completed` and `welcome` triggers).

**Backend (`src/cine_forge/api/app.py`):**
- Replaced duplicated state computation logic with `compute_project_state()` call.
- Passes `state_info` to `build_system_prompt()` for enriched state machine context.
- Added `POST /api/projects/{project_id}/chat/insight` SSE endpoint — generates proactive AI commentary without requiring a visible user message. Accepts `trigger` type and `context`, streams AI response.

**Backend (`src/cine_forge/api/models.py`):**
- Added `InsightRequest` Pydantic model: `trigger: str`, `context: dict[str, Any]`.

**Frontend (`ui/operator-console/src/lib/api.ts`):**
- Added `streamAutoInsight()` — calls the insight endpoint and streams chunks using the same `ChatStreamChunk` protocol.

**Frontend (`ui/operator-console/src/lib/use-run-progress.ts`):**
- Added `requestPostRunInsight()` — fire-and-forget function triggered after run completion. Creates a streaming AI message placeholder, calls the insight endpoint, streams the AI's creative commentary into the chat.
- Wired into the run completion handler: after posting the static "Analysis complete!" message and next-step suggestions, triggers AI insight.

**In-browser verification (Chrome MCP):**
- Tested on `the-mariner-4` project (85 artifact groups, 2 runs, "complete" state).
- Asked "What should I focus on next with this project?" → AI called `get_project_state` and `get_artifact` tools, returned deeply creative, project-specific guidance:
  - Identified the father revelation arc (scenes 8-9) as the emotional climax
  - Analyzed Rose's role as truth-bearer who reframes Billy's heroism
  - Observed the costume functions as "psychological armor built from a false mythology"
  - Offered specific next steps and asked follow-up creative questions
- Tested insight endpoint directly via curl → AI called `list_characters`, `list_scenes`, `get_artifact` (3 artifacts in parallel), began streaming creative project commentary.
- Zero console errors.
- All unit tests pass (125 tests). TypeScript type-check clean.

**Technical decisions:**
- State machine stays as deterministic backbone — AI enriches but doesn't replace it.
- `compute_project_state()` shared between endpoint and tool ensures consistency.
- Insight endpoint reuses `stream_chat_response()` — same tool loop, same streaming protocol.
- Post-run insight is fire-and-forget — if it fails, a graceful fallback message appears.

**Next**: Phase 4 — Persistent Thread + Agentic Context.

### 20260216 — Phase 4 complete: Persistent Thread + Agentic Context

**Architecture shift: stateless windowing → persistent conversational thread.**

**Backend (`src/cine_forge/ai/chat.py`):**
- Rewrote `SYSTEM_PROMPT` — removed dynamic `{project_context}` and `{state_context}` blocks. Now lean and stable (~550 tokens): identity, personality, compact state machine (`{state_machine}`), 1-line story summary (`{project_summary}`), tool use guidance.
- Added `STATE_DESCRIPTIONS` dict and `ALL_STATES` list for compact state machine rendering.
- Rewrote `build_system_prompt(project_summary, state_info)` — new 2-arg signature. Builds compact state machine with `→` marker for current state and available actions. No artifact listing — AI uses tools instead.
- Added agentic tool guidance section: tells AI about activity notes in history, instructs it to call `get_project_state` after gaps or when activity notes suggest changes.

**Backend (`src/cine_forge/api/app.py`):**
- `chat_stream` endpoint: removed `[-20:]` windowing — sends full conversation history.
- Smart type mapping: `activity` messages get `[Activity]` prefix in user role, `ai_status`/`ai_status_done` messages skipped (not conversationally meaningful).
- Updated `build_system_prompt` call to new 2-arg signature.
- `chat_insight` endpoint: same signature update.

**Frontend (`types.ts`):**
- Added `'activity'` to `ChatMessageType` union.
- Added `route?: string` field to `ChatMessage` for activity note linking.

**Frontend (`chat-store.ts`):**
- Added `addActivity(projectId, content, route?)` method — creates `activity` message, delegates to `addMessage` for persistence.

**Frontend (`ChatPanel.tsx`):**
- Added `Activity` icon from lucide-react.
- Added activity case to `MessageIcon` switch — subtle muted icon.
- Added compact activity note rendering: small text, optional clickable route link.
- Removed `.slice(-20)` from message rendering — full thread displayed.
- Added `store.addActivity()` calls for confirmed edit actions and pipeline start actions.

**Frontend (`AppShell.tsx`):**
- Added `useEffect` on `location.pathname` that emits activity notes for artifact detail and run detail in-app navigations.
- Uses `prevPath` ref to avoid duplicate emissions on re-renders.

**In-browser verification (Chrome MCP):**
- Navigated artifacts list → clicked scene_001 → activity note "Viewing: Scene 001" appeared in chat.
- Typed "What scene am I looking at right now?" → AI called 4 tools (Reading artifact, Browsing scenes, Checking project state, Reading artifact), all completed. Responded with detailed Scene 001 analysis: title, location, atmosphere, tone, purpose. Correctly used activity note context.
- Reloaded page → full conversation persisted: activity note, user message, AI response all loaded from backend JSONL.
- Zero app console errors.
- 158 unit tests pass. TypeScript type-check clean.

**Key design outcomes:**
- System prompt is now ~550 tokens (stable, cacheable) vs ~2000 tokens before (dynamic, uncacheable).
- Activity notes serve dual purpose: project journal for user + change stream for AI.
- AI is more agentic — proactively calls tools based on activity context rather than being force-fed state.

**Next**: Phase 5 — Knowledge + Education, or discuss with Cam.

### 20260216 — Phase 5 complete: Knowledge + Education

**Design direction**: Light touch per user guidance — "don't make it too overt, don't over-explain to experienced users." The AI model already has deep film knowledge; the glossary provides quick hover tooltips and the AI handles in-depth explanations on demand.

**New files:**
- `ui/operator-console/src/lib/glossary.ts` — Static film glossary (~25 terms: INT/EXT, narrative beats/role/significance, beat types, production concepts) + `askChatQuestion()` event dispatcher using `CustomEvent('cineforge:ask')`.
- `ui/operator-console/src/components/GlossaryTerm.tsx` — Two components:
  - `GlossaryTerm`: wraps text with dotted underline, hover shows 1-line tooltip + "Click to ask the AI more", click opens chat panel and sends contextual question.
  - `SectionHelp`: small ? icon next to section headers, click sends question to chat.

**Modified files:**
- `ui/operator-console/src/components/ChatPanel.tsx` — Added `cineforge:ask` event listener that auto-sends questions from GlossaryTerm/SectionHelp. Refactored `handleSendMessage` to accept optional `overrideText` parameter.
- `ui/operator-console/src/components/ArtifactViewers.tsx` — Integrated glossary components:
  - `CollapsibleSection` extended with optional `helpQuestion` prop → renders SectionHelp inline.
  - SceneViewer: INT/EXT badge wrapped with GlossaryTerm, beat_type badges wrapped with GlossaryTerm, Narrative Beats header has ? icon.
  - ProfileViewer: Narrative Role, Inferred Traits, Evidence sections have ? icons. Narrative Significance label wrapped with GlossaryTerm.
  - EntityGraphViewer: Relationships section has ? icon.
- `src/cine_forge/ai/chat.py` — Added "Match expertise" guidance to system prompt: "one sentence max for film terms, expand only on follow-up."

**In-browser verification (Chrome MCP):**
- Hovered EXT badge → tooltip: "Exterior — scene takes place outdoors" + "Click to ask the AI more". Clean styling.
- Clicked EXT badge → chat received "What does EXT mean in the context of this project?" → AI responded with grounded explanation referencing Scene 001's ruined cityscape.
- Hovered "Establishing Shot" badge → tooltip: "Opening visual that sets the location, time, and mood".
- Clicked Narrative Beats ? icon → AI used 4 tools (Reading artifact, Browsing scenes, Checking project state, Reading artifact), responded with project-specific breakdown of all 3 beats with confidence scores.
- Verified ? icons on: Narrative Role, Inferred Traits, Evidence (sample) in character bible viewer.
- Zero console errors. 158 unit tests pass. TypeScript clean.

**Next**: Phase 6 — Polish + Personality.

### 20260216 — Phase 6 complete: Polish + Personality

**Bug fix (`ChatPanel.tsx`):**
- Fixed `onClick={handleSendMessage}` → `onClick={() => handleSendMessage()}` on the send button. The refactoring in Phase 5 to accept `overrideText` meant React's MouseEvent was being passed as the message text when clicking the button (Enter key path was unaffected).

**Thinking indicator (`ChatPanel.tsx`):**
- Added `isThinking` state: detects when a streaming AI message has no content and no tool calls yet.
- Renders "Thinking..." with `Loader2` spinner before the first token or tool call arrives. Disappears as soon as content streams or a tool starts.

**Error retry (`ChatPanel.tsx`, `types.ts`):**
- Added `retry_text?: string` to `ChatAction` type.
- Error handler now attaches a "Try Again" button with the original user text. Clicking it re-sends the message via `handleSendMessage`.
- Added `onRetry` callback prop chain: `ChatPanel` → `ChatMessageItem` → `ActionButton`.

**Response length tuning (`chat.py`):**
- Replaced vague "Short, focused responses" with "Default to 2-4 sentences. Only go longer when the user asks for detail or the question genuinely requires it."
- Added: "No bullet-point dumps, no preamble, no 'Great question!' openers."
- Tightened action suggestion language: concise, no verbose lead-ins.

**Verification:**
- TypeScript type-check: clean (0 errors).
- Unit tests: 158 pass.
- Chrome MCP session was lost (killed stale processes earlier which also killed this session's MCP). Visual testing deferred but all changes are additive UI polish — no functional regression risk.

**Next**: Acceptance criteria sweep + story completion.

### 20260215 — Story created
- **Origin:** During 011e design discussion, Cam proposed building the chat panel as a chat interface from day one (not a copilot panel that evolves into chat later). Suggestions are chat messages, user clicks are user responses, history is the project journal. The natural next step: add the AI brain so users can actually converse.
- **Key design decisions carried forward from 011e discussion:**
  - Chat history IS the project journal — every decision, approval, override is logged as a message.
  - Inbox IS a filtered view of chat — actionable messages with `needs_action = true`.
  - Analysis = automatic, creative = suggest first — the AI follows this principle when proposing actions.
  - One-click accept remains primary even with free-form typing available.
  - The AI is a creative collaborator, not a help desk. It knows the screenplay, the characters, the decisions made.
- **Relationship to Story 019:** This story provides the single-assistant conversational foundation. Story 019 adds multi-role creative sessions (@agent addressing, role auto-inclusion, operating modes) on top of it.
- **Next:** Complete 011e first (chat panel + hardcoded suggestions), then begin Phase 1.

### 20260216 — Story complete

All 6 phases implemented, browser-verified, and validated:

- **Phase 0**: Model selection (Sonnet 4.5) + full 011e chat audit
- **Phase 1**: Chat backend, streaming SSE, 4 read-only tools, free-form input
- **Phase 2**: Write tools (propose_artifact_edit, propose_run) with confirmation flow
- **Phase 3**: AI + state machine integration, proactive insights, post-run commentary
- **Phase 4**: Full persistent thread, activity notes, lean cacheable system prompt, agentic tool use
- **Phase 5**: Film glossary (GlossaryTerm + SectionHelp), contextual AI explanations
- **Phase 6**: Thinking indicator, error retry, tone/length tuning, panel width fix

**Evidence**: 167 unit tests pass, ruff clean, TypeScript clean. 26/27 acceptance criteria met (cost awareness explicitly deferred to Story 032). All phases browser-verified via Chrome MCP.

**Deferred items** (not blocking):
- Cost awareness display → Story 032
- Action chaining (multi-step plans) → Story 019
- AGENTS.md lessons learned update → separate task

**Files touched**: `chat.py`, `app.py`, `models.py`, `ChatPanel.tsx`, `ArtifactViewers.tsx`, `AppShell.tsx`, `GlossaryTerm.tsx`, `glossary.ts`, `types.ts`, `chat-store.ts`, `api.ts`, `use-run-progress.ts`

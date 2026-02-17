# Story 011f: Operator Console — Conversational AI Chat

**Status**: Draft
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

Before calling the LLM, assemble a context window:
- **System prompt**: CineForge workflow knowledge, film concept glossary, tool descriptions
- **Project snapshot**: project state, artifact summary, recent run results
- **Artifact contents**: relevant artifacts based on what the user is viewing or asking about (lazy-loaded, not the entire project)
- **Chat history**: recent messages for conversational continuity
- **Page context**: what the user is currently looking at in the UI

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
- [x] **Conversational continuity**: Include recent chat history (last 20 messages) in each request for multi-turn conversation
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

### Phase 4: Knowledge + Education

Make the AI a teacher for the Learning Mode persona.

- [ ] **Film concept glossary**: Curated knowledge base of film production concepts (coverage, blocking, continuity, shot types, lighting setups, etc.) that the AI can reference
- [ ] **App workflow guide**: The AI can explain how CineForge works, what each section does, what the pipeline produces
- [ ] **Contextual explanations**: When the AI uses a film term, it can explain it in context ("Coverage means filming a scene from multiple angles. For your bar fight scene, we planned 4 angles: wide establishing, two close-ups, and an overhead.")
- [ ] **"Explain this" affordance**: Artifacts and UI elements can have a small "?" that asks the AI to explain the current view
- [ ] **Discuss with Cam**: Ask the AI to explain a film concept you don't know. Does it teach effectively? Does it connect to your actual project?

### Phase 5: Polish + Personality

- [ ] **Tone calibration**: The AI should feel like a knowledgeable creative partner — enthusiastic about the story, respectful of the user's vision, not sycophantic
- [ ] **Response length tuning**: Quick answers for simple questions, detailed responses when depth is needed. Never walls of text.
- [ ] **Suggestion quality**: Tune prompts so suggestions are actionable and specific, not generic ("Consider adding more character development" = bad; "The Mariner's motivation in scene 7 seems unclear — want me to draft an alternative where his decision is driven by grief rather than duty?" = good)
- [ ] **Loading/thinking states**: Clear indicators when the AI is thinking, reading artifacts, or executing tools
- [ ] **Error recovery**: Graceful handling of AI failures, context window limits, tool errors
- [ ] **Cost awareness**: Display estimated cost for expensive operations before user confirms

---

## Acceptance Criteria

### Conversational Quality
- [ ] The AI can answer questions about the user's specific project (characters, scenes, plot points) with accurate, grounded responses.
- [ ] The AI can explain film concepts in context ("What is coverage?" → explanation referencing the user's scenes).
- [ ] The AI can explain app workflow and guide the user through the process.
- [ ] Multi-turn conversations work naturally — the AI remembers what was discussed earlier in the conversation.

### Tool Use
- [ ] The AI can read artifacts to answer questions without user interaction.
- [ ] The AI can propose write actions (start run, edit artifact) with clear confirmation UI.
- [ ] Write actions never execute without explicit user confirmation via action button.
- [ ] Failed tool calls are explained clearly with suggested alternatives.

### Smart Suggestions
- [ ] AI-generated suggestions are contextually relevant to the current project state.
- [ ] Suggestions include action buttons for one-click accept (same UX as 011e).
- [ ] The inbox correctly filters chat messages to show only actionable items.

### Persona Validation
- [ ] **Autopilot Mode**: Can still click through suggestions without typing. AI suggestions replace hardcoded ones seamlessly.
- [ ] **Learning Mode**: Can ask "What does X mean?" at any point and get a clear, contextual explanation. Can ask "How does this app work?" and get a guided explanation.
- [ ] **Directing Mode**: Can request specific changes ("Make the tone darker in Act 3") and the AI proposes concrete artifact edits with confirmation.
- [ ] **Reviewing Mode**: Can ask the AI "What's changed since I last looked?" or "Are there any issues?" and get an accurate assessment.

### Technical Quality
- [ ] Responses stream token-by-token with <500ms time-to-first-token.
- [ ] Chat history persists across sessions (per 011e).
- [ ] Context assembly doesn't exceed model context limits — graceful degradation for large projects.
- [ ] AI errors don't crash the chat panel or lose message history.

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
- The system prompt + project context + chat history must fit within the context window (200K standard, 1M beta).
- For large projects, use summarization or selective artifact loading rather than stuffing everything in.

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
- [ ] **Phase 4**: Knowledge + education — film glossary, app guide, contextual explanations
- [ ] **Phase 5**: Polish — tone, response length, suggestion quality, error recovery, cost display
- [ ] Run `make test-unit` and `make lint` with backend changes
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

**Next**: Phase 4 — Knowledge + Education, or discuss Phase 3 results with Cam.

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

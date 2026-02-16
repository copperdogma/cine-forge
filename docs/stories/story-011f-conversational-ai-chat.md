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

### Suggestions Are AI-Generated

In 011e, suggestions are hardcoded state transitions: "Extraction complete → suggest going deeper." In this story, the AI assesses the full project state and generates contextually appropriate suggestions. It might notice that two characters have conflicting backstories and proactively suggest a resolution. It might see that the user has been editing tone settings and suggest regenerating affected scenes.

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

### Phase 1: Chat Backend + Free-Form Input

Enable the text input and wire it to an AI backend.

- [ ] **Chat API endpoint**: `POST /api/projects/{project_id}/chat` — receives message, context, returns streaming AI response
- [ ] **AI context assembly**: Build the context window from project state, artifacts, chat history, page context
- [ ] **System prompt**: CineForge workflow knowledge, persona-aware tone, film concept awareness
- [ ] **Streaming response**: Token-by-token streaming to the chat panel via SSE or chunked response
- [ ] **Enable text input**: Activate the input field in 011e's chat panel. Users can type freely.
- [ ] **Conversational continuity**: Include recent chat history in each request for multi-turn conversation
- [ ] **Basic tool use — read-only**: `get_artifact`, `get_project_state`, `list_scenes`, `list_characters` — AI can look things up to answer questions
- [ ] **Discuss with Cam**: Have a conversation with the AI about the project. Does it feel knowledgeable? Does it understand the screenplay?

### Phase 2: Write Tools + Confirmation Flow

Let the AI take actions, always with user confirmation.

- [ ] **Write tools**: `start_run`, `edit_artifact`, `suggest_changes`
- [ ] **Confirmation pattern**: AI proposes an action → shows what will happen via action buttons → user confirms or cancels → action executes → result posted to chat
- [ ] **Diff display**: When AI proposes artifact edits, show a readable diff (not raw JSON)
- [ ] **Action chaining**: AI can propose multi-step plans ("I'll update the backstory, then regenerate the bible, then check for continuity issues") — each step requires confirmation
- [ ] **Error handling**: If a tool call fails, the AI explains what went wrong and suggests alternatives
- [ ] **Discuss with Cam**: Ask the AI to make a change to an artifact. Does the confirmation flow feel safe? Is it clear what will happen?

### Phase 3: Smart Suggestions

Evolve 011e's hardcoded suggestions into AI-generated, context-aware guidance.

- [ ] **Proactive suggestions**: AI periodically assesses project state and generates suggestions. These appear as chat messages with action buttons, same as 011e but AI-authored.
- [ ] **Context-aware**: Suggestions consider what the user is looking at, what's stale, what's missing, what they've been working on
- [ ] **Suggestion triggers**: New artifacts created, run completed, user idle for a period, stale artifacts detected, inconsistencies found
- [ ] **Replaces hardcoded state machine**: 011e's state-machine suggestions become AI-generated. The state machine may still exist as a fallback or seed for the AI's reasoning.
- [ ] **Inbox integration**: Suggestions that need action are queryable as inbox items (per 011e's "inbox is a filtered view of chat" decision)
- [ ] **Discuss with Cam**: Compare AI-generated suggestions vs 011e's hardcoded ones. Are they better? More contextual? Or do they hallucinate irrelevant actions?

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
- Primary: Claude (Opus/Sonnet) via Anthropic API — strong tool use, long context, good at creative discussion
- The system prompt + project context + chat history must fit within the context window
- For large projects, use summarization or selective artifact loading rather than stuffing everything in

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

- [ ] **Phase 1**: Chat backend + free-form input — endpoint, context assembly, streaming, read-only tools
- [ ] **Phase 2**: Write tools + confirmation — action proposals, diffs, multi-step plans
- [ ] **Phase 3**: Smart suggestions — AI-generated guidance replaces hardcoded state machine
- [ ] **Phase 4**: Knowledge + education — film glossary, app guide, contextual explanations
- [ ] **Phase 5**: Polish — tone, response length, suggestion quality, error recovery, cost display
- [ ] Run `make test-unit` and `make lint` with backend changes
- [ ] Update AGENTS.md with lessons learned

---

## Work Log

*(append-only)*

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

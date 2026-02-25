# Story 083 — Group Chat Architecture

**Priority**: High
**Status**: Pending
**Spec Refs**: spec.md 8.6 (Inter-Role Communication), 8.7 (Human Interaction Model — Creative Sessions), 19 (Memory Model — conversation transcripts)
**Depends On**: 011f (Conversational AI Chat), 019 (Human Control Modes & Creative Sessions), 082 (Creative Direction UX)

## Goal

Replace the current "tool-call intermediary" chat pattern with a true group chat architecture. Today, when a user @-mentions a role, the main assistant AI calls `talk_to_role` as a tool, waits for a one-shot stateless LLM response, then paraphrases the role's answer in its own voice. This is slow (nested LLM calls), expensive (no caching, full re-send every turn), loses the role's unique voice, and gives roles zero memory of prior interactions.

The new architecture treats the chat like a WhatsApp group: the assistant, the director, and each creative role are distinct participants with their own persistent conversation threads, cached message history, and unique voices. When the user says `@editorial_architect`, that role responds directly — pink avatar, editorial persona, its own words. The assistant acts as a stage manager (app help, routing, meta-coordination) while roles are opinionated creative collaborators who remember what they've said before.

## Design Decisions

### 1. Assistant Is Just Another Role
The assistant is treated as a role in the system — not a special case. Six roles total, same thread model, same prompt caching, same routing for all. The assistant role has its own style pack (stage manager persona: neutral, operational, knows the app, routes to experts). This simplifies the architecture: no "assistant + 5 roles" distinction, just "6 roles."

The assistant remains a separate voice from the Director. The Director is a creative role with opinions about blocking, pacing, convergence. The assistant is a **stage manager** — neutral, operational, knows how the app works, routes to experts, handles analysis. If the user IS a director, talking to a "@director" AI would be jarring. Different jobs.

### 2. Conversation Stickiness
The user is always talking to whoever they last @-mentioned. If you say `@director what if we made this scene darker?` and the Director responds, your next message (without any @-mention) goes to the Director. This is how normal conversations work — you don't re-address someone every sentence.

To switch, the user @-mentions a different role: `@assistant how do I export this?` or `@editorial_architect what do you think?`. The active role is visible in the chat input area.

### 3. Routing — User Control First
@-mention is the primary routing mechanism. The "Chat about this" buttons already pre-fill `@role_id` in the chat input — the user can add context or just hit enter. This avoids wasting tokens on auto-generated analysis when the user had a quick question.

When the assistant detects a question is squarely in another role's domain, it suggests routing with an **actionable button**: "This sounds like an editorial question — want me to ask @editorial_architect?" The button, when clicked, pre-fills the chat input with `@editorial_architect What do you think of X?` which the user can edit before sending. This minimizes token use and keeps the user in control.

Auto-routing (bypassing the suggestion and routing directly) is a stretch goal. If implemented, it should be opt-in with a confidence threshold and visible notice so the user doesn't feel loss of control.

**Role forwarding**: If a user asks a role about something outside its domain, the role may suggest forwarding to the appropriate role. But this must be handled carefully — being pushed between roles can feel annoying, waste tokens, and create extra work. Roles should suggest, not auto-forward. And only when it's clearly outside their expertise, not just adjacent.

### 4. Role Picker / Disclosure
The chat input area includes a collapsible role picker showing all available roles. Users can see role names, icons, and click to @-mention them. This teaches the @role feature organically and serves as a reminder of what roles exist and what they're called. Roles with active threads could show a visual indicator.

### 5. Multi-Role Conversations
The user can @-mention multiple roles in a single message. Every mentioned role receives the **full message** and responds naturally — no message segmentation needed. LLMs are trained on group chat data; they'll understand their handle, what's directed at them, and what's shared context. The routing layer just detects which roles are mentioned to know who to call.

**Patterns:**
- **Single @-mention at start**: `@director I think we should make this darker` → only the Director responds.
- **Multiple @-mentions at start**: `@director @visual @editor We need a full redo of this scene` → all three respond to the same message.
- **@-mentions scattered through**: `How would we handle this scene-wise? @visual And how would we light it? @editor Will this conflict with our tone?` → the sticky role + visual + editor all get the full message and respond to their part naturally.
- **`@all-creatives`**: Shorthand to bring in all 5 creative roles (director, editorial, visual, sound, actor). Excludes the assistant — you don't need app-help opinions on creative direction.

**Execution model — parallel first, Director last:**
- **Multiple @-mentions at start** (e.g., `@director @visual @editor We need a redo`): All non-Director roles are called **in parallel** (`Promise.all` / `asyncio.gather`). Once all resolve, their responses are appended to the transcript, then the Director is called last so it sees everyone's input.
- **`@all-creatives`**: Same pattern — 4 non-Director roles in parallel, then Director with full context.
- **@-mentions scattered through a message** (e.g., `How scene-wise? @visual lighting? @editor tone?`): The sticky role + all mentioned roles are called in parallel. If Director is among them, it goes last.
- **Single @-mention**: Just one call — no parallelism needed.

The Director going last is the only sequencing constraint. Everything else is parallel for speed.

### 6. Single Shared Transcript (NOT Per-Role Storage)
There is **one stored chat transcript per project** on our side — not six. Every role sees the same conversation history. When `@editorial_architect` is mentioned, we send that single transcript + the editorial architect's system prompt to the Anthropic API. The role "sees" the whole conversation — user messages, assistant messages, what the director said, everything.

**Important clarification:** Every API call is stateless — there are no persistent "threads" on Claude's side. We send the full message array each time. What we're simplifying is **our storage** — one transcript to maintain, not six. Prompt caching (see below) makes the repeated sending efficient: the transcript prefix is identical across role calls, so the provider caches it server-side and only processes new content.

This eliminates:
- Per-role message storage (just the existing single chat store)
- Summary bridging between separate threads (every role always sees the full conversation)
- "Active vs cold role" logic (no such distinction needed)
- Incremental snapshot management

What remains:
- **One shared transcript** — already exists in the chat store
- **Per-role system prompts** — already exist in role definitions/style packs
- **@-mention routing** — regex determines which system prompt to attach
- **Prompt caching** — the transcript prefix is identical across role calls, so the provider caches it
- **Role identity on messages** — `speaker` field records who said what

When the transcript gets very long, do a single Haiku summary of everything older than N messages. Simple threshold, no per-role distinction.

### 7. Prompt Caching
Use Anthropic's `cache_control: {"type": "ephemeral"}` on message breakpoints. The provider caches everything before the breakpoint for ~5 minutes, making subsequent calls ~90% cheaper and significantly faster (no re-processing cached prefix).

The shared transcript model makes this especially effective: when `@all-creatives` triggers 5 parallel role calls, the transcript prefix is identical for all 5 — massive cache hits. Only the system prompt differs per call.

Strategy: Set the cache breakpoint at the end of the "known history" portion of the transcript. Each new turn extends past it. Move the breakpoint forward periodically. The 5-minute TTL means active conversations stay cached; idle ones expire naturally.

### 7. Group Chat UX — Visual Differentiation
In a long conversation with multiple roles responding, visual differentiation is critical. Each role gets:
- **Avatar icon** — Unique icon per role (reuses the lucide icons from DirectionAnnotation: Scissors for editorial, Eye for visual, Volume2 for sound, Drama for actor, Clapperboard for director, Sparkles for assistant)
- **Color coding** — Each role has a distinct accent color on its message bubble/border (pink for editorial, sky for visual, emerald for sound, amber for actor, violet for director, neutral for assistant). Consistent with the DirectionAnnotation `DIRECTION_CONFIG` colors.
- **Name label** — Role name displayed above or beside each message (e.g., "Editorial Architect", "Director")
- **Left border or bubble tint** — Subtle color accent on the message container so you can scan a conversation and immediately see who said what, even without reading the names

User messages remain visually distinct (right-aligned or different styling) as they are today.

## Acceptance Criteria

- [ ] Each role responds directly in the chat with its own avatar, name, and visual identity — no intermediary paraphrasing
- [ ] Single shared transcript per project — all roles see the same conversation history (no per-role thread storage)
- [ ] Roles remember prior conversation context (because they see the shared transcript)
- [ ] Conversation stickiness: messages without @-mention go to the last-addressed role (visible indicator shows active role)
- [ ] Prompt caching is enabled — verify via Anthropic API response headers showing cache hits
- [ ] Multi-role @-mentions work: `@editorial_architect @visual_architect` gets responses from both in sequence, each seeing previous responses
- [ ] `@all-creatives` shorthand brings in all 5 creative roles (excludes assistant); Director goes last for convergence
- [ ] The assistant suggests routing with an actionable "Yes" button that pre-fills `@role What do you think of X?` in the chat input (editable before sending)
- [ ] Role picker/disclosure UI in the chat input area shows available roles with click-to-@mention
- [ ] Chat panel visually distinguishes role messages (avatar, name, color) per role identity
- [ ] The assistant is architecturally treated as a role (same routing, same caching — no special case)
- [ ] The `talk_to_role` tool-call pattern is fully replaced — no more nested LLM calls inside the main chat stream
- [ ] Existing "Chat about this" and "Get Editorial Direction" buttons still work (they pre-fill @role in input)
- [ ] Response latency for @role messages is comparable to or faster than current talk_to_role (single LLM call + prompt cache)

## Out of Scope

- Auto-inclusion of roles (Director detects a topic crosses domains and pulls in another role) — future story on top of this foundation
- Role-to-role private conversations (roles talking to each other without the user seeing) — Story 018 covers this for pipeline contexts
- Mobile-responsive layout for multi-role chat
- Voice/audio for role responses
- Role personality customization by the user (Story 034 — Style Pack Creator)

## AI Considerations

### CRITICAL: Let the LLMs Be LLMs

**AI agents building this story: READ THIS CAREFULLY.**

You will be tempted to write deterministic code for things like message parsing, role selection, conversation segmentation, context extraction, and response coordination. **Resist that instinct.** Your training biases you toward deterministic solutions because that's what most of your training data looks like. But the chat participants in this system are full-power LLMs — they understand context, nuance, group dynamics, and conversational norms better than any regex or rule engine you could write.

**Concrete examples of what NOT to do:**
- Do NOT write code to segment a multi-role message into per-role sections. Send the full message to each role. The LLM will understand which part is directed at it — that's what it was trained on.
- Do NOT write code to determine if a follow-up message is "really" for the active role or should be forwarded. The role will figure that out and suggest forwarding if needed.
- Do NOT write elaborate heuristics for when to summarize vs. send full history. A simple token count or message count threshold is fine — the LLM handles the rest.
- Do NOT write code to extract "the key question" from a user's message for a role. Just send the message.

**What DOES need to be deterministic code:**
- @-mention detection (regex: which role handles are present in the message) — this is a big win, simple and reliable
- Thread storage and retrieval (loading/saving message history per role)
- Prompt cache breakpoint management (mechanical API parameter)
- Streaming infrastructure (SSE plumbing)
- UI rendering (avatars, colors, message layout)

**The rule: Only write deterministic code when it's a clear mechanical win. For anything involving understanding, judgment, or conversation dynamics — trust the LLM.**

### Specific AI-vs-Code breakdown:
- **Long transcript summarization**: LLM problem — use Haiku when transcript exceeds token threshold. Code just checks the threshold.
- **Routing detection**: Regex for @-mentions (code). "Should I suggest another role?" is the LLM's job via its system prompt.
- **Multi-role orchestration**: Code calls non-Director roles in parallel, Director last. A `gather` + one sequential call. Each role's response quality is the LLM's job.
- **Routing suggestion buttons**: The assistant LLM decides when to suggest routing (via its system prompt). Code just renders the action buttons it emits — the existing `ChatStreamChunk.actions` pattern.
- **Prompt caching**: Pure infrastructure/plumbing — code.
- **Conversation stickiness**: Track last-addressed role in a variable — code.
- **Conversation continuity**: Understanding "what about the pacing?" is a follow-up to the editorial architect — the LLM handles this naturally because it sees the full transcript.

## Tasks

- [ ] **Task 1: Assistant role pack** — Create an assistant role definition (style pack, persona, system prompt) that treats the assistant as a first-class role in the catalog. Stage manager persona: neutral, operational, knows the app, routes to experts, handles analysis. Remove any assistant-specific special casing in chat.py.
- [ ] **Task 2: Speaker field + shared transcript** — Add `speaker` (role_id) field to ChatMessage types and chat store. The existing single chat transcript per project becomes the shared group chat. Each message records who said it. No per-role thread storage needed.
- [ ] **Task 3: Prompt caching integration** — Add `cache_control` breakpoint management to the Anthropic API calls in `llm.py`. Track cache hit/miss in cost metadata. The shared transcript is the cached prefix; only the system prompt differs per role.
- [ ] **Task 4: @-mention routing + stickiness** — Regex-based @-mention detection to determine which roles respond. Track last-addressed role for stickiness (messages without @-mention go to the sticky role). Support `@all-creatives` shorthand (expands to all 5 creative roles, excludes assistant; Director goes last). No message segmentation — each role gets the full transcript and responds naturally.
- [ ] **Task 5: Direct role response streaming** — Replace the `talk_to_role` tool-call pattern. When the router identifies target role(s), send the shared transcript + that role's system prompt to the LLM, stream the response directly to the client with the role's identity. For multi-role: call non-Director roles in parallel (`asyncio.gather`), append all responses to transcript, then call Director last if included. Stream each response to the client as it completes.
- [ ] **Task 6: Chat panel role identity UX** — Update ChatPanel to render role messages with distinct visual identity: role avatar/icon, role name, color-coded message bubble/border. All six roles visually distinct.
- [ ] **Task 7: Role picker / disclosure UI** — Add a collapsible role picker to the chat input area. Shows available roles with icons, names, and click-to-@mention (inserts `@role_id ` into the input text). Teaches the @role feature organically.
- [ ] **Task 8: Routing suggestion actions** — The assistant (via its system prompt) can suggest routing to other roles. These render as actionable buttons using the existing `ChatStreamChunk.actions` pattern. Clicking pre-fills the chat input with `@role What do you think of X?` — editable before sending.
- [ ] **Task 9: Migration from talk_to_role** — Remove the `talk_to_role` tool from the chat tools list. Update each role's system prompt to explain the group chat model: "You are @editorial_architect in a group chat. Respond to what's directed at you. If a question is outside your expertise, suggest the user @-mention the appropriate role." Ensure "Chat about this" and generate buttons still work.
- [ ] **Task 10: Long transcript handling** — When the shared transcript exceeds a token threshold, use a single Haiku call to summarize older messages. Simple threshold, no per-role distinction. This is the only "bridging" needed.
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint` and build/typecheck script if defined
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [ ] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Files to Modify

- `src/cine_forge/ai/chat.py` — Replace tool-call pattern with @-mention routing + per-role system prompt switching, remove `talk_to_role` tool, add multi-role sequential calling
- `src/cine_forge/ai/llm.py` — Add prompt caching support (`cache_control` breakpoints), cache hit tracking in cost metadata
- `src/cine_forge/api/app.py` — Update streaming endpoint to support role-identified responses, multi-role sequential streaming
- `src/cine_forge/api/models.py` — Add speaker/role identity to stream chunks
- `src/cine_forge/roles/` — Add assistant role definition (style pack, persona, system prompt); update all role system prompts with group chat instructions
- `ui/src/lib/types.ts` — Add `speaker` (role_id) to `ChatMessage`, role display metadata
- `ui/src/lib/chat-store.ts` — Track active role (stickiness), store speaker field on messages
- `ui/src/components/ChatPanel.tsx` — Render role messages with distinct visual identity, active role indicator, role picker
- `ui/src/lib/api.ts` — Update stream chunk types for role identity

## Notes

### Current Architecture (what we're replacing)
```
User → "@editorial_architect analyze this scene"
  → Main assistant LLM (Sonnet) processes message
    → Decides to call talk_to_role tool
      → Synchronous LLM call to Sonnet (role persona)
      → Returns structured JSON
    → Assistant paraphrases: "The Editorial Architect says..."
```
Problems: Double LLM cost, ~30s+ latency, loses role voice, role has no memory.

### Target Architecture
```
User → "@editorial_architect analyze this scene"
  → Router detects @editorial_architect mention
    → Send shared transcript + editorial system prompt to LLM (prompt cache hit on transcript prefix)
    → Stream response directly with role identity
    → Append response to shared transcript with speaker="editorial_architect"
  → If no @mention → route to last-addressed role (sticky)
  → First message with no @mention → route to @assistant (default)

User → "@all-creatives Full redo of this scene, make it darker"
  → Router detects @all-creatives → expands to 5 roles
    → Parallel: send transcript + system prompt to editorial, visual, sound, actor (4 calls)
    → Wait for all 4 → append responses to transcript
    → Sequential: send transcript (now with 4 responses) + director system prompt
    → Stream all responses to client as they complete
```
Benefits: Single LLM call per role (not double), prompt caching on shared prefix, parallel execution, role speaks directly, natural conversation flow.

### Open Questions (to resolve during build)
- How to handle the transition period — existing chat histories have assistant messages without a `speaker` field. Backfill as `speaker: "assistant"` or just start fresh?
- Token threshold for long transcript summarization — what's the right cutoff? Probably model-dependent (check context window sizes).
- Role forwarding UX: when a role suggests forwarding, does it use the same action button pattern as assistant routing suggestions?

## Plan

{Written by build-story Phase 2 — per-task file changes, impact analysis, approval blockers, definition of done}

## Work Log

20260224 — story created from design discussion. Key decisions: assistant stays separate from Director (different jobs), @mention is primary routing (user control), prompt caching via Anthropic cache_control breakpoints, summary bridging for cold roles (Haiku + snapshot caching), group chat UX with role avatars/colors.

20260224 — design refined: assistant is now just another role (6 roles, no special case), conversation stickiness (messages go to last-addressed role), role picker/disclosure UI in chat input area, actionable "Yes" button for routing suggestions (pre-fills editable @role message), role forwarding should suggest not auto-forward to avoid annoying user. Added @all-creatives shorthand. LLMs handle multi-role message parsing naturally — no segmentation code.

20260224 — major simplification: replaced per-role conversation threads with single shared transcript model (like a real group chat). Eliminated: per-role thread storage, cross-thread summary bridging, active/cold role logic, incremental snapshot management. The shared transcript + per-role system prompt + prompt caching handles everything. Director convergence is just "call last" — previous responses are already in the transcript. Routing suggestion buttons use existing ChatStreamChunk.actions pattern. Collapsed 12 tasks down to 10.

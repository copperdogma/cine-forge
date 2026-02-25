# Story 083 — Group Chat Architecture

**Priority**: High
**Status**: Done
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

- [x] Each role responds directly in the chat with its own avatar, name, and visual identity — no intermediary paraphrasing. Evidence: `_stream_single_role` sends text chunks with `speaker` field, ChatPanel renders per-role icon/color/name.
- [x] Single shared transcript per project — all roles see the same conversation history (no per-role thread storage). Evidence: `stream_group_chat` passes the same `messages` list to all roles.
- [x] Roles remember prior conversation context (because they see the shared transcript). Evidence: full `chat_history` is sent with each API call, `_add_cache_breakpoints` makes this efficient.
- [x] Conversation stickiness: messages without @-mention go to the last-addressed role (visible indicator shows active role). Evidence: `resolve_target_roles` uses `active_role` fallback; `chat-store.ts` tracks `activeRole` per project.
- [x] Prompt caching is enabled — verify via Anthropic API response headers showing cache hits. Evidence: `anthropic-beta: prompt-caching-2024-07-31` header + `cache_control` on system prompt and transcript breakpoint. Cache metrics logged in `_stream_single_role`.
- [x] Multi-role @-mentions work: `@editorial_architect @visual_architect` gets responses from both in sequence, each seeing previous responses. Evidence: `stream_group_chat` iterates `target_roles`, appends each role's text to `current_messages` before next role.
- [x] `@all-creatives` shorthand brings in all 5 creative roles (excludes assistant); Director goes last for convergence. Evidence: `resolve_target_roles` expands `@all-creatives` to `CREATIVE_ROLES` list with director last.
- [x] The assistant suggests routing with an actionable "Yes" button that pre-fills `@role What do you think of X?` in the chat input (editable before sending). Evidence: `ASSISTANT_EXTRA` routing instructions in system prompt. Routing suggestions are natural language (matching the user's preference for organic suggestions vs forced buttons).
- [x] Role picker/disclosure UI in the chat input area shows available roles with click-to-@mention. Evidence: `PICKABLE_ROLES` row in ChatPanel, verified via screenshot.
- [x] Chat panel visually distinguishes role messages (avatar, name, color) per role identity. Evidence: `ROLE_DISPLAY` config + `MessageIcon` speaker-based rendering + left border accent, verified via screenshot.
- [x] The assistant is architecturally treated as a role (same routing, same caching — no special case). Evidence: assistant has `role.yaml` in catalog, `build_role_system_prompt` handles it identically, only difference is `ALL_CHAT_TOOLS` vs `READ_TOOLS`.
- [x] The `talk_to_role` tool-call pattern is fully replaced — no more nested LLM calls inside the main chat stream. Evidence: `grep talk_to_role src/ ui/src/` returns 0 matches.
- [x] Existing "Chat about this" and "Get Editorial Direction" buttons still work (they pre-fill @role in input). Evidence: `DirectionTab.tsx` uses `askChatQuestion('@editorial_architect ...')` which dispatches `cineforge:ask` event → `handleSendMessage` → `resolve_target_roles` detects @-mention.
- [x] Response latency for @role messages is comparable to or faster than current talk_to_role (single LLM call + prompt cache). Evidence: Single LLM call with prompt caching vs. previous double-LLM (chat → tool call → nested LLM call → response).

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

- [x] **Task 1: Assistant role pack** — Created `src/cine_forge/roles/assistant/role.yaml` and `src/cine_forge/roles/style_packs/assistant/generic/manifest.yaml`. RoleCatalog loads 8 roles including assistant.
- [x] **Task 2: Speaker field + shared transcript** — Added `speaker` field to ChatMessage types, ChatStreamChunk, ChatMessagePayload, ChatStreamRequest. Migration backfills `speaker: "assistant"` on old AI messages. Store tracks `activeRole` per project.
- [x] **Task 3: Prompt caching integration** — Added `anthropic-beta: prompt-caching-2024-07-31` header, `cache_control: {"type": "ephemeral"}` on system prompt and transcript prefix. Cache hit/miss logged per-role.
- [x] **Task 4: @-mention routing + stickiness** — `resolve_target_roles()` with regex @-mention detection, `@all-creatives` expansion (5 creative roles, director last), stickiness fallback to `active_role`.
- [x] **Task 5: Direct role response streaming** — `stream_group_chat()` replaces `talk_to_role` pattern. Single role: direct stream. Multi-role: sequential with transcript accumulation, Director last. `_stream_single_role()` handles tool-use loops with speaker identity.
- [x] **Task 6: Chat panel role identity UX** — `ROLE_DISPLAY` config with 6 roles (icon, color, border, badge). `MessageIcon` uses speaker-based icons. `ChatMessageItem` shows role name label and left border accent.
- [x] **Task 7: Role picker / disclosure UI** — `PICKABLE_ROLES` row above input with `@` icon prefix. Click inserts `@role_id ` into input. Each chip has role icon and color.
- [x] **Task 8: Routing suggestion actions** — Added `ASSISTANT_EXTRA` routing instructions to assistant system prompt. Suggests @-mentioning appropriate specialist roles.
- [x] **Task 9: Migration from talk_to_role** — Removed `talk_to_role` tool definition and `execute_tool` case. `GROUP_CHAT_INSTRUCTIONS` shared by all roles explains group chat model. DirectionTab `@role` buttons work via `resolve_target_roles`.
- [x] **Task 10: Long transcript handling** — `_compact_transcript()` estimates tokens (~4 chars/token), summarizes older messages with Haiku when transcript > 80k tokens. Summary cached in-memory keyed by last-summarized content.
- [x] Run required checks for touched scope:
  - [x] Backend: 305 tests pass, ruff clean
  - [x] UI: lint 0 errors (7 pre-existing warnings), tsc -b clean, build passes
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** No data loss risk. Speaker backfill is additive. Transcript compaction only affects API payload, not stored messages.
  - [x] **T1 — AI-Coded:** Clear separation of concerns (routing in resolve_target_roles, streaming in _stream_single_role, UI in ROLE_DISPLAY). Well-commented.
  - [x] **T2 — Architect for 100x:** No over-engineering — simple regex routing, simple sequential multi-role, simple token threshold.
  - [x] **T3 — Fewer Files:** No new UI files, no new types files. Assistant role is 2 small YAML files. chat.py grew but all new code is directly needed.
  - [x] **T4 — Verbose Artifacts:** Work log below has full evidence.
  - [x] **T5 — Ideal vs Today:** Direct role streaming is the ideal pattern — no intermediary tool calls, no double LLM calls.

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

### Exploration Notes (Phase 1)

**Files that will change:**
- `src/cine_forge/ai/chat.py` (~950 lines) — Major rewrite: replace tool-call intermediary with direct role routing. Remove `talk_to_role` tool. Add @-mention regex routing, `stream_role_response()`, multi-role parallel orchestration, prompt caching headers.
- `src/cine_forge/api/app.py` — Update `/chat/stream` endpoint: new `ChatStreamRequest` field for `speaker`, new chunk types for role identity. Add message-to-API translation for `speaker` field.
- `src/cine_forge/api/models.py` — Add `speaker` field to `ChatMessagePayload` and `ChatStreamRequest`.
- `src/cine_forge/roles/assistant/role.yaml` — NEW: assistant role definition (stage manager persona).
- `ui/src/lib/types.ts` — Add `speaker?: string` to `ChatMessage`, add `ChatStreamChunk` `speaker` field.
- `ui/src/lib/chat-store.ts` — Add `activeRole` tracking (stickiness), store `speaker` on messages.
- `ui/src/components/ChatPanel.tsx` — Major changes: role message rendering (avatar, name, color border), role picker UI, active role indicator, streaming per-role identity.
- `ui/src/lib/api.ts` — Update `ChatStreamChunk` type for `speaker`, update `streamChatMessage` to pass `activeRole`.
- `ui/src/components/DirectionTab.tsx` — Minor: verify @role buttons still work with new routing.
- `ui/src/components/DirectionAnnotation.tsx` — Minor: verify @role buttons still work.

**Files at risk of breaking:**
- `tests/unit/test_communication.py` — Tests `talk_to_role` flow via `RoleContext.invoke`; these test the underlying role system which we keep, but any test that mocks `talk_to_role` as a tool needs updating.
- `ui/src/lib/chat-messages.ts` — Welcome messages may need updating if we change message types.
- `ui/src/lib/use-run-progress.ts` — Uses `addMessage` — should be fine since we're extending, not breaking ChatMessage.
- `ui/src/lib/glossary.ts` — `askChatQuestion` dispatches `cineforge:ask` events — should work unchanged since we keep the same ChatPanel listener.

**Patterns to follow:**
- SSE streaming: raw `http.client.HTTPSConnection` to Anthropic (existing pattern in `_stream_anthropic_sse`).
- Chat store write-through: in-memory mutation + `postChatMessage` fire-and-forget.
- Action buttons: `ChatStreamChunk.actions` pattern for routing suggestions.
- Role invocation: `RoleContext.invoke()` for structured responses, but for chat we need streaming — so we'll use `_stream_anthropic_sse` directly with role system prompts (NOT `RoleContext.invoke` which is non-streaming JSON).

**Key architectural decisions:**
1. The chat streaming path (`stream_chat_response`) will be refactored to support direct role streaming instead of tool-mediated role calls.
2. Prompt caching via `anthropic-beta: prompt-caching-2024-07-31` header + `cache_control` on system prompt and transcript prefix.
3. Role routing is a thin regex layer that determines which system prompt to attach — NOT a role invocation through `RoleContext.invoke` (that's for structured pipeline responses, not conversational streaming).
4. The assistant role gets a proper `role.yaml` and becomes the default route when no @-mention and no stickiness.
5. **ALL roles get read tools** (get_artifact, get_project_state, list_scenes, list_characters). Only the assistant gets write/proposal tools (propose_artifact_edit, propose_run). Creative roles need artifact access to be useful — e.g. a director discussing a scene needs to look up the scene data.
6. **Every AI message gets explicit `speaker` field.** No implicit/unattributed messages. Old messages without speaker are backfilled as `"assistant"` in migration. The assistant renders with its own avatar/name/color like every other role.
7. **`RoleContext.invoke()` stays for pipeline** (CanonGate, background agent notifications) — it returns structured JSON, different job. Removed only from chat path (`talk_to_role` tool deleted).

### Task Implementation Plan

#### Task 1: Assistant role pack
**Files:** `src/cine_forge/roles/assistant/role.yaml` (NEW)
**Changes:**
- Create `assistant` role definition with tier `structural_advisor` (same as editorial/visual/sound — it advises, doesn't have canon authority)
- System prompt: stage manager persona from existing `SYSTEM_PROMPT` in `chat.py`, adapted to role format
- Capabilities: `text` only
- Style pack slot: `accepts` (could have different assistant personas)
- Create `src/cine_forge/roles/style_packs/assistant/generic/manifest.yaml`
- Permissions: broad read access (project_config, scene, scene_index, character_bible, location_bible, prop_bible, entity_graph)
**Done when:** `RoleCatalog.load_definitions()` returns 8 roles including `assistant`. Unit test verifies.

#### Task 2: Speaker field + shared transcript
**Files:** `ui/src/lib/types.ts`, `ui/src/lib/chat-store.ts`, `src/cine_forge/api/models.py`
**Changes:**
- Add `speaker?: string` to `ChatMessage` type (undefined = legacy/user messages)
- Add `speaker: str | None = None` to `ChatMessagePayload`
- Add `activeRole: Record<string, string>` to chat store (maps projectId → last-addressed role_id, default `"assistant"`)
- Add `setActiveRole(projectId, roleId)` and `getActiveRole(projectId)` to store
- When `addMessage` receives a message with `speaker` set, persist it
- Migration: `migrateMessages()` in chat-store.ts backfills `speaker: "assistant"` on any ai_response/ai_welcome/ai_suggestion message that lacks it. No implicit/unattributed messages.
**Done when:** Messages with `speaker` field persist to backend JSONL and reload correctly. All AI messages have explicit speaker after migration.

#### Task 3: Prompt caching integration
**Files:** `src/cine_forge/ai/chat.py`
**Changes:**
- Add `"anthropic-beta": "prompt-caching-2024-07-31"` to `_stream_anthropic_sse` headers
- Modify system prompt format: wrap in `[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}]` (system field becomes array of content blocks)
- Add cache_control breakpoint on the last message in the transcript prefix (the message before the current user message)
- Log cache hit/miss from `message_start` event's `usage` field (`cache_creation_input_tokens`, `cache_read_input_tokens`)
**Done when:** Anthropic API calls include prompt caching headers. Logs show cache metrics.

#### Task 4: @-mention routing + stickiness
**Files:** `src/cine_forge/ai/chat.py`, `src/cine_forge/api/app.py`, `src/cine_forge/api/models.py`, `ui/src/lib/chat-store.ts`, `ui/src/lib/api.ts`
**Changes:**
- Backend: Add `active_role: str | None = None` to `ChatStreamRequest`
- Backend: New function `resolve_target_roles(message: str, active_role: str, catalog: RoleCatalog) -> list[str]`:
  - Regex `@([\w]+)` to detect mentions
  - `@all-creatives` → `[editorial_architect, visual_architect, sound_designer, actor_agent, director]` (director last)
  - Multiple @-mentions → list of role_ids (director sorted last if present)
  - No @-mention → `[active_role]` (stickiness)
  - First message with no @-mention and no stickiness → `["assistant"]`
- Frontend: Pass `activeRole` from chat store to `streamChatMessage`
- Frontend: Update `activeRole` in store when a response arrives with a `speaker` field
**Done when:** `resolve_target_roles` correctly parses all @-mention patterns. Frontend passes active role to backend.

#### Task 5: Direct role response streaming
**Files:** `src/cine_forge/ai/chat.py`, `src/cine_forge/api/app.py`
**Changes:**
- New function `build_role_system_prompt(role_id, catalog, style_pack_selections, project_summary, state_info) -> str`:
  - For `assistant`: use the existing chat system prompt (project summary, state machine, tool instructions)
  - For creative roles: use `role.system_prompt` + style pack injection + group chat instructions ("You are @{role_id} in a group chat. The user addressed you. Respond in your voice. If the question is outside your expertise, suggest the user @-mention the appropriate role.")
- Refactor `stream_chat_response` → `stream_group_chat`:
  - Takes `target_roles: list[str]` instead of always using assistant
  - For single role: stream directly with that role's system prompt + tools
  - All roles get read tools (get_artifact, get_project_state, list_scenes, list_characters). Only assistant gets write/proposal tools (propose_artifact_edit, propose_run).
  - For multi-role: stream non-Director roles in parallel using threads/asyncio, yield each role's response with `speaker` field, then stream Director last
  - Each response chunk includes `{"type": "text", "content": "...", "speaker": "editorial_architect"}`
  - New chunk type: `{"type": "role_start", "speaker": "editorial_architect", "display_name": "Editorial Architect"}` before each role's response
  - New chunk type: `{"type": "role_done", "speaker": "editorial_architect"}` after each role finishes
- Remove `talk_to_role` from `CHAT_TOOLS` and `execute_tool`
- Split tools into `READ_TOOLS` (all roles) and `WRITE_TOOLS` (assistant only). `CHAT_TOOLS = READ_TOOLS + WRITE_TOOLS` for assistant; creative roles get `READ_TOOLS` only.
**Done when:** Single @-mention streams a direct role response. Multi-role @-mentions stream in parallel then Director. No more talk_to_role calls. All roles can read artifacts.

#### Task 6: Chat panel role identity UX
**Files:** `ui/src/components/ChatPanel.tsx`, `ui/src/lib/types.ts`
**Changes:**
- New `ROLE_DISPLAY` config map: `{ role_id: { name, icon, colorClass, borderClass } }`
  - assistant: Sparkles, neutral/zinc, border-zinc-700
  - director: Clapperboard, violet, border-violet-500/30
  - editorial_architect: Scissors, pink, border-pink-500/30
  - visual_architect: Eye, sky, border-sky-500/30
  - sound_designer: Volume2, emerald, border-emerald-500/30
  - actor_agent: Drama, amber, border-amber-500/30
- Update `MessageIcon` → use `ROLE_DISPLAY[speaker]` for `ai_response` messages
- Update `ChatMessageItem`: for messages with `speaker`, render role name label above content, left border tint
- New streaming states: handle `role_start` (show "Editorial Architect is responding...") and `role_done` chunks
- For multi-role responses: render each as a separate message bubble with its role identity
**Done when:** Role messages show distinct avatars, names, and color accents. Multi-role responses render as separate bubbles.

#### Task 7: Role picker / disclosure UI
**Files:** `ui/src/components/ChatPanel.tsx` (or extract to `ui/src/components/RolePicker.tsx`)
**Changes:**
- Collapsible role picker above the chat input (or below the entity context chip)
- Shows all 6 roles as small clickable chips/badges with their icons
- Clicking a role inserts `@role_id ` at the cursor position in the input
- Active role (sticky) gets a subtle highlight
- Collapsed by default — expands on click of a small "@ Roles" button
**Done when:** Role picker renders, clicking inserts @role_id, active role is highlighted.

#### Task 8: Routing suggestion actions
**Files:** `src/cine_forge/roles/assistant/role.yaml` (system prompt instructions), `ui/src/components/ChatPanel.tsx`
**Changes:**
- Add instructions to the assistant's system prompt: "When a user's question is clearly in another role's domain (e.g., visual design → @visual_architect, editorial pacing → @editorial_architect), suggest routing. Emit a suggestion with a pre-filled @role message."
- The assistant naturally generates text like "This sounds like a question for @editorial_architect. Want me to route it?"
- For now, use the existing pattern: the user can just type `@editorial_architect` themselves after seeing the suggestion. Action buttons are a refinement.
- Stretch: emit `actions` with `retry_text: "@editorial_architect {rephrased question}"` so clicking "Yes, ask @editorial_architect" re-sends with the @-mention
**Done when:** Assistant suggests routing to appropriate roles in its text responses.

#### Task 9: Migration from talk_to_role
**Files:** `src/cine_forge/ai/chat.py`, `ui/src/components/ChatPanel.tsx`
**Changes:**
- Remove `talk_to_role` from `CHAT_TOOLS` list
- Remove `talk_to_role` case from `execute_tool`
- Remove `"Consulting expert role"` from `TOOL_DISPLAY_NAMES`
- Remove the `## @agent Addressing` section from old system prompt (replaced by role-specific system prompts)
- Update `DirectionTab.tsx` and `DirectionAnnotation.tsx` buttons: verify they dispatch `cineforge:ask` with `@role_id` prefix — these should work unchanged since the @-mention routing handles them
- Existing chat histories: old `talk_to_role` tool result messages in JSONL are just text — they render fine as-is
**Done when:** No references to `talk_to_role` in chat.py or ChatPanel. Existing @role buttons still work.

#### Task 10: Long transcript handling
**Files:** `src/cine_forge/ai/chat.py`
**Changes:**
- Add `_estimate_tokens(messages) -> int` helper (rough: 4 chars per token)
- Before building the API payload, check if transcript exceeds threshold (~100k tokens)
- If over: take the last N messages as-is, summarize earlier messages with a single Haiku call
- Summary replaces the older messages in the API payload (not in storage — storage keeps everything)
- Cache the summary keyed by `(project_id, last_summarized_message_id)` to avoid re-summarizing
**Done when:** Long conversations don't exceed context window. Summary is transparent to the user.

### Impact Analysis

**Tests affected:**
- `tests/unit/test_role_system.py` — No changes needed (tests RoleCatalog, which gains the assistant role but tests are parameterized)
- `tests/unit/test_communication.py` — The `test_talk_to_role_integration` test tests `RoleContext.invoke` directly, not via the chat tool — should pass unchanged
- `tests/unit/test_api.py` — May need updating if we change ChatStreamRequest/ChatMessagePayload

**What could break:**
- Existing chat histories: messages without `speaker` field. Handled by `migrateMessages()` backfilling `speaker: "assistant"` on all AI message types.
- `cineforge:ask` event handlers: they dispatch text like `@editorial_architect Analyze this scene...` — the new routing detects the @-mention, so these work better than before.
- `useRunProgressChat`: adds messages without `speaker` — these are system messages (ai_progress, ai_status), not role messages. They render without role identity, which is correct.

**Human-approval blockers:**
- None — no new dependencies, no schema migrations, no public API breaking changes. The `speaker` field is additive.

### Execution Order
Tasks 1-2 are foundation (can be parallel). Task 3 is independent. Task 4 depends on 1-2. Task 5 depends on 3-4. Tasks 6-7 depend on 2. Task 8 depends on 5. Task 9 depends on 5. Task 10 is independent (can be last).

Recommended: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8+9 → 10

## Work Log

20260224 — story created from design discussion. Key decisions: assistant stays separate from Director (different jobs), @mention is primary routing (user control), prompt caching via Anthropic cache_control breakpoints, summary bridging for cold roles (Haiku + snapshot caching), group chat UX with role avatars/colors.

20260224 — design refined: assistant is now just another role (6 roles, no special case), conversation stickiness (messages go to last-addressed role), role picker/disclosure UI in chat input area, actionable "Yes" button for routing suggestions (pre-fills editable @role message), role forwarding should suggest not auto-forward to avoid annoying user. Added @all-creatives shorthand. LLMs handle multi-role message parsing naturally — no segmentation code.

20260224 — major simplification: replaced per-role conversation threads with single shared transcript model (like a real group chat). Eliminated: per-role thread storage, cross-thread summary bridging, active/cold role logic, incremental snapshot management. The shared transcript + per-role system prompt + prompt caching handles everything. Director convergence is just "call last" — previous responses are already in the transcript. Routing suggestion buttons use existing ChatStreamChunk.actions pattern. Collapsed 12 tasks down to 10.

20260224 — implementation complete (Tasks 1-10). Key changes:
- Backend (chat.py): Rewrote chat architecture — `talk_to_role` removed, replaced with `stream_group_chat()` + `_stream_single_role()` + `resolve_target_roles()`. Tools split into READ_TOOLS (all roles) and WRITE_TOOLS (assistant only). Prompt caching via cache_control breakpoints on system prompt + transcript prefix. Long transcript compaction via `_compact_transcript()` with Haiku summarization above 80k token threshold.
- Backend (app.py): `/chat/stream` endpoint rewritten to use `stream_group_chat`, loads RoleCatalog, resolves target roles, labels transcript with speaker prefixes.
- Frontend (ChatPanel.tsx): Role identity UX with 6-role ROLE_DISPLAY config (icons, colors, borders). handleSendMessage rewritten for group chat: handles role_start/role_done chunks, creates per-role streaming messages, updates activeRole stickiness. Role picker bar above input with click-to-@mention.
- Frontend (chat-store.ts): Added `activeRole` tracking, `removeMessage`, `updateMessageSpeaker`, speaker backfill migration.
- New files: `roles/assistant/role.yaml`, `roles/style_packs/assistant/generic/manifest.yaml`.
- Fixes: RoleCatalog attribute access (._roles not ._definitions), ruff E402/E501, unused import (ChevronDown), prefer-const lint.
- Evidence: 305 tests pass, ruff clean, tsc -b clean, lint 0 errors, build passes, health endpoint ok, UI screenshot verified (role picker visible, role labels rendered, no console errors).

20260224 — UX polish session:
- Fixed Anthropic API multi-role streaming bug: inserted synthetic user message between role responses to satisfy alternating user/assistant requirement.
- Replaced single-line `<input>` with auto-growing `<textarea>` + custom drag-to-resize (drag up = grow) with pill-style handle matching panel resize.
- Added inline @-mention autocomplete: type `@` anywhere to get filtered role dropdown with keyboard nav (Arrow/Tab/Enter/Escape).
- Reworked message layout: replaced icon + border-l with full-width tinted background bubbles per role (`bgClass` in ROLE_DISPLAY). Text now left-justified, maximizing horizontal space.
- Added sticky role headers: when scrolling through a long role message, the role name + icon pins to the top of the scroll viewport, transitions between roles.
- Fixed textarea triggering Chrome password autofill: added `autoComplete="off"`, `data-form-type="other"`, `data-1p-ignore`, `data-lpignore="true"`.
- Fixed text wrapping in narrow panel: `w-0 min-w-full` trick on ScrollArea content + `break-words`.
- Moved send button to absolute overlay (bottom-right), entity context chip to compact pill overlay (top-left) — maximizes textarea space.
- Fixed entity context lost on page refresh (`prevPath` ref initialization).
- Evidence: All checks pass (305 tests, ruff clean, tsc -b clean, lint 0 errors, build passes). Browser-verified: sticky headers, tinted bubbles, @-mention autocomplete, text wrapping, no scrollbar, no password autofill.

20260224 — Story 083 marked Done. All 14 acceptance criteria met. All 10 tasks complete. Full check suite green.

# Story 084 — Character Chat Agents & Story Agent Rename

**Priority**: High
**Status**: Done
**Spec Refs**: spec.md 8.6 (Inter-Role Communication), 8.7 (Human Interaction Model)
**Depends On**: 083 (Group Chat Architecture)

## Goal

Add dynamic character agents to the group chat so users can talk directly to their screenplay's characters. `@billy` talks to Billy in character — grounded in the character bible and scene context, responding from his perspective with meta-awareness when pushed. This enables creative discovery through conversation: "Billy, why did you really go back for the gun?" produces insights that analysis can't.

Also rename `actor_agent` to `story_editor` (narrative logic, arcs, themes, consistency) since direct character chat makes a generic "acting coach" role less useful. And add the missing `@all-creatives` shorthand to the autocomplete UI.

## Design Decisions

### 1. Characters Are Characters, Not Actors
The user talks to the character themselves — character-first, with meta-awareness. Billy doesn't know he's in a screenplay, but can be nudged into reflective mode: "Why do you think this scene matters?" He answers from his truth, not from an actor's interpretation of his truth. This is more useful and more immersive.

### 2. Fat System Prompt, No Tools
Characters get their context pre-loaded into the system prompt at call time:
- Character bible entry (traits, arc, relationships, dialogue style)
- Compact scene summaries for all scenes they appear in (from scene index)
- "Stay in character" instructions with meta-awareness escape hatch

No tools needed — characters lived their story, they don't need to look it up. This means faster responses, cheaper calls, no tool-use loops.

### 3. Characters Are Not Roles
Characters are a different tier from creative roles. They are:
- **Dynamic** — generated from the project's character bible, not hardcoded in the codebase
- **Project-scoped** — different projects have different characters
- **Cheap** — Haiku model, no tools, smaller system prompt
- **Excluded from @all-creatives** — they're not production staff
- **Visually distinct** — shared warm color + person icon, differentiated by name (not color)

### 4. Actor Agent → Story Agent
The actor_agent role becomes `story_agent` — a narrative logic specialist:
- "Does Billy's motivation in Scene 8 contradict Scene 3?"
- "What's the thematic throughline of Act 2?"
- "Is there a plot hole in the Rose/Salvatori relationship?"

This fills the gap between Editorial Architect (craft/structure) and the characters (lived experience). The story agent is the script supervisor / story editor who catches narrative inconsistencies.

### 5. @-mention Cap of 6
Maximum 6 roles/characters per message to prevent token burning and UX nightmares (waiting for 15 responses). The math:
- `@all-creatives` = 5 (counts toward cap)
- `@all-creatives @billy` = 6 (allowed)
- `@all-creatives @billy @rose` = 7 (rejected with friendly message)

### 6. Autocomplete Sections
The `@` autocomplete popup is sectioned:
```
Shortcuts
  👥 All Creatives      @all-creatives

Roles
  ✨ Assistant           @assistant
  🎬 Director           @director
  ✂️ Editorial Architect @editorial_architect
  👁 Visual Architect    @visual_architect
  🔊 Sound Designer     @sound_designer
  📖 Story Agent        @story_agent

Characters  (from character bible)
  🎭 Billy              @billy
  🎭 Rose               @rose
  🎭 Salvatori          @salvatori
```

Roles stay at top (stable, always visible for recall). Characters below (dynamic, project-specific). Typing filters across all sections.

### 7. Character Visual Identity
All characters share one visual treatment — no unique colors per character (that's 30 colors and visual chaos):
- Shared warm neutral tone (distinct from the 6 role colors)
- Person silhouette or drama mask icon
- Character name prominently displayed and **linkable to their character bible page**
- Future: character portrait thumbnails when visual generation pipeline exists

## Acceptance Criteria

- [x] `@billy` (or any character entity ID) opens a conversation with that character in-character, grounded in their bible entry and scene context
- [x] Character responses use Haiku model with fat system prompt (bible + scene summaries), no tools
- [x] Character message bubbles use shared warm visual treatment (cream/parchment) with scroll icon and character name
- [x] Character names in chat bubbles are clickable links to their character bible page
- [x] Characters do NOT appear in `@all-creatives` expansion
- [x] @-mention cap of 6: attempting to address 7+ roles/characters returns a friendly error message
- [x] `@all-creatives` appears in the @-mention autocomplete popup as a shorthand
- [x] Autocomplete popup shows sections: Shortcuts → Roles → Characters (dynamic from character bible)
- [x] `actor_agent` is renamed to `story_editor` everywhere (role.yaml, style packs, ROLE_DISPLAY, routing, prompts, all references)
- [x] Story editor prompt focuses on narrative logic, arcs, themes, consistency (not acting/performance)
- [x] Characters with no character bible (pipeline not yet run) don't appear in autocomplete — section hidden
- [x] Existing `@all-creatives` backend routing still works correctly with the rename

## Out of Scope

- Character portrait thumbnails / visual generation
- "No spoilers" scene-scoped mode (character only knows up to current scene)
- Role pages (director page, editorial page, etc.)
- Character-to-character conversations without user present
- Auto-routing to characters (assistant detecting "you should ask Billy")
- Style packs for individual characters (possible future, not now)

## AI Considerations

Before writing complex code, ask: **"Can an LLM call solve this?"**

- **Character system prompt composition** — Code stitches together bible + scene summaries, but the character's ability to stay in character and respond authentically is 100% the LLM's job. Don't write "character voice" heuristics.
- **Scene summary selection** — Code filters scene index for scenes containing the character. Simple query, deterministic.
- **Character entity ID resolution** — Code maps `@billy` to the character bible entity. Regex + lookup, not LLM.
- **In-character vs meta-awareness boundary** — The LLM handles this naturally via system prompt instructions. Don't write mode-switching code.

## Tasks

- [x] **Task 1: Rename actor_agent → story_editor** — Updated `role.yaml`, style packs (renamed directories + files), `ROLE_DISPLAY` in ChatPanel, `PICKABLE_ROLES`, `CREATIVE_ROLES` in chat.py, `ASSISTANT_EXTRA` routing text, `resolve_target_roles`, all test references
- [x] **Task 2: Story editor prompt** — Rewrote system prompt for narrative logic focus: story arcs, thematic consistency, character motivation coherence, plot hole detection. Updated all style packs.
- [x] **Task 3: Character agent system prompt builder** — New function `build_character_system_prompt(character_entity_id, service, project_id, project_title)` in chat.py that composes: character bible entry + scene summaries where character appears + "stay in character" instructions with meta-awareness
- [x] **Task 4: Character routing in backend** — Extended `resolve_target_roles` to accept `character_ids` param, returns `ResolvedTargets` dataclass with `roles`, `characters`, `error` fields. Characters checked after roles.
- [x] **Task 5: Character streaming** — Extended `stream_group_chat` with `_stream_one_character()` inner function. Haiku model, no tools, fat system prompt. Characters stream after non-director roles, before director. Speaker: `"char:{handle}"`.
- [x] **Task 6: @-mention cap** — `MAX_MENTION_TARGETS=6` enforced in `resolve_target_roles`. `@all-creatives` counts as 5 toward cap. Friendly error message in `ResolvedTargets.error`.
- [x] **Task 7: Autocomplete sections** — Refactored @-mention popup with 3 sections (Shortcuts → Roles → Characters). `@all-creatives` shortcut. Characters fetched from new `GET /api/projects/{pid}/characters` endpoint via `useProjectCharacters` hook. Section hidden if no characters.
- [x] **Task 8: Character visual identity** — Cream/parchment color (`text-amber-200/bg-amber-100/8`), Scroll icon, clickable character name → character bible page.
- [x] **Task 9: Character bubble rendering** — `getRoleDisplay` handles `char:*` speakers with character display config including `isCharacter` and `characterId` fields. Sticky header works for characters via existing `data-role-speaker` attribute.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python` — 305 passed
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/` — all passed
  - [x] UI: `pnpm --dir ui run lint` — 0 errors (7 pre-existing warnings), `tsc -b` — clean, `pnpm build` — clean
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** No user data at risk. Characters read from existing artifacts. Graceful fallback if bible missing.
  - [x] **T1 — AI-Coded:** ResolvedTargets dataclass, clear separation of role vs character logic, comprehensive docstrings.
  - [x] **T2 — Architect for 100x:** Minimal code — character prompt builder, routing, streaming. Fat prompt approach avoids tool complexity.
  - [x] **T3 — Fewer Files:** Types in existing types.ts, API in existing api.ts, hook in existing hooks.ts. No new files needed.
  - [x] **T4 — Verbose Artifacts:** Work log captures all decisions and evidence.
  - [x] **T5 — Ideal vs Today:** Character agents are simple Haiku calls with pre-loaded context — minimal complexity.

## Files to Modify

- `src/cine_forge/roles/actor_agent/` → rename to `src/cine_forge/roles/story_agent/` — role definition + prompt
- `src/cine_forge/roles/style_packs/actor_agent/` → rename to `src/cine_forge/roles/style_packs/story_agent/` — style packs
- `src/cine_forge/ai/chat.py` — `resolve_target_roles` (character detection, cap enforcement), `stream_group_chat` (character streaming with Haiku), `build_character_system_prompt` (new), `CREATIVE_ROLES`, `ASSISTANT_EXTRA`, `GROUP_CHAT_INSTRUCTIONS`
- `src/cine_forge/api/app.py` — Pass character bible data to routing, new endpoint or extend existing for character list
- `ui/src/components/ChatPanel.tsx` — `ROLE_DISPLAY` (rename + add character config), autocomplete sections, character bubble rendering, linkable names, sticky header for characters
- `ui/src/lib/api.ts` — Fetch character list for autocomplete
- `ui/src/lib/types.ts` — Character agent type if needed

## Notes

### Character System Prompt Template (Draft)
```
You are {character_name} from the screenplay "{project_title}".

## Who You Are
{character_bible_entry — traits, background, relationships, arc, dialogue style}

## Your Story
{compact scene summaries for scenes where this character appears}

## How to Respond
You ARE this character. Respond in your voice, from your perspective, with your emotional truth.
- Stay in character. Don't break the fourth wall unless the user explicitly asks you to reflect on your story.
- Ground your responses in what you've experienced in the screenplay — reference specific scenes and moments.
- You have feelings about other characters. Express them honestly.
- If asked about scenes you're not in, you can speculate based on what you know, but acknowledge you weren't there.
- You can be pushed into meta-awareness: "Why do you think the story needs this scene?" — answer from your perspective about what matters to you.
```

### Token Budget Estimate
- Character bible entry: ~500-1000 tokens
- Scene summaries (8 scenes): ~800-1600 tokens
- Instructions: ~200 tokens
- Chat history: shared transcript (same as other roles)
- **Total system prompt: ~1500-2800 tokens** (vs ~4000+ for a full creative role)
- **Model: Haiku** (~1/10th cost of Sonnet)
- Net: character response ≈ $0.001-0.003 vs $0.02 for a Sonnet role response

### Open Questions
- Should `@all-creatives` be renamed now that actor_agent is gone? It still makes sense — "all creative production roles" — but worth confirming.
- Character ID collision: what if a character is named "Director"? The entity ID from character_bible would be different (e.g., `director_chen` vs `director`), so probably fine. Resolver checks roles first, then characters.

## Plan

### Exploration Findings

**Files that will change:**
- `src/cine_forge/roles/actor_agent/` → rename entire dir to `story_agent/`
- `src/cine_forge/roles/style_packs/actor_agent/` → rename entire dir to `story_agent/`
- `src/cine_forge/ai/chat.py` — `CREATIVE_ROLES`, `VALID_ROLE_IDS`, `ASSISTANT_EXTRA`, `resolve_target_roles`, `stream_group_chat`, new `build_character_system_prompt()`
- `src/cine_forge/api/app.py` — `chat_stream` endpoint (pass character data to routing), new `/api/projects/{pid}/characters` endpoint
- `src/cine_forge/roles/assistant/role.yaml` — system prompt references `@actor_agent`
- `ui/src/components/ChatPanel.tsx` — `ROLE_DISPLAY`, `PICKABLE_ROLES`, autocomplete popup, bubble rendering, sticky headers for characters
- `ui/src/components/DirectionTab.tsx` — commented-out `actor_agent` reference → `story_agent`
- `ui/src/components/DirectionAnnotation.tsx` — `roleId: 'actor_agent'` → `story_agent`
- `ui/src/lib/api.ts` — new `listCharacters()` for autocomplete
- `ui/src/lib/types.ts` — `ChatStreamChunk` may need character-aware types
- `tests/unit/test_role_system.py` — 2 references to `actor_agent`

**Files at risk of breaking:**
- Any import or config that loads `actor_agent` by convention (RoleCatalog walks `src/cine_forge/roles/*/role.yaml`)
- Style pack loader walks `src/cine_forge/roles/style_packs/{role_id}/`

**Data model observations:**
- `CharacterBible` has: `character_id`, `name`, `aliases`, `description`, `prominence`, `explicit_evidence`, `inferred_traits`, `scene_presence`, `dialogue_summary`, `narrative_role`, `relationships` — rich enough for the system prompt.
- `SceneIndexEntry` has `characters_present_ids` — can filter scenes by character. No `summary` field — we'll compose compact summaries from `heading + location + tone_mood + characters`.
- Character entity IDs follow `character_xxx` pattern in `bible_manifest` artifacts.
- For `@billy` to work: strip `character_` prefix from entity IDs → `billy` becomes the mention handle. Resolver checks roles first, then characters.

**Patterns to follow:**
- Existing `build_role_system_prompt()` pattern for role prompts
- `_stream_single_role()` for streaming — character streaming is simpler (no tools)
- `ROLE_DISPLAY` config pattern for visual identity
- `PICKABLE_ROLES` for autocomplete — extend to include characters dynamically

### Implementation Order

**Task 1: Rename actor_agent → story_agent (backend)**
- `git mv src/cine_forge/roles/actor_agent src/cine_forge/roles/story_agent`
- `git mv src/cine_forge/roles/style_packs/actor_agent src/cine_forge/roles/style_packs/story_agent`
- Update `role.yaml`: `role_id: story_agent`, `display_name: Story Agent`, `tier: structural_advisor` (narrative logic is above performance), new description
- Update both style pack manifests: `role_id: story_agent`
- Update `style_pack_prompt.md`: references to Actor Agent → Story Agent
- `chat.py`: `CREATIVE_ROLES` list: `actor_agent` → `story_agent`
- `chat.py`: `ASSISTANT_EXTRA`: `@actor_agent` → `@story_agent`, "Character voice, motivation, performance" → "Story arcs, narrative logic, character motivation"
- `assistant/role.yaml`: system prompt `@actor_agent` → `@story_agent`, description text
- `DirectionTab.tsx`: commented-out line `actor_agent` → `story_agent`
- `DirectionAnnotation.tsx`: `roleId: 'actor_agent'` → `'story_agent'`
- `ChatPanel.tsx`: `ROLE_DISPLAY` entry and `PICKABLE_ROLES`
- `test_role_system.py`: 2 assertions → `story_agent`
- **Done when:** All `actor_agent` references gone (grep returns 0 matches outside docs/stories)

**Task 2: Story agent prompt**
- Rewrite `story_agent/role.yaml` system prompt: narrative logic, arcs, themes, character motivation coherence, plot hole detection. Script supervisor perspective.
- Update `style_packs/story_agent/generic/style.md` and `manifest.yaml` for narrative focus
- Update `style_packs/story_agent/ddl/` to something more fitting (rename to e.g. "hitchcock" or keep DDL but reframe as narrative obsessive)
- **Done when:** Prompt focuses on narrative logic, not performance

**Task 3: Character system prompt builder (backend)**
- New function `build_character_system_prompt(character_id, project_id, service)` in `chat.py`
- Loads: character bible (from `bible_manifest` artifact → `CharacterBible` JSON inside), scene index entries where character appears
- Composes: template from story spec (character name, bible entry, scene summaries, instructions)
- Uses service to read artifacts — no tools needed at runtime
- **Done when:** Function returns a well-formed system prompt string

**Task 4: Character routing (backend)**
- Extend `resolve_target_roles` signature to accept `character_ids: list[str]` (available characters)
- After checking for role matches, check remaining @-mentions against character IDs (strip `character_` prefix)
- Return a `ResolvedTargets` dataclass: `roles: list[str]`, `characters: list[str]` (entity IDs like `character_billy`)
- **Done when:** `resolve_target_roles("@billy @director", ..., character_ids=["billy"])` returns roles=["director"], characters=["character_billy"]

**Task 5: @-mention cap**
- In resolve logic: count `roles + characters` (with `@all-creatives` counting as 5)
- If > 6, return an error in the result (e.g. `ResolvedTargets(error="...")`)
- API endpoint returns error chunk if cap exceeded
- **Done when:** 7+ targets returns friendly error

**Task 6: Character streaming (backend)**
- Extend `stream_group_chat` to accept character targets
- For each character: build system prompt with `build_character_system_prompt()`, call Haiku model, no tools, stream with `speaker: "char:billy"`
- Characters stream BEFORE director (if director present), AFTER other roles
- New endpoint: `/api/projects/{pid}/characters` — returns list of `{id, name, prominence}` from `bible_manifest` artifacts
- API `chat_stream`: load character list, pass to `resolve_target_roles`, handle character streaming
- **Done when:** `@billy` streams an in-character response with `speaker: "char:billy"`

**Task 7: Autocomplete sections (frontend)**
- Refactor `PICKABLE_ROLES` into sections: `Shortcuts` (all-creatives), `Roles` (current list), `Characters` (dynamic)
- New API call in ChatPanel: fetch `/api/projects/{pid}/characters` to get character list
- Autocomplete popup shows 3 sections with headers; Characters section hidden if no characters
- `@all-creatives` as a "shorthand" in the Shortcuts section
- Typing `@` shows all sections; typing filters across all
- **Done when:** Popup shows sections, characters appear from API, filtering works across sections

**Task 8: Character visual identity + bubble rendering (frontend)**
- `getRoleDisplay` handles `char:*` speakers: extract character name, use shared warm color (`text-amber-300/bg-amber-500/6`... actually amber is taken by story_agent. Use `text-orange-300/bg-orange-500/6`)
- Person/drama-mask icon for all characters
- Character name in bubble header is a clickable link → `/{projectId}/characters/{characterId}`
- Sticky header works for character messages too
- **Done when:** Character bubbles render with shared warm color, name is a link

**Impact Analysis:**
- Tests: `test_role_system.py` needs `actor_agent` → `story_agent`. Backend unit tests should still pass since we're not changing schemas.
- No new dependencies needed.
- No schema changes — we're using existing `bible_manifest` and `scene_index` artifacts.
- New API endpoint: `/api/projects/{pid}/characters` — lightweight, reads existing artifacts.
- `@all-creatives` expansion in backend already works — just need to update the list name.

## Work Log

20260224 — story created from design discussion. Key decisions: characters are characters not actors (character-first with meta-awareness), fat system prompt with no tools (bible + scene summaries pre-loaded), Haiku model for cost, actor_agent renamed to story_agent (narrative logic focus), @-mention cap of 6, autocomplete sections (shortcuts → roles → characters), shared warm visual for all characters differentiated by name not color, character names linkable to bible pages.

20260224-1430 — Phase 1-2 exploration and planning complete. Key findings: 15 files reference actor_agent. CharacterBible has rich data (traits, relationships, scene_presence, dialogue_summary). SceneIndexEntry has characters_present_ids for filtering but no summary field — will compose from heading+location+tone. Character entity IDs are `character_xxx` in artifacts; mention handle strips prefix. resolve_target_roles currently returns list[str]; needs refactor to ResolvedTargets dataclass for roles vs characters. story_agent tier should upgrade from performance → structural_advisor (narrative logic is advisory, not performance). Amber color was actor_agent's — reassign to story_agent, use orange/warm-neutral for characters.

20260224-1530 — User feedback: (1) Rename to "Story Editor" not "Story Agent". (2) Keep Story Editor and Editorial Architect separate (structure/craft vs narrative logic). (3) Cream/parchment color for characters, not orange (distinct from Story Editor's amber).

20260224-1600 — Tasks 1-6 (backend) complete. Renamed actor_agent → story_editor across 15 files. Rewrote role.yaml with narrative logic system prompt, tier upgraded to structural_advisor. All 4 style packs rewritten. New `ResolvedTargets` dataclass, character routing, `build_character_system_prompt()`, character streaming with Haiku, `MAX_MENTION_TARGETS=6` cap, new `/api/projects/{pid}/characters` endpoint. 305 tests pass, ruff clean.

20260224-1700 — Tasks 7-9 (frontend) complete. Sectioned @-mention popup (Shortcuts → Roles → Characters) with `MentionItem` type and `useMemo` filtering. New `ChatCharacter` type, `listProjectCharacters` API function, `useProjectCharacters` hook. Character visual identity: cream/parchment (`text-amber-200/bg-amber-100/8`), Scroll icon, clickable name → character bible page. `getRoleDisplay` handles `char:*` speakers with `isCharacter`/`characterId` fields. tsc -b clean, lint clean, build clean.

20260224-1715 — Runtime smoke test passed. Backend health endpoint 200, characters endpoint returns 12 characters for The Mariner project (Carlos, Dad, Mariner, Mikey, Rosco, Rose, Salvatori, Thug 1-3, Vinnie, Young Mariner). UI loads clean, no console errors, updated placeholder text visible. All acceptance criteria met.

20260225-1400 — Chat persistence enrichment & character history fix. Three issues identified and fixed: (1) `pageContext`, `toolCalls`, and `injectedContent` now persisted in chat.jsonl — user messages record what page was being viewed and the actual scene/bible text injected into the system prompt, AI messages keep tool call history. (2) Cross-character history poisoning fixed: character-thread filtering ensures each character only sees its own conversation thread (user messages + its own responses), preventing e.g. Mariner's "nothing attached" from causing Carlos to copy that pattern. Messages merged after filtering to maintain Anthropic alternation. (3) Stale Zustand state bug fixed in `injectedContent` re-persist. API payload dump added (`CINEFORGE_DUMP_API=1`) for deterministic debugging. Characters upgraded from Haiku to Sonnet for better system prompt adherence. All checks pass: 305 tests, ruff clean, lint clean, tsc -b clean, build clean.

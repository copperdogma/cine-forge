# Story 084 — Character Chat Agents & Story Agent Rename

**Priority**: High
**Status**: Pending
**Spec Refs**: spec.md 8.6 (Inter-Role Communication), 8.7 (Human Interaction Model)
**Depends On**: 083 (Group Chat Architecture)

## Goal

Add dynamic character agents to the group chat so users can talk directly to their screenplay's characters. `@billy` talks to Billy in character — grounded in the character bible and scene context, responding from his perspective with meta-awareness when pushed. This enables creative discovery through conversation: "Billy, why did you really go back for the gun?" produces insights that analysis can't.

Also rename `actor_agent` to `story_agent` (narrative logic, arcs, themes, consistency) since direct character chat makes a generic "acting coach" role less useful. And add the missing `@all-creatives` shorthand to the autocomplete UI.

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

- [ ] `@billy` (or any character entity ID) opens a conversation with that character in-character, grounded in their bible entry and scene context
- [ ] Character responses use Haiku model with fat system prompt (bible + scene summaries), no tools
- [ ] Character message bubbles use shared warm visual treatment with person icon and character name
- [ ] Character names in chat bubbles are clickable links to their character bible page
- [ ] Characters do NOT appear in `@all-creatives` expansion
- [ ] @-mention cap of 6: attempting to address 7+ roles/characters returns a friendly error message
- [ ] `@all-creatives` appears in the @-mention autocomplete popup as a shorthand
- [ ] Autocomplete popup shows sections: Shortcuts → Roles → Characters (dynamic from character bible)
- [ ] `actor_agent` is renamed to `story_agent` everywhere (role.yaml, style packs, ROLE_DISPLAY, routing, prompts, all references)
- [ ] Story agent prompt focuses on narrative logic, arcs, themes, consistency (not acting/performance)
- [ ] Characters with no character bible (pipeline not yet run) don't appear in autocomplete — section hidden
- [ ] Existing `@all-creatives` backend routing still works correctly with the rename

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

- [ ] **Task 1: Rename actor_agent → story_agent** — Update `role.yaml`, style packs (rename directories + files), `ROLE_DISPLAY` in ChatPanel, `PICKABLE_ROLES`, `CREATIVE_ROLES` in chat.py, `ASSISTANT_EXTRA` routing text, `resolve_target_roles`, all test references
- [ ] **Task 2: Story agent prompt** — Rewrite system prompt for narrative logic focus: story arcs, thematic consistency, character motivation coherence, plot hole detection. Update generic style pack.
- [ ] **Task 3: Character agent system prompt builder** — New function `build_character_system_prompt(character_id, project_id)` that composes: character bible entry + scene summaries where character appears + "stay in character" instructions with meta-awareness
- [ ] **Task 4: Character routing in backend** — Extend `resolve_target_roles` to detect `@character_id` mentions by checking against project's character bible entities. Return character targets as a separate list/type from role targets.
- [ ] **Task 5: Character streaming** — Extend `stream_group_chat` to handle character targets: use Haiku model, no tools, fat system prompt. Character responses get `speaker: "char:billy"` (or similar prefix to distinguish from roles).
- [ ] **Task 6: @-mention cap** — Enforce max 6 targets in `resolve_target_roles`. Return error chunk if exceeded. `@all-creatives` counts as 5.
- [ ] **Task 7: Autocomplete sections** — Refactor @-mention popup to show sections (Shortcuts, Roles, Characters). Add `@all-creatives` as a shorthand. Characters fetched from character bible API. Section hidden if no characters exist.
- [ ] **Task 8: Character visual identity** — Add character display config: shared warm color, person icon, character name. Linkable name → character bible page (`/{projectId}/characters/{characterId}`).
- [ ] **Task 9: Character bubble rendering** — ChatPanel handles `speaker: "char:*"` messages with character visual treatment. Sticky header shows character name when scrolling.
- [ ] Run required checks for touched scope:
  - [ ] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [ ] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [ ] UI (if touched): `pnpm --dir ui run lint` and `cd ui && npx tsc -b`
- [ ] Search all docs and update any related to what we touched
- [ ] Verify adherence to Central Tenets (0-5):
  - [ ] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [ ] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [ ] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [ ] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [ ] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [ ] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

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

{Written by build-story Phase 2}

## Work Log

20260224 — story created from design discussion. Key decisions: characters are characters not actors (character-first with meta-awareness), fat system prompt with no tools (bible + scene summaries pre-loaded), Haiku model for cost, actor_agent renamed to story_agent (narrative logic focus), @-mention cap of 6, autocomplete sections (shortcuts → roles → characters), shared warm visual for all characters differentiated by name not color, character names linkable to bible pages.

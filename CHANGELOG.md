# Changelog

## [2026-02-28-04] — Scout 003: cross-project pattern adoption

### Added
- `/improve-skill` retrospective skill for post-interaction skill improvement
- AI-as-Tester principle in AGENTS.md — qualitative AI behavior testing via subagent probes
- Eval mismatch investigation mandate (Definition of Done #5, `/validate`, `/build-story`, `/mark-story-done`)
- ADR template: Integration Checklist and "Settled — DO NOT suggest alternatives" marker
- Scout 003 expedition doc and index entry
- Draft stories 102-106: multi-turn evals, AGENTS.md extraction, tiered metrics, parallel extraction, chunk cache

### Changed
- `/triage-inbox`: "fold into existing story" + "what if we don't do this?" + delete-not-archive policy
- `/scout`: automatic source resolution from scout history for re-scouts
- `docs/inbox.md`: removed Triaged archive section (inbox is now a queue)

## [2026-02-28-03] — Look & Feel visual direction (Story 021)

### Added
- `look_and_feel_v1` pipeline module: per-scene parallel analysis with 3-scene sliding window, bible + Intent/Mood context injection, QA loop with escalation, mock support
- `LookAndFeelIndex` schema for project-level visual identity aggregate
- Visual Architect role enhanced with rich persona (lighting philosophy, colour theory, camera language, composition, costume/production design)
- `look_and_feel` stage in creative direction recipe with `store_inputs_optional` for intent_mood, character_bible, location_bible
- Look & Feel entry activated in DirectionTab with "Get Look & Feel Direction" / "Regenerate Look & Feel" buttons
- `look_and_feel_index` registered in artifact-meta.ts (Eye icon, sky-400)
- 14 unit tests for Look & Feel module

### Fixed
- DirectionTab run tracking: buttons now stay disabled for full pipeline run duration via `setActiveRun()` wiring to global `useRunProgressChat` system
- Button cursor-pointer added to global shadcn/ui button styles
- Recipe `needs` vs `after` fix: creative direction stages use `after: [intent_mood]` instead of `needs: [intent_mood]` to avoid schema compatibility failures
- Engine `start_from` wave scheduling: skipped stages now added to `already_satisfied` set so `after` dependencies resolve correctly
- Chat store migration: `resolveTaskProgress()` flips stale running/pending task_progress items to done on page reload
- DirectionTab generalized: dynamically loops over all concern groups instead of hardcoding Rhythm & Flow only

### Changed
- `look_and_feel` added to `REVIEWABLE_ARTIFACT_TYPES` in engine.py
- `look_and_feel_index` added to pipeline graph artifact_types with nav_route
- `look_and_feel` added to `NODE_FIX_RECIPES` in graph.py

## [2026-02-28-02] — Intent / Mood UX improvements (Story 095)

### Added
- Deep breakdown gate: Intent & Mood page requires character/location bibles before showing the full form, with explanation of why and "Run Deep Breakdown" button
- `TaskProgressCard` component for compact multi-item progress in chat timeline
- `task_progress` message type for grouped operation progress (heading + per-item status)
- Chat activity messages for all long-running operations (deep breakdown, propagation)
- Propagation progress: per-concern-group spinner→checkmark transitions in chat
- Status banner during propagation matching ProcessingView style
- Explanatory text below Save & Propagate buttons describing what propagation does
- User Feedback Contract directive in AGENTS.md for durable long-running operation UX

### Changed
- "Suggest a Vibe" upgraded from deterministic keyword matching to LLM call (Haiku) with structured output — correctly matches mood/preset to script context
- Save & Propagate button shows descriptive loading state: "Generating suggestions for all concern groups..."
- Reference film input made full-width (was constrained to small inline box)
- Suggest endpoint now returns reference films from matched preset
- ProcessingView is now recipe-aware: shows "Running Deep Breakdown..." or "Running Creative Direction..." instead of generic "Processing your screenplay..."
- 5 concern group pipeline nodes (`look_and_feel`, `sound_and_music`, `character_and_performance`, `story_world`, `rhythm_and_flow`) changed to `implemented=True` — Direction dropdown now shows completion status instead of "Coming soon"
- `rhythm_and_flow` node accepts both `rhythm_and_flow_index` and `rhythm_and_flow` artifact types

## [2026-02-28-01] — Intent / Mood warm invitation UX (Story 095)

### Added
- Warm invitation card on Intent & Mood page: shows script context (title, genre, tone, themes, logline) when no intent is set but script bible exists
- "Suggest a Vibe" button: deterministic mood suggestion from script analysis (mood word extraction + best preset match by keyword overlap)
- `GET /api/projects/{id}/script-context` endpoint returning `ScriptContextResponse`
- `POST /api/projects/{id}/intent-mood/suggest` endpoint returning `IntentMoodSuggestion`
- 7 new unit tests for suggest flow (401 total)

## [2026-02-27-05] — Intent / Mood Layer (Story 095)

### Added
- Style preset catalog: 6 built-in "vibe" presets (Neo-Noir, Summer Indie, Documentary Realism, Gothic Horror, Ethereal Drama, Action Thriller) as YAML in `configs/style_presets/` with `StylePreset` model in `src/cine_forge/presets/`
- Propagation service (`src/cine_forge/services/intent_mood.py`): Director-driven AI translation of mood intent into per-concern-group suggested defaults
- 4 new API endpoints: GET/POST `/api/projects/{id}/intent-mood`, POST `/api/projects/{id}/intent-mood/propagate`, GET `/api/projects/{id}/style-presets`
- Pipeline module `intent_mood_v1` in `src/cine_forge/modules/creative_direction/intent_mood_v1/` with mock mode and structured LLM output
- Intent & Mood UI page (`ui/src/pages/IntentMoodPage.tsx`): preset picker, mood chip selector, reference film tags, NL textarea, save/propagate, propagation preview cards
- Scene-level intent panel (`SceneIntentPanel` in `DirectionTab.tsx`): shows inherited project mood with "Customize for this scene" button
- "Intent" nav item in sidebar between Script and Scenes
- 17 unit tests in `tests/unit/test_intent_mood.py`

### Changed
- Pipeline graph: `intent_mood` node flipped to `implemented=True` with `nav_route="/intent"`
- `recipe-creative-direction.yaml`: added `intent_mood` stage before `rhythm_and_flow`
- `NODE_FIX_RECIPES` now maps `intent_mood` → `creative_direction`

## [2026-02-27-04] — Concern group artifact schemas (Story 094)

### Added
- 6 concern group schemas in `src/cine_forge/schemas/concern_groups.py`: IntentMood, LookAndFeel, SoundAndMusic, RhythmAndFlow, CharacterAndPerformance, StoryWorld (plus shared MotifAnnotation and container types)
- Readiness computation in `src/cine_forge/schemas/readiness.py`: RED/YELLOW/GREEN per concern group per scene with per-group yellow thresholds
- 6 concern group nodes in pipeline graph (intent_mood, rhythm_and_flow, look_and_feel, sound_and_music, character_and_performance, story_world)
- 7 artifact metadata entries in UI (artifact-meta.ts, constants.ts)
- 24 unit tests across test_concern_group_schemas.py and test_readiness.py

### Changed
- Migrated EditorialDirection → RhythmAndFlow (schema, module output, recipe, role YAMLs)
- DirectionAnnotation.tsx now uses generic concern group renderer instead of hardcoded EditorialDirection fields
- DirectionTab.tsx button labels: "Get Rhythm & Flow Direction" (was "Get Editorial Direction")
- Pipeline direction phase expanded from 3 nodes to 6 concern group nodes

### Removed
- `src/cine_forge/schemas/editorial_direction.py` — replaced by RhythmAndFlow in concern_groups.py

## [2026-02-27-03] — Script bible artifact (Story 093)

### Added
- Script bible schema (`ScriptBible`, `ActStructure`, `ThematicElement`) in `src/cine_forge/schemas/script_bible.py`
- `script_bible_v1` pipeline module — single Sonnet LLM call from canonical script
- `script_bible` stage in `recipe-mvp-ingest.yaml` (parallel with `breakdown_scenes`)
- Pipeline graph node for script bible in the `script` phase
- ScriptBiblePanel on the Script page — expandable panel with tone, theme badges (with tooltips), synopsis, conflict/journey/arc/setting grid, act structure
- `useScriptBible` hook and artifact metadata
- `stage_order` field on `RunState` — recipe YAML is now the single source of truth for stage display order
- 7 unit tests for the script bible module

### Changed
- Deleted hardcoded `RECIPE_STAGE_ORDER` from UI constants — frontend reads order from backend API
- Moved 4 legacy partial-ingest recipes from `configs/recipes/` to `tests/fixtures/recipes/`
- Fixed stale `stages["extract"]` assertions in timeline/track integration tests

### Fixed
- `json.dump(..., sort_keys=True)` in `_write_run_state` was destroying stage insertion order — resolved by explicit `stage_order` array

## [2026-02-27-02] — Document two-tier preference model across project

### Added
- Two-tier preference explanation in ideal.md header (vision-level vs compromise-level)
- Counterpart explanation in spec.md header
- Preference-level awareness in AGENTS.md Ideal reference block
- Compromise-level preferences tagged on C1 (Cost Transparency) and C7 (Working Memory)
- Vision-level vs compromise-level contrast in setup-ideal skill
- Compromise-level preference intro in setup-spec skill

## [2026-02-27-01] — ADR-003 decided: Three-Layer Director's Vision Model

### Added
- ADR-003 decided (Option E) — Intent/Mood layer → 5 concern groups → scope substrate
- `decisions-log.md` — 14 comment decisions from synthesis review
- Deep research: 4 provider reports (OpenAI, Anthropic, Google, xAI) + final synthesis
- R17 in ideal.md — real-world assets as first-class inputs
- Round-trip decomposition vision preference in ideal.md
- 4 inbox items under "ADR-003 Deferred Ideas" (film decomposition, AI enhancement, location lookup, mood-board synthesis)
- 8 new story skeletons: 093 (Script Bible), 094 (Concern Group Schemas), 095 (Intent/Mood Layer), 096 (Chat About This), 097 (AI Artifact Editing), 098 (Real-World Asset Upload), 099 (Scene Workspace), 100 (Motif Tracking)
- Recommended build order in stories.md (7 groups, dependency-aware)

### Changed
- spec.md §12 completely rewritten: 4 direction types → 5 concern groups + Intent/Mood + Readiness Indicators + Prompt Compilation Model
- spec.md §4.5 (Script Bible), §4.6 (Two-Lane Architecture) added
- spec.md §4.4, §9, §13, §18 updated for ADR-003 terminology and R17
- Stories 021 (Look & Feel), 022 (Sound & Music), 023 (Character & Performance) reshaped for concern group model
- Story 025 (Shot Planning) dependency changed from Story 024 → concern group stories
- Story 028 (Render Adapter) updated for concern group inputs, R17 dependency
- Stories 026, 027, 029, 030, 056 updated for concern group terminology
- Stories 082, 085 (Done) — ADR-003 impact notes added to work logs
- setup-checklist.md, retrofit-gaps.md updated for concern group terminology
- Untriaged "Prompt transparency / direct editing" resolved by ADR-003 Decision #4

### Removed
- Story 024 (Direction Convergence) cancelled — Intent/Mood layer handles cross-group coherence

## [2026-02-26-04] — Ideal-first retrofit: ideal.md, spec annotations, gap analysis, ADR-003

### Added
- `docs/ideal.md` — The Ideal document (16 requirements, 11 vision preferences, the north star for all design decisions)
- `docs/retrofit-gaps.md` — Gap analysis: missing evals, golden refs, untraceable stories, under-covered requirements, Dossier integration plan
- `docs/setup-checklist.md` — Prioritized retrofit checklist (P0–P3)
- `docs/decisions/adr-003-film-elements/` — ADR for creative element grouping between screenplay and film
- Ideal reference block at top of AGENTS.md ("Is it easy, fun, and engaging?")
- Prompt Transparency AC added to Story 028 (Render Adapter) per Ideal R12
- Dependency `Blocks: 025` added to Story 092 (Continuity AI)

### Changed
- `docs/spec.md` annotated with 7 compromise blocks (C1–C7), compromise index, untriaged ideas section
- Story 090 (Persona-Adaptive Workspaces) cancelled — superseded by two-view architecture + interaction mode
- Extraction-related checklist items struck through (Dossier will handle)

## [2026-02-26-03] — Scout dossier: adopt ideal-first methodology skills

### Added
- 9 new skills from dossier: `/setup-ideal`, `/setup-golden`, `/setup-evals`, `/setup-spec`, `/setup-stories`, `/setup-env-ai`, `/setup-env-dev`, `/retrofit-ideal`, `/reflect`
- `docs/prompts/ideal-app.md` — reusable generator prompt for Ideal App documents
- "Baseline = Best Model Only" principle in AGENTS.md
- Story Conventions section in AGENTS.md (Draft → Pending → In Progress → Done)
- Runbook Conventions section in AGENTS.md (`[script]`/`[judgment]` tagging, skill↔runbook rule)
- Scout expedition 002 — dossier infrastructure (22 findings, 15 adopted)

### Changed
- Story template default status from `Pending` to `Draft`

## [2026-02-26-02] — Remove dead Inspector tab from right panel

### Removed
- Inspector tab and all supporting code — never had any functionality (nothing called `openInspector`)
- `ui/src/lib/inspector.tsx` (orphaned context provider, never mounted)
- Inspector tab bar, `setTab()`, `ActiveTab` type, `useInspector()` wrapper from right panel context
- "Toggle Inspector" command from command palette

### Changed
- Right panel is now a single-purpose Chat panel with a simple header (no tabs)
- `⌘I` shortcut relabeled from "Toggle inspector" to "Toggle right panel"
- Theme showcase layout skeleton updated ("Inspector" → "Chat")

## [2026-02-26-01] — Pipeline capability graph, AI navigation, preflight cards, staleness UX, interaction mode (Stories 085–089)

### Added
- Pipeline capability graph: 19 nodes across 6 phases (Script/World/Direction/Shots/Storyboards/Production) with dynamic status from artifact store (`src/cine_forge/pipeline/graph.py`)
- Pipeline bar: persistent horizontal bar in app shell showing project progress with phase segments, tooltips, completion badges, and click-to-navigate (`ui/src/components/PipelineBar.tsx`)
- AI `read_pipeline_graph` tool: chat AI can read full pipeline state and recommend next steps
- AI navigation intelligence: system prompt guidance for pipeline-aware responses, tiered preflight checks (green/yellow/red) before proposing runs, prerequisite validation
- Preflight summary cards: visual cards in chat showing recipe readiness, input health, and warnings before expensive runs (`ui/src/components/PreflightCard.tsx`)
- Staleness tracing: `trace_staleness()` walks dependency graph to explain WHY artifacts are stale, shown in pipeline bar tooltips and AI chat output
- "Fix with rerun" button on stale pipeline nodes — dispatches chat message to rerun the appropriate recipe
- Interaction mode selector (guided/balanced/expert): adjusts AI verbosity and system prompt framing, stored in project.json
- `GET /api/projects/{pid}/pipeline-graph` endpoint
- `interaction_mode` field in project settings API
- ADR-002 (Goal-Oriented Project Navigation): decided, with deep research from 4 AI providers
- Story 090 (Persona-Adaptive Workspaces) created for ADR-002 Layer 4

### Changed
- AI system prompt includes pipeline navigation guidance and post-run graph refresh instructions
- Staleness propagation records `stale_cause` for upstream traceability
- Story 023 rewritten to reflect Story 084 superseding actor agent scope
- AGENTS.md repo map updated with `src/cine_forge/pipeline/` package

## [2026-02-25-01] — Chat persistence enrichment & character history fix (Story 084)

### Added
- `pageContext` persisted on user messages in chat.jsonl (records what page the user was viewing)
- `injectedContent` persisted on user messages (records the actual scene/bible text injected into the AI's system prompt)
- `toolCalls` persisted on AI messages (no longer stripped before persistence)
- `injected_content` SSE event type for streaming the actual injected artifact content
- API payload dump for debugging: `CINEFORGE_DUMP_API=1` writes exact Anthropic API JSON to `/tmp/`

### Fixed
- Character-thread filtering: each character now only sees its own conversation thread, preventing cross-character history poisoning (e.g., Mariner saying "nothing attached" no longer causes Carlos to copy that pattern)
- User message upsert in chat.jsonl so `injectedContent` can be added after initial persist
- Stale Zustand state bug: `injectedContent` re-persist now reads fresh state after store update

### Changed
- Characters upgraded from Haiku to Sonnet for better system prompt adherence
- Scene/entity artifact injection for roles (not just characters) via `_inject_page_artifact`
- User message hint injection when page context has attached content

## [2026-02-24-07] — Character Chat Agents & Story Editor Rename (Story 084)

### Added
- Character chat agents: `@billy`, `@rose`, etc. open in-character conversations grounded in character bibles and scene context
- Character system prompt builder: fat prompt with character bible + scene summaries, Haiku model, no tools
- `GET /api/projects/{pid}/characters` endpoint returning characters from bible_manifest artifacts
- Sectioned @-mention autocomplete: Shortcuts (`@all-creatives`) → Roles → Characters (dynamic from API)
- Character visual identity: cream/parchment color, scroll icon, clickable name → character bible page
- `ResolvedTargets` dataclass for structured role + character routing
- `MAX_MENTION_TARGETS` cap of 6 (with `@all-creatives` counting as 5)

### Changed
- Renamed `actor_agent` → `story_editor` across 15 files (role definition, style packs, routing, UI, tests)
- Story editor prompt rewritten for narrative logic: character motivation coherence, plot logic, thematic consistency, timeline/continuity
- Story editor tier upgraded from `performance` → `structural_advisor`
- Character streaming ordered: non-director roles → characters → director

## [2026-02-24-06] — ADR-001: Shared Entity Extraction → Dossier

### Added
- ADR-001 research, decision, and full specification for shared entity extraction library ("Dossier")
- Multi-model deep research (OpenAI, Google, Anthropic, xAI) with synthesis
- "Critical Pushback Required" mandate in AGENTS.md

### Changed
- ADR-001 status: PENDING → DECIDED (standalone library, new repo at github.com/copperdogma/dossier)

## [2026-02-24-05] — Group Chat Architecture (Story 083)

### Added
- True group chat: roles respond directly with their own voice, avatar, and visual identity (no intermediary paraphrasing)
- Assistant as a first-class role in the catalog (`roles/assistant/role.yaml` + generic style pack)
- `@-mention` routing: `@director`, `@editorial_architect`, `@visual_architect`, `@sound_designer`, `@story_editor`, `@all-creatives`
- Conversation stickiness: messages without @-mention go to the last-addressed role
- Multi-role sequential streaming with Director-last convergence
- Anthropic prompt caching (`cache_control` breakpoints on system prompt + transcript prefix)
- Inline @-mention autocomplete: type `@` anywhere for filtered role dropdown with keyboard nav
- Per-role tinted message bubbles with icon + name header (full-width, no wasted horizontal space)
- Sticky role headers: role name pins to top of chat when scrolling through long messages
- Auto-growing textarea with custom drag-to-resize (drag up = grow, pill-style handle)
- Send button overlaid inside textarea container (ChatGPT-style)
- Long transcript compaction via Haiku summarization (above 80k estimated tokens)
- READ_TOOLS available to all roles (get_artifact, list_scenes, list_characters, etc.)

### Removed
- `talk_to_role` tool-call pattern (nested LLM calls, paraphrased responses)

### Changed
- `/chat/stream` endpoint now uses `stream_group_chat()` with RoleCatalog-backed role resolution
- Chat messages now carry `speaker` field for role attribution
- Streaming chunks include `role_start`/`role_done` envelope events for multi-role responses

### Fixed
- Multi-role streaming: synthetic user message between role responses to satisfy Anthropic alternating requirement
- Textarea no longer triggers Chrome password autofill (`autoComplete="off"`, `data-form-type="other"`)
- Chat text wraps properly in narrow panel (`w-0 min-w-full` + `break-words`)
- Entity context preserved on page refresh

## [2026-02-24-04] — Creative Direction UX (Story 082)

### Added
- Direction tab on scene detail pages with Overview/Direction tab layout
- `DirectionAnnotation` component — Word/Google Docs comment-style UI for creative direction, parameterized by direction type (editorial/visual/sound/performance)
- `DirectionTab` component with generate-via-chat buttons, direction artifact cards, empty state with @role teaching nudges
- `RolePresenceIndicators` — role avatar badges on scene headers showing which roles have direction
- "Get Editorial Direction" button sends `@editorial_architect` chat message (maintains full chat history)
- "Review with Director" convergence chat shell for cross-role direction review
- `page_context` now sent from frontend to backend chat API (was defined but unused)
- Scene context injected into AI system prompt so roles know which scene the user is viewing

## [2026-02-24-03] — Editorial Architect and editorial direction pipeline (Story 020)

### Added
- `EditorialDirection` and `EditorialDirectionIndex` Pydantic schemas for per-scene editorial analysis
- `editorial_direction_v1` module under new `creative_direction/` stage directory with 3-scene sliding window analysis, parallel extraction, QA escalation, and streaming progress
- `recipe-creative-direction.yaml` — Phase 5 creative direction recipe (editorial direction stage)
- "Creative Direction" recipe option in Pipeline UI, ordered after Narrative Analysis
- `editorial_direction` added to `REVIEWABLE_ARTIFACT_TYPES` for Director/Script Supervisor canon review
- UI artifact metadata for editorial direction artifacts (Scissors icon, pink)
- 9 unit tests covering mock output, scene window construction, full module run, edge cases

### Changed
- Editorial Architect system prompt expanded from 2 lines to rich persona covering cut-ability prediction, coverage adequacy, pacing, transitions, and montage identification
- Editorial Architect role permissions updated to include `editorial_direction`
- Recipe list in Pipeline UI now sorted by logical pipeline execution order

## [2026-02-24-02] — Scene index as canonical character source, prominence sort (Story 081)

### Changed
- Entity discovery consumes `scene_index.unique_characters` as the canonical character list instead of independently re-scanning the canonical script via LLM
- Prominence sort on characters page now groups by tier (Primary > Secondary > Minor) then by scene count within each tier

### Added
- `breakdown_scenes: scene_index` wired into entity discovery's `store_inputs` in world-building recipe
- `character_source` field in entity discovery processing metadata (`"scene_index"` or `"llm"`)
- 11 entity discovery tests (up from 1): scene-index passthrough, normalization, fallback, refine mode

### Fixed
- THUG 3 now appears in character bibles (was missing because entity discovery's independent LLM scan couldn't parse "THUGS 2 & 3")
- Entity discovery cost reduced ~31% (no character-scanning LLM calls when scene_index is available)

## [2026-02-24-01] — LLM-powered action line entity extraction (Story 080)

### Added
- LLM call (Haiku-class) per scene extracts characters and props from action/description lines, replacing brittle regex
- `_ActionLineEntities` Pydantic model and `_extract_action_line_entities()` function with mock path for deterministic tests
- `props_mentioned` field on `Scene` and `SceneIndexEntry` schemas
- Golden reference fixture (`tests/fixtures/golden/the_mariner_scene_entities.json`) — 12 hand-verified characters, 6 props
- Golden References table in AGENTS.md documenting all test fixtures
- 6 regression tests: mock path, empty input, props field, LLM+dialogue union, provenance update, index aggregation

### Changed
- Scene breakdown unions LLM-extracted characters with structural dialogue-cue characters (additive, no regression)
- Provenance annotation reflects `method="ai"` and `discovery_tier="structural+ai"` when LLM contributes new characters
- Passes both action and dialogue elements to LLM to handle Fountain element misclassification

### Removed
- `_extract_character_mentions` regex function — replaced entirely by LLM extraction

## [2026-02-23-07] — Character coverage and prominence tiers (Story 077)

### Added
- `prominence` field on `CharacterBible` schema: `primary`, `secondary`, or `minor` — AI-assigned at extraction time based on SAG-AFTRA-aligned rubric
- Lightweight extraction path for minor characters (score < 4) — stripped-down prompt, ~80% cheaper per character
- `ProminenceBadge` UI component (Crown/Star/User icons per tier) on character list cards and detail page header
- Prominence filter chips (All/Primary/Secondary/Minor) on Characters list view, persisted via sticky preference
- Adjudication prompt rule to preserve named minor characters (THUG 1, GUARD 2, etc.)
- Stub candidate entries for discovery-only characters whose names differ from scene_index normalization (e.g. "THUG 1"/"THUG 2" collapsed to "THUG" by scene parser)
- 7 regression tests for plausibility filter, prominence field, minor character paths, and discovery-only extraction

### Fixed
- Plausibility filter now accepts alphanumeric tokens — "THUG 1" no longer rejected by regex
- Removed "THUG" from `CHARACTER_STOPWORDS` — was incorrectly blocking functional character names
- Discovery-only characters (found by LLM entity discovery but missing from scene_index due to name normalization) no longer silently dropped

## [2026-02-23-06] — Script view scene dividers and entity hotlinks (Story 070)

### Added
- Scene divider bars injected at each scene boundary in the CodeMirror screenplay editor — shows scene number, visually distinct from script text, clickable to navigate to the scene detail page
- `onSceneDividerClick`, `onCharacterNameClick` callbacks and `scenes` prop on `ScreenplayEditor` — scene dividers implemented as CodeMirror 6 `StateEffect` + `StateField` + `WidgetType` block decorations
- `ScriptViewer` (artifact detail page) now accepts `projectId` and fetches scene data internally — scene dividers and hotlinks work on both the project home script view and the canonical script artifact detail page
- `startLine` / `endLine` fields promoted to the UI `Scene` interface from `source_span` in scene artifacts
- Hover states on scene divider bars (dim amber → bright amber), scene heading lines (amber tint), and character name lines (blue tint) — implemented via `Decoration.line()` stamping stable `.cm-heading-line` / `.cm-character-line` CSS classes, since `HighlightStyle` uses opaque generated class names incompatible with `:has()`

### Fixed
- Character name lines (ALL-CAPS cue lines) in the screenplay editor are now clickable hotlinks — clicking "ROSE" navigates to `/:projectId/characters/rose`
- Character names with trailing parentheticals (`ROSE (O.S.)`, `MARINER (V.O.)`) now resolve correctly — parenthetical stripped before entity lookup
- Fuzzy entity resolver fallback: cue text "MARINER" now matches entity_id "the_mariner" via substring check

## [2026-02-23-05] — Chat & nav bug fixes: slash-search routing, entity context chip (Story 079)

### Added
- Entity context chip above chat input — shows icon + entity name when viewing a character, location, prop, or scene detail page; updates on navigation, clears on list pages; clicking navigates back to the entity
- `entityContext` state in `chat-store` (`setEntityContext` / `clearEntityContext` actions) — pure UI state, not persisted

### Fixed
- Slash-search (CommandPalette `/` trigger) now navigates to entity detail pages (`/characters/:id`, `/locations/:id`, `/props/:id`, `/scenes/:id`) instead of raw artifact URLs
- `addActivity` idempotency bug — activity message was silently skipped when a newer message (e.g. AI response) had landed after the last navigation; fixed by finding the stable ID anywhere in the list instead of only checking the last message
- `ChatMessagePayload` backend model now includes `route` field so activity message routes persist to JSONL storage on cold load

## [2026-02-23-04] — Entity detail UX polish: scroll-to-top, cross-ref ordering, prop ownership (Story 078)

### Added
- Owner link-pills on the Props list page — all three density variants (compact/medium/large) show linked character chips for signature props; click navigates to character without triggering prop navigation
- "Owned by" row in the prop detail Profile card — linked character chip(s) appear at the bottom of the profile for any prop with `signature_prop_of` edges
- Scene Appearances now sorted by script order on entity detail pages — uses scene index heading→scene_number map, unknown headings go to end

### Changed
- Entity navigation scrolls to top of page on every route change — targets the Radix `<ScrollArea>` viewport via `[data-radix-scroll-area-viewport]` query in `AppShell.tsx`
- Characters, Locations, and Props panels in `CrossReferencesGrid` sorted by scene co-occurrence count descending (most connected co-stars appear first); ties broken alphabetically
- Props panel in `CrossReferencesGrid` splits signature props (amber ★, sorted first) from co-occurrence props (no star, sorted below); both halves sorted by scene count
- `RawEdge` in `CrossReferencesGrid` now carries `sceneRefs: string[]` — dedup merges refs from duplicate edges for accurate count
- `EntityLink` component gains optional `suffix` slot for decorative elements rendered after the label

### Removed
- "Scene Presence" collapsible section from `ProfileViewer` — duplicated the Scene Appearances panel in the cross-reference grid but with unlinked plain-text chips; `Film` icon and `scenePresence` variable cleaned up

## [2026-02-23-03] — Entity cross-linking: prop edges, scene_presence, associated_characters (Story 045)

### Added
- `characters_present_ids` field on `Scene` and `SceneIndexEntry` — slugified entity IDs alongside display-name `characters_present`, used by entity_graph for accurate co-occurrence edges
- `associated_characters` field on `PropBible` — AI-extracted slugified character IDs representing signature ownership (e.g. Mariner's oar, Rose's purse)
- `_find_scene_presence()` in `prop_bible_v1` — deterministic scan of canonical_script line spans to populate `scene_presence` reliably instead of relying on AI
- `_generate_signature_edges()` in `entity_graph_v1` — emits `signature_prop_of` edges (conf=0.95) from `associated_characters`
- Prop co-occurrence edges in `entity_graph_v1` — prop↔character and prop↔location edges (conf=0.9) from `scene_presence`
- Props subsection on scene detail pages — inferred from prop bibles' `scene_presence` via UI-side filter
- Unresolved entity links now render with `opacity-50` and tooltip instead of appearing identical to resolved links

### Fixed
- `entity_graph_v1` prop_list prompt bug: was always empty string due to wrong `prop.get("files", [])` key
- `entity_graph_v1` co-occurrence ID mismatch: `char.lower()` → `_slugify(char)` for consistent entity IDs
- `scene_analysis_v1` was not emitting `characters_present_ids` in its enriched scene output, causing the field to be empty after the AI enrichment pass

## [2026-02-23-02] — Streaming artifact yield: live per-entity progress in sidebar (Story 052)

### Added
- `scene_breakdown_v1` now calls `announce_artifact` per scene as each completes, so sidebar "Scenes" count ticks up one at a time instead of jumping at stage completion.
- Sidebar nav category rows light up with a soft teal glow when a new entity lands, fading over 3 seconds. Rapid additions each reset the animation for a cascading effect across categories.
- Two new engine unit tests: `test_announce_artifact_persists_mid_stage` (verifies mid-stage announce with no duplication) and `test_announce_artifact_batch_fallback_still_works` (confirms batch-path backwards compat).

### Changed
- `scene_breakdown_v1/main.py`: replaced `del context` with `announce = context.get("announce_artifact")`.
- `AppShell.tsx`: extracted main nav rows into `NavItem` component with row-level glow animation.

## [2026-02-23-01] — Artifact graph staleness: regression tests + sibling cross-contamination fix (Story 074)

### Fixed
- `DependencyGraph.propagate_stale_for_new_version`: sibling artifacts produced in parallel no longer marked stale via a shared intermediate node. Before BFS, builds a `latest_version` lookup per `(artifact_type, entity_id)`; when BFS reaches a node whose entity has a newer version in the graph, marks the node stale but stops BFS propagation there (downstream was already rebuilt from the newer version)

### Added
- `test_new_version_not_marked_stale`: regression test for Bug 1 (self-staleness) — newly-saved artifact must not appear in `get_stale()`
- `test_sibling_not_marked_stale_via_shared_intermediate`: regression test for Bug 2 (sibling cross-contamination) — sibling artifact remains VALID after a co-sibling's propagation crosses a shared intermediate

## [2026-02-22-12] — Add `after:` ordering-only stage dependency to recipe DSL (Story 073)

### Added
- `RecipeStage.after: list[str]` — ordering-only dependency field; stage waits for all `after` stages to complete but receives no data from them and is not subject to schema compatibility checks
- `after` included in topological sort (`resolve_execution_order`) and wave eligibility (`_compute_execution_waves`) so execution order is correctly enforced
- `after` included in stage fingerprint for correct cache invalidation
- 4 unit tests covering: ordering enforced, schema check skipped, no overlap with `store_inputs`, coexistence with `needs`

### Changed
- `recipe-world-building.yaml`: `entity_discovery` now uses `after: [analyze_scenes]` (was `needs: []` workaround) — expresses ordering intent correctly without false schema mismatch

## [2026-02-22-11] — Live entity discovery feedback during world-building runs (Story 072)

### Added
- `engine.py`: `announce_artifact` callback in context — modules call it per entity mid-stage to save with full lineage and emit an `artifact_saved` event with `entity_id`, `display_name`, and (for `entity_discovery_results`) candidate counts; `pre_saved` flag prevents double-save in the post-module loop
- `artifact_saved` event type emitted for all saved artifacts (mid-stage via announce and post-module via normal path)
- `use-run-progress.ts`: handles `artifact_saved` events for bible types — updates one in-place chat message per type ("Writing 3 character bibles…") as each entity lands, immediately invalidates sidebar artifact counts
- `index.css`: `@keyframes badge-pop` — teal brand-color flash at 1.45× scale, fades back to secondary over 1.5s with glow ring
- `ChatPanel.tsx`: smart auto-scroll — only scrolls to bottom if user is within 120px of bottom; preserves scroll position when user has scrolled up to review earlier messages

### Changed
- `character_bible_v1`, `location_bible_v1`, `prop_bible_v1`: switched from `zip(candidates, futures)` to `as_completed()` — entities announced to sidebar and chat as each LLM call completes rather than in a batch at stage end
- `hooks.ts`: `useArtifactGroups` accepts optional `refetchInterval` param
- `AppShell.tsx`: polls `useArtifactGroups` at 750ms during active run (no interval when idle); `CountBadge` uses `pulseCount` integer key to force Badge remount and restart `badge-pop` animation on each count increment
- `use-run-progress.ts`: bible progress spinners (`ai_status`) resolved to `ai_status_done` checkmarks when run completes

## [2026-02-22-10] — Post-smoke-test UI/UX fixes: insight ordering, display names, stage order

### Fixed
- `ProjectHome.tsx`: removed `syncMessages()` from stage-completion effect — it was overwriting in-memory state from the backend, racing with the in-flight insight stream and silently dropping streaming AI insight messages before they could be persisted
- `use-run-progress.ts`: insight placeholder now added before the "Next Steps" CTA so the insight streams in above the action button rather than below it (no more button jumping up the screen)
- `ui/src/lib/constants.ts`: `entity_discovery` now appears before `analyze_scenes` in the `world_building` stage display order — matches actual execution order (code-based discovery always finishes before LLM scene analysis)

### Changed
- `use-run-progress.ts` + `src/cine_forge/ai/chat.py`: AI insight prompt now uses user-facing recipe names ("Script Breakdown", "Deep Breakdown") instead of raw recipe IDs ("mvp_ingest", "world_building") — prompt includes instruction to never leak technical names

## [2026-02-22-09] — Refactor ingestion into 3-stage pipeline; fix graph staleness (Story 062)

### Added
- `scene_breakdown_v1` module: deterministic structural scene parsing (scene headings, elements, cast lists) — Tier 1 ingest, no LLM
- `scene_analysis_v1` module: LLM narrative enrichment (beats, tone, subtext, inferences) — Tier 2 world-building
- `tests/unit/test_scene_breakdown_module.py`, `tests/unit/test_scene_analysis_module.py`
- Story 072 (Pending): live entity discovery feedback as world-building runs

### Changed
- `recipe-mvp-ingest.yaml`: `extract_scenes` stage → `breakdown_scenes` (scene_breakdown_v1)
- `recipe-world-building.yaml`: added `analyze_scenes` stage (scene_analysis_v1); fixed `entity_discovery` schema dependency; bible stages now wait for `analyze_scenes`
- UI stage labels and order updated for `breakdown_scenes` / `analyze_scenes`

### Fixed
- `artifacts/graph.py`: `propagate_stale_for_new_version` no longer marks the newly-created artifact as stale (self-staleness via BFS through shared lineage ancestors)

### Removed
- `scene_extract_v1` module (monolithic scene extraction+enrichment — replaced by two-stage split)

## [2026-02-22-08] — Parallel bible extraction via ThreadPoolExecutor (Story 065)

### Changed
- `character_bible_v1`, `location_bible_v1`, `prop_bible_v1`: entity extraction loop now runs via `ThreadPoolExecutor` (default concurrency 5). Per-entity failures are caught and logged without crashing the module. Cost aggregated thread-safely in the main thread after all futures resolve.
- `recipe-world-building.yaml`: added `concurrency: 5` param to all three bible stages.
- `location_bible_v1`: fixed stale `claude-sonnet-4-5` default model → `claude-sonnet-4-6`.

## [2026-02-22-07] — Fix escalate model defaults; close Story 039

### Fixed
- `script_normalize_v1`: escalate fallback `claude-sonnet-4-6` → `claude-opus-4-6` (matches benchmark triad)
- `location_bible_v1`: escalate fallback `claude-sonnet-4-5` → `claude-opus-4-6` (missed in prior model update pass)

### Changed
- Story 039 marked Done; remaining checklist items (smoke test, config recalibration) deferred as non-blocking

## [2026-02-22-06] — Skill split: triage → triage-inbox + triage-stories; deep-research docs refresh

### Added
- `/triage-stories` skill: evaluates story backlog and recommends what to work on next

### Changed
- Renamed `/triage` to `/triage-inbox` for clarity alongside the new stories skill
- Updated deep-research docs: Google provider now configured, new `--provider`/`--mode deep` flags, `status`/`stub`/`check-providers` commands, removed stale streaming patch note

## [2026-02-22-05] — UI polish bundle: chat dedup, back nav, inbox read state (Stories 067, 068, 069)

### Fixed
- Chat navigation messages no longer duplicate on reload — stable activity IDs + backend upsert + client-side dedup safety net (Story 067)
- Back buttons now use browser history (`navigate(-1)`) instead of hardcoded routes, with fallback for direct-link opens (Story 068)

### Added
- Gmail-style read/unread inbox model with filter toggle (Unread/Read/All), per-item read indicators, and "Mark All Read" (Story 069)
- Shared `inbox-utils.ts` with stable ID builders and `useHistoryBack` hook for cross-component reuse

### Changed
- Inbox nav badge now shows unread count only, persisted in project `ui_preferences`
- Back button labels changed from "Back to {X}" to generic "Back" (destination is unknowable with history-based nav)

## [2026-02-22-04] — Triage session: 5 new stories from inbox

### Added
- Stories 067–071: Chat nav dedup, back button history, inbox read state, script scene dividers & hotlinks, refine vs. regenerate pipeline modes.
- Triage skill prioritization step: evaluate inbox, recommend top items with rationale, flag defer candidates before walking through items individually.

### Changed
- Moved 5 triaged items from inbox Untriaged to Triaged section with story references.

## [2026-02-22-03] — Scout 001: Adopt Storybook skill improvements

### Changed
- Restructured `/build-story` into 3 explicit phases (Explore → Plan → Implement) with mandatory human gate before implementation and runtime smoke test as hard guardrail.
- Added `## Plan` section to story template for auditable plan artifacts that persist across sessions.

### Added
- `/decompose-spec` skill — systematic pipeline from spec.md → feature map → coverage matrix → stories.
- `/webapp-testing` skill — Playwright-based web testing toolkit with `with_server.py` helper for server lifecycle.
- Scout expedition system (`docs/scout.md` index + `docs/scout/scout-001-storybook-repo.md`).
- Gemini CLI wrappers for new skills.

## [2026-02-22-02] — UI Component Deduplication & Template Consolidation (Story 066)

### Changed
- Replaced 4 near-identical entity list pages (`CharactersList`, `LocationsList`, `PropsList`, `ScenesList`) with a single parameterized `EntityListPage` component (~350 lines replacing ~1006 lines).
- Consolidated `healthBadge` (9+ inline copies → `HealthBadge.tsx`), `artifactMeta` (2 copies → `artifact-meta.ts`), `timeAgo` (3 copies → `format.ts`), `formatDuration` (2 copies → `format.ts`), status badge/icon (3 copies → `StatusBadge.tsx`), page headers (4+ copies → `PageHeader.tsx`).
- Added AGENTS.md "UI Component Registry" (10 entries) and "Mandatory Reuse Directives" (8 rules with file paths) to prevent AI agent code duplication.

### Fixed
- `timeAgo()` seconds-vs-milliseconds mismatch in `ProjectHome.tsx` — standardized on millisecond input.
- `null`-null handling in script-order sort inconsistent across 4 list pages — unified in `EntityListPage`.
- `paused` run status only styled in `RunDetail` — now handled in shared `StatusBadge` for all pages.

### Added
- `jscpd` copy-paste detection with 5% threshold, runnable via `pnpm --dir ui run lint:duplication`.

## [2026-02-22-01] — Screenplay Format Round-Trip & High-Fidelity Rendering (Story 064)

### Added
- **Round-Trip Fidelity Suite**: Automated `pytest -m round_trip` tests for Fountain↔PDF and FDX↔Fountain↔FDX with golden master masters.
- **afterwriting Integration**: Switched to `afterwriting` as the primary PDF renderer for industry-standard screenplay formatting (Courier 12pt, WGA margins, CONT'D markers).
- **pdfplumber Extraction**: Implemented `pdfplumber` for high-fidelity text extraction from screenplay PDFs, preserving whitespace and column structure.
- **Low-Credit Chat Alerts**: Automatic project chat notifications when pipeline runs fail due to AI provider quota or billing issues.

### Changed
- **Automatic Promotion**: UI now favors the high-fidelity `canonical_script` version over raw input upon stage completion.
- **Metadata Healer**: Screenplay normalization now automatically heals title page blocks, mapping custom keys like "Alternate Title" to the professional cover page.
- **Enhanced Centering**: Broadened character cue detection to support smart quotes and extensions, ensuring correct centering for complex names.

### Fixed
- **L&C Formatting**: Resolved multiple issues where L&C PDF exports had missing cover pages or uncentered dialogue.
- **ASGI TypeError**: Fixed technical crash in export background cleanup task.
- **Word Metadata Tags**: Updated .docx export to strip Fountain metadata tags for a professional title page.

## [2026-02-21-04]
 — Automatic Project Title Extraction from Script (Story 063)

### Added
- Backend endpoint `POST /api/projects/quick-scan` for format-aware text extraction (PDF, DOCX, Fountain) from file snippets.
- `quick_scan` method in `OperatorConsoleService` to immediately identify project titles before full upload.
- Improved LLM title extraction prompt using `claude-sonnet-4-6` for higher precision on complex script headers.

### Changed
- Updated `NewProject` UI to trigger `quick-scan` immediately upon file selection, providing instant AI-detected project names.
- Upgraded default title extraction model from Haiku to Sonnet 4.6 to handle "Alternate Title" scenarios and complex formatting.

### Fixed
- Resolved issue where projects would default to sanitized filenames (e.g., "L C") instead of their creative titles (e.g., "Liberty and Church").
- Fixed binary snippet extraction for PDFs and DOCX files in the project creation flow.

## [2026-02-21-03]
 — Ingestion Pipeline Parallelization & Performance Optimization (Story 061)

### Added
- Parallel processing in `scene_extract_v1` using `ThreadPoolExecutor` for concurrent per-scene enrichment and QA.
- Parallel processing in `script_normalize_v1` for concurrent scene-level normalization fixes during "smart chunk-skip".
- Internal timing logs to `scene_extract_v1` and `project_config_v1` for bottleneck observability.
- `skip_qa` option to `project_config_v1` to allow bypassing sequential verification for faster ingestion.

### Changed
- Refactored ingestion modules to utilize multi-threading (default 10 workers), significantly reducing wait times for long scripts.
- Truncated script content in `project_config_v1` detection prompt to the first 500 lines to keep TTFT low and reduce token processing overhead.
- Updated `recipe-ingest-extract.yaml` to use `${model}` placeholders for improved runtime flexibility.

### Fixed
- Resolved the "lc-3 bottleneck" where long scripts took up to 25 minutes to ingest; reduced expected duration to ~3 minutes for similar inputs.
- Eliminated sequential LLM call stalls in the extraction and normalization stages.
- Fixed React 19 purity errors in `ProjectRun.tsx` (impure `Date.now()` and cascading `setState`).
- Cleared UI lint debt (legacy `any` and unused variables) to satisfy strict production build gates.

## [2026-02-21-02] — Comprehensive Export & Share (Story 058)

### Added
- New backend export module `src/cine_forge/export/` with `MarkdownExporter`, `PDFGenerator`, and `ScreenplayRenderer`.
- Support for industry-standard screenplay formats: PDF, DOCX, and Fountain.
- Professional Project Analysis Report PDF with record-based layouts and enriched metadata.
- Unified CLI command `python -m cine_forge export` for headless operation.
- New API endpoints for component-aware artifact exports.
- Granular export selection UI in `ExportModal.tsx` with component checkboxes and "Check All/None" helpers.

### Changed
- Refactored `ExportModal` into a tabbed interface separating Screenplay and Project Data workflows.
- Migrated all export logic from frontend to backend to support AI headless operation.
- Standardized Courier 12pt and industry-standard margins/indents for screenplay exports.

### Fixed
- Resolved `doc.autoTable` and horizontal space errors in PDF generation.
- Fixed title page formatting to strictly follow script preamble and separate it from content.
- Fixed clipping of long project titles on PDF cover pages.
- Fixed missing script content in Fountain and Markdown exports.

## [2026-02-21-01] — Pipeline UI Refinement & Entity Quality Fixes (Story 059, 060)

### Added
- Standardized headers across all run-related UI views to show bold Recipe Name and muted Status (e.g., **Script Intake** Running).
- Added stat cards (Total Cost, Duration, Model, Stages) to the active pipeline run progress page for real-time visibility.
- Enabled horizontal scrolling in the main content area to handle grid overflows gracefully.
- Added "Back to Runs" button to the Run Detail and Pipeline configuration pages.
- New unit test `tests/unit/test_character_naming_regression.py` to prevent "The [Entity]" naming drops.

### Changed
- Refactored `ProjectRuns.tsx` to use human-readable recipe names instead of cryptic run IDs.
- Removed fixed width constraints (`max-w-5xl`) from run views to allow dynamic resizing when the chat panel is open.
- Unified character name normalization logic across `entity_discovery_v1` and `character_bible_v1`.
- Made `store_inputs_all` permissive in DriverEngine to allow runs to proceed even if no existing artifacts of that type are found.

### Fixed
- Fixed critical bug where "THE MARINER" was dropped from character bibles due to stopword rejection after a normalization failure.
- Fixed navigation trap where clicking "Start New Run" wouldn't clear the previous run context.
- Fixed `KeyError: 'data'` in `entity_discovery_v1` when processing unwrapped artifact inputs in Refine Mode.
- Fixed layout issues where stat cards and artifact grids were cut off when side panels were open.

## [2026-02-20-04] — Artifact Quality Improvements (Story 041)

### Added
- New `entity_discovery_v1` module implementing an incremental AI-first "sliding window" discovery pass.
- Supports **Refine Mode** in `entity_discovery_v1` — can bootstrap from existing `character_bible`, `location_bible`, and `prop_bible` artifacts to extend or normalize them.
- `EntityDiscoveryResults` schema for consolidated candidate tracking.
- Benchmark tasks for Liberty & Church: Golden list generation, prompt comparison, and Haiku discovery validation.
- Added "Refine World Model" action button to chat interface after project completion.

### Changed
- `world_building` recipe now includes `entity_discovery` as a prerequisite stage and optionally re-ingests existing bibles.
- `character_bible_v1`, `location_bible_v1`, and `prop_bible_v1` now prioritize candidates from the discovery pass.
- `scene_extract_v1` now enforces narrative analysis (beats, tone) during the enrichment pass.
- Centralized pipeline stage ordering logic to ensure "Entity Discovery" consistently appears as the first stage in "World Building" across all UI views.
- Standardized `ProjectRun` layout width to `max-w-5xl` for visual consistency.

### Fixed
- Fixed sparse scene analysis in long screenplays by ensuring narrative fields trigger AI enrichment.
- Resolved "black screen" crash in `ProjectRun.tsx` caused by race conditions during stage loading.
- Cleared critical UI lint debt: fixed conditional hooks, declaration order, and forbidden ref access during render.
- Improved schema validation resilience in the driver pipeline.

## [2026-02-20-03] — Entity Prev/Next Navigation (Story 057)

### Added
- New `useEntityNavigation` hook in `ui/src/lib/hooks.ts` for sequential entity traversal.
- Navigation header in `EntityDetailPage.tsx` with previous/next buttons.
- Keyboard shortcuts (←/→) for navigating between entities.
- Chronological navigation for scenes (always script-order, regardless of active sort).
- Shared `formatEntityName` utility in `ui/src/lib/utils.ts`.
- Shared sorting and density types in `ui/src/lib/types.ts`.

### Changed
- Refactored `CharactersList`, `LocationsList`, `PropsList`, and `ScenesList` to use centralized sorting types and name formatting.
- Improved `EntityDetailPage` hook ordering to comply with React strict rules (no conditional hooks).

### Fixed
- Fixed lint errors across UI list pages (const vs let, unused variables, dependency arrays).

## [2026-02-20-02] — Human control modes, creative sessions, and direct artifact editing (Story 019)

### Added
- Three configurable operating modes: `autonomous`, `checkpoint`, and `advisory`.
- `Checkpoint` mode pipeline enforcement in `DriverEngine` (stage-by-stage pauses).
- Creative Session infrastructure in chat assistant via `talk_to_role` tool.
- Multi-role `@role_id` addressing and domain-specific expert consultation.
- Project Inbox UI for review management and bulk approval.
- Direct artifact editing with background agent notification and commentary.
- New `stage_review` artifact type for audit-ready approval tracking.
- Backend endpoints for run resumption and review responses.
- Full unit/integration coverage for interaction modes and gating.

### Changed
- `ProjectConfig` and project settings now track `human_control_mode`.
- `DriverEngine` integrated with `CanonGate` for review orchestration.
- Operator Console UI updated with mode selector, inbox, and review viewers.
- `RunProgressCard` now handles `paused` state with live status indicators.

### Fixed
- Fixed thread-safety issues when multiple stages write to shared invocation logs.
- Resolved module export errors in TypeScript for `ProjectSummary`.
- Fixed 500 errors in project settings updates via correct Pydantic serialization.
- Corrected indentation and assertion failures in existing integration suites.

## [2026-02-20] — Inter-role communication protocol and conversation artifacts (Story 018)

### Added
- New conversation and disagreement schemas:
  - `src/cine_forge/schemas/conversation.py` (`Conversation`, `ConversationTurn`, `DisagreementArtifact`)
- New conversation management logic:
  - `src/cine_forge/roles/communication.py` (`ConversationManager` for multi-role review orchestration)
- Multi-role review orchestration:
  - `ConversationManager.convene_review` allows the Director to gather input from multiple roles and synthesize a decision.
- Disagreement recording:
  - `ConversationManager.record_disagreement` captures objections and resolution rationales with links to conversations and artifacts.
- Story-018 coverage:
  - `tests/unit/test_communication.py`
  - `tests/integration/test_communication_integration.py`

### Changed
- `RoleResponse` and `RoleContext` updated to track `suggestion_ids` for turn-to-suggestion linking.
- `DriverEngine` schema registry updated with `conversation` and `disagreement` types.

## [2026-02-20] — Creative suggestion and editorial decision tracking (Story 017)

### Added
- New suggestion and decision schemas:
  - `src/cine_forge/schemas/suggestion.py` (`Suggestion`, `Decision`, `SuggestionStatus`)
- New suggestion management logic:
  - `src/cine_forge/roles/suggestion.py` (`SuggestionManager` for lifecycle, querying, and stats)
- Automated suggestion capture:
  - `RoleContext.invoke` now automatically persists suggestions emitted in role responses as immutable artifacts.
- Suggestion resurfacing:
  - `CanonGate` now automatically resurfaces deferred suggestions during scene-stage reviews.
- Story-017 coverage:
  - `tests/unit/test_suggestion_system.py`
  - `tests/integration/test_suggestion_integration.py`

### Changed
- `RoleResponse` schema now includes optional `suggestions` field.
- `StageReviewArtifact` now includes `deferred_suggestions` list for auditability.
- `DriverEngine` schema registry updated with `suggestion` and `decision` types.

## [2026-02-20] — Style Pack infrastructure and built-in example profiles (Story 016)

### Added
- Folder-based `StylePack` infrastructure for creative persona profiles:
  - `src/cine_forge/roles/style_packs/` (built-in repository)
  - `StylePack` and `StylePackFileRef` schema enhancements (`audio_reference` kind)
- Style pack management and validation:
  - `RoleCatalog.list_style_packs(role_id)` for dynamic discovery
  - `RoleCatalog.load_style_pack` with role-type and permission validation
- Creative research templates:
  - `style_pack_prompt.md` templates for Director, Visual Architect, Sound Designer, Editorial Architect, and Actor Agent.
- Built-in `generic` style packs for all creative roles.
- High-fidelity example style packs:
  - Director: `tarantino`
  - Visual Architect: `deakins`
  - Sound Designer: `lynch`
  - Editorial Architect: `schoonmaker`
  - Actor Agent: `ddl` (Daniel Day-Lewis)
- Automated verification:
  - `tests/unit/test_style_packs.py` (catalog/context logic)
  - `tests/integration/test_style_pack_integration.py` (lifecycle + prompt injection)

### Changed
- `RoleContext` now injects style-pack content into system prompts during role invocation.
- `RoleDefinition` schemas and role YAMLs now explicitly declare `style_pack_slot` (accepts/forbidden).

## [2026-02-20] — Director and Canon Guardians stage-gating workflow (Story 015)

### Added
- Canon-level role behaviors and hierarchy enforcement:
  - `src/cine_forge/roles/canon.py` (`CanonGate` orchestration)
  - Director authority (canon authority), Script Supervisor and Continuity Supervisor (canon guardians).
- Stage completion gating:
  - `StageReviewArtifact` schema for immutable review persistence.
  - `ReviewDecision`, `ReviewReadiness` enums.
  - Disagreement protocol (objection + override justification records).
- Automated verification:
  - `tests/unit/test_canon_gate.py`
  - `tests/integration/test_canon_gate_integration.py`

### Changed
- Role YAMLs updated with specific guardian/authority system prompts and capabilities.
- Driver schema registry now includes `stage_review`.
- Director and Continuity Supervisor now declare `image` perception capability.

## [2026-02-20] - Role system foundation infrastructure for AI persona runtime (Story 014)

### Added
- New role-system schemas for hierarchy/runtime/style-pack contracts:
  - `src/cine_forge/schemas/role.py` (`RoleDefinition`, `RoleResponse`, `StylePack`)
- New role runtime implementation:
  - `src/cine_forge/roles/runtime.py` (`RoleCatalog`, `RoleContext`, hierarchy + capability gates, invocation audit logging)
- Skeleton role definitions for Director, Script Supervisor, Continuity Supervisor, Editorial Architect, Visual Architect, Sound Designer, and Actor Agent under `src/cine_forge/roles/*/role.yaml`.
- Generic default style packs for style-pack-accepting roles under `src/cine_forge/roles/style_packs/*/generic/`.
- Story-014 coverage:
  - `tests/unit/test_role_system.py`
  - `tests/integration/test_role_system_integration.py`

### Changed
- Driver schema registry now includes `role_definition`, `role_response`, and `style_pack` (`src/cine_forge/driver/engine.py`).
- Schema exports updated to include role-system types (`src/cine_forge/schemas/__init__.py`).
- Role permission semantics aligned to artifact-type scope; model capability checks now validate invocation-requested media types.
- Story tracking updated with Story 014 marked done and full completion evidence (`docs/stories/story-014-role-system-foundation.md`, `docs/stories.md`).

## [2026-02-20] - Track system artifact and always-playable backend resolution (Story 013)

### Added
- New track schemas for immutable track state:
  - `src/cine_forge/schemas/track.py` (`TrackEntry`, `TrackManifest`)
- New timeline track-system module:
  - `src/cine_forge/modules/timeline/track_system_v1/main.py`
  - `src/cine_forge/modules/timeline/track_system_v1/module.yaml`
- New recipe for cross-recipe track manifest construction:
  - `configs/recipes/recipe-track-system.yaml`
- New Story-013 test coverage:
  - `tests/unit/test_track_system_module.py`
  - `tests/integration/test_track_system_integration.py`

### Changed
- Driver schema registry now includes `track_manifest` (`src/cine_forge/driver/engine.py`).
- Schema exports now include `TrackEntry` and `TrackManifest` (`src/cine_forge/schemas/__init__.py`).
- Story tracking updated: Story 013 marked done in `docs/stories.md` and completion evidence recorded in `docs/stories/story-013-track-system.md`.

## [2026-02-20] - Story 054/055 completion, LLM-first entity adjudication, and Mariner fallback fix

### Added
- Story 054 artifact investigation deliverables:
  - `docs/reports/liberty-church-2-artifact-inventory.md`
  - `tests/fixtures/liberty_church_2/prod_snapshot_2026-02-19/` (prod snapshot for reproducible debugging)
  - story record: `docs/stories/story-054-liberty-church-character-artifact-cleanup-inventory.md`
- Story 055 implementation story record:
  - `docs/stories/story-055-llm-first-entity-adjudication-for-character-location-prop.md`
- Shared entity adjudication contract:
  - schema: `src/cine_forge/schemas/entity_adjudication.py`
  - helper: `src/cine_forge/ai/entity_adjudication.py`

### Changed
- World-building modules now run LLM adjudication before bible emission:
  - `character_bible_v1`, `location_bible_v1`, `prop_bible_v1`
- Added adjudication decision-trace annotations into artifact metadata for debugging and prompt tuning (`decision_trace`, rationale/confidence, outcomes).
- Added runtime model-slot fallback in world-building modules to honor `default_model`, `utility_model`, and `sota_model` passed via runtime params.
- Expanded unit coverage for adjudication outcomes (`valid`, `invalid`, `retype`) across character/location/prop modules.
- Updated story index with Story 054 and Story 055 marked done (`docs/stories.md`).

### Fixed
- Resolved regression where a valid character could be dropped after adjudication if canonicalized name failed deterministic plausibility checks (e.g., `MARINER` with canonical `The Mariner`).
- Character adjudication now falls back to the original validated candidate when canonicalization fails plausibility, preventing false removals of core characters.

## [2026-02-19] - Re-align skills to CineForge architecture (Python-first + ui split)

### Changed
- Reworked validation/build/close-story skill flows to use CineForge-native checks instead of root `pnpm` assumptions.
- Updated `validate` skill to:
  - start with full local-diff audit
  - use scope-based check profiles (backend, UI, full-stack)
  - require `tsc -b` guidance for UI type-check parity
- Updated `build-story` skill to restore required story-section checks and repo-appropriate verification flow.
- Replaced deploy skill scaffold with CineForge-specific Fly.io deployment workflow:
  - preflight checks, API/UI smoke tests, failure protocol
  - duration logging/recalibration and runbook references
  - `--depot=false` guardrail
- Updated story template and related skills (`mark-story-done`, `run-pipeline`, `init-project`, `scout`) to remove non-CineForge assumptions and align wording/commands with this repo.

## [2026-02-19] - Timeline artifact implementation and ordering-model hardening (Story 012)

### Added
- New immutable `timeline` artifact model and schema:
  - `src/cine_forge/schemas/timeline.py`
  - schema exports in `src/cine_forge/schemas/__init__.py`
- New timeline build module:
  - `src/cine_forge/modules/timeline/timeline_build_v1/module.yaml`
  - `src/cine_forge/modules/timeline/timeline_build_v1/main.py`
- New timeline recipe:
  - `configs/recipes/recipe-timeline.yaml`
- Timeline-focused tests:
  - `tests/unit/test_timeline_module.py`
  - `tests/integration/test_timeline_integration.py`

### Changed
- Driver schema registration now includes `timeline`.
- Stage module context now includes `project_dir` for store-aware module execution.
- Recipe/engine input resolution now supports optional cross-recipe dependencies via `store_inputs_optional`:
  - `src/cine_forge/driver/recipe.py`
  - `src/cine_forge/driver/engine.py`
- Timeline reorder operations now require exact scene-id set matching (reject missing/extra IDs).
- Story tracking/docs updates:
  - Story 012 marked `Done` with full work log evidence.
  - Story 013 rewritten to align with current timeline-first architecture.
  - Story 046 annotated with architecture update note.

## [2026-02-19] - Full Storybook skill-pack sync (scout, triage, ADR/init, and create-story templates)

### Added
- Imported additional canonical skills from Storybook: `create-adr`, `init-project`, `scout`, and `triage`.
- Added `create-story` scaffolding assets:
  - `.agents/skills/create-story/scripts/start-story.sh`
  - `.agents/skills/create-story/templates/story.md`
  - `.agents/skills/create-story/templates/stories-index.md`
- Generated new Gemini wrappers for added skills:
  - `.gemini/commands/create-adr.toml`
  - `.gemini/commands/init-project.toml`
  - `.gemini/commands/scout.toml`
  - `.gemini/commands/triage.toml`

### Changed
- Synced shared existing skill definitions to Storybook’s latest canonical wording and workflow structure:
  - `build-story`, `check-in-diff`, `create-story`, `deploy`, `mark-story-done`, `validate`
- Regenerated `.gemini/commands/*.toml` wrappers from synced canonical skills.
- `deploy` Gemini wrapper removed because deploy is now non-invocable in canonical frontmatter (`user-invocable: false`).

## [2026-02-19] - Align cross-CLI skill system with latest storybook architecture

### Changed
- Updated `scripts/sync-agent-skills.sh` to match the new canonical flow:
  - parse arbitrary frontmatter fields
  - generate Gemini wrappers only for `user-invocable` skills
  - clear stale Gemini wrappers before regeneration
- Updated `.agents/skills/create-cross-cli-skill/SKILL.md` to require `user-invocable` metadata and include `templates/` as an optional colocated resource.
- Regenerated `.gemini/commands/*.toml` wrappers from canonical skill definitions after sync.

## [2026-02-19] - Cross-CLI skills unification and canonical agent skill layout (Story 053)

### Added
- Canonical skill source tree at `.agents/skills/` including `create-cross-cli-skill` meta-skill for portable skill creation.
- Skill synchronization tooling via `scripts/sync-agent-skills.sh` and Makefile targets `skills-sync` / `skills-check`.
- Gemini CLI compatibility wrappers generated under `.gemini/commands/*.toml` from canonical `SKILL.md` files.

### Changed
- Story tracking updated: Story 053 marked `Done` in both `docs/stories.md` and `docs/stories/story-053-cross-cli-skills-unification.md`.
- Claude and Cursor skill discovery now point to canonical source via symlinks (`.claude/skills`, `.cursor/skills`).
- Legacy prompt-era Cursor commands moved to `.cursor/commands.legacy/` to remove active duplication while preserving reference history.

## [2026-02-19] - Story 049 OCR-noisy PDF normalization fix and production validation

### Added
- Regression tests for OCR-noisy PDF screenplay handling in normalization:
  - `test_is_screenplay_path_detects_ocr_noisy_pdf_screenplay`
  - `test_run_module_routes_ocr_noisy_pdf_misclassified_as_prose_to_tier2`

### Fixed
- `script_normalize_v1` now preserves screenplay routing for OCR-noisy/misclassified PDF inputs instead of hard-rejecting to empty canonical script in Tier 3 when screenplay signals are present.
- Tier routing now still rejects true high-confidence prose, preventing false-positive screenplay promotion.

### Changed
- Story 049 marked done in `docs/stories.md` and `docs/stories/story-049-import-normalization-format-suite.md` after successful production validation on `the-body-4` input `d93d9cc3_The_Body.pdf`.
- Deploy timing log updated in `docs/deploy-log.md` with latest successful Fly deploy and smoke evidence.

---

## [2026-02-19] - Fix TypeScript build parity between local validation and production

### Fixed
- Validate and deploy skills now use `tsc -b` instead of `tsc --noEmit`, matching the production Docker build. `tsc --noEmit` silently skipped strict checks (`noUnusedLocals`) due to root `tsconfig.json` having `"files": []`.

---

## [2026-02-19] - Chat UX polish, progress card, live counts, and parallel execution (Story 051)

### Added
- `RunProgressCard` component: single updating widget replaces per-stage chat message spam, stages render in recipe-defined order with live status icons (pending/spinner/checkmark/error/cached).
- `ChangelogDialog` shared component: extracted from Landing and AppShell, with overflow fixes.
- Sidebar live count badges: Scenes, Characters, Locations, Props nav items show artifact counts with pulse animation on increment.
- Inbox unread count badge in sidebar navigation.
- Progress card artifact counts: inline summaries (e.g., "13 scenes, 4 characters") next to completed stages.
- Parallel stage execution: independent stages in the same wave run concurrently via `ThreadPoolExecutor`.
- Thread safety for `ArtifactStore` and `DependencyGraph` (write locks prevent TOCTOU races during parallel execution).

### Changed
- Chat message ordering: completion summary → AI insight → next-step CTA (previously out of order).
- Action button naming: "Break Down Script" / "Deep Breakdown" / "Browse Results" with plain-language descriptions.
- Button hierarchy: golden-path actions use `variant: 'default'`, navigation links use `variant: 'outline'`.
- Sidebar counts refresh mid-run by invalidating artifact queries on stage completion.

---

## [2026-02-19] - Provider resilience hardening, OCR runtime tooling, and deploy estimate recalibration

### Added
- Stage retry/fallback observability across run state and events, including per-attempt metadata and fallback transitions.
- New failed-stage resume endpoint: `POST /api/runs/{run_id}/retry-failed-stage`.
- Artifact metadata annotations for final model/provider used in each stage:
  - `final_stage_model_used`
  - `final_stage_provider_used`
- OCR-capable runtime dependencies in the production image (`poppler-utils`, `ocrmypdf`, `tesseract-ocr`, `tesseract-ocr-eng`, `ghostscript`).
- Deploy timing memory file: `docs/deploy-log.md`.

### Fixed
- Transient error classification now covers provider overload/capacity cases (including HTTP `529`) with exponential backoff + jitter.
- Provider circuit breaker behavior integrated into LLM transport to reduce retry storms and skip unhealthy providers.
- Resume-from-failure path now supports upstream reuse via prior artifact refs when stage cache is unavailable.
- Ingest/normalize/extract guards now fail fast on empty extracted/normalized screenplay text with actionable errors.

### Changed
- Story tracking updates:
  - Story 050 marked `Done` with resilience scope complete.
  - Story 049 reopened (`To Do`) for deferred OCR-noisy PDF normalization quality follow-up.
- Deploy skill now includes a required duration recalibration workflow using recent successful deploy medians.
- Deploy expected duration recalibrated to `~1.5 minutes` based on recent successful runs.

---

## [2026-02-18] - Centralized browser MCP runbook and hardened deploy smoke workflow

### Added
- New canonical browser automation + MCP runbook: `docs/runbooks/browser-automation-and-mcp.md`
- Cross-environment guidance for Codex, Cursor, Claude Code, and Gemini CLI MCP setup/recovery.
- Codex nested-browser validation pattern with deterministic evidence capture (`codex exec -o ...`, screenshot artifacts, console error summary).
- Observed failure-mode troubleshooting (wrong MCP config scope, missing log directories, verbose output handling, empty MCP resource list discrepancy).

### Changed
- `skills/deploy/SKILL.md` now references the canonical browser runbook instead of embedding long tool-specific troubleshooting.
- Deploy skill now includes:
  - cache-hit fast deploy interpretation guidance
  - explicit nested-Codex browser smoke path when direct in-session browser tools are unavailable
  - reporting requirements for screenshot paths + console error logs
- `AGENTS.md` now references the browser runbook in UI verification and deployment guidance.
- `docs/deployment.md` now points to the canonical browser runbook for environment-specific browser automation recovery.

---

## [2026-02-18] - PDF import preview fix and cross-format normalization test hardening

### Added
- Story docs for:
  - `story-048-pdf-input-preview-decode.md`
  - `story-049-import-normalization-format-suite.md`
- New ingest fixtures:
  - `tests/fixtures/ingest_inputs/patent_registering_votes_us272011_scan_5p.pdf`
  - `tests/fixtures/ingest_inputs/run_like_hell_teaser_scanned_5p.pdf`
- Expanded ingest/normalize coverage across all supported import formats (`txt`, `md`, `fountain`, `fdx`, `docx`, `pdf`) with semantic assertions.
- PDF extractor diagnostics for observability (`pdf_extractors_attempted`, `pdf_extractor_selected`, `pdf_extractor_output_lengths`).

### Fixed
- Project input preview endpoint now uses ingest extraction for supported formats, preventing raw binary UTF-8 decode garbage for PDFs.
- PDF extraction quality improved through staged fallback (`pdftotext -layout` -> `pypdf` -> `ocrmypdf`) plus layout repair handling.

### Changed
- `docs/stories.md` updated to include Stories 048 and 049 as Done.
- Wrapped overlong unit-test lines in `tests/unit/test_story_ingest_module.py` to satisfy Ruff and keep deployment preflight green.

---

## [2026-02-18] - Story 039 deferred evals, Gemini multi-provider fixes, and /deploy skill

### Added
- `/deploy` skill and canonical deployment runbook doc for repeatable production deploys (Story 037 follow-up).
- Three deferred promptfoo eval configs (location, prop, relationship) built and run across all 13 providers (Story 039).
- CalVer versioning (`YYYY.MM.DD`) derived from CHANGELOG.md; shown in sidebar footer and landing page.
- `/api/health` returns `version` field; `/api/changelog` serves full changelog as text.
- Clickable version badge opens changelog dialog in both AppShell and Landing page.
- UI smoke test added to `/deploy` skill (screenshots, console error check).

### Fixed
- Stale model defaults replaced after benchmarking revealed better-performing models per task (Story 039).
- Landing page version positioned in fixed bottom-left corner (matching sidebar pattern).

### Changed
- Trimmed `AGENTS.md` operational noise; moved deployment detail to dedicated doc.
- Story 038 marked done; Story 039 scope expanded to include deferred eval coverage.

---

## [2026-02-17] - Production deployment, Gemini support, Sonnet 4.6 benchmarks, and Story 037-038-047

### Added
- Deployed CineForge to production at `cineforge.copper-dog.com` on Fly.io with Let's Encrypt SSL, Cloudflare DNS, and a persistent 1GB volume (Story 037).
- Multi-provider LLM transport with Google Gemini support (`gemini-2.5-flash`, `gemini-2.5-pro`); backend now routes to Anthropic, OpenAI, or Google based on model ID prefix (Story 038).
- Story 045 (Entity Cross-Linking) and Story 046 (Theme System) draft files added to backlog.

### Fixed
- `PermissionError` crash on Fly.io when the volume `lost+found` directory was encountered during project discovery.
- Untracked `.claude/settings.local.json` from git and added it to `.gitignore`.

### Changed
- Benchmarked Sonnet 4.6 across all six promptfoo evals (character extraction, scene extraction, location, prop, relationship, config detection) against 12 other providers; updated model defaults in `src/cine_forge/schemas/models.py` with winning models per task (Story 047).

---

## [2026-02-16] - Conversational AI Chat, Entity-first Navigation, UI wiring, and pipeline performance

### Added
- Conversational AI Chat (Story 011f): full six-phase implementation including streaming AI responses, persistent chat thread, knowledge layer surfacing relevant artifacts into context, inline tool-use for running pipeline stages, smart suggestions, and lint cleanup.
- Entity-first navigation (Story 043): dedicated Character, Location, and Prop detail pages with cross-references; enriched sorting by narrative prominence; script-to-scene deep links; breadcrumbs; sticky sort/density preferences persisted to `project.json`.
- Story 041 (Artifact Quality Improvements) story file added; immediately implemented as Story 042 after renumbering.

### Fixed
- Wired all mock UI components to real backend APIs, replacing placeholder data with live artifact fetches (Story 042).
- Entity ID consistency across detail pages; breadcrumb navigation and artifact UX polish (Story 042).
- World-building cost explosion caused by unnecessary QA passes: hardcoded `skip_qa` and removed dead recipe references.
- Landing page now shows 5 most recent projects with timestamps and an expand/collapse toggle.

### Changed
- `ui/operator-console/` directory flattened to `ui/` — Story 043 done and directory structure simplified.
- Pipeline performance optimized (Story 040): reduced redundant AI calls, improved stage caching, and lowered median run cost.
- Chat-driven progress replaces polling: server-side chat events drive run state updates (Story 011e Phases 1.5–2.5).
- Project identity now uses URL slugs (`/projects/:slug`) rather than numeric IDs; chat state persisted server-side (Story 011e).

---

## [2026-02-15] - Operator Console production build, promptfoo benchmarking, and model selection

### Added
- Production Operator Console build (Story 011d): full React + shadcn/ui UI with file-first project creation, script-centric home page, story-centric navigation (Script / Scenes / Characters / Locations / World / Inbox), and chat panel as the primary interaction surface.
- Script-centric home page and chat panel Phase 1 implementation (Story 011e): chat replaces sidebar hints; Inbox is a filtered view of `needs_action` chat messages.
- promptfoo benchmarking tooling evaluation complete (Story 035): workspace structure, dual evaluation pattern (Python scorer + LLM rubric), cross-provider judge strategy, and pitfalls documented in `AGENTS.md`.
- Model Selection and Eval Framework (Story 036): character extraction eval across 13 providers; Opus 4.6 established as judge; winning models recorded per task.
- Claude Code skills wired up via `.claude/skills/` symlinks for agent discovery.

### Changed
- Story 011b Operator Console research and design decisions documented and complete.
- Story 011c phase summary and recommended order synced in story file.
- `AGENTS.md` updated with benchmarking workspace structure, eval catalog, model selection table, and lessons learned (promptfoo pitfalls: `max_tokens` trap, `---` separator trap, Gemini token budget).

---

## [2026-02-14] - World-building pipeline, Entity Relationship Graph, 3-Recipe Architecture, and UI routing

### Added
- High-fidelity world-building infrastructure: bible generation modules, resilient LLM retry logic with token escalation, and catch-and-retry on malformed JSON (`src/cine_forge/ai/llm.py`).
- Entity Relationship Graph module: AI-powered entity extraction, `needs_all` orchestration pattern, and selective per-entity re-runs.
- Basic UI visualization for the Entity Relationship Graph.
- 3-Recipe Architecture (Intake / Synthesis / Analysis): partitions pipeline into independently runnable segments with human-in-the-loop gates between expensive world-building steps.
- Continuity tracking foundation added alongside 3-Recipe Architecture.
- Resource-oriented routing foundation for Operator Console: identity in URL path, not search params.
- Stories 008 and 009 documented and marked done.

### Changed
- Enhanced Entity Graph with real AI extraction replacing stubs; selective re-run support added.
- `AGENTS.md`: added "No Implicit Commits" mandate; captured cross-recipe artifact reuse pattern via `store_inputs`; documented 3-Recipe Architecture lesson and resource-oriented UI principle.

---

## [2026-02-13] - Story 007c remediation, DOCX support, hot-reload, and bible module

### Added
- Semantic quality gates for degraded PDF ingestion: confidence scoring, anomaly detection, and remediation triggers to prevent schema-valid-but-useless artifacts (Story 007c).
- Unit and integration regression tests for Story 007c PDF quality remediation.
- DOCX ingestion support: `python-docx` based parser added to the ingest module; UI file picker now accepts `.docx` alongside `.pdf` and `.fountain`.
- Bible infrastructure and character bible module: `CharacterBible` schema, AI-driven extraction, and versioned artifact output.
- All missing story files (008–034) scaffolded with design foundations.

### Fixed
- Hot-reloading enabled for the Operator Console backend via `uvicorn --reload`; eliminates manual restarts during local development.

### Changed
- Story index (`docs/stories.md`) updated to reflect new stories and status changes.

---

## [2026-02-13] - Deliver Operator Console Lite and add MVP fidelity remediation story

### Added
- New Operator Console Lite backend service under `src/cine_forge/operator_console/` with project lifecycle, run start/state/events, artifact browsing, recent-project discovery, and input upload endpoints.
- New React + Vite UI under `ui/operator-console-lite/` with file-first project creation (drag/drop + file picker), run controls, runs/events inspection, artifact browser, and on-demand project switcher drawer.
- New test coverage:
  - `tests/unit/test_operator_console_api.py`
  - `tests/integration/test_operator_console_integration.py`
  - `ui/operator-console-lite/e2e/operator-console.spec.ts`
- New remediation planning story `docs/stories/story-007c-mvp-reality-remediation.md` to address real-run artifact fidelity issues discovered via UI-led validation.

### Fixed
- Resolved local dev CORS failures causing UI "Failed to fetch" by allowing localhost/127.0.0.1 origins across local ports in Operator Console API middleware.
- Improved artifact browser UX with explicit selected group/version highlighting and auto-selection of latest/single version.
- Stabilized Playwright test startup behavior in UI config for deterministic local runs.

### Changed
- Updated Story 007b acceptance/task wording to align with approved UX (`Project Switcher` replacing dedicated `Open Project` route while preserving open-existing-project functionality).
- Updated docs in `README.md` and story index in `docs/stories.md` for Operator Console flows and new 007c scope.
- Extended project guidance in `AGENTS.md` for mandatory manual UI verification and captured pitfalls from recent execution.
- Updated `.gitignore` for UI build/test artifacts (`*.tsbuildinfo`, `test-results/`, `playwright-report/`).

## [2026-02-13] - Complete Story 007 MVP recipe smoke coverage and runtime parameter UX

### Added
- New Story 007 end-to-end recipe at `configs/recipes/recipe-mvp-ingest.yaml` with runtime placeholders for input/model/acceptance controls.
- New Story 007 fixture corpus under `tests/fixtures/` including screenplay/prose inputs and mocked AI response bundles for normalization, scene QA, and project config detection.
- New integration suite `tests/integration/test_mvp_recipe_smoke.py` covering mocked smoke, live-gated smoke, staleness propagation, and fixture integrity preflight checks.
- New CLI unit coverage in `tests/unit/test_driver_cli.py` for `--params-file` loading, `--param` override precedence, and non-mapping params-file rejection.

### Fixed
- Resolved live structured-output schema failures by rebuilding normalization envelope models and tightening project-config detected-field typing.
- Repaired mocked fixture regression by replacing empty per-scene fixture files with valid JSON and adding preflight validation to prevent recurrence.

### Changed
- Driver CLI now supports generic runtime parameter injection via `--param` and `--params-file`, with improved failure summaries and success output.
- Driver runtime now resolves `${...}` recipe placeholders before validation/execution and supports optional stage-level lineage aggregation for aggregate artifacts.
- Updated Story 007 docs/work-log status to Done and synchronized story index status in `docs/stories.md`.
- Added `smoke-test` and `live-test` Make targets and expanded README runbook docs for MVP smoke execution and artifact inspection.

## [2026-02-12] - Implement Story 006 project configuration module and confirmation flow

### Added
- New `project_config_v1` ingest module with AI-assisted project parameter detection, draft file output, confirmation modes (`--accept-config`, `--config-file`, `--autonomous`), and schema-validated draft/canonical artifact handling.
- New `ProjectConfig` and `DetectedValue` schemas, plus unit/integration coverage for schema validation, module behavior, and end-to-end project config persistence.
- New recipe `configs/recipes/recipe-ingest-extract-config.yaml` for ingest -> normalize -> scene extraction -> project config flow.
- New Story 019 scaffold at `docs/stories/story-019-human-interaction.md` to track deferred non-CLI interaction scope (web UI / Director chat).

### Changed
- Driver runtime now supports config confirmation flags, stage pause state (`paused`), and runtime fingerprint hashing of `input_file`/`config_file` contents for safer cache invalidation.
- Driver schema registry now includes `project_config`.
- Story tracking updates: Story 006 marked `Done` with completed acceptance/tasks/work-log evidence, and deferred interaction scope moved to Story 019.
- Added driver tests proving stale propagation for downstream artifacts when `project_config` changes.

## [2026-02-12] - Implement Story 005 scene extraction pipeline

### Added
- New `scene_extract_v1` ingest module with deterministic-first scene splitting, structured element extraction, provenance tracking, selective AI enrichment, and per-scene QA retry handling.
- New scene schemas (`Scene`, `SceneIndex`, and supporting models) in `src/cine_forge/schemas/scene.py`.
- New extraction recipe `configs/recipes/recipe-ingest-extract.yaml` chaining ingest -> normalize -> extract.
- New unit and integration coverage for scene schemas, extraction behavior, parser/fallback benchmarks, and end-to-end artifact persistence.
- New Story 005 parser evaluation note at `docs/research/story-005-scene-parser-eval.md`.

### Changed
- Driver schema registration now includes `scene` and `scene_index`.
- Driver multi-output validation now resolves schema per artifact (`schema_name`/`artifact_type`) to avoid cross-schema false failures.
- Story tracking updates: Story 005 marked `Done` in `docs/stories.md` and `docs/stories/story-005-scene-extraction.md`.
- Added AGENTS effective pattern documenting per-artifact schema selection for multi-output stages.

Ideas, links, and resources captured for triage. Newest first.
Triaged together via `/triage` skill in AI agent sessions.

## Untriaged

- nano banana 2 templates would be useful for global style transfers: https://x.com/geminiapp/status/2027081255804870985?s=12&t=uFZE-MuhgWdh1YErEZzLtQ

- Runway Character Rendered App: https://x.com/runwayml/status/2027411005509161375?s=20

### ADR-003 Deferred Ideas

- 20260227: **Film decomposition / remix**: Take any existing film, decompose it into CineForge artifacts (screenplay, character bibles, visual references, sound design, direction), modify any element, re-render. E.g., take Pulp Fiction, recast a character, change the ending. The round-trip decomposition test (decompose → re-render → compare) is an Ideal vision preference; the remix feature itself is far-future. *(Source: ADR-003, Decision #8)*

- 20260227: **AI enhancement of minimal inputs**: Headshot → full character reference set (multiple angles, expressions, lighting). Phone video of location → clean reference stills from multiple angles. "Take whatever we can get and back-create proper artifacts from it." Leverages image gen models with uploaded asset as conditioning. *(Source: ADR-003, Decision #9)*

- 20260227: **Location lookup from web**: Given a location name ("Sydney Opera House"), fetch public images from the web to use as reference. Use real building facades and create fictional interiors. Needs web search/image API integration. *(Source: ADR-003, Decision #9)*

- 20260227: **Mood-board synthesis input**: Feed in multiple inspiration images (hairstyles, environments, objects, textures) as reference material for AI to synthesize into character/location/prop designs. "This hairstyle + this jacket + this vibe → character design." Natural extension of reference image system. *(Source: ADR-003, Decision #9)*

### UI / Interaction

- 20260226: **Narrative-aware timeline export**: When exporting to NLE formats (OpenTimelineIO, Final Cut XML, AAF, EDL), embed CineForge's narrative structure as timeline markers, color-coded regions, and clip notes. Scene boundaries, beat changes, character entrances, emotional tone shifts — metadata that no other AI video tool has because they don't understand story structure. Makes the editor's job dramatically easier. Formats: single video, scene folder, and NLE interchange formats.

- 20260226: **Video preview/assembly view**: Simple video player with a scene strip below it — drag to reorder scenes, click to play from any point, basic trim handles. NOT a full NLE, just enough to preview flow and make coarse adjustments before export. Think iMovie simplified timeline, not Premiere.

- 20260226: **Scene Workspace (View 2)**: Per-scene production control center. Shows the scene's inputs (characters, location, props, direction, storyboard) as tiles with red/yellow/green readiness indicators. Red = raw text only (AI guesses everything), yellow = bibles but no reference images (inconsistent visuals), green = fully specified. "Make all green" button runs missing pipeline stages. Click any element to drill into its detail page. This is the filmmaker's primary workspace — NOT an NLE, but a generation control surface. See ADR-002 design discussion (2026-02-26 session).

- 20260226: **Two-view architecture**: CineForge has two primary views — (1) Story Explorer (existing: script/scenes/characters/locations/props nav) for narrative exploration and (2) Scene Workspace (new) for production readiness and generation. Both operate on the same artifact data. A third "view" is export (video file, scene folder, NLE interchange formats). No built-in NLE — users export to their editor of choice.

- 20260226: **Kill pipeline DAG view (Story 091 deleted)**: ADR-002 Layer 3 called for an on-demand DAG visualization of the 19 pipeline nodes. After design discussion, decided this is wrong — the pipeline is invisible plumbing. This matches our own design principle from `docs/design/decisions.md`: "The pipeline DAG is not shown to users. The word 'pipeline' never appears in the primary UI." The pipeline bar (Story 085) provides sufficient ambient awareness. The Scene Workspace is the right "big picture" view, not a node graph. Story 091 was created and deleted in the same session.

- 20260226: **No built-in NLE — export instead**: Don't build a video editor. NLE is a solved problem (DaVinci Resolve is free), building a good one is years of work, and filmmakers already have tools they love. CineForge's job is to generate and assemble. Export formats: single video, scene folder, and NLE interchange (OpenTimelineIO, Final Cut XML, AAF, EDL). The video preview/assembly view (see above) handles the "watch it through and reorder" need without being a full editor.

- 20260226: **CineForge's differentiator is quality intelligence, not timeline/NLE**: Competitors: LTX Studio (script → storyboard → scene editor → timeline), Saga (script + storyboard + NLE editor), Kling 3.0 (multi-shot up to 6 cuts per generation), Runway Gen-4 (reference images for cross-shot character consistency). What NONE of them do well: structured reasoning about quality. CineForge's pipeline graph, readiness model, "here's what AI guessed vs. what you specified" transparency, and ability to trace bad output back to missing upstream artifacts — that's the unique value. Build there, not on commodity NLE.

- 20260226: **"AI-filled" / skip-ahead state**: When a user hits "generate" without completing all upstream steps, AI fills gaps from whatever exists. This creates a new artifact state beyond completed/not_started: "AI-inferred." Every AI-guessed element should be visibly labeled. Example: you have a script and bibles but no reference images — AI generates video but characters look different every scene because there's no visual anchor. Each element in the Scene Workspace would show this state. Needs more design work — how to represent quality degradation, what the "AI guessed this" indicator looks like, whether users can retroactively upgrade (generate reference images, then re-render). Ties into the preflight tiered response system (Story 087).

- 20260226: **Prompt transparency / direct prompt editing**: For ANY AI-generated output (reference photos, video, music, sound effects, voices), let users see the exact prompt that generated it and edit/re-submit directly. This is a powerful creative control that treats prompts as first-class editable artifacts. "Why not." Applies to: video generation prompts, image generation prompts, music/soundtrack prompts, voice synthesis prompts. Each generated artifact should link back to its prompt.

- 20260226: **Voice specification for characters**: Not in the spec yet. Users should be able to specify character voices for dialogue — tone, accent, age, reference clips. This feeds into video/audio generation. Needs a spec section and eventually a story.

- 20260226: **Scene-level vs shot-level video generation**: Kling 3.0 can generate multi-shot sequences (up to 6 camera cuts per generation). The atomic unit for video gen is moving from "shot" toward "scene." Scene Workspace should be scene-first with shot detail as a drill-down, not shot-first. User preference: generate whole scene vs. shot-by-shot vs. whole scene with per-shot regeneration.

- 20260226: **Scene Workspace prerequisites** (what must exist before it can be built): Visual direction (Story 021), sound direction (Story 022), shot planning / shot-level data model (Story 025), storyboard generation (Story 026), reference image generation (Story 056, currently Blocked), render adapter / video generation (Story 028), voice specification (new, not in spec), per-scene readiness computation (new). These are the next priorities to unblock the Scene Workspace vision.

- 20260226: **ADR-002 outstanding items** (not yet storied): Onboarding flow ("I'm a [Screenwriter/Director/Producer/Explorer]" single question, skippable, defaults to Explorer), explorer demo project (pre-populated tutorial project, Notion pattern), per-feature AI autonomy levels (auto/assisted/manual per pipeline action, partially in Story 090), placeholder generation with visible marking for yellow-tier scenarios, quality estimates in preflight ("★★★☆☆ estimated quality"). Story 090 (Persona-Adaptive Workspaces) covers some of these but not all.

- 20260218 ai: [Google Gemini: Lyria 3 music generation](https://x.com/geminiapp/status/2024152863967240529) (@GeminiApp) - Turn ideas/photos/videos into 30-sec custom soundtracks with lyrics. Might be useful for music/soundtrack generation ^az86u1

- Stale: Why is this entity listed as stale? http://localhost:5174/the-mariner-40/locations/13th_floor Also I think when you hover over Stale it should tell you what that means. It currently looks like there's something wrong, but there's no info as to what, what that means for the user, or how they can do anythnig about it.
  - Related, the rest of them are listed as "valid". Are those are two states? Valid and stale? And valid in what way? Validated by what? Is that the right word for this?

- Generate WAY better formatted callsheets like these ones from StudioBinder and Gill (my sister): '/Users/cam/Documents/Projects/cine-forge/input/Sample Call Sheets'

- Steal Google new image gen AI: https://x.com/kimmonismus/status/2024773017432441133?s=12&t=uFZE-MuhgWdh1YErEZzLtQ
		- But also eval all others out there. Find SOTA and figure out what ours should look like.

- **Ghost-text inline suggestions** (GitHub Copilot pattern): Show AI suggestions as faded text inline with the user's content. User presses Tab to accept, keeps typing to dismiss. Great for script editing, bible enrichment, config tuning. *(Source: 011b landscape research)*

- **AI preference learning from user choices**: Every time we suggest something (or multiple variants) and the user chooses one, modifies a result, or adjusts an AI decision (e.g. scene split point), save both the AI suggestion and the user's final choice. This is training data for making future suggestions better. First-class architectural concept, not an afterthought. *(Source: Cam, 011b review)*

- **Entity graph visualization**: Visual graph of character/location/prop relationships. May be overkill — character relationships could just be a list view in the character bible. Revisit if entity count grows. *(Source: 011b landscape research)*

- ~~We might need to give the user the ability to specify HOW much help they want up front...~~ → **Triaged to ADR-002: Goal-Oriented Project Navigation** (`docs/decisions/adr-002-goal-oriented-navigation/adr.md`)

- in the chat UI we need to subtly put somewhere what model is actually doing the chatting. Just once, not every time it speaks.

### Data & Identity

### Workflow

- **Tighten entity_discovery character/prop taxonomy prompts**: Character taxonomy currently reads "speaking roles or silent roles with plot impact" — allows generic noise like WAITER, GUARD, CROWD. Prop taxonomy already excludes "costumes or set dressing" but could be stricter. Add explicit exclusions: unnamed background characters, crowd members, generic service roles. Small prompt edit in `entity_discovery_v1/main.py` lines 49-57. *(Deferred from Story 065 — noise reduction scope)*

- **Story-to-screenplay conversion**: For non-screenplay inputs (short stories, novels, treatments), send to a strong model with "make this into a screenplay" and take the output. Good for commercials and short-form. Not primary workflow but worth having as a convenience path. *(Source: Cam, 011b review)*

- Google's Lyira3: https://deepmind.google/models/lyria/ We could use this for background tracks, but it ALSO will video to go with them. Likely they wouldn't work when placed within a film due to style differences, but many video gen models now have the ability to use a another video as timing/music/motion reference. So for instance we could tell Lyria3 to make an emotional montage with a man and a woman doing x,y,z with a song and the people's actions should sync with the music. Then feed that into a genAI along with reference images of OUR characters and say "use the motion/timing reference and music and replace the man and the woman with our chars." That could be amazing.


## Triaged

- 2026-02-23 — Entity click → chat reference regression + slash-search routing + chat auto-scroll + ChatMessagePayload route field + ghost param audit → created story-079
- 2026-02-22 — Chat nav message duplication bug → created story-067
- 2026-02-22 — Back button hardcoded navigation → created story-068
- 2026-02-22 — Inbox items never marked read/complete → created story-069
- 2026-02-22 — Scene dividers in script view + hotlink screenplay to artifacts → created story-070
- 2026-02-22 — Refine vs. Regenerate modes for Deep Breakdown → created story-071
- 2026-02-21 — Finding scene boundaries and structure slow → created story-061
- 2026-02-21 — Smart project name inference on file pick → already implemented
- 2026-02-21 — Human-readable project slugs → already implemented

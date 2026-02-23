Ideas, links, and resources captured for triage. Newest first.
Triaged together via `/triage` skill in AI agent sessions.

## Untriaged

- Tweak: When the chat window gets added to and the user is scrolled to the bottom, auto-scroll to the bottom of the chat window. If they're not at the bottom, don't scroll.

- BUG: When you use the slash search command it goes to the raw artifact, not the char/location/pro detail as it should. For example in this local script: http://localhost:5174/the-mariner-28, searching /MARINER brings you to http://localhost:5174/the-mariner-28/artifacts/character_bible/mariner/1 instead of http://localhost:5174/the-mariner-28/characters/mariner . I think the raw artifacts should always be secondary in the search. That's almost never what anyone wants.

### UI / Interaction

- **ChatMessagePayload missing `route` field**: The backend Pydantic model `ChatMessagePayload` (models.py:205) doesn't include `route`, so activity message routes are silently stripped on persistence. Activity messages sent from the frontend include `route` (used for navigation context), but `model_dump(exclude_none=True)` drops it before JSONL storage. On cold load, activity messages lose their route association. Low severity — activity messages are ephemeral UI context — but should be fixed for completeness.

- Generate WAY better formatted callsheets like these ones from StudioBinder and Gill (my sister): '/Users/cam/Documents/Projects/cine-forge/input/Sample Call Sheets'

- Steal Google new image gen AI: https://x.com/kimmonismus/status/2024773017432441133?s=12&t=uFZE-MuhgWdh1YErEZzLtQ
		- But also eval all others out there. Find SOTA and figure out what ours should look like.

- **Ghost-text inline suggestions** (GitHub Copilot pattern): Show AI suggestions as faded text inline with the user's content. User presses Tab to accept, keeps typing to dismiss. Great for script editing, bible enrichment, config tuning. *(Source: 011b landscape research)*

- **AI preference learning from user choices**: Every time we suggest something (or multiple variants) and the user chooses one, modifies a result, or adjusts an AI decision (e.g. scene split point), save both the AI suggestion and the user's final choice. This is training data for making future suggestions better. First-class architectural concept, not an afterthought. *(Source: Cam, 011b review)*

- **Entity graph visualization**: Visual graph of character/location/prop relationships. May be overkill — character relationships could just be a list view in the character bible. Revisit if entity count grows. *(Source: 011b landscape research)*

- We might need to give the user the ability to specify HOW much help they want up front... We have an opinionated workflow that guides them from raw script to finished film, but if someone doens't want that where do they say "STOP ASKING ME TO DO THAT?" We have so many uses cases: writers who just want their script analyzed, writers with an IDEA who want help fleshing out characters, people who want to use it for the storyboarding or design work, people who already have most of what they want, want to import it, and just get the final film made, etc, etc. Me personally I'd usually want to noodle through every stage, being hands-on with every step and agent. But how do we give them visibility on goal/system autonomy? And how do they change their minds later? We don't to essentially turn off all AI agents and then have them have no idea how to turn them back on. And during onboarding do we do a little interview? That seems like a lot of friction. Do we just offer that up as an option in chat now and then? I think maybe we should have another panel on the left for all of these settings? And what are the settings? do we just turn them on or off? Maybe "settings" is the wrong concept. There IS a whole pipeline that's never really visualized. Maybe this is a good opportunity to give them a whole screen to show them what stage their film is in, what's next, what's available in terms of AI generation/help (and how to turn on/off each), AND a nice way to let them jump into any part. maybe they've imported their script and it's exacted their bibles and they want to jump STRAIGHT in to storyboarding or just rendering the final scene with whatever they have so far and see how it works.

- in the chat UI we need to subtly put somewhere what model is actually doing the chatting. Just once, not every time it speaks.

### Data & Identity

### Workflow

- **Audit `skip_enrichment` / `perform_deep_analysis` ghost param**: `scene_extract_v1` has an undeclared `skip_enrichment` param (used in code but missing from `module.yaml`). Story 062 originally planned a `perform_deep_analysis` toggle on `ProjectConfig` but dropped it — the 3-stage split makes Analysis optional by architecture (separate recipe stage), no config flag needed. Grep for `skip_enrichment` and `perform_deep_analysis` across the codebase and purge any references that survived. The old `skip_enrichment` disappears naturally when `scene_extract_v1` is deprecated. *(Source: Story 062 planning, 2026-02-22)*

- **Tighten entity_discovery character/prop taxonomy prompts**: Character taxonomy currently reads "speaking roles or silent roles with plot impact" — allows generic noise like WAITER, GUARD, CROWD. Prop taxonomy already excludes "costumes or set dressing" but could be stricter. Add explicit exclusions: unnamed background characters, crowd members, generic service roles. Small prompt edit in `entity_discovery_v1/main.py` lines 49-57. *(Deferred from Story 065 — noise reduction scope)*

- **Story-to-screenplay conversion**: For non-screenplay inputs (short stories, novels, treatments), send to a strong model with "make this into a screenplay" and take the output. Good for commercials and short-form. Not primary workflow but worth having as a convenience path. *(Source: Cam, 011b review)*

- Google's Lyira3: https://deepmind.google/models/lyria/ We could use this for background tracks, but it ALSO will video to go with them. Likely they wouldn't work when placed within a film due to style differences, but many video gen models now have the ability to use a another video as timing/music/motion reference. So for instance we could tell Lyria3 to make an emotional montage with a man and a woman doing x,y,z with a song and the people's actions should sync with the music. Then feed that into a genAI along with reference images of OUR characters and say "use the motion/timing reference and music and replace the man and the woman with our chars." That could be amazing.


## Triaged

- 2026-02-22 — Chat nav message duplication bug → created story-067
- 2026-02-22 — Back button hardcoded navigation → created story-068
- 2026-02-22 — Inbox items never marked read/complete → created story-069
- 2026-02-22 — Scene dividers in script view + hotlink screenplay to artifacts → created story-070
- 2026-02-22 — Refine vs. Regenerate modes for Deep Breakdown → created story-071
- 2026-02-21 — Finding scene boundaries and structure slow → created story-061
- 2026-02-21 — Smart project name inference on file pick → already implemented
- 2026-02-21 — Human-readable project slugs → already implemented

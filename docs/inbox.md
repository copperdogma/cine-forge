Ideas, links, and resources captured for triage. Newest first.
Triaged together via `/triage` skill in AI agent sessions.

## Untriaged

### UI / Interaction

- Do we still need the Inspector tab?

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

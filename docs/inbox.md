Ideas, links, and resources captured for triage. Newest first.
Triaged via `/triage-inbox` skill. Processed items are deleted — the inbox is a queue, not an archive.

## Untriaged

- If you open a scene and click View In script it just takes you to to the top of the script. It shuld jump down to that scene in the script.

- nano banana 2 templates would be useful for global style transfers: https://x.com/geminiapp/status/2027081255804870985?s=12&t=uFZE-MuhgWdh1YErEZzLtQ

- Runway Character Rendered App: https://x.com/runwayml/status/2027411005509161375?s=20

### ADR-003 Deferred Ideas

- 20260227: **Film decomposition / remix**: Take any existing film, decompose it into CineForge artifacts (screenplay, character bibles, visual references, sound design, direction), modify any element, re-render. E.g., take Pulp Fiction, recast a character, change the ending. The round-trip decomposition test (decompose → re-render → compare) is an Ideal vision preference; the remix feature itself is far-future. *(Source: ADR-003, Decision #8)*

- 20260227: **AI enhancement of minimal inputs**: Headshot → full character reference set (multiple angles, expressions, lighting). Phone video of location → clean reference stills from multiple angles. "Take whatever we can get and back-create proper artifacts from it." Leverages image gen models with uploaded asset as conditioning. *(Source: ADR-003, Decision #9)*

- 20260227: **Location lookup from web**: Given a location name ("Sydney Opera House"), fetch public images from the web to use as reference. Use real building facades and create fictional interiors. Needs web search/image API integration. *(Source: ADR-003, Decision #9)*

- 20260227: **Mood-board synthesis input**: Feed in multiple inspiration images (hairstyles, environments, objects, textures) as reference material for AI to synthesize into character/location/prop designs. "This hairstyle + this jacket + this vibe → character design." Natural extension of reference image system. *(Source: ADR-003, Decision #9)*

### UI / Interaction

- 20260226: **Narrative-aware timeline export**: When exporting to NLE formats (OpenTimelineIO, Final Cut XML, AAF, EDL), embed CineForge's narrative structure as timeline markers, color-coded regions, and clip notes. Scene boundaries, beat changes, character entrances, emotional tone shifts — metadata that no other AI video tool has because they don't understand story structure. Makes the editor's job dramatically easier. Formats: single video, scene folder, and NLE interchange formats.

- 20260218 ai: [Google Gemini: Lyria 3 music generation](https://x.com/geminiapp/status/2024152863967240529) (@GeminiApp) - Turn ideas/photos/videos into 30-sec custom soundtracks with lyrics. Might be useful for music/soundtrack generation ^az86u1

- Stale: Why is this entity listed as stale? http://localhost:5174/the-mariner-40/locations/13th_floor Also I think when you hover over Stale it should tell you what that means. It currently looks like there's something wrong, but there's no info as to what, what that means for the user, or how they can do anythnig about it.
  - Related, the rest of them are listed as "valid". Are those are two states? Valid and stale? And valid in what way? Validated by what? Is that the right word for this?

- Generate WAY better formatted callsheets like these ones from StudioBinder and Gill (my sister): '/Users/cam/Documents/Projects/cine-forge/input/Sample Call Sheets'

- Steal Google new image gen AI: https://x.com/kimmonismus/status/2024773017432441133?s=12&t=uFZE-MuhgWdh1YErEZzLtQ
		- But also eval all others out there. Find SOTA and figure out what ours should look like.

- **Ghost-text inline suggestions** (GitHub Copilot pattern): Show AI suggestions as faded text inline with the user's content. User presses Tab to accept, keeps typing to dismiss. Great for script editing, bible enrichment, config tuning. *(Source: 011b landscape research)*

- **AI preference learning from user choices**: Every time we suggest something (or multiple variants) and the user chooses one, modifies a result, or adjusts an AI decision (e.g. scene split point), save both the AI suggestion and the user's final choice. This is training data for making future suggestions better. First-class architectural concept, not an afterthought. *(Source: Cam, 011b review)*

- in the chat UI we need to subtly put somewhere what model is actually doing the chatting. Just once, not every time it speaks.

### Workflow

- **Tighten entity_discovery character/prop taxonomy prompts**: Character taxonomy currently reads "speaking roles or silent roles with plot impact" — allows generic noise like WAITER, GUARD, CROWD. Prop taxonomy already excludes "costumes or set dressing" but could be stricter. Add explicit exclusions: unnamed background characters, crowd members, generic service roles. Small prompt edit in `entity_discovery_v1/main.py` lines 49-57. *(Deferred from Story 065 — noise reduction scope)*

- **Story-to-screenplay conversion**: For non-screenplay inputs (short stories, novels, treatments), send to a strong model with "make this into a screenplay" and take the output. Good for commercials and short-form. Not primary workflow but worth having as a convenience path. *(Source: Cam, 011b review)*

- Google's Lyira3: https://deepmind.google/models/lyria/ We could use this for background tracks, but it ALSO will video to go with them. Likely they wouldn't work when placed within a film due to style differences, but many video gen models now have the ability to use a another video as timing/music/motion reference. So for instance we could tell Lyria3 to make an emotional montage with a man and a woman doing x,y,z with a song and the people's actions should sync with the music. Then feed that into a genAI along with reference images of OUR characters and say "use the motion/timing reference and music and replace the man and the woman with our chars." That could be amazing.

Ideas, links, and resources captured for triage. Newest first.
Triaged together via `/triage` skill in AI agent sessions.

## Untriaged


### UI / Interaction

- Generate WAY better formatted callsheets like these ones from StudioBinder: /Users/cam/Documents/Projects/cine-forge/input/Sample Studiobinder Call Sheets

- If the last item in the chat was a link to whatever the user clicked on, that's supposed to only show the most RECENT like, i.e.: there should only ever be ONE of those showing. If they click on somethign else it replaces the current one, so we shoudl only ever see one of those in a row in the chat history, but for this run [https://www.youtube.com/watch?v=zKX0zlJk840] I see this which should never happen:
    Reviewing Run History
    Viewing run: run-990d70d0
    Reviewing Run History
    Viewing run: run-990d70d0
    Reviewing Run History
    Viewing run: run-990d70d0

- We need a deep pass in how we do templating. I'm constnatly asking the AI to fix something that works on one page but is broken on some almost-identical page. wtf are we doing here? Is every single page custom coded? We need much smarter use of templates and components.

- inbox items are never marked as read/complete

- Steal Google new image gen AI: https://x.com/kimmonismus/status/2024773017432441133?s=12&t=uFZE-MuhgWdh1YErEZzLtQ
		- But also eval all others out there. Find SOTA and figure out what ours should look like.

- **Ghost-text inline suggestions** (GitHub Copilot pattern): Show AI suggestions as faded text inline with the user's content. User presses Tab to accept, keeps typing to dismiss. Great for script editing, bible enrichment, config tuning. *(Source: 011b landscape research)*

- **AI preference learning from user choices**: Every time we suggest something (or multiple variants) and the user chooses one, modifies a result, or adjusts an AI decision (e.g. scene split point), save both the AI suggestion and the user's final choice. This is training data for making future suggestions better. First-class architectural concept, not an afterthought. *(Source: Cam, 011b review)*

- **Entity graph visualization**: Visual graph of character/location/prop relationships. May be overkill — character relationships could just be a list view in the character bible. Revisit if entity count grows. *(Source: 011b landscape research)*

- **Smart project name inference on file pick**: When the user selects a screenplay (drag-and-drop or file picker), immediately attempt to guess a project name. Could be as simple as the filename sans extension, or we could read the first few pages of the PDF/FDX to extract a title page. Auto-populate the project name field so the user can accept or edit. Relevant to both the NewProject page and the Pipeline drop zone. *(Source: Cam, 011d build)*

- We might need to give the user the ability to specify HOW much help they want up front... We have an opinionated workflow that guides them from raw script to finished film, but if someone doens't want that where do they say "STOP ASKING ME TO DO THAT?" We have so many uses cases: writers who just want their script analyzed, writers with an IDEA who want help fleshing out characters, people who want to use it for the storyboarding or design work, people who already have most of what they want, want to import it, and just get the final film made, etc, etc. Me personally I'd usually want to noodle through every stage, being hands-on with every step and agent. But how do we give them visibility on goal/system autonomy? And how do they change their minds later? We don't to essentially turn off all AI agents and then have them have no idea how to turn them back on. And during onboarding do we do a little interview? That seems like a lot of friction. Do we just offer that up as an option in chat now and then? I think maybe we should have another panel on the left for all of these settings? And what are the settings? do we just turn them on or off? Maybe "settings" is the wrong concept. There IS a whole pipeline that's never really visualized. Maybe this is a good opportunity to give them a whole screen to show them what stage their film is in, what's next, what's available in terms of AI generation/help (and how to turn on/off each), AND a nice way to let them jump into any part. maybe they've imported their script and it's exacted their bibles and they want to jump STRAIGHT in to storyboarding or just rendering the final scene with whatever they have so far and see how it works.

- in the chat UI we need to subtly put somewhere what model is actually doing the chatting. Just once, not every time it speaks.

### Data & Identity

- Why does "Finding scene boundaries and structure..." tale SO long? If the pipeline artifacfts don't already give us the answer from their logs, we need to improve the logs. If they do, what's causing it? How could we speed it up? SHOULD we speed it up or would that just compromise quality? Should we consider a promptfoo eval to find a better way?

- **Human-readable project slugs**: Currently project IDs are raw hashes (e.g., `ed0e25e86b3cb84...`). These are ugly in URLs, breadcrumbs, and the sidebar. Proposed: Generate slugs from the project's display name ("The Mariner" → `the-mariner`), with numeric suffixes for collisions (`the-mariner-2`). Store both `project_id` (hash, internal) and `slug` (human-readable, for URLs). UI routes use the slug (`/:slug/run` instead of `/:projectId/run`). Backend resolves slug → project_id on each request. Slug should be editable; changing the project name updates the slug with confirmation. Scope: Backend change (service layer + API) + UI routing update. Do when hooking the console to real API. *(Source: 011e operator-console research)*

### Workflow

- **Refine vs. Regenerate modes for Deep Breakdown**: 
  - **Regenerate (Current)**: Run discovery and bible extraction from scratch using only the script as input. Useful for major structural changes.
  - **Refine (Proposed)**: Pass the `latest_version` of an entity artifact (and its lineage) back to the AI alongside script changes. 
  - **Goal**: Allow AI to update a character or location profile while preserving user edits or existing context. Leverages CineForge's immutability (creates `vNext`) to ensure no data is ever actually lost, just evolved. 
  - **UI**: Need a version browser/history viewer so users can easily diff and restore if a re-run produces unwanted changes.

- **Story-to-screenplay conversion**: For non-screenplay inputs (short stories, novels, treatments), send to a strong model with "make this into a screenplay" and take the output. Good for commercials and short-form. Not primary workflow but worth having as a convenience path. *(Source: Cam, 011b review)*

- Google's Lyira3: https://deepmind.google/models/lyria/ We could use this for background tracks, but it ALSO will generate videos to go with them. Likely they wouldn't work when placed within a film due to style differences, but many video gen models now have the ability to use a another video as timing/music/motion reference. So for instance we could tell Lyria3 to make an emotional montage with a man and a woman doing x,y,z with a song and the people's actions should sync with the music. Then feed that into a genAI along with reference images of OUR characters and say "use the motion/timing reference and music and replace the man and the woman with our chars." That could be amazing.


## Triaged
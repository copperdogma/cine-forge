# Ideas Backlog

Ideas worth keeping but not in scope for current work. Review periodically.

---

## UI / Interaction

- **Ghost-text inline suggestions** (GitHub Copilot pattern): Show AI suggestions as faded text inline with the user's content. User presses Tab to accept, keeps typing to dismiss. Great for script editing, bible enrichment, config tuning. *(Source: 011b landscape research)*

- **AI preference learning from user choices**: Every time we suggest something (or multiple variants) and the user chooses one, modifies a result, or adjusts an AI decision (e.g. scene split point), save both the AI suggestion and the user's final choice. This is training data for making future suggestions better. First-class architectural concept, not an afterthought. *(Source: Cam, 011b review)*

- **Entity graph visualization**: Visual graph of character/location/prop relationships. May be overkill — character relationships could just be a list view in the character bible. Revisit if entity count grows. *(Source: 011b landscape research)*

- **Smart project name inference on file pick**: When the user selects a screenplay (drag-and-drop or file picker), immediately attempt to guess a project name. Could be as simple as the filename sans extension, or we could read the first few pages of the PDF/FDX to extract a title page. Auto-populate the project name field so the user can accept or edit. Relevant to both the NewProject page and the Pipeline drop zone. *(Source: Cam, 011d build)*

## Data & Identity

- **Human-readable project slugs**: Currently project IDs are raw hashes (e.g., `ed0e25e86b3cb84...`). These are ugly in URLs, breadcrumbs, and the sidebar. Proposed: Generate slugs from the project's display name ("The Mariner" → `the-mariner`), with numeric suffixes for collisions (`the-mariner-2`). Store both `project_id` (hash, internal) and `slug` (human-readable, for URLs). UI routes use the slug (`/:slug/run` instead of `/:projectId/run`). Backend resolves slug → project_id on each request. Slug should be editable; changing the project name updates the slug with confirmation. Scope: Backend change (service layer + API) + UI routing update. Do when hooking the console to real API. *(Source: 011e operator-console research)*

## Workflow

- **Story-to-screenplay conversion**: For non-screenplay inputs (short stories, novels, treatments), send to a strong model with "make this into a screenplay" and take the output. Good for commercials and short-form. Not primary workflow but worth having as a convenience path. *(Source: Cam, 011b review)*

- Google's Lyira3: https://deepmind.google/models/lyria/ We could use this for background tracks, but it ALSO will generate videos to go with them. Likely they wouldn't work when placed within a film due to style differences, but many video gen models now have the ability to use a another video as timing/music/motion reference. So for instance we could tell Lyria3 to make an emotional montage with a man and a woman doing x,y,z with a song and the people's actions should sync with the music. Then feed that into a genAI along with reference images of OUR characters and say "use the motion/timing reference and music and replace the man and the woman with our chars." That could be amazing.
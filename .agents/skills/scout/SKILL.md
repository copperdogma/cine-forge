---
name: scout
description: Research a source (repo, URL, article) for ideas to adopt, recommend changes, implement approved items, and self-verify.
user-invocable: true
---

# /scout [source]

Research external sources for patterns, ideas, and approaches worth adopting. Produces a persistent scout document tracking what was found, what was adopted, and verification evidence.

## Inputs

- **source** (required): One of:
  - Local repo path (e.g., `~/Projects/other-repo`)
  - GitHub URL (e.g., `https://github.com/org/repo`)
  - Article/web URL
  - File path to research paper or docs
- **scope** (optional): Time range, branch, specific area to focus on

## Phase 0 — Bootstrap

Run the start script to set up everything automatically:

```bash
.agents/skills/scout/scripts/start-scouting.sh <topic-slug>
```

This handles all setup in one call:
- Creates `docs/scout.md` index from template if it doesn't exist
- Creates `docs/scout/` directory if it doesn't exist
- Finds the next available expedition number
- Creates the expedition file from template (e.g., `docs/scout/scout-003-topic-slug.md`)
- Outputs the file path for you to fill in

## Phase 1 — Research

1. **Check history:** Read `docs/scout.md` for previous expeditions against this source.
   - If found: suggest "Last scouted on YYYY-MM-DD — only check changes since then?" Wait for user confirmation or override.
   - If not found: scout the full source (no arbitrary time window).

2. **Explore the source** based on type:
   - **Local repo:** `git log --oneline --stat`, read changed files, AGENTS.md, key docs
   - **GitHub URL:** Clone to temp dir or use `gh api` / `gh repo clone --depth=1`
   - **Article/URL:** WebFetch, extract key ideas and patterns
   - **Docs/paper:** Read and extract actionable patterns

3. **Compare against our project:** For each finding, assess:
   - What does the source do?
   - Do we already have this? (check our files)
   - How valuable would it be for this project? (HIGH / MEDIUM / LOW)
   - How much effort to adopt? (small = inline, large = needs a story)

4. **Fill in the scout document** created in Phase 0 with findings.

5. **Present findings** as a numbered list with value ratings and effort estimates. Group items if there are more than 5.

6. **Recommend:** End with a clear approval prompt. Example:
   ```
   Items 1-3 (skill infrastructure): Ready for inline implementation.
   Item 4 (voice mode rewrite): Too large — recommend creating a story.
   Items 5-6: Low value — recommend skipping.

   Approve all inline items? Or pick specific ones?
   ```

## Phase 2 — Approval

Wait for user to approve. Options:
- "yes" — implement all recommended inline items
- Specific items by number
- Groups by letter/name
- "story for X" — create a story for a large item via `/create-story`

Update the scout doc's **Approved** section with what was approved.

## Phase 3 — Implementation

1. **Create task list** from approved items (use internal task tracking).
2. **Implement each item**, marking tasks complete as you go.
3. For items that should be stories:
   - Create the story file via the create-story skill pattern
   - Mark the scout item as "Deferred → Story NNN"
4. For inline items:
   - Make the changes
   - Mark complete with brief evidence

## Phase 4 — Verification

After all implementation is done:

1. **Re-read every modified file** to confirm changes landed correctly.
2. **Fill in evidence** for each approved item in the scout doc.
3. **Run any relevant checks** (sync scripts, lint, typecheck — whatever applies to the changes made).
4. **Update the scout doc** with final status per item. Set status to Complete.
5. **Update `docs/scout.md` index** with the new expedition row.
6. **Report summary** to user:
   ```
   Scout NNN complete:
   - X items adopted, Y deferred, Z skipped
   - All adopted items verified
   - Story NNN created for [large item] (if applicable)
   ```

## Story Escalation

Suggest creating a story (not inline implementation) when an item would:
- Touch more than ~5 files across multiple packages
- Require adding new dependencies
- Change core architecture or conventions
- Involve significant new code (not just config/docs)
- Take more than ~30 minutes to implement

When escalating: create the story with context from the scout findings, link back to the scout doc, and mark the scout item as deferred.

## Guardrails

- Never implement without explicit user approval of specific items.
- Always create the scout document before implementation — it's the audit trail.
- Never skip the verification phase. Every adopted item needs evidence.
- When in doubt about size, suggest a story rather than inline implementation.
- Don't commit or push unless the user explicitly requests it.
- Record ALL findings, even ones you recommend skipping — they may be relevant later.

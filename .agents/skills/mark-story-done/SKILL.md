---
name: mark-story-done
description: Validate a story is complete and update story statuses safely.
user-invocable: true
---

# mark-story-done

Use this skill to close a completed story.

## Inputs

- Story id/title/path (optional if inferable from context).

## Validation Steps

1. Resolve story file.
2. Validate:
   - tasks complete
   - acceptance criteria met
   - work log current
   - dependency constraints addressed
   - relevant tests/checks executed
3. Produce completion report with any remaining gaps.

## Apply Completion

If complete (or user approves remaining gaps):

1. Set story file status to `Done`.
2. Update corresponding row in `docs/stories.md` to `Done`.
3. Append completion note to story work log with date and evidence.
4. Update CHANGELOG.md:
   - Grep CHANGELOG.md for the story number (e.g. `grep -i "Story 042" CHANGELOG.md`).
   - If an entry already exists, skip — do not duplicate.
   - If no entry exists, prepend a new entry after the `# Changelog` header using Keep a Changelog format:

     ```
     ## [YYYY-MM-DD] - Short summary (Story NNN)

     ### Added
     - ...

     ### Changed
     - ...

     ### Fixed
     - ...
     ```

   - Use today's date. Derive the summary from the story file's Goal section.
   - Only include `### Added`, `### Changed`, `### Fixed` subsections that apply.

If not complete, stop and list blockers.

## Guardrails

- Never hide gaps; always report unmet criteria explicitly.
- Ask for confirmation when unresolved items remain.
- Do not duplicate CHANGELOG.md entries — always check before writing.

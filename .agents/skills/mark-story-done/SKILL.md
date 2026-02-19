---
name: mark-story-done
description: Validate a story is complete and update statuses safely
user-invocable: true
---

# /mark-story-done [story-number]

Close a completed story after validation.

## Inputs

- Story id, title, or path (optional if inferable from context)

## Validation Steps

1. **Resolve story file** — Read `docs/stories/story-{NNN}-*.md`.

2. **Validate completeness:**
   - [ ] All task checkboxes checked
   - [ ] All acceptance criteria met (with evidence)
   - [ ] Work log is current
   - [ ] Dependencies addressed
   - [ ] Required checks passed for changed scope:
     - Backend: `make test-unit PYTHON=.venv/bin/python` + `.venv/bin/python -m ruff check src/ tests/`
     - UI (if touched): `pnpm --dir ui run lint` + build/typecheck script if defined
   - [ ] Tenet verification checkbox checked
   - [ ] Doc update checkbox checked

3. **Produce completion report** — List any remaining gaps.

## Apply Completion

If complete (or user approves remaining gaps):

1. Set story file status to `Done`.
2. Update corresponding row in `docs/stories.md` to `Done`.
3. Append completion note to story work log with date and evidence.
4. Update CHANGELOG.md:
   - Search CHANGELOG.md for the story number (e.g., `Story 001`)
   - If an entry already exists, skip — do not duplicate
   - If no entry exists, prepend a new entry after the `# Changelog` header:

     ```
     ## [YYYY-MM-DD] — Short summary (Story NNN)

     ### Added
     - ...

     ### Changed
     - ...

     ### Fixed
     - ...
     ```

   - Use today's date. Derive the summary from the story's Goal section.
   - Only include subsections that apply.

If not complete, stop and list blockers.

## Guardrails

- Never hide gaps — always report unmet criteria explicitly
- Ask for confirmation when unresolved items remain
- Do not duplicate CHANGELOG.md entries — always check before writing
- Never mark Done without running the full check suite

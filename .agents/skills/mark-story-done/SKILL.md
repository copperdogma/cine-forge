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
   - [ ] Required checks passed for all code changes:
     - Backend: `make test-unit PYTHON=.venv/bin/python` + `.venv/bin/python -m ruff check src/ tests/`
     - UI: `pnpm --dir ui run lint` + `cd ui && npx tsc -b`
   - [ ] If story touched an AI module or eval: all significant eval mismatches classified (model-wrong / golden-wrong / ambiguous) with evidence
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
     ## [YYYY-MM-DD-NN] — Short summary (Story NNN)

     ### Added
     - ...

     ### Changed
     - ...

     ### Fixed
     - ...
     ```

   - Use today's date. Derive the summary from the story's Goal section.
   - **Versioning (CalVer)**: Use the `YYYY-MM-DD-NN` format for the header, where `NN` is the release sequence for that day (e.g., `01`, `02`, `03`). Check the previous entry to increment correctly. The API parses this into `YYYY.MM.DD-NN`.
   - Only include subsections that apply.

If not complete, stop and list blockers.

## Guardrails

- Never hide gaps — always report unmet criteria explicitly
- Ask for confirmation when unresolved items remain
- Do not duplicate CHANGELOG.md entries — always check before writing
- Never mark Done without running the full check suite

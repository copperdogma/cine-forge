---
name: mark-story-done
description: Validate a story is complete and update statuses safely
user-invocable: true
---

# /mark-story-done [story-number]

> ADR check: If this task raises an architectural, workflow, schema, or UX question, read the relevant decision record(s) in `docs/decisions/` and supporting docs in `docs/design/` before choosing an approach. If none apply, say so explicitly.

Close a completed story after validation.

## Inputs

- Story id, title, or path (optional if inferable from context)

## Validation Steps

1. **Resolve story file** — Read `docs/stories/story-{NNN}-*.md`.

2. **Check workflow gates first:**
   - [ ] `Build complete` is checked
   - [ ] `Validation complete or explicitly skipped by user` is checked, or the user explicitly instructed you to skip validation in this close-out request
   - [ ] `Story marked done via /mark-story-done` is still unchecked

3. **Validate completeness:**
   - [ ] All task checkboxes checked
   - [ ] All acceptance criteria met (with evidence)
   - [ ] Work log is current
   - [ ] Dependencies addressed
   - [ ] Required checks passed for all code changes:
     - Backend: `make test-unit PYTHON=.venv/bin/python` + `.venv/bin/python -m ruff check src/ tests/`
     - UI: `pnpm --dir ui run lint` + `cd ui && npx tsc -b`
   - [ ] If evals were run: `/verify-eval` report exists in work log with every mismatch classified as model-wrong / golden-wrong / ambiguous. Golden-wrong findings must be fixed and evals re-run before closing.
   - [ ] If any eval was run: `docs/evals/registry.yaml` updated with new scores, `git_sha`, and date
   - [ ] Tenet verification checkbox checked
   - [ ] Doc update checkbox checked

4. **Produce completion report** — List any remaining gaps.

## Apply Completion

If complete (or user approves remaining gaps):

1. Set story file status to `Done`.
2. Check `Story marked done via /mark-story-done`.
3. If validation was explicitly skipped by the user, record that decision in the work log and check `Validation complete or explicitly skipped by user`.
4. Update corresponding row in `docs/stories.md` to `Done`.
5. Append completion note to story work log with date and evidence. End the note with the recommended next step: `/check-in-diff`.
6. Update CHANGELOG.md:
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
- Never mark Done if evals were run without a `/verify-eval` report (or equivalent classification) in the work log
- Never mark a Draft story as Done — it must be promoted to Pending and built via `/build-story` first
- End with a concise summary and recommend `/check-in-diff` as the next step unless the user already approved later steps
- If the user already explicitly approved `/check-in-diff`, commit, or push, continue without redundant confirmation unless a meaningful blocker appears

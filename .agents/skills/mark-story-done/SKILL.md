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
   - [ ] If evals were run: the work log contains a mismatch-classification report from `/improve-eval` or equivalent protocol with every mismatch classified as model-wrong / golden-wrong / ambiguous. Golden-wrong findings must be fixed and evals re-run before closing.
   - [ ] If any detector or compromise eval remained red: the work log or validation note records whether the remaining failure is runtime-blocking or non-runtime-blocking.
   - [ ] If any eval was run: `docs/evals/registry.yaml` updated with new scores, `git_sha`, and date
   - [ ] Tenet verification checkbox checked
   - [ ] Doc update checkbox checked

4. **Produce completion report** — List any remaining gaps and recommend a single disposition:
   - `Close now` — story is complete and can be marked `Done`
   - `Rescope then close` — a coherent slice shipped, the remaining gaps already live in follow-up work, and this story should be narrowed to match what landed
   - `Keep open` — remaining work still belongs in this story
   - `Mark blocked` — an external dependency or decision is preventing closure

   If recommending `Rescope then close`, propose the exact story edits before closing:
   - Narrow the title, goal, acceptance criteria, and tasks to the shipped slice
   - Add a work-log note linking the remaining work to the follow-up story or stories
   - Re-run this close-out check against the revised story

## Apply Completion

If complete (or the user explicitly approves the closure recommendation and any remaining gaps):

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

If not complete, stop after reporting:
- what is incomplete
- the single recommended disposition (`Rescope then close`, `Keep open`, or `Mark blocked`)
- the exact edits or next steps required

## Guardrails

- Never hide gaps — always report unmet criteria explicitly
- Ask for confirmation when unresolved items remain
- Do not duplicate CHANGELOG.md entries — always check before writing
- Never mark Done without running the full check suite
- Never mark Done if evals were run without a mismatch-classification report (`/improve-eval` or equivalent) in the work log
- Never mark a Draft story as Done — it must be promoted to Pending and built via `/build-story` first
- End with a concise summary, recommend `/check-in-diff` as the next step unless the user already approved later steps, and include a short `Where to verify` note whenever there is a concrete path for the user to inspect the result themselves
- When incomplete, never end with "can't mark done" alone. Always include a firm recommendation: `Rescope then close`, `Keep open`, or `Mark blocked`.
- If the user already explicitly approved `/check-in-diff`, commit, or push, continue without redundant confirmation unless a meaningful blocker appears

---
name: build-story
description: Execute a story from planning through implementation with work-log discipline
user-invocable: true
---

# /build-story [story-number]

Execute a development story end-to-end.

## Steps

1. **Resolve story** — Read `docs/stories/story-{NNN}-*.md` (or resolve from `docs/stories.md` if id/title/path is ambiguous). Verify status is Pending or In Progress.

2. **Verify required sections** — Ensure the story has usable:
   - Goal
   - Acceptance Criteria
   - Tasks (checkbox items)
   - Work Log
   If tasks are missing, add actionable checkbox items without discarding existing intent.

3. **Understand context** — Read all spec refs, dependency stories, and referenced ADRs. Read the "Files to Modify" list if present.

4. **Plan** — Review tasks and acceptance criteria. If anything is ambiguous, ask before proceeding. Identify files to create/modify.

5. **AI-first check** — Before writing any complex logic, review the story's "AI Considerations" section. For each significant piece of work, ask:
   - Is this a reasoning/language/understanding problem? → **Try an LLM call first** (structured output validated against project schemas)
   - Is this orchestration/storage/UI? → Write code
   - Have you checked current SOTA? Your training data may be stale — web search if unsure what models can do today
   - See AGENTS.md "AI-First Problem Solving" for full guidance

6. **Implement** — Work through tasks in order. For each task:
   - Mark task as in progress in the story file
   - Do the work
   - Run relevant project checks after meaningful changes (backend: unit tests + Ruff; UI: `pnpm --dir ui run lint` and build/typecheck scripts)
   - Run relevant tests
   - Mark task complete with brief evidence

7. **Verify** — Run full checks for all code changes:
   - Backend: `make test-unit PYTHON=.venv/bin/python` and `.venv/bin/python -m ruff check src/ tests/`
   - UI: `pnpm --dir ui run lint` and `cd ui && npx tsc -b`
   - Review each acceptance criterion — is it met?

8. **Update docs** — Search all docs in the codebase and update any related to what we touched.

9. **Verify Central Tenets** — Check each tenet checkbox in the story:
   - Tenet 0: Could any user data be lost? Is capture-first preserved?
   - Tenet 1: Is the code AI-friendly? Would another AI session understand it?
   - Tenet 2: Did we over-engineer something AI will handle better soon?
   - Tenet 3: Are files appropriately sized? Types centralized?
   - Tenet 4: Is the work log verbose enough for handoff?
   - Tenet 5: Did we check: can this be simplified toward the ideal?

10. **Update work log** — Add dated entry: what was done, decisions made, evidence, any blockers or follow-ups.

11. **Update status** — If all acceptance criteria met and checks pass, mark story Done. Update `docs/stories.md` index.

## Work Log Format

```
YYYYMMDD-HHMM — action: result, evidence, next step
```

Entries should be verbose. Capture decisions, failures, solutions, and learnings. These are build artifacts — any future AI session should be able to pick up context from the log.

## Guardrails

- Never skip acceptance criteria verification
- Never mark Done if any check fails
- Never commit without running the required checks for changed scope
- Always update the work log, even for partial progress
- If blocked, record the blocker and stop — don't guess

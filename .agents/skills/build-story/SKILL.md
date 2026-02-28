---
name: build-story
description: Execute a story from planning through implementation with work-log discipline
user-invocable: true
---

# /build-story [story-number]

Execute a development story end-to-end.

## Phase 1 — Explore (read-only, no file writes)

1. **Resolve story** — Read `docs/stories/story-{NNN}-*.md` (or resolve from `docs/stories.md` if id/title/path is ambiguous). Verify status is Pending or In Progress.

2. **Verify required sections** — Ensure the story has usable:
   - Goal
   - Acceptance Criteria
   - Tasks (checkbox items)
   - Work Log
   If tasks are missing, add actionable checkbox items without discarding existing intent.

3. **Read context** — Read all spec refs, dependency stories, and referenced ADRs. Read the "Files to Modify" list if present.

4. **Explore the codebase actively** — Don't just read what's listed. Trace the code:
   - Follow call graphs from every entry point the story touches
   - Find every file that will need to change (not just the obvious ones)
   - Find every file that could break (callers, consumers, tests)
   - Identify existing patterns and conventions to match
   - Note any schema, config, or migration concerns

5. **Record exploration findings** — Write a brief "Exploration Notes" entry in the work log:
   - Files that will change
   - Files at risk of breaking
   - Patterns to follow
   - Any surprises or risks found

## Phase 2 — Plan (produces a written artifact)

6. **AI-first check** — For each significant piece of work, ask:
   - Is this a reasoning/language/understanding problem? → **Try an LLM call first** (structured output validated against project schemas)
   - Is this orchestration/storage/UI? → Write code
   - Have you checked current SOTA? Your training data may be stale — web search if unsure what models can do today
   - See AGENTS.md "AI-First Problem Solving" for full guidance

7. **Write the implementation plan** — Add a `## Plan` section to the story file with:
   - For each task: which files change, what changes, in what order
   - Impact analysis: what tests are affected, what could break
   - Any human-approval blockers (new dependencies, schema changes, public API changes)
   - What "done" looks like for each task

8. **Human gate** — Present the plan to the user. Surface any ambiguities or risks. Do not write any implementation code until the user approves. If something in the plan is unclear, ask now — not mid-implementation.

## Phase 3 — Implement

9. **Implement** — Work through tasks in order. For each task:
   - Mark task as in progress in the story file
   - Do the work
   - Run relevant project checks after meaningful changes (backend: unit tests + Ruff; UI: `pnpm --dir ui run lint` and `cd ui && npx tsc -b`)
   - Run relevant tests
   - Mark task complete with brief evidence

10a. **Static verification** — Run the project's full validation suite:
   - Backend: `make test-unit PYTHON=.venv/bin/python` and `.venv/bin/python -m ruff check src/ tests/`
   - UI: `pnpm --dir ui run lint` and `cd ui && npx tsc -b`
   - `pnpm --dir ui run build` (catches errors typecheck misses)
   - Review each acceptance criterion — is it met?

10b. **Eval mismatch investigation** (if the story touched an AI module or eval):
   - Run relevant promptfoo evals or acceptance tests
   - For every significant mismatch, classify as: **model-wrong**, **golden-wrong**, or **ambiguous** with evidence
   - Do not proceed to Done if mismatches remain unclassified

10c. **Runtime smoke test** — Verify the app actually works end-to-end:
   - Start dev servers — confirm they start with no error output in logs
   - If backend changed: hit the health endpoint — confirm 200 with valid JSON
   - If any frontend files changed: Chrome MCP screenshot — page loads, no blank screen, no JS console errors
   - If frontend→backend communication was added or changed: confirm the call succeeds and response is correct
   - Record evidence in the work log: server startup output, curl response, screenshot description
   - **Do not mark Done if this step was skipped** — static checks passing ≠ app works

11. **Update docs** — Search all docs in the codebase and update any related to what we touched.

12. **Verify Central Tenets** — Check each tenet checkbox in the story:
   - Tenet 0: Could any user data be lost? Is capture-first preserved?
   - Tenet 1: Is the code AI-friendly? Would another AI session understand it?
   - Tenet 2: Did we over-engineer something AI will handle better soon?
   - Tenet 3: Are files appropriately sized? Types centralized?
   - Tenet 4: Is the work log verbose enough for handoff?
   - Tenet 5: Did we check: can this be simplified toward the ideal?

13. **Update work log** — Add dated entry: what was done, decisions made, evidence, any blockers or follow-ups.

14. **Update status** — If all acceptance criteria met and checks pass, mark story Done. Update `docs/stories.md` index.

## Work Log Format

```
YYYYMMDD-HHMM — action: result, evidence, next step
```

Entries should be verbose. Capture decisions, failures, solutions, and learnings. These are build artifacts — any future AI session should be able to pick up context from the log.

## Guardrails

- Never write implementation code before the human gate (step 8) — exploration and planning are read-only
- Never skip acceptance criteria verification
- Never mark Done if any check fails
- Never mark Done if the runtime smoke test (10c) was skipped — static checks passing ≠ app works
- Never mark Done if eval mismatches remain unclassified (10b) — silently accepting noise is a hard stop
- Never commit without running the required checks for changed scope
- Always update the work log, even for partial progress
- If blocked, record the blocker and stop — don't guess

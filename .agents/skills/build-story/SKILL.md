---
name: build-story
description: Execute a story from planning through implementation with work-log discipline
user-invocable: true
---

# /build-story [story-number]

Execute a development story end-to-end.

## Phase 1 — Explore (read-only, no file writes)

1. **Resolve story** — Read `docs/stories/story-{NNN}-*.md` (or resolve from `docs/stories.md` if id/title/path is ambiguous). Verify status is Pending or In Progress. If status is **Draft**, STOP — it needs detailed acceptance criteria and tasks before it can be built. Tell the user to promote it to Pending first (or promote it inline if they approve).

2. **Verify required sections** — Ensure the story has usable:
   - Goal
   - Acceptance Criteria
   - Tasks (checkbox items)
   - Work Log
   If tasks are missing, add actionable checkbox items without discarding existing intent.

3. **Read context** — Read `docs/ideal.md` first, then all spec refs, dependency stories, and referenced ADRs. Read the "Files to Modify" list if present.

4. **Ideal Alignment Gate** — Before exploring code, verify this story moves toward the Ideal:
   - Does this story close an Ideal gap? → proceed
   - Does it move AWAY from the Ideal? → STOP, tell user to re-evaluate
   - Does it build infrastructure for pipeline stages that don't exist yet? → flag as potentially premature
   - Does it optimize a limitation that's shrinking on its own (check `docs/retrofit-gaps.md`)? → flag as potentially premature
   - If the story introduces a new AI compromise: note whether a detection eval exists or should be created

5. **Explore the codebase actively** — Don't just read what's listed. Trace the code:
   - Follow call graphs from every entry point the story touches
   - Find every file that will need to change (not just the obvious ones)
   - Find every file that could break (callers, consumers, tests)
   - Identify existing patterns and conventions to match
   - Note any schema, config, or migration concerns

6. **Record exploration findings** — Write a brief "Exploration Notes" entry in the work log:
   - Files that will change
   - Files at risk of breaking
   - Patterns to follow
   - Any surprises or risks found

## Phase 2 — Plan (produces a written artifact)

7. **Eval-first approach gate** — Before planning implementation, establish how you'll measure success and which approaches to compare:
   - **What eval?** Identify or create a test that measures whether this task succeeds. Even a minimal fixture + assertion counts. If no eval exists for this area, create one before choosing an approach.
   - **What's the baseline?** Run the eval against current code. Document the number.
   - **What are the candidate approaches?** For any task involving reasoning, language, or understanding: enumerate at least AI-only, hybrid (deterministic detection + AI judgment), and pure code. The story's "Approach Evaluation" section is input — if it pre-decided an approach without eval evidence, challenge it.
   - **Test the simplest first.** Often that's a single LLM call. Run it against the eval. If it works, don't build code for a problem AI already solves.
   - For pure orchestration/storage/plumbing/UI: code is obviously simpler — no comparison needed.
   - **Model selection requires live data**: Never pick models from training data. Query the provider API and check current pricing. Cost differences can be 10-20x.

8. **Write the implementation plan** — Add a `## Plan` section to the story file with:
   - For each task: which files change, what changes, in what order
   - Impact analysis: what tests are affected, what could break
   - Any human-approval blockers (new dependencies, schema changes, public API changes)
   - What "done" looks like for each task

9. **Human gate** — Present the plan to the user. Surface any ambiguities or risks. Do not write any implementation code until the user approves. If something in the plan is unclear, ask now — not mid-implementation.

## Phase 3 — Implement

10. **Implement** — Work through tasks in order. For each task:
   - Mark task as in progress in the story file
   - Do the work
   - Run relevant project checks after meaningful changes (backend: unit tests + Ruff; UI: `pnpm --dir ui run lint` and `cd ui && npx tsc -b`)
   - Run relevant tests
   - Mark task complete with brief evidence

11a. **Static verification** — Run the project's full validation suite:
   - Backend: `make test-unit PYTHON=.venv/bin/python` and `.venv/bin/python -m ruff check src/ tests/`
   - UI: `pnpm --dir ui run lint` and `cd ui && npx tsc -b`
   - `pnpm --dir ui run build` (catches errors typecheck misses)
   - Review each acceptance criterion — is it met?

11b. **Eval mismatch investigation** (if the story touched an AI module or eval):
   - Run relevant promptfoo evals or acceptance tests
   - Prompt the user to run `/verify-eval`. Every mismatch must be classified as **model-wrong**, **golden-wrong**, or **ambiguous** before the story can close. Do not attempt the full investigation inline — it overwhelms context.
   - **Re-assess acceptance criteria against verified scores.** Golden fixes from `/verify-eval` change the real scores. What looked like a passing story on raw scores may fail on verified scores (or vice versa). Only verified scores determine whether acceptance criteria are met.
   - Do not proceed to Done if mismatches remain unclassified
   - **Update `docs/evals/registry.yaml`** with new scores, `git_sha`, and date for every eval you ran. Stale registry scores are worse than no scores — they cause future agents to waste time on already-solved problems or miss regressions.

11c. **Runtime smoke test** — Verify the app actually works end-to-end:
   - Start dev servers — confirm they start with no error output in logs
   - If backend changed: hit the health endpoint — confirm 200 with valid JSON
   - If any frontend files changed: Chrome MCP screenshot — page loads, no blank screen, no JS console errors
   - If frontend→backend communication was added or changed: confirm the call succeeds and response is correct
   - Record evidence in the work log: server startup output, curl response, screenshot description
   - **Do not mark Done if this step was skipped** — static checks passing ≠ app works

12. **Update docs** — Search all docs in the codebase and update any related to what we touched.

13. **Verify Central Tenets** — Check each tenet checkbox in the story:
   - Tenet 0: Could any user data be lost? Is capture-first preserved?
   - Tenet 1: Is the code AI-friendly? Would another AI session understand it?
   - Tenet 2: Did we over-engineer something AI will handle better soon?
   - Tenet 3: Are files appropriately sized? Types centralized?
   - Tenet 4: Is the work log verbose enough for handoff?
   - Tenet 5: Did we check: can this be simplified toward the ideal?

14. **Update work log** — Add dated entry: what was done, decisions made, evidence, any blockers or follow-ups.

15. **Update status** — If all acceptance criteria met and checks pass, mark story Done. Update `docs/stories.md` index.

## Work Log Format

```
YYYYMMDD-HHMM — action: result, evidence, next step
```

Entries should be verbose. Capture decisions, failures, solutions, and learnings. These are build artifacts — any future AI session should be able to pick up context from the log.

## Guardrails

- Never write implementation code before the human gate (step 9) — exploration and planning are read-only
- Never skip acceptance criteria verification
- Never mark Done if any check fails
- Never mark Done if the runtime smoke test (11c) was skipped — static checks passing ≠ app works
- Never mark Done if eval mismatches remain unclassified (11b) — silently accepting noise is a hard stop
- Never commit without running the required checks for changed scope
- Always update the work log, even for partial progress
- If blocked, record the blocker and stop — don't guess

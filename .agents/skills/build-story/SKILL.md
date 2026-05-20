---
name: build-story
description: Execute a story from planning through implementation with work-log discipline
user-invocable: true
---

# /build-story [story-number]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`, `docs/methodology/graph.json`, generated dashboards, and relevant decision records in `docs/decisions/` / `docs/design/`. If this work touches a known constraint in `docs/spec.md`, respect both its limitation type and its current state phase (`climb`, `hold`, `converge`, `unplanned`). If none apply, say so explicitly.

Execute a development story end-to-end.

## Eval Ladder Gate

For AI-capability work, identify the eval ladder before creating or prioritizing
implementation backlog:

- the root Ideal eval or full-path golden, or the explicit reason it is deferred
- the parent eval or latest higher-level result that shows the current failure
- the measured failure mode that makes decomposition necessary
- the child eval, failure-classification attempt, ADR/spec update, or story that
  advances the next unresolved ladder node

Prefer rerunning a root/parent eval when new models, provider changes, code
changes, scorer fixes, or changed constraints could collapse the current
decomposition. Prefer a child eval or failure-classification attempt when the
parent failure is still too vague to choose AI-only, multi-call AI, deterministic
code, or hybrid implementation honestly.

## Phase 1 — Explore (read-only, no file writes)

1. **Resolve story** — Read `docs/stories/story-{NNN}-*.md` (or resolve from the generated story index `docs/stories.md` if id/title/path is ambiguous). Verify status is Draft, Pending, In Progress, or Blocked.
   - If status is **Draft**, do not stop yet. Continue through the required-section and substrate checks first.
   - If the Draft story is still skeletal, underspecified, or substrate-unverified after those checks, STOP and recommend keeping it `Draft`.
   - If the Draft story is already detailed enough and substrate-verified, record that it should be promoted and continue.
   - If status is **Blocked**, read `Blocker Summary`, `Blocker Evidence`, `Unblock Condition`, the latest work log, and `## Plan` first. STOP unless the user explicitly asked to reassess the blocker.
   - When reassessing a blocked story, continue only if there is fresh evidence that the unblock condition is now met. If it is still unmet, rewrite any stale plan text that still reads as "proceed" or "build now" so the story matches blocker truth, then stop and report the line as a health flag.

2. **Verify required sections** — Ensure the story has usable:
   - Goal
   - Acceptance Criteria
   - Tasks (checkbox items)
   - Workflow Gates
   - Work Log
   If tasks or workflow gates are missing, add actionable checkboxes without discarding existing intent.

3. **Read context** — Read `docs/ideal.md` first, then all spec refs,
   dependency stories, the relevant state lane in `docs/methodology/state.yaml`,
   and referenced ADRs. If the story does not cite an ADR and the work affects
   architecture, workflow, schemas, or UX patterns, search `docs/decisions/`
   and `docs/design/` for relevant decision records instead of assuming none
   exist. Read the "Files to Modify" list if present.

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
   - Identify existing components, helpers, services, or abstractions that this change could replace or make redundant
   - Note any schema, config, or migration concerns

5b. **Scope coherence check** — If exploration reveals important work that is missing from the story but is necessary to actually satisfy the story goal:
   - **Small, tightly coupled delta** → expand the current story inline. Update the story's acceptance criteria, tasks, and work log so the real scope is visible.
   - **Larger delta** → do not silently absorb it or silently split it out. Add it to the plan as a recommended scope expansion for user approval.
   - Prefer a follow-up story only when the new work is materially distinct, changes the story goal, adds major blast radius, or would make validation unclear.
   - If exploration proves the story cannot honestly proceed because of a named blocker, record blocker summary, blocker evidence, and unblock condition in the story artifact and plan to mark it `Blocked` instead of pretending it is build-ready.
   - When a story becomes `Blocked`, clear or rewrite any stale `## Plan` text that still implies immediate implementation. The visible next move should be the unblock condition or reassessment path, not an invalidated build plan.

6. **Record exploration findings** — Write a brief "Exploration Notes" entry in the work log:
   - Files that will change
   - Files at risk of breaking
   - ADRs / decision docs consulted
   - Patterns to follow
   - Potential redundant code or cleanup targets
   - Any surprises or risks found

## Phase 2 — Plan (produces a written artifact)

If the implementation approach is genuinely unclear because the solution space
is weak, use `/ideation` before writing the plan. Keep this optional and
bounded: the ideation packet can improve alternatives and tradeoffs. If the
user has explicitly authorized delegation and the option search is not blocking
the immediate next local step, a bounded ideation subagent is a good fit. The
main `/build-story` thread still owns the plan, approval gate, and final
implementation judgment.

7. **Eval-first approach gate** — Before planning implementation, establish how you'll measure success and which approaches to compare:
   - **What eval?** Identify or create a test that measures whether this task succeeds. Even a minimal fixture + assertion counts. If no eval exists for this area, create one before choosing an approach.
   - **What's the baseline?** Run the eval against current code. Document the number.
   - **What are the candidate approaches?** For any task involving reasoning, language, or understanding: enumerate at least AI-only, hybrid (deterministic detection + AI judgment), and pure code. The story's "Approach Evaluation" section is input — if it pre-decided an approach without eval evidence, challenge it.
   - **Test the simplest first.** Often that's a single LLM call. Run it against the eval. If it works, don't build code for a problem AI already solves.
   - For pure orchestration/storage/plumbing/UI: code is obviously simpler — no comparison needed.
   - **Model selection requires live data**: Never pick models from training data. Query the provider API and check current pricing. Cost differences can be 10-20x.

8. **Repo-fit / optimality gate** — Before writing the plan, prove the chosen approach fits this repo better than the alternatives:
   - Cite project evidence: relevant `docs/ideal.md` guidance, spec compromises, ADRs, prior stories, existing code patterns, eval results, and current code constraints
   - State why the chosen approach is better here, not just generally plausible
   - State why the main alternatives were rejected
   - If you cannot produce repo-specific evidence, do more research instead of calling the plan "optimal"
   - Avoid research theater: concise evidence beats generic architecture prose

9. **Structural Health Check** — Before writing the plan, assess architectural fit:
   - Run `make check-size` (or `wc -l` on each file in "Files to Modify") — list every file to be touched with its current line count
   - If any file is >500 lines: note it explicitly in the plan. If the story adds logic to it without a decomposition task first, flag as a plan risk and consider adding an extraction phase
   - If any method to be modified is >100 lines: first task should be extracting it into a testable unit
   - For any new data crossing a layer boundary (engine↔service, service↔API, API↔UI): verify a Pydantic model is defined in a schema file before code that uses it — if not, add a schema-first task
   - For any new event type: verify it has an entry in `src/cine_forge/schemas/events.py` before the emit call site
   - Record the health check findings in the plan

10. **Write the implementation plan** — Add a `## Plan` section to the story file with:
   - For each task: which files change, what changes, in what order
   - Impact analysis: what tests are affected, what could break
   - Repo-fit / optimality evidence (from step 8)
   - Structural health check findings (from step 9)
   - Redundancy plan: what old code, helper paths, or docs should be removed if the new path lands
   - UI verification plan for UI-affecting work: browser tools to use, the desktop and mobile golden paths to exercise, and the fallback runbook if browser tooling is unavailable
   - Any human-approval blockers (new dependencies, schema changes, public API changes)
   - Any recommended scope adjustments discovered during exploration
   - What "done" looks like for each task

11. **Human gate** — Present the plan to the user. Surface any ambiguities or risks. Do not write any implementation code until the user approves. If something in the plan is unclear, ask now — not mid-implementation.
   - Small scope expansions already folded into the story should be called out explicitly.
   - Larger scope expansions should be presented as a recommendation with rationale and relative effort (`XS`, `S`, `M`, `L`, `XL`) before implementation starts.

## Optional Delegation After the Plan Gate

When launching post-plan sidecars, size each worker model and reasoning level to shard risk. Use cheaper or lower-reasoning workers for lookup, compatibility-link or optional-alias checks, and mechanical scans; keep stronger workers for semantic contracts, security, eval correctness, cross-repo decisions, or high-cost misses. Record any explicit override rationale in the plan or work log.

After the user approves the Phase 2 plan, the main thread may use
subagents/sidecars for non-trivial work when delegation reduces risk or protects
context. Keep routine small stories single-threaded.

- The main thread owns the approved plan, Ideal/spec fit, integration, final
  implementation judgment, and handoff.
- Useful post-gate sidecars include bounded exploration that no longer blocks
  approval, disjoint implementation slices, test or eval writing, artifact
  inspection, and review of already-written changes.
- Before delegated code edits, assign explicit, disjoint file, service, or UI
  surface ownership. Do not let multiple agents edit overlapping files or settle
  shared product or architecture questions independently.
- Subagents do not reopen scope, choose the final design, mark workflow gates,
  or decide whether the story is ready for validation.
- If delegation is unavailable, unsafe for the checkout, or explicitly disabled,
  run the same work sequentially and note the fallback.

## Phase 3 — Implement

12. **Implement** — Work through tasks in order. For each task:
   - If the story status is `Draft` and exploration proved it honestly buildable, first promote it to `Pending` and run `pnpm methodology:compile` so the status matches repo reality.
   - If the story status is `Pending`, set it to `In Progress` before implementation starts, then run `pnpm methodology:compile`
   - Mark task as in progress in the story file
   - Do the work
   - Run relevant project checks after meaningful changes (backend: unit tests + Ruff; UI: `pnpm --dir ui run lint` and `cd ui && npx tsc -b`)
   - For significant UI changes, use browser tools during the build loop when possible in both desktop and mobile views (screenshot + console check), not only at the end
   - Run relevant tests
   - Mark task complete with brief evidence
   - If implementation or deeper exploration proves a real blocker instead, record it, set the story to `Blocked`, rewrite stale `## Plan` text around the unblock path, regenerate the graph/index, and stop

13a. **Static verification** — Run the project's full validation suite:
   - Backend: `make test-unit PYTHON=.venv/bin/python` and `.venv/bin/python -m ruff check src/ tests/`
   - UI: `pnpm --dir ui run lint` and `cd ui && npx tsc -b`
   - `pnpm --dir ui run build` (catches errors typecheck misses)
   - Methodology surfaces (if story metadata, ADR metadata, AGENTS, runbooks,
     or skills changed): `pnpm methodology:check`
   - Review each acceptance criterion — is it met?

13b. **Eval mismatch investigation** (if the story touched an AI module or eval):
   - Run relevant promptfoo evals or acceptance tests
   - Prompt the user to run `/improve-eval` when structured mismatch investigation is needed. At minimum, complete its failure-classification workflow so every mismatch is tagged **model-wrong**, **golden-wrong**, or **ambiguous** before the story can close. Do not attempt the full investigation inline — it overwhelms context.
   - **Re-assess acceptance criteria against verified scores.** Golden or scorer fixes discovered through `/improve-eval` change the real scores. What looked like a passing story on raw scores may fail on verified scores (or vice versa). Only verified scores determine whether acceptance criteria are met.
   - Do not proceed to Done if mismatches remain unclassified
   - **Update `docs/evals/registry.yaml`** with new scores, `git_sha`, and date for every eval you ran. Stale registry scores are worse than no scores — they cause future agents to waste time on already-solved problems or miss regressions.

13c. **Runtime smoke test** — Verify the app actually works end-to-end:
   - Start dev servers — confirm they start with no error output in logs
   - If backend changed: hit the health endpoint — confirm 200 with valid JSON
   - If any frontend files changed: use browser tools when possible to capture screenshots, exercise the changed UI path in desktop and mobile views, and inspect JS console errors
   - For UI/product verification, use a project state that is reachable through the normal API/driver pipeline for the feature under test. Do not treat hand-seeded artifacts, manually copied project dirs, or impossible substrate combinations as acceptance evidence. Synthetic fixtures are allowed only for narrow mechanical smoke checks and must be called out explicitly as non-representative.
   - If browser tools are unavailable or failing: follow `docs/runbooks/browser-automation-and-mcp.md` and record the blocker
   - If frontend→backend communication was added or changed: confirm the call succeeds and response is correct
   - Run a redundancy pass before closing: remove obsolete code paths if safe, otherwise record a concrete follow-up
   - Record evidence in the work log: server startup output, curl response, screenshot description, console status, redundancy outcome
   - **Do not mark Done if this step was skipped** — static checks passing ≠ app works

14. **Update docs** — Search all docs in the codebase and update any related to
   what we touched. If story metadata, ADR metadata, or methodology state
   changed during the work, rerun `pnpm methodology:compile`.

15. **Verify Central Tenets** — Check each tenet checkbox in the story:
   - Tenet 0: Could any user data be lost? Is capture-first preserved?
   - Tenet 1: Is the code AI-friendly? Would another AI session understand it?
   - Tenet 2: Did we over-engineer something AI will handle better soon?
   - Tenet 3: Are files appropriately sized? Types centralized?
   - Tenet 4: Is the work log verbose enough for handoff?
   - Tenet 5: Did we check: can this be simplified toward the ideal?

16. **Update work log** — Add dated entry: what was done, decisions made, evidence, any blockers or follow-ups.

17. **Implementation handoff** — Do not close the story here:
   - Check the `Build complete` workflow gate
   - Leave `Validation complete or explicitly skipped by user` and `Story marked done via /mark-story-done` unchecked
   - Leave the story status as `In Progress`
   - Give the user a concise implementation summary, briefly explain the practical impact in plain language (what improved, what the operator or end user should notice, or what risk got smaller), highlight any residual risks, recommend `/validate` as the next step, and include a short `Where to verify` note whenever there is a concrete way for the user to inspect the result themselves
   - `Where to verify` should be specific and optional: UI work should name the route/screen plus 1-3 interactions; CLI/backend work should name the command, endpoint, or file to inspect
   - Phrase the recommended next step so the user can approve it with a simple `yes`. Prefer the explicit form: Reply `yes` to proceed with: `/validate <story-id>` when that is the one clear next move.
   - By default, stop here. If the user already explicitly approved the next step(s), continue to `/validate` inline instead of asking again

## Work Log Format

```
YYYYMMDD-HHMM — action: result, evidence, next step
```

Entries should be verbose. Capture decisions, failures, solutions, and learnings. These are build artifacts — any future AI session should be able to pick up context from the log.


## Reviewed Learning Hook

Before final handoff, run or explicitly consider `/learning-review` only when
this build was noisy, failed, widened unexpectedly, exposed a missing guardrail,
or included an explicit user correction that appears reusable. Skip the detector
for ordinary successful builds. If `/learning-review` returns
`RESULT: candidate-warranted`, report the finding or draft it through
`/learning-candidate`; do not promote or mutate live workflow surfaces during
ordinary build closeout.

## Guardrails

- Never write implementation code before the human gate (step 11) — exploration and planning are read-only
- Never skip acceptance criteria verification
- Never claim an approach is "optimal" without repo-specific evidence
- Never trust or preserve stale blocked-story plan text that contradicts the current blocker evidence
- Never leave obvious redundant code in place without either removing it or recording a concrete follow-up
- Never mark a story `Done` from `/build-story` — story closure belongs to `/mark-story-done`
- Never mark Done if any check fails
- Never mark Done if the runtime smoke test (13c) was skipped — static checks passing ≠ app works
- Never mark Done if eval mismatches remain unclassified (13b) — silently accepting noise is a hard stop
- Never mark a UI-affecting story Done without browser-based verification evidence or a documented browser-tool blocker
- Never punt necessary adjacent work as "out of scope" when it is still part of delivering the story goal
- Never commit without running the required checks for changed scope
- Always update the work log, even for partial progress
- If blocked, record the blocker and stop — don't guess

---
name: validate
description: Assess implementation quality against story requirements and local diffs
user-invocable: true
---

# /validate [story-number]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`, `docs/methodology/graph.json`, generated dashboards, and relevant decision records in `docs/decisions/` / `docs/design/`. If this work touches a known constraint in `docs/spec.md`, respect both its limitation type and its current state phase (`climb`, `hold`, `converge`, `unplanned`). If none apply, say so explicitly.

Assess whether a story's implementation meets its requirements.

## Steps

1. **Collect local delta first**:
   - `git status --short`
   - `git diff --stat`
   - `git diff`
   - `git ls-files --others --exclude-standard`

2. **Read the story** — Load `docs/stories/story-{NNN}-*.md`. Note all acceptance criteria and tasks.

2b. **Check workflow gates** — Read the `Workflow Gates` section if present. If it is missing on an older story, add equivalent gates before continuing so the handoff state is explicit.

2c. **Separate implementation completeness from close-out bookkeeping**:
   - Missing close-out items owned by `/mark-story-done` or `/finish-and-push` do **not** count as implementation gaps by themselves.
   - Examples: story/status/index flips, changelog entries, commit/push/PR hygiene, or "Story marked done via /mark-story-done".
   - If implementation is complete and only that bookkeeping remains, treat the story as implementation-complete and recommend `Close now`.

3. **Read architecture context** — Read `docs/ideal.md`, the story's spec refs,
   the relevant state lane in `docs/methodology/state.yaml`, and all referenced
   ADRs. If the story touches architecture, workflows, schemas, or UX patterns
   and no ADR is cited, search `docs/decisions/` and `docs/design/` for
   relevant decision records before reviewing implementation quality.

4. **Run the full check suite**:
   - **Mandatory for all code changes** (regardless of perceived scope):
     - **Backend**:
       - `make test-unit PYTHON=.venv/bin/python`
       - `.venv/bin/python -m ruff check src/ tests/`
       - Story-targeted pytest(s) when applicable.
     - **UI**:
       - `pnpm --dir ui run lint`
       - `cd ui && npx tsc -b`
       - If UI files changed: `pnpm --dir ui run build`
   - **Agent/process surfaces**:
      - If `AGENTS.md` or `.agents/skills/` changed: `./scripts/sync-agent-skills.sh --check`
      - If story metadata, ADR metadata, methodology state, runbooks, or other
        methodology surfaces changed: `pnpm methodology:check`
   - **Rationale**: Strict linting (e.g., React 19 purity) and type-checking can flag issues that aren't immediately obvious in the IDE. Running these locally is the only way to ensure a green deployment gate.
   - If a command is unavailable (missing script/tool), report it explicitly.

5. **Review acceptance criteria** — For each criterion:
   - **Met** — Evidence that it works (test output, code reference)
   - **Partial** — Partially implemented, what's missing
   - **Unmet** — Not implemented or broken

6. **Review approach quality and code health:**
   - Does the implementation match the relevant ADRs and repo patterns?
   - Is there evidence this was the right approach for this repo, or does the diff look like generic solutioning?
   - Are there simpler existing abstractions/components/helpers that should have been reused?
   - Did the change make any older code paths, helpers, components, or docs redundant?
   - Did the diff introduce architecture-drift signals such as:
     - compatibility shims or normalization layers that preserve an obsolete path
     - duplicate ownership where two modules/prompts/flows now own the same behavior
     - empty stubs or dead wrappers left behind after a refactor
     - widened types or guard clauses added to tolerate uncertainty instead of fixing the source contract
   - Are there any files over 600 lines that should be split?
   - Are types centralized or scattered?
   - Are error cases handled?
   - Are integration tests covering the boundaries?

7. **Run browser verification for UI changes**:
   - If UI files changed, use browser tools when possible to load the modified flow in both desktop and mobile views, capture screenshots, and inspect browser console errors
   - Browser verification that counts toward acceptance must use a project state reachable through the normal API/driver pipeline for the feature under test. Hand-seeded artifacts, manually copied project dirs, or impossible substrate combinations may be used only for narrow smoke checks and must be labeled non-representative.
   - If browser tools are unavailable or failing, follow `docs/runbooks/browser-automation-and-mcp.md` and report the blocker explicitly
   - Missing desktop or mobile browser evidence for a UI-affecting story is a finding, not a footnote

8. **Eval mismatch investigation** (if the story touched an AI module or eval):
   - Run relevant promptfoo evals or acceptance tests
   - Use `/improve-eval` when structured mismatch investigation is required. At minimum, complete its failure-classification workflow so every mismatch is classified as **model-wrong**, **golden-wrong**, or **ambiguous** with evidence.
   - Unclassified mismatches are a finding (priority: high) — grade cannot exceed B
   - For compromise or detection evals, record whether any remaining failures are `runtime-blocking` or `non-runtime-blocking`. Verified red results only block closure when they are runtime-blocking or when removing that compromise is the story's explicit goal.
   - **Update `docs/evals/registry.yaml`** with verified scores, `git_sha`, and date for every eval you ran

9. **Check Ideal alignment** — Read the relevant section of `docs/ideal.md`. Does the implementation move toward the Ideal or entrench a compromise? If entrenching: is the compromise justified and does a detection eval exist?

10. **Update story handoff state**:
   - Check `Validation complete or explicitly skipped by user` when validation was actually run
   - Leave `Story marked done via /mark-story-done` unchecked
   - Add a work log note summarizing validation outcome and the recommended next step
   - If validation surfaces medium/high architecture drift outside the current
     shipping slice, map it to the best-fit `architecture_audits` domain and
     recommend `/triage-architecture`
   - In that note and in the report, label results only from commands rerun in this validation pass; anything not rerun here must be called out as not freshly verified

11. **Produce report** — Findings must explicitly call out:
   - missing ADR / decision alignment
   - weak or unproven approach selection
   - redundant code left behind
   - explicit drift signals
   - whether any drift signals should feed the architecture-audit lane
   - missing browser verification for UI work
   - unmet acceptance criteria or failed checks
   - remaining implementation gaps separately from close-out bookkeeping owned by `/mark-story-done` or `/finish-and-push`
   - a single closure recommendation: `Close now`, `Rescope then close`, `Keep open`, or `Mark blocked`
   - prefer `Keep open` when the remaining work still belongs to the same subsystem, validation boundary, and success surface
   - use `Rescope then close` only when the remaining work is genuinely separate and already has a clear follow-up home
   - use `Mark blocked` only for named blockers with explicit evidence and an unblock condition recorded in the story artifact
   - if recommending `Rescope then close`, the exact story edits needed before closure
   - a short `Impact` note for technical work: what improved for the operator or end user, what practical issue got smaller, or what they should notice now
   - recommended next step (`/mark-story-done` if clean, otherwise fix issues)
   - phrase the recommended next step so the user can approve it with a simple `yes`; prefer the explicit form: Reply `yes` to proceed with: ... when there is one clear next move
   - a short `Where to verify` note whenever there is a concrete path for the user to spot-check the result themselves
   - `Where to verify` should be concise and optional: UI work should name the route/screen plus 1-3 interactions; CLI/backend work should name the command, endpoint, or file to inspect
   - By default, stop after the report. If the user already explicitly approved the next step(s) and validation is clean enough to proceed, continue to `/mark-story-done` inline instead of asking again

```
## Validation Report — Story {NNN}

### Findings
- [priority: high/medium/low] description

### Checks
- backend tests: PASS/FAIL
- backend lint: PASS/FAIL
- ui checks: PASS/FAIL/NOT RUN (with reason)
- browser verification: PASS/FAIL/NOT RUN (with reason, including desktop + mobile status for UI work)
- agent skill sync: PASS/FAIL/N/A
- missing/unavailable checks: [list]

### Acceptance Criteria
- [criterion]: Met/Partial/Unmet — evidence

### Close-out Follow-up
- [item]: Needed / Not needed — owner (`/mark-story-done`, `/finish-and-push`, or N/A)

### Architecture / ADR Fit
- relevant decisions reviewed: [list]
- aligns with repo patterns: yes/no/partial

### Approach Review
- chosen approach appears justified: yes/no/partial
- evidence: [repo-specific evidence or lack thereof]

### Redundancy Review
- redundant code/docs left behind: yes/no
- details: [list]

### Drift Signals
- compatibility shims / stacked normalization / duplicate ownership / dead wrappers / widened guards: none found | found
- details: [list]

### Ideal Alignment
- Moves toward Ideal: yes/no/partial
- New compromises introduced: [list, with detection eval status]

### Impact
- plain-language effect: [what improved for the operator or end user, what practical issue got smaller, or what they should notice now]

### Grade: A/B/C/D/F

### Closure Recommendation
- Close now / Rescope then close / Keep open / Mark blocked — [reason]

### Next Steps
- [one recommended next step or short sequence phrased so the user can approve it by replying `yes`]
```

## Guardrails

- Never hide gaps or inflate the grade
- Always report unmet criteria clearly
- Always include evidence for "Met" ratings
- Never mark a story `Done` from `/validate` — story closure belongs to `/mark-story-done`
- Never give an A to a UI-affecting story without browser verification evidence from both desktop and mobile views
- Never ignore redundant code that the new implementation clearly supersedes
- Never ignore explicit drift signals just because tests pass
- Never treat close-out bookkeeping owned by `/mark-story-done` or `/finish-and-push` as an implementation failure by itself
- If grade is below B, list specific remediation steps
- When the story is not ready to close, never stop at "not done." Always recommend one disposition: `Rescope then close`, `Keep open`, or `Mark blocked`.
- If implementation is complete and only close-out bookkeeping remains, prefer `Close now`
- Never recommend `Rescope then close` for remaining work that still belongs to the same subsystem, validation boundary, and success surface
- Never report a check as PASS/FAIL unless you reran it in this validation pass and inspected the output
- **Mandatory UI Checks**: Never skip UI `lint` and `tsc -b` for code changes, even if you think only the backend was touched.
- Prefer project-native checks over generic templates
- Use `tsc -b` (not `tsc --noEmit`) for UI type checks in this repo

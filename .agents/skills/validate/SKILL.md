---
name: validate
description: Assess implementation quality against story requirements and local diffs
user-invocable: true
---

# /validate [story-number]

Assess whether a story's implementation meets its requirements.

## Steps

1. **Collect local delta first**:
   - `git status --short`
   - `git diff --stat`
   - `git diff`
   - `git ls-files --others --exclude-standard`

2. **Read the story** — Load `docs/stories/story-{NNN}-*.md`. Note all acceptance criteria and tasks.

3. **Choose the check profile based on scope**:
   - **Backend-only changes** (default in CineForge): run
     - `make test-unit PYTHON=.venv/bin/python`
     - `.venv/bin/python -m ruff check src/ tests/`
     - Story-targeted pytest(s) when applicable (especially integration boundaries)
   - **UI changes** (`ui/` touched): run
     - `pnpm --dir ui run lint`
     - `cd ui && npx tsc -b` (preferred typecheck for this repo)
     - `pnpm --dir ui run build` when available
     - UI tests only if the project defines them
   - **Full-stack changes**: run both backend and UI profiles.
   - If a command is unavailable (missing script/tool), report it explicitly instead of silently skipping.

4. **Review acceptance criteria** — For each criterion:
   - **Met** — Evidence that it works (test output, code reference)
   - **Partial** — Partially implemented, what's missing
   - **Unmet** — Not implemented or broken

5. **Review code quality:**
   - Are there any files over 600 lines that should be split?
   - Are types centralized or scattered?
   - Are error cases handled?
   - Are integration tests covering the boundaries?

6. **Produce report:**

```
## Validation Report — Story {NNN}

### Findings
- [priority: high/medium/low] description

### Checks
- backend tests: PASS/FAIL
- backend lint: PASS/FAIL
- ui checks: PASS/FAIL/NOT RUN (with reason)
- missing/unavailable checks: [list]

### Acceptance Criteria
- [criterion]: Met/Partial/Unmet — evidence

### Grade: A/B/C/D/F

### Next Steps
- [what needs to happen before this can be marked Done]
```

## Guardrails

- Never hide gaps or inflate the grade
- Always report unmet criteria clearly
- Always include evidence for "Met" ratings
- If grade is below B, list specific remediation steps
- Prefer project-native checks over generic templates
- Use `tsc -b` (not `tsc --noEmit`) for UI type checks in this repo

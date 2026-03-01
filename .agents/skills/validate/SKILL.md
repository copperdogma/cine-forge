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

3. **Run the full check suite**:
   - **Mandatory for all code changes** (regardless of perceived scope):
     - **Backend**:
       - `make test-unit PYTHON=.venv/bin/python`
       - `.venv/bin/python -m ruff check src/ tests/`
       - Story-targeted pytest(s) when applicable.
     - **UI**:
       - `pnpm --dir ui run lint`
       - `cd ui && npx tsc -b`
   - **Rationale**: Strict linting (e.g., React 19 purity) and type-checking can flag issues that aren't immediately obvious in the IDE. Running these locally is the only way to ensure a green deployment gate.
   - If a command is unavailable (missing script/tool), report it explicitly.

4. **Review acceptance criteria** — For each criterion:
   - **Met** — Evidence that it works (test output, code reference)
   - **Partial** — Partially implemented, what's missing
   - **Unmet** — Not implemented or broken

5. **Review code quality:**
   - Are there any files over 600 lines that should be split?
   - Are types centralized or scattered?
   - Are error cases handled?
   - Are integration tests covering the boundaries?

5b. **Eval mismatch investigation** (if the story touched an AI module or eval):
   - Run relevant promptfoo evals or acceptance tests
   - Run `/verify-eval` for the structured investigation protocol. Every mismatch must be classified as **model-wrong**, **golden-wrong**, or **ambiguous** with evidence.
   - Unclassified mismatches are a finding (priority: high) — grade cannot exceed B
   - **Update `docs/evals/registry.yaml`** with verified scores, `git_sha`, and date for every eval you ran

6. **Check Ideal alignment** — Read the relevant section of `docs/ideal.md`. Does the implementation move toward the Ideal or entrench a compromise? If entrenching: is the compromise justified and does a detection eval exist?

7. **Produce report:**

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

### Ideal Alignment
- Moves toward Ideal: yes/no/partial
- New compromises introduced: [list, with detection eval status]

### Grade: A/B/C/D/F

### Next Steps
- [what needs to happen before this can be marked Done]
```

## Guardrails

- Never hide gaps or inflate the grade
- Always report unmet criteria clearly
- Always include evidence for "Met" ratings
- If grade is below B, list specific remediation steps
- **Mandatory UI Checks**: Never skip UI `lint` and `tsc -b` for code changes, even if you think only the backend was touched.
- Prefer project-native checks over generic templates
- Use `tsc -b` (not `tsc --noEmit`) for UI type checks in this repo

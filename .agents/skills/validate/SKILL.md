---
name: validate
description: Assess implementation quality against story requirements
user-invocable: true
---

# /validate [story-number]

Assess whether a story's implementation meets its requirements.

## Steps

1. **Read the story** — Load `docs/stories/story-{NNN}.md`. Note all acceptance criteria and tasks.

2. **Run checks:**
   - `pnpm typecheck` — zero errors?
   - `pnpm test` — all pass?
   - `pnpm lint` — clean?

3. **Review acceptance criteria** — For each criterion:
   - **Met** — Evidence that it works (test output, code reference)
   - **Partial** — Partially implemented, what's missing
   - **Unmet** — Not implemented or broken

4. **Review code quality:**
   - Are there any files over 600 lines that should be split?
   - Are types centralized or scattered?
   - Are error cases handled?
   - Are integration tests covering the boundaries?

5. **Produce report:**

```
## Validation Report — Story {NNN}

### Checks
- typecheck: PASS/FAIL
- tests: PASS/FAIL (X passed, Y failed)
- lint: PASS/FAIL

### Acceptance Criteria
- [criterion]: Met/Partial/Unmet — evidence
- [criterion]: Met/Partial/Unmet — evidence

### Findings
- [priority: high/medium/low] description

### Grade: A/B/C/D/F

### Next Steps
- [what needs to happen before this can be marked Done]
```

## Guardrails

- Never hide gaps or inflate the grade
- Always report unmet criteria clearly
- Always include evidence for "Met" ratings
- If grade is below B, list specific remediation steps

---
name: align
description: Check alignment of the methodology graph after a change — Ideal, ADRs, Spec, State, Generated Dashboards, Stories, Evals — and propose corrections
user-invocable: true
---

# /align [what-changed | ADR-NNN]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, and relevant decision records in `docs/decisions/` / `docs/design/`. If this work touches a known compromise in `docs/spec.md`, respect its limitation type and evolution path. If none apply, say so explicitly.

Check the methodology graph for misalignment after a change. Read-only and advisory — surfaces what needs attention, doesn't rewrite anything.

Companion runbook: `docs/runbooks/align.md`

## When to Use

Any time something changes that might ripple through the methodology graph:

- an ADR is decided
- the Ideal changes
- the spec changes
- methodology state or generated dashboards change materially
- an eval or external model shift suggests a compromise might be deletable
- a story lands and changes system structure
- no specific trigger — you just want to check for drift

## Steps

1. **Identify the change**
   - Use the argument, recent git history, or the current thread context.

2. **Read current state**
   - `docs/ideal.md`
   - `docs/methodology-ideal-spec-compromise.md`
   - `docs/spec.md`
   - `docs/methodology/state.yaml`
   - `docs/methodology/graph.json`
   - `docs/build-map.md`
   - `docs/stories.md`
   - relevant ADRs / decision docs
   - relevant eval entries in `docs/evals/registry.yaml`

3. **Check alignment across the graph**

   **Ideal**
   - Does this reveal a new requirement or preference?
   - Does it make an implicit ideal explicit?

   **Spec / compromises**
   - Does this create, simplify, or delete a compromise?
   - Does it change a limitation type or detection mechanism?

   **Methodology state / generated dashboards**
   - Does system ownership or dependency order change?
   - Do substrate, phase, roadmap, or compromise-progress fields need an update?

   **Stories**
   - Are any Draft/Pending/In Progress stories now blocked, stale, or unnecessary?
   - Should a follow-up story exist? Flag it, don't create it.

   **Evals**
   - Should any evals be re-run, added, or retired?
   - Do any detector failures need runtime-blocking vs non-runtime-blocking classification?

   **ADRs**
   - Does the change contradict an accepted decision?
   - Should a decision be updated or superseded?

4. **Produce the alignment report**

```markdown
## Align — {what changed}

### Ideal
- {impact or "Aligned"}

### Spec
- {impact or "Aligned"}

### State / Dashboards
- {impact or "Aligned"}

### Stories
- {affected stories or "Aligned"}

### Evals
- {eval actions or "Aligned"}

### ADRs
- {decision impact or "Aligned"}

### Recommended Actions
- [ ] {specific action}
```

5. **Suggest next steps**
   - State update → edit `docs/methodology/state.yaml`, then rerun `pnpm methodology:compile`
   - Story realignment → `/triage stories`
   - Eval action → `/triage evals` or `/improve-eval`
   - New decision needed → create or update an ADR

## Guardrails

- This skill is read-only and advisory
- Always read the actual docs instead of guessing from memory
- If everything is aligned, say so directly
- Do not create stories, inbox items, or ADRs from this skill

---
name: triage-architecture
description: Decide whether an architecture audit is due, target the highest-leverage domain, and recommend or record the next simplification action
user-invocable: true
---

# /triage-architecture [scan] [domain-id]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`, `docs/methodology/graph.json`, and relevant decision records in `docs/decisions/` / `docs/design/`. If none apply, say so explicitly.

Architecture-audit leaf skill for recurring refactor and simplification triage.

Use this when the question is not "what feature should we build next?" but
"where is architecture drift or structural simplification most due right now?"

Companion runbook: `docs/runbooks/triage-architecture.md`

## Modes

- **Default mode** (`/triage-architecture` or `/triage-architecture <domain-id>`)
  - audit-focused
  - may update `docs/methodology/state.yaml` for the audited domain(s)
  - should rerun `pnpm methodology:compile` if it records state changes
- **Scan mode** (`/triage-architecture scan` or `/triage-architecture scan <domain-id>`)
  - read-only
  - used by `/triage`
  - never edits files

## Inputs

- `scan` — optional first argument; switches to read-only mode
- `domain-id` — optional. Focus a specific audit domain from
  `state.architecture_audits.domains` instead of selecting one automatically

## Phase 1 — Identify Whether an Audit Is Due

1. **Read the shared methodology frame**
   - `docs/ideal.md`
   - `docs/spec.md`
   - `docs/methodology/state.yaml`
   - `docs/methodology/graph.json`
   - recent `git log --oneline -20`

2. **Read architecture-audit state**
   - `state.architecture_audits.cadence`
   - `state.architecture_audits.domains`
   - note:
     - `last_audited_at`
     - `recent_story_refs`
     - `stories_since_audit`
     - `open_findings`
     - `manual_priority`
     - any `last_result` / `last_summary` fields if present

3. **Pick the target domain**
   - If the user passed a `domain-id`, audit that domain directly
   - Otherwise rank domains using this order:
     - explicit `manual_priority: high`
     - domains with open findings
     - domains whose `stories_since_audit` meets or exceeds the target cadence
     - domains with recent story churn but no prior audit
     - domains that have been untouched longest while still owning active work
   - Audit at most 1-2 domains in one pass

4. **Name why the audit is due**
   - concentrated churn
   - repeated drift signals
   - stale audit history
   - active focus / roadmap relevance
   - performance / complexity complaints

If no domain is credibly due, say so clearly. In default mode, record a no-op
for the best candidate domain rather than leaving the lane silent forever.

## Phase 2 — Inspect the Target Domain

For each selected domain:

1. **Read the recent work**
   - open the recent story files listed in `recent_story_refs`
   - inspect relevant ADRs and spec sections
   - if a recent validation report or work-log note flagged drift, use that as
     an audit seed

2. **Inspect the current code reality**
   - inspect the ownership surface the domain maps to
   - read hotspot files
   - inspect recent churn for the domain when useful
   - verify whether the claimed substrate is real in code, not just in docs

3. **Look specifically for architecture-drift signatures**
   - compatibility shims preserving an obsolete path
   - wrappers with no real abstraction value
   - duplicate ownership or second homes for the same behavior
   - stale old paths left alive after the new path shipped
   - files/modules growing because ownership never got re-homed
   - performance issues caused by indirect architecture rather than tuning

4. **Bias toward simplification**
   - prefer delete / merge / re-home / narrow / split by ownership
   - propose a new architecture only when the current shape is clearly the
     blocker and simplification alone is insufficient

## Phase 3 — Decide the Output

Valid outputs are:

- **No action**
  - the domain looks healthy enough
  - record that the audit happened and why no change is needed
- **Follow-up story**
  - the issue is real and needs implementation work
  - prefer one concrete story over a vague cleanup umbrella
- **Fold into existing story**
  - a current in-flight story already owns the needed simplification
- **Escalate architecture decision**
  - only if ADR-level uncertainty actually exists

When findings came from validation drift signals, explicitly map them back to
the audit domain and say whether they should now be recorded as open findings
or treated as already resolved by this audit.

## Phase 4 — Record State (default mode only)

If not in scan mode, update the audited domain(s) in
`docs/methodology/state.yaml`:

- set `last_audited_at`
- update `open_findings`
- update `stories_since_audit`
- add or refresh `last_result` / `last_summary` when useful
- keep `recent_story_refs` honest if the audit was triggered by newly completed
  work

Then rerun:

```bash
pnpm methodology:compile
```

Do not create a story automatically unless the user explicitly asked for that
follow-on action. Recording an audit result is allowed; creating implementation
work is a separate decision.

## Output Format

Use:

```markdown
## Architecture Triage

### Target Domain
- <domain-id> — <why this domain was chosen>

### Why Now
- <cadence/churn/staleness/open-finding reason>

### Findings
- <finding or "No major simplification work justified">

### Recommendation
- <no action | create story | fold into existing story | escalate decision>

### State Update
- <recorded | scan mode, no changes>

### Kickoff
- <exact next command or concrete action on yes>
```

End with one concrete default recommendation and a direct yes/no handoff.

## Guardrails

- In scan mode, never modify files
- Audit at most 1-2 domains per pass
- Prefer simplification over novelty
- Do not recommend repo-wide undirected cleanup
- Do not force an architecture story when a no-op audit is the honest result
- Do not record stale open findings if the audit just proved they are gone
- When validation or story work logs raised the finding, cite that source
- If the user passed a domain id, honor it instead of re-ranking the whole repo

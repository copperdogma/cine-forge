---
name: triage-health
description: Return read-only CineForge health and freshness candidates for triage orchestration
user-invocable: true
---

# /triage-health [scan]

Use this as a read-only lane for CineForge triage health and freshness. It
feeds full-sweep `/triage`; it does not make the final cross-domain decision.

## Contract

`/triage-health` is always read-only, including direct scan mode. It may
recommend follow-up commands such as `/codebase-improvement-scout`,
`/triage-evals`, `/triage-architecture`, `/discover-models`, UI-scout work, or
methodology wrapper sync, but it must not run heavy provider calls, broad
codebase scouts, architecture audits, dependency changes, or implementation
work during ordinary triage. It returns neutral health candidates for
`/triage` to rank; it does not select the repo-wide recommendation or a final
health winner.

## Evidence To Read

1. Read the shared frame:
   - `docs/ideal.md`
   - `docs/spec.md`
   - `docs/methodology/state.yaml`
   - `docs/methodology/graph.json`
   - `docs/ui-scout.md`
2. Run the parseable fact collector directly:

   ```bash
   python scripts/triage_facts.py --json
   ```

3. Inspect existing health surfaces only:
   - latest `docs/reports/codebase-improvement/*.md`
   - `docs/evals/registry.yaml`
   - `docs/evals/attempts/`
   - `docs/evals/models-available.yaml`
   - `docs/methodology/state.yaml` architecture-audit and UI-scout state
   - `.agents/skills`, `.gemini/commands`, and `scripts/sync-agent-skills.sh --check`
   - `pyproject.toml`, `package.json`, and existing dependency/provider notes when relevant

## Candidate Areas

Return up to three health candidates:

- **UI-scout freshness** — stale, failed, or never-run canonical scenarios;
  reports marked `issues_found` / `recheck_due`; or UI claims that no longer
  match the honest product path.
- **Codebase improvement freshness** — broad hygiene scan age, source churn
  since the last scan, unresolved scan recommendations, or absence of a real
  broad report.
- **Eval/model/golden freshness** — stale scores, ready retry triggers, new
  model evidence already recorded, missing root/parent/child eval proof, or
  golden-build debt.
- **Methodology/tooling health** — wrapper drift, generated graph drift,
  missing active surfaces, setup checklist drift, or skill-sync problems.
- **Architecture-audit health** — due domains from `architecture_audits`,
  open findings, repeated drift, or stale recent-story references.
- **Dependency/provider health** — existing evidence of provider, Python,
  Node, package, or dependency drift that could make the next feature/eval
  story misleading.

## Output

Use this shape:

```markdown
## Triage Health

### Health Candidates
1. {candidate}
   - Evidence: {files/facts}
   - Why now: {trigger}
   - Suggested action: {follow-up command or no-op}
   - Stop condition: {what would make it done}
   - Blockers: {constraints/dependencies, if any}
   - Reasons not now: {if any}

### Lane Packet
- {neutral health candidate + Ideal/spec value + evidence + why now + action shape + stop condition + blockers + reasons not now}

### Stop Conditions
- {why no health action is warranted now, if applicable}
```

## Guardrails

- Stay read-only.
- Do not run `/codebase-improvement-scout`, `/discover-models`,
  `/triage-architecture`, provider-backed evals, golden builds, dependency
  upgrades, or implementation work during health triage.
- Do not let health work automatically outrank a larger Ideal/spec product or
  eval gap; return evidence so `/triage` can rank it.
- Do not treat UI-scout freshness as optional when the Ideal gap is product
  feel, operator confidence, or workflow obviousness.

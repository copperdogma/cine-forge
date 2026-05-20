# Triage Health

Use this runbook for read-only health and freshness evidence during full-sweep
`/triage`. The health lane gathers candidates; the main triage thread chooses
the final recommendation against `docs/ideal.md`.

## Evidence

- `python scripts/triage_facts.py --json`
- `docs/methodology/state.yaml`
- `docs/methodology/graph.json`
- `docs/ui-scout.md` and latest `docs/ui-scout/*.md`
- `docs/evals/registry.yaml`, `docs/evals/attempts/`, and
  `docs/evals/models-available.yaml`
- latest `docs/reports/codebase-improvement/*.md`
- `.agents/skills`, compatibility links, optional command aliases, and `scripts/sync-agent-skills.sh --check`

## Candidate Types

- UI-scout freshness or unresolved UI-scout follow-up
- codebase-improvement scan freshness
- eval/model/golden freshness
- methodology/tooling drift
- architecture-audit due domains or open findings
- dependency/provider health

## Output

Return up to three neutral health candidates with evidence, why now, suggested
action shape, stop condition, and reasons not now. Do not choose the repo-wide
winner. Health packets feed the main `/triage` top-three shortlist and final
recommendation.

## Guardrails

- Read-only only.
- Do not run heavy scans, provider-backed evals, architecture audits, or
  implementation work.
- Do not let health automatically outrank larger product/eval gaps.
- Do not dismiss UI-scout freshness when the Ideal concern is product feel,
  fun, obviousness, or operator confidence.

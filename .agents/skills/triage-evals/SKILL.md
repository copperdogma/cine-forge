---
name: triage-evals
description: Diagnose which eval, compromise gate, or stale benchmark needs attention next using current registry data
user-invocable: true
---

# /triage-evals [eval-id|compromise-id] [--stale-only]

> ADR check: If this task raises an architectural, workflow, schema, or UX question, read the relevant decision record(s) in `docs/decisions/` and supporting docs in `docs/design/` before choosing an approach. If none apply, say so explicitly.

Cheap, read-only eval diagnosis. Use this when the question is "what should we work on next?" rather than "go improve this eval now."

Companion runbook: `docs/runbooks/triage-evals.md`

## Purpose

- Identify the next eval, compromise gate, or stale score that deserves attention
- Surface whether the right next action is `/improve-eval`, a fresh benchmark rerun, `/verify-eval`, or no action
- Keep diagnosis cheap by reading `docs/evals/registry.yaml`, result artifacts, and existing helper scripts instead of running promptfoo by default

## Inputs

- `[eval-id|compromise-id]` — optional. Focus on a specific eval or compromise gate instead of scanning the full registry.
- `--stale-only` — optional. Only report stale or under-measured evals rather than ranking all candidates.

## Phase 1 — Inventory

1. **Read the registry first** — open `docs/evals/registry.yaml` and note:
   - eval type (`quality` vs `compromise`)
   - targets
   - latest `scores`
   - latest `git_sha`
   - prior `attempts`

2. **Check current repo state**:
   - `git rev-parse --short HEAD`
   - `git status --short`
   - if the worktree is dirty, note that some score staleness may be unmeasurable until those changes are committed or discarded

3. **Check compromise status cheaply**:
   - Run `.venv/bin/python scripts/check-compromises.py`
   - Note which compromises are already green, nearly green, or blocked by a single weak eval

4. **Check model landscape cheaply**:
   - Run `.venv/bin/python scripts/discover-models.py --summary`
   - Note new or recently available models that could invalidate older "model-insufficient" conclusions

## Phase 2 — Diagnose

If the user passed a specific eval or compromise id:

1. Assess that item directly:
   - Is the latest score stale relative to current `HEAD`?
   - Is it missing attempt history?
   - Is it near target, badly below target, or already good enough?
   - Does it look blocked by golden quality, prompt quality, model choice, or simple lack of recent measurement?
2. Recommend the next action:
   - `/improve-eval`
   - rerun benchmark first
   - `/verify-eval`
   - no action
3. Stop after the focused report.

If no id was passed:

1. Rank candidates using this order:
   - **Priority 1: stale default-driving evals** — scores behind `HEAD` on evals that back current model defaults
   - **Priority 2: near-target evals** — quality, latency, or cost gaps small enough that one more attempt could plausibly close them
   - **Priority 3: compromise leverage** — evals whose improvement could eliminate or simplify a live compromise
   - **Priority 4: under-investigated failures** — weak or empty attempt history despite clear gaps
   - **Priority 5: passing-but-expensive defaults** — good quality with suspicious latency/cost compared to the rest of the field

2. For each top candidate, answer:
   - What is the current state?
   - Why does it matter now?
   - What is the cheapest next step?
   - Is the problem likely model-wrong, golden-wrong, stale-measurement, or architecture-limited?

3. Produce a ranked top 3-5 list unless `--stale-only` was passed.

## Phase 3 — Recommend

For each recommended item, end with one concrete next action:

- **`/improve-eval <eval-id>`** — when the registry is current enough and the next improvement attempt is clear
- **Rerun benchmark first** — when score staleness makes diagnosis unreliable
- **`/verify-eval`** — when the main blocker appears to be mismatch classification or golden quality
- **Skip for now** — when the eval is healthy enough or the compromise is not actionable yet

## Output Format

Present the result as:

```
## Eval Triage — YYYY-MM-DD

### Registry Health
- Current HEAD: <sha>
- Dirty worktree: yes/no
- Compromise summary: ...
- New model signal: ...

### Top Candidates
1. <eval-or-compromise> — why it ranks here
   State: ...
   Cheapest next action: ...
   Recommendation: /improve-eval | rerun benchmark first | /verify-eval | skip

### Notable Deferrals
- <item> — why it is not worth attention now
```

## Guardrails

- This skill is **read-only diagnosis** by default — do not run promptfoo just to triage
- If scores are clearly stale, say so instead of pretending the ranking is precise
- Do not recommend the same failed approach again without new evidence from attempts, models, or goldens
- Do not treat every red compromise eval as blocking; use AGENTS expected-fail semantics
- When a single model default depends on an eval, prioritize stale defaults over nice-to-have benchmarking curiosity

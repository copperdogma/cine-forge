---
name: triage-evals
description: Diagnose which eval work best advances the current methodology gap or convergence detector using current registry data
user-invocable: true
---

# /triage-evals [eval-id|compromise-id] [--stale-only]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/build-map.md`, and relevant decision records in `docs/decisions/` / `docs/design/`. If none apply, say so explicitly.

Cheap, read-only eval diagnosis. Use this when the question is "does eval work deserve priority for the current methodology gap?" rather than "go improve this eval now."

Companion runbook: `docs/runbooks/triage-evals.md`

## Purpose

- Identify the next eval, compromise gate, or stale score that deserves attention
- Determine whether eval work is actually the right next move for the current Ideal/spec/build-map gap
- Surface whether the right next action is `/improve-eval`, a fresh benchmark rerun, or no action
- Respect build-map phase semantics:
  - `climb` = quality/capability work
  - `hold` = efficiency, simplicity, latency, or cost work
  - `converge` = deletion work once the gate is truly green
- Keep diagnosis cheap by reading `docs/evals/registry.yaml`, `docs/build-map.md`, result artifacts, and existing helper scripts instead of running promptfoo by default

## Inputs

- `[eval-id|compromise-id]` — optional. Focus on a specific eval or compromise gate instead of scanning the full registry.
- `--stale-only` — optional. Only report stale or under-measured evals rather than ranking all candidates.

## Phase 1 — Inventory

1. **Read the methodology frame first**
   - Open `docs/ideal.md`
   - Open `docs/spec.md`
   - Open `docs/build-map.md`
   - Goal: identify which live gap or compromise eval work would actually serve

2. **Read the registry** — open `docs/evals/registry.yaml` and note:
   - eval type (`quality` vs `compromise`)
   - targets
   - latest `scores`
   - latest `git_sha`
   - prior `attempts`
   - whether the item maps to a live build-map compromise

3. **Check current repo state**:
   - `git rev-parse --short HEAD`
   - `git status --short`
   - if the worktree is dirty, note that some score staleness may be unmeasurable until those changes are committed or discarded

4. **Check compromise status cheaply when the environment allows**
   - Prefer `.venv/bin/python scripts/check-compromises.py`
   - If `.venv` is unavailable, try an equivalent local Python if dependencies exist
   - If the checker cannot run, say so explicitly and fall back to registry-only diagnosis

5. **Check model landscape cheaply when the environment allows**
   - Prefer `.venv/bin/python scripts/discover-models.py --summary`
   - If `.venv` is unavailable, try an equivalent local Python if dependencies exist
   - If the summary cannot run, say so explicitly and fall back to registry-only diagnosis

## Phase 2 — Diagnose

If the user passed a specific eval or compromise id:

1. Assess that item directly:
   - What live gap or compromise does it serve?
   - Is the latest score stale relative to current `HEAD`?
   - Is it missing attempt history?
   - Is it near target, badly below target, or already good enough?
   - Does it look blocked by golden quality, model choice, simple lack of recent measurement, or an architecture limitation?
   - If it is not the current highest-leverage gap, say so explicitly instead of pretending it is top priority
2. Recommend the next action:
   - `/improve-eval`
   - rerun benchmark first
   - no action
3. Stop after the focused report.

If no id was passed:

1. Rank candidates using this order:
   - **Priority 1: evals or detectors attached to the highest-leverage live gap** — especially when they unblock a `climb` decision or a real `converge` deletion
   - **Priority 2: credible convergence detectors** — compromise gates where a passing or near-passing result would simplify the system materially
   - **Priority 3: stale default-driving evals that block decisions in the active category** — not every stale score matters equally
   - **Priority 4: near-target evals with a clear next attempt** — quality, latency, or cost gaps small enough that one more attempt could plausibly close them
   - **Priority 5: under-investigated failures or hold-phase efficiency opportunities** — useful, but subordinate to the larger methodology gap

   If no current methodology gap is eval-led, say that explicitly and recommend story / ADR / spec work instead of forcing eval work to the top.

2. For each top candidate, answer:
   - What is the current state?
   - Why does it matter now?
   - What is the cheapest next step?
   - Which build-map phase does it support?
   - Is the problem likely model-wrong, golden-wrong, stale-measurement, or architecture-limited?

3. Produce a ranked top 3-5 list unless `--stale-only` was passed.

## Phase 3 — Recommend

For each recommended item, end with one concrete next action:

- **`/improve-eval <eval-id>`** — when the registry is current enough and the next improvement attempt is clear
- **Rerun benchmark first** — when score staleness makes diagnosis unreliable
- **Skip for now** — when the eval is healthy enough or the compromise is not actionable yet
- **Do story / ADR / spec work first** — when the bigger gap is not actually waiting on eval evidence

## Output Format

Present the result as:

```
## Eval Triage — YYYY-MM-DD

### Methodology Context
- Primary gap: ...
- Spec / Build Map: ...
- Why eval work does or does not deserve priority now: ...

### Registry Health
- Current HEAD: <sha>
- Dirty worktree: yes/no
- Compromise summary: ...
- New model signal: ...

### Top Candidates
1. <eval-or-compromise> — why it ranks here
   State: ...
   Cheapest next action: ...
   Recommendation: /improve-eval | rerun benchmark first | skip

### Notable Deferrals
- <item> — why it is not worth attention now
```

## Guardrails

- This skill is **read-only diagnosis** by default — do not run promptfoo just to triage
- If scores are clearly stale, say so instead of pretending the ranking is precise
- Do not recommend the same failed approach again without new evidence from attempts, models, or goldens
- Do not treat every red compromise eval as blocking; use AGENTS expected-fail semantics
- When a single model default depends on an eval, stale defaults matter, but they still do not outrank a bigger unrelated `climb` gap without explanation
- Do not force eval work to the top if the current system bottleneck is product substrate rather than measurement

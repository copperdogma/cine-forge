# Triage Evals

## Context

Use this runbook when you need to decide whether eval work deserves attention next for the current methodology gap without paying the cost of a fresh promptfoo run just to get oriented.

This is the operational companion to `/triage-evals`.

## Prerequisites

- `docs/evals/registry.yaml` exists and has current-ish score history
- `.venv` is available for helper scripts
- You understand whether the goal is diagnosis only or a real improvement attempt

## Steps

1. **[script] Read the methodology frame first**
   - Open `docs/ideal.md`
   - Open `docs/spec.md`
   - Open `docs/methodology/state.yaml`
   - Open `docs/methodology/graph.json`
   - Open `docs/build-map.md`
   - Prefer the compiled eval/compromise actionability fields in `graph.json`
     for last-action and retry-posture reads before reconstructing them
     manually from registry prose.
   - Goal: identify the current live gap and whether it is even waiting on eval evidence

2. **[script] Read the current registry and repo state**
   - Open `docs/evals/registry.yaml`
   - Run `git rev-parse --short HEAD`
   - Run `git status --short`
   - Capture the last meaningful action date and artifact for the line you are
     considering.
   - Goal: know whether score entries are obviously stale relative to current code, which systems/compromises would benefit most from eval movement, and whether the right move is a `climb`, `hold`, or `converge` action
   - If the latest attempt has `retry_when` or `retry_status` metadata, open the
     referenced attempt file before calling the eval retry-ready

3. **[script] Check compromise status**
   - Run `.venv/bin/python scripts/check-compromises.py` when possible
   - If the environment cannot run it, say so explicitly and fall back to registry-only judgment
   - Goal: see which compromises are already green, nearly green, or blocked by one weak eval

4. **[script] Check model freshness**
   - Run `.venv/bin/python scripts/discover-models.py --summary` when possible
   - If the environment cannot run it, say so explicitly and fall back to registry-only judgment
   - Goal: spot new SOTA or cheaper models that may invalidate older registry conclusions

5. **[judgment] Classify candidate types**
   - First remove false freshness:
     - if the latest retry trigger is already marked exhausted-until-new-trigger
     - or if the same `retry_when` condition was already checked and nothing
       materially changed
     - then the item is a deferral / health flag, not a top candidate
   - Separate candidates into:
     - evals directly attached to the highest-leverage live gap
     - converge detectors with real simplification leverage
     - stale default-driving evals that block current decisions
     - near-target evals
     - under-investigated failures / hold-phase efficiency opportunities
   - Good output: a short list with a clear reason each item matters now

6. **[judgment] Choose the cheapest next action**
   - Prefer:
     - rerun benchmark first when scores are stale
     - `/improve-eval` when mismatch classification or golden quality is the blocker
     - `/improve-eval` when the registry is current enough and the next attempt is obvious for the category's current phase
     - no eval action when the current methodology bottleneck is product substrate rather than measurement
     - skip when the item is healthy enough or not actionable yet
   - Good output: each candidate ends with one concrete next action, not a vague paragraph

7. **[judgment] Apply expected-fail semantics**
   - For compromise or detection evals, do not treat a red result as automatically blocking
   - Check whether the remaining failure is runtime-blocking or non-runtime-blocking
   - Good output: only runtime-blocking detector failures get elevated as urgent blockers

## Boundaries

### Always do

- Read the registry before recommending any eval work
- Read the methodology frame before deciding eval work is top priority
- Check `git_sha` staleness against current `HEAD`
- Use `scripts/check-compromises.py` and `scripts/discover-models.py --summary` before claiming an eval is the highest leverage next step
- End with a concrete next action per recommended item
- Treat `retry_when` as dormant until a materially new trigger actually appears
- Name the last meaningful action and the current why-now trigger before
  recommending any rerun

### Ask first

- Before running fresh promptfoo evals during triage
- Before modifying goldens, scorers, or benchmark configs
- Before turning triage into an implementation attempt

### Never do

- Never run promptfoo by default just to answer a prioritization question
- Never ignore stale scores when they materially weaken the recommendation
- Never recommend repeating an approach that prior attempt history already disproved
- Never treat an exhausted retry trigger as newly actionable because it still
  exists in the registry
- Never treat every red compromise gate as release-blocking
- Never force eval work to the top when a larger uncovered `climb` gap is the real bottleneck

## Troubleshooting

- **Registry has no useful scores**
  - Result: triage becomes speculation
  - Fix: recommend a fresh benchmark rerun before ranking candidates

- **Worktree is dirty**
  - Result: score staleness may be hard to interpret
  - Fix: call it out explicitly and downgrade confidence in staleness judgments

- **Compromise checker output conflicts with intuition**
  - Result: likely a mismatch between registry freshness and current code
  - Fix: prefer "rerun benchmark first" over forcing a ranking

- **The only obvious follow-up is a repeated retry trigger**
  - Result: triage starts looping the same eval plan
  - Fix: mark it as exhausted-until-new-trigger and keep it in deferrals until
    a materially new model, approach, golden fix, architecture change, or
    dependency actually appears

## Lessons Learned

- 2026-03-13 — Cheap diagnosis is different from expensive verification: use registry data and helper scripts to choose the next eval target before spending promptfoo time on a full rerun.
- 2026-03-20 — Eval triage is subordinate to the methodology spine. Staleness alone does not make an eval the highest-priority next action.
- 2026-04-04 — `retry_when` is a detector, not a standing todo. Once the same
  trigger has been checked and found unchanged, the item should stay exhausted
  until a materially new trigger appears.
- 2026-04-10 — "Still red" and "still important" are not enough. Eval triage
  should explain what changed since the last meaningful action or keep the line
  in deferrals/health flags.

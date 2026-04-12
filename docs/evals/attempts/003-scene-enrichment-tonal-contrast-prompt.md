# Eval Attempt 003 — Scene Enrichment: Tonal Contrast Prompt Reinforcement

**Status:** Succeeded
**Eval:** scene-enrichment
**Date:** 2026-04-12
**Worker Model:** GPT-5.4
**Subject Model(s):** Sonnet 4.6

## Mission

Recover the `scene-enrichment` score regression on the default `Sonnet 4.6` path by improving prompt grounding around tonal contradiction, raising the score from `0.913` back to or above the `0.93` target without breaking latency or cost targets.

## Prior Attempts

First attempt on this eval.

## Plan

1. Confirm the exact mismatch in the latest eval artifact and compare it against the last passing Sonnet 4.6 run.
2. Tighten both the benchmark prompt and runtime scene-analysis prompt so soundtrack and tonal juxtaposition are treated as explicit evidence instead of optional nuance.
3. Add a narrow regression test for the runtime prompt contract.
4. Re-run the bounded `Sonnet 4.6` eval with `--no-cache`, then run it again to verify the improvement holds.
5. Record the measurements and update the registry.

## Work Log

- 2026-04-12 15:31 UTC: Reviewed the current registry entry, benchmark prompt, scorer, and exported result. Classified the elevator miss as `model-wrong` on prompt adherence, not `golden-wrong` or `ambiguous`, because the excerpt explicitly includes UB40 muzak and the prior passing Sonnet 4.6 output captured it.
- 2026-04-12 15:39 UTC: Reinforced tonal-contrast instructions in both the benchmark prompt and `scene_analysis_v1` runtime prompt, plus a regression test for the runtime prompt contract.
- 2026-04-12 15:41 UTC: Ran local guardrails before spending more eval budget. `pnpm --dir ui run lint` passed cleanly after restoring `ui/node_modules`; `cd ui && npx tsc -b` passed; `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_scene_analysis_execution.py -q` passed; `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` passed.
- 2026-04-12 15:32-15:34 UTC: First prompt revision reruns:
  - `benchmarks/results/scene-enrichment-attempt-003-run1.json` -> overall `0.899`, latency `11282 ms`, cost `$0.0107`.
  - `benchmarks/results/scene-enrichment-attempt-003-run2.json` -> overall `0.921`, latency `10922 ms`, cost `$0.0102`.
  These runs fixed the elevator regression but left the flashback scene inconsistent: the model sometimes implied `PAST` via the heading without explicitly describing the scene as a formative flashback or memory. Classified as `model-wrong` under an under-specified prompt contract.
- 2026-04-12 15:35 UTC: Added an explicit prompt instruction for flashback/memory framing in both the benchmark and runtime prompts, and extended the prompt-contract unit test to cover that requirement.
- 2026-04-12 15:34-15:36 UTC: Verified the stronger prompt with two more no-cache bounded reruns:
  - `benchmarks/results/scene-enrichment-attempt-003-run3.json` -> overall `0.965`, latency `14131 ms`, cost `$0.0133`.
  - `benchmarks/results/scene-enrichment-attempt-003-run4.json` -> overall `0.959`, latency `12659 ms`, cost `$0.0124`.
  Both runs cleared the `0.93` target and stayed under the latency (`15000 ms`) and cost (`$0.05`) ceilings.

## Conclusion

**Result:** succeeded
**Score before:** 0.913
**Score after:** 0.959
**Latency before:** 11146ms per call
**Latency after:** 12659ms per call
**Cost before:** $0.0109 per call
**Cost after:** $0.0124 per call

**What worked:** Explicitly naming the missing inference categories in the prompt contract worked. The first prompt pass restored the elevator scene by forcing soundtrack-backed tonal contradiction into the output; the second pass stabilized the flashback scene by forcing explicit memory/formative-context language instead of leaving that implication buried in the heading.

**What failed:** Fixing only the tonal-contrast wording was not enough. Two no-cache reruns still left the flashback scene below target because the model sometimes treated `PAST` as metadata rather than a narrative framing cue.

**What NOT to retry:** Do not spend time changing the golden or scorer for this regression. The failing evidence was in the excerpt and in the prior passing Sonnet 4.6 output, so this was not an eval-definition problem.

**Retry state:** retired

**Retry when:**
No immediate retry needed. Reopen only if a later prompt or module change causes the default Sonnet 4.6 path to fall back below target.

---

## Definition of Done Checklist

- [x] Read all previous attempts for this eval before starting
- [x] Ran the eval with `--no-cache` to get clean measurements
- [x] Recorded score_before and score_after in this file
- [x] Updated `docs/evals/registry.yaml` — scores section with new measurements
- [x] Updated `docs/evals/registry.yaml` — attempts section with summary entry
- [x] If approach succeeded: verified improvement holds across multiple runs
- [x] If follow-on work remains: set `retry_state` and `retry_when` honestly
- [x] Did NOT silently accept score regressions
- [x] Recorded latency_ms and cost_usd before/after in this file
- [x] Updated registry.yaml scores with latency_ms and cost_usd (run: python scripts/extract-eval-metrics.py --result-file <path>)
- [x] If optimizing for speed/cost: verified quality didn't regress below target

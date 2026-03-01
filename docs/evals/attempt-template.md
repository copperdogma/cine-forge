# Eval Attempt {ID} — {Eval Name}: {Short Title}

**Status:** In Progress | Succeeded | Failed | Inconclusive
**Eval:** {eval-id from registry.yaml}
**Date:** {YYYY-MM-DD}
**Worker Model:** {AI doing the improvement work, e.g. "Opus 4.6"}
**Subject Model(s):** {Model(s) being evaluated/used in pipeline, e.g. "Sonnet 4.6, Haiku 4.5"}

## Mission

{One paragraph: what are we trying to improve, from what score to what target, and why this eval was chosen.}

## Prior Attempts

{Summary of past attempts on this eval — what was tried, what failed, what's off-limits.
Read ALL previous attempt files for this eval before writing this section.
If this is the first attempt, write "First attempt on this eval."}

## Plan

{Numbered steps for the improvement approach. Be specific.}

## Work Log

{Chronological log of what was tried and what happened. Include scores.}

- {timestamp or step}: {action taken} — {result, with score if applicable}

## Conclusion

**Result:** {succeeded | failed | inconclusive}
**Score before:** {0.XXX}
**Score after:** {0.XXX}
**Latency before:** {NNNNms per call}
**Latency after:** {NNNNms per call}
**Cost before:** {$X.XXX per call}
**Cost after:** {$X.XXX per call}

**What worked:** {For successes — what specifically made the difference.}

**What failed:** {For failures — what approaches didn't work and why.}

**What NOT to retry:** {Approaches that made things worse or are definitively dead ends.}

**Retry when:**
{Structured conditions under which this should be retried. Use registry condition codes:
new-worker-model, new-subject-model, cheaper-subject-model, new-approach,
golden-fix, architecture-change, dependency-available}

---

## Definition of Done Checklist

- [ ] Read all previous attempts for this eval before starting
- [ ] Ran the eval with `--no-cache` to get clean measurements
- [ ] Recorded score_before and score_after in this file
- [ ] Updated `docs/evals/registry.yaml` — scores section with new measurements
- [ ] Updated `docs/evals/registry.yaml` — attempts section with summary entry
- [ ] If approach succeeded: verified improvement holds across multiple runs
- [ ] If approach failed: classified the failure and set retry_when conditions
- [ ] Did NOT silently accept score regressions
- [ ] Recorded latency_ms and cost_usd before/after in this file
- [ ] Updated registry.yaml scores with latency_ms and cost_usd (run: python scripts/extract-eval-metrics.py --result-file <path>)
- [ ] If optimizing for speed/cost: verified quality didn't regress below target

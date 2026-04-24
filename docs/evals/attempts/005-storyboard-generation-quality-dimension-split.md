# Eval Attempt 005 — Storyboard Generation Quality: Dimension Split

**Status:** Succeeded
**Eval:** storyboard-generation-quality
**Date:** 2026-04-23
**Worker Model:** GPT-5
**Subject Model(s):** gpt-image-2

## Mission

Make the storyboard-generation eval explain *why* one candidate scores lower
instead of collapsing style consistency, identity continuity, story specificity,
reference fidelity, and text cleanliness into one opaque quality number. This
was needed after the template-grid experiment appeared worse overall despite
manual inspection showing better medium consistency and no photoreal drift.

## Prior Attempts

Attempt 004 proved the template-grid lane's cost/latency value but found the
aggregate quality score unstable and hard to interpret. The previous report made
it look like grid was simply "lower quality," even though the real concern was
probably story/reference specificity rather than visual medium consistency.

## Plan

1. Add a first-class `style_assessment` to the storyboard analysis prompt and
   schema.
2. Rename deterministic scorer dimensions into product-readable dimensions:
   story specificity, style consistency, identity consistency, reference
   fidelity, text cleanliness, prop discipline, and evidence.
3. Teach the report to recompute and average per-dimension scores from promptfoo
   outputs and render them as table columns.
4. Rerun promptfoo only, using existing default, square, and template-grid image
   outputs. Do not regenerate storyboard images.
5. Record the split metrics in the registry.

## Work Log

- 2026-04-23: Added `StoryboardStyleAssessment`, updated
  `StoryboardAnalysisWeights`, and changed scorer dimensions from
  `summary`/`identity`/`reference` to explicit product dimensions.
- 2026-04-23: Updated `benchmarks/prompts/storyboard-understanding.txt` and
  `benchmarks/tasks/storyboard-generation-quality.yaml` to request
  `style_assessment` and grade dimensions separately.
- 2026-04-23: Updated `storyboard_generation_quality_report.py` to emit
  `Story`, `Style`, `Identity`, `Reference`, and `Text` columns in the markdown
  decision report.
- 2026-04-23: Reran promptfoo with `--no-cache` against existing generated
  images for full-size, square, and template-grid `gpt-image-2` candidates.
  Result: full-size default `0.735`, square `0.7288`, template grid `0.6775`.
  All three scored `1.0` on style consistency. The grid loss is concentrated in
  story specificity (`0.5`) and identity consistency (`0.5`), while grid kept
  text cleanliness at `1.0`.

## Conclusion

**Result:** succeeded
**Score before:** 0.8562 aggregate v1 scorer, not directly comparable
**Score after:** 0.735 split v2 scorer for the default lane
**Latency before:** 672297ms mean total runtime for the default lane
**Latency after:** 672297ms mean total runtime for the default lane
**Cost before:** $0.447 mean total cost for the default lane
**Cost after:** $0.447 mean total cost for the default lane

**What worked:** Splitting the dimensions confirmed the user's read. The grid
lane is not worse because of photoreal/style drift; it scored `1.0` on style
consistency, just like the per-frame lanes. Its lower aggregate score comes from
weaker story specificity and identity consistency.

**What failed:** The split exposed that the default lane now lands just below
the 0.75 usefulness floor under the stricter v2 evaluator because it still has
imperfect text cleanliness and identity consistency in the current measured
packet. That is useful pressure, but it means this attempt changed eval
observability rather than fixing the generation lane itself.

**What NOT to retry:** Do not use a single aggregate quality score to answer
questions about visual consistency. Use the split dimensions for future
generation-lane decisions.

**Retry state:** retired

**Retry when:**
No retry needed for the dimension split itself. Future grid work should use this
split report as the baseline.

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
- [x] Updated registry.yaml scores with latency_ms and cost_usd
- [ ] If optimizing for speed/cost: verified quality didn't regress below target

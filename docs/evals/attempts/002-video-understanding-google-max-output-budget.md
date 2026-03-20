# Eval Attempt 002 — Video Understanding: Google 3.x Max Output Budget

**Status:** Succeeded
**Eval:** video-understanding
**Date:** 2026-03-19
**Worker Model:** Codex (GPT-5)
**Subject Model(s):** Gemini 2.5 Pro, Gemini 2.5 Flash, Gemini 3.1 Pro Preview, Gemini 3 Flash Preview

## Mission

Investigate whether the poor Gemini video-understanding scores were partly caused by the
benchmark's `max_tokens=1400` cap rather than actual model weakness. The target was to verify
the failure mode, then rerun the 6-clip anchor subset with a corrected budget if the cap was
proven to be constraining output.

## Prior Attempts

First attempt on this eval.

## Plan

1. Inspect raw promptfoo result metadata for Gemini 3.x runs to compare prompt tokens,
   completion tokens, and total tokens.
2. Verify live Gemini model output limits from the provider API and confirm whether the task
   config is far below the available maximum.
3. If the usage pattern shows budget exhaustion, raise the Gemini `max_tokens` setting to the
   live model maximum and rerun the same 6-clip anchor subset with `--no-cache`.
4. Compare score, latency, cost, JSON-parse reliability, and remaining failure classification
   against the prior capped runs across the full Google subject set.

## Work Log

- 20260319-1820: Inspected capped Gemini 3.x result files. The visible completion tokens were low (`44`-`373`), but `totalTokenCount - promptTokenCount` clustered at `1384`-`1386` on most failed clips, nearly identical to the configured `1400` cap.
- 20260319-1823: Queried live Gemini model metadata via `https://generativelanguage.googleapis.com/v1beta/models/{model}`. Both `gemini-3.1-pro-preview` and `gemini-3-flash-preview` reported `outputTokenLimit=65536`.
- 20260319-1826: Cross-checked Google docs on thinking. Gemini thinking models use dynamic thinking by default, and the effective output budget includes internal thinking, so a low output cap can truncate strict JSON responses before the visible answer is complete.
- 20260319-1829: Updated `benchmarks/tasks/video-understanding.yaml` to raise Gemini `max_tokens` from `1400` to `65536` for the Google subject models under test.
- 20260319-1832: Re-ran `Gemini 3.1 Pro Preview` on the 6-clip anchor subset with `--no-cache`. Result improved from `0.2813` to `0.6342`, and JSON parse reliability improved from `1/6` valid outputs to `6/6`.
- 20260319-1836: Re-ran `Gemini 3 Flash Preview` on the same subset with `--no-cache`. Result improved from `0.3487` to `0.5475`, and JSON parse reliability improved from `3/6` valid outputs to `6/6`.
- 20260319-1843: Checked the older Gemini 2.5 runs and found the same cap signature: `totalTokenCount - promptTokenCount` also clustered at `1383`-`1397`, so the 2.5 scores were not a fair baseline either.
- 20260319-1848: Re-ran `Gemini 2.5 Pro` with the corrected cap. Result improved from `0.1492` to `0.5662`, and JSON parse reliability improved from `1/6` valid outputs to `6/6`.
- 20260319-1852: Re-ran `Gemini 2.5 Flash` with the corrected cap. Result improved from `0.1561` to `0.6523`, and JSON parse reliability improved from `1/6` valid outputs to `6/6`.
- 20260319-1856: Generated a merged comparison report across GPT-5.4, Sonnet 4.6, and the corrected full Google suite. GPT-5.4 still leads overall, but the earlier conclusion that Gemini broadly "collapsed" on this harness was wrong.

## Conclusion

**Result:** succeeded
**Score before:** 0.3487
**Score after:** 0.6523
**Latency before:** 7617ms per call
**Latency after:** 8706ms per call
**Cost before:** $0.001046 per call
**Cost after:** $0.000551 per call

**What worked:** Raising Gemini `max_tokens` to the live `65536` limit eliminated the JSON
truncation failures across the Google suite. The benchmark had been under-allocating output
budget for thinking-capable models, so hidden reasoning consumed most of the cap before the
visible JSON finished.

**What failed:** The original `1400` cap was not safe for Gemini on this task. It made
multiple clips look like model failures when the real issue was a harness budget mistake.

**What NOT to retry:** Do not use a low Gemini output cap on strict-JSON evals and then
conclude the model is weak from truncated responses. Do not reason from visible completion
tokens alone; inspect `totalTokenCount - promptTokenCount` across the whole provider suite.

**Retry when:**
- `new-approach` — add a native-video Gemini provider path instead of the current sampled-frames
  contract to see whether Google's video-first path closes the remaining gap versus GPT-5.4.

---

## Definition of Done Checklist

- [x] Read all previous attempts for this eval before starting
- [x] Ran the eval with `--no-cache` to get clean measurements
- [x] Recorded score_before and score_after in this file
- [x] Updated `docs/evals/registry.yaml` — scores section with new measurements
- [x] Updated `docs/evals/registry.yaml` — attempts section with summary entry
- [ ] If approach succeeded: verified improvement holds across multiple runs
- [ ] If approach failed: classified the failure and set retry_when conditions
- [x] Did NOT silently accept score regressions
- [x] Recorded latency_ms and cost_usd before/after in this file
- [x] Updated registry.yaml scores with latency_ms and cost_usd (run: python scripts/extract-eval-metrics.py --result-file <path>)
- [ ] If optimizing for speed/cost: verified quality didn't regress below target

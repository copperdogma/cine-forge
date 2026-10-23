# Eval Attempt 024 — QA Pass: Gemini 3.7 Flash Known-Good Screen

**Status:** Failed — source-grounding quality gate
**Eval:** qa-pass
**Date:** 2026-08-13
**Worker Model:** Codex (GPT-5.6)
**Subject Model(s):** Gemini 3.7 Flash (`gemini-3.7-flash`) direct through Google

## Mission

Test whether Gemini 3.7 Flash repairs Gemini 3.6 Flash's exact source-backed known-good QA failure before allowing any broader CineForge lane. The maintained full QA target is `1.0`, with latency at most `10,000 ms` and cost at most `$0.02` per subject call. This progressive first step runs only the known-good case; failure stops the six-case ordered-frame and script-bible follow-ons.

## Prior Attempts

Attempt 010 proved the old good fixture was source-wrong. Attempt 018 repaired the source fixture, deterministic accounting, and judge budget, then established clean decision-grade rejection evidence: Gemini 3.6 Flash scored `0.74995` across two cases and passed neither; Gemini 3.5 Flash-Lite scored `0.8484` and passed one. The differentiating Gemini 3.6 failure was a generic positive-case judgment that omitted the AirTag, armed-thug, and oar/gunfire source anchors. Those clean contracts were frozen here.

## Plan

1. Add the exact `gemini-3.7-flash` Google subject with low thinking, Google's supported structured-output schema subset, and current introductory pricing.
2. Run only the repaired known-good case with no cache and concurrency one through the repo provider-env wrapper.
3. Allow one transport-contract retry, but no semantic retry or prompt/scorer/golden change.
4. Inspect requested/served identity, terminal state, schema, raw usage, deterministic and Opus rubric components, source text, latency, and cost.
5. Stop Gemini's ladder on any quality, latency, cost, transport, or reliability failure.

## Work Log

- Initial transport attempt: Google rejected `additionalProperties` in its supported `responseSchema` subset before returning a candidate. This is adapter/contract failure, not model evidence. Retained as `benchmarks/results/qa-pass-gemini37flash-known-good-2026-08-13.json`.
- Single contract retry: removed only the unsupported schema keyword while preserving all required typed fields, frozen prompt, scorer, golden, and Opus rubric. Google returned exact `gemini-3.7-flash`, terminal `STOP`, valid required-shape JSON, 2,235 input tokens, 60 visible output tokens, and 155 thinking tokens.
- Result: deterministic `0.5999`, Opus rubric `0.82`, aggregate `0.70995`, subject latency `1,358 ms`, estimated subject cost `$0.0024825`. The verdict itself was correct (`passed=true`, no issues), but the summary generically claimed accuracy without naming any maintained source facts; the deterministic source-grounding hard gate failed.
- Classification: **model-wrong, runtime-blocking if used as the QA default**. The source-clean fixture and scorer encode the same differentiating requirement that rejected Gemini 3.6. The Opus judge was more lenient, but the independent deterministic gate prevented a false pass.
- Progressive stop: the six-case ordered-frame lane and optional script-bible comparison were **not measured**. This is not evidence about Gemini 3.7's visual capability.

## Conclusion

**Result:** failed
**Score before:** `0.74995` Gemini 3.6 full two-case reference; not directly comparable to this one-case progressive screen
**Score after:** `0.70995` on the Gemini 3.7 known-good case
**Latency before:** `6,516 ms/call` Gemini 3.6 full-run mean
**Latency after:** `1,358 ms` subject call
**Cost before:** `$0.012589/call` Gemini 3.6 estimated full-run mean
**Cost after:** `$0.0024825` estimated subject call

**What worked:** Exact model identity, terminal completion, typed schema, usage, latency, and both scoring components were retained. Gemini was fast and within the cost gate.

**What failed:** The answer repeated a generic QA conclusion rather than grounding its positive verdict in the source. It therefore failed the maintained quality gate despite a correct boolean verdict.

**What NOT to retry:** Do not rerun the same prompt/case, weaken source-anchor requirements, or infer visual/script-bible quality from this stopped ladder.

**Retry state:** exhausted-until-new-trigger

**Retry when:**

- `new-subject-model`: a materially newer Gemini model replaces 3.7 for this lane.
- `new-approach`: a production-approved prompt or QA contract changes the source-grounding requirement and is independently validated.

---

## Definition of Done Checklist

- [x] Read all previous attempts for this eval before starting
- [x] Ran the eval with `--no-cache`
- [x] Recorded score, latency, and cost
- [x] Updated registry score and attempt history
- [x] Classified the mismatch against source evidence
- [x] Stopped the progressive ladder without changing defaults

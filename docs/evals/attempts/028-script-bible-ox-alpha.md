# Eval Attempt 028 — Script Bible: Ox Alpha Bounded Runtime Evaluation

**Status:** Deferred — no fail-closed ZDR route
**Eval:** script-bible
**Date:** 2026-08-22
**Worker Model:** Codex (GPT-5.6)
**Subject Model(s):** Ox Alpha (`stealth/ox-alpha`) via OpenRouter/Stealth

## Mission

Qualify exact no-fallback OpenRouter access, fail-closed route privacy, and
provider-enforced strict `ScriptBible` output, then measure one frozen
low-reasoning Open Frequency arm only if transport qualifies. No default change
is authorized.

## Prior Attempts

Attempts 020–027 establish the bounded exact-runtime ladder. Opus 5 and Qwen3.8
missed latency/cost; DeepSeek routes failed full-script reliability/value;
Grok 4.6 passed quality/latency but missed cost; GLM-5.3 stopped before
invocation on access and strict-schema blockers. Do not reuse historical
one-corpus rows, weaken schema/privacy, tune scorer/golden, or expand after a
hard gate failure.

## Plan

1. Preserve Story 215's decision contract and US$0.75 aggregate ledger.
2. Reuse the benchmark-only generic OpenRouter seam for exact Ox Alpha/Stealth.
3. Run a tiny native request with strict `ScriptBible`, pinned provider,
   fallbacks disabled, required parameters, denied data collection, and ZDR.
4. Advance to exact-runtime parity and one no-cache Open Frequency case only if
   identity, privacy, strict schema, terminal output, and usage all qualify.
5. Inspect and classify every executed or blocked stage, then record immutable
   sanitized evidence without changing production code or defaults.

## Predeclared Matrix and Gates

- Candidate: `stealth/ox-alpha`, provider `Stealth`, low reasoning, strict
  schema, 65,536 maximum output tokens, sampling omitted.
- First and only fixture if qualified: repo-authored synthetic Open Frequency.
- Quality: overall `>=0.90`; deterministic `>=0.70` plus every hard assertion;
  frozen cross-provider Opus rubric `>=0.80`; every assertion passes.
- Operations: latency `<=30,000 ms`; subject cost `<=$0.01`; exact identity;
  terminal complete output; raw reconciled usage/cost; no fallback;
  provider-enforced strict `ScriptBible` JSON.
- Privacy: `data_collection=deny`, `zdr=true`, and
  `require_parameters=true`; fail closed if no route remains.
- Execution: no cache, concurrency one, one transient retry, one documented
  request-variable repair, and no semantic retry after a valid response.
- Spend: `$0` before calls; US$0.75 aggregate hard cap.

## Work Log

- 20260822-0000: owner discovery and focused zero-cost harness preflight passed;
  exact current worktree/base, model, route, schema, privacy, spend, and stop
  rules were frozen before provider invocation. Spend `$0`.
- 20260822-1500: current public endpoint metadata returned the single exact
  Stealth route, 1,048,576 context, 131,072 maximum completion tokens, zero
  list price, `response_format` support, and unknown `data_policy`. The combined
  strict `ScriptBible` plus fail-closed privacy request returned HTTP 404 before
  invocation: no endpoint could handle the requested parameters.
- 20260822-1501: the one allowed one-variable diagnostic removed only
  `response_format`; it retained the exact model/provider pin, no fallback,
  required parameters, denied collection, ZDR, low reasoning, and synthetic
  input. OpenRouter again returned HTTP 404 before invocation, now explicitly
  because no endpoint matched the Zero Data Retention policy. No parity,
  screenplay, scorer, judge, incumbent, or second-corpus call ran. Spend `$0`.

## Mismatch Classification

- **Access/provider route, pre-response:** the account credential was accepted
  far enough for policy routing, but the exact model has no endpoint eligible
  under mandatory ZDR. This is not a model-quality failure.
- **Transport:** strict JSON Schema remains unqualified because the mandatory
  privacy gate removed every endpoint first. Public `response_format` metadata
  is not provider-enforced strict-schema proof.
- **Capability:** not measured. No model output, scorer result, rubric result,
  or source mismatch exists.

## Conclusion

**Result:** deferred — mandatory ZDR route unavailable

**Score before/after:** N/A; no semantic invocation

**Latency:** `257 ms` combined route rejection; `155 ms` privacy-isolation
rejection. Neither is model latency.

**Cost:** `$0` of the US$0.75 cap; zero model and judge invocations.

**Access:** constrained by route policy. **Transport:** blocked before strict
schema qualification. **Reliability/capability:** not measured. **Economics:**
zero list price is known, but full-lane cost is not measured. **Adoption:**
defer; keep provisional `gemini-3.5-flash-lite` unchanged.

**What NOT to retry:** do not disable ZDR/data-collection denial, accept an
unpinned/fallback route, infer strict schema from catalog metadata, or send a
full screenplay while the fail-closed privacy route is ineligible.

**Retry state:** exhausted-until-new-trigger

**Retry when:** OpenRouter endpoint metadata or a live fail-closed probe proves
that exact `stealth/ox-alpha` has a ZDR route which also supports required
strict JSON Schema. An explicit new payload/privacy approval could redefine the
route, but is outside this evaluation.

## Definition of Done Checklist

- [x] Read all previous exact-runtime script-bible attempts before starting
- [x] Ran an eval with `--no-cache`, or recorded the pre-scoring blocker
- [x] Recorded score/latency/cost or explicit not-measured values
- [x] Updated registry attempt history
- [x] Classified all significant mismatches or blockers
- [x] Set retry state and retry conditions honestly
- [x] Did not weaken the contract or silently accept a failure

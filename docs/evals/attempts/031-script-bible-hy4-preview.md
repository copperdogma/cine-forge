# Eval Attempt 031 — Script Bible: Hy4 Preview Bounded Runtime Evaluation

**Status:** Inconclusive — upstream shared-pool capacity stop
**Eval:** script-bible
**Date:** 2026-08-29
**Worker Model:** Codex (GPT-5.6)
**Subject Model:** Hy4 preview (`tencent/hy4-preview`) via OpenRouter

## Mission

Qualify exact OpenRouter access and provider-enforced strict `ScriptBible`
output, then measure one frozen low-reasoning Open Frequency arm only if the
production transport contract qualifies. No default change is authorized.

## Prior Attempts

Attempts 020–030 establish the bounded exact-runtime ladder. Valid outputs from
Opus 5 and Qwen3.8 missed latency/cost; DeepSeek routes failed operational
gates; Grok 4.6 passed quality/latency but narrowly missed cost; GLM-5.3 stopped
before invocation; Ox Alpha never produced a strict valid artifact. Do not
weaken schema, tune scoring truth, or expand after an absolute gate failure.

## Frozen Decision Contract

- Exact requested/served `tencent/hy4-preview`; no model-list fallback; record
  the resolved same-model provider without pinning it.
- Production `script_bible_v1.EXTRACTION_PROMPT`, strict `ScriptBible` schema,
  Open Frequency screenplay/golden, deterministic scorer, and Opus 4.6 rubric.
- Low reasoning, hidden reasoning, omitted sampling, route-capped 64,000 output
  tokens, no cache, concurrency one, and US$0.75 aggregate ceiling.
- Require provider-enforced strict schema and `require_parameters=true`.
- Require overall `>=0.90`, deterministic `>=0.70` plus every hard assertion,
  rubric `>=0.80`, latency `<=30s`, and subject cost `<=US$0.01`.
- Open Frequency is repo-authored synthetic and approved even if the route may
  retain or train on it. No private or second corpus is eligible.
- Stop before semantic scoring on access/identity/terminal/schema/usage/parity
  failure; stop after Open Frequency on any absolute failure. No comparator.

## Plan

1. Add and test the narrow benchmark-only OpenRouter model metadata/config.
2. Resolve the exact one-cell harness matrix without provider spend.
3. Run one tiny direct strict `ScriptBible` probe.
4. If qualified, run the full Open Frequency cell with no cache and `-j 1`.
5. Inspect the artifact, classify mismatches, record the ledger and verdict.

## Work Log

- 20260829-2020: predeclared the exact candidate, frozen runtime contract,
  synthetic-only privacy boundary, gates, stop rule, no-cache/concurrency policy,
  and US$0.75 aggregate cap. Spend is `$0`.
- 20260829-2023: focused provider tests and the zero-cost resolved-matrix
  preflight passed. The matrix is one exact `tencent/hy4-preview` subject, one
  Open Frequency case, production prompt/schema, frozen Opus 4.6 judge, no
  cache, and concurrency one. Contract hashes are retained in the evidence file.
- 20260829-2025: the tiny strict `ScriptBible` probe reached OpenRouter's sole
  Tencent route but returned pre-invocation HTTP 429, provider code `429001`,
  `limit_source=upstream_provider_shared_pool`, and `Retry-After: 60`. No model
  output, usage, request identity, schema result, or charge existed.
- 20260829-2027: after the provider's 60-second availability window, the one
  predeclared identical transient retry returned the same upstream shared-pool
  429. Stopped before harness parity, Open Frequency, scorer, judge, incumbent,
  or another route. Total provider spend remained `$0`.

## Mismatch Classification

- **Provider capacity / pre-response:** both attempts failed before invocation
  with `limit_source=upstream_provider_shared_pool`. This is access/reliability
  evidence for the selected route, not a Hy4 semantic or schema failure.
- **Transport / capability:** unmeasured. No valid model response existed, so
  strict schema, scorer, rubric, source fidelity, latency, and subject economics
  cannot be classified.

## Conclusion

**Result:** inconclusive — exact route capacity unavailable

**Access:** constrained by the exact Tencent route's upstream shared pool.

**Transport:** not measured beyond routing; provider-enforced strict
`ScriptBible` output remains unverified.

**Reliability:** failed to produce a response across the original probe and one
provider-directed retry.

**Capability:** not measured; no answer reached either scorer.

**Economics:** `$0` of the US$0.75 cap; no model or judge invocation.

**Adoption:** defer. Keep provisional `gemini-3.5-flash-lite`; no defaults or
production transports changed.

**What NOT to retry:** do not repeatedly poll the unchanged shared pool, switch
models, add a provider account integration, run the full screenplay, or infer
strict-schema compatibility from catalog metadata.

**Retry state:** open only after material provider availability changes.

**Retry when:** OpenRouter's exact Tencent route can accept the same tiny strict
probe. Resume at the failed transport gate without rediscovery or broader scope.

## Definition of Done Checklist

- [x] Read all previous exact-runtime script-bible attempts before starting
- [x] Ran an eval with `--no-cache`, or recorded the pre-scoring blocker
- [x] Recorded score/latency/cost or explicit not-measured values
- [x] Updated registry attempt history
- [x] Classified all significant mismatches or blockers
- [x] Set retry state and retry conditions honestly
- [x] Did not weaken the contract or silently accept a failure

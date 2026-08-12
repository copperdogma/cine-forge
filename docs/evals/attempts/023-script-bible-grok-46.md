# Eval Attempt 023 — Script Bible: Grok 4.6 Bounded Runtime Evaluation

**Status:** Failed — bounded subject-cost rejection
**Eval:** script-bible
**Date:** 2026-08-12
**Worker Model:** Codex (GPT-5.6)
**Subject Model(s):** xAI Grok 4.6 (`grok-4.6`); Gemini 3.5 Flash-Lite comparator gated on candidate success

## Mission

Qualify exact direct xAI Grok 4.6 and measure one frozen low-reasoning arm on
the repaired exact-runtime Open Frequency script-bible boundary. Advance to the
second corpus and fresh executable incumbent only if Grok clears overall
quality `>=0.90`, latency `<=30,000 ms`, subject cost `<=$0.01`, reliability,
privacy, safety, identity, usage, and strict-schema gates. No production default
change is authorized.

## Prior Attempts

Attempt 020 qualified Opus 5 after a narrow schema repair but stopped when one
valid full-script response missed latency and cost. Attempt 021 qualified Qwen
3.8 via pinned OpenRouter but stopped after the same value failures. Attempt 022
repaired three source-proven scorer defects, then found DeepSeek V4 Flash's tiny
probe extremely slow and its full-script route unable to return a terminal
response; the fresh Gemini Open Frequency comparator failed the structural hard
gate. Do not reuse historical one-corpus Grok 4.5/Gemini scores as current
truth, weaken the semantic contract, tune the golden/scorer, or expand after an
absolute gate failure.

## Plan

1. Preserve the Story 212 decision contract and `$5` aggregate ledger.
2. Verify exact live catalog authorization, then run one tiny native Responses
   strict-schema call at low reasoning with unsupported sampling omitted.
3. Require exact served identity, terminal completion, reconciled usage, current
   pricing, and live `x-zero-data-retention` evidence; treat `store:false` as
   storage control rather than ZDR proof.
4. Add the smallest benchmark-only parity lane and focused request/response tests.
5. Run one complete synthetic Open Frequency case at `--no-cache -j 1`, inspect
   source/output/scorer/rubric/latency/cost/reliability, and apply the stop rule.
6. Record every executed call, attempt outcome, registry evidence, contract
   provenance, story log, and methodology surfaces without changing defaults.

## Predeclared Matrix and Gates

- Candidate: direct xAI `grok-4.6`, low reasoning, provider-enforced strict
  `ScriptBible`, no temperature/top-p/seed/stop/penalties.
- First fixture: complete repo-authored synthetic Open Frequency screenplay.
- Comparator/second fixture: fresh Gemini 3.5 Flash-Lite and The Mariner only
  after Grok clears every first-case gate and live ZDR makes the latter eligible.
- Scoring: maintained Python scorer plus frozen cross-provider Opus 4.6 rubric;
  every assertion must pass and the aggregate must be at least `0.90`.
- Execution: no cache, concurrency one, at most one transport/capacity retry,
  no semantic retry after a valid completion.
- Spend: `$0` before probes; `$5` aggregate hard cap.

## Work Log

- 20260812-2230: live discovery returned exact new catalog slug `grok-4.6` with
  repo-scoped xAI credentials available. Official xAI docs establish 500k
  context, strict JSON Schema, low/medium/high/xhigh reasoning, `$2/M` input and
  `$6/M` output below 200k input, default 30-day retention, optional team ZDR,
  and Responses storage enabled unless `store:false`. A separate output-token
  ceiling is not documented. No paid calls yet; ledger remains `$0`.
- 20260812-2233: native Responses access probe completed in `2,171 ms` with
  exact requested/returned `grok-4.6`, strict `API_OK` JSON, low reasoning,
  `store=false`, `275` input / `101` billed output tokens including `93`
  reasoning tokens, and provider-reported `$0.000964`. Live
  `x-zero-data-retention` was `false`, so the privacy boundary stayed
  synthetic-only.
- 20260812-2234: the exact production prompt and `ScriptBible` schema qualified
  on a tiny synthetic screenplay in `12,444 ms`, with `1,530` input / `458`
  billed output tokens including `153` reasoning tokens and `$0.005616`. Added
  the benchmark-only direct Responses lane, cached-token pricing, exact usage
  normalization, and focused tests without changing production transport.
- 20260812-2235: final no-cache Open Frequency result retained at
  `script-bible-grok46-open-frequency-2026-08-12.json`; its accounting-repaired
  derivative changes only Promptfoo's normalized visible/reasoning counters and
  is retained alongside the original. Exact subject evidence: completed strict
  JSON, `2,330` input / `1,180` billed output tokens including `27` reasoning,
  `23,699 ms`, and `$0.011548`. All assertions passed: deterministic `0.9333`,
  cross-provider Opus rubric `0.92`, overall `0.92665`.
- 20260812-2238: applied the progressive stop because subject cost exceeded
  `$0.01` by `$0.001548` (`15.48%`). No incumbent, second corpus, diagnostic
  configuration, retry, or other slot ran. Maintained judge usage was `2,969`
  input / `1,200` output tokens, approximately `$0.134535`. Total known spend:
  `$0.152663` across both probes, one subject, and one judge, below the `$5` cap.

## Mismatch Classification

- **Model-wrong / non-runtime-blocking nuance:** the synopsis calls the portable
  antenna “battered,” while the source applies “battered” to Noah's mixer. The
  semantic judge independently identified this as trivial; it does not overturn
  the clean assertion pass.
- **Model-correct on maintained hard contracts:** exact schema, source events,
  ending, act partition, evidence, exclusions, genre/tone, and required fields
  all passed. The deterministic conflict/journey keyword subscores of `0.50`
  and logline score `0.67` did not conceal a hard-gate failure.
- **Harness-wrong, repaired without a subject rerun:** xAI Responses reports
  `output_tokens` inclusive of reasoning, while the extractor assumed xAI Chat
  Completions semantics. The repair derives visible output from provider-owned
  counters and accounts for cached input at xAI's documented rate. The frozen
  subject output, scores, raw usage, latency, and reported cost are unchanged.
- **Runtime-blocking for adoption:** `$0.011548` exceeds the exact slot's hard
  `$0.01` per-subject gate. One successful observation makes conditional
  reliability acceptable but not broad evidence. Live ZDR false separately
  prevents sending the non-synthetic second corpus under this invocation.

## Conclusion

**Result:** failed — do not adopt for script bible at current price
**Score before:** N/A — no repaired Grok 4.6 evidence
**Score after:** 0.92665 (`0.9333` deterministic, `0.92` rubric)
**Latency before:** N/A
**Latency after:** 23,699ms per subject call
**Cost before:** N/A
**Cost after:** $0.011548 per subject call

**What worked:** Exact direct identity, native Responses, provider-enforced
strict `ScriptBible`, terminal completion, low reasoning, `store=false`, raw
usage/cost, structural quality, semantic quality, and latency all qualified.

**What failed:** The candidate missed the hard cost gate by 15.5%. Live team ZDR
was also false, so The Mariner remained ineligible and unmeasured.

**What NOT to retry:** Do not rerun the unchanged low-reasoning Open Frequency
arm, increase reasoning, send The Mariner without privacy approval, or weaken
the scorer/golden/rubric to rescue a measured cost failure.

**Retry state:** exhausted-until-new-trigger

**Retry when:** xAI pricing or a documented exact-model mode makes the frozen
call plausibly clear `$0.01`; separately, a live true ZDR header or explicit
payload approval is required before broader private-corpus evidence.

---

## Definition of Done Checklist

- [x] Read all previous attempts for this eval before starting
- [x] Ran the eval with `--no-cache` to get clean measurements
- [x] Recorded score_before and score_after in this file
- [x] Updated `docs/evals/registry.yaml` — scores section with new measurements
- [x] Updated `docs/evals/registry.yaml` — attempts section with summary entry
- [ ] If approach succeeded: verified improvement holds across the frozen ladder
- [x] If follow-on work remains: set `retry_state` and `retry_when` honestly
- [x] Did NOT silently accept score regressions
- [x] Recorded latency_ms and cost_usd before/after in this file
- [x] Updated registry.yaml scores with latency_ms and cost_usd
- [x] If optimizing for speed/cost: verified quality did not regress below target

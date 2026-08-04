# Eval Attempt 022 — Script Bible: DeepSeek V4 Flash Repaired Comparison

**Status:** Failed — full-script transport/reliability gate
**Eval:** script-bible
**Date:** 2026-08-03
**Worker Model:** Codex (GPT-5.6)
**Subject Model(s):** DeepSeek V4 Flash
(`deepseek/deepseek-v4-flash-0731`) via one pinned OpenRouter ZDR endpoint;
Gemini 3.5 Flash-Lite fresh incumbent comparator

## Mission

Repair the three source-proven structural scorer defects recorded by Attempt
021, then run one fresh, full-screenplay `script_bible_v1` comparison between
the immutable DeepSeek V4 Flash 0731 snapshot and the executable Gemini 3.5
Flash-Lite default. The maintained target is overall quality at least `0.90`,
latency at most `30,000 ms`, and cost at most `$0.01` per subject call. No other
model slot, fixture corpus, production default, or transport is in scope.

## Prior Attempts

Attempt 020 qualified Opus 5 after a narrow schema-subset transport repair but
stopped when one exact-runtime full-script call missed latency by `2.17x` and
cost by `14.85x`. Attempt 021 qualified Qwen3.8 Max through pinned OpenRouter
routing but stopped after the complete synthetic Open Frequency call missed
latency and cost by just over `2x`. Both attempts found that the structural
scorer rejected schema-permitted descriptive act boundaries and under-read
source-faithful evidence; Attempt 021 also isolated a false positive spanning
`Kell` and `cell towers are dead`. Do not weaken real unsupported-ending,
death, theme, or act-grounding checks, tune the golden, reuse stale comparator
scores, or broaden this attempt into QA/video/scene/model-slot work.

## Plan

1. Add regression tests for the three known scorer defects and confirm they fail
   on the current scorer while existing negative controls remain green.
2. Repair only those scorer defects; freeze the production prompt, schema,
   Open Frequency source/golden, Opus 4.6 rubric, thresholds, and base SHA.
3. Generalize the existing benchmark-only OpenRouter strict-schema seam for
   immutable `deepseek/deepseek-v4-flash-0731`; pin one ZDR provider, disable
   fallbacks/data collection, require parameters, and retain exact identity,
   finish, usage, reasoning, provider, and cost evidence.
4. Qualify one tiny synthetic native/parity call, then run DeepSeek low
   reasoning and Gemini minimal thinking together on the complete synthetic
   Open Frequency screenplay with `--no-cache -j 1`.
5. Inspect structural details, rubric evidence, source text, latency, cost, and
   reliability; classify every mismatch and stop without a second fixture or
   another slot.
6. Record the exact result, registry score/history, truth ledger, Story 211
   work log, spend ledger, and contract hashes; regenerate methodology surfaces
   and run focused plus full validation.

## Predeclared Matrix and Gates

- **Candidate:** `deepseek/deepseek-v4-flash-0731`, canonical
  `deepseek/deepseek-v4-flash-20260731`, low reasoning, strict schema, 65,536
  maximum output tokens.
- **Comparator:** `gemini-3.5-flash-lite`, minimal thinking, strict schema,
  65,536 maximum output tokens.
- **Fixture:** complete repo-authored synthetic Open Frequency screenplay only.
- **Scoring:** repaired maintained Python scorer plus frozen Opus 4.6 rubric;
  report both separately before the aggregate.
- **Execution:** no cache, concurrency one, at most one transport/capacity retry,
  no semantic retry after a valid completion.
- **Hard gates:** overall `>=0.90`, latency `<=30,000 ms`, subject cost
  `<=$0.01`, exact identity, terminal strict schema, sane reconciled usage, no
  fallback, pinned ZDR route, and no policy/safety refusal.
- **Spend cap:** `$5` aggregate across probe, both subjects, retries, and judges.
- **Stop:** pre-response access/transport failure yields capability not measured;
  otherwise complete this two-arm comparison and stop. The one-case result can
  support a scoped default decision only if all gates and source inspection pass.

## Work Log

- 20260803-2127: reused and reopened Story 211 as the existing owner for the
  same exact-runtime decision surface. Live official DeepSeek documentation and
  OpenRouter catalog/endpoint data resolved the latest immutable snapshot,
  dual-mode low reasoning, 1M context, current pricing, strict structured-output
  routes, and ZDR choices. The repo has an OpenRouter credential but no native
  DeepSeek credential. The comparison, repair boundary, privacy boundary,
  matrix, `$5` spend cap, and stop rules above were frozen before paid calls.
- 20260803-2140: regression coverage reproduced and repaired all three
  source-proven Attempt 021 scorer defects. Frozen Qwen output now passes the
  current deterministic scorer at `0.9533`; paired with its retained `0.95`
  rubric, the diagnostic is `0.95165`. Its original `64,608 ms` / `$0.021418`
  value failures are unchanged. Existing unsupported-claim and exact-partition
  negative controls still fail.
- 20260803-2143: a tiny synthetic DeepSeek probe qualified exact requested and
  returned identity, Phala-only routing, strict `ScriptBible`, terminal stop,
  low reasoning, ZDR, denied data collection, reconciled usage, and `$0.001317`
  cost. Its `133,706 ms` latency already missed the lane's `30,000 ms` gate.
- 20260803-2146: the no-cache two-arm run produced one valid fresh Gemini cell
  but Promptfoo's independent Python-worker watchdog killed DeepSeek at
  `300,000 ms`, below the provider's predeclared 600-second ceiling. Gemini
  scored `0.78995` overall (`0.6999` deterministic fail, `0.88` rubric pass),
  took `4,128 ms`, and cost an estimated `$0.0028251`.
- 20260803-2151: the single predeclared transport retry raised only the worker
  watchdog and reran DeepSeek alone. The pinned route exhausted Promptfoo's
  rate-limit handling after `182,003 ms` without a response, usage, or charge.
  No semantic retry, alternate endpoint, fallback, second fixture, or other
  slot was run.

## Mismatch Classification

- **DeepSeek transport/provider-wrong, runtime-blocking for adoption:** the tiny
  strict probe succeeded, but the full-script call supplied no terminal output
  within five minutes and the one repaired retry ended in rate-limit
  exhaustion. Quality is unmeasured. Both observations independently fail the
  30-second latency/reliability requirements.
- **Harness-wrong, repaired before the allowed retry:** Promptfoo's Python
  worker defaulted to `300,000 ms` while the provider request ceiling was
  `600` seconds. The task now explicitly sets a `660,000 ms` worker ceiling.
  The retry then reached the provider outcome, so this defect does not explain
  the final rate-limit failure.
- **Gemini model-wrong, runtime-blocking for a clean current-contract pass:**
  acts two and three both claim the final morning scene, so the acts overlap
  instead of partitioning the four source headings. The output also reduces
  the tower plea to generic medical supplies and does not retain enough of the
  north-shelter/insulin/dry-blankets/signal event contract. The semantic judge
  still passed it at `0.88`; the deterministic hard gate correctly prevents
  that mean from becoming a pass.
- **Non-runtime-blocking nuance:** Gemini's rubric noted minor embellishments
  such as “formally rebrands” and “essential lifeline.” These are source-close
  interpretations, not the hard failure.

## Spend Ledger

- DeepSeek strict probe: `$0.001317` measured.
- Fresh Gemini subject: `$0.0028251` estimated from returned usage; maintained
  Opus 4.6 judge: approximately `$0.121305` from `2,587` prompt and `1,100`
  completion tokens at the maintained rates.
- Known total: approximately `$0.1254471`. The timed-out DeepSeek request did
  not return usage or cost; at the pinned endpoint's configured prices and
  65,536-token cap its conservative maximum is below `$0.027`. The retry
  returned only rate-limit errors. The aggregate therefore remained below the
  predeclared `$5` cap even under that conservative ceiling.

## Conclusion

**Result:** failed — DeepSeek full-script capability unmeasured; do not adopt
**Score before:** N/A — no repaired DeepSeek row or contemporaneous comparator
**Score after:** DeepSeek N/A; Gemini `0.78995` (`0.6999` deterministic,
`0.88` rubric)
**Latency before:** N/A
**Latency after:** DeepSeek `>300,000 ms` without a terminal first attempt and
`182,003 ms` retry error; Gemini `4,128 ms`
**Cost before:** N/A
**Cost after:** DeepSeek full-script unknown/unreconciled; Gemini `$0.0028251`

**What worked:** The scorer repair, frozen Qwen regrade, exact pinned DeepSeek
probe, strict schema/privacy/identity evidence, and fresh Gemini comparator all
produced replayable evidence.

**What failed:** DeepSeek never produced a full-script result, so it cannot be
scored or considered for adoption. The fresh Gemini comparator clears latency
and cost but fails the repaired structural quality gate.

**What NOT to retry:** Do not retry this exact Phala route immediately, switch
to a non-ZDR/fallback route, weaken the scorer, or expand to another corpus or
slot. Do not treat the tiny probe as full-script semantic evidence.

**Retry state:** exhausted-until-new-trigger

**Retry when:** the exact immutable snapshot has a stable ZDR endpoint that can
plausibly return this full-script strict-schema request under 30 seconds, or a
native DeepSeek credential is explicitly supplied and separately qualified.

---

## Definition of Done Checklist

- [x] Read all previous attempts for this eval before starting
- [x] Ran the eval with `--no-cache` to get clean measurements
- [x] Recorded score_before and score_after in this file
- [x] Updated `docs/evals/registry.yaml` — scores section with new measurements
- [x] Updated `docs/evals/registry.yaml` — attempts section with summary entry
- [ ] If approach succeeded: verified improvement holds across the frozen
  two-arm comparison
- [x] If follow-on work remains: set `retry_state` and `retry_when` honestly
- [x] Did NOT silently accept score regressions
- [x] Recorded latency_ms and cost_usd before/after in this file
- [x] Updated registry.yaml scores with latency_ms and cost_usd
- [x] If optimizing for speed/cost: verified quality did not regress below target

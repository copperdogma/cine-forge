# Eval Attempt 021 — Script Bible: Qwen3.8 via OpenRouter

**Status:** Failed — bounded value-gate rejection
**Eval:** script-bible
**Date:** 2026-08-03
**Worker Model:** Codex (GPT-5.6)
**Subject Model(s):** Qwen3.8 Max (`qwen/qwen3.8-max`) via OpenRouter/Alibaba; Gemini 3.5 Flash-Lite comparator gated on candidate success

## Mission

Qualify Qwen3.8's exact OpenRouter route and measure the frozen low-reasoning
arm on the repaired exact-runtime script-bible boundary. The maintained target
is overall quality at least `0.90`, latency at most `30,000 ms`, and cost at
most `$0.01` per call. No production default changes are authorized.

## Prior Attempts

Attempt 020 qualified Opus 5 on this eval, repaired a narrow provider-schema
defect, and stopped after one exact-runtime The Mariner call missed latency and
cost gates. Story 208 made all older one-corpus and runtime-mismatched rows
non-decision-grade. Do not reuse historical rows as current comparator truth,
change the golden/scorer to help Qwen, or advance a candidate that fails an
absolute gate.

## Plan

1. Verify authenticated OpenRouter access, exact served identity/provider,
   no-fallback routing, mandatory reasoning controls, strict JSON Schema,
   terminal completion, real usage, pricing, and privacy.
2. Add the smallest isolated exact-runtime provider branch proven by the native
   call, with focused unit coverage.
3. Run one no-cache Open Frequency case at concurrency one using frozen low
   reasoning and the production prompt/schema.
4. Inspect the synthetic screenplay, subject output, deterministic details,
   Opus rubric, latency, cost, and reliability; classify every mismatch.
5. Stop on any absolute gate failure. A one-case pass remains provisional and
   advances only to an explicitly privacy-eligible second corpus plus a fresh
   default comparator.

## Work Log

- 20260803-1255: predeclared the story decision contract, `$5` total cap,
  initial `$0.02` probe cap, synthetic-only privacy boundary, no-cache / `-j 1`
  execution, one retry maximum, and progressive stop before the first paid call.
- Live qualification found exact OpenRouter model `qwen/qwen3.8-max`, canonical
  snapshot `qwen/qwen3.8-max-20260803`, and one Alibaba endpoint. The endpoint
  is not on OpenRouter's ZDR list, so only repo-authored Open Frequency was
  eligible. A native no-fallback strict-schema probe returned the exact model,
  Alibaba provider, terminal stop, valid JSON, `54` prompt / `76` completion
  tokens including `54` reasoning tokens, and `$0.000564` cost.
- Added an isolated OpenRouter branch to the existing runtime-shaped provider:
  Alibaba pinned, fallbacks disabled, required-parameter routing, strict JSON
  Schema, low reasoning excluded from the visible response, exact identity,
  terminal completion, Pydantic validation, and raw usage/provider evidence.
  Focused provider and metric tests passed.
- Final no-cache Open Frequency result:
  `script-bible-qwen38-openrouter-open-frequency-2026-08-03.json`. Exact
  requested/returned model `qwen/qwen3.8-max`, provider Alibaba, terminal stop,
  strict schema valid, `1,349` prompt / `3,120` completion tokens including
  `798` reasoning tokens, `64,608 ms`, and `$0.021418` subject cost.
- Score: deterministic `0.6999` fail (raw `0.8065`); maintained Opus 4.6 rubric
  `0.95` pass; reported mean `0.82495` fail. The judge used `3,961` prompt /
  `909` completion tokens, approximately `$0.127590` at the maintained
  `$15/$75` rates. Total task spend was approximately `$0.149572`: `$0.000564`
  native + `$0.021418` subject + `$0.127590` judge, below the `$5` cap.
- Progressive stop: Qwen exceeded the `30s` latency gate by `2.15x` and the
  `$0.01` cost gate by `2.14x`. The Mariner, fresh Gemini comparator, and xhigh
  diagnostic were not run because none could rescue those absolute failures.

## Mismatch Classification

- **Scorer-contract mismatch / non-runtime-blocking for this rejection:** all
  three acts use source headings for starts and faithful source-beat
  descriptions for ends. The production `ActStructure` schema explicitly
  permits a scene heading *or description*, but the deterministic scorer
  requires exact headings for both and assigns `act_boundary_grounding=0`.
- **Scorer-wrong / non-runtime-blocking:** all 16 theme evidence items contain
  source-faithful quotations or beats followed by explanatory annotations.
  The lexical matcher compares the entire annotated item to one source line,
  so 15 are rejected and `theme_evidence_grounding=0.06`; the semantic judge
  independently verified the quotations and evidence.
- **Scorer-wrong / non-runtime-blocking:** the forbidden-death regex matches
  the harmless phrase span beginning with `Kell` and ending with `cell towers
  are dead`. No character death is asserted, so `unsupported_claims=0` is a
  false positive.
- **Model-wrong / non-runtime-blocking for the value rejection:** the output
  overstates the source in several places: “all communication infrastructure,”
  “catastrophic” isolation, a failed “power grid,” and a “small American town”
  are not explicitly established. These are minor grounding defects rather
  than contradictions, consistent with the rubric's `0.95` rather than a
  perfect score.
- **Runtime-blocking for adoption:** measured latency and cost independently
  fail the current value-slot gates on a valid exact-runtime call. The one-case
  reliability observation is acceptable but cannot overcome either failure.

## Conclusion

**Result:** failed
**Score before:** N/A
**Score after:** 0.82495 bounded one-case diagnostic
**Latency before:** N/A
**Latency after:** 64,608ms per subject call
**Cost before:** N/A
**Cost after:** $0.021418 per subject call

**What worked:** Exact OpenRouter/Alibaba routing, strict structured output,
terminal completion, production prompt/schema parity, raw usage/cost evidence,
and strong conditional semantic quality all qualified.

**What failed:** Qwen missed both absolute value gates by just over `2x`. The
maintained structural scorer also under-read the valid answer in three known
ways, so the aggregate is not a fine-grained capability rank.

**What NOT to retry:** Do not run the unchanged second corpus, comparator, or
xhigh arm at current price/latency. Do not tune the scorer or golden to rescue
Qwen's measured value failure.

**Retry state:** exhausted-until-new-trigger

**Retry when:** OpenRouter pricing or serving latency makes this exact call
plausibly clear `$0.01` and `30,000 ms`; independently regrade the frozen output
after a verified scorer repair without spending on a new subject call.

---

## Definition of Done Checklist

- [x] Read all previous attempts for this eval before starting
- [x] Ran the eval with `--no-cache` to get clean measurements
- [x] Recorded score_before and score_after in this file
- [x] Updated `docs/evals/registry.yaml` — scores section with new measurements
- [x] Updated `docs/evals/registry.yaml` — attempts section with summary entry
- [ ] If approach succeeded: verified improvement holds across multiple runs
- [x] If follow-on work remains: set `retry_state` and `retry_when` honestly
- [x] Did NOT silently accept score regressions
- [x] Recorded latency_ms and cost_usd before/after in this file
- [x] Updated registry.yaml scores with latency_ms and cost_usd
- [x] If optimizing for speed/cost: verified quality did not regress below target

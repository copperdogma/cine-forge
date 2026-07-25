# Eval Attempt 020 — Script Bible: Opus 5 Runtime Comparison

**Status:** Failed — bounded value-gate rejection
**Eval:** script-bible
**Date:** 2026-07-24
**Worker Model:** Codex (GPT-5.6)
**Subject Model(s):** Claude Opus 5; Gemini 3.5 Flash-Lite comparator predeclared but not run after progressive stop

## Mission

Test Anthropic `claude-opus-5` on the repaired exact-runtime script-bible
boundary and compare it with the executable Gemini 3.5 Flash-Lite default only
if it clears the first differentiating full-screenplay gate. The maintained
target is overall quality at least `0.90`, latency at most `30,000 ms`, and cost
at most `$0.01` per call.

## Prior Attempts

The registry lists no previous attempt for `script-bible`. Story 206 evaluated
Opus 4.8 on the older one-corpus benchmark-only prompt and found a quality pass
but a latency/cost miss. Story 208 repaired the corpus, source truth, scorer,
goldens, and exact-schema requirements, then marked all older rows ineligible
for an exact runtime decision.

## Plan

1. Qualify official identity, live catalog access, native served identity,
   strict structured output, usage, and pricing.
2. Add the smallest runtime-shaped provider seam using the production
   `EXTRACTION_PROMPT` and `ScriptBible` Pydantic schema.
3. Run one no-cache The Mariner parity case at concurrency one.
4. Advance to the second corpus and fresh default only if Opus 5 clears the
   absolute quality, latency, cost, reliability, privacy, and safety gates.
5. Inspect source and classify deterministic/rubric mismatches before deciding.

## Work Log

- Native probe: exact `claude-opus-5` request and returned identity, strict
  schema parse, `262` input / `21` output tokens, `3.154s`, `$0.001835`.
- Initial parity diagnostic:
  `script-bible-runtime-opus5-parity-2026-07-24.json` stopped before generation
  because Anthropic's grammar compiler rejects Pydantic `minimum` constraints.
  This was a transport/schema failure with no semantic evidence and no billed
  model output.
- Narrow repair: matched Anthropic's documented SDK behavior by stripping
  unsupported `minimum`, `maximum`, `minLength`, and `maxLength` keywords from
  the transmitted grammar, carrying them into field descriptions, and retaining
  original Pydantic validation after parsing. Focused tests passed.
- A v2 valid diagnostic proved the repaired schema path, then the final provider
  was isolated from shared production transport so this bounded eval could not
  invalidate Story 208's immutable contracts. Final parity result:
  `script-bible-runtime-opus5-parity-v3-2026-07-24.json`.
  Exact requested/returned `claude-opus-5`, request
  `msg_011CdMK3hgPmHuGeJndEaazW`, `9,515` input / `4,037` output tokens,
  `64,961 ms`, `$0.148500` subject cost, terminal stop, strict schema valid.
- Score: deterministic `0.6999` fail; maintained Opus 4.6 rubric `0.88` pass;
  reported mean `0.78995` fail. The same-provider judge used `8,669` input /
  `1,251` output tokens, approximately `$0.223860` at the registry's maintained
  Opus 4.6 `$15/$75` rates.
- Final-evidence spend ledger: `$0.001835` native + `$0.148500` subject +
  approximately `$0.223860` judge = `$0.374195`. Including the superseded v2
  subject/judge diagnostic brings actual task spend to approximately `$0.740985`,
  still below the `$5` cap.
- Progressive stop: Opus 5 exceeded the `30s` latency gate by `2.17x` and the
  `$0.01` cost gate by `14.85x`. The second corpus and fresh Gemini comparator
  were not run because neither could rescue Opus 5's absolute value failure.

## Mismatch Classification

- **Scorer-wrong / non-runtime-blocking for this rejection:** the deterministic
  reason says all required terminal and plot events are missing even though the
  output explicitly includes the AirTag, rescue, purse chip/password, flare gun,
  Salvatori gunpoint scene, confiscated oar/kneeling, Rose's hero speech,
  never-backs-down line, clenched fists, and unresolved cut to black.
- **Scorer-contract mismatch / non-runtime-blocking:** it requires exact source
  headings for act boundaries, while the production schema explicitly permits a
  scene heading *or description*. The runtime-shaped answer used descriptive
  boundaries.
- **Model-wrong / non-runtime-blocking for the value rejection:** the synopsis
  says Mariner is shot in the leg; the screenplay says a shot hits his back,
  although Rose then wraps his leg. An act turning point also says he kills
  Mikey and Carlos, while the source only says their heads crack together and
  they drop.
- **Ambiguous:** exact theme-evidence lexical grounding is under-credited by the
  deterministic matcher, while the same-provider Opus judge may be lenient.
  Conditional semantic quality is therefore promising but not decision-grade.
- **Runtime-blocking for adoption:** latency and cost independently fail hard
  current slot gates on a valid production-shaped call.

## Conclusion

**Result:** failed
**Score before:** N/A — no repaired exact-runtime row
**Score after:** 0.78995 bounded one-case diagnostic
**Latency before:** N/A
**Latency after:** 64,961ms per call
**Cost before:** N/A
**Cost after:** $0.148500 per subject call

**What worked:** Exact first-party identity, provider-enforced structured output,
full-script context, runtime prompt/schema parity, and replayable usage/cost all
qualified after one documented schema-subset repair in an isolated benchmark
provider.

**What failed:** Opus 5 missed both absolute value gates by large margins. The
maintained deterministic scorer also under-read a strong output, so the numeric
quality aggregate must not be used as a fine-grained model ranking.

**What NOT to retry:** Do not run the unchanged second-corpus/comparator matrix
at current pricing and latency; the first valid long-script call already makes
Opus 5 ineligible for the value-default slot. Do not tune the golden or scorer
to rescue this result.

**Retry state:** exhausted-until-new-trigger

**Retry when:**

- `cheaper-subject-model`: Anthropic pricing or a provider mode reduces this
  exact call below `$0.01` without weakening the contract.
- `faster-subject-model`: Opus 5 or its successor clears `30,000 ms` on the same
  full script.
- `golden-fix`: the maintained structural scorer is repaired and independently
  reverified, but only rerun Opus if the value gates also become plausible.

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
- [x] If optimizing for speed/cost: verified quality didn't regress below target

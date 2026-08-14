# Eval Attempt 025 — Script Bible: DeepSeek V4 Pro Bounded Runtime Screen

**Status:** Failed — latency/reliability gate before full-script scoring
**Eval:** script-bible
**Date:** 2026-08-13
**Worker Model:** Codex (GPT-5.6)
**Subject Model(s):** DeepSeek V4 Pro (`deepseek/deepseek-v4-pro`) through pinned OpenRouter routes

## Mission

Determine whether the GA DeepSeek V4 Pro alias repairs V4 Flash's full-script transport failure on the exact `script_bible_v1` prompt and strict `ScriptBible` schema. The decision fixture is the complete repo-authored synthetic Open Frequency screenplay. Hard gates are overall quality `>=0.90`, latency `<=30,000 ms`, subject cost `<=$0.01`, exact identity, terminal schema-valid completion, reliable usage, no fallback, and an explicitly pinned privacy posture.

## Prior Attempts

Attempts 020 and 021 stopped Opus 5 and Qwen3.8 on absolute latency/cost failures. Attempt 022 qualified DeepSeek V4 Flash 0731 through pinned Phala ZDR strict output, but its tiny probe took `133,706 ms`; the full screenplay exceeded five minutes and one bounded retry exhausted rate limits. Quality was unmeasured. Attempt 023 showed the exact progressive stop pattern again: Grok 4.6 passed quality/latency but exceeded the `$0.01` cost gate. Do not run a second corpus or incumbent after an absolute candidate failure.

## Plan

1. Reuse the exact runtime prompt/schema provider and add only the V4 Pro alias plus pinned route metadata.
2. Calibrate at most two public/synthetic provider/privacy arms: a strict Together/ZDR route and the Scout-qualified lower-priced Baidu/non-ZDR route with data collection denied.
3. Freeze the viable route before the full decision fixture. Require no fallback, supported parameters, exact identity, terminal strict schema, reconciled usage, and provider-reported cost.
4. Stop before the full screenplay if a tiny route probe already violates or makes an absolute lane gate non-credible.

## Work Log

- Together/ZDR probe: exact requested/returned `deepseek/deepseek-v4-pro`, pinned `Together`, no fallback, required parameters, data collection denied, `zdr=true`, terminal `stop`, strict `ScriptBible`, and reconciled raw usage all qualified. The tiny 464-input/985-completion-token call took `19,109 ms` and cost `$0.00423516`; 984 completion tokens were reported as reasoning. This consumed 42% of the full lane cost gate on a tiny source.
- Route freeze: because the full screenplay was implausible under `$0.01` on Together, froze Scout 044's lower-cost Baidu route for public/synthetic data only. The route is explicitly non-ZDR; fallbacks remained disabled and data collection denied.
- Baidu probe: the request remained open without a response beyond 60 seconds, already exceeding the `30,000 ms` hard gate by more than 2x on the tiny source. It was interrupted to prevent additional waste. No terminal response, usage, cost, or semantic output exists for this route.
- Progressive stop: the complete Open Frequency call, Opus judge, incumbent, second corpus, and all other slots were **not measured**. Capability remains unmeasured; end-to-end latency/reliability failed.
- Classification: operational provider/model-route failure, not a semantic model miss. The strict Together route is callable but economically implausible for the lane; the lower-cost Baidu route failed latency/reliability qualification.

## Conclusion

**Result:** failed
**Score before:** unmeasured for DeepSeek V4 Flash
**Score after:** unmeasured for DeepSeek V4 Pro
**Latency before:** `>=300,000 ms` full-script V4 Flash attempt
**Latency after:** `19,109 ms` Together tiny probe; `>60,000 ms` Baidu tiny probe without completion
**Cost before:** unmeasured for V4 Flash full script
**Cost after:** `$0.00423516` Together tiny probe; unknown Baidu interrupted probe

**What worked:** Together proved exact alias access, strict schema, pinned routing, ZDR, terminal completion, and provider-reported accounting.

**What failed:** No route qualified as both plausibly under the full-script value gates and reliably under 30 seconds. Therefore semantic quality could not be measured honestly.

**What NOT to retry:** Do not run the complete screenplay on these same route/configuration arms, treat the tiny synthetic output as quality evidence, or use private data on the non-ZDR route.

**Retry state:** exhausted-until-new-trigger

**Retry when:**

- `stable-fast-zdr-route`: an exact V4 Pro route supports strict schema and plausibly completes the full prompt under 30 seconds and `$0.01`.
- `native-deepseek-access`: an explicitly supplied direct DeepSeek credential permits a separately qualified low-cost call; do not infer permission or borrow credentials.
- `cheaper-subject-model`: documented OpenRouter pricing/routing changes make a strict privacy-compatible arm plausibly clear the full-script cost gate.

---

## Definition of Done Checklist

- [x] Read prior script-bible attempts before starting
- [x] Qualified exact identity/schema on a public synthetic probe
- [x] Recorded latency, cost, routing, and privacy evidence
- [x] Updated registry attempt history
- [x] Kept capability unmeasured after operational failure
- [x] Stopped without a full paid run or default change

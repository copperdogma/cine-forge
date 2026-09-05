# Eval Attempt 035 — Script Bible: GPT-6 Astra Bounded Runtime Evaluation

**Status:** Failed — bounded quality, latency, and subject-cost rejection
**Eval:** script-bible
**Date:** 2026-09-05
**Worker Model:** Codex (GPT-6 Astra)
**Subject Model(s):** OpenAI GPT-6 Astra (`gpt-6-astra`); Gemini 3.5 Flash-Lite comparator gated on candidate success

## Mission

Qualify exact direct OpenAI GPT-6 Astra and measure one frozen low-reasoning arm
on the repaired exact-runtime Open Frequency script-bible boundary. Advance to
medium, high, or the fresh incumbent only if the preceding arm clears overall
quality `>=0.90`, latency `<=30,000 ms`, subject cost `<=$0.01`, reliability,
identity, usage, and provider-enforced strict-schema gates. No default change.

## Prior Attempts

Attempts 020–034 show that access and transport failures are not semantic
misses, and that strong one-case quality does not rescue a hard cost or latency
miss. Attempt 023 is the closest direct-Responses precedent: Grok 4.6 passed
quality at `0.92665` and latency at 23,699 ms, but failed the $0.01 cost gate.
Story 216's current comparable Gemini 3.5 Flash-Lite evidence remains below the
quality gate. Do not weaken the semantic contract, tune the golden/scorer, or
expand after an absolute gate failure.

## Predeclared Matrix and Gates

- Candidate: direct OpenAI `gpt-6-astra`, low reasoning, provider-enforced
  strict ScriptBible, `store=false`, no sampling controls.
- First and only initially eligible fixture: repo-authored synthetic Open
  Frequency.
- Later arms: medium then high, and fresh Gemini 3.5 Flash-Lite, only after the
  immediately preceding Astra arm clears every gate. `xhigh`/`max` excluded.
- Scoring: maintained Python scorer plus frozen cross-provider Opus 4.6 rubric;
  every assertion passes and aggregate is at least `0.90`.
- Execution: no cache, concurrency one, at most one transient retry, no semantic
  retry after valid completion.
- Spend: `$0` before probes; `$0.60` aggregate hard cap.

## Plan

1. Test the benchmark-only direct Responses adapter without provider spend.
2. Run the smallest native strict-schema qualification and retain sanitized
   terminal identity/usage/cost evidence.
3. Inspect the resolved one-provider/one-case Promptfoo topology with no call.
4. If transport qualifies, run Astra low on Open Frequency with `--no-cache -j 1`.
5. Apply the progressive stop and record every executed call and unmeasured arm.

## Work Log

- 20260905-1002: frozen contract and ledger before paid calls. Exact model is
  catalog-visible using the owning repo's configured OpenAI credential. Official
  current pricing makes the low arm potentially expensive relative to the hard
  per-call gate, so the run remains single-case and progressive.
- 20260905-1004: a tiny native Responses probe completed in 15,766 ms with
  exact requested/returned `gpt-6-astra`, low reasoning, `store=false`, strict
  ScriptBible JSON, and reconciled usage (722 input, 741 output, zero reasoning
  tokens). Estimated cost was $0.04427.
- 20260905-1005: Promptfoo config validation and a filtered topology inspection
  resolved exactly one provider, one Open Frequency case, the runtime marker,
  Python scorer, Opus 4.6 rubric judge, no cache, and concurrency one.
- 20260905-1009: the no-cache Open Frequency call returned exact terminal strict
  JSON in 33,086 ms. Subject usage was 1,889 input and 1,762 output tokens with
  estimated cost $0.10699. The rubric passed at 0.95; deterministic raw quality
  was 0.9279, but its theme-evidence hard gate produced 0.6999 and the aggregate
  was 0.82495. Applied the progressive stop: no medium/high or comparator.
- 20260905-1012: source inspection found every disputed theme item materially
  faithful, including exact dialogue quotations. The scorer rejects several
  accurate paraphrased scene references because its grounding function requires
  near-verbatim token runs, while the frozen prompt explicitly permits precise
  references. Classified this as scorer-contract ambiguity, not a clean model
  error. It does not alter the adoption rejection because latency and subject
  cost independently fail absolute gates. Estimated aggregate spend, including
  the independent judge, is $0.290085 of the $0.60 cap.
- 20260905-1016: the metric extractor reported 33,086 ms and $0.10699. Its
  registry update mode correctly refused to promote the bounded one-case result
  as full two-corpus coverage (`missing=1`), so the result remains an explicit
  bounded-rejection row rather than current full-lane evidence. Validation
  passed: 151 focused tests, Ruff, JSON/YAML loads, methodology compile/check,
  and `git diff --check`. Existing architecture-audit and UI-scout freshness
  warnings remain unrelated to this eval.

## Mismatch Classification

- **Scorer-contract ambiguity:** the model supplied materially accurate scene
  references, but only 36% passed the deterministic near-verbatim evidence
  heuristic. The independent Opus judge verified the citations and scored 0.95.
  Regrading may be appropriate after a separately approved scorer repair.
- **Model-correct on transport and most content contracts:** exact schema,
  source events, ending, act partition, exclusions, genre/tone, and required
  fields qualified. There was no invented ending or material contradiction.
- **Runtime-blocking economics and latency:** $0.10699 is 10.7x the $0.01
  subject gate, and 33,086 ms exceeds the 30,000 ms latency gate by 10.3%.

## Exact Evidence

- Result: `benchmarks/results/script-bible-gpt6-astra-low-open-frequency-2026-09-05.json`
- Contract manifest: `docs/evals/story-218-gpt6-astra-contract-manifest.json`
- Command: `promptfoo eval -c runtime_tasks/script-bible-runtime.yaml --no-cache --no-share --filter-providers '^GPT-6 Astra Low$' --filter-pattern 'Open Frequency' -j 1 -o results/script-bible-gpt6-astra-low-open-frequency-2026-09-05.json`
- Spend: native probe $0.04427; subject $0.10699; judge estimated $0.138825;
  total estimated $0.290085 of $0.60.

## Conclusion

**Result:** failed — do not adopt for the value-optimized script-bible slot

**Score before:** N/A — no prior Astra evidence
**Score after:** 0.82495 (`0.6999` deterministic hard-gated from `0.9279` raw;
`0.95` rubric)
**Latency after:** 33,086 ms
**Cost after:** $0.10699 per subject call

Access and production-shaped transport qualified. Conditional semantic quality
was strong but deterministically ambiguous rather than a clean maintained pass.
The independent latency and cost failures are decisive, so medium, high, and a
fresh Gemini comparator were not run. Retry only after a materially cheaper and
faster exact-model mode; regrade the frozen output without a new subject call if
the theme-evidence scorer is independently repaired.

**What NOT to retry:** Do not repeat the unchanged low arm, advance reasoning on
this value lane, rerun a comparator, or weaken the scorer/golden to rescue an
absolute economics failure.

## Definition of Done Checklist

- [x] Read prior attempts and current owner contracts
- [x] Ran no-cache at concurrency one
- [x] Recorded score, latency, cost, identity, transport, and spend
- [x] Updated registry score and attempt history
- [x] Preserved result and dirty-contract hashes
- [x] Applied the progressive stop without hidden retries

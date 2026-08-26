# Eval Attempt 030 — Script Bible: Ox Alpha Force-Fresh Drift Rerun

**Status:** Inconclusive — same transport failure, slower diagnostic
**Eval:** script-bible
**Date:** 2026-08-25
**Worker Model:** Codex (GPT-5.6)
**Subject Model:** Ox Alpha (`stealth/ox-alpha`) via OpenRouter

## Mission

Repeat Attempt 029's exact progressive public/synthetic lane without semantic
or transport tuning. The objective is candidate drift: determine whether the
same opaque OpenRouter model identity now behaves better than it did on
2026-08-22. This can detect behavioral change under the same contract, but it
cannot prove that the cause is live learning rather than a provider-side model,
serving, or sampling change.

## Frozen Decision Contract

- Exact requested/served `stealth/ox-alpha`; no fallback model list.
- Same production `script_bible_v1.EXTRACTION_PROMPT`, strict `ScriptBible`
  schema, Open Frequency screenplay and golden, deterministic scorer, and Opus
  4.6 rubric as Attempt 029.
- Same low reasoning, omitted sampling, 65,536 output-token ceiling,
  concurrency one, no cache, one candidate response per progressive stage, and
  US$0.75 aggregate cap.
- First require provider-enforced strict schema with `require_parameters=true`.
  If rejected before a valid artifact, repeat the existing client-only
  diagnostic: no `response_format`, `require_parameters=false`, explicit
  JSON-only instruction, whole-response fence removal only, and raw body saved
  before parsing.
- Start and stop on Open Frequency. Advance to The Mariner and a fresh incumbent
  only if the unchanged absolute gates all pass: valid ScriptBible, latency
  `<=30s`, cost `<=US$0.01`, overall `>=0.90`, deterministic `>=0.70` with all
  hard assertions, rubric `>=0.80`, and every assertion passing.
- Public/synthetic and owner-authorized fixtures may be processed even if the
  provider retains or trains on them. No default, account setting, prompt,
  scorer, golden, commit, push, or deployment change is authorized.

## Preflight

- Clean isolated base: `a68a6cda6f1ea31a8a519b23032f5536ad0ec951`.
- Attempt 029 contract hashes still match for the task, provider, marker prompt,
  scorer, Open Frequency golden/input, runtime prompt/schema, and focused tests.
- Live OpenRouter endpoint metadata on 2026-08-25 still lists one Stealth route
  for exact `stealth/ox-alpha`, zero list price, 1,048,576 context, 131,072 max
  completion tokens, and `response_format` plus `reasoning_effort` support.
- Owner discovery completed. The only configuration mutation before calls is a
  fresh ignored raw-output directory, so Attempt 029 evidence cannot be
  overwritten.

## Work Log

- The strict Open Frequency arm returned the same pre-invocation HTTP 404 as
  Attempt 029 in 153 ms: no endpoint accepted the required strict-schema
  parameters. No provider-enforced ScriptBible artifact existed.
- The unchanged client-only diagnostic returned one terminal exact-model
  response. The adapter validated exact returned model identity before parsing
  and saved the complete 7,608-byte fenced body first. Whole-response fence
  removal succeeded, but Pydantic rejected malformed JSON at line 5 column 350
  because a key/value separator was missing.
- Provider latency was 96,146 ms and Promptfoo's total evaluation duration was
  217,675 ms, versus the prior 47,799 ms provider latency. Both exceed the
  unchanged 30-second absolute gate; the new provider latency is 48,347 ms
  slower (2.0115x the prior result).
- The exception path retained neither the provider response ID nor raw usage,
  so exact identity is supported by the adapter's fail-closed validation order
  but response-level usage/cost cannot be reconciled. OpenRouter still lists
  zero price and Promptfoo reported `$0`.
- Stopped as predeclared. No scorer, Opus judge, The Mariner, or incumbent call
  ran. The response changed in syntax and length, but did not improve on any
  decision gate. An opaque alias rerun cannot establish whether any drift came
  from live learning, a backend model update, serving variation, or sampling.

## Classification and Verdict

- **Access:** available on the relaxed diagnostic route; strict request blocked.
- **Transport:** blocked. Provider-enforced strict schema is still unavailable,
  and the diagnostic still failed JSON parsing.
- **Reliability:** failed; one terminal completion, no valid ScriptBible, and
  provider latency exceeded the gate by 66,146 ms.
- **Capability:** not measured. Neither structural nor semantic scoring ran.
- **Economics:** endpoint list price and Promptfoo-reported spend are `$0`, but
  response-level usage/cost were lost on the parse-error path.
- **Adoption:** defer. The force-fresh result does not support adoption or an
  improvement claim.

## Mismatch Classification

The malformed diagnostic is **model-wrong and runtime-blocking** for the
client-only JSON instruction: after the only allowed fence removal, the output
was still syntactically invalid. No source-content assertions ran, so there is
no screenplay-fact mismatch to classify. The provider's strict-schema 404 is a
transport incompatibility, not a semantic model failure.

## Evidence

- `docs/evals/story-215-ox-alpha-drift-rerun-evidence.json`
- Strict result: `eval-FTV-2026-08-26T05:47:38`
- Diagnostic result: `eval-wYR-2026-08-26T05:47:51`
- Ignored raw body:
  `output/evals/ox-alpha-script-bible-20260825/open-frequency-raw.md`
- Promptfoo-reported spend: `$0` of `$0.75`

## Retry State

`exhausted-until-new-trigger`. A later same-contract rerun can measure another
point of behavioral variance, but repeated daily attempts should not be treated
as proof of live learning. A decision-grade retry trigger remains native strict
schema support or an explicitly approved adapter lane.

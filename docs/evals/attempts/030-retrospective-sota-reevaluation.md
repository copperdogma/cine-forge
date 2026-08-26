# Attempt 030 — Retrospective SOTA reevaluation

**Date:** 2026-08-14
**Story:** 216
**Scope:** fresh incumbent parity against exact `gemini-3.7-flash` on QA, project config, and script bible

## Decision

No model changes. The freshly rerun incumbents are still the measured quality
leaders on all three surfaces, but none clears its repaired absolute quality
contract. “Measured quality leader” and “production-eligible winner” are now
reported separately; there is no production-eligible winner in this attempt.

| Surface | Fresh quality leader | Challenger | Production result |
|---|---:|---:|---|
| QA | GPT-4.1 Mini `0.817475`, `3905 ms`, `$0.0010718/call` | Gemini 3.7 `0.73495`, `3082 ms`, `$0.0039071/call` | neither clears two-case `1.0`; retain default by measured lead, not by stale evidence |
| Project config | Gemini 3 Flash `0.67995`, `17514 ms`, `$0.0141698/call` | Gemini 3.7 `0.65245`, `6585 ms`, est. `$0.009455/call` | neither clears `0.92`; incumbent also misses latency |
| Script bible | Gemini 3.5 Flash-Lite `0.74495`, `4933 ms`, `$0.003700/call` | Gemini 3.7 `0.70995`, `10106 ms`, est. `$0.011435/call` | neither clears `0.90`; challenger also misses cost |

QA used the exact shared production prompt/schema provider. Script bible used
the exact production prompt and provider-enforced `ScriptBible` schema on both
corpora. Config detection remains the maintained two-corpus runtime proxy.

## Judge failure and repair

The frozen Claude Opus 4.6 rubric returned non-parseable prose for every config
and script-bible row. Those raw results are retained as judge-infrastructure
failure evidence and are not ranked. One symmetric replacement arm used a
single frozen GPT-5.4 grader for both candidate and incumbent; no prompt,
scorer, golden, or subject configuration changed between the compared rows.
QA's original rubric was parseable and needed no replacement.

## Failure classification

- QA incumbent passed the positive control but omitted all six required repair
  families on the deliberately bad extraction. Gemini 3.7 also underspecified
  the positive summary and missed the negative-family contract. Model-wrong.
- Both config models produced valid ten-field objects but made material source
  fidelity/calibration errors. Gemini 3 Flash remained higher quality; its
  latency is independently runtime-blocking. Model-wrong plus
  operationally ineligible.
- Both script-bible models preserved strict schema but missed material source
  fidelity/completeness requirements. Gemini 3.5 Flash-Lite remained higher
  quality. Gemini 3.7 was also slower and above the per-call value gate.

## Evidence and spend

- QA result: `benchmarks/results/retrospective-qa-parity-20260814.json`
  (`28e01c914320ef1cb59349ad9c5825adad710507df9867321d6876f89864b756`)
- Config decision result: `benchmarks/results/retrospective-config-parity-openai-judge-20260814.json`
  (`14a06a4c504d4e124f8b5015b3b2b879d7bed3340e14542ac9a4158c4b064a27`)
- Script-bible decision result: `benchmarks/results/retrospective-script-bible-parity-openai-judge-20260814.json`
  (`8c07a3a9b340baffcc408734d254d966d68ea8798bc994ad0f2c8cb71810cbb2`)
- Broken-judge results are retained beside them, including the full two-corpus
  run and the predeclared Mariner progressive arm.

Estimated total provider spend for all subject calls and both judge arms is
`$0.942709`, below the `$5` repo cap. The estimate uses recorded provider cost
where present, Gemini 3.7 introductory pricing for unpriced rows, Claude Opus
4.6 `$5/$25` per million input/output tokens, and GPT-5.4 `$2.50/$15`.

Contract hashes: QA task `f8557380...b4f0`, scorer `c52728b6...6791`, golden
`fea7b91f...d93e`; config task `63c2209a...f4e`, scorer `20c5ba4a...656`; script
bible task `cf587fa7...acdf`, runtime provider `8c0e0a9c...12fe`, scorer
`87a3fa7a...c6d9`.

No executable default, production module, private data, commit, or push was
changed by this attempt.

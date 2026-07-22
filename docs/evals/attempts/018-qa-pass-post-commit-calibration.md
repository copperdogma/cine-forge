# Eval Attempt 018 - QA Pass Post-Commit Calibration

**Status:** In progress after independently adjudicated fixture defect
**Eval:** qa-pass
**Date:** 2026-07-22
**Worker Model:** GPT-5.6 with two independent source/scorer reviewers
**Subject Model(s):** Gemini 3.6 Flash and Gemini 3.5 Flash-Lite; Opus 4.6 judge

## Mission

Run the bounded fresh QA confirmation required to close Story 208 after the
first immutable repaired-contract commit. Classify every mismatch before
changing the fixture or scorer, repair only defects that directly invalidate
this final gate, roll the contract manifest forward, and rerun without cache.

## Diagnostic Baseline

- Contract commit: `d1a1284fb6dfd1ceafd1419782c8fe74d2e143b3`
- Result: `benchmarks/results/qa-pass-story-208-post-repair-2026-07-22.json`
- Result SHA-256:
  `ad4c9d5f976c9081f46476a62d7d5f191b5a78ad6a8524a6a7dca5a4530d922d`
- Matrix: two subjects by two cases; `0/4` rows cleared both gates; total
  evaluation duration `60,998 ms`.
- Diagnostic aggregates: Gemini 3.6 Flash `0.58745`, `6,228 ms/call`, about
  `$0.0113/call`; Gemini 3.5 Flash-Lite `0.61245`, `1,484 ms/call`, about
  `$0.0011/call`.

## Classification

- The nominal positive extraction was still fixture/golden-wrong. It resolved
  an unidentified bloody scrap as scalp/skull, called a partial costume list
  full, and omitted the title card, Rose's uniform, the Dad tattoo, and other
  source material while requiring zero warnings.
- Both subjects' generic positive judgments were also model-wrong: neither
  summary supplied the three source facts required by the deterministic gate.
- Gemini 3.5 Flash-Lite produced six valid error-level negative findings and
  received `0.95` from Opus. The deterministic scorer was wrong because its
  declared `min_errors: 6` was contradicted by an all-eight hard gate and its
  lexical matcher missed `revelation` versus `reveal`.
- Gemini 3.6 Flash reported only four matched error-level findings plus one
  warning and remains model-wrong under the six-error contract.
- The diagnostic result is non-decision-grade. These challenger failures are
  non-runtime-blocking because neither model owns the QA slot, but the broken
  fixture/scorer is default-decision-blocking for any QA comparison.

## Bounded Repair and Retry Plan

1. Make the positive extraction genuinely warning-free without changing its
   expected verdict or the negative case's six-error threshold.
2. Keep all eight negative facts as full-score expectations, but make the hard
   pass gate honor `min_errors` and normalize `revelation` to `reveal`.
3. Add exact positive-source and six-versus-fewer-than-six regressions.
4. Preserve this diagnostic result, commit the corrected v2 contract manifest,
   then rerun the same four rows to a new result path.

## Second Diagnostic

- Contract commit: `f89271b14146ce6924c093257eea89930586414a`
- Result: `benchmarks/results/qa-pass-story-208-post-repair-v2-2026-07-22.json`
- Result SHA-256:
  `01daf7b90f5f5c1ef36a557b974b25efbb89a781c01e125bd2e2c5780c873629`
- The repaired deterministic gate behaved correctly: Flash-Lite's six-error
  negative control scored `0.9437`, while fewer-than-six and unsupported
  judgments stayed red. Remaining subject misses are model-wrong.
- Both positive-case Opus calls stopped at exactly `1,024` completion tokens
  and returned unparseable rubric output; the two shorter negative graders
  completed at `548` and `504` tokens. Promptfoo's bare Anthropic judge string
  did not inherit the separately declared subject-provider budget.
- Classification: judge-contract-wrong and decision-blocking. The narrow retry
  sets `defaultTest.options.provider.config.max_tokens: 4096`, rolls the
  immutable contract manifest to v3, commits, and repeats only these four rows.

## Full-Budget Diagnostic

- Contract commit: `8851717131ee57e42feaba2be25c5d51defb3069`
- Result: `benchmarks/results/qa-pass-story-208-post-repair-v3-2026-07-22.json`
- Result SHA-256:
  `8014a03146f05d1e2dc8bbd76d27804ef312e4233be94231cea621da45271e85`
- All four rubric responses parsed; the positive rows used `1,128` and `1,076`
  completion tokens, directly proving the former `1,024` ceiling was removed.
- Opus then found that the positive fixture called the bloody scrap unidentified
  and unresolved even though Rose asks whether it is skull and Mariner answers
  yes. A fresh context-isolated third adjudicator independently classified the
  fixture GOLDEN-WRONG: it is skull, while only whose skull remains unknown.
- The narrow final retry corrects those two statements, obtains a later
  independent CLEAN pass, rolls immutable manifest v4, commits, and repeats only
  the same four rows. The first post-fix verifier caught and repaired a residual
  chronology mismatch around Mariner's introduction, title card, and confirmation.
  All remaining subject misses stay classified model-wrong.

## Definition of Done

- [x] Diagnostic result retained with exact contract and file identity
- [x] Significant mismatches independently classified
- [x] Direct fixture/scorer defects repaired without lowering the valid gate
- [x] Independent source-first positive-fixture CLEAN pass
- [x] Corrected source/scorer contract committed before the replacement run
- [x] Second four-row diagnostic inspected and judge truncation classified
- [x] Explicit judge output budget and manifest v3 committed before retry
- [x] Full-budget diagnostic inspected and fixture dispute independently adjudicated
- [x] Corrected fixture receives a later independent CLEAN pass
- [ ] Manifest v4 committed before the final retry
- [ ] Final four-row no-cache subject-plus-Opus result inspected and recorded
- [ ] Registry and Story 208 updated with the final decision

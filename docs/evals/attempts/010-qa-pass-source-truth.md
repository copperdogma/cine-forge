# Eval Attempt 010 - QA Pass Source Truth

**Status:** Succeeded with documented limitation
**Eval:** qa-pass
**Date:** 2026-07-21
**Worker Model:** GPT-5.6 orchestrator with context-isolated source-first verifiers
**Subject Model(s):** Gemini 3.6 Flash and Gemini 3.5 Flash-Lite cached outputs; maintained current default/ceiling only if bounded confirmation is later justified

## Mission

Repair the QA source, golden, scorer, and rubric contract that currently labels
a materially incomplete extraction as good. Re-establish an independently
verified pass/fail boundary, then rescore immutable Gemini outputs before any
fresh model call. The goal is decision-grade QA evidence, not preservation of a
historical score.

## Prior Attempts

First dedicated QA attempt. Story 208's model refresh found both new Gemini
models rejected the supposedly good fixture. Manual source comparison then
showed their rejection was substantively correct, so those raw QA scores are
non-decision-grade pending this repair.

## Baseline Reproduction and Classification

- The supposed good case changes where the AirTag was hidden and omits the
  three thugs and gunfight from the source sequence.
- The golden still expects that case to pass.
- The scorer does not enforce all declared warning bounds or required summary
  facts, so a structurally plausible but materially incomplete QA response can
  pass.
- **Classification:** golden-wrong, non-runtime-blocking for the challenger
  models; default-decision-blocking for QA model evidence.

## Plan

1. Use the reset golden workflow. Each verifier reads the screenplay/source
   first, then the QA input/golden. The orchestrator coordinates only verdicts.
2. Correct source-derived facts and persist source path plus SHA-256 provenance.
3. Require an independent later CLEAN pass and structural validation after any
   fix.
4. Add direct scorer controls for expected pass/fail, error and warning bounds,
   required summary facts, materially wrong details, and contradictory output.
5. Probe the matching prompt and Opus rubric for answer leakage, schema-only
   acceptance, and contradiction handling; change only demonstrated defects.
6. Rescore cached Gemini outputs with immutable hashes. Restore both
   deterministic and rubric judging for any bounded final confirmation.

## Work Log

- 2026-07-21: Created the attempt before semantic edits. Reset checklist marks
  the QA fixture pending and preserves its prior false CLEAN status.
- 2026-07-21: Added direct scorer controls before touching the QA golden. The
  prior scorer could still pass a wrong `passed` boolean (`0.70` composite), a
  bad-case issue that merely repeated the expected field, unlimited good-case
  warnings, and a good-case summary missing every declared conclusion. The
  repaired scorer hard-gates those contracts while exact good and bad controls
  remain `1.0`; seven perfect/adversarial/monotonicity tests pass. Classification
  remains `golden-wrong` evaluation evidence caused by scorer defects,
  non-runtime-blocking but default-decision-blocking. No subject call or cost.
- 2026-07-21: Three independent source-first passes corrected 15 total semantic
  defects and ended CLEAN. Both nominal candidates correctly fail. The final
  source-backed contract contains six required defects for the first candidate
  and eight for the second, with achievable error thresholds; validator and all
  omission/flip/count mutations pass. Follow-up scorer probes closed one-token
  reason, note/error filler, per-required severity, low-confidence, empty-summary,
  and root-schema bypasses; 23 focused tests pass. The task label and both Opus
  rubrics remain under prompt/rubric repair before cached regrading.
- 2026-07-22: Final repair rebuilt the maintained positive extraction from the
  complete elevator source while preserving the independently verified
  negative case. The scorer now enforces exact root and issue schemas, expected
  pass/fail, zero-error/zero-warning bounds for the positive, error and warning
  bounds for the negative, confidence, required issue semantics, required
  positive facts, and polarity-aware summary grounding. Prompt and rubric
  probes reject answer copying, generic filler, contradictory/negated facts,
  and schema-only responses. Registry history is explicitly non-decision-grade.

## Evidence Identity

- Base git SHA: `a5b5c88`
- Working-tree state: uncommitted and provisional.
- Cached result paths: existing Story 208 Gemini QA result artifacts are
  retained as historical evidence. They are not comparable to the repaired
  eval because the evaluated positive input itself changed materially.
- Current contract identity is included in
  `docs/evals/story-208-contract-manifest-v1.json` and remains provisional while
  uncommitted.
- Paid repair calls: none.

## Conclusion

**Result:** succeeded with documented limitation
**Score before:** `0.5813` Gemini 3.6 Flash; `0.5950` Gemini 3.5 Flash-Lite, both invalid under the known-wrong contract
**Score after:** no replacement model score; cached outputs are non-comparable
because the positive input and semantic contract changed
**Latency before:** `5.7s` / `1.6s` per case respectively
**Latency after:** Unchanged during cached rescore
**Cost before:** `$0.0038` / `$0.0014` per case respectively
**Cost after:** `$0.00` incremental during contract repair and cached rescore

---

## Definition of Done Checklist

- [x] Baseline contradiction and classification recorded before repair
- [x] Two independent source-first golden reviews complete
- [x] Any FIXED pass receives a later independent CLEAN pass
- [x] Structural validator passes
- [x] Source path/fingerprint and semantic invariants are durable
- [x] QA scorer perfect/adversarial/monotonicity tests pass
- [x] Prompt and rubric probes pass
- [x] Cached subject outputs are preserved and explicitly classified non-comparable
- [x] Registry score/history and attempt summary are updated
- [x] Bounded fresh confirmation is deferred until a runtime decision requires paid evidence on the repaired contract

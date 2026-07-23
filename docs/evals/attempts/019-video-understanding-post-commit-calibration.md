# Eval Attempt 019 - Video Understanding Post-Commit Calibration

**Status:** Succeeded — decision-grade HOLD for both challengers
**Eval:** video-understanding
**Date:** 2026-07-22
**Worker Model:** GPT-5.6 with independent result review
**Subject Model(s):** Gemini 3.6 Flash and Gemini 3.5 Flash-Lite; Opus 4.6 judge

## Mission

Run the bounded fresh six-case ordered-JPEG confirmation required to close
Story 208. Repair only a direct output-contract defect found in the committed
v2 gate, roll the versioned prompt/manifest forward, and rerun the same twelve
rows without cache.

## Diagnostic Baseline

- Contract commit: `d1a1284fb6dfd1ceafd1419782c8fe74d2e143b3`
- Result:
  `benchmarks/results/video-understanding-story-208-post-repair-2026-07-22.json`
- Result SHA-256:
  `3a4b820a0d1ef1ec7f316b772d9712e36cb8e162cd7b1802dd3717214d66ef56`
- Matrix: two subjects by six source-backed cases; total duration `267,323 ms`.
- Opus means were `0.3867` for Gemini 3.6 Flash and `0.3717` for Gemini 3.5
  Flash-Lite. Every stored deterministic component was a parse-failure zero.

## Classification

- The v2 prompt named keys but did not state that `continuity_notes` was an
  array, `continuity_status` was scalar, or evidence required exact
  `frame_index`/`cue` objects. Gemini received `responseMimeType` but no
  `responseSchema`.
- All 12 outputs therefore used a string for `continuity_notes`; ten also used
  evidence strings, the other two used the wrong evidence key, and three used
  a list for `continuity_status`. The scorer rejected every response before
  content scoring. Classification: prompt/transport contract-wrong and
  decision-blocking; the generated hold report is diagnostic only.
- Opus also found substantive model-wrong camera, motion, continuity, tone,
  and evidence misses in every row. A shape-only local diagnostic still left
  all deterministic scores below `0.70`; those derived values are not promoted.
- Subjective tone and abstract-shape readings remain documented ambiguities,
  not reasons to change the source-backed targets during this bounded repair.

## Bounded Repair and Retry Plan

1. Roll the prompt lineage to `video-understanding-frame-packet-v3` and state
   every nested JSON type explicitly.
2. Send Gemini an exact all-fields-required response schema derived from the
   maintained prediction model; retain the strict scorer unchanged.
3. Add prompt, transport, schema, and lineage regressions.
4. Preserve this diagnostic result, commit the corrected v2 contract manifest,
   then rerun the same twelve rows to a new result path and regenerate the
   report.

## Final v3 Result

- Contract commit: `f89271b14146ce6924c093257eea89930586414a`
- Durable evidence commit: `2367cc0`
- Raw result:
  `benchmarks/results/video-understanding-story-208-post-repair-v3-2026-07-22.json`
  (`2891a9d0988b562eb199ff71f171136a1a583028c37d59ba91203dd9d7a9dd72`)
- Report JSON:
  `benchmarks/results/video-understanding-story-208-post-repair-v3-2026-07-22-report.json`
  (`a29edb847c0bb68c0a0bc26c0f69149d28f3564df9bddaaaab4f5e9830899a5c`)
- Report Markdown:
  `benchmarks/results/video-understanding-story-208-post-repair-v3-2026-07-22-report.md`
  (`329c8f84658eb5bde6aa8563cea25ef8a23c3aab8de53ebf36a0719d940ec5a5`)
- All twelve outputs satisfy the exact 13-field schema, every expected case
  appears once per subject, identity/raw usage are complete, and the report has
  no contract or regrade errors. Both models fail all six cases.
- Gemini 3.6 Flash: deterministic `0.4294`, rubric `0.4500`, combined `0.4397`,
  `6,356 ms/call`, about `$0.017154/call`.
- Gemini 3.5 Flash-Lite: deterministic `0.4442`, rubric `0.3700`, combined
  `0.4071`, `2,307 ms/call`, about `$0.002730/call`.

## Classification and Boundary

- Model-wrong failures span motion, continuity, camera language, recurring
  objects, tone/emotion, and frame-bound evidence; neither challenger is close
  to the `0.80` gate.
- Subjective silent-frame tone/speed readings are ambiguous and do not affect
  the rejection.
- Row inspection found conservative target/matcher defects: gold/amber synonym
  penalties, missing red/blue palette truth, rectangle/rectangular matching,
  an unsupported increasing-scale rooftop target, and exact-keyword penalties
  for semantic equivalents. The largest quantified correction moves 3.6 only
  from `0.4397` to about `0.4575`; every row still fails and HOLD is unchanged.
  Per the user's frozen boundary these are recorded follow-up, not another audit
  expansion. The result is decision-grade for HOLD/do-not-adopt, not for fine
  ranking or native video/audio capability claims.

## Conclusion

**Result:** succeeded. Retain both challengers as non-defaults for this ordered-
frame lane. Remaining failures are non-runtime-blocking for current production.

## Definition of Done

- [x] Diagnostic result retained with exact contract and file identity
- [x] Every significant parse/content mismatch classified
- [x] v3 prompt and Gemini response schema implemented with focused tests
- [x] Independent v3 contract review passes
- [x] Corrected contract committed before the replacement run
- [x] Fresh twelve-row no-cache subject-plus-Opus result and report inspected
- [x] Registry and Story 208 updated with the final decision

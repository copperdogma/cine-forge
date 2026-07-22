# Eval Attempt 019 - Video Understanding Post-Commit Calibration

**Status:** In progress after diagnostic contract failure
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

## Definition of Done

- [x] Diagnostic result retained with exact contract and file identity
- [x] Every significant parse/content mismatch classified
- [x] v3 prompt and Gemini response schema implemented with focused tests
- [x] Independent v3 contract review passes
- [ ] Corrected contract committed before the replacement run
- [ ] Fresh twelve-row no-cache subject-plus-Opus result and report inspected
- [ ] Registry and Story 208 updated with the final decision

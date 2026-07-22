# Eval Attempt 011 - Textual Golden Source Reverification

**Status:** Succeeded with process exception
**Eval:** repository-textual-golden-truth (19 maintained semantic goldens)
**Date:** 2026-07-21
**Worker Model:** GPT-5.6 orchestrator; fresh GPT-5.6 high-reasoning verifier per fixture/pass
**Subject Model(s):** N/A - source and expected-output truth repair

## Mission

Reverify every maintained default-driving textual golden from its source with
two independent context-isolated reviews, correct all material omissions and
inventions, and leave durable source identity plus structural validation. A
historical CLEAN label, schema validity, or scorer agreement is not semantic
proof. Any fixture changed in a pass must receive a later fresh CLEAN pass.

## Prior Attempts

This is the first repository-wide source-first golden attempt. Config Attempt
001 previously found four source errors capable of reversing model rankings,
but the maintained checklist later declared ten fixtures clean while omitting
entity discovery, script bible, and the action-line scene-entity golden. Story
208 then proved the checklist's QA clean claim false.

## Baseline Reproduction and Classification

- Reset `10` historical CLEAN rows with prior status preserved.
- Expanded the checklist from `10` to `13` semantic fixtures.
- The existing checklist omitted two benchmark goldens and one default-driving
  test golden.
- The QA fixture has a known screenplay contradiction.
- **Classification:** golden-wrong where source review finds defects;
  non-runtime-blocking unless the same assumption is consumed by production,
  but default-decision-blocking for every affected eval.

## Verification Protocol

1. One fresh high-capability agent owns one fixture in one pass.
2. The verifier reads the input/source first and builds an independent model
   before opening the golden.
3. Context-isolated verifiers, not the orchestrator, are the certification
   authority. The intended process kept source/golden semantics out of the
   orchestration context; during later adversarial remediation the orchestrator
   necessarily saw some semantic snippets. That exception is disclosed and did
   not replace the later independent source-first CLEAN passes.
4. Pass 1 always remains nonterminal. Pass 2 may become CLEAN only if it finds
   zero issues; any FIXED pass requires a later independent CLEAN pass.
5. Every pass runs the fixture validator. Structural errors are a hard stop.
6. Final evidence records source/golden fingerprints and material correction
   classes; uncommitted evidence remains provisional.

## Work Log

- 2026-07-21: Reset and expanded the checklist before semantic edits.
- 2026-07-21: Scene-extraction pass 1 found one reversed floor-direction claim
  and fixed it; validator passed with two intentional empty-character warnings.
- 2026-07-21: Location-extraction pass 1 found seven defects: four omitted
  significant interior locations, two coverage/evidence omissions, and one
  invented recency inference. Validator passed without warnings. Fresh pass-2
  agents were launched for both changed fixtures.
- 2026-07-22: The campaign closed with 19 maintained semantic goldens: the 13
  original/default-driving fixtures plus six Open Frequency/difficult-
  normalization fixtures. Every changed fixture received a later independent
  source-first zero-issue pass; the last prop and script-bible passes also
  replayed 23 accumulated polarity/schema/association mutations. The new Open
  Frequency config golden required a separate independent source-first review
  and follow-up scorer/golden repair before certification. The canonical
  validator discovers all 19 and finishes with zero errors; its 38 warnings are
  intentional empty optional fields recorded by fixture.

## Evidence Identity

- Base git SHA: `a5b5c88`
- Checklist: `benchmarks/golden/_verification-checklist.md`
- Protocol: `benchmarks/golden/_verify-golden-outputs.md`
- Working-tree state: uncommitted and provisional.
- Source/golden and verification-contract hashes are frozen in
  `docs/evals/story-208-contract-manifest-v1.json`.
- Paid calls: none.

## Conclusion

**Result:** succeeded with process exception
**Score before/after:** Not applicable; expected truth must be clean before cached rescoring
**Latency before/after:** Not applicable
**Cost before/after:** `$0.00`

---

## Definition of Done Checklist

- [x] Historical statuses reset with audit trail
- [x] All 19 maintained semantic goldens are listed
- [x] Original fixtures received the reset source-first review campaign; all new/changed fixtures received independent source-first certification
- [x] Every FIXED pass has a later independent CLEAN pass
- [x] Every final fixture passes structural validation
- [x] Source paths and SHA-256 fingerprints are durable
- [x] Material corrections and mismatch/runtime classifications are recorded
- [x] Final source/golden hash manifest is recorded
- [x] Ledger rows are terminal with evidence
- [x] Comparable cached outputs were regraded; changed-input outputs are explicitly non-comparable before any paid rerun

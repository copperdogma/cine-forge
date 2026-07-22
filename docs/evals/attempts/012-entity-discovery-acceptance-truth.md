# Eval Attempt 012 - Entity Discovery Acceptance Truth

**Status:** Succeeded with documented limitation
**Eval:** entity-discovery acceptance and prompt/rubric contract
**Date:** 2026-07-21
**Worker Model:** GPT-5.6
**Subject Model(s):** No new subject call during harness repair

## Mission

Remove the circular entity-discovery acceptance setup, gate both recall and
precision from independent source annotations, and align the subject prompt and
semantic rubric with the production taxonomy before any live confirmation.

## Prior Evidence

Story 208 proved that the deterministic scorer awarded empty entities a false
perfect and that the acceptance lane constructed its entire upstream scene
index from the same entity golden used to score the output. The subject prompt
and Opus rubric also said extra entities would not be penalized while the
production prompt, module tests, and downstream bible costs explicitly prefer a
short, source-grounded entity set.

## Baseline Reproduction and Classification

- The acceptance test copied golden required/optional characters, locations,
  and props into `breakdown_scenes`, making required recall self-fulfilling.
- It asserted only required location/prop recall and declared passthrough
  characters always correct; fabricated or noisy predictions had no gate.
- **Classification:** `golden-wrong` evaluation evidence caused by circular
  fixture construction and missing precision criteria; non-runtime-blocking but
  default-decision-blocking.

## Repair and Evidence

- The acceptance input now comes from the separately source-verified action-line
  scene annotation fixture and is shaped exactly like the normal
  `breakdown_scenes` upstream artifact.
- The entity golden is used only after execution to compute independent required
  recall and required-plus-optional precision.
- Characters, locations, and props each require `1.0` recall and at least `0.8`
  precision; unexpected predictions are printed in the live evidence packet.
- Two direct unit controls prove scene-derived upstream construction and that an
  unknown prediction lowers precision. Together with the repaired deterministic
  scorer suite, six focused tests pass. Ruff is clean.
- The subject prompt now balances recall with downstream precision, rejects
  noun dumps and duplicate aliases, and no longer discloses fixture-specific
  answer examples. The Opus rubric receives the screenplay instead of an
  answer key, treats material false positives as failures, and requires both
  strong recall and precision for a semantic pass. These changes are covered by
  the Group B contract suite. The final entity scorer also uses exact schema,
  exact required recall, zero unknown entities, explicit exclusions, and
  source-valid staged-location aliases. Historical rows are marked
  non-decision-grade; no provider call or incremental cost occurred.

## Evidence Identity

- Base git SHA: `a5b5c88`
- Acceptance: `tests/acceptance/test_entity_discovery_verification.py`
- Independent input truth: `tests/fixtures/golden/the_mariner_scene_entities.json`
- Direct controls: `tests/unit/test_entity_discovery_acceptance_contract.py`
- Working-tree state: uncommitted and provisional.
- Final contract hashes: `docs/evals/story-208-contract-manifest-v1.json`
  (provisional while uncommitted).

## Conclusion

**Result:** succeeded with documented limitation - circular input and
prompt/rubric contracts are fixed; fresh runtime-shaped model evidence is absent
**Quality before:** recall-only and self-seeded
**Quality after:** independent `1.0` recall plus `>=0.8` precision contract
**Latency before/after:** unchanged; no subject call
**Cost before/after:** `$0.00` incremental

---

## Definition of Done Checklist

- [x] Circular baseline reproduced and classified before repair
- [x] Normal upstream-shaped input is independently source annotated
- [x] Recall and precision both gate all three entity categories
- [x] Direct acceptance-contract regressions pass
- [x] Subject prompt and Opus rubric agree with precision contract
- [x] Comparable cached outputs are regraded or explicitly invalidated before a live call
- [x] Registry and ledger carry final non-decision-grade status and contract hashes

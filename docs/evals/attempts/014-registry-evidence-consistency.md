# Eval Attempt 014 - Registry Evidence Consistency

**Status:** Succeeded
**Eval:** registry, task, and retained-result consistency
**Date:** 2026-07-21
**Worker Model:** GPT-5.6
**Subject Model(s):** N/A - evidence-governance repair

## Mission

Make the eval registry fail closed when a configured task, scorer, golden,
declared case count, or retained result no longer exists or disagrees with the
record. Preserve unavailable historical evidence as an explicit limitation
rather than deleting the score or pretending an ignored path is durable.

## Baseline Reproduction and Classification

- All 25 registry eval IDs and their top-level config/scorer/golden/script paths
  currently resolve.
- `video-understanding` declares six cases while its task config contains 20.
  The command's `--filter-first-n 6` makes this an undocumented pilot policy,
  not an equivalent case count.
- Three `full-script-throughput` score rows point at ignored `output/runs/...`
  run-state files that are no longer present.
- There is no maintained executable contract checking unique IDs, declared
  case counts, referenced task files, or result-file durability.
- **Classification:** evidence-provenance wrong / `golden-wrong` decision
  metadata, non-runtime-blocking but decision-blocking wherever a missing or
  mismatched artifact is treated as reproducible proof.

## Repair Contract

1. Parse the registry and every maintained Promptfoo task.
2. Require unique eval IDs and existing configured owner paths.
3. Compare task test count with the registry, allowing only an explicit,
   machine-readable pilot/filter policy.
4. Resolve prompt, Python assertion, input, golden, and other file references
   relative to each task and fail on missing paths.
5. Require every retained score result path to exist, or carry an explicit
   unavailable-evidence status and reason.
6. Add direct mutation tests for duplicate IDs, missing paths, case drift, and
   missing historical results.

## Evidence Identity

- Base git SHA: `a5b5c88`
- Registry: `docs/evals/registry.yaml`
- Working-tree state: uncommitted and provisional.
- Paid calls: none.

## Work Log

- 2026-07-22: Added the registry/task consistency checker and direct duplicate,
  case-drift, missing-reference, missing-result, and classified-unavailable
  controls. The maintained 25-entry registry passes the checker.
- 2026-07-22: A downstream propagation audit found that
  `scripts/methodology-graph.js` selected the latest/highest registry score
  without reading either the score's `evidence_status` or the eval's inherited
  `historical_evidence_status`. A contaminated row could therefore reappear as
  current planning evidence after the registry itself had invalidated it. The
  compiler now excludes explicit non-decision-grade rows and makes an unmarked
  row inherit a top-level contaminated historical status; an explicitly
  decision-grade repaired row remains eligible. Sixteen methodology-graph
  tests pass, including a mutation where newer `1.0` and `0.99` contaminated
  rows lose to the only repaired-contract `0.81` row. Classification:
  evidence-provenance wrong, non-runtime-blocking but planning/default-decision
  blocking. No provider call or cost.
- 2026-07-22: Added a separate truth-audit-ledger validator instead of treating
  YAML parse success as completion. It initially enforced 159 expected surfaces by
  kind, unique IDs, required owner/decision/notes/limitations fields, allowed
  statuses, and resolving evidence for every terminal row. Seven direct
  mutation/canonical controls pass. Normal `make check-evals` now runs the
  structural check; final closure additionally requires
  `check_truth_audit_ledger.py --require-terminal`, which currently fails by
  design while audit rows remain pending.
- 2026-07-22: Final closure expands the executable inventory to 165 surfaces,
  including 19 semantic goldens and four audit harnesses. Every row is terminal,
  every maintained task/scorer/prompt/provider/golden/registry ID is discovered
  from the repository rather than trusted from a hand count, config detection's
  second corpus is reconciled, and the generated contract manifest freezes the
  exact selected file bundle by bytes and SHA-256. The registry, terminal ledger,
  contract manifest, compromise checker, and generated methodology graph all
  pass together.

## Conclusion

**Result:** succeeded
**Quality before:** path presence was conventional, not enforced
**Latency/cost before/after:** not applicable; `$0.00` incremental

---

## Definition of Done Checklist

- [x] Baseline case drift and missing retained artifacts reproduced
- [x] Registry/task checker added with adversarial tests
- [x] Pilot case policy is explicit and checked
- [x] Missing historical artifacts are explicitly classified
- [x] All 25 entries pass the maintained checker
- [x] Ledger and story evidence are updated
- [x] All 165 surfaces are terminal with resolving evidence
- [x] Contract manifest passes its no-drift check
- [x] Generated methodology views exclude contaminated history

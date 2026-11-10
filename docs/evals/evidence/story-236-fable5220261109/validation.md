# Validation — 2026-11-09

Evaluation-only adapter/tooling and evidence changes; no product/UI callsite,
default, deployment or asset change. The smallest applicable checks were used.

- `PYTHONPATH=src <cineforge-python> -m pytest -q` with
  `test_video_understanding_fable52_contract.py`,
  `test_video_understanding_gpt6_contract.py`,
  `test_video_understanding_mistral_price_contract.py`,
  `test_video_understanding_scorer_adversarial.py`,
  `test_video_understanding_v4_archive.py`,
  `test_video_understanding_benchmark.py`,
  `test_video_understanding_opus55_contract.py`,
  `test_video_understanding_sonnet55_contract.py`,
  `test_video_understanding_haiku55_contract.py`: **71 passed** against this
  worktree's source. Later accounting/doc-only changes do not affect them.
- Ruff on both changed adapters, new Fable runner, both offline report versions
  and Fable contract tests: passed.
- Source `build_video_understanding_truth_v4.py --check`: passed,13files match
  frozen source/corrections. No truth/golden/prompt/scorer modification.
- Original report and accounting-only v2 `--verify`: both passed.18native/
  adapter exact-wire/parsed-output replay pairs,18 complete-source reviews,
  37 ledger entries. All18 final outputs checked to contain exact13keys.
- Original zero-accounting assumption preserved, not rewritten. V2 carries
  known usage estimate1.00078155USD plus2.15872 unreconciled rejected-request
  reservation, conservative3.15950155/20. No later paid call.
- `scripts/check_eval_registry.py`: passed.
- `scripts/check_truth_audit_ledger.py`: passed.
- `scripts/build_eval_contract_manifest.py --output
  docs/evals/story-208-contract-manifest-v36.json --write`, then `--check`:
  passed,1089files; historicalv35 untouched.
- `node scripts/methodology-graph.js build` and `check`: passed. Existing
  architecture-audit and UI-scout freshness warnings retained.
- `git diff --check`: passed. Generated graph/index/build-map only add Story236.
- Raw subjects/reviews inspected; all30 original JPEGs viewed in lossless source
  sheets, with dialogue originalframes0/4 directly viewed. Root independently
  corroborated dialogue geometry and reviewed source-first classification.
  Two judge rationale errors retained and explicitly rejected without rescoring.
- Root separately verified all264 current v2 manifest hash/size records.
- Worktree has no .env/.env.local created; existing owner credentials loaded
  through sanctioned wrapper, no injection or key copying. No credential cleanup
  required. Final disk free about44GiB, above512MiB guard; no unrelated cleanup.

No runtime/frontend suite was needed for this isolated benchmark adapter work.
Remaining red quality/value gates are non-runtime-blocking. Native source/code
identities remain unchanged after tests; docs/accounting-only closeout reused
applicable checks. Worktree retained uncommitted on
codex/fable52-video-20261109 for coordinator review; no commit/push/cleanup.

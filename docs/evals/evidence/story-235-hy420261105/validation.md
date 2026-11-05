# Validation — 2026-11-05

- `PYTHONPATH=src <cineforge-python> -m pytest tests/unit/test_video_understanding_benchmark.py tests/unit/test_video_understanding_mistral_price_contract.py tests/unit/test_video_understanding_dataset.py tests/unit/test_video_understanding_scorer_adversarial.py -q`: 65 passed on changed optional reasoning adapter and unchanged source/scorer contracts. An earlier command used a nonexistent scorer filename, corrected before this pass.
- Ruff on both new scripts, both changed provider files and changed benchmark test: passed.
- `PYTHONPATH=src <cineforge-python> benchmarks/scripts/report_hy4_video_comparison.py --verify`: passed; 9 settled calls, 3 exact native/adapter pairs, complete strict high request and frozen producing/source/evidence hashes.
- `scripts/check_eval_registry.py`: passed.
- `scripts/build_eval_contract_manifest.py --output docs/evals/story-208-contract-manifest-v35.json --check`: passed, new immutable 1088-file contract manifest; historical v34 unchanged.
- `node scripts/methodology-graph.js build` and `check`: passed. Existing architecture audit and UI scout freshness warnings retained. Initial custom frontmatter parser rejected inline category lists; multiline metadata repaired, no subject evidence changed.
- `git diff --check`: passed.

No runtime or UI change, so product integration/frontend suites were not applicable. Raw model and source outputs were inspected, including original source frames 0/3/4. Evaluation rejection is non-runtime-blocking. Existing owner credentials were used through their normal wrapper; no injected variable or secret cleanup required. No live calls during closeout.

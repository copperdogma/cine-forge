# Runbook: Promptfoo

> Run, inspect, and record CineForge promptfoo evals.

## Context

CineForge uses promptfoo for model/prompt benchmarking across pipeline tasks.
The maintained `benchmarks/` contracts and `docs/evals/registry.yaml` live in
the same CineForge checkout. A result is replayable only when the task,
registry, exact subject output, and every nondeterministic input used for
scoring resolve from that exact checkout and commit. For visual/media evals,
the candidate bytes are not goldens, but decision-bearing panels, grids,
references, clips, frames, and artifact lineage must still be checked in under
a hash-validated evidence manifest.

Use this runbook when creating, running, or recording promptfoo-based evals.

## Prerequisites

- Node.js 24 LTS available via `nvm`
- `promptfoo` installed globally
- API keys set for the providers under test
- an active CineForge checkout containing both `benchmarks/tasks/` and
  `docs/evals/registry.yaml`
- If you want a freshness delay for the global `promptfoo` install, configure it in `~/.npmrc`; repo-local npm config does not reliably govern global installs

## Steps

1. `[judgment]` Resolve and freeze the evidence checkout.
   - Require `benchmarks/tasks/` and `docs/evals/registry.yaml` in the same
     checkout.
   - Record the commit before a decision-grade run. If the contracts are dirty,
     keep the result provisional and do not promote it as current score evidence.
   - For a visual/media run, verify that the exact scored media and its manifest
     are tracked, hash-valid, and unchanged from the real commit recorded on the
     score row. `working-tree` is provisional, never decision-grade. A manifest
     under an ignored runtime directory is diagnostic only because it cannot
     restore missing bytes.

2. `[script]` Load the Node toolchain.

```bash
source ~/.nvm/nvm.sh && nvm use 24 > /dev/null 2>&1
```

3. `[script]` Run the eval in a `benchmarks/` subshell from the repository root.

```bash
(cd benchmarks && promptfoo eval -c tasks/<eval>.yaml --no-cache -j 3)
```

Save results explicitly when you need a named artifact:

```bash
(cd benchmarks && promptfoo eval -c tasks/<eval>.yaml --no-cache --output results/<run-name>.json -j 3)
```

4. `[script]` Return to the repository root and inspect metrics from the same
   checkout.

```bash
.venv/bin/python scripts/extract-eval-metrics.py --result-file benchmarks/results/<run-name>.json
```

5. `[judgment + script]` Stage one complete score row, validate one exact result
   against the current task, then refresh its extracted runtime metrics.

   First add exactly one complete row to `docs/evals/registry.yaml` for the
   selected result. Record model/call identity, evidence status, score metrics,
   measured date, contract `git_sha`, and `result_file`; for a decision-grade
   visual row, also record the retained-media manifest and manifest SHA-256.
   This is an explicit classification/promotion decision. The extraction tool
   does not create a score row or decide that evidence is decision-grade; it
   requires the exact row to exist and only validates the retained result while
   refreshing latency/cost fields.

```bash
PYTHONPATH=src .venv/bin/python scripts/extract-eval-metrics.py \
  --update-registry --dry-run \
  --result-file benchmarks/results/<run-name>.json
PYTHONPATH=src .venv/bin/python scripts/extract-eval-metrics.py \
  --update-registry \
  --result-file benchmarks/results/<run-name>.json
```

   - The update must fail if the result's provider/model/call identity, task
     config, prompt bytes, rubric, grader, or case matrix is stale or incomplete.
   - confirm the staged row records score, latency, cost, `git_sha`, and result
     file; for visual evidence, confirm the retained-media path and digest
   - add an attempt summary when the run was part of an improvement loop

6. `[judgment]` Classify significant mismatches before closing the work.
   - `model-wrong`
   - `golden-wrong`
   - `ambiguous`
   - for compromise/detection evals, also record `runtime-blocking` vs
     `non-runtime-blocking`

## Boundaries

### Always do

- run Promptfoo in the documented `benchmarks/` subshell, then run registry
  extraction from the repository root
- set explicit output files for named benchmark artifacts
- update the registry whenever you run an eval
- use one explicit result file and validate it against the current task before
  changing current score evidence
- retain every nondeterministic visual/media input whose bytes influenced a
  decision-grade score, even though candidates remain distinct from goldens

### Ask first

- benchmark workspace path cannot be resolved
- the task appears to require a second benchmark system instead of promptfoo

### Never do

- assume the benchmark workspace is in the current checkout if you have not
  verified it
- treat a red compromise/detection eval as automatically blocking without
  mismatch classification
- bulk-update registry rows from a directory of unrelated retained results
- promote a dirty-contract, duplicate-key, stale-task, or non-replayable result
  as decision-grade evidence
- treat a hash-only manifest in an ignored directory as recoverable visual
  evidence

## Troubleshooting

- If `promptfoo` cannot write under your normal home directory, set a repo-local
  `PROMPTFOO_HOME` for the run and record that choice in the work log.
- If you want npm release-age gating for global `promptfoo` updates, set it in
  `~/.npmrc`; this repo cannot enforce that knob for a global install.
- If a config looks valid but the model returns truncated JSON, check output
  token caps before concluding the model is weak.
- If the benchmark workspace is missing entirely, restore or create it through
  `/setup-methodology refresh` before adding new promptfoo tasks.

## Lessons Learned

- 2026-07-22 — Story 208 consolidated the truth boundary: maintained promptfoo
  contracts and the registry must be read from the same exact CineForge
  checkout. A historical sidequest path is not provenance.

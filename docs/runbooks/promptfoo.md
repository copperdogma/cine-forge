# Runbook: Promptfoo

> Run, inspect, and record CineForge promptfoo evals.

## Context

CineForge uses promptfoo for model/prompt benchmarking across pipeline tasks.
The benchmark workspace lives in a separate sidequest worktree with the standard
`benchmarks/` layout documented in `AGENTS.md`.

Use this runbook when creating, running, or recording promptfoo-based evals.

## Prerequisites

- Node.js 24 LTS available via `nvm`
- `promptfoo` installed globally
- API keys set for the providers under test
- access to the benchmark workspace that contains `benchmarks/tasks/`
- `docs/evals/registry.yaml` available in the main repo

## Steps

1. `[judgment]` Resolve the benchmark workspace.
   - If the current checkout already has `benchmarks/`, use it.
   - Otherwise use the sidequest worktree documented in `AGENTS.md`.

2. `[script]` Load the Node toolchain.

```bash
source ~/.nvm/nvm.sh && nvm use 24 > /dev/null 2>&1
```

3. `[script]` Run the eval from the `benchmarks/` directory.

```bash
promptfoo eval -c tasks/<eval>.yaml --no-cache -j 3
```

Save results explicitly when you need a named artifact:

```bash
promptfoo eval -c tasks/<eval>.yaml --no-cache --output results/<run-name>.json -j 3
```

4. `[script]` Extract metrics back in the main repo.

```bash
.venv/bin/python scripts/extract-eval-metrics.py --result-file benchmarks/results/<run-name>.json
```

5. `[script]` Update `docs/evals/registry.yaml`.
   - record score, latency, cost, `git_sha`, and result file
   - add an attempt summary when the run was part of an improvement loop

6. `[judgment]` Classify significant mismatches before closing the work.
   - `model-wrong`
   - `golden-wrong`
   - `ambiguous`
   - for compromise/detection evals, also record `runtime-blocking` vs
     `non-runtime-blocking`

## Boundaries

### Always do

- run promptfoo from the `benchmarks/` directory
- set explicit output files for named benchmark artifacts
- update the registry whenever you run an eval

### Ask first

- benchmark workspace path cannot be resolved
- the task appears to require a second benchmark system instead of promptfoo

### Never do

- assume the benchmark workspace is in the current checkout if you have not
  verified it
- treat a red compromise/detection eval as automatically blocking without
  mismatch classification
- leave scores stale after a real eval run

## Troubleshooting

- If `promptfoo` cannot write under your normal home directory, set a repo-local
  `PROMPTFOO_HOME` for the run and record that choice in the work log.
- If a config looks valid but the model returns truncated JSON, check output
  token caps before concluding the model is weak.
- If the benchmark workspace is missing entirely, restore or create it through
  `/setup-methodology refresh` before adding new promptfoo tasks.

## Lessons Learned

- 2026-03-20 — CineForge's promptfoo lane is a documented sidequest workspace,
  not an implied in-repo folder. Runbooks and skills should describe that
  contract explicitly instead of pretending there is one stable absolute path.

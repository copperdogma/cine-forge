# Runbook: Promptfoo

> Run, inspect, and record CineForge promptfoo evals.

## Context

CineForge uses promptfoo for model/prompt benchmarking across pipeline tasks.
The benchmark workspace is the verified CineForge checkout containing the
selected task, prompt, scorer, golden, result, and registry contracts. It may
be the current checkout or a separate sidequest worktree; resolve it from live
worktree state as documented in `AGENTS.md`. A result is replayable only when
the registry, exact subject output, and every nondeterministic scoring input
resolve from that same checkout and commit. For visual/media evals, candidate
bytes are not goldens, but decision-bearing panels, grids, references, clips,
frames, and artifact lineage must still be checked in under a hash-validated
evidence manifest.

Use this runbook when creating, running, or recording promptfoo-based evals.
For an end-to-end new/repeated/multi-model decision, start with
`/evaluate-model`; this runbook is its mechanical Promptfoo layer.

## Prerequisites

- Node.js 24 LTS available via `nvm`
- `promptfoo` installed globally
- provider credentials loadable through the selected checkout's env wrapper
- an active CineForge checkout containing both `benchmarks/tasks/` and
  `docs/evals/registry.yaml`
- access to that checkout's `scripts/with_cine_forge_provider_env.py`
- If you want a freshness delay for the global `promptfoo` install, configure it in `~/.npmrc`; repo-local npm config does not reliably govern global installs

## Steps

1. `[judgment]` Resolve and freeze the evidence checkout.
   - Prefer the current checkout when it contains `benchmarks/`; otherwise use
     `git worktree list` to resolve the documented CineForge sidequest.
   - Require the selected task, prompt, scorer, golden, provider, result
     directory, and `docs/evals/registry.yaml` in that same checkout. Do not
     trust a remembered absolute path or combine separate worktrees.
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

3. `[script]` Run the eval in the resolved checkout's `benchmarks/` subshell
   through that checkout's provider-env wrapper. Start at concurrency one and
   filter to the declared subject/comparator arms.

```bash
CINEFORGE_ROOT=/absolute/path/to/the/selected/cine-forge-checkout
CINEFORGE_PYTHON=/absolute/path/to/a/cine-forge-python
(
  cd "$CINEFORGE_ROOT/benchmarks"
  PROMPTFOO_PYTHON="$CINEFORGE_PYTHON" \
    "$CINEFORGE_PYTHON" "$CINEFORGE_ROOT/scripts/with_cine_forge_provider_env.py" \
    promptfoo eval -c tasks/<eval>.yaml --no-cache \
    --filter-providers '<declared-filter>' -j 1
)
```

Save results explicitly when you need a named artifact:

```bash
(
  cd "$CINEFORGE_ROOT/benchmarks"
  PROMPTFOO_PYTHON="$CINEFORGE_PYTHON" \
    "$CINEFORGE_PYTHON" "$CINEFORGE_ROOT/scripts/with_cine_forge_provider_env.py" \
    promptfoo eval -c tasks/<eval>.yaml --no-cache \
    --filter-providers '<declared-filter>' -j 1 \
    --output results/<run-name>.json
)
```

Raise concurrency only after provider limits are verified, and do not exceed
the repo norm without a separate throughput experiment. Use `--filter-first-n
1` for the first harness smoke. Preserve distinct output names for force-fresh
runs.

4. `[script]` Return to the selected checkout root and inspect metrics there.

```bash
"$CINEFORGE_PYTHON" "$CINEFORGE_ROOT/scripts/extract-eval-metrics.py" \
  --result-file "$CINEFORGE_ROOT/benchmarks/results/<run-name>.json"
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
(
  cd "$CINEFORGE_ROOT"
  PYTHONPATH=src "$CINEFORGE_PYTHON" scripts/extract-eval-metrics.py \
    --update-registry --dry-run \
    --result-file benchmarks/results/<run-name>.json
  PYTHONPATH=src "$CINEFORGE_PYTHON" scripts/extract-eval-metrics.py \
    --update-registry \
    --result-file benchmarks/results/<run-name>.json
)
```

   - The update must fail if the result's provider/model/call identity, task
     config, prompt bytes, rubric, grader, or case matrix is stale or incomplete.
   - confirm the staged row records score, latency, cost, `git_sha`, and result
     file; for visual evidence, confirm the retained-media path and digest
   - add an attempt summary when the run was part of an improvement loop
   - for dirty eval/provider code, record the base SHA plus hashes or patches
     for every relevant changed file and ignored raw artifact; base SHA alone
     is not exact provenance

6. `[judgment]` Classify significant mismatches before closing the work.
   - `model-wrong`
   - `golden-wrong`
   - `ambiguous`
   - for compromise/detection evals, also record `runtime-blocking` vs
     `non-runtime-blocking`

7. `[judgment]` Protect decision semantics.
   - Read the current target from the registry; do not reuse historical gates.
   - Compare a model-slot challenger with both the executable runtime default
     and best eligible maintained evidence. Treat slots independently.
   - Use both the maintained structural scorer and semantic rubric, and record
     judge-provider/capability bias. A same-provider judge is not sole evidence
     for a marginal decision-changing result.
   - Keep historical Story 208 `qa-pass` and `video-understanding` rows
     quarantined. Use only later rows explicitly marked decision-grade after
     source-backed repair and clean revalidation.

## Boundaries

### Always do

- run Promptfoo in the selected checkout's `benchmarks/` subshell, then run
  registry extraction from that checkout's repository root
- load provider variables through `scripts/with_cine_forge_provider_env.py`
- set explicit output files for named benchmark artifacts
- qualify exact served identity and the production schema/modality before
  treating a result as scoreable
- update the registry whenever you run an eval
- use one explicit result file and validate it against the current task before
  changing current score evidence
- retain every nondeterministic visual/media input whose bytes influenced a
  decision-grade score, even though candidates remain distinct from goldens

### Ask first

- benchmark workspace path cannot be resolved
- the task appears to require a second benchmark system instead of promptfoo
- a provider call would exceed the `/evaluate-model` spend or privacy boundary

### Never do

- assume the benchmark workspace is in the current checkout if you have not
  verified it
- expose or copy credentials instead of using the CineForge env wrapper
- treat HTTP success, prompt-only JSON, or a parsed cleanup result as proof of
  production-contract parity
- treat a red compromise/detection eval as automatically blocking without
  mismatch classification
- bulk-update registry rows from a directory of unrelated retained results
- promote a dirty-contract, duplicate-key, stale-task, or non-replayable result
  as decision-grade evidence
- treat a hash-only manifest in an ignored directory as recoverable visual
  evidence
- use quarantined QA/video raw scores for a model decision
- leave scores stale after a real eval run

## Troubleshooting

- If `promptfoo` cannot write under your normal home directory, set a repo-local
  `PROMPTFOO_HOME` for the run and record that choice in the work log.
- If you want npm release-age gating for global `promptfoo` updates, set it in
  `~/.npmrc`; this repo cannot enforce that knob for a global install.
- If a config looks valid but the model returns truncated JSON, check output
  token caps, thinking-token usage, finish reason, and provider-native schema
  flags before concluding the model is weak.
- If a native probe works but Promptfoo fails, inspect the API family, request
  shape, env-wrapper ownership, cache key, and served-model metadata before
  changing the semantic prompt.
- If a challenger appears to win, verify the runtime default, best eligible
  maintained result, judge bias, current target, and fixture health before
  recommending adoption.
- If the benchmark workspace is missing entirely, restore or create it through
  `/setup-methodology refresh` before adding new promptfoo tasks.

## Lessons Learned

- 2026-03-20 — CineForge's promptfoo lane may use a documented sidequest
  workspace. Resolve it from current worktree state instead of assuming a
  stable absolute path.
- 2026-07-22 — Story 208 consolidated the truth boundary: maintained promptfoo
  contracts and the registry must be read from the same exact CineForge
  checkout. A historical sidequest path by itself is not provenance.
- 2026-07-22 — Prefer the current checkout when it actually contains the
  selected benchmark files, and otherwise resolve a sidequest from current
  worktree state. Always use the CineForge env wrapper and qualify transport
  before interpreting scores.
- 2026-07-22 — Story 208 proved that QA/video golden contamination can invert a
  model verdict. Quarantine those rows until repaired rather than compounding
  them with more subject runs.

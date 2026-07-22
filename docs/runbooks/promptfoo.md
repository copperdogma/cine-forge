# Runbook: Promptfoo

> Run, inspect, and record CineForge promptfoo evals.

## Context

CineForge uses promptfoo for model/prompt benchmarking across pipeline tasks.
The benchmark workspace is the verified CineForge checkout containing the
selected task and its prompt/scorer/golden. It may be the current checkout or a
separate sidequest worktree; resolve it from live worktree state as documented
in `AGENTS.md`.

Use this runbook when creating, running, or recording promptfoo-based evals.
For an end-to-end new/repeated/multi-model decision, start with
`/evaluate-model`; this runbook is its mechanical Promptfoo layer.

## Prerequisites

- Node.js 24 LTS available via `nvm`
- `promptfoo` installed globally
- provider credentials loadable through the selected checkout's env wrapper
- access to the benchmark workspace that contains `benchmarks/tasks/`
- access to that checkout's `scripts/with_cine_forge_provider_env.py`
- `docs/evals/registry.yaml` available in the main repo
- If you want a freshness delay for the global `promptfoo` install, configure it in `~/.npmrc`; repo-local npm config does not reliably govern global installs

## Steps

1. `[judgment]` Resolve the benchmark workspace.
   - If the current checkout already has `benchmarks/`, use it.
   - Otherwise inspect `git worktree list` and resolve the documented CineForge
     sidequest checkout.
   - Verify the selected task, prompt, scorer, golden, provider, and result
     directory all belong to the intended code state. Do not trust a remembered
     absolute path.

2. `[script]` Load the Node toolchain.

```bash
source ~/.nvm/nvm.sh && nvm use 24 > /dev/null 2>&1
```

3. `[script]` Run the eval from the resolved `benchmarks/` directory through
   the owning checkout's provider-env wrapper. Start at concurrency one and
   filter to the declared subject/comparator arms.

```bash
CINEFORGE_ROOT=/absolute/path/to/the/selected/cine-forge-checkout
CINEFORGE_PYTHON=/absolute/path/to/a/cine-forge-python
PROMPTFOO_PYTHON="$CINEFORGE_PYTHON" \
  "$CINEFORGE_PYTHON" "$CINEFORGE_ROOT/scripts/with_cine_forge_provider_env.py" \
  promptfoo eval -c tasks/<eval>.yaml --no-cache \
  --filter-providers '<declared-filter>' -j 1
```

Save results explicitly when you need a named artifact:

```bash
PROMPTFOO_PYTHON="$CINEFORGE_PYTHON" \
  "$CINEFORGE_PYTHON" "$CINEFORGE_ROOT/scripts/with_cine_forge_provider_env.py" \
  promptfoo eval -c tasks/<eval>.yaml --no-cache \
  --filter-providers '<declared-filter>' -j 1 \
  --output results/<run-name>.json
```

Raise concurrency only after provider limits are verified, and do not exceed
the repo norm without a separate throughput experiment. Use `--filter-first-n
1` for the first harness smoke. Preserve distinct output names for force-fresh
runs.

4. `[script]` Extract metrics back in the main repo.

```bash
"$CINEFORGE_PYTHON" "$CINEFORGE_ROOT/scripts/extract-eval-metrics.py" \
  --result-file "$CINEFORGE_ROOT/benchmarks/results/<run-name>.json"
```

5. `[script]` Update `docs/evals/registry.yaml`.
   - record score, latency, cost, `git_sha`, and result file
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
   - While Story 208/registry contamination notes remain current, quarantine
     raw `qa-pass` and `video-understanding` scores from adoption/default/
     compromise decisions until source-backed repair and revalidation.

## Boundaries

### Always do

- run promptfoo from the `benchmarks/` directory
- load provider variables through `scripts/with_cine_forge_provider_env.py`
- set explicit output files for named benchmark artifacts
- qualify exact served identity and the production schema/modality before
  treating a result as scoreable
- update the registry whenever you run an eval

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
  workspace. Runbooks and skills must resolve the checkout containing the
  selected benchmark files instead of pretending there is one stable absolute
  path.
- 2026-07-22 — Prefer the current checkout when it actually contains the
  selected benchmark files, and otherwise resolve a sidequest from current
  worktree state. Always use the CineForge env wrapper and qualify transport
  before interpreting scores.
- 2026-07-22 — Story 208 proved that QA/video golden contamination can invert a
  model verdict. Quarantine those rows until repaired rather than compounding
  them with more subject runs.

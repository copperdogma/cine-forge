# Runbook: Create Eval

> Scaffold a new CineForge eval in the registry and benchmark workspace.
> Use this runbook with `/create-eval`.

## Context

`/create-eval` is the day-to-day front door for **new eval creation** after the
baseline methodology package already exists. It is separate from
`/setup-methodology` and from `/improve-eval`:

- `/setup-methodology` installs the eval/golden baseline
- `/create-eval` scaffolds a new eval
- `/improve-eval` iterates on an existing eval

## Prerequisites

- `docs/evals/registry.yaml` exists
- `docs/evals/README.md` exists
- the current checkout contains both `benchmarks/` and the eval registry
- relevant story / spec / methodology-category context exists for the new eval

## Steps

1. `[judgment]` Read the methodology context.
   - `docs/ideal.md`
   - relevant `spec:N` sections
   - relevant methodology category (`docs/methodology/state.yaml` or generated
     dashboard view)
   - linked ADRs / design docs

2. `[judgment]` Classify the eval.
   - `quality` vs `compromise`
   - promptfoo vs custom runner
   - runtime/capability/deletion-gate intent

3. `[judgment]` Resolve the benchmark workspace.
   - require `benchmarks/` and `docs/evals/registry.yaml` in the same checkout
   - if either is missing, restore the methodology package or ask for the
     intended checkout; do not mix a sibling worktree's contracts

4. `[script]` Scaffold the registry entry.
   - add a full entry in `docs/evals/registry.yaml`
   - include command, config/script path, target metric, and linkage notes

5. `[script]` Scaffold the implementation files.
   - create the task config or script stub in the benchmark workspace
   - reuse the existing naming/layout conventions under `benchmarks/`

6. `[script]` Verify the scaffold.
   - referenced paths exist
   - runner choice matches the task
   - the eval can be handed off to `/improve-eval`

## Boundaries

### Always do

- Link every new eval to a story, `spec:N`, and methodology category
- Reuse the existing benchmark layout before inventing a new one
- Keep registry entries complete from the start

### Ask first

- Benchmark-workspace path cannot be resolved confidently
- The new eval would require a second incompatible benchmark system

### Never do

- Start optimization work inside `/create-eval`
- Create an eval with no methodology anchor
- Leave the registry entry partial

## Troubleshooting

- Keep task contracts and the registry in the same checkout. Registry paths use
  the repo-relative `benchmarks/...` shape; never bake in a machine-local path or
  point at a sibling worktree's bytes.
- If the task looks like "rerun or tune an existing eval", use `/improve-eval`
  instead.
- If the repo is missing its eval/golden baseline entirely, use
  `/setup-methodology refresh` first.

## Lessons Learned

- 2026-03-20 — CineForge split "create a new eval" from "improve an existing
  eval" so new tasks stop overloading `/improve-eval` and the registry/workspace
  linkage is explicit from the start.

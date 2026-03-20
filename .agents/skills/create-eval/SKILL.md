---
name: create-eval
description: Scaffold a new CineForge eval in the registry and benchmark workspace, linked to the relevant story, spec compromise, and build-map category
user-invocable: true
---

# /create-eval [eval-id or short description]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/build-map.md`, and relevant decision records in `docs/decisions/` / `docs/design/`. If none apply, say so explicitly.

Create a **new eval scaffold**. Baseline eval/golden setup belongs to
`/setup-methodology`; once that package exists, `/create-eval` is the recurring
front door for adding a new eval. Use `/improve-eval` only after the eval
already exists.

Companion runbook: `docs/runbooks/create-eval.md`

## Workspace Assumptions

Use the repo-equivalent paths if the benchmark workspace is laid out
differently, but do not invent a second eval surface if the documented one
already fits.

- Registry: `docs/evals/registry.yaml`
- Eval docs / protocol: `docs/evals/README.md`
- Attempt template: `docs/evals/attempt-template.md`
- Promptfoo operations: `docs/runbooks/promptfoo.md`
- Benchmark workspace: the sidequest promptfoo worktree described in `AGENTS.md`
- Benchmark layout inside that workspace:
  - `benchmarks/tasks/`
  - `benchmarks/prompts/`
  - `benchmarks/scorers/`
  - `benchmarks/golden/`
  - `benchmarks/results/`

## Steps

1. **Read context first**
   - `docs/ideal.md`
   - relevant `spec:N` sections and build-map category
   - linked ADRs / design docs
   - `docs/evals/README.md`
   - `docs/runbooks/promptfoo.md` if the eval is prompt-based

2. **Classify the eval**
   - Choose registry `type`: `quality` or `compromise`
   - Derive the intent from that type + context:
     - `quality-runtime` — model / cost / latency trade-off
     - `quality-capability` — feature quality gate
     - `compromise-detection` — deletion gate for a spec compromise

3. **Choose the runner**
   - `promptfoo` for prompt/model comparisons and rubric-scored outputs
   - `custom` for runtime / contract / system-level checks
   - Reuse the existing benchmark layout before inventing a second one

4. **Resolve the benchmark workspace**
   - If the current checkout already contains the `benchmarks/` tree, use it
   - Otherwise use the documented sidequest benchmark worktree contract from
     `AGENTS.md`
   - If the workspace cannot be found confidently, stop and ask for the path
     instead of hardcoding a guess

5. **Scaffold the registry entry**
   - Add a full entry in `docs/evals/registry.yaml`
   - Include command, config/script path, target metric, and linkage notes
   - If the eval is a compromise gate, make the linked compromise explicit

6. **Scaffold the implementation files**
   - Create the task config or script stub in the benchmark workspace
   - Point to prompts, scorers, and golden fixtures using the current layout
   - Reuse existing helpers and naming patterns when possible

7. **Link the eval to the methodology graph**
   - owning story or story draft
   - relevant `spec:N` or compromise ID
   - relevant build-map category / phase
   - any fixture or golden IDs the eval depends on

8. **Verify the scaffold**
   - paths referenced in the registry exist
   - runner choice matches the actual task
   - the new eval can be handed off cleanly to `/improve-eval`

## Guardrails

- Do not run the `/improve-eval` optimization loop here.
- Do not create an eval with no story / spec / build-map anchor.
- Do not invent a second eval layout when the sidequest benchmark workspace
  already fits the task.
- Do not leave the registry entry partial; a new eval is not created until the
  registry has a real entry.

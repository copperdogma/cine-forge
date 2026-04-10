---
name: setup-methodology
description: Canonical bootstrap for the CineForge methodology package — docs, checklist, eval/golden baseline, story wiring, and public skill surface
user-invocable: true
---

# /setup-methodology [greenfield|retrofit|refresh]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`, generated graph surfaces under `docs/methodology/`, and relevant decision records in `docs/decisions/` / `docs/design/`. If none apply, say so explicitly.

Use this skill as the **single public bootstrap entrypoint** for CineForge's
methodology package. It replaces the old phased setup surface with one
integrated flow.

Companion runbook: `docs/runbooks/setup-methodology.md`

Use the bundled checklist template at
`.agents/skills/setup-methodology/templates/setup-checklist.md` and the mode
reference at `.agents/skills/setup-methodology/references/modes.md`.

## What This Skill Owns

- `docs/ideal.md` / `docs/spec.md` / `docs/methodology/state.yaml` alignment
- `docs/setup-checklist.md` working-copy generation from the bundled template
- generated methodology surfaces (`docs/build-map.md`, `docs/stories.md`, `docs/methodology/graph.json`)
- baseline golden + eval setup, including CineForge's sidequest benchmark lane
- story / planning bootstrap guidance
- optional recurring methodology lanes already encoded in the package, such as
  `ui_scout` plus its history and runbook surfaces
- `AGENTS.md` methodology wiring and canonical public surface
- cross-CLI skill sync via `scripts/sync-agent-skills.sh`

## Modes

### `greenfield`

For a new repo or fresh skeleton. Install the full methodology package:
ideal/spec/state/checklist, generated graph surfaces, eval + golden baseline,
story bootstrap, and canonical skill surface.

### `retrofit`

For an existing repo that needs the methodology package applied or re-applied.
Read the repo first, preserve provenance, and normalize the package without
rewriting valid project-specific content.

### `refresh`

For a repo that already has the package but has drifted. Refresh the checklist,
AGENTS wiring, runbooks, eval/golden references, and public surface without
redoing the entire methodology conversation.

## Working Rules

1. **Create or refresh the checklist first.** `docs/setup-checklist.md` is the
   active working copy for setup/migration/refresh passes.
2. **State-first operating rule:** planning and triage start from
   `docs/methodology/state.yaml`, then compile the generated dashboard views.
   Implementation starts from the active story, but must read the relevant
   `spec:N` category, state lane, and linked ADRs first.
3. **Treat goldens and evals as baseline setup.** The methodology package is not
   fully installed until the repo has both the golden workspace and the eval
   registry / benchmark workflow.
4. **Keep recurring work separate.** After the package exists, ongoing eval work
   should flow through `/create-eval`, `/improve-eval`, `/align`, the local
   `ui-scout` lane when `state.ui_scout` exists, and the normal
   story/build/validate/close-out skills.
5. **Canonical public surface only.** AGENTS/docs should advertise
   `/setup-methodology` as the setup front door. Remove deprecated phased setup
   skills instead of keeping hidden aliases around.

## Steps

1. **Determine mode from repo reality**
   - Verify whether the repo is greenfield, retrofit, or refresh.
   - If the user supplied a mode, confirm it matches the actual repo state.

2. **Read the canonical references**
   - `docs/runbooks/setup-methodology.md`
   - `docs/methodology-ideal-spec-compromise.md`
   - `docs/methodology/state.yaml`
   - generated dashboards (`docs/build-map.md`, `docs/stories.md`) if present
   - `AGENTS.md`
   - relevant ADRs / design docs if the current drift involves workflow,
     architecture, schema, or UX decisions
   - existing setup/eval/golden/story docs if present

3. **Create or refresh `docs/setup-checklist.md`**
   - Copy the bundled template if the file is missing or still reflects the old
     one-off retrofit format
   - Preserve historical context instead of deleting it blindly
   - Check items off as the run proceeds

4. **Install or refresh the methodology package**
   - Ensure `docs/ideal.md`, `docs/spec.md`, and `docs/methodology/state.yaml`
     describe the same system
   - Run `pnpm methodology:compile` after metadata changes so generated
     dashboards stay current
   - Add or refresh `docs/runbooks/setup-methodology.md`
   - When `state.ui_scout` exists, keep `docs/ui-scout.md`,
     `docs/runbooks/full-pipeline-ui-manual-walkthrough.md`, and the AGENTS
     routing aligned with the package
   - Update `AGENTS.md` so the repo teaches the current hierarchy and public
     skill surface

5. **Bootstrap baseline evidence infrastructure**
   - Ensure the golden workspace exists and matches current schemas
   - Ensure `docs/evals/README.md`, `docs/evals/registry.yaml`, and
     `docs/evals/attempt-template.md` are current
   - If the repo uses promptfoo-style evals, ensure `docs/runbooks/promptfoo.md`
     exists and matches the actual benchmark workspace layout
   - Ensure `/create-eval` and `/improve-eval` cover new-eval creation vs
     existing-eval iteration cleanly

6. **Normalize the public setup surface**
   - `/setup-methodology` is the advertised setup entrypoint
   - deprecated phased setup skills are removed from the repo
   - `ui_scout` is documented only when the package includes the UI
     product-truth lane
   - `init-project` installs the same package for new repos
   - run `scripts/sync-agent-skills.sh`
   - validate with `scripts/sync-agent-skills.sh --check`

7. **Audit and summarize**
   - search for stale phased-setup language in AGENTS, runbooks, and active
     skills
   - confirm eval creation vs improvement paths are clearly separated
   - perform a short alignment sweep across Ideal / Spec / State / Generated
     Dashboards / Stories / Evals / AGENTS

## Outputs

- canonical setup skill surface installed
- working copy of `docs/setup-checklist.md`
- runbook + AGENTS docs aligned to the same package
- generated methodology dashboards refreshed from the compiler
- baseline golden/eval/story bootstrap included
- cross-CLI wrappers regenerated and checked

## Guardrails

- Do not teach multiple competing setup models in AGENTS or runbooks.
- Do not leave deprecated phased setup skills in place as hidden aliases.
- Do not split methodology bootstrap from golden/eval baseline unless the user
  explicitly chooses to defer it.
- Do not hardcode a benchmark-worktree path you cannot verify; use the documented
  sidequest workspace contract instead.

# Runbook: Setup Methodology

> Canonical guide for CineForge's methodology package.
> Use this runbook with `/setup-methodology`.

## Context

CineForge no longer treats setup as a loose chain of public one-off skills.
The methodology is an integrated package:

- dual ideal (`docs/ideal.md`)
- category-aligned spec (`docs/spec.md`)
- canonical methodology state (`docs/methodology/state.yaml`)
- compiled graph + generated dashboards (`docs/build-map.md`, `docs/stories.md`)
- baseline golden + eval setup
- story / planning bootstrap
- AGENTS wiring and cross-CLI skill sync

The package works because those artifacts describe the same system from
different angles. Teaching them as unrelated public entrypoints created drift
and made the bootstrap surface harder to follow than the methodology itself.

## Prerequisites

- Read `AGENTS.md`
- Read `docs/methodology-ideal-spec-compromise.md`
- Read `docs/methodology/state.yaml`
- Read generated dashboards if present (`docs/build-map.md`, `docs/stories.md`)
- Read relevant ADRs / design docs if the current drift touches workflow,
  architecture, schema, or UX

## Public Surface

### Bootstrap

- `/setup-methodology` — the canonical setup entrypoint

Modes:
- `greenfield`
- `retrofit`
- `refresh`

### Recurring Day-to-Day Skills

- `/create-eval` — scaffold a new eval
- `/improve-eval` — iterate on an existing eval
- `/align` — sweep the methodology graph for drift
- UI product-truth scouting via `docs/ui-scout.md` +
  `docs/runbooks/full-pipeline-ui-manual-walkthrough.md` when `state.ui_scout`
  is part of the package
- the normal story / build / validate / close-out skills

### Removed Old Surface

Older phased setup skills are removed from the repo. If older notes mention
them, use `/setup-methodology` instead.

## Steps

1. `[judgment]` Determine mode from repo reality.
   - `greenfield`: new repo or light scaffold
   - `retrofit`: meaningful existing docs/code/stories need package alignment
   - `refresh`: package exists but docs / skill surface have drifted

2. `[script]` Create or refresh the working checklist.
   - Use `.agents/skills/setup-methodology/templates/setup-checklist.md`
   - Copy it to `docs/setup-checklist.md` if the current file is missing or stale

3. `[judgment]` Align the methodology graph.
   - `docs/ideal.md`, `docs/spec.md`, and `docs/methodology/state.yaml` should
     describe the same system and hierarchy
   - `pnpm methodology:compile` should refresh the generated dashboards after
     metadata or state changes
   - `AGENTS.md` should teach the same hierarchy and public surface

4. `[judgment]` Confirm baseline evidence setup.
   - golden workspace exists and matches current schemas
   - eval registry and attempt template exist
   - promptfoo workflow is documented if the repo uses it
   - `/create-eval` and `/improve-eval` split creation vs iteration cleanly

5. `[judgment]` Keep optional recurring lanes honest.
   - If `state.ui_scout` exists, `docs/ui-scout.md`,
     `docs/runbooks/full-pipeline-ui-manual-walkthrough.md`, and the AGENTS
     routing should stay aligned with that lane
   - Do not add UI-scout boilerplate to repos that do not use the lane

6. `[judgment]` Normalize the setup surface.
   - `/setup-methodology` is the advertised setup entrypoint
   - phased setup skills are removed rather than kept as hidden aliases
   - `init-project` installs the same package

7. `[script]` Sync the skill wrappers.
   - `./scripts/sync-agent-skills.sh`
   - `./scripts/sync-agent-skills.sh --check`

8. `[script]` Audit for stale surface drift.
   - run `rg` across `AGENTS.md`, `docs/`, and `.agents/skills/` for the old
     phased setup names
   - run `pnpm methodology:check` after rewiring active methodology surfaces

## Boundaries

### Always do

- Use `docs/setup-checklist.md` as the working copy
- Treat evals and goldens as baseline setup, not optional later polish
- Keep AGENTS, runbooks, and skills teaching the same public surface
- Keep optional recurring lanes such as `ui_scout` aligned when the repo uses
  them
- Keep authored state separate from generated views

### Ask first

- Rewriting valid project-specific methodology content instead of refreshing its packaging

### Never do

- Teach multiple competing setup models in AGENTS or runbooks
- Hardcode an unverifiable benchmark-worktree path
- Split methodology bootstrap from golden/eval baseline by accident

## Troubleshooting

- If `docs/setup-checklist.md` contains historical retrofit notes, preserve them
  and add the new working-copy structure above them instead of deleting context.
- If the benchmark workspace is outside the current checkout, document the
  sidequest-worktree contract rather than inventing a fake in-repo path.
- If stale setup references remain after sync, audit AGENTS, runbooks, and
  user-invocable skills first; historical scout docs and old story files may
  remain untouched.
- If generated dashboards look wrong, fix canonical inputs first
  (`state.yaml`, story metadata, ADR metadata) and rerun
  `pnpm methodology:compile` instead of patching the generated files directly.

## Lessons Learned

- 2026-03-20 — CineForge adopted `/setup-methodology` as the canonical setup
  entrypoint.
- 2026-03-20 — User-directed cleanup removed the deprecated phased setup skills
  entirely so the repo no longer teaches or carries a second setup surface.

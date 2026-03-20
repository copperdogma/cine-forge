# Scout 015 — storybook-dossier-methodology-delta

**Sources:** `/Users/cam/Documents/Projects/Storybook/storybook`, `/Users/cam/Documents/Projects/dossier`
**Scouted:** 2026-03-20
**Scope:** Storybook changes since Scout 013 focused on the ADR-021 methodology bootstrap consolidation and new eval-entrypoint surface; Dossier changes focused on `/scout` upgrades for concrete pattern ports
**Previous:** Scout 013 (Storybook, Dossier, codex-forge agent updates, 2026-03-13) and Scout 014 (Dossier finish-and-push, 2026-03-18)
**Status:** Complete
**Alignment:** No local ADR directly governs CineForge's methodology-bootstrap or scout-artifact surfaces. The closest local anchors are `docs/methodology-ideal-spec-compromise.md`, `docs/build-map.md`, `docs/setup-checklist.md`, `docs/evals/README.md`, and the existing scout/runbook rules in `AGENTS.md`.

## Findings

1. **A single `/setup-methodology` package would replace CineForge's fragmented setup surface with one canonical bootstrap contract** — HIGH value
   What: Storybook commit `de2a224` replaces the phased setup surface with one `/setup-methodology` package that owns the methodology bootstrap end to end: ideal/spec/build-map alignment, checklist generation, golden+eval baseline setup, story bootstrap, AGENTS wiring, and cross-CLI sync. It ships as a skill package with a companion runbook and a bundled checklist template, not as a loose pile of setup skills.
   Us: CineForge still exposes eight separate setup entrypoints (`setup-env-ai`, `setup-env-dev`, `setup-eval-registry`, `setup-evals`, `setup-golden`, `setup-ideal`, `setup-spec`, `setup-stories`) plus a historical retrofit checklist. The methodology itself is strong, but the public bootstrap surface teaches multiple models at once and leaves no single "this is the canonical way to install or refresh the methodology package" entrypoint.
   Recommendation: **Adopt inline** — implemented here as a CineForge-specific methodology package adaptation. The port kept Storybook's single-entrypoint contract, translated it to CineForge's promptfoo workspace and existing methodology docs, and then removed the deprecated phased setup skills entirely.
   Transfusion:
   Exemplar: Storybook's `.agents/skills/setup-methodology/` package plus `docs/runbooks/setup-methodology.md`
   Invariant: One canonical bootstrap entrypoint owns the methodology package instead of scattering setup across unrelated skills
   Adaptation: CineForge must account for its separate promptfoo sidequest workspace, existing `setup-env-*` / `setup-eval-registry` surfaces, and current retrofit checklist history instead of bulk-copying Storybook's public surface
   Proof target: AGENTS/docs point to one canonical methodology-bootstrap entrypoint, and the skill, runbook, checklist, and setup references all teach the same package

2. **`/create-eval` is the missing day-to-day front door for adding new evals after baseline setup exists** — HIGH value
   What: Storybook added `/create-eval` as the recurring new-eval entrypoint. It is explicitly separate from the baseline setup package and from `/improve-eval`: bootstrap establishes the eval system, `/create-eval` scaffolds a new eval anchored to registry/spec/build-map/story context, and `/improve-eval` iterates on existing evals.
   Us: CineForge already has strong eval improvement and registry discipline (`/improve-eval`, `docs/evals/README.md`, `docs/evals/registry.yaml`) but no dedicated "create a new eval" skill. New eval creation is currently implicit and easy to do inconsistently, especially because the runnable promptfoo workspace lives in the sidequests worktree rather than this repo.
   Recommendation: **Adopt inline** — add a CineForge-specific `/create-eval` plus a companion runbook/docs update that points to the sidequests promptfoo workspace and our existing registry/update rules.
   Transfusion:
   Exemplar: Storybook's `.agents/skills/create-eval/SKILL.md`
   Invariant: New evals must have a real methodology anchor before implementation starts: registry entry, story/spec/build-map linkage, and a clear runner choice
   Adaptation: The skill must target CineForge's external `benchmarks/` worktree layout and current promptfoo conventions instead of Storybook's in-repo eval paths
   Proof target: An agent can scaffold a new CineForge eval without overloading `/setup-evals` or `/improve-eval`, and the resulting instructions point to the correct registry/worktree surfaces

3. **Scout artifacts should record exemplar-transfer intent when a finding is a real port, not just an inspiration** — MEDIUM value
   What: Dossier commit `864cc2c` upgraded `/scout` and its expedition template with optional `Exemplar`, `Invariant`, `Adaptation`, and `Proof target` fields for concrete pattern transfers. The same template also adds explicit `Verification` and `Evidence` sections so ports leave a clearer audit trail.
   Us: CineForge already uses scouts as the main cross-repo adoption mechanism, but our scout docs stop at findings / approved / skipped. That works for pure research, but it obscures what behavior we meant to preserve when a finding becomes a real pattern port.
   Recommendation: **Adopt inline** — small, local scout-surface improvement with clear value for future cross-repo ports and close-out evidence.
   Transfusion:
   Exemplar: Dossier's updated `/scout` skill and scout-expedition template
   Invariant: Concrete pattern transfers should preserve the portable behavior, not just note that another repo had an interesting idea
   Adaptation: Keep the fields optional so pure research passes and skip items do not become noisier
   Proof target: Future CineForge scout docs only add transfusion metadata for real port candidates, and approved ports have explicit verification/evidence slots

## Approved

- [x] 1. `/setup-methodology` package consolidation — Approved for inline adaptation by user on 2026-03-20
- [x] 2. `/create-eval` skill + runbook adaptation — Approved for inline implementation by user on 2026-03-20
- [x] 3. Scout gene-transfusion + verification/evidence template upgrade — Approved for inline implementation by user on 2026-03-20

## Implementation Checklist

- [x] Confirm local alignment context and whether any CineForge ADR directly governs this surface
- [x] Add `.agents/skills/setup-methodology/` package (`SKILL.md`, `references/modes.md`, `templates/setup-checklist.md`)
- [x] Add `docs/runbooks/setup-methodology.md`
- [x] Remove phased setup skills and refresh live references to the canonical surface
- [x] Refresh `docs/setup-checklist.md` to the methodology-package working-copy format while preserving historical retrofit context
- [x] Update `AGENTS.md`, `init-project`, and golden-workspace references to advertise the canonical setup/eval surface
- [x] Add `.agents/skills/create-eval/SKILL.md`
- [x] Add `docs/runbooks/create-eval.md`
- [x] Add `docs/runbooks/promptfoo.md` and refresh `docs/evals/README.md` for the new baseline vs day-to-day split
- [x] Upgrade `/scout` and the scout expedition template with optional transfusion, verification, and evidence sections
- [x] Run `./scripts/sync-agent-skills.sh`
- [x] Run `./scripts/sync-agent-skills.sh --check`
- [x] Re-read modified files, update scout evidence, and add Scout 015 to `docs/scout.md`

## Skipped / Rejected

- None yet

## Verification

- Read `docs/scout.md`, [docs/scout/scout-013-storybook-dossier-codex-forge-agent-updates.md](/Users/cam/.codex/worktrees/ba9c/cine-forge/docs/scout/scout-013-storybook-dossier-codex-forge-agent-updates.md), and [docs/scout/scout-014-dossier-finish-and-push.md](/Users/cam/.codex/worktrees/ba9c/cine-forge/docs/scout/scout-014-dossier-finish-and-push.md)
- Reviewed Storybook commits `0de4719` and `de2a224` plus their touched methodology files
- Reviewed Dossier commit `864cc2c` plus its scout artifact updates
- Compared CineForge's current setup/eval/scout surfaces: `.agents/skills/setup-*`, `.agents/skills/init-project/SKILL.md`, `docs/setup-checklist.md`, `docs/evals/README.md`, and `.agents/skills/scout/`
- Ran `./scripts/sync-agent-skills.sh` and confirmed the new public surfaces synced across CLI wrappers
- Ran `./scripts/sync-agent-skills.sh --check` serially after sync and got a clean wrapper/skill inventory
- Ran `git diff --check` and re-read the rewritten package/docs tails (`init-project`, `docs/evals/README.md`, `docs/setup-checklist.md`) to catch malformed endings
- Removed the deprecated phased setup skill files, refreshed the remaining active references, and verified `docs/runbooks/golden-build.md` no longer carries the old `setup-golden` note

## Evidence

- Storybook files reviewed:
  - `/Users/cam/Documents/Projects/Storybook/storybook/.agents/skills/setup-methodology/SKILL.md`
  - `/Users/cam/Documents/Projects/Storybook/storybook/.agents/skills/create-eval/SKILL.md`
  - `/Users/cam/Documents/Projects/Storybook/storybook/docs/runbooks/setup-methodology.md`
  - `/Users/cam/Documents/Projects/Storybook/storybook/docs/decisions/adr-021-execution-ideal-build-constraints/adr.md`
- Dossier files reviewed:
  - `/Users/cam/Documents/Projects/dossier/.agents/skills/scout/SKILL.md`
  - `/Users/cam/Documents/Projects/dossier/.agents/skills/scout/templates/scout-expedition.md`
  - `/Users/cam/Documents/Projects/dossier/docs/scout/scout-009-software-factory.md`
- CineForge comparison points:
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/.agents/skills/init-project/SKILL.md`
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/.agents/skills/improve-eval/SKILL.md`
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/.agents/skills/scout/SKILL.md`
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/docs/evals/README.md`
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/docs/setup-checklist.md`
- CineForge files removed:
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/.agents/skills/setup-env-ai/SKILL.md`
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/.agents/skills/setup-env-dev/SKILL.md`
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/.agents/skills/setup-eval-registry/SKILL.md`
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/.agents/skills/setup-evals/SKILL.md`
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/.agents/skills/setup-golden/SKILL.md`
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/.agents/skills/setup-ideal/SKILL.md`
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/.agents/skills/setup-spec/SKILL.md`
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/.agents/skills/setup-stories/SKILL.md`
- CineForge files added:
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/.agents/skills/setup-methodology/SKILL.md`
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/.agents/skills/setup-methodology/references/modes.md`
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/.agents/skills/setup-methodology/templates/setup-checklist.md`
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/.agents/skills/create-eval/SKILL.md`
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/docs/runbooks/setup-methodology.md`
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/docs/runbooks/create-eval.md`
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/docs/runbooks/promptfoo.md`
- CineForge files materially updated:
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/AGENTS.md`
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/.agents/skills/scout/SKILL.md`
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/.agents/skills/scout/templates/scout-expedition.md`
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/.agents/skills/init-project/SKILL.md`
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/.agents/skills/improve-eval/SKILL.md`
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/.agents/skills/golden-create/SKILL.md`
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/docs/evals/README.md`
  - `/Users/cam/.codex/worktrees/ba9c/cine-forge/docs/setup-checklist.md`

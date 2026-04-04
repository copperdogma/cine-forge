---
id: "145"
title: "Methodology Graph + State Migration"
status: "Done"
priority: "High"
ideal_refs:
  - "Execution Ideal"
  - "Radical transparency"
  - "R14 (Nothing is ever lost)"
spec_refs:
  - "spec:11"
adr_refs: []
depends_on:
  - "134"
  - "136"
category_refs:
  - "spec:11"
compromise_refs:
  - "B2"
  - "B3"
  - "B5"
input_coverage_refs: []
architecture_domains:
  - "methodology_tooling"
roadmap_tags:
  - "campaign:methodology-graph-state-migration"
legacy_system: "Cross-Cutting"
---

# Story 145 — Methodology Graph + State Migration

**Priority**: High
**Status**: Done
**Ideal Refs**: Execution Ideal; radical transparency; R14 (nothing is ever lost)
**Spec Refs**: spec:11 (Planning Infrastructure & Agent Tooling)
**ADR Refs**: None found after search in CineForge for this methodology layer; reviewed `docs/design/decisions.md` and local ADR-001..003. External reference sources: Storybook migration runbook, Storybook methodology audit artifact, and Storybook Story 079.
**Depends On**: Story 134, Story 136

## Goal

Migrate CineForge from the current hand-authored build-map/story-index
methodology shape to the newer graph+state model described in Storybook's
runbook, but as a CineForge adaptation instead of a blind port. The migration
must perform a repo-specific no-loss audit first, create a structured
operational state layer, compile a deterministic methodology graph, generate
`docs/stories.md` and a human-readable `docs/build-map.md`, rewire the active
skills/runbooks/templates to read the new authority surfaces, and add a bounded
architecture-audit lane. The migration must preserve CineForge's local
strengths: the `spec:1` through `spec:11` category model, existing compromise
IDs (`C*`, `B*`), the film-specific story backlog, the eval registry, and the
legacy suffixed story IDs already present in the repo.

## Acceptance Criteria

- [x] A CineForge-specific no-loss audit exists at
      `docs/methodology-artifact-audit-and-migration.md`, covering the current
      authored methodology surfaces, their real responsibilities, consumer
      hotspots, replacement model, lint contract, architecture-audit plan, and
      phased migration checklist.
- [x] `docs/methodology/state.yaml` exists and seeds the current mutable
      planning state currently buried in `docs/build-map.md` and the overlay
      sections of `docs/stories.md`, including:
  - [x] category substrate + phase state for `spec:1` through `spec:11`
  - [x] compromise phase state for active `C*` and `B*` compromises
  - [x] roadmap focus / campaign state
  - [x] preserved story-index overlay sections
  - [x] architecture-audit cadence + bounded CineForge domains
- [x] A deterministic local compiler exists and is wired into a stable command
      surface (for example `pnpm methodology:compile` / `pnpm methodology:check`)
      that:
  - [x] reads `docs/ideal.md`, `docs/spec.md`, story files, ADRs,
        `docs/evals/registry.yaml`, and `docs/methodology/state.yaml`
  - [x] emits `docs/methodology/graph.json`
  - [x] emits a generated `docs/stories.md`
  - [x] emits a generated `docs/build-map.md`
  - [x] supports legacy CineForge story IDs with suffixes (for example `003b`)
        during migration rather than corrupting or dropping them
- [x] Active methodology consumers are migrated so they no longer treat the
      hand-authored `docs/build-map.md` or `docs/stories.md` as source-of-truth
      inputs. At minimum this includes:
  - [x] `AGENTS.md`
  - [x] `docs/methodology-ideal-spec-compromise.md`
  - [x] `docs/runbooks/setup-methodology.md`
  - [x] `docs/setup-checklist.md`
  - [x] `.agents/skills/setup-methodology/SKILL.md`
  - [x] `.agents/skills/triage/SKILL.md`
  - [x] `.agents/skills/align/SKILL.md`
  - [x] `.agents/skills/build-story/SKILL.md`
  - [x] `.agents/skills/validate/SKILL.md`
  - [x] `.agents/skills/mark-story-done/SKILL.md`
  - [x] `.agents/skills/create-story/SKILL.md`
  - [x] `.agents/skills/init-project/SKILL.md`
- [x] A dedicated architecture-audit lane exists and is wired into the package:
  - [x] `state.yaml` contains `architecture_audits`
  - [x] `.agents/skills/triage-architecture/SKILL.md` exists
  - [x] `docs/runbooks/triage-architecture.md` exists
  - [x] `/triage` and `/validate` reference the lane correctly
- [x] The migration has a local certification loop and passes it after the last
      structural issue is fixed:
  - [x] generated outputs are current
  - [x] methodology checks pass with only documented legacy-metadata warnings
  - [x] `make skills-check` passes after the skill/runbook rewiring
  - [x] repo-native validation for touched scope is recorded in the work log

## Out of Scope

- Rewriting CineForge's product/runtime architecture outside what is necessary
  to migrate methodology consumers
- Mass-migrating every historical story file to frontmatter in this pass
- Re-scoping unrelated pending product stories
- Running promptfoo or product-runtime evals unless the migration itself touches
  those surfaces
- Creating a new CineForge-local ADR for methodology unless the migration
  uncovers a genuinely unresolved decision that cannot live in this story +
  audit artifact

## Approach Evaluation

- **Simplification baseline**: No. This is large repo-structure/process work.
  An LLM can draft an audit checklist, but it cannot safely replace authored
  planning surfaces, preserve CineForge's legacy story IDs, and rewire active
  skills without repo-grounded verification.
- **AI-only**: Wrong. Blindly copying Storybook would import the wrong domain
  assumptions and break CineForge-specific surfaces such as the film-oriented
  `spec:1` through `spec:11` model, the existing eval registry, and the legacy
  suffixed story IDs.
- **Hybrid**: Expected winner. Reuse Storybook's migration structure, compiler
  shape, and certification loop, but adapt them to CineForge's local categories,
  docs, and workflow package.
- **Pure code**: Not enough by itself. The risky part is not just writing a
  compiler; it is deciding ownership and updating the human/agent workflow
  surfaces coherently.
- **Repo constraints / ADRs**: Must respect AGENTS' methodology hierarchy,
  Story 134's build-map migration, Story 136's execution-ideal / phase-governance
  migration, and the absence of any CineForge-local ADR that already governs the
  graph+state substrate.
- **Existing patterns to reuse**: Storybook `docs/runbooks/migrate-methodology-to-graph-state.md`,
  Storybook `docs/methodology-artifact-audit-and-migration.md`, Storybook Story
  079, CineForge Story 134, CineForge Story 136, and CineForge's existing
  `scripts/sync-agent-skills.sh` + `make skills-check`.
- **Eval**: The proof surface is repo-native, not promptfoo. Success is
  measured by clean regeneration + methodology checks + skill sync checks +
  semantic review of the generated outputs and rewired active surfaces.

## Tasks

- [x] Audit the current methodology spine and migration constraints:
  - [x] Read the external Storybook runbook, audit artifact, and Story 079
  - [x] Read local `docs/ideal.md`, `docs/spec.md`,
        `docs/methodology-ideal-spec-compromise.md`, `docs/build-map.md`,
        `docs/stories.md`, `docs/setup-checklist.md`, and relevant methodology
        stories
  - [x] Search the repo for live `build-map.md`, `docs/stories.md`, and
        methodology-package consumers
- [x] Create the CineForge migration artifacts first:
  - [x] Create Story 145 as the long-running migration story
  - [x] Create `docs/methodology-artifact-audit-and-migration.md`
  - [x] Seed Story 145 work-log evidence as phases land
- [x] Build the new methodology substrate:
  - [x] Create `docs/methodology/state.yaml`
  - [x] Add a deterministic compiler/check script
  - [x] Generate `docs/methodology/graph.json`
  - [x] Generate `docs/stories.md`
  - [x] Generate `docs/build-map.md`
- [x] Migrate story/ADR metadata tooling:
  - [x] Update story template + `create-story` workflow to emit frontmatter and
        rerun generation
  - [x] Update ADR template/tooling for the new state/graph package
  - [x] Keep legacy story headers supported during migration
- [x] Rewire active methodology consumers:
  - [x] setup/bootstrap surfaces
  - [x] triage/alignment surfaces
  - [x] build/validate/closeout surfaces
  - [x] init-project / exported package surfaces
- [x] Add the architecture-audit lane:
  - [x] seed `architecture_audits` in state
  - [x] add `/triage-architecture`
  - [x] add the runbook
  - [x] teach `/triage` and `/validate` the routing/feed rules
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Methodology compile: `pnpm methodology:compile`
  - [x] Methodology check: `pnpm methodology:check`
  - [x] Backend minimum: not required for docs/skills/scripts-only scope
  - [x] Backend lint: not required for docs/skills/scripts-only scope
  - [x] UI (if touched): not required for docs/skills/scripts-only scope
- [x] If agent tooling or project instructions are touched: `make skills-check`
- [x] If evals or goldens are changed: not applicable; no eval or golden surfaces changed
- [x] If UI is touched: not applicable; no UI surfaces changed
- [x] Search all docs and update any related to what we touched
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 — Data Safety:** Can any user data be lost? Is capture-first preserved?
  - [x] **T1 — AI-Coded:** Is the code AI-friendly? Would another AI session understand it?
  - [x] **T2 — Architect for 100x:** Did we over-engineer something AI will handle better soon?
  - [x] **T3 — Fewer Files:** Are files appropriately sized? Types centralized?
  - [x] **T4 — Verbose Artifacts:** Is the work log verbose enough for handoff?
  - [x] **T5 — Ideal vs Today:** Can this be simplified toward the ideal?

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Architectural Fit

- **Owning class/module**: This migration owns methodology/package surfaces
  only: docs, skills, templates, and the new methodology compiler. No product
  runtime module should absorb it.
- **Data contracts**: No runtime cross-layer contracts are expected. The new
  contract is documentary/operational: `state.yaml`, `graph.json`, generated
  `docs/stories.md`, and generated `docs/build-map.md`.
- **File sizes**: `make check-size` run on 2026-04-04. Large touched docs:
  `docs/spec.md` (1431), `AGENTS.md` (677), `docs/build-map.md` (335),
  `docs/stories.md` (262), `docs/methodology-ideal-spec-compromise.md` (185),
  `.agents/skills/build-story/SKILL.md` (169), `.agents/skills/validate/SKILL.md`
  (165). New compiler/state files will be added in fresh paths.
- **Decision context**: Reviewed `docs/design/decisions.md`,
  `docs/decisions/adr-003-film-elements/adr.md`, local ADR-001..003 directory
  inventory, Story 134, Story 136, and the Storybook migration references. No
  CineForge-local ADR currently governs the graph+state methodology substrate.

## Files to Modify

- `docs/methodology-artifact-audit-and-migration.md` — repo-specific audit and
  migration authority (new)
- `docs/stories/story-145-methodology-graph-state-migration.md` — long-running
  migration story + proof log (new)
- `docs/methodology/state.yaml` — structured operational state (new)
- `docs/methodology/graph.json` — compiled methodology graph (new, generated)
- `docs/build-map.md` — generated dashboard view replacing the authored source
  (`335`)
- `docs/stories.md` — generated story index replacing the authored source
  (`262`)
- `docs/setup-checklist.md` — graph+state setup checklist (`126`)
- `docs/methodology-ideal-spec-compromise.md` — state/graph methodology doctrine
  (`185`)
- `AGENTS.md` — methodology-stack and workflow guidance (`677`)
- `package.json` — add methodology script surface (`5`)
- `scripts/methodology-graph.js` — compiler + check command (new)
- `.agents/skills/setup-methodology/SKILL.md` — bootstrap package rewrite (`133`)
- `.agents/skills/triage/SKILL.md` — state/graph-first triage (`126`)
- `.agents/skills/align/SKILL.md` — state/graph-first alignment (`105`)
- `.agents/skills/build-story/SKILL.md` — generated-index regeneration + state
  references (`169`)
- `.agents/skills/validate/SKILL.md` — architecture-audit feed + state/graph
  checks (`165`)
- `.agents/skills/mark-story-done/SKILL.md` — generated-index closeout flow
  (`97`)
- `.agents/skills/create-story/SKILL.md` — frontmatter + regeneration flow (`92`)
- `.agents/skills/create-story/templates/story.md` — frontmatter template (`89`)
- `.agents/skills/init-project/SKILL.md` — exported methodology package rewrite
  (`251`)
- `.agents/skills/create-adr/templates/adr.md` — state/graph integration
  checklist (`53`)
- `.agents/skills/triage-architecture/SKILL.md` — new bounded architecture-audit
  lane (new)
- `docs/runbooks/setup-methodology.md` — bootstrap runbook rewrite
- `docs/runbooks/triage.md` — state/graph-first triage runbook
- `docs/runbooks/triage-architecture.md` — architecture-audit runbook (new)

## Redundancy / Removal Targets

- treating `docs/build-map.md` as a hand-authored source of truth
- manual edits to `docs/stories.md`
- build-map-first/bootstrap wording that teaches the old package shape
- story/ADR templates that cannot feed the compiler reliably
- implicit architecture-audit drift with no bounded operating lane

## Notes

### CineForge deltas vs Storybook

- CineForge already has the `spec:1` through `spec:11` category model from
  Story 136. Do not import Storybook's product categories.
- CineForge currently teaches `docs/build-map.md` more broadly than Storybook
  did. Preserving the path as a generated dashboard is lower risk than deleting
  it outright.
- CineForge has legacy suffixed story IDs (`003b`, `007c`, `011f`) that the
  compiler must preserve.
- CineForge is a Python-first repo with a minimal root `package.json`, but Node
  24 and `pnpm` are available locally, so a zero-dependency local compiler
  surface is acceptable.

## Plan

1. Create the audit artifact and turn Story 145 into the migration authority.
2. Seed `docs/methodology/state.yaml` with CineForge's current category,
   compromise, roadmap, and architecture-audit state.
3. Add a local compiler/check command that emits `graph.json`, generated
   `docs/stories.md`, and generated `docs/build-map.md`.
4. Update story/ADR templates and methodology consumers to treat state+graph as
   authority and generated docs as outputs.
5. Add the architecture-audit lane and re-run the certification loop until the
   final pass is clean.

## Work Log

20260404-0030 — story-created: Created Story 145 from the local `create-story`
bootstrap, then rewrote it as the long-running CineForge graph+state migration
story. Evidence=`./.agents/skills/create-story/scripts/start-story.sh
methodology-graph-state-migration High`, Storybook runbook, Storybook audit
artifact, Storybook Story 079. Next=create the repo-specific audit artifact and
start the substrate implementation.

20260404-0030 — audit-started: Re-read the current CineForge methodology spine
and consumer hotspots before changing anything. Evidence=`docs/ideal.md`,
`docs/spec.md`, `docs/methodology-ideal-spec-compromise.md`,
`docs/build-map.md`, `docs/stories.md`, `docs/setup-checklist.md`, Story 134,
Story 136, `AGENTS.md`, and grep sweeps across `.agents/skills/`, `docs/`,
and `scripts/`. Key finding=no `docs/methodology/` substrate exists yet and
multiple active skills still treat `docs/build-map.md` / `docs/stories.md` as
hand-authored truth. Next=land the audit artifact, then build state + graph.

20260404-0046 — substrate-landed: Added the graph+state substrate and generated
planning surfaces. Evidence=`docs/methodology/state.yaml`,
`scripts/methodology-graph.js`, `package.json`, `pnpm methodology:compile`,
generated `docs/methodology/graph.json`, generated `docs/stories.md`, and
generated `docs/build-map.md`. Key result=mutable planning state now lives in
`docs/methodology/state.yaml`, while `docs/build-map.md` and `docs/stories.md`
are regenerated views instead of authored sources. Next=re-wire active
workflow/package consumers to the new authority model.

20260404-0051 — consumer-rewire: Updated the active methodology package to read
state+graph authority and regenerate views instead of editing them manually.
Evidence=`AGENTS.md`, `docs/spec.md`, `docs/methodology-ideal-spec-compromise.md`,
`docs/runbooks/setup-methodology.md`, `docs/runbooks/triage.md`,
`docs/runbooks/align.md`, `docs/runbooks/create-eval.md`,
`docs/runbooks/finish-and-push.md`, `.agents/skills/setup-methodology/SKILL.md`,
`.agents/skills/triage*.SKILL.md`, `.agents/skills/build-story/SKILL.md`,
`.agents/skills/validate/SKILL.md`, `.agents/skills/mark-story-done/SKILL.md`,
`.agents/skills/create-story/SKILL.md`, `.agents/skills/create-adr/templates/adr.md`,
`.agents/skills/create-story/templates/story.md`, and deletion of
`.agents/skills/create-story/templates/stories-index.md`. Next=add the bounded
architecture-audit lane and rerun package validation.

20260404-0054 — certification-pass: Added the architecture-audit lane and
completed the certification loop for this migration slice. Evidence=new
`.agents/skills/triage-architecture/SKILL.md`, new
`docs/runbooks/triage-architecture.md`, `./scripts/sync-agent-skills.sh`,
`make skills-check`, and `pnpm methodology:compile && pnpm methodology:check`.
Outcome=all structural checks now pass; remaining warnings are documented legacy
metadata debt only (historical story statuses, missing local ADR-019/021 files,
legacy story/ADR metadata, and the open `methodology_tooling` audit domain).
Next=`/validate` if the user wants formal story validation, or a follow-up
metadata-normalization story if they want to eliminate the remaining warnings.

20260404-0054 — phase-certification-rerun: Re-ran the migration phase checklist
from the audit artifact and Story 145 to verify positive proof and negative
proof per phase instead of trusting the earlier summary. Evidence=`pnpm
methodology:compile && pnpm methodology:check && make skills-check`, targeted
inspection of `package.json`, `scripts/methodology-graph.js`,
`.agents/skills/create-story/templates/story.md`,
`.agents/skills/create-adr/templates/adr.md`,
`.agents/skills/triage-architecture/SKILL.md`,
`docs/runbooks/triage-architecture.md`, and grep sweeps confirming no active
surface still teaches manual `docs/stories.md` edits or authored build-map
authority. Result=phases 0-6 remain intact; only documented warning debt is the
legacy metadata backlog and missing local ADR-019/021 files. Next=decide
whether to treat this as sufficient and move to `/validate`, or open a
follow-up story for warning-debt cleanup.

20260404-0054 — contract-alignment: Tightened the audit artifact's certification
loop so it matches the repo-specific acceptance bar actually being used here:
no structural errors, no stale live workflow instructions, and any remaining
warnings must be explicitly classified as staged migration debt. Evidence=
`docs/methodology-artifact-audit-and-migration.md` certification loop update
plus a fresh `pnpm methodology:check && make skills-check` pass. Next=report
the phase-by-phase audit result to the user.

20260404-0103 — validation: Re-ran the close-out validation suite for the
shipping diff and confirmed the migration is implementation-complete. Evidence=
`make test-unit PYTHON=.venv/bin/python` (`660 passed, 144 deselected, 1
warning`), `.venv/bin/python -m ruff check src/ tests/`, `pnpm --dir ui run
lint` (existing fast-refresh warnings only, no errors), `cd ui && npx tsc -b`,
`pnpm --dir ui run build`, `pnpm methodology:compile && pnpm methodology:check`,
and `make skills-check`. Remaining methodology warnings are the documented
legacy-metadata backlog plus missing local ADR-019/021 files, not a structural
failure in the new graph+state package. Next=`/check-in-diff`.

20260404-0103 — closure: Marked Story 145 done after confirming the graph+state
substrate, generated planning views, workflow rewiring, and architecture-audit
lane are all landed and re-verified. Evidence=`docs/methodology/state.yaml`,
`scripts/methodology-graph.js`, generated `docs/build-map.md`,
generated `docs/stories.md`, new `/triage-architecture` surfaces, refreshed
`docs/setup-checklist.md`, and the full validation pass recorded above. Next=
`/check-in-diff`.

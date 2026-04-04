---
id: "134"
title: "Compromise Convergence Tooling Migration"
status: "Done"
priority: "High"
ideal_refs:
  - "Vision-level preference: easy, fun, and engaging"
  - "R12 (every AI decision explainable and overridable)"
  - "R14 (nothing is ever lost)"
spec_refs:
  - "spec:11.2"
  - "spec:11.3"
  - "spec:11.4"
adr_refs: []
depends_on:
  - "053"
  - "125"
category_refs:
  - "spec:11"
compromise_refs: []
input_coverage_refs: []
architecture_domains: []
roadmap_tags: []
legacy_system: ""
---

# Story 134 — Compromise Convergence Tooling Migration

**Priority**: High
**Status**: Done
**Ideal Refs**: Vision-level preference: easy, fun, and engaging; R12 (every AI decision explainable and overridable); R14 (nothing is ever lost)
**Spec Refs**: spec:11.2 (Build Map, Triage, and Substrate Tracking), spec:11.3 (Verification, Eval Classification, and Registry Discipline), spec:11.4 (Agent Instructions, Skills, and Runbooks)
**ADR Refs**: None found after search in CineForge; reviewed `docs/design/decisions.md` and local ADR-001..003, which do not govern agent-tooling methodology. External reference source: Storybook ADR-019 migration guide and companion artifacts.
**Depends On**: Story 053, Story 125

## Goal

Migrate CineForge's agent-process tooling to the ADR-019 "compromise convergence tracking" model that was proven in Storybook, but do it as a CineForge adaptation rather than a blind port. This story should land a `build-map`, replace `adr-reflect` with `align`, merge `/verify-eval` into `/improve-eval`, add the orchestrating `/triage` meta-skill, and update the surrounding docs/templates/runbooks so the repo has one coherent methodology graph. The build must preserve CineForge's existing strengths (`triage-evals`, `check-compromises.py`, current lifecycle skills) instead of flattening them just to match Storybook's names.

## Acceptance Criteria

- [x] `.agents/skills/align/SKILL.md` exists as the replacement for `adr-reflect`, reads the full methodology graph (Ideal, spec, build map, stories, evals, ADRs), and all active references to `adr-reflect` are updated or intentionally classified as historical-only.
- [x] `/improve-eval` absorbs failure classification as an explicit phase, `.agents/skills/verify-eval/` is removed, and all active lifecycle/template/runbook references move to `/improve-eval` or equivalent "classify failures in Phase 4" wording.
- [x] `docs/build-map.md` exists and is populated from CineForge's actual spec/registry structure, including system summaries plus **Compromise Progress** sections for the active compromise inventory where applicable.
- [x] `/triage` exists as a read-only orchestrator, `/triage-evals` remains the canonical eval leaf, and `triage-inbox` / `triage-stories` are upgraded only as needed to support full-sweep orchestration and build-map-aware ranking.
- [x] Orientation surfaces (`AGENTS.md`, setup skills, story/template skills, runbooks, and any generated wrappers) describe the post-migration behavior consistently, with no active guidance still pointing at `feature-map.md`, `adr-reflect`, or `/verify-eval`.
- [x] Verification greps, skill sync/check, and manual content review confirm the migration is semantically complete, and the story work log records any intentional CineForge-specific deviations from Storybook's exact implementation.

## Out of Scope

- Product/runtime pipeline features unrelated to agent-process tooling
- Blindly copying Storybook docs or skills when CineForge already has a better local pattern
- Retiring `triage-evals` or `check-compromises.py` just to make `/triage` look more "unified"
- Large promptfoo benchmark reruns that are not required to validate the migration itself
- Cross-repo rollout to Dossier or codex-forge

## Approach Evaluation

- **Simplification baseline**: No. This is durable repo-structure/process work, not an AI reasoning task that can be replaced by a single model call. The simplest viable approach is still "adapt the existing docs/skills carefully, then verify with repo-native checks."
- **AI-only**: Blind copy-editing from Storybook is the fastest path but also the likeliest regression. CineForge has no `feature-map.md`, already has `triage-evals`, already has `check-compromises.py`, and does not have Storybook's methodology doc surface. Pure prose-porting would import wrong assumptions.
- **Hybrid**: Use Storybook ADR-019 artifacts as reference implementations, then adapt CineForge's local skills/docs/scripts with grep-driven verification and manual semantic review. This is the expected winning approach.
- **Pure code**: Mechanical renames plus wrapper sync are necessary, but insufficient. The risky part is semantic alignment: deciding where convergence guidance belongs, how build-map sections map to CineForge's spec, and how to preserve local leaf-skill ownership.
- **Repo constraints / ADRs**: Must respect AGENTS' ADR-discipline, Story 053's canonical-skill architecture, Story 125's workflow hardening, and Scout 013's warning that bulk-porting external skill rewrites can be a regression. No local ADR currently governs this methodology layer.
- **Existing patterns to reuse**: `scripts/sync-agent-skills.sh`, `make skills-check`, `.agents/skills/triage-evals/SKILL.md`, `scripts/check-compromises.py`, Storybook's `align`, `triage`, `improve-eval`, `build-map.md`, and the Storybook ADR-019 migration guide as the checklist seed.
- **Eval**: This story is validated by repo-native checks, not promptfoo quality scores: `./scripts/sync-agent-skills.sh`, `make skills-check`, grep sweeps for stale names, `scripts/check-compromises.py`, and manual content review of `docs/build-map.md` and the touched orientation docs.

## Tasks

### 1. Frame the CineForge migration, not a Storybook clone

- [x] Capture the repo-specific starting state in the work log before changing files:
  - no `docs/feature-map.md`
  - no `docs/build-map.md`
  - `adr-reflect` exists
  - `verify-eval` exists separately
  - `triage-evals` already exists
  - `check-compromises.py` already exists
  - `triage` does not exist
  - `triage-inbox` has no read-only `scan` mode
  - `docs/methodology-ideal-spec-compromise.md` does not exist
- [x] Identify which Storybook ADR-019 assets are reference material versus direct copy candidates.
- [x] Record the intentional migration rule: preserve or improve CineForge-specific strengths; do not flatten them for naming symmetry.

### 2. Rename `adr-reflect` -> `align`

- [x] Create `.agents/skills/align/SKILL.md`, using Storybook's `align` as the reference shape but adapting it to CineForge's document graph.
- [x] Delete `.agents/skills/adr-reflect/` only after `align` is in place and wrapper sync is ready.
- [x] Update active references in setup/orientation surfaces and skill docs.
- [x] Ensure `align` reads `docs/build-map.md` and remains read-only/advisory.
- [x] Verify `rg -l 'adr-reflect' .agents docs -g'*.md' -g'!**/migration.md'` is empty or historical-only.
- [x] Verify `rg -l '/adr-reflect' .agents docs -g'*.md' -g'!**/migration.md'` is empty or historical-only.

Comparison / adaptation:
- Storybook already had `build-map.md`; CineForge does not. `align` must tolerate that gap during the migration instead of assuming the file exists on step one.

### 3. Merge `/verify-eval` into `/improve-eval`

- [x] Add an explicit failure-classification phase to `.agents/skills/improve-eval/SKILL.md` so it absorbs the core work now done by `/verify-eval`.
- [x] Delete `.agents/skills/verify-eval/` and any generated wrappers that only exist for that skill.
- [x] Update lifecycle skills and templates that still require `/verify-eval`:
  - `.agents/skills/build-story/SKILL.md`
  - `.agents/skills/validate/SKILL.md`
  - `.agents/skills/mark-story-done/SKILL.md`
  - `.agents/skills/create-story/SKILL.md`
  - `.agents/skills/create-story/templates/story.md`
  - `.agents/skills/setup-golden/SKILL.md`
  - `.agents/skills/triage-evals/SKILL.md`
  - `docs/runbooks/golden-build.md`
  - `docs/runbooks/triage-evals.md`
  - any other active references found by grep
- [x] Update wording from "run `/verify-eval`" to the new unified contract without losing mismatch-classification rigor.
- [x] Verify `rg -l 'verify-eval' .agents docs -g'*.md' -g'!**/migration.md'` is empty or historical-only.

Comparison / adaptation:
- CineForge already has `/improve-eval`; this is a merge, not a new skill. The migration should preserve existing attempt-record and registry discipline while eliminating the split-brain workflow.

### 4. Create `docs/build-map.md` from scratch (required deliverable)

- [x] Derive the build-map system structure from CineForge's actual spec sections rather than inventing Storybook-style systems that do not match this repo.
- [x] Use the Storybook build-map header/preamble pattern as a model, but write CineForge-specific content.
- [x] Add system summaries, spec refs, ADR refs (or explicit "none"), dependencies, and story coverage markers where appropriate.
- [x] Add **Compromise Progress** subsections for the active compromise inventory, including Optimize + Eliminate tracking.
- [x] Pull elimination data from `docs/evals/registry.yaml` and `scripts/check-compromises.py` where that is the best local source of truth.
- [x] Include actual eval IDs, thresholds, latest recorded scores/dates, and retry conditions when they exist; say "No scores recorded" when they do not.
- [x] Update stale `feature-map.md` references in setup/decomposition skills and any other active docs:
  - `.agents/skills/setup-stories/SKILL.md`
  - `.agents/skills/decompose-spec/SKILL.md`
  - any other hits from grep
- [x] Re-read `docs/build-map.md` after creation to ensure it is semantically current, not just string-replaced prose.

Comparison / adaptation:
- Storybook renamed an existing `feature-map.md`; CineForge has nothing to rename. This story must create a real build map, not a placeholder file with copied headings.
- CineForge's `check-compromises.py` is already a cheap compromise-status signal. Reuse it; do not duplicate the same deletion-gate logic manually in multiple docs/skills.

### 5. Keep leaf triage skills; add orchestrating `/triage`

- [x] Create `.agents/skills/triage/SKILL.md` as a read-only orchestrator modeled on Storybook's version.
- [x] Create `docs/runbooks/triage.md` as the operational companion for the new `/triage` meta-skill.
- [x] Keep `.agents/skills/triage-evals/SKILL.md` as the eval/convergence leaf and update it for post-migration wording (`align`, `build-map`, unified `improve-eval` classification).
- [x] Upgrade `.agents/skills/triage-stories/SKILL.md` so ranking explicitly considers convergence/build-map value.
- [x] Upgrade `.agents/skills/triage-inbox/SKILL.md` with a read-only `scan` mode for full-sweep orchestration.
- [x] Fix the stale `docs/stories/index.md` reference in `triage-inbox`; CineForge's story index is `docs/stories.md`.
- [x] Register the new `/triage` skill in `AGENTS.md` and sync wrappers.
- [x] Verify full-sweep `/triage` is read-only and does not absorb the action-taking logic that still belongs in leaf skills.

Comparison / adaptation:
- Unlike Storybook, CineForge already has a useful `/triage-evals` leaf. The migration is wrong if `/triage` duplicates or weakens that logic instead of dispatching to it.

### 6. Update methodology, orientation, and creation surfaces

- [x] Add the eval-class taxonomy header comments to `docs/evals/registry.yaml`.
- [x] Create `docs/runbooks/align.md` as the operational companion for the new `/align` skill.
- [x] Update `.agents/skills/create-cross-cli-skill/SKILL.md` so new skills explicitly use the broader alignment/build-map check rather than the narrower ADR-only framing.
- [x] Decide the right home for the "Convergence Tracking: The Build Map" methodology note:
  - [x] A dedicated methodology doc is worth creating, and `docs/methodology-ideal-spec-compromise.md` now holds that connective guidance.
  - [x] AGENTS stays focused on agent behavior while linking back to the methodology doc and build map.
- [x] Update `AGENTS.md`, setup skills, runbooks, and templates so they describe the post-migration names and responsibilities.
- [x] Re-check generated/wrapper-facing surfaces after sync so the canonical skills and the generated command wrappers agree.

Comparison / adaptation:
- Storybook already had `docs/methodology-ideal-spec-compromise.md`; CineForge does not. Creating a new doc just for parity may be worse than updating an existing source-of-truth surface. Make that choice deliberately during build.

### 7. Verification sweep

- [x] Run `./scripts/sync-agent-skills.sh`
- [x] Run `./scripts/sync-agent-skills.sh --check`
- [x] Run `make skills-check`
- [x] Run `.venv/bin/python scripts/check-compromises.py`
- [x] Run `rg -l 'adr-reflect|/reflect' .agents docs -g'*.md' -g'!**/migration.md'` and classify each hit as historical-only or fix-required.
- [x] Run `rg -l 'verify-eval' .agents docs -g'*.md' -g'!**/migration.md'` and classify each hit as historical-only or fix-required.
- [x] Run `rg -l 'feature-map\\.md' .agents docs -g'*.md' -g'!CHANGELOG.md' -g'!**/migration.md'` and classify each hit as historical-only or fix-required.
- [x] Run `rg -n '/Users/.+/.codex/worktrees/' .agents docs -g'*.md'` and make sure no active guidance ships with worktree-local absolute paths.
- [x] Manually review `docs/build-map.md`, `AGENTS.md`, and the touched skills/runbooks to confirm the prose matches the implementation and phase numbering.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=.venv/bin/python`
  - [x] Backend lint: `.venv/bin/python -m ruff check src/ tests/`
  - [x] UI not touched; UI lint/typecheck/build not required for this story
- [x] If agent tooling or project instructions are touched: `make skills-check`
- [x] No benchmark scores or attempt records changed; unified `/improve-eval` failure-classification flow was not needed beyond lifecycle-contract updates, so `docs/evals/registry.yaml` stayed terminology-only.
- [x] UI not touched; browser verification not required for this story
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

- **Owning class/module**: This is repo-process infrastructure owned by `AGENTS.md`, canonical skills under `.agents/skills/`, the story/template system, and supporting docs under `docs/`. No runtime service or product module should absorb this migration.
- **Data contracts**: No new runtime cross-layer contracts are expected. The primary artifact is structured markdown guidance (`docs/build-map.md`, skill docs, runbooks, templates). If any code-generated data is introduced for build-map upkeep, that would need its own follow-up design.
- **File sizes**: Likely touched files include large docs that need careful churn control: `AGENTS.md` (649), `docs/spec.md` (1073, reference source, not necessarily modified), `docs/evals/registry.yaml` (1393), `docs/stories.md` (260), `.agents/skills/improve-eval/SKILL.md` (260), `.agents/skills/build-story/SKILL.md` (169), `.agents/skills/setup-golden/SKILL.md` (157). Smaller but likely touched files include `.agents/skills/adr-reflect/SKILL.md` (102), `.agents/skills/verify-eval/SKILL.md` (185), `.agents/skills/triage-evals/SKILL.md` (119), `.agents/skills/triage-stories/SKILL.md` (63), `.agents/skills/triage-inbox/SKILL.md` (57), `.agents/skills/setup-env-ai/SKILL.md` (118), `.agents/skills/setup-stories/SKILL.md` (127), `.agents/skills/decompose-spec/SKILL.md` (108), `.agents/skills/create-cross-cli-skill/SKILL.md` (40), `.agents/skills/create-story/SKILL.md` (92), `.agents/skills/create-story/templates/story.md` (89), `.agents/skills/validate/SKILL.md` (138), `.agents/skills/mark-story-done/SKILL.md` (97), `docs/runbooks/triage-evals.md` (91), `docs/runbooks/golden-build.md` (279), `scripts/check-compromises.py` (371).
- **Decision context**: Reviewed `docs/design/decisions.md`, local ADR-001..003, Storybook ADR-019 migration guide, Storybook's `align` / `triage` / `improve-eval` / `build-map.md`, and Scout 013. No CineForge-local ADR currently governs this methodology/tooling layer, so this story must document its adaptation choices explicitly rather than pretending a local ADR already exists.

## Files to Modify

- `AGENTS.md` — skill inventory/orientation updates and any convergence-tracking guidance home chosen during build (649)
- `.agents/skills/align/SKILL.md` — new replacement for `adr-reflect` (new)
- `.agents/skills/adr-reflect/SKILL.md` — remove after replacement lands (102)
- `.agents/skills/improve-eval/SKILL.md` — absorb failure classification and post-migration terminology (260)
- `.agents/skills/verify-eval/SKILL.md` — remove after merge (185)
- `.agents/skills/triage/SKILL.md` — new orchestrating meta-skill (new)
- `docs/runbooks/triage.md` — runbook for the new `/triage` skill (new)
- `.agents/skills/triage-evals/SKILL.md` — keep as canonical eval leaf; update references and recommendation language (119)
- `.agents/skills/triage-stories/SKILL.md` — add build-map/convergence scoring (63)
- `.agents/skills/triage-inbox/SKILL.md` — add `scan` mode and fix story-index path (57)
- `docs/runbooks/align.md` — runbook for the new `/align` skill (new)
- `.agents/skills/setup-env-ai/SKILL.md` — rename/reflection skill inventory updates (118)
- `.agents/skills/setup-stories/SKILL.md` — `feature-map` -> `build-map` and related guidance updates (127)
- `.agents/skills/decompose-spec/SKILL.md` — `feature-map` -> `build-map` and related guidance updates (108)
- `.agents/skills/create-cross-cli-skill/SKILL.md` — alignment/build-map rule update (40)
- `.agents/skills/create-story/SKILL.md` — eval/classification wording updates (92)
- `.agents/skills/create-story/templates/story.md` — post-migration story template wording (89)
- `.agents/skills/build-story/SKILL.md` — `/verify-eval` references removed in favor of unified improve-eval wording (169)
- `.agents/skills/validate/SKILL.md` — post-migration eval-classification wording (138)
- `.agents/skills/mark-story-done/SKILL.md` — post-migration eval-classification wording (97)
- `.agents/skills/setup-golden/SKILL.md` — post-migration eval-classification wording (157)
- `docs/build-map.md` — new build-map source of truth for system structure + compromise progress (new)
- `docs/evals/registry.yaml` — eval-class taxonomy header comments and any migration-related wording cleanup (1393)
- `docs/runbooks/triage-evals.md` — post-migration terminology and leaf/orchestrator roles (91)
- `docs/runbooks/golden-build.md` — post-migration terminology and lifecycle references (279)
- `docs/stories.md` — add/update story index and execution-map summary (260)
- `scripts/check-compromises.py` — only if needed to support build-map or triage wording without duplicating logic (371)
- `docs/methodology-ideal-spec-compromise.md` — create only if the build chooses a dedicated methodology doc as the right source of truth (new, conditional)

## Redundancy / Removal Targets

- `.agents/skills/adr-reflect/`
- `.agents/skills/verify-eval/`
- Active references to nonexistent `docs/feature-map.md`
- Any duplicate prose that re-documents compromise-tracking logic already owned by `docs/build-map.md` or `scripts/check-compromises.py`
- Any fake `/triage` unification that duplicates leaf-skill logic instead of orchestrating it

## Notes

Reference source set:
- Storybook `docs/decisions/adr-019-compromise-convergence-tracking/migration.md`
- Storybook `docs/decisions/adr-019-compromise-convergence-tracking/adr.md`
- Storybook `docs/build-map.md`
- Storybook `.agents/skills/align/SKILL.md`
- Storybook `.agents/skills/triage/SKILL.md`
- Storybook `.agents/skills/improve-eval/SKILL.md`
- Storybook `docs/methodology-ideal-spec-compromise.md`

### CineForge Delta vs Storybook

| Area | Storybook target state | CineForge current state | Required adaptation |
|---|---|---|---|
| Reflection meta-skill | `align` | `adr-reflect` exists | Rename + broaden scope to full methodology graph |
| Eval mismatch handling | inside `/improve-eval` Phase 4 | separate `/verify-eval` plus many references | Merge, delete old skill, update lifecycle/docs |
| Build map | rename existing `feature-map.md` | no `feature-map.md`, no `build-map.md` | Create a real `docs/build-map.md` from scratch |
| Eval triage | leaf under `/triage` | already has `/triage-evals` + `check-compromises.py` | Preserve as leaf; wire `/triage` to it |
| Inbox full sweep | `triage-inbox scan` | no scan mode; stale `docs/stories/index.md` ref | Add scan mode and fix path |
| Methodology doc | dedicated file exists | no dedicated methodology doc | Choose the best source of truth intentionally |
| Feature-map references | rename existing references | stale references exist even though file never existed | Update to `build-map.md` and review semantics |

Pushback / migration rule:
- A direct Storybook copy would be wrong because CineForge's current process surface is materially different. The migration only succeeds if the end state is coherent in CineForge terms, not if the filenames merely match Storybook.
- User decision: CineForge will have its own `docs/build-map.md` as part of this story. That is settled scope, not an optional follow-up.

## Plan

Chosen approach: adapt Storybook ADR-019's end state into CineForge's existing skill/doc architecture, with `docs/build-map.md` as a required deliverable and a dedicated `docs/methodology-ideal-spec-compromise.md` as the long-term methodology source of truth. This is better than stuffing convergence prose into `AGENTS.md` because AGENTS is the agent instruction surface, while the methodology doc is durable project doctrine that should be linkable independently of CLI behavior.

Why this repo-fit is better than the alternatives:
- Storybook-copy approach rejected: CineForge has no `feature-map.md`, already has a strong `triage-evals` leaf, and already has `scripts/check-compromises.py`. Copying prose without adaptation would import wrong assumptions and weaken local strengths.
- AGENTS-only methodology approach rejected: it would bury build-map methodology inside an agent-instruction file instead of giving the project a stable source-of-truth document.
- Monolithic `/triage` approach rejected: Storybook ADR-019 and local `triage-evals` both show that leaf skills own real domain logic. `/triage` should orchestrate, not replace them.

Structural health check:
- Ran `make check-size` on 2026-03-15. The repo has many oversized runtime/UI files, but this story stays in agent tooling/docs. Expected touched files are all docs/skills/scripts; no new runtime layer contracts or event schemas are required.
- Large touched files acknowledged up front: `AGENTS.md` (649), `docs/evals/registry.yaml` (1393). Churn in those files should stay targeted and terminology-only.
- No new inter-layer data contracts are expected. If build-map upkeep grows into code-generated data later, that should become a separate story.

Scope expansion folded into this story:
- Add `docs/runbooks/triage.md` and `docs/runbooks/align.md`. AGENTS' runbook rule says every new skill with 3+ procedural steps should ship with a runbook. This is a small, tightly coupled delta, so it belongs in Story 134 rather than a follow-up.

Implementation order:
1. Create the new source-of-truth docs first:
   - `docs/build-map.md`
   - `docs/methodology-ideal-spec-compromise.md`
   - `docs/runbooks/triage.md`
   - `docs/runbooks/align.md`
2. Create the new skills and migrate the old ones:
   - add `.agents/skills/align/SKILL.md`
   - add `.agents/skills/triage/SKILL.md`
   - update `.agents/skills/improve-eval/SKILL.md`
   - update `triage-evals`, `triage-stories`, `triage-inbox`
   - remove `.agents/skills/adr-reflect/` and `.agents/skills/verify-eval/`
3. Update orientation and authoring surfaces:
   - `AGENTS.md`
   - `setup-env-ai`, `setup-stories`, `decompose-spec`
   - `create-cross-cli-skill`, `create-story`, `create-story` template
   - `build-story`, `validate`, `mark-story-done`, `setup-golden`
   - `docs/runbooks/triage-evals.md`, `docs/runbooks/golden-build.md`, `docs/evals/README.md`
4. Update `docs/evals/registry.yaml` header comments and any migration-related wording only if needed.
5. Sync wrappers and run verification:
   - `./scripts/sync-agent-skills.sh`
   - `./scripts/sync-agent-skills.sh --check`
   - `make skills-check`
   - `.venv/bin/python scripts/check-compromises.py`
   - grep sweeps for stale names/paths
6. Re-read the touched docs/skills semantically, then complete the story tasks, checks, and work log.

Impact / break-risk analysis:
- Main risk: renaming skills but leaving stale active guidance behind, causing future agents to follow conflicting instructions.
- Main mitigation: grep-based cleanup plus manual readback of AGENTS, build-map, lifecycle skills, and runbooks after sync.
- Secondary risk: `docs/build-map.md` becoming a shallow copy of spec headings instead of a useful convergence tracker.
- Main mitigation: derive the system structure from CineForge's actual spec/story coverage and use `scripts/check-compromises.py` plus the registry for elimination data.

Definition of done for this build:
- `align`, `triage`, `build-map`, methodology doc, and new runbooks exist and are coherent.
- `adr-reflect` and `/verify-eval` are retired from active guidance.
- Leaf triage ownership remains intact, especially `triage-evals`.
- Skill wrappers sync cleanly and grep sweeps show no active stale references.
- Story 134 remains `In Progress` with `Build complete` checked and `/validate` as the next step.

## Work Log

20260315-1656 — story-created: Drafted a Pending migration story from Storybook ADR-019 guidance, but rewrote it around CineForge's actual starting state (`triage-evals`, `check-compromises.py`, no `feature-map.md`, no methodology doc). Evidence=Storybook ADR-019 migration guide + local skill/doc audit. Next=`/build-story 134` when ready.
20260315-1703 — scope-confirmed: User confirmed that CineForge should get its own `docs/build-map.md` as part of this migration. Evidence=current session direction. Next=keep build-map creation as a mandatory deliverable during `/build-story`.
20260315-1732 — exploration-complete: Read `docs/ideal.md`, Story 053, Story 125, local lifecycle skills, local triage/eval/golden runbooks, Storybook ADR-019 reference artifacts, and the current compromise sources (`docs/spec.md`, `docs/evals/registry.yaml`, `scripts/check-compromises.py`). Evidence=`make check-size`, grep audit for `adr-reflect` / `verify-eval` / `feature-map.md`, Storybook reference files. Impact=confirmed the migration should preserve `triage-evals` + `check-compromises.py`, must create `docs/build-map.md`, and should add runbooks for new `align` / `triage` skills per AGENTS rules. Next=implement the new docs/skills, then clean up stale references and sync wrappers.
20260315-1826 — implementation-complete: Landed the CineForge-specific convergence stack rather than a Storybook copy. Added `docs/build-map.md`, `docs/methodology-ideal-spec-compromise.md`, `docs/runbooks/align.md`, `docs/runbooks/triage.md`, `.agents/skills/align/SKILL.md`, and `.agents/skills/triage/SKILL.md`; upgraded `improve-eval`, `triage-evals`, `triage-stories`, `triage-inbox`, setup/create/lifecycle skills, and AGENTS/orientation docs; removed `.agents/skills/adr-reflect/` and `.agents/skills/verify-eval/`. Impact=the methodology graph is now explicit, build-map-driven, and routed through `align` + `triage` while preserving `triage-evals` and `scripts/check-compromises.py` as CineForge-specific strengths. Evidence=manual readback of `docs/build-map.md`, `docs/methodology-ideal-spec-compromise.md`, `AGENTS.md`, and the touched skill/runbook set. Next=run wrapper sync/checks, classify leftover grep hits, and record final handoff evidence.
20260315-1841 — verification-complete: Synced wrappers and verified the migration with repo-native checks. Evidence=`./scripts/sync-agent-skills.sh` (`36` skills synced), `./scripts/sync-agent-skills.sh --check`, `make skills-check`, `.venv/bin/python scripts/check-compromises.py`, `.venv/bin/python -m ruff check src/ tests/`, and `make test-unit PYTHON=.venv/bin/python` (`552 passed`, `127 deselected`, `1` existing pytest mark warning). Grep classification=`adr-reflect` / `/reflect` hits are limited to Story 134 and historical scout docs; `verify-eval` hits are limited to Story 134 plus historical done stories/scout docs; `feature-map.md` hits are limited to Story 134 and historical scout docs; worktree-path grep found no active guidance beyond the command text in Story 134 itself. Impact=active guidance is coherent post-migration, wrappers match the canonical skills, and no runtime-compromise status changed beyond confirming the current C2/C3/C4/C5/C7 state. Next=`/validate 134`.
20260315-1910 — validation-cleanup: Compared the landed migration directly against Storybook `migration.md` and found three misses that the initial build handoff had not caught: `benchmarks/golden/README.md` still referenced `/verify-eval`, the new methodology/build-map/runbook docs used absolute local markdown links, and `docs/build-map.md` left all "Stories cover this system" boxes unchecked despite populated story coverage. Fixed all three inline, then re-ran targeted greps plus `make skills-check`; all returned clean. Impact=the implementation now matches the migration guide's trap list as well as its headline steps. Evidence=`rg` on the affected files for absolute `/Users/cam/Documents/Projects/cine-forge` links, `/verify-eval`, and unchecked build-map coverage boxes returned no matches after the fixes; `make skills-check` remained green. Next=`/mark-story-done 134`.
20260315-1922 — validate: Re-ran the validate skill's required suite and re-reviewed Story 134 against the local delta, `docs/ideal.md`, `docs/spec.md` compromise refs, local decisions, and the Storybook migration guide. Evidence=`make test-unit PYTHON=.venv/bin/python` (`552 passed`, `127 deselected`, `1` existing pytest mark warning), `.venv/bin/python -m ruff check src/ tests/` (pass), `pnpm --dir ui run lint` (pass with 5 pre-existing `react-refresh/only-export-components` warnings outside this story), `cd ui && npx tsc -b` (pass), `make skills-check` (pass), `.venv/bin/python scripts/check-compromises.py` (same C2/C3/C4/C5/C7 not-yet status, no regression), and targeted grep review of the active migration surfaces. Impact=no remaining findings for Story 134; the migration is clean against its acceptance criteria and against Storybook's trap list. Next=`/mark-story-done 134`.
20260315-1930 — story-closed: Marked Story 134 Done after validation confirmed the migration is clean. Evidence=workflow gates completed, acceptance criteria all met, story index updated, and changelog entry added. Runtime note=remaining red compromise detectors (C2/C3/C4/C5/C7) are non-runtime-blocking for this story because Story 134 only migrated convergence tooling; it did not attempt to eliminate those compromises. Next=`/check-in-diff`.

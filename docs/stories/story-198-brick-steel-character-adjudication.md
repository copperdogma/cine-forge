---
id: "198"
title: "Brick & Steel Character Adjudication"
status: "Done"
priority: "High"
ideal_refs:
  - "R1 (story understanding)"
  - "R5 (full spectrum of human involvement)"
  - "R8 (professional-grade production artifacts)"
  - "R12 (transparency & control)"
spec_refs:
  - "spec:2.4"
  - "spec:2.6"
  - "spec:3.1"
  - "spec:3.2"
  - "spec:3.3"
  - "spec:5.4"
  - "spec:8.2"
adr_refs:
  - "ADR-001"
  - "ADR-002"
  - "ADR-003"
depends_on:
  - "055"
  - "081"
  - "097"
  - "124"
  - "129"
category_refs:
  - "spec:2"
  - "spec:3"
  - "spec:5"
  - "spec:8"
compromise_refs:
  - "C2"
  - "C3"
input_coverage_refs: []
architecture_domains:
  - "ingest_and_world_building"
  - "api_service_and_operator_console"
roadmap_tags:
  - "brick-steel"
  - "entity-adjudication"
  - "artifact-editing"
  - "character-resolution"
legacy_system: ""
---

# Story 198 - Brick & Steel Character Adjudication

**Priority**: High
**Status**: Done
**Ideal Refs**: R1, R5, R8, R12
**Spec Refs**: spec:2.4, spec:2.6, spec:3.1, spec:3.2, spec:3.3, spec:5.4, spec:8.2
**ADR Refs**: ADR-001, ADR-002, ADR-003
**Depends On**: Story 055, Story 081, Story 097, Story 124, Story 129

## Goal

Fix or honestly classify the Brick & Steel character-resolution defect where the tiny script leaves `Brick` and `Brick Braddock` as separate characters, then verify whether the in-app AI artifact-editing flow can actually resolve the duplicate through versioned artifact changes. The product failure is not just a bad extraction row: duplicate characters poison reference generation, downstream rendering, and trust in the conversational "just fix it" loop.

## Eval Ladder Context

- **Root Ideal need**: R1/R8 require CineForge to understand the story's characters well enough to build coherent downstream artifacts. R5/R12 require the user or AI to correct canon without hidden mutation or dead-end chat.
- **Parent evidence**: Story 055 introduced LLM-first entity adjudication, Story 081 made the scene index canonical for characters, Story 097 implemented AI artifact editing, Story 124 added recall verification, and Story 129 tightened entity taxonomy.
- **Measured failure mode**: the Brick & Steel production project still showed separate Brick/Brick Braddock entries in the Characters surface, and a user attempt to have in-app AI fix it appeared to try but did not deprecate or merge the duplicate in the end.
- **Child validation**: reproduce on current project/artifacts, determine whether the failure is extraction/adjudication, alias metadata, UI canonicalization, or AI artifact-edit application, then fix the smallest owner and verify both API/artifact and UI truth.

## Acceptance Criteria

- [x] Current Brick & Steel character state is captured with exact artifact refs, entity ids, UI route evidence, and whether `Brick` / `Brick Braddock` still duplicate on the current code/data.
- [x] The root cause is classified: extraction/adjudication miss, alias/canonical-name miss, artifact editing miss, UI grouping miss, or stale production data.
- [x] If the duplicate still reproduces from a deterministic fixture, a regression fixture is added before the fix.
- [x] The fixed flow produces one canonical Brick character with aliases or deprecations preserved honestly, not silent deletion of user-visible canon.
- [x] In-app AI artifact editing either applies the merge/deprecation as a new immutable artifact version or surfaces a clear unsupported-action blocker. It must not pretend to have changed canon when it did not.
- [x] Downstream character references, scene presence, and entity navigation do not keep pointing at a dead duplicate after the fix.
- [x] Browser verification covers the Characters surface and the relevant chat/artifact-edit path on desktop and mobile, unless a documented environment blocker prevents the full chat probe.

## Out of Scope

- General redesign of all entity resolution.
- Visual reference-pack quality after the character identity is canonical; Story 197 owns reference fidelity.
- Production xAI readiness; Story 195 owns provider configuration.
- Final-render prompt/timing defects already handled by Stories 191, 193, and 194.

## Approach Evaluation

- **Simplification baseline**: Manually edit the duplicate character away. That may fix one project but does not prove the ingestion/adjudication or AI edit path is trustworthy.
- **AI-only**: A model can adjudicate the duplicate, but persistence, provenance, alias/deprecation semantics, and downstream invalidation need deterministic code and tests.
- **Hybrid**: Likely best. AI can decide whether two entities are the same; code owns schema, artifact versioning, stale propagation, and UI consistency.
- **Pure code**: Useful only if the failure is a deterministic alias/canonicalization bug. It is unlikely to handle all script phrasing safely without AI adjudication.
- **Repo constraints / ADRs**: ADR-001 requires eval/fixture-backed model decisions. ADR-002 requires the UI/chat to be honest about what changed. ADR-003 requires upstream artifact edits rather than prompt hacks.
- **Existing patterns to reuse**: `entity_discovery_v1`, scene-index canonical character rules, entity adjudication from Story 055, artifact editing from Story 097, provider failure/action messaging patterns, and character/entity UI routes.
- **Eval**: Focused fixture plus existing entity-discovery/character extraction evals if defaults or prompts change. Browser/chat verification distinguishes the artifact-editing trust surface.

## Tasks

- [x] Capture current Brick & Steel character artifact state for `Brick`, `Brick Braddock`, and any `Dick/Steel` adjacent aliases.
- [x] Capture current Characters UI route evidence for the duplicate state, unless browser verification is explicitly blocked.
- [x] Inspect the artifact-edit helper path that should merge/deprecate duplicates; record the action endpoint, artifact ref, proposal status, and diff shape.
- [x] Record chat/API blocker evidence for the identity merge/deprecation path.
- [x] Create a deterministic regression fixture if current code can reproduce the duplicate from source script/substrate.
- [x] Identify the narrow owner: extraction prompt, adjudication logic, alias schema, artifact-edit routing, change propagation, or UI display.
- [x] Implement the smallest fix with schema-first changes if aliases/deprecations cross boundaries.
- [x] Add focused tests for duplicate detection/adjudication and for AI artifact-edit truth if that path changes.
- [x] Verify deterministic downstream refs after fresh character collapse so scene/prop/graph edges resolve Brick Braddock aliases to canonical `brick`.
- [x] Rerun or replace stale Brick & Steel production artifacts so the live project data no longer shows both Brick variants.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  - [x] Backend lint: `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`
  - [x] Post-Round-4 downstream focused tests: `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest -m unit tests/unit/test_entity_graph_module.py tests/unit/test_character_bible_module.py` (`28 passed`)
  - [x] Round-12 current focused Story 198 unit set: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest -m unit tests/unit/test_chat_artifact_edits.py tests/unit/test_artifact_editing.py tests/unit/test_api_artifact_editing.py tests/unit/test_character_bible_module.py tests/unit/test_character_naming_regression.py tests/unit/test_entity_graph_module.py` (`80 passed, 14 deselected`)
  - [x] Final reset-shard-C focused Story 198 unit set after continuity follow-up, including artifact-manager current-stage filtering: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest -m unit tests/unit/test_chat_artifact_edits.py tests/unit/test_artifact_editing.py tests/unit/test_api_artifact_editing.py tests/unit/test_character_bible_module.py tests/unit/test_character_naming_regression.py tests/unit/test_entity_graph_module.py tests/unit/test_artifact_manager_artifact_groups.py` (`84 passed, 14 deselected`)
  - [x] Final-final full unit set after artifact-manager and continuity follow-up: `make test-unit PYTHON=.venv/bin/python` (`904 passed, 183 deselected, 1 warning`)
  - [x] Round-8 direct naming regression check: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_character_naming_regression.py` (`14 passed`)
  - [x] Round-12 current full unit set: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` (`900 passed, 183 deselected, 1 warning`)
  - [x] Redundancy cleanup targeted candidate tests: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest -m unit tests/unit/test_character_bible_module.py` (`21 passed`)
  - [x] Post-Round-4 targeted Ruff passed for the changed downstream graph/test files.
  - [x] Reset-shard-C Ruff check: `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/` passed.
  - [x] Final-final UI lint/typecheck: `pnpm --dir ui run lint` and `cd ui && npx tsc -b` passed.
  - [x] UI not required for the current diff because no UI files were touched; run `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build` if that changes.
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile` and `pnpm methodology:check`
- [x] If evals or goldens are changed: no eval/golden files changed in the current diff, so no registry update is required.
- [x] Browser verification: Characters route plus chat/artifact-edit or documented blocker, on desktop and mobile
- [x] Search Story 198 docs/methodology/evidence surfaces and update related generated views for this shard.
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 - Data Safety:** Are old character versions preserved rather than silently deleted?
  - [x] **T1 - AI-Coded:** Is entity merge/deprecation traceable?
  - [x] **T2 - Architect for 100x:** Does the fix avoid brittle name-only heuristics?
  - [x] **T3 - Fewer Files:** Is ownership centralized in the existing entity/edit seams?
  - [x] **T4 - Verbose Artifacts:** Are before/after refs and chat actions recorded?
  - [x] **T5 - Ideal vs Today:** Does the user get closer to "tell the AI to fix canon and it actually does"?

## Workflow Gates

- [x] Build complete: implementation finished, required checks run, and human summary shared
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via `/mark-story-done`

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: entity discovery/adjudication owns canonical identity; artifact editing owns user/AI corrections; UI should display canonical state but not invent identity merges.
- **Data contracts**: If merge/deprecation state is insufficient, update Pydantic contracts before UI/API consumption. Preserve lineage and downstream staleness.
- **File sizes**: likely watchpoints include entity-discovery modules, API artifact editing routes/managers, chat/edit helpers, and Characters UI. Use focused helpers where possible.
- **Decision context**: ADR-001, ADR-002, ADR-003, Stories 055, 081, 097, 124, 129, and the Brick & Steel inbox note.

## Files to Modify

- `docs/reports/story-198-brick-steel-character-adjudication/` - before/after evidence
- `src/cine_forge/modules/world_building/entity_discovery_v1/` or related adjudication modules if root cause is extraction
- `src/cine_forge/api/artifact_manager.py` and focused edit helpers if root cause is AI artifact edit persistence
- `src/cine_forge/ai/chat*` edit proposal helpers if chat action generation is wrong
- Character/entity schemas if alias/deprecation metadata changes
- `ui/src/pages` or entity components if the UI groups or routes duplicate entities incorrectly
- Focused unit/integration tests and optional browser smoke script

## Redundancy / Removal Targets

- Any name-only post-filter that hides duplicates in UI without fixing canonical artifacts.
- Any AI edit action that reports success without a new artifact version.
- Any duplicate alias/deprecation representation spread across bibles, scene index, and UI-only state.

## Notes

- The inbox item includes two linked concerns: bad duplicate resolution and the user's failed attempt to get in-app AI to modify artifacts. Keep them in one story because the acceptance surface is "canon is correct and the correction loop is trustworthy."
- Do not solve this by deleting an old character folder in place. Preserve immutable history and make the current canonical state clear.

## Plan

### Read-Only Baseline (Pre-Fix)

- Baseline project evidence was real, not stale UI: `/Users/cam/Documents/Projects/cine-forge/output/brick-steel-full-retired/artifacts/scene_index/project/v2.json` listed both `BRICK` and `BRICK BRADDOCK`, with empty `characters_present_ids` on enriched index entries.
- Baseline downstream artifacts were already poisoned: `entity_discovery_results/project/v1.json` copied both names from `scene_index`; `character_bible/brick/v1.json` and `character_bible/brick_braddock/v1.json` both existed; `entity_graph/project/v1.json` contained separate `brick` and `brick_braddock` edges, including a co-occurrence edge between them.
- Baseline folder-backed bibles already showed alias evidence but no canonical merge: `bibles/character_brick/master_v1.json` had `aliases=["Brick Braddock"]`; `bibles/character_brick_braddock/master_v1.json` had `aliases=["Brick"]`; `bibles/character_brick_braddock/manifest_v2.json` also owned the selected visual reference image.
- Read-only code probe against baseline artifacts showed `_prepare_character_candidates(...)` printed `Skipping second-pass adjudication for discovery-backed candidates`, returned both Brick variants, produced no rejected candidates, and had `decision_trace_len=0`. The merge-capable `_adjudicate_candidates` path was therefore bypassed on the production path.
- Read-only chat-edit probe showed `build_artifact_edit_tool_result` accepted a request that changed `character_id` from `brick_braddock` to `brick` and returned `status=proposal_ready` for `bible_manifest/character_brick_braddock`. That was not a real merge/deprecation operation; it would edit one master file while leaving the duplicate group and downstream refs intact.

### Root-Cause Classification

- Primary root cause: alias/canonical-name adjudication miss caused by a control-flow bug. Discovery-backed characters bypassed second-pass adjudication, so full-name/dialogue-cue aliases from the scene index were never merged before bible emission.
- Secondary trust gap: artifact editing supported single-artifact field edits only and did not recognize cross-artifact identity merge/deprecation as unsupported. It could produce a plausible-looking proposal that was not sufficient canon repair.
- Contributing source: `scene_analysis_v1` can carry enriched `characters_present` names into the enriched index and drops `characters_present_ids`; this makes the duplicate source easy to propagate. It is not the final owner of identity, but the fix should preserve IDs where possible or explicitly leave that as covered by the candidate-resolution owner.
- Not a UI grouping bug: the Characters surface reads `bible_manifest` groups; the duplicate exists in immutable artifacts and graph edges.

### Current Implementation State

- Before-state evidence was captured in `docs/reports/story-198-brick-steel-character-adjudication/baseline.md`; that report is baseline-only and should not be read as current post-fix validation.
- Regression coverage now includes discovery-backed Brick/Brick Braddock alias adjudication, alias scene-presence deduplication, extraction prompt alias context, and alias preservation in `tests/unit/test_character_bible_module.py`.
- Candidate preparation/adjudication has been extracted into `character_bible_v1/candidate_resolution.py`, and discovery-backed candidates now pass through adjudication instead of bypassing it.
- Entity adjudication prompt wording now permits evidence-backed alias/full-name collapses while explicitly guarding against brittle substring, surname, or numbered-role merges.
- Artifact-edit guard coverage now makes broad character identity merge/deprecation attempts return `unsupported_action` / `unsupported_artifact_edit` instead of presenting a plausible single-artifact proposal. Round 5 coverage includes direct identity changes, identity removal, camelCase and nested/dotted identity fields, merge/deprecation markers, manifest identity drift, missing existing identity, empty master updates, and master-definition removal.
- Downstream graph generation now resolves scene-index character IDs through the character-bible resolver, including aliases, before deduplication. The Round 4 material fix prevents a fresh run from emitting `brick_braddock` graph edges after the character-bible stage has collapsed Brick Braddock into canonical `brick`.
- Earlier Story 198 implementation checks passed with focused `37 passed`, full unit `867 passed`, full Ruff, and methodology compile/check before the Round 4 graph fix.
- Post-Round-4 downstream focused tests passed with `28 passed` for `tests/unit/test_entity_graph_module.py tests/unit/test_character_bible_module.py`, and targeted Ruff passed for the downstream graph/test change.
- Round 7 tightened two material edges: generic `entity_id`/`entityId` fields are now identity fields for bible edit blockers, and candidate alias adjudication separates the LLM merge group from the surviving artifact identity so the strongest source candidate can remain the emitted bible identity when the LLM canonical name is only an alias.
- The redundancy pass removed the temporary `character_bible_v1/main.py` candidate-resolution compatibility shim. Tests now import candidate-resolution helpers from the owner module, and `run_module` calls `prepare_character_candidates` directly.
- Round 8 found and fixed one material candidate-resolution edge: discovery-backed names that are not locally plausible now reach adjudication before filtering, so the LLM can explicitly reject sound cues or normalize a discovered name instead of the code silently dropping it before trace generation.
- Round 8 also fixed one redundancy-cleanup fallout: `tests/unit/test_character_naming_regression.py` now imports naming helpers from the candidate-resolution owner module and its stale `THUG` expectation matches the current adjudication-first policy.
- Round 9 found and fixed one material artifact-edit edge: split identity paths like `character.id`, `entity.id`, nested `character.id`, and list-contained identity references are now treated as identity drift, and existing drift markers cannot be removed as if they were normal non-identity edits.
- Round 10 found and fixed one material artifact-edit edge: existing merge/deprecation markers in the current master definition now block edits even when a replacement payload tries to remove the marker and otherwise look like a normal description edit.
- Round 12 found and fixed one material artifact-edit edge: direct backend/API bible-manifest edits can no longer falsify unchanged master-definition entry metadata, such as version or provenance, without supplying a replacement master payload.
- Round-12 current focused Story 198 unit coverage passed with `80 passed, 14 deselected` across candidate collapse, naming-regression collection, broad unsupported identity-edit behavior, API edit rejection, chat helper blockers, and graph alias resolution. Full unit coverage passed with `900 passed, 183 deselected, 1 warning`; Ruff, `git diff --check`, and methodology compile/check also passed.

### Browser / API Evidence

- Current route evidence is captured in `docs/reports/story-198-brick-steel-character-adjudication/browser/`: `characters-desktop.png` (1440x1000), `characters-mobile.png` (390x844), `cdp-console.json`, and `route-evidence.md`.
- The current browser packet loaded `http://127.0.0.1:5199/brick-steel-full-retired/characters` without exceptions or failed requests. Desktop and mobile card-heading evidence includes `Brick` and does not include a separate `Brick Braddock`; raw page text can still include `Brick Braddock` as alias/descriptive canon under canonical Brick.
- Current API groups expose only canonical Brick for Brick character/bible/continuity current groups, while historical duplicate artifacts remain on disk.
- The chat/artifact-edit correction loop is currently honest at the helper/API layer: broad merge/deprecation and identity-drift attempts for the duplicate character return `unsupported_action` / `unsupported_artifact_edit` with no proposed single-artifact edit action, rather than claiming canon was changed.
- Existing browser chat-action evidence remains valid for the unsupported identity-merge path: a seeded ChatPanel action reached the real artifact-edit endpoint, returned `422 unsupported_artifact_edit`, surfaced the unsupported edit error on desktop and mobile, and did not create a new bible-manifest version. That evidence does not exercise live LLM tool selection.

### Central Tenet Check

- **T0 - Data Safety:** old bible versions are preserved; unsupported identity edits do not create partial new versions or delete the duplicate in place.
- **T1 - AI-Coded:** adjudication decisions, aliases, and unsupported-action blockers are traceable in annotations/tested payloads.
- **T2 - Architect for 100x:** the fix routes aliases through the LLM adjudicator and resolver seams instead of brittle name-only UI hiding.
- **T3 - Fewer Files:** ownership stays in candidate resolution, bible identity-edit guards, and graph ID resolution rather than a second UI-only grouping path.
- **T4 - Verbose Artifacts:** baseline artifact refs, route screenshots/console data, and API blocker payload behavior are recorded.
- **T5 - Ideal vs Today:** fresh runs move toward "AI fixes canon honestly"; unsupported live edit requests now fail transparently until a real cross-artifact merge workflow exists.

### Remaining Validation

1. Complete; build, loop-verify, validation, production refresh, browser
   evidence, and `/mark-story-done` are current. Next repo step is
   `/check-in-diff`.

### Repo-Fit / Alternatives

- AI-only was insufficient here because the pre-fix control-flow bug prevented the AI adjudicator from running, and artifact merge persistence/provenance must remain deterministic.
- Pure code name heuristics are too brittle for the Ideal and ADR-001; they risk merging unrelated people with shared first/last tokens. The code should route candidates through the existing LLM adjudicator and only own the persistence/control-flow guarantees.
- The chosen hybrid path matches ADR-001's LLM adjudication gate, ADR-002's honest UI/chat behavior, and ADR-003's upstream artifact-edit principle. Round 1 fixed the pipeline owner first and made the chat correction loop honest without pretending a full merge feature exists.

### Structural Health Check

- `make check-size` passed but reported existing large files. Round 1 touched watchpoints included `character_bible_v1/main.py` 1060 lines, `entity_discovery_v1/main.py` 505 lines, `ai/artifact_editing.py` 521 lines, `api/artifact_manager.py` 630 lines, `EntityListPage.tsx` 593 lines, and `EntityDetailPage.tsx` 905 lines.
- To respect the large-file rule, candidate-resolution logic moved out of `character_bible_v1/main.py` before behavior changes, and the identity-edit guard lives in focused helper/API seams rather than growing a new UI-only workaround.
- No new cross-layer merge/deprecation schema is planned unless implementation proves the unsupported blocker is inadequate. If a real merge contract is added, update Pydantic schemas before API/UI use.

### Verification

- Earlier focused tests: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest -m unit tests/unit/test_character_bible_module.py tests/unit/test_chat_artifact_edits.py tests/unit/test_artifact_editing.py`
- Earlier backend closeout evidence: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` and `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`.
- Post-Round-4 downstream evidence: `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest -m unit tests/unit/test_entity_graph_module.py tests/unit/test_character_bible_module.py` passed with `28 passed`; targeted Ruff passed for the downstream graph/test change.
- Round-12 current focused evidence: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest -m unit tests/unit/test_chat_artifact_edits.py tests/unit/test_artifact_editing.py tests/unit/test_api_artifact_editing.py tests/unit/test_character_bible_module.py tests/unit/test_character_naming_regression.py tests/unit/test_entity_graph_module.py` passed with `80 passed, 14 deselected`.
- Round-8 direct naming-regression evidence: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_character_naming_regression.py` passed with `14 passed`.
- Round-12 current full unit evidence: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed with `900 passed, 183 deselected, 1 warning`.
- Round-12 current docs/methodology evidence: Ruff, `git diff --check`, `pnpm methodology:compile`, and `pnpm methodology:check` passed.
- Round-14 clean-loop evidence: candidate-resolution, artifact-edit, graph, and docs shards returned no material findings. Final focused Story 198 suite passed with `80 passed, 14 deselected`; full unit passed with `900 passed, 183 deselected, 1 warning`; Ruff, `git diff --check`, `pnpm methodology:compile`, and `pnpm methodology:check` passed.
- Validation pass 20260505-0709: focused Story 198 suite passed with `80 passed, 14 deselected`; Ruff passed; UI lint passed; UI `npx tsc -b` passed with the existing npm `min-release-age` warning; `pnpm methodology:check`, `git diff --check`, and `make check-size` passed. The exact worktree command `make test-unit PYTHON=.venv/bin/python` failed four OTIO export tests with `RuntimeError: bad any cast` from `opentimelineio` under Python 3.14.3; rerunning the full unit suite with the established project venv, `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`, passed with `900 passed, 183 deselected, 1 warning`.
- Post-validate environment fix: the ignored worktree `.venv` was replaced with a symlink to `/Users/cam/Documents/Projects/cine-forge/.venv` after reproducing the OTIO `bad any cast` issue under the old Python 3.14.3 venv. The exact command `make test-unit PYTHON=.venv/bin/python` then passed with `900 passed, 183 deselected, 1 warning`.
- Final reset-shard-C validation consistency evidence after continuity follow-up: `.venv` is still a symlink to `/Users/cam/Documents/Projects/cine-forge/.venv`, and `make -n test-unit PYTHON=.venv/bin/python` expands to `PYTHONPATH=src .venv/bin/python -m pytest -m unit`. This bounded shard did not start a full unit run. The expanded focused Story 198 suite, including `tests/unit/test_artifact_manager_artifact_groups.py`, passed with `84 passed, 14 deselected`; Ruff, `git diff --check`, and `pnpm methodology:check` passed.
- Final-final validation/story-gate consistency: Story 198 remains `In Progress` with `/mark-story-done` unchecked. Current check evidence aligns to the focused Story 198 suite (`84 passed, 14 deselected`), full unit (`904 passed, 183 deselected, 1 warning`), UI lint, UI typecheck, Ruff, `git diff --check`, and `pnpm methodology:check`. Methodology warnings are the known `api_service_and_operator_console`, `generation_and_visualization`, and UI scout freshness warnings.
- Live refresh evidence: `story198-brick-steel-character-refresh-20260505` refreshed `character_bible` with `character_bible/brick:v2` and `bible_manifest/character_brick:v2`; `story198-brick-steel-graph-refresh-20260505` refreshed `entity_graph/project:v2`; `story198-brick-steel-continuity-refresh-20260505` refreshed `continuity_index/project:v2` and canonical Brick continuity states; `docs/reports/story-198-brick-steel-character-adjudication/live-refresh-evidence.md` records refs, costs, and preservation of historical `brick_braddock` artifacts.
- Browser route evidence: `docs/reports/story-198-brick-steel-character-adjudication/browser/characters-desktop.png`, `characters-mobile.png`, `cdp-console.json`, and `route-evidence.md` now prove the live Characters route card headings include `Brick` and no separate `Brick Braddock` card on desktop/mobile, no current API group contains `brick_braddock`, and console/page/response captures are clean.
- Browser chat/action evidence: `docs/reports/story-198-brick-steel-character-adjudication/browser/chat-action-evidence.md` records desktop/mobile ChatPanel action proof on a disposable project copy; clicking the real UI action hit the artifact-edit endpoint, returned the expected unsupported identity-merge blocker, and created no new duplicate bible-manifest version.
- Reset-shard-B live artifact/browser evidence: live API and stage cache expose only canonical Brick for Brick character/bible current groups; refreshed `entity_graph/project:v2` has no `brick_braddock` id matches; historical duplicate artifacts still exist; desktop/mobile route evidence has `Brick` but no separate `Brick Braddock` card heading; existing chat-action browser evidence remains valid for the unsupported identity-merge path with no new manifest version and no production artifact mutation.
- UI checks only if UI files change: `pnpm --dir ui run lint`, `cd ui && npx tsc -b`, and `pnpm --dir ui run build`.
- Methodology surfaces only if story metadata changes after this plan: `pnpm methodology:compile` and `pnpm methodology:check`.
- Browser verification: `/brick-steel-full-retired/characters`, canonical `brick` after-state, and the chat/artifact edit path that asks to merge/deprecate the duplicate.

## Work Log

20260430-1133 - story-created: created from approved inbox triage for Brick/Brick Braddock duplicate character resolution and the failed in-app AI artifact-edit attempt. Next step: `/build-story 198`.
20260504-2154 - build-story exploration: verified Story 198 was Pending with complete gates, read Ideal/spec/ADR/state context, and traced the production duplicate through baseline artifacts. The Brick & Steel project had `BRICK` and `BRICK BRADDOCK` in `scene_index/project/v2.json`, copied into `entity_discovery_results/project/v1.json`, emitted as separate `character_bible/brick/v1.json` and `character_bible/brick_braddock/v1.json`, and referenced separately by `entity_graph/project/v1.json`. Pre-fix code probe showed discovery-backed character candidates skipped second-pass adjudication entirely (`decision_trace_len=0`), so the existing merge-capable adjudication helper never saw the alias pair. Pre-fix chat-edit probe showed a merge-like `character_id` edit returned `proposal_ready` for one bible manifest rather than an honest merge/deprecation or unsupported-action blocker. Plan updated to fix candidate resolution first, add regression tests before behavior changes, and make fake cross-artifact merge edits explicit blockers.
20260504-2212 - loop-verify docs shard: aligned task truth with current build-story evidence. Artifact/probe capture, regression fixture, owner classification, implementation, focused tests, required backend checks, methodology compile/check, and conditional UI/eval check handling are tracked as done; UI route evidence, exact in-app chat trace, downstream navigation verification, browser verification, validation, and mark-done remain open.
20260504-2230 - loop-verify Round 2 shard: corrected stale post-Round-1 wording so the story no longer presents implemented candidate-resolution and unsupported identity-edit work as the next plan. Remaining work is now explicitly UI/chat/browser evidence, downstream reference/navigation verification, redundancy review, `/validate`, and `/mark-story-done`.
20260504-2236 - loop-verify Round 3 docs shard: rechecked the story, methodology state, generated views, and baseline report for acceptance-evidence honesty. No material truth issue found: Story 198 remains In Progress, baseline evidence remains explicitly pre-fix, and UI/chat/browser/downstream validation remains open. Reran `pnpm methodology:compile`, `pnpm methodology:check`, and `git diff --check`; methodology still reports the existing architecture-audit and UI-scout freshness warnings.
20260504-2248 - loop-verify Round 4 docs/evidence shard: fixed material acceptance bookkeeping after Round 3 and the main-thread Round 4 downstream graph fix. Characters route evidence is now documented from desktop/mobile screenshots and `cdp-console.json`; the route currently still shows `Characters 15`, `Brick`, and `Brick Braddock` because production artifacts were not rerun/replaced. Chat/API identity merge evidence is marked done through helper/API unsupported-action coverage, not a live browser transcript. Downstream acceptance now records the `entity_graph_v1` material fix: graph character edge IDs resolve through the character-bible resolver including aliases, preventing fresh runs from emitting `brick_braddock` graph edges after the bible collapse. Evidence from main thread: focused `tests/unit/test_entity_graph_module.py tests/unit/test_character_bible_module.py` passed (`28 passed`) and targeted Ruff passed. `/validate` and `/mark-story-done` remain open; Round 4 resets because the graph fix was material.
20260505-0019 - loop-verify Round 6 docs/evidence shard: refreshed acceptance bookkeeping after the Round 5 identity-edit guard broadening. Build-story implementation is now recorded complete, with current focused Story 198 unit evidence passing (`62 passed`) for discovery-backed Brick candidate collapse, alias scene-presence deduplication, broad unsupported identity-edit behavior across chat/helper/API save paths, and entity-graph alias resolution. The live Brick & Steel Characters route still shows both `Brick` and `Brick Braddock` because the production artifact set was not rerun or replaced; that remains an open live-evidence gate rather than a claim that the existing immutable artifacts were mutated. `/validate` and `/mark-story-done` remain open.
20260504-2319 - loop-verify Round 7/main redundancy pass: validated the current Round 7 patches before the next reset with focused Story 198 tests (`67 passed`), full unit tests (`887 passed, 183 deselected, 1 warning`), Ruff, and `git diff --check`. Round 7 material fixes covered generic `entity_id`/`entityId` identity blockers and surviving artifact identity selection when adjudication groups a full name under a shorter alias. The redundancy pass then removed the temporary candidate-resolution compatibility shim from `character_bible_v1/main.py`, moved tests to the real `candidate_resolution` owner seam, and kept runtime monkeypatch injection on that owner module. Targeted candidate tests passed (`20 passed`) and targeted Ruff passed. This was a material cleanup, so the next loop-verify round must reset across the full Story 198 scope.
20260504-2326 - loop-verify Round 8 reset: Round 8 was not clean. Candidate-resolution review found a material traceability bug where discovery-backed but locally implausible names were filtered before adjudication; fixed so discovery-backed names reach the adjudicator first and added regression coverage. Full unit then exposed one remaining import fallout from the candidate-resolution extraction in `tests/unit/test_character_naming_regression.py`; updated that test to import the owner module and corrected its stale `THUG` expectation to match the current adjudication-first policy. Evidence after fixes: focused Story 198 suite passed (`68 passed, 14 deselected`), direct naming regression passed (`14 passed`), full unit passed (`888 passed, 183 deselected, 1 warning`), Ruff passed, and `git diff --check` passed. Because Round 8 made material changes, loop-verify must reset again across the full Story 198 scope.
20260504-2339 - loop-verify Round 9 reset: Round 9 was not clean. Artifact-edit review found a material identity-path gap where split identity paths such as `character.id`, `entity.id`, nested `character.id`, and list-contained identity references were not treated as identity drift, and an edit could remove an existing drift marker as if it were an ordinary artifact edit. Added guard coverage in the chat/helper/API save path and backend apply tests. Evidence after fixes: focused Story 198 suite passed (`77 passed, 14 deselected`), full unit passed (`897 passed, 183 deselected, 1 warning`), Ruff passed, and `git diff --check` passed. Because Round 9 made material changes, loop-verify must reset again across the full Story 198 scope.
20260504-2345 - loop-verify Round 10 reset: Round 10 was not clean. Artifact-edit review found a material existing-marker gap where a current master with `merge_into` could be edited by replacing the master payload without the marker, hiding merge/deprecation state as if the request were an ordinary description edit. `detect_unsupported_identity_edit` now checks the current master for merge/deprecation intent before accepting the replacement payload, and backend regression coverage preserves the blocker. Evidence after fixes: focused Story 198 suite passed (`78 passed, 14 deselected`), full unit passed (`898 passed, 183 deselected, 1 warning`), Ruff passed, `git diff --check` passed, and methodology compile/check passed. Because Round 10 made material changes, loop-verify must reset again across the full Story 198 scope.
20260504-2349 - loop-verify Round 11 reset: Round 11 was not clean because the docs/evidence shard found missing Round 10 methodology compile/check evidence in the story closeout record and added it to the Round 10 reset entry. Candidate, artifact-edit, and graph shards found no code issues; their focused shard checks passed. The docs shard reran methodology compile/check, verified route evidence and screenshots still describe stale production data honestly, and kept `/validate` plus `/mark-story-done` open. Because Round 11 made a material evidence change, loop-verify must reset again across the full Story 198 scope.
20260504-2356 - loop-verify Round 12 reset: Round 12 was not clean. Artifact-edit review found a material manifest/master truth gap where direct backend/API bible-manifest edits could keep the current master payload but falsify the master-definition entry metadata, such as version or provenance, without providing replacement master content. Backend and API guard coverage now reject unchanged-master metadata drift. Evidence after fixes: focused Story 198 suite passed (`80 passed, 14 deselected`), artifact-edit shard passed (`45 passed`), full unit passed (`900 passed, 183 deselected, 1 warning`), Ruff passed, and `git diff --check` passed. Because Round 12 made material changes, loop-verify must reset again across the full Story 198 scope.
20260505-0002 - loop-verify Round 13 reset: Round 13 was not clean. The docs/evidence shard fixed material browser-evidence bookkeeping: Characters route screenshots remain valid current stale-data evidence, and helper/API tests remain valid artifact-edit honesty evidence, but the story no longer claims the full browser chat/artifact-edit verification gate is complete. Candidate, artifact-edit, and graph shards found no code issues. Evidence after fixes: methodology compile/check passed with existing architecture/UI-scout warnings, `git diff --check` passed, and production artifact rerun/replacement, browser chat verification or explicit deferral, `/validate`, and `/mark-story-done` remain open. Because Round 13 made a material evidence change, loop-verify must reset again across the full Story 198 scope.
20260505-0009 - loop-verify Round 14 clean: Round 14 completed with no material findings across candidate-resolution, artifact-edit, graph, and docs/evidence shards. Final focused Story 198 unit coverage passed (`80 passed, 14 deselected`), full unit coverage passed (`900 passed, 183 deselected, 1 warning`), Ruff passed, methodology compile/check passed with the existing architecture/UI-scout warnings, and `git diff --check` passed. Remaining gates are intentionally open: rerun or replace stale Brick & Steel production artifacts, complete or explicitly defer the full browser chat/artifact-edit verification, then run `/validate` and `/mark-story-done`.
20260505-0709 - validate: findings-first review found no material Story 198 code defect in candidate adjudication, unsupported bible identity-edit blocking, or graph alias resolution. Fresh focused Story 198 tests, Ruff, UI lint, UI type-check, methodology check, diff check, and size check passed. The exact worktree full-unit command `make test-unit PYTHON=.venv/bin/python` failed four OTIO export tests with `RuntimeError: bad any cast` from `opentimelineio` under Python 3.14.3; the established project venv full-unit command passed with `900 passed, 183 deselected, 1 warning`. Recommendation: keep open, because production Brick & Steel artifact rerun/replacement and the full browser chat/artifact-edit verification or explicit deferral remain part of this story's acceptance surface.
20260505-0753 - loop-verify follow-up material fix: resolved the remaining live gates. The ignored worktree `.venv` now points at the primary project venv and the exact `make test-unit PYTHON=.venv/bin/python` command passed. Added current-stage artifact-group filtering in `ArtifactManager` with regression coverage so stage-retired entity groups stop appearing as current without deleting historical folders. Refreshed live Brick & Steel `character_bible` and `entity_graph` in place with this worktree's code: current refs are `character_bible/brick:v2`, `bible_manifest/character_brick:v2`, and `entity_graph/project:v2`; `Brick Braddock` survives as a Brick alias, historical `brick_braddock` files are preserved, and current API groups no longer expose `brick_braddock` as a character/bible-manifest group. Browser route evidence now passes on desktop/mobile, and the earlier disposable ChatPanel browser proof covers the unsupported identity-merge action path. Because this made a material source and artifact truth change, loop-verify and validation must reset once more before mark-done.
20260505-0758 - loop-verify reset shard C: verified validation/regression consistency after the material follow-up. `.venv` still points at the primary project venv; `make -n test-unit PYTHON=.venv/bin/python` uses `.venv/bin/python -m pytest -m unit`; a broad unit process was already running at shard start, so this pass did not start another full unit run. The expanded focused Story 198 suite including artifact-manager current-stage filtering and the existing identity-edit suites passed (`82 passed, 14 deselected`), Ruff passed, and mark-done remains unclaimed: Story 198 is still `In Progress` with the `/mark-story-done` gate unchecked.
20260505-0759 - loop-verify reset shard B: verified live Brick & Steel artifact/browser evidence after `story198-brick-steel-character-refresh-20260505` and `story198-brick-steel-graph-refresh-20260505`. Live API and stage cache expose only `character_bible/brick:v2` and `bible_manifest/character_brick:v2` for Brick character/bible current groups; refreshed `entity_graph/project:v2` has no `brick_braddock` id matches; historical duplicate artifacts remain on disk; desktop/mobile route evidence includes `Brick` and no separate `Brick Braddock` card heading; existing chat-action browser evidence remains valid for the unsupported identity-merge path. Patched documentation only to remove stale wording around post-refresh route truth and browser chat-action completeness.
20260505-0808 - continuity follow-up: review found stale `continuity_state/character_brick_braddock_*` groups still visible as downstream stale groups after the character/graph refresh. Added continuity state/index to the current-stage artifact-group filter, extended regression coverage so retired continuity states remain readable but stop appearing as current groups, and refreshed live Brick & Steel continuity with `story198-brick-steel-continuity-refresh-20260505` (`22` artifacts, `$0.126057`). Current stage cache now has canonical `character_brick_scene_001:v2`, `character_brick_scene_004:v2`, and `character_brick_scene_005:v2` refs, `continuity_index/project:v2` has no `brick_braddock` ids, live API groups expose no current `brick_braddock` group, and desktop/mobile Characters route evidence was regenerated from a restarted backend.
20260505-0812 - loop-verify final reset shard C: verified validation and story-gate consistency after the continuity follow-up. The focused Story 198 suite includes `tests/unit/test_artifact_manager_artifact_groups.py`, which covers current-stage filtering for retired character, bible-manifest, and continuity-state groups while preserving historical reads; the suite passed with `84 passed, 14 deselected`. Ruff, `git diff --check`, and `pnpm methodology:check` passed. Full unit was intentionally not rerun in this bounded shard. Story 198 remains `In Progress`, and `/mark-story-done` remains unchecked.
20260505-0819 - loop-verify final-final shard C: corrected validation/story-gate bookkeeping so current Story 198 evidence matches the latest check set: focused Story 198 suite `84 passed, 14 deselected`, full unit `904 passed, 183 deselected, 1 warning`, UI lint/typecheck passed, Ruff passed, `git diff --check` passed, and `pnpm methodology:check` passed with only the known methodology warnings. Story 198 remains `In Progress`, and `/mark-story-done` remains unchecked.
20260505-0824 - loop-verify final clean-only pass: verified docs/state surfaces after the exact methodology-note fix. `git diff --check` and `pnpm methodology:check` passed with only the known methodology warnings; Story 198, methodology state, generated stories view, and methodology graph all record the current evidence. Remaining validation was narrowed to `/mark-story-done` only.
20260505-0851 - validate: findings-first review found no material defects in the Story 198 diff. Fresh validation evidence: `make test-unit PYTHON=.venv/bin/python` passed (`904 passed, 183 deselected, 1 warning`); focused Story 198 suite passed (`84 passed, 14 deselected`); Ruff, UI lint, UI typecheck, `pnpm methodology:check`, `git diff --check`, and `make check-size` passed. Live artifact/browser evidence remains current: canonical Brick is the only current Brick character/bible/continuity group, `Brick Braddock` remains preserved as alias/history, refreshed graph and continuity index contain no `brick_braddock` ids, and desktop/mobile Characters-route evidence is clean. Recommendation: close now; remaining gate is `/mark-story-done`.
20260505-0903 - mark-story-done: closed Story 198 after confirming all acceptance criteria, task checkboxes, validation evidence, live refresh evidence, browser evidence, and tenet checks were complete. Status is now `Done`, generated planning surfaces were refreshed, and the recommended next step is `/check-in-diff`.

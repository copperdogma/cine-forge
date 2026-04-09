# Scout 018 — dossier-methodology-hardening-audit

**Requested source artifact:** `docs/scout/scout-018-dossier-methodology-hardening-audit.md` was not present in this worktree at audit time.
**Audit basis:** Closest matching Dossier-style methodology-hardening checklist classes from the current Storybook / sibling-repo audits, checked against current CineForge after Stories 145, 146, and 147.
**Audited:** 2026-04-08
**Scope:** Audit which candidate post-migration methodology-hardening misses still genuinely need follow-up in CineForge, versus which ones were already fixed here or do not apply to this repo.

## Result

10 valid items were implemented in Story 154.
9 candidate items remain superseded or not applicable in this repo.

## Implemented Checklist

- [x] 1. Widen the active-surface lint boundary.
  Outcome: the compiler now checks README, Ideal/spec/eval docs, the methodology audit artifact, ADRs, scout index, inbox, and Gemini command wrappers.
- [x] 2. Rewrite the methodology audit artifact out of migration-plan tense.
  Outcome: `docs/methodology-artifact-audit-and-migration.md` now reads as a current contract record with historical-baseline framing.
- [x] 3. Bring the ADR layer under the guardrail and fix stale generated-view guidance.
  Outcome: ADR files are in the active-surface boundary and ADR-003 no longer teaches manual `docs/stories.md` upkeep.
- [x] 5. Add explicit canonical eval lineage metadata.
  Outcome: every registry entry now declares `spec_refs`, `story_refs`, `category_refs`, and `compromise_refs`, and the compiler validates them directly.
- [x] 6. Guard or clean scout history that `/scout` reuses as live context.
  Outcome: `/scout` now treats earlier scout docs as source/date recovery only, not current repo truth.
- [x] 7. Make the published lint contract match the compiler.
  Outcome: the compiler now validates unexpected structured-state keys directly, and the audit artifact’s lint contract was rewritten to match that reality.
- [x] 8. Strengthen generated-view framing for `docs/stories.md` / `story index` language.
  Outcome: live skills/docs were rewritten around generated-view phrasing, including the internal `retrofit-ideal` leaf, and the compiler now rejects unqualified story-index wording on active surfaces.
- [x] 10. Finish the state/graph alignment-check rollout across live methodology-facing skills.
  Outcome: the live methodology skills now include the standard alignment-check line with state/graph/generated-dashboard anchors, including the follow-up cleanup on the remaining methodology-facing skills found during the re-audit.
- [x] 11. Fix `/create-adr` as a methodology front-door surface.
  Outcome: `/create-adr` now includes the alignment check, drops retired `setup.md` guidance, and teaches generated-planning-surface refresh instead.
- [x] 19. Add direct regression coverage for methodology guardrails, not just the happy-path compiler behavior.
  Outcome: `tests/unit/test_methodology_graph.py` now covers explicit eval lineage, category-ref mismatch detection, structured-state key validation, active-surface stale wording, and the `-setup.md` false-positive case.

## Superseded Or Not Applicable

| # | Candidate finding | Resolution |
|---|---|---|
| 4 | Remove the dead manual story-index substrate from `/create-story` | Already handled before this sweep. |
| 9 | Rewrite historical migration stories that overclaim a perfectly clean finish | Still not worth separate action; live surfaces were the real problem. |
| 12 | Clean the inbox surface or guard it like other live methodology docs | No current action; `docs/inbox.md` is empty and the broader guardrail widening already covers the live surface. |
| 13 | Repair retired intake-path guidance | Not applicable in CineForge. |
| 14 | Repair README guidance to missing intake paths | Not applicable in CineForge. |
| 15 | Remove setup-runbook links to an outdated ADR-021 migration guide | Not applicable in CineForge. |
| 16 | Fix a live ADR-creation runbook that still points at retired planning surfaces | Not applicable; CineForge does not ship that runbook. |
| 17 | Fix a live deep-research runbook that still teaches obsolete ADR status flow | Not applicable; CineForge does not ship that runbook. |
| 18 | Fix a `create-adr` support README with the wrong ADR lifecycle | Not applicable; CineForge does not ship that support README. |

## Validation

- `pnpm methodology:compile`
- `pnpm methodology:check`
- `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m pytest tests/unit/test_methodology_graph.py -q`
- `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
- `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/`
- `make skills-check`
- `git diff --check`

## Useful Bundles

- Guardrail / compiler hardening: 1, 3, 6, 7, 8, 19
- Live methodology-surface cleanup: 2, 10, 11
- Eval lineage hardening: 5

## Verification Basis

- Reviewed `docs/stories/story-145-methodology-graph-state-migration.md`
- Reviewed `docs/stories/story-146-legacy-methodology-metadata-backfill.md`
- Reviewed `docs/stories/story-147-problem-first-triage-and-story-workflow-migration.md`
- Reviewed `scripts/methodology-graph.js`
- Reviewed `tests/unit/test_methodology_graph.py`
- Ran targeted `rg` sweeps across `AGENTS.md`, `README.md`, `docs/`, `.agents/skills/`, `.gemini/commands/`, and `docs/decisions/**/adr.md`

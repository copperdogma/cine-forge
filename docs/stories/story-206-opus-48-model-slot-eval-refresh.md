---
id: "206"
title: "Opus 4.8 Model-Slot Eval Refresh"
status: "Done"
priority: "High"
ideal_refs:
  - "R1 (story understanding)"
  - "R2 (character understanding)"
  - "R12 (transparency & control)"
  - "R18 (model improvements collapse scaffolding)"
spec_refs:
  - "spec:2"
  - "spec:3"
  - "spec:8"
adr_refs:
  - "ADR-001"
  - "ADR-003"
depends_on:
  - "035"
  - "204"
  - "205"
category_refs:
  - "spec:2"
  - "spec:3"
  - "spec:8"
compromise_refs:
  - "C3"
input_coverage_refs: []
architecture_domains:
  - "methodology_tooling"
  - "ingest_and_world_building"
roadmap_tags:
  - "evals"
  - "model-refresh"
  - "opus-4.8"
  - "anthropic"
legacy_system: "Cross-Cutting"
---

# Story 206 - Opus 4.8 Model-Slot Eval Refresh

**Priority**: High
**Status**: Done
**Ideal Refs**: R1 (story understanding), R2 (character understanding), R12 (transparency & control), R18 (model improvements collapse scaffolding)
**Spec Refs**: spec:2, spec:3, spec:8
**ADR Refs**: ADR-001 (eval-first model assignment), ADR-003 (model upgrades reduce scaffolding only with evidence)
**Depends On**: Story 035, Story 204, Story 205

## Goal

Evaluate Anthropic `claude-opus-4-8` as a CineForge text/model-slot challenger using existing maintained promptfoo surfaces. The target is a bounded evidence refresh for full-screenplay understanding and character reasoning, not a default change from launch claims.

## Source

- Inbox item dated 2026-05-28 from Conductor Scout 043: `/Users/cam/.codex/worktrees/1375/conductor/docs/scout/scout-043-claude-opus-48-api-eval-opportunities.md`
- Anthropic release page confirms `claude-opus-4-8` availability on 2026-05-28 at unchanged regular Opus pricing.
- Live discovery on 2026-05-29 found `claude-opus-4-8` as callable and `[NEW]` through the Anthropic API.

## Eval Ladder Context

- **Root / parent need**: `spec:8` requires evidence-backed model choices; `spec:2` and `spec:3` require strong screenplay and character understanding; C3 stays only while no single model dominates quality, latency, and cost across default-driving surfaces.
- **Parent evals**: maintained promptfoo tasks for `script-bible` and `character-extraction`.
- **Measured trigger**: `scripts/discover-models.py --check-new` confirmed the account can call `claude-opus-4-8`; the registry has no rows for it yet.
- **Child eval / baseline**: add one Opus 4.8 lane to the two existing task configs, run only that provider, save raw result JSON, and compare quality/latency/cost against current registry leaders and defaults.

## Acceptance Criteria

- [x] Live discovery and pricing evidence for `claude-opus-4-8` are recorded before running paid evals.
- [x] Opus 4.8 is wired into `script-bible` and `character-extraction` without changing production defaults.
- [x] Raw promptfoo result JSON files are saved under `benchmarks/results/`.
- [x] `docs/evals/registry.yaml` records score, latency, cost, measured date, git SHA, result file, and mismatch/runtime classification for each new result.
- [x] C3 implications are explicitly stated; defaults stay unchanged unless measured quality, latency, and cost justify a change.
- [x] The completed Opus 4.8 inbox item is removed only after registry evidence is complete.
- [x] Required focused lint/tests, methodology compile/check, YAML/JSON load, and `git diff --check` pass or blockers are recorded.

## Out of Scope

- Running image, video, render-provider, or video-understanding evals.
- Running a full all-task benchmark matrix.
- Changing production model defaults from discovery or public benchmark claims alone.
- Re-tuning prompts, scorers, or goldens to help Opus 4.8 pass.
- Committing or pushing changes.

## Approach Evaluation

- **Simplification baseline**: the eval itself is the simplification test. If one frontier model clears the maintained targets with acceptable latency/cost, C3 pressure drops; discovery alone is insufficient.
- **AI-only**: run Opus 4.8 directly on existing promptfoo tasks. This is the correct path because the benchmarked behavior is model reasoning, not new code behavior.
- **Hybrid**: provider pricing and result extraction stay in code; quality is still measured by deterministic Python scorers plus Opus rubric judgment.
- **Pure code**: appropriate only for provider-list additions, pricing/cost helpers, raw-result extraction, and registry bookkeeping.
- **Repo constraints / ADRs**: ADR-001 requires eval-first assignment. ADR-003 says model improvements should delete workaround complexity only when measured evidence supports it. The inbox explicitly excludes render-video and still-image lanes.
- **Existing patterns to reuse**: Stories 200, 204, and 205 model-refresh workflow, `scripts/discover-models.py`, `src/cine_forge/ai/llm.py`, `scripts/extract-eval-metrics.py`, `scripts/with_cine_forge_provider_env.py`, promptfoo task provider blocks, and `docs/evals/registry.yaml`.
- **Eval**: `script-bible` distinguishes full-screenplay understanding; `character-extraction` distinguishes character arc, relationship, and evidence-grounding depth. No new scorer or golden is expected unless a run exposes a harness bug.

## Tasks

- [x] Confirm the inbox note, official release/API slug, and live provider discovery.
- [x] Read methodology/spec/ADR/recent model-refresh context and run `make check-size`.
- [x] Add Opus 4.8 pricing/cost support.
- [x] Add Opus 4.8 lanes to `script-bible` and `character-extraction`.
- [x] Run the targeted Opus 4.8 eval set and save result JSON.
- [x] Update `docs/evals/registry.yaml` with measured rows and mismatch/runtime classifications.
- [x] Decide whether any default-changing recommendation is warranted.
- [x] Remove the completed inbox item.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [x] Run required checks for touched scope:
  - [x] Backend minimum: `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python`
  - [x] Backend lint for touched Python files.
  - [x] UI not touched; UI checks are not applicable.
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile` and `pnpm methodology:check`
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`
- [x] UI not touched; browser verification is not applicable.
- [x] Search all docs and update any related to what we touched.
- [x] Verify adherence to Central Tenets (0-5):
  - [x] **T0 - Data Safety:** No user project data mutated; benchmark artifacts are additive.
  - [x] **T1 - AI-Coded:** Provider lanes and registry notes are clear to future agents.
  - [x] **T2 - Architect for 100x:** No default or workaround changes without measured value evidence.
  - [x] **T3 - Fewer Files:** Reuse existing eval/discovery seams rather than adding parallel infrastructure.
  - [x] **T4 - Verbose Artifacts:** Raw results, registry rows, and work log preserve evidence.
  - [x] **T5 - Ideal vs Today:** New model evidence tests whether scaffolding can shrink.

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

- **Owning class/module**: discovery stays in `scripts/discover-models.py`; runtime cost estimates and the Opus 4.8 no-temperature API quirk stay in `src/cine_forge/ai/llm.py`; promptfoo result cost extraction stays in `scripts/extract-eval-metrics.py`; eval truth stays in `docs/evals/registry.yaml`.
- **Data contracts**: no new application-layer contracts. Promptfoo provider rows return existing output, token usage, cost, latency, and metadata fields.
- **File sizes**: `make check-size` reports existing large-file watchpoints. This story keeps large-file edits surgical: `src/cine_forge/ai/llm.py` is `986` lines and receives only a pricing row plus the Opus 4.8 no-temperature guard; `scripts/extract-eval-metrics.py` is `364` lines; benchmark YAML edits are provider-list additions.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/spec.md` model/compromise sections, `docs/methodology/state.yaml`, `docs/build-map.md`, ADR-001, ADR-003, Stories 200/204/205, current eval registry, and the Opus 4.8 official release. No new ADR is needed because this is measurement and tooling, not a product architecture decision.

## Files to Modify

- `src/cine_forge/ai/llm.py` - add Opus 4.8 pricing and omit unsupported `temperature` for Opus 4.8 runtime calls (`986` lines).
- `scripts/extract-eval-metrics.py` - add Opus 4.8 pricing for result-to-registry extraction (`364` lines).
- `benchmarks/providers/anthropic_messages_provider.py` - add a text-only promptfoo provider that uses CineForge's Anthropic runtime wrapper while promptfoo's built-in provider still sends deprecated temperature (`72` lines).
- `benchmarks/tasks/script-bible.yaml` - add Opus 4.8 lane (`155` lines).
- `benchmarks/tasks/character-extraction.yaml` - add Opus 4.8 lane (`226` lines).
- `benchmarks/results/*opus48-2026-05-29.json` - raw promptfoo evidence.
- `docs/evals/registry.yaml` - measured score rows and classifications (`3382` lines).
- `docs/evals/models-available.yaml` - refreshed live discovery cache (`544` lines).
- `docs/inbox.md` - remove the completed Opus 4.8 item after evidence is recorded (`24` lines).
- `docs/stories/story-206-opus-48-model-slot-eval-refresh.md` - story truth and work log.

## Redundancy / Removal Targets

- None expected. This is a new measurable model lane; existing Anthropic, OpenAI, Google, xAI, and Moonshot lanes remain comparators unless registry evidence proves a replacement.

## Notes

- Anthropic regular Opus 4.8 pricing is listed as unchanged from Opus 4.7: `$5` input / `$25` output per 1M tokens. This differs from the older Opus 4.6 cost row in the repo, so the eval must compare cost and latency alongside score.
- `claude-opus-4-7` is also discovered as new, but the inbox and user request are specifically about Opus 4.8.
- Promptfoo 0.121.1 does not yet know Opus 4.8 and its built-in Anthropic Messages provider sends a default `temperature: 0`, which the Opus 4.8 API rejects. The repo-local provider exists only to bridge that current provider gap and should be removed if promptfoo's built-in provider gains correct Opus 4.8 support.

## Plan

Wire Anthropic Opus 4.8 pricing and one provider lane into `script-bible` and `character-extraction`, run only Opus 4.8 with Node 24 through `scripts/with_cine_forge_provider_env.py`, record raw results and registry rows with mismatch classifications, remove the processed inbox note, then validate the touched tooling and methodology surfaces. Production defaults remain unchanged unless Opus 4.8 clearly beats current model-slot strategy on quality, latency, and cost.

## Work Log

20260529-0023 - discovery-and-plan: confirmed the `docs/inbox.md` item from Conductor Scout 043, verified Anthropic's 2026-05-28 release page names `claude-opus-4-8` as available through the Claude API, and live discovery found `claude-opus-4-8` as callable and `[NEW]` with all provider keys configured. Reviewed methodology state, build map, spec model/compromise sections, ADR-001, ADR-003, Stories 200/204/205, current registry baselines, and ran `make check-size`. This story is intentionally limited to `script-bible` and `character-extraction` so it tests long-form screenplay understanding and character reasoning without widening into render/video lanes. Next step: add pricing/provider lanes and run the targeted promptfoo evals.

20260529-0035 - targeted-eval-results: added Opus 4.8 pricing, promptfoo lanes, and a repo-local Anthropic text provider after promptfoo's built-in Anthropic Messages provider failed twice with `temperature is deprecated for this model`. The runtime wrapper now also omits temperature for `claude-opus-4-8`. Targeted results saved under `benchmarks/results/`: `script-bible` 0.9025, 1/1 pass, 53.251s, `$0.1334`; `character-extraction` 0.9326, 3/3 pass, 30.934s, `$0.1034`. Registry rows classify character gaps as model-wrong/non-runtime-blocking for default selection; script-bible is a quality pass but a value/latency miss. No model default changes are warranted, and C3 compromise pressure does not shrink. Removed the completed Opus 4.8 inbox item and refreshed `docs/evals/models-available.yaml`. Next step: run validation.

20260529-0040 - validation-and-closeout: verification passed for the touched scope. Evidence: `PYTHONPATH=src /Users/cam/Documents/Projects/cine-forge/.venv/bin/python -m ruff check src/ tests/ scripts/extract-eval-metrics.py benchmarks/providers/anthropic_messages_provider.py` passed; YAML/JSON loading passed for both task configs, registry, model cache, story metadata, and both Opus 4.8 result files; `/Users/cam/Documents/Projects/cine-forge/.venv/bin/python scripts/check-compromises.py` still reports C3 as `not yet`; `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed with `913 passed, 186 deselected, 1 existing acceptance-mark warning`; `pnpm methodology:compile` and `pnpm methodology:check` passed with existing architecture-audit/UI-scout freshness warnings only; `git diff --check` passed. Redundancy check: the repo-local Anthropic provider is a narrow workaround for promptfoo's stale built-in provider and should be deleted once promptfoo supports Opus 4.8 without sending deprecated temperature. Recommended next step: `/check-in-diff`.

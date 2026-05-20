---
id: "205"
title: "Kimi K2.6 Model-Slot Eval Scout"
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
category_refs:
  - "spec:2"
  - "spec:3"
  - "spec:8"
compromise_refs:
  - "C2"
  - "C3"
input_coverage_refs: []
architecture_domains:
  - "methodology_tooling"
  - "ingest_and_world_building"
roadmap_tags:
  - "evals"
  - "model-refresh"
  - "kimi-k2.6"
  - "moonshot"
legacy_system: "Cross-Cutting"
---

# Story 205 - Kimi K2.6 Model-Slot Eval Scout

**Priority**: High
**Status**: Done
**Ideal Refs**: R1 (story understanding), R2 (character understanding), R12 (transparency & control), R18 (model improvements collapse scaffolding)
**Spec Refs**: spec:2, spec:3, spec:8
**ADR Refs**: ADR-001 (eval-first model assignment), ADR-003 (models improve and workaround pressure should shrink only with evidence)
**Depends On**: Story 035, Story 204

## Goal

Evaluate Moonshot `kimi-k2.6` against representative maintained CineForge text/model-slot eval surfaces and decide whether it is useful enough to pursue for runtime defaults, QA gates, or follow-up multimodal/provider work. This is a scout, not a production default change.

## Source

- User request on 2026-05-20: evaluate Kimi after `CINE_FORGE_MOONSHOT_API_KEY` was added to the main checkout `.env`.
- Inbox search found no current `kimi` or `moonshot` item in this checkout.
- Official Kimi docs list OpenAI-compatible API access at `https://api.moonshot.ai/v1`, `kimi-k2.6` as the recommended K2.6 test model, JSON mode support, and benchmarking defaults of temperature `1.0`, top-p `0.95`, thinking enabled, low concurrency, and high token budgets.

## Eval Ladder Context

- **Root / parent need**: `spec:8` needs current evidence-backed model choices; `spec:2` and `spec:3` need high-quality story, entity, and character understanding; C2/C3 stay only while dedicated QA and tiered model selection are still justified.
- **Parent evals**: maintained promptfoo tasks for `script-bible`, `character-extraction`, `entity-discovery`, and `qa-pass`.
- **Measured trigger**: Moonshot account model discovery returned `kimi-k2.6` and `kimi-k2.5`; before this story the registry had no Kimi rows.
- **Child eval / baseline**: add one Kimi K2.6 lane to the representative task configs, run only Kimi, save raw JSON, and compare quality/latency/cost against registry leaders.

## Acceptance Criteria

- [x] Live Moonshot model discovery and Kimi API-mode evidence are recorded before paid evals.
- [x] Kimi K2.6 is wired into representative maintained promptfoo configs without changing production defaults.
- [x] Raw Kimi promptfoo result JSON files are saved under `benchmarks/results/`.
- [x] `docs/evals/registry.yaml` records score, latency, cost, measured date, git SHA, result file, and mismatch/runtime classification for each Kimi result.
- [x] The story states whether Kimi is useful for any current model slot or only future follow-up.
- [x] Required focused tests, lint, methodology compile/check, YAML/JSON load, and `git diff --check` pass or blockers are recorded.

## Out of Scope

- Changing production model defaults from Kimi discovery or public benchmark claims alone.
- Running image/video understanding, final-render, storyboard, or live provider-floor evals.
- Building a full Moonshot runtime transport unless the scout evidence justifies it.
- Re-tuning prompts, scorers, or goldens to improve Kimi.
- Committing or pushing changes.

## Approach Evaluation

- **Simplification baseline**: one Kimi call per maintained task is exactly the simplification test. If it dominates a model slot, C3 pressure drops; if it fails, tiered routing remains justified.
- **AI-only**: the benchmarked behavior is pure model reasoning. Use existing promptfoo tasks and Opus rubric judging.
- **Hybrid**: provider discovery and cost estimation are code; quality remains deterministic scorer plus LLM rubric.
- **Pure code**: limited to Moonshot env/discovery/cost plumbing and promptfoo provider lanes.
- **Repo constraints / ADRs**: ADR-001 requires eval-first model assignment. ADR-003 says model improvements remove scaffolding only after measured evidence. AGENTS requires live discovery before model-choice work.
- **Existing patterns to reuse**: Story 200 and Story 204 model-refresh workflow, `scripts/discover-models.py`, `scripts/extract-eval-metrics.py`, `scripts/with_cine_forge_provider_env.py`, promptfoo provider blocks, and `docs/evals/registry.yaml`.
- **Eval**: `script-bible`, `character-extraction`, `entity-discovery`, and `qa-pass` distinguish full-script understanding, rich character understanding, recall-oriented entity discovery, and QA-gate safety.

## Tasks

- [x] Verify Kimi/Moonshot API docs and local model availability.
- [x] Read methodology/spec/ADR/recent model-refresh context and run `make check-size`.
- [x] Add Moonshot env alias, model discovery, and Kimi cost-estimation support.
- [x] Add Kimi K2.6 lanes to `script-bible`, `character-extraction`, `entity-discovery`, and `qa-pass`.
- [x] Run the targeted Kimi K2.6 eval set and save result JSON.
- [x] Update `docs/evals/registry.yaml` with measured rows and mismatch/runtime classifications.
- [x] Decide whether any default-changing or follow-up recommendation is warranted.
- [x] Check whether the chosen implementation makes any existing code, helper paths, or docs redundant; remove them or create a concrete follow-up.
- [x] Run required checks for touched scope:
  - [x] Backend focused tests for env/discovery support.
  - [x] Backend lint for touched Python files.
  - [x] UI not touched; UI checks are not applicable.
- [x] If story metadata, ADR metadata, or methodology state changes: `pnpm methodology:compile` and `pnpm methodology:check`.
- [x] If evals or goldens are changed: run `/improve-eval` or equivalent mismatch investigation, classify all mismatches, and update `docs/evals/registry.yaml`.
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
- [x] Validation complete
- [x] Story marked done

## Blocker Summary

N/A

## Blocker Evidence

N/A

## Unblock Condition

N/A

## Architectural Fit

- **Owning class/module**: discovery stays in `scripts/discover-models.py`; promptfoo result cost extraction stays in `scripts/extract-eval-metrics.py`; eval truth stays in `docs/evals/registry.yaml`.
- **Data contracts**: no new application-layer contracts. Promptfoo provider rows return existing output, token usage, cost, latency, and metadata fields.
- **File sizes**: `scripts/discover-models.py` is already large (`783` lines before this story), so changes stay provider-list/query scoped. `docs/evals/registry.yaml` is large (`3322` lines) and should only receive measured rows.
- **Decision context**: Reviewed `docs/ideal.md`, `docs/spec.md`, `docs/methodology/state.yaml`, ADR-001, ADR-003, Story 200, Story 204, current eval registry, and Kimi official API/model/benchmark docs. No new ADR is needed because this is measurement and tooling, not a product architecture decision.

## Files to Modify

- `src/cine_forge/env.py` - add `CINE_FORGE_MOONSHOT_API_KEY` / `MOONSHOT_API_KEY` alias (`126` lines).
- `scripts/discover-models.py` - add Moonshot provider discovery and Kimi tiering (`783` lines).
- `scripts/extract-eval-metrics.py` - add Kimi K2.6 cost estimate (`362` lines).
- `tests/unit/test_env.py` - cover Moonshot env export (`101` lines).
- `tests/unit/test_discover_models_xai.py` - cover Moonshot discovery support (`74` lines).
- `benchmarks/tasks/script-bible.yaml` - add Kimi K2.6 lane (`138` lines).
- `benchmarks/tasks/character-extraction.yaml` - add Kimi K2.6 lane (`209` lines).
- `benchmarks/tasks/entity-discovery.yaml` - add Kimi K2.6 lane (`160` lines).
- `benchmarks/tasks/qa-pass.yaml` - add Kimi K2.6 lane (`191` lines).
- `benchmarks/results/*kimi-k26-2026-05-20.json` - raw result evidence.
- `docs/evals/registry.yaml` - measured Kimi rows and classifications (`3322` lines).
- `docs/evals/models-available.yaml` - refreshed discovery cache if discovery cache is updated.
- `.agents/skills/discover-models/SKILL.md` - keep the skill's provider coverage notes aligned with the script.
- `docs/stories/story-205-kimi-k26-model-slot-eval-scout.md` - story truth and work log.

## Redundancy / Removal Targets

- None expected. This is a new measurable provider lane; existing OpenAI/Anthropic/Google/xAI lanes remain comparators unless registry evidence proves a replacement.

## Notes

- Kimi official docs recommend `kimi-k2.6` for K2.6 testing, with default thinking enabled, temperature `1.0`, top-p `0.95`, max token budgets above ordinary non-thinking JSON tasks, low concurrency, and retries. Promptfoo's native OpenAI-compatible provider is non-streaming, so this scout keeps concurrency at `1` and records any provider interruption as a harness/runtime issue rather than silent model failure.
- Pricing estimates use Kimi K2.6 public token rates of `$0.95` input / `$4.00` output per 1M tokens; official docs confirm per-1M-token billing but the rendered pricing table is not reliably exposed in local text fetches.
- Promptfoo's OpenAI-compatible provider prepends `reasoning_content` to output when `showThinking` is left enabled. Kimi thinking mode remains on, but the Kimi promptfoo lanes set `showThinking: false` so scorers judge final JSON content instead of visible reasoning text.

## Plan

Wire Moonshot discovery and one Kimi lane into the representative eval tasks, run only Kimi K2.6 at low concurrency, update registry evidence with mismatch classifications and a default decision, then validate the touched tooling and methodology surfaces. Production defaults remain unchanged unless Kimi clearly beats current model-slot strategy on maintained evals.

## Work Log

20260520-1259 - discovery-and-plan: searched `docs/inbox.md`, stories, methodology state, registry, and repo files for `kimi` / `moonshot`; no active inbox item exists in this checkout. Live Moonshot `/v1/models` returned `kimi-k2.6`, `kimi-k2.5`, and Moonshot V1 variants with K2.6 at 256k context and text/image/video/reasoning flags. Reviewed `docs/ideal.md`, `docs/spec.md`, `docs/methodology/state.yaml`, ADR-001, ADR-003, Story 200, Story 204, Kimi official API/model/benchmark docs, and ran `make check-size`. Next step: run targeted promptfoo evals and record registry-backed findings.

20260520-1324 - implementation-and-eval: added Moonshot env aliasing, live model discovery, Kimi K2.6 pricing estimates, promptfoo Kimi lanes, and refreshed `docs/evals/models-available.yaml`. First script-bible control run failed JSON parsing because promptfoo exposed Kimi `reasoning_content`; after setting `showThinking: false`, the scored final-content run passed. Final Kimi results: `script-bible` 0.9750 / 78620 ms / $0.0362 estimated; `character-extraction` 0.8780 / 126827 ms / $0.0507 estimated; `entity-discovery` 0.9250 / 70902 ms / $0.0340 estimated; `qa-pass` 0.5938 / 21321 ms / $0.0101 estimated. Decision: Kimi K2.6 is useful as a frontier script-bible comparison or occasional fallback, but not as a default. It is too slow/expensive for entity and character slots, below target for entity, below current character leaders, and unsafe as a QA default because it false-negatived the known-good scene. Registry rows now classify the Kimi mismatches as model-wrong; the QA failure is runtime-blocking if adopted.

20260520-1324 - validation: focused tests passed (`tests/unit/test_env.py tests/unit/test_discover_models_xai.py`, 12 passed), touched Python Ruff passed, YAML/JSON load passed for task configs, registry, model cache, story, and all Kimi result files, and `make test-unit PYTHON=/Users/cam/Documents/Projects/cine-forge/.venv/bin/python` passed (`913 passed, 186 deselected, 1 existing acceptance-mark warning`). `pnpm methodology:compile` and `pnpm methodology:check` passed after removing eval-level Story 205 refs that over-widened derived eval category lineage; both commands report existing architecture-audit/UI-scout freshness warnings only. `git diff --check` passed. Story closed with no default model changes.

# Story 036 — Model Selection and Eval Framework

**Phase**: Cross-Cutting
**Priority**: High
**Status**: To Do
**Depends on**: Story 035 (promptfoo tooling — complete)

## Goal

Select the optimal model for every AI task in the CineForge pipeline using systematic evaluation. Each task needs a **try-validate-escalate triad** — but any of the three steps can be code-based, AI-based, or a mix. The framework must be extensible: as new modules land, new evals get added incrementally.

## Context

CineForge currently defaults to `gpt-4o-mini` (work/verify) and `gpt-4o` (escalate) everywhere. These are ancient. Story 035 validated promptfoo as the eval tool and built a working character extraction benchmark. This story uses that tooling to make actual production model decisions.

### Current AI Task Inventory (17 tasks across 7 modules)

| Module | Task | Input | Try | Validate | Escalate |
|--------|------|-------|-----|----------|----------|
| **script_normalize_v1** | Normalize screenplay text | Full source text (chunked) | AI | AI (QA w/ repairs) | AI (SOTA model) |
| | Extract normalization metadata | Source + produced screenplay | AI | Code (schema check) | AI |
| **scene_extract_v1** | Validate uncertain boundaries | Single scene chunk | AI | Code (heading check) | AI |
| | Enrich scene metadata | Scene text + deterministic data | AI | AI (QA per scene) | AI |
| **project_config_v1** | Detect project metadata | Script + scene index | AI | AI (QA plausibility) | None |
| **character_bible_v1** | Extract character definition | Full script + char metadata | AI | AI (QA: accuracy/depth) | AI |
| **location_bible_v1** | Extract location definition | Full script + loc metadata | AI | AI (QA) | AI |
| **prop_bible_v1** | Discover significant props | Script excerpt | AI | Code (dedup) | None |
| | Extract prop definition | Full script | AI | AI (QA) | AI |
| **entity_graph_v1** | Extract relationships | Entity summaries | AI | Code (dedup/merge) | None |
| **continuity_tracking_v1** | Generate state snapshots | Entity + scene snippet | **Stubbed** | — | — |

### The try-validate-escalate triad isn't always three AI calls

The user's key insight: each step can be code, cheap AI, or expensive AI depending on the task.

**Example — Scene splitting:**
- **Try**: Code-based (regex on headings, Fountain parsing) — already works well
- **Validate**: Cheap model reviews each scene boundary ("is this one scene or two?")
- **Escalate**: SOTA model fixes incorrectly-split scenes

**Example — Character extraction:**
- **Try**: Mid-tier model extracts character bible
- **Validate**: Code checks schema + cheap model checks factual accuracy
- **Escalate**: SOTA model re-extracts with QA feedback

The eval framework must test the right thing for each step: code-based steps don't need model benchmarks, but the AI steps need quality/cost/latency measurements.

## Acceptance Criteria

- [ ] Complete task map documenting every AI call point, input shape, and current try-validate-escalate pattern
- [ ] Eval tasks exist in `benchmarks/tasks/` for every AI-based step (not code-based steps)
- [ ] Golden references exist for each eval (hand-crafted or expert-validated)
- [ ] Python scorers exist for each eval measuring task-specific quality dimensions
- [ ] Each eval has been run across the full model matrix (cheap/mid/SOTA tiers from both OpenAI and Anthropic)
- [ ] Results documented: recommended model per task per step, with cost/quality/latency evidence
- [ ] Model defaults updated in `src/cine_forge/schemas/models.py` to reflect selections
- [ ] Recipe configs updated with new model variable defaults
- [ ] Framework documented so new modules can add evals incrementally

## Non-Goals

- Building a CI system or automated regression suite (local-only, run manually)
- Benchmarking non-LLM components (code-based parsing, schema validation)
- Cost optimization at scale (that's Story 032)
- Judge model research (capture findings but don't block on perfecting the judge)

## Tasks

### Phase 1 — Task Map and Eval Design

- [ ] Audit all modules and document every AI call point with input/output shapes
- [ ] For each task, classify each try-validate-escalate step as: code-only, AI-only, or hybrid
- [ ] Identify which tasks share enough structure to reuse scorers (e.g., all bible extractions)
- [ ] Design golden reference strategy per task type:
  - Character/location/prop extraction → hand-crafted bibles from The Mariner
  - Scene enrichment → validated scene metadata
  - Normalization → known-good screenplay output
  - QA tasks → seed with known-good and known-bad inputs
- [ ] Document the eval plan in `benchmarks/README.md`

### Phase 2 — Build and Run Evals

- [ ] Build evals for normalization tasks (text normalization, metadata extraction)
- [ ] Build evals for scene tasks (boundary validation, enrichment)
- [ ] Build evals for bible extraction tasks (character, location, prop)
- [ ] Build evals for relationship extraction (entity graph)
- [ ] Build evals for QA/validation passes (shared scorer for QA quality)
- [ ] Run full model matrix for all evals
- [ ] Analyze results: pick try/validate/escalate model per task
- [ ] Update model defaults in code and recipe configs
- [ ] Document results and rationale in `benchmarks/results/`

### Incremental Eval Pattern (for future modules)

When a new AI-powered module lands:
1. Add input fixture to `benchmarks/input/`
2. Add golden reference to `benchmarks/golden/`
3. Add prompt template to `benchmarks/prompts/`
4. Add Python scorer to `benchmarks/scorers/`
5. Add promptfoo config to `benchmarks/tasks/`
6. Run eval, pick models, update defaults

## Model Matrix

Models to evaluate (as of Feb 2026):

**OpenAI** (prefix: `openai:`):
- GPT-4.1 Nano (cheapest)
- GPT-4.1 Mini
- GPT-4.1
- GPT-5.2 (SOTA)

**Anthropic** (prefix: `anthropic:messages:`):
- Claude Haiku 4.5
- Claude Sonnet 4.5
- Claude Opus 4.6 (SOTA)

**Google** (prefix: `google:`, uses `GEMINI_API_KEY`):
- Gemini 2.5 Flash Lite (cheapest)
- Gemini 2.5 Flash
- Gemini 2.5 Pro (SOTA)

All three providers must be evaluated for every task. The matrix may grow as new models release. Pin to specific model IDs in configs.

## Technical Notes

- promptfoo is installed globally via npm (`promptfoo` v0.120.24, Node 24 LTS)
- Benchmark workspace: separate git worktree on `sidequests/model-benchmarking` branch
- Python scorers use `get_assert(output, context)` interface
- Dual evaluation: deterministic Python scorer + LLM rubric judge per task
- All evals run locally with `--no-cache` for reproducibility
- Character extraction benchmark from Story 035 provides the template for all future evals

## Work Log

_(Updated as work progresses)_

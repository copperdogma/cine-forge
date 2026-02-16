# Story 035: AI Model Benchmarking System

**Status**: Done
**Created**: 2026-02-15
**Phase**: 8 — Cross-Cutting Polish
**Priority**: High
**Depends On**: None (standalone tooling story)
**Reference Project**: `codex-forge` (`/Users/cam/Documents/Projects/codex-forge`) — production AI pipeline with model selection, cost tracking, and try-validate-escalate patterns

---

## Goal

Build or adopt a systematic model benchmarking system that evaluates AI models across CineForge pipeline tasks to find the optimal cost/quality tradeoff for each. The system should be reusable across projects (like `deep-research`), not CineForge-specific.

CineForge uses AI models for a growing number of tasks with very different quality requirements:

- **Script normalization** (story-004): Format conversion + screenplay understanding
- **Scene extraction** (story-005): Structured data from narrative text
- **Bible generation** (stories 008-009): Character/location/prop synthesis
- **Entity graph extraction** (story-010): Relationship identification
- **Continuity tracking** (story-011): State change detection across scenes
- **Future**: Editorial direction, visual direction, shot planning, role reasoning

Some tasks need SOTA models because even the best results are barely adequate. Others can use cheap models because the work requires LLM smarts but not much of them. Today we guess. This story replaces guessing with data.

---

## Context from codex-forge

The `codex-forge` project (Fighting Fantasy gamebook digitization pipeline) demonstrated several patterns directly relevant to model benchmarking:

### Architecture Patterns Worth Adopting

1. **Recipe-driven task definitions (YAML)**: Each pipeline stage is defined in a recipe with explicit module, model, and parameter choices. Tasks for benchmarking should be similarly declarative.

2. **Try-validate-escalate pattern**: Code-first extraction → validate result → escalate to AI on failure → retry with stronger model. This is exactly the kind of multi-model comparison a benchmarking system should measure.

3. **Instrumentation system**: Comprehensive cost/timing tracking per model per stage. Every LLM call records `model`, `prompt_tokens`, `completion_tokens`, `cost`. Aggregated in `instrumentation.json` with per-model breakdowns. Example output:
   ```
   | model        | prompt_tokens | completion_tokens | cost      |
   |--------------|--------------|-------------------|-----------|
   | gpt-5.1      | 456,789      | 123,456           | $12.35    |
   | gpt-4.1-mini | 332,223      | 111,111           | $11.11    |
   ```

4. **Module registry with metadata**: Modules self-describe via `module.yaml` (input/output schemas, default params, param validation). A benchmarking task definition should follow this same pattern — self-contained, schema-validated, discoverable.

5. **Pricing configuration**: `configs/pricing.default.yaml` maintains a model cost table (`prompt_per_1k`, `completion_per_1k` per model). The benchmarking system needs this for cost/quality ratio calculations.

6. **Dual evaluation approaches**:
   - **Code-based validation**: Regex extraction, structural checks, coverage metrics (e.g., "100% sections found", "all choice targets resolved"). Deterministic, fast, cheap.
   - **AI-judge validation**: When code can't evaluate quality (e.g., "is this character description faithful to the screenplay?"), a stronger model judges the output. More expensive but necessary for subjective tasks.

7. **Model escalation**: Tasks start with cheap models and escalate on validation failure:
   ```python
   models = ["gpt-4.1-mini", "gpt-4.1", "gpt-5.1"]
   for model in models:
       result = extract_llm(text, model=model)
       if validate(result):
           return result  # Found the cheapest model that works
   ```

### What codex-forge Lacked (Benchmarking Gaps)

- **No systematic comparison**: Model selection was manual/intuitive, not data-driven
- **No golden datasets**: No curated set of known-good outputs to score against
- **No leaderboard/aggregation**: Results scattered across run directories, no cross-run comparison
- **Single provider**: Only OpenAI — no Anthropic, Google, xAI comparison
- **No automated scoring**: Validation was pass/fail, not scored on a quality scale

### CineForge Tasks to Benchmark

| Task | Current Model | Evaluation Type | Quality Sensitivity |
|------|--------------|-----------------|---------------------|
| Script normalization | claude-opus-4-6 | AI judge + structural | High — errors cascade |
| Scene extraction | claude-opus-4-6 | Structural + coverage | High — foundation artifact |
| Character bible | claude-opus-4-6 | AI judge | Medium — can iterate |
| Location bible | claude-opus-4-6 | AI judge | Medium — can iterate |
| Entity graph extraction | claude-opus-4-6 | Graph metrics + AI judge | Medium |
| Continuity tracking | claude-opus-4-6 | Structural + AI judge | High — subtle errors |
| Screenplay format detection | code-first | Code (deterministic) | Low — binary decision |
| FDX/Fountain parsing | code-first | Code (deterministic) | N/A — no LLM needed |

---

## Phases

### Phase 1: Deep Research — Build vs. Buy

Use `deep-research` to investigate:

**Research Project A: Existing Tools**
- [ ] `deep-research init "ai-model-benchmarking-tools"` in `docs/research/`
- [ ] Write research prompt covering: existing open-source model benchmarking/evaluation frameworks, their features, how well they match our needs (task-specific eval, cost tracking, multi-provider, custom judges, golden datasets)
- [ ] `deep-research run` → `format` → `final`
- [ ] Evaluate findings against our requirements checklist (below)
- [ ] **Decision gate**: Do any existing tools meet ≥80% of our requirements?

**Requirements Checklist for Existing Tools:**
- [ ] Multi-provider support (OpenAI, Anthropic, Google minimum)
- [ ] Custom task definitions (not just standard benchmarks like MMLU)
- [ ] Support for both code-based and AI-judge evaluation
- [ ] Cost tracking per model per task
- [ ] Golden dataset / reference output management
- [ ] Aggregation and comparison across runs
- [ ] CLI interface (not just web UI)
- [ ] Extensible (custom scoring functions, custom providers)
- [ ] Python-based or Python-friendly
- [ ] Reasonable maintenance/community health

**Research Project B: How to Build (conditional)**
If no existing tool meets needs:
- [ ] `deep-research init "building-ai-model-benchmarking-system"` in `docs/research/`
- [ ] Write research prompt covering: architecture patterns, evaluation frameworks, scoring methodologies (Elo, Bradley-Terry, direct scoring), golden dataset creation, statistical significance in model comparison, cost-normalized quality metrics
- [ ] `deep-research run` → `format` → `final`
- [ ] Synthesize findings into design principles for Phase 3

**Discuss with Cam**: Present findings — existing tool recommendation or build rationale.

### Phase 2: Adopt Existing Tool (conditional — only if Phase 1 finds a good match)

- [ ] Install the chosen tool in a test environment
- [ ] Define 2-3 CineForge benchmark tasks using the tool's format
- [ ] Create golden datasets for those tasks (use SOTA model outputs, manually verified)
- [ ] Run benchmarks against 3+ models (cheap, mid, expensive)
- [ ] Validate: Does it produce actionable cost/quality comparisons?
- [ ] Validate: Can we extend it with custom AI judges?
- [ ] Validate: Does cost tracking match our needs?
- [ ] Document usage patterns for CineForge in `docs/guides/model-benchmarking.md`
- [ ] Add the tool to project dependencies and document setup
- [ ] **Discuss with Cam**: Review benchmark results — do they match intuition? Are they actionable?

### Phase 3: Write Spec for New Tool (conditional — only if Phase 1 finds no adequate existing tool)

- [ ] Synthesize codex-forge patterns + deep research into a tool specification
- [ ] Write `spec.md` covering:
  - **Core concepts**: Tasks, Golden Datasets, Runs, Scores, Leaderboards
  - **Task definition format**: YAML with prompt template, input schema, output schema, evaluation config
  - **Evaluation types**: Code-based (deterministic scoring functions), AI-judge (configurable judge model + rubric), hybrid (code pre-filter + AI judge for survivors)
  - **Provider abstraction**: Pluggable model providers (OpenAI, Anthropic, Google, xAI, local models)
  - **Cost tracking**: Token usage, latency, cost-per-task, cost-normalized quality scores
  - **Golden dataset management**: Reference outputs, versioning, human verification status
  - **Scoring system**: Raw quality score (0-100), cost-normalized score, Elo ratings for pairwise comparison
  - **Aggregation**: Per-task leaderboards, cross-task model profiles, cost/quality Pareto frontiers
  - **CLI interface**: `bench init`, `bench add-task`, `bench run`, `bench compare`, `bench report`
  - **Output format**: JSON results + human-readable reports (like codex-forge's `instrumentation.md`)
  - **Extensibility**: Custom scoring functions, custom providers, plugin system
  - **Statistical rigor**: Multiple runs per model, confidence intervals, significance testing
- [ ] Drop spec at a location Cam specifies (default: `docs/specs/model-benchmarking-spec.md`)
- [ ] **Discuss with Cam**: Review spec before spinning up new project

---

## Acceptance Criteria

### Phase 1 (always required)
- [ ] Deep research completed with at least 2 AI providers
- [ ] Requirements checklist scored for any candidate tools
- [ ] Clear build-vs-buy recommendation with evidence
- [ ] Decision documented in work log

### Phase 2 (if adopting a tool)
- [ ] Tool installed and functional
- [ ] At least 2 CineForge tasks benchmarked with golden datasets
- [ ] Results demonstrate actionable cost/quality differentiation
- [ ] Usage guide written for CineForge context
- [ ] Tool integrated into project workflow

### Phase 3 (if building our own)
- [ ] Spec covers all bullet points above
- [ ] Spec incorporates codex-forge learnings and deep research findings
- [ ] Spec reviewed and approved by Cam
- [ ] Ready to spin up as a standalone project

---

## Constraints

- This is a **tooling story**, not a pipeline feature. The benchmarking system should be a standalone tool (like `deep-research`) usable by any project.
- Do NOT build the tool in this story. Phase 3 produces a spec only. Building happens in its own project.
- Do NOT prematurely optimize CineForge's model choices. Get data first, then make informed changes in follow-up work.
- Golden datasets should use real CineForge inputs (screenplay excerpts) with SOTA-verified outputs, not synthetic data.

---

## Out of Scope

- Building the benchmarking tool itself (separate project)
- Changing CineForge's current model selections (follow-up story after benchmarking data exists)
- Benchmarking non-LLM tasks (image generation, TTS, etc.) — focus on text-in/text-out first
- Continuous benchmarking / CI integration (future enhancement)
- Fine-tuning or model training

---

## Tasks

- [x] **Phase 1**: Deep research — find existing tools, evaluate against requirements
- [x] **Decision gate**: Build vs. buy — **BUY (promptfoo)**. Reviewed with Cam.
- [x] **Phase 2** *(conditional)*: Install, test, validate, and document adopted tool
- [N/A] **Phase 3** *(conditional)*: Write comprehensive spec for new standalone tool — not needed (BUY path taken)
- [x] Update story index (`docs/stories.md`) with this story

---

## Work Log

*(append-only)*

### 20260215 — Story created
- **Action**: Researched codex-forge project architecture; created story with codex-forge learnings incorporated.
- **Evidence**: codex-forge patterns documented in story Context section (recipe-driven tasks, instrumentation, try-validate-escalate, dual evaluation, model escalation, pricing config).
- **Next**: Phase 1 — run deep research on existing AI model benchmarking tools.

### 20260215 — Phase 1 complete: Deep research done, decision made
- **Action**: Ran deep-research with OpenAI (gpt-5.2) and Anthropic (claude-opus-4-6). Both providers converge on the same recommendation.
- **Decision**: **BUY — adopt promptfoo as primary benchmarking framework.**
- **Key findings**:
  - promptfoo scores 93% on must-haves, 83% on should-haves (clears both thresholds)
  - It's the only tool where multi-model comparison is the *core design* — YAML matrix of prompts × providers × test cases
  - Built-in cost tracking with dollar amounts, web UI for leaderboards, CLI-first
  - Python scorers supported via subprocess (minor friction, not a blocker)
  - VC-backed, daily commits, full-time team
  - DeepEval recommended as complement for Python-native CI/CD quality gates (pytest integration)
  - No tool found with 100% coverage, but promptfoo's gaps are addressable with ~3-5 days of lightweight scripts
  - Building from scratch estimated at 4-10+ weeks for equivalent functionality — not worth it
- **Tools NOT recommended**: OpenAI Evals (abandoned), Ragas (RAG-only), Phoenix (observability-focused), LangSmith/Braintrust/Humanloop (proprietary platforms)
- **Evidence**: `docs/research/ai-model-benchmarking-tools/final-synthesis.md` (3,639 words, $2.32 total research cost)
- **Result**: Phase 2 is the active path. Phase 3 (write spec) is NOT needed.
- **Next**: Phase 2 — install promptfoo, define 2-3 CineForge benchmark tasks, validate the workflow.

### 20260215 — Phase 2 complete: promptfoo validated, documented, judge model decided
- **Action**: Installed promptfoo, built two benchmark tasks (scene extraction + character extraction), ran full 7-model evaluations, documented everything in AGENTS.md.
- **Setup**:
  - Node.js upgraded to v24.13.1 LTS (promptfoo requires 22+), installed via nvm
  - promptfoo v0.120.24 installed globally via npm
  - Benchmark workspace at `benchmarks/` in sidequests worktree
- **Benchmark 1 — Scene extraction** (7 models × 1 test case): Pivoted away from this — scene extraction is code-based in CineForge, not a meaningful AI benchmark. Kept as a reference.
- **Benchmark 2 — Character extraction** (7 models × 3 characters): Mirrors the actual `character_bible_v1` module. Three test cases of increasing difficulty:
  - THE MARINER (protagonist, most scenes) — all but Nano passed
  - ROSE (co-lead, hidden backstory) — Nano, Mini, GPT-4.1 failed
  - DAD (flashback-only, dual presentation) — hardest; Haiku produced invalid JSON, Mini and Nano failed
- **Results summary** (avg Python score across 3 characters):
  1. GPT-5.2: 0.917 — best overall, most consistent
  2. Claude Opus 4.6: 0.910 — strongest on main characters
  3. Claude Sonnet 4.5: 0.864 — solid mid-tier
  4. GPT-4.1: 0.831 — decent for the price
  5. GPT-4.1 Mini: 0.795 — fine on easy chars, choked on hard
  6. Claude Haiku 4.5: 0.590 — great on easy, catastrophic on hard (invalid JSON on DAD)
  7. GPT-4.1 Nano: 0.589 — consistently weak
- **Judge model decision**: Claude Opus 4.6 as the standard judge for all evals. Cross-provider judging reduces same-provider bias. Configured via `defaultTest.options.provider` in YAML configs.
- **Dual evaluation validated**: Python scorer + LLM rubric judge catch different failure modes. GPT-4.1 Mini scored 0.915 on Python but 0.62 on LLM judge — the judge caught shallow reasoning the structural check missed.
- **Documentation**: Full promptfoo guide added to AGENTS.md — prerequisites, workspace structure, commands, scorer interface, judge config, 6 pitfalls with workarounds, incremental eval pattern for new modules.
- **Pitfalls discovered and documented**: `max_tokens` truncation trap, `---` prompt separator, `file://` path resolution, Anthropic JSON code blocks, exit code 100, no `--dry-run` flag.
- **Evidence**: `benchmarks/results/character-extraction-run1.json`, `benchmarks/results/scene-extraction-run1.json`, AGENTS.md diff (+118 lines)
- **Follow-up**: Story 036 created for actual model selection using this framework.

# AGENTS.md

This file is the project-wide source of truth for agent behavior and engineering principles. It serves as both a core directive and a living memory for AI agents working on this codebase.

> **The Ideal (`docs/ideal.md`) is the most important document in this project.**
> It defines what CineForge should be with zero limitations at two levels: the
> **product ideal** (what the user should get) and the **execution ideal** (what
> building CineForge should feel like when AI no longer needs scaffolding). Every
> architectural decision should move toward those ideals. Every compromise in the
> spec (`docs/spec.md`) carries a detection mechanism for when it's no longer
> needed. When in doubt about a design choice, ask: "Does this move us toward the
> Ideal?"
>
> The Ideal's primary test: **Is it easy, fun, and engaging?** If using CineForge
> feels like work, something is wrong.
>
> **Preferences exist at two levels.** Vision-level preferences (in `docs/ideal.md`)
> persist across all implementations — they survive even when every compromise is
> eliminated. Compromise-level preferences (on individual compromises in `docs/spec.md`)
> are legitimate investments but die when their compromise is eliminated. Know which
> level you're working at.
>
> **Methodology stack**: `docs/methodology-ideal-spec-compromise.md` explains how
> the dual ideals, category-aligned spec (`spec:1` through `spec:11`),
> `docs/methodology/state.yaml`, generated dashboard views, stories, and evals
> fit together. `docs/methodology/state.yaml` is the canonical planning state.
> `docs/build-map.md` is a generated dashboard view that tracks product need,
> tech need, substrate status, story coverage, ADR refs, and phase governance
> (`climb`, `hold`, `converge`, `unplanned`). Read both when work touches
> planning, methodology, or simplification decisions. Canonical methodology
> bootstrap skill: `/setup-methodology`. Recurring companion skills:
> `/create-eval`, `/improve-eval`, and `/align`.

## Core Agent Mandates

- **GREENFIELD PROJECT — NO BACKWARDS COMPATIBILITY**: This app is under active development with zero real users, zero valuable user data, and zero old processes or file formats to preserve. Do NOT waste time on backwards compatibility shims, migration paths, deprecation warnings, old format support, or "gentle" transitions. When something needs to change, **change it directly**. Delete the old code. Update all call sites. If a schema changes, change it — don't version it. If an API changes, change it — don't keep the old endpoint. The only cost is a `git revert` away.
- **Critical Pushback Required**: When the user proposes an idea, approach, or architecture — push back if it has problems. Point out when an idea is worse than what already exists, when it introduces unnecessary complexity, when it contradicts established patterns, or when it's solving the wrong problem. Sycophantic agreement is actively harmful in design discussions. The user trusts direct, evidence-based disagreement far more than reflexive validation. Say "that's wrong because X" when it's wrong. Say "the spec already handles this better via Y" when it does. This applies to design reviews, spec discussions, architecture decisions, and implementation approach — not to simple task execution.
- **ADR Discipline**: Before making or reviewing architectural, workflow, schema, or UX decisions, read the relevant decision record(s) under `docs/decisions/` and any supporting decision docs under `docs/design/`. If a task does not cite an ADR but the work touches those areas, search for the relevant decision before choosing an approach. If no ADR applies, state that explicitly instead of guessing.
- **No Implicit Commits**: NEVER commit or push changes unless explicitly requested by the user.
- **Security First**: NEVER stage or commit secrets, API keys, or sensitive credentials.
- **Permissioned Actions**: NEVER run `git commit`, `git push`, or modify remotes without explicit user permission.
- **Bundled Permission Counts**: A single user message can authorize multiple sequential actions (for example: validate, mark done, commit, and push). Do not create artificial hard stops between already-approved steps unless a real blocker, risk, or contradiction appears.
- **Verify, Don't Assume**: NEVER assume a library is available or a file has a specific content. Use `read_file` and dependency checks (`package.json`, `pyproject.toml`) to ground your work.
- **Immutability**: Versioned artifacts are immutable. NEVER mutate an existing version in place; always produce a new version with incremented metadata.
- **AI-First Engineering**: Prefer roles, prompts, and structured artifacts over rigid hard-coded business rules. Architecture should facilitate AI reasoning.
- **Baseline = Best Model Only**: Never conclude "AI can't do this" from a cheap model's failure. Always test SOTA first. If the best available model succeeds in one call, there is nothing to build — cheaper models are a cost optimization question, not a capability question. This is the single most expensive mistake in eval-first development.
- **Live Model Discovery First**: Before deciding what models to use for any feature, benchmark, or eval, always run [$discover-models](.agents/skills/discover-models/SKILL.md) so the choice is grounded in the current provider catalogs, not training-cutoff assumptions.
- **Headless Operation**: All core application capabilities (e.g., export, analysis, remediation) MUST be performable via CLI scripts or direct backend calls, bypassing the UI. This ensures AI agents can autonomously operate the system.
- **Coherent Scope Expansion**: If exploration reveals small, tightly coupled work that is necessary to actually satisfy the story goal, expand the current story and update the story file/work log instead of punting it as "out of scope." For larger expansions, surface the recommendation explicitly for approval instead of silently absorbing or silently splitting it out.
- **Relative Effort, Not Calendar Theater**: Unless the user explicitly asks for time estimates, express scope or follow-up effort in relative sizes (`XS`, `S`, `M`, `L`, `XL`), not hours or days. Optimize for coherent AI-sized slices, not human sprint rituals.
- **Definition of Done**: A task is complete ONLY when:
  1. Relevant tests pass (`make test-unit` minimum).
  2. Artifacts are produced and manually inspected for semantic correctness.
  3. Schema validation passes.
  4. If the task touched the UI: browser verification covers both a desktop view and a mobile view, with screenshots or equivalent evidence and clean console output unless a documented environment blocker prevented it. That verification must use a project state reachable through the normal API/driver pipeline for the feature under test, not a hand-seeded or impossible substrate combination, unless the artifact is explicitly labeled as a narrow non-evaluative smoke fixture.
  5. The active story's work log is updated with evidence and next actions.
  6. If the story touched an AI module or eval: every significant eval mismatch is classified as **model-wrong**, **golden-wrong**, or **ambiguous** with evidence. For compromise or detection evals, record whether any remaining failures are **runtime-blocking** or **non-runtime-blocking**. Silently accepting mismatches as noise is a hard stop.
  7. If you ran an eval (promptfoo, pytest acceptance, or any scored test): update `docs/evals/registry.yaml` with the new score, `git_sha`, and date. Stale scores are worse than no scores.

## General Agent Engineering Principles

- **Semantic Quality over Structural Validity**: A JSON that passes a schema but contains "UNKNOWN" or placeholder data is a failure. Assert semantic quality predicates in tests.
- **Boundary Awareness**: Code that works in a unit test can fail in a long-running service (due to state, cache, or import-time definitions). Validate through the service layer or API boundary.
- **Representative UI State Only**: For browser verification, UX judgment, and story acceptance, use project states produced through the normal project/API/driver workflow for the feature under test. Do not count manually copied artifacts, seeded impossible combinations, or bypassed substrate states as product evidence. Synthetic fixtures are allowed only for narrow mechanical smoke tests and must be labeled as non-representative.
- **Package Init Boundaries**: Keep package `__init__.py` files import-light. Do not eagerly import FastAPI apps or other top-level stacks from packages reused by services/helpers; prefer lazy re-exports when package imports would otherwise create circular dependencies during test or driver import.
- **Dynamic Module Loader Safety**: Internal helper containers inside driver-loaded modules should avoid annotation-dependent dataclass/Pydantic magic unless you confirm they survive dynamic import. Prefer plain classes for purely internal state carriers.
- **Dynamic Module Loader Imports**: When splitting a driver-loaded module across helper files, use absolute package imports (`cine_forge...`) instead of relative imports. Driver entrypoints are loaded via `spec_from_file_location`, so absolute imports are the safe default.
- **Process Lifecycle**: Restart long-running backend/API processes after changing schemas or core logic. Hot-reloading is a tool, but a clean restart is the source of truth.
- **Architecture Drift Is Real Debt**: Compatibility shims, duplicate ownership, dead wrappers, placeholder pass-throughs, and widened guards that preserve an obsolete path are bugs even when tests still pass. Remove the obsolete path or re-home the responsibility instead of papering over it.
- **Regression Fixes start with Fixtures**: When a real-world run fails, capture the failing input as a deterministic test fixture BEFORE implementing the fix.
- **Conservative Heuristics**: When building classifiers (screenplay vs. prose), use weighted evidence and confidence scores. Favor "needs_review" over silent incorrectness.
- **Prompt-First Before Model Escalation**: Before escalating to a more expensive model to improve quality, first try strengthening the prompt: add a completeness contract ("verify all items are covered before responding"), add grounding language ("base claims strictly on provided text"), add a verification instruction ("check your output against every requirement"). Only increase model size or reasoning effort after prompt-level improvements have been measured and found insufficient. (Source: Scout 010 — OpenAI GPT-5.4 Prompt Guidance)
- **Lineage Tracking**: Every transformation must record its upstream sources. Data without provenance is noise.
- **Context Traceability**: Every run must persist its full execution context (e.g., `runtime_params`, recipe fingerprints) in its core artifacts (`run_state.json`). Never leave the operator guessing which model or flag produced an outcome.
- **Project-Scoped Preferences**: Store user preferences and settings in `project.json`, not `localStorage`. `localStorage` is ephemeral — it doesn't survive browser clears, doesn't sync across machines, and isn't visible to the backend. Only use `localStorage` for truly throwaway UI state (e.g., collapsed panel memory within a single session). Anything the user would miss if it vanished belongs in project settings.
- **AI-as-Tester**: AI agents have a blind spot — they default to writing deterministic test scripts even when the problem requires judgment and observation. When verifying AI behavior (role persona quality, creative direction coherence, tone consistency), the correct approach is to *have a conversation personally* with the AI component, not just validate JSON structure. Use the subagent pattern: spawn a subagent to conduct a focused multi-turn probe of the AI behavior, then report findings back to the orchestrator. Structural tests (Pydantic schema, field coverage) are necessary but not sufficient — they miss shallow reasoning, wrong tone, and missing creative insight. This complements promptfoo evals, not replaces them.
- **Operator Verification Handoff**: When summarizing completed work, include a brief `Where to verify` pointer whenever there is a concrete way for the user to inspect it themselves. For UI work, name the route or screen and 1-3 interactions. For backend or CLI work, give the command, endpoint, or artifact to inspect. Keep it succinct, grounded in what was actually verified, and make clear the extra check is optional.

## Working Norms

- **Keep the work log live**: Update the active story's work log for every meaningful implementation, investigation, validation, or scope decision.
- **Report impact first**: For substantive progress notes or work-log entries, say what changed, what it improved or failed to improve, what evidence you checked, and what the next falsifiable step is.
- **Debug from artifacts first**: Inspect actual outputs, JSON, eval results, screenshots, and intermediate files before changing code. Prefer evidence-driven diagnosis over guess-and-edit loops.
- **Reuse proven patterns first**: Before inventing a new helper, prompt shape, or workflow, find a working local pattern and adapt it with the smallest change that fits.

## Project Context (CineForge)

- **CineForge** is a film reasoning and production pipeline using immutable artifacts.
- **Core Stack**: Python 3.12+, Pydantic (schemas), YAML (recipes), React (UI).
- **Core Pattern**: Driver orchestrates Modules which consume/produce versioned Artifacts stored in an ArtifactStore.

## Subagent Strategy

Use subagents aggressively to parallelize work and protect the main context window. The orchestrating agent (Opus) is responsible for final quality — always review subagent output before accepting it.

### Model Selection by Task Type

| Task | Model | Rationale |
|------|-------|-----------|
| File search, glob, grep, simple reads | **Haiku** | Fast, cheap, mechanical |
| Write a single focused component/page | **Sonnet** | Good code quality, fast enough |
| Multi-file refactor, architecture decisions | **Opus** | Needs full context and judgment |
| Research/exploration across codebase | **Sonnet** | Good at synthesis, thorough |
| Writing tests for existing code | **Sonnet** | Needs to understand contracts |
| Reviewing/validating generated code | **Opus** | Quality gate, catches subtle issues |
| Writing docs, updating AGENTS.md | **Haiku** | Mechanical text, Opus reviews |

### Guidelines
- **Parallelize independent work only when ownership is clear**: If building 3 pages that don't depend on each other and the write boundaries are already clear, launch 3 subagents simultaneously. If ownership is overlapping or unclear, keep one primary execution path and use subagents for exploration/review instead of concurrent edits.
- **Opus orchestrates, delegates, reviews**: The main agent reads results, spots issues, and iterates — never blindly trusts.
- **Context protection**: Use subagents for tasks that produce large output (exploration, research) to avoid flooding the main context.
- **Fail fast**: If a subagent produces bad output, don't retry the same prompt — adjust the approach or do it yourself.

### Running Log
Track model performance observations in `/memory/subagent-log.md` to refine the table above over time.

## Architecture Rules

These rules prevent the accumulation of god objects and untyped interfaces. They are enforced at plan time (build-story Phase 2) and verified at review time (tenet checklist).

- **Method size**: Methods >100 lines must be decomposed before adding new logic OR carry an explicit `# OVERSIZED: <reason>` comment approved in the story review.
- **Class size**: Classes >500 lines require a decomposition plan in any story that touches them. List the current line count in "Files to Modify." If you are adding to a file this large, first task must be extraction.
- **Inter-layer contracts**: Any data crossing a layer boundary (engine↔service, service↔API, API↔frontend types) must be a Pydantic model defined in a schema file before any code uses it. No stringly-typed dicts as inter-layer protocols.
- **Event schema-first**: Any new event type requires an entry in `src/cine_forge/schemas/events.py` before the call site that emits it.
- **God object check**: Before adding a method to an existing class, state in the story why this responsibility belongs to that class and not a new focused one.
- **`make check-size`**: Run before finalizing any implementation plan. Files flagged at >400 lines must be acknowledged in the plan.

### Known large files (as of Story 115 audit, 2026-03-02)

| File | Lines | Status | Story |
|------|-------|--------|-------|
| `src/cine_forge/ai/chat.py` | 2,191 | Not yet planned | — |
| `tests/unit/test_driver_engine.py` | 1,648 | Test file — exempt from class size rule | — |
| `src/cine_forge/driver/engine.py` | 1,159 | Decomposed (Story 117) — 4 class extractions | Story 117 |
| `src/cine_forge/api/app.py` | 1,032 | Route consolidation done (Story 118) | Story 118 |
| `src/cine_forge/api/service.py` | 1,002 | Decomposed (Story 118) — 3 class extractions | Story 118 |

## Operational Guide

### Common Driver Commands
- **Validate only**: `PYTHONPATH=src python -m cine_forge.driver --recipe configs/recipes/recipe-test-echo.yaml --dry-run`
- **Execute recipe**: `PYTHONPATH=src python -m cine_forge.driver --recipe configs/recipes/recipe-test-echo.yaml --run-id test-001`
- **Resume from stage**: `PYTHONPATH=src python -m cine_forge.driver --recipe configs/recipes/recipe-test-echo.yaml --start-from echo --run-id test-002`

### Test Commands
- **Unit tests**: `.venv/bin/python -m pytest -m unit` (not system pytest — version mismatch)
- **Lint**: `.venv/bin/python -m ruff check src/ tests/`
- **Backend smoke fallback**: if `uvicorn` is unavailable in the active Python env but FastAPI CLI is installed, use `fastapi run src/cine_forge/api/app.py --host 127.0.0.1 --port 8000 --app app` for local browser/API smoke checks.

### Deep Research
For multi-model research tasks, use the `deep-research` CLI tool (v0.3.3+).
- Installed at `/Users/cam/miniconda3/bin/deep-research`
- Available providers: OpenAI (gpt-5.2-pro), Anthropic (claude-opus-4-6), Google (gemini-3.1-pro-preview). xAI key not configured.
- Outputs go under `docs/research/<topic>/`.
- Workflow:
  1. `deep-research init "<topic>" --dir docs/research/` — creates folder with template files
  2. Edit `research-prompt.md` — write the research prompt (keep frontmatter)
  3. `deep-research run` — sends to all available providers in parallel
  4. `deep-research run --provider openai --provider google` — limit to specific providers
  5. `deep-research run --mode deep` — use deep-research APIs (OpenAI Responses API + Google Interactions API); providers without deep support fall back to standard mode
  6. `deep-research format` — renames placeholder files based on content, cleans up unused slots
  7. `deep-research final [model]` — synthesizes all reports into final report (aliases: opus, sonnet, chatgpt, gemini, grok; default: best available)
  8. `deep-research prepare-final` — assembles for manual pasting if API fails
- Utility commands:
  - `deep-research status` — show current state of the research project
  - `deep-research stub [provider...]` — create blank report stubs for manual paste-in (e.g. `stub xai` for providers without API keys)
  - `deep-research check-providers` — check for newer SOTA models and update config
- Pitfalls:
  - **NEVER `cd` into a research dir then delete it** — kills CWD and breaks all subsequent shell commands. Always use absolute paths.
  - `deep-research run` expects to be run from within the project directory (where `research-prompt.md` lives).
  - If a report file already exists (even an error file), `run` will prompt to overwrite — delete old files first.
  - `--agents N` flag on `init` controls how many blank agent placeholder files are created.

### Model Benchmarking (promptfoo)

We use [promptfoo](https://www.promptfoo.dev/) for evaluating AI model quality across pipeline tasks. Benchmark workspace lives in a separate git worktree (`cine-forge-sidequests`), currently on the existing user-managed branch `sidequests/model-benchmarking`. New agent-created branches elsewhere should use `codex/*`.

Runbook: `docs/runbooks/promptfoo.md`

#### Prerequisites
- **Node.js 24 LTS** (v24.13.1+). Promptfoo requires Node 22+. Installed via nvm.
- **promptfoo** installed globally: `npm install -g promptfoo` (v0.120.24+).
- Shell sessions need nvm loaded: `source ~/.nvm/nvm.sh && nvm use 24`.
- API keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and `GEMINI_API_KEY` must be set in environment.
- If you want a freshness delay for the global `promptfoo` install, configure it at the user level (`~/.npmrc`). npm added `min-release-age` in `11.10.0`; a repo-local file cannot reliably enforce it for global installs.

#### Workspace Structure
```
benchmarks/
├── tasks/           # promptfoo YAML configs (one per eval task)
├── prompts/         # Prompt templates with {{variable}} placeholders
├── golden/          # Hand-crafted reference data for scoring
├── input/           # Test input files (screenplays, scene excerpts)
├── scorers/         # Python scoring scripts
├── results/         # JSON output from eval runs
└── scripts/         # Analysis helpers
```

#### Running Benchmarks
```bash
# From the benchmarks/ directory in the sidequests worktree:
source ~/.nvm/nvm.sh && nvm use 24 > /dev/null 2>&1

# Run a benchmark (no cache for reproducibility)
promptfoo eval -c tasks/character-extraction.yaml --no-cache -j 3

# Save results to file
promptfoo eval -c tasks/character-extraction.yaml --no-cache --output results/run-name.json

# View results in web UI
promptfoo view

# Override the judge/grader model
promptfoo eval -c tasks/character-extraction.yaml --grader anthropic:messages:claude-opus-4-6
```

#### Judge / Grader Model

**Default**: promptfoo uses `gpt-5` (OpenAI) for `llm-rubric` assertions when `OPENAI_API_KEY` is set.

**Our standard**: Use **`claude-opus-4-6`** as the judge for all evals. Rationale:
- The judge must be at least as capable as the models being tested (we test GPT-5.2, Opus 4.6, and Gemini 2.5 Pro).
- Cross-provider judging reduces same-provider bias (Claude judging OpenAI/Google outputs and vice versa).
- Opus 4.6 has the strongest reasoning capabilities available.

**Provider prefixes**: `openai:`, `anthropic:messages:`, `google:` (uses `GEMINI_API_KEY`). Always evaluate models from all three providers.

Override per-eval in the YAML config:
```yaml
defaultTest:
  options:
    provider: anthropic:messages:claude-opus-4-6
```

Or per-assertion:
```yaml
assert:
  - type: llm-rubric
    value: "Evaluate the output..."
    provider: anthropic:messages:claude-opus-4-6
```

Or via CLI: `--grader anthropic:messages:claude-opus-4-6`

#### Python Scorer Interface

Promptfoo calls `get_assert(output, context)` from Python scorer files:

```python
def get_assert(output: str, context: dict) -> dict:
    """
    Args:
        output: Raw model response text
        context: Dict with 'vars' (test variables), 'prompt', etc.
    Returns:
        {"pass": bool, "score": float 0-1, "reason": str}
    """
```

- Access test variables via `context["vars"]["variable_name"]`
- `file://` in vars loads file *content*, not paths — use plain strings for paths the scorer will resolve itself.

#### Dual Evaluation Pattern

Every eval should use both:
1. **Python scorer** — Deterministic, structural quality (JSON validity, field completeness, trait/relationship matching against golden reference). Fast, reproducible, catches structural failures.
2. **LLM rubric** — Semantic quality (coherence, insight depth, evidence grounding). Catches qualitative issues the structural scorer misses. More expensive, slightly non-deterministic.

A test case passes only if *both* assertions pass. This is intentional — Mini scored 0.915 on a Python scorer but 0.62 on the LLM judge for the same output, meaning the judge caught shallow reasoning the structural check missed.

#### Expected-Fail Semantics

Compromise and detection evals are capability detectors, not runtime-default gates.

- They can stay red for long periods and still be healthy.
- Treat them as process-green only when the harness ran correctly, significant mismatches were classified, and runtime impact was recorded as `runtime-blocking` or `non-runtime-blocking`.
- Only `runtime-blocking` outcomes, or a story whose explicit goal is to remove that compromise, should block story completion.

#### Pitfalls and Gotchas

- **`max_tokens` is NOT set by default for OpenAI models.** Always set `max_tokens` in provider config or outputs will truncate silently (producing invalid JSON). Anthropic requires it; OpenAI doesn't enforce it but needs it for long outputs.
- **Gemini thinking models can silently exhaust low output caps.** For Gemini 3.x and similar thinking-capable models, a low `max_tokens` / `maxOutputTokens` budget can be consumed by hidden reasoning before the visible JSON finishes. On strict-JSON evals, inspect `usageMetadata.totalTokenCount - promptTokenCount`, not just visible completion tokens, and use a generous output cap.
- **`---` in prompt files is a prompt separator.** Promptfoo treats `---` as a delimiter between multiple prompts. Use `==========` or another delimiter if you need a visual separator in your prompt text.
- **`file://` paths resolve relative to the config file**, not CWD. A config at `tasks/foo.yaml` referencing `file://../prompts/bar.txt` resolves to `prompts/bar.txt` from the `benchmarks/` root.
- **`file://` in test vars loads content, not path.** If a scorer needs a file *path* (to load itself), use a plain string without `file://` prefix.
- **Anthropic models wrap output in ```json blocks.** Scorers must handle this (strip markdown fences before JSON.parse). The scorer should still work but may penalize slightly (0.9 vs 1.0 for JSON validity).
- **Exit code 100 = test failures**, not system errors. This is normal when models fail assertions.
- **`--dry-run` doesn't exist.** Use `--filter-first-n 1` to validate config with a single test case.
- **Concurrency**: Use `-j N` to control parallelism. `-j 3` is a good default (avoids rate limits while keeping runs under 10 min).

#### Adding a New Eval (for future modules)

When a new AI-powered module lands:
1. Copy test input to `benchmarks/input/`
2. Create golden reference in `benchmarks/golden/` (hand-crafted, expert-validated)
3. Write prompt template in `benchmarks/prompts/` (use `{{var}}` placeholders)
4. Write Python scorer in `benchmarks/scorers/` (implement `get_assert(output, context)`)
5. Create promptfoo config in `benchmarks/tasks/` (providers × test cases × assertions)
6. Run eval, analyze, pick models, update defaults in `src/cine_forge/schemas/models.py`

#### Eval Registry

All eval scores, targets, and improvement attempts are tracked in **`docs/evals/registry.yaml`** — the single source of truth. Do not hardcode eval scores in this file.

- **View current scores**: Read `docs/evals/registry.yaml`
- **Check compromise gates**: `.venv/bin/python scripts/check-compromises.py`
- **Discover available models**: `.venv/bin/python scripts/discover-models.py --summary`
- **Triage what to work on next**: `/triage` for cross-system prioritization, `/triage-evals` for eval-only triage
- **Improve an eval**: `/improve-eval`
- **Re-run for a new model**: Add provider block to `benchmarks/tasks/*.yaml` → `promptfoo eval -c tasks/<name>.yaml --no-cache --filter-providers "ModelName" -j 3` → update `docs/evals/registry.yaml` with new scores

All evals use dual scoring (Python structural scorer + LLM rubric), judge = Opus 4.6. Benchmark configs live in `benchmarks/tasks/`.

#### Value-Optimized Module Defaults

Every module default is backed by eval evidence. Selections use **value analysis** (quality per dollar), not just peak quality. Scored in Story 107 (2026-03-02). Full data in `docs/evals/registry.yaml`.

| Module | Param | Default | Quality | Cost/call | Rationale |
|--------|-------|---------|---------|-----------|-----------|
| `character_bible_v1` | `model` | `claude-sonnet-4-6` | 0.952 | $0.054 | Quality leader; cheaper tiers fall below 5% quality floor |
| `location_bible_v1` | `model` | `claude-sonnet-4-6` | 0.922 | $0.025 | Strong mid-tier, much cheaper than Opus (old default) |
| `prop_bible_v1` | `model` | `claude-sonnet-4-6` | 0.916 | $0.022 | Quality leader on structured prop extraction |
| `entity_graph_v1` | `model` | `gemini-2.5-flash` | 0.995 | $0.002 | Tied top quality at 31x cheaper than Sonnet 4.6 |
| `project_config_v1` | `model` | `gemini-3-flash-preview` | 0.953 | $0.001 | Triple winner: quality + cost + latency (13s) |
| `project_config_v1` | `qa_model` | `gpt-4.1-mini` | 1.000 | $0.001 | Perfect QA score, cheapest model |
| `script_normalize_v1` | `model` | `claude-haiku-4-5-20251001` | 0.954 | $0.002 | 1% gap vs GPT-4.1, $0.002, 2.3s — best holistic for high-stakes norm |
| `script_normalize_v1` | `qa_model` | `gpt-4.1-mini` | 1.000 | $0.001 | Perfect QA score |
| `scene_analysis_v1` | `work_model` | `claude-sonnet-4-6` | 0.890 | $0.011 | Only model above 5% quality floor for scene enrichment |
| `scene_analysis_v1` | `qa_model` | `gpt-4.1-mini` | 1.000 | $0.001 | Perfect QA score, replaces Haiku 4.5 |
| `script_bible_v1` | `work_model` | `gemini-2.5-flash-lite` | 0.885 | $0.001 | 7.8s, value=1000; Sonnet 4.6 is *worse* (0.863, 73s, $0.066) |
| `entity_discovery_v1` | `discovery_model` | `gemini-2.5-flash-lite` | 0.905 | $0.001 | 2.0s, value=1698, 13x cheaper than Haiku 4.5 |
| `continuity_tracking_v1` | `work_model` | `claude-haiku-4-5-20251001` | 0.948 | $0.010 | Updated Story 092 — 5% gap vs Sonnet at 5x lower cost |
| `scene_breakdown_v1` | `work_model` | `claude-haiku-4-5-20251001` | — | — | Boundary validation only; no cheap model gap identified |

**Key insight from Story 107**: Gemini models dramatically outperform Claude on full-screenplay tasks (script bible, entity discovery). Claude Sonnet 4.6 was the *worst* performing model on script bible (0.863 combined, 73.5s, $0.066). Gemini 2.5 Flash Lite achieved 0.885 at $0.00089 in 7.8s. Always re-eval when adding a new full-text module — model rankings invert at large context scales.

**Creative direction modules** (`editorial_direction_v1`, `intent_mood_v1`, `look_and_feel_v1`, `sound_and_music_v1`): Evaluated as smoke tests only — structural field-presence scorer + LLM rubric. Golden-reference comparison is not feasible because persona-driven outputs (Kubrick vs Tarantino director) are intentionally different. Detection mechanism for feasibility: when Opus can score its own creative outputs 0.95+ consistently across 3 different screenplays, revisit.

### Ideas Backlog
- `docs/inbox.md` captures features, patterns, and design concepts that are good but not in scope for current work.
- When a feature is deferred during story work, move it to `docs/inbox.md` rather than losing it.
- When a conversation surfaces a good idea that's out of scope, add it to `docs/inbox.md`.

### Story Conventions

**Core story statuses:** Draft → Pending → In Progress → Blocked → Done

- **Draft**: Worth preserving, but still incomplete, underspecified, or not yet substrate-verified enough to claim build-readiness. `/build-story` may keep it `Draft` if those gaps are still real, or promote it if the story is already detailed enough and the substrate check passes.
- **Pending**: Fully detailed and honestly buildable now.
- **In Progress**: Actively being worked on.
- **Blocked**: Concrete enough to preserve, but cannot honestly proceed now because of a named blocker with explicit evidence and an unblock condition. Blocked-story truth belongs in the story artifact, not only in chat history.
- **Done**: Built, validated, formally closed, and reflected in generated planning surfaces.

`Deferred` and `Cancelled` remain valid parking/archive states, but they are outside the normal build progression above.

Use `Draft` liberally for future stories, but do not leave honestly buildable work in `Draft`, and do not treat story-shell existence as priority by itself.

Blocked lines with unmet unblock conditions are **health flags**, not default next actions. Triage may surface them to preserve truth, but it must not recommend reopening them because of continuity, recent commits, or lack of other options unless the unblock condition is now materially satisfied or the user explicitly asks how to unblock them.

Eval `retry_when` conditions are also detectors, not evergreen invitations. If the same retry trigger has already been checked and nothing materially changed, treat that eval follow-on as exhausted until a genuinely new trigger appears.

### Story Execution Protocol

- `/build-story` owns implementation only. It MUST stop at the implementation handoff, leave the story `In Progress`, summarize the work, and recommend `/validate` as the next step.
- `/build-story` may promote a buildable `Draft` to `Pending` before implementation starts, and it may mark the story `Blocked` if exploration or implementation proves a real named blocker with evidence.
- `/validate` owns validation only. It MUST report findings, update the validation gate, and recommend `/mark-story-done` if the story is clean. If the story is not clean, it MUST recommend a single disposition: `Rescope then close`, `Keep open`, or `Mark blocked`. Prefer `Keep open` for remaining work that is still in the same subsystem, validation boundary, and success surface. Use `Rescope then close` only when the remaining work is genuinely separate.
- `/mark-story-done` is the only skill that may mark a story `Done` or update the story index to `Done`. If the story is incomplete, it MUST still recommend a single disposition (`Rescope then close`, `Keep open`, or `Mark blocked`) instead of stopping at a blocker list, and it should keep same-surface work in the current story by default.
- `/check-in-diff` happens after story closure to review the diff and prepare commit/push.
- `/finish-and-push` is the bundled close-out path when the user explicitly wants story closure plus validated check-in/landing in one request. It MUST run `/mark-story-done` before `/check-in-diff` and may only fix minor close-out issues inline.
- Commit and push happen only when the user explicitly requests them.
- Each step should end with a concise summary and a recommended next step the user can approve with a simple "yes".
- When there is a concrete verification path, include a short `Where to verify` note so the user can spot-check the result themselves without reverse-engineering the change.
- If the user already authorized later steps in the chain, continue without redundant confirmation unless a meaningful blocker or risk appears.

### Runbook Conventions

Runbooks live in `docs/runbooks/`. Create a runbook when a process has 3+ steps, will be repeated across sessions, and has gotchas that cost time if undocumented.

**Structure:**
1. **Context** — When and why to use this runbook
2. **Prerequisites** — What must be true before starting
3. **Steps** — Each tagged `[script]` (deterministic, run a command) or `[judgment]` (requires agent reasoning)
4. **Boundaries** — Always do / Ask first / Never do
5. **Troubleshooting** — Common failures and fixes
6. **Lessons learned** — Append-only, dated

**Skill↔runbook rule:** Every runbook should have a corresponding skill. Every skill with 3+ procedural steps should have a runbook. Apply this going forward — don't retroactively create runbooks for existing skills.

Current runbooks:
- `align.md` — Methodology-graph drift check across Ideal/spec/build map/stories/evals (skill: `/align`)
- `check-in-worktree-landing.md` — Safe check-in and landing flow for task branches and worktrees (skill: `/check-in-diff`)
- `codebase-improvement-scout.md` — Repo hygiene scan and cleanup triage flow (skill: `/codebase-improvement-scout`)
- `create-eval.md` — Scaffold a new eval in the registry and benchmark workspace (skill: `/create-eval`)
- `finish-and-push.md` — Bundled story closure plus validated landing flow (skill: `/finish-and-push`)
- `golden-build.md` — Building hand-curated golden references and auditing eval mismatches (canonical bootstrap: `/setup-methodology`; day-to-day: `/golden-create`, `/golden-verify`)
- `promptfoo.md` — Run, inspect, and record promptfoo benchmark passes in the sidequest eval workspace
- `setup-methodology.md` — Install or refresh the methodology package and canonical setup surface (skill: `/setup-methodology`)
- `triage.md` — Cross-system routing to the highest-value next action (skill: `/triage`)
- `triage-evals.md` — Cheap diagnosis of which eval, compromise gate, or stale benchmark needs attention next (skill: `/triage-evals`)

### UI Development Workflow

When building or substantially redesigning a UI, follow this process:

#### 1. Project Setup (mechanical)
- Scaffold with `npm create vite@latest` (React + TypeScript template).
- Install the standard stack: `shadcn/ui`, `tailwindcss`, `@tailwindcss/vite`, `zustand`, `@tanstack/react-query`, `react-router-dom`, `lucide-react`, `class-variance-authority`, `clsx`, `tailwind-merge`.
- Run `npx shadcn@latest init -d` to initialize shadcn/ui with default dark theme and CSS variables.
- Add base components: `npx shadcn@latest add button card badge input separator tooltip`.
- Set up path alias (`@/` → `./src/*`) in both `tsconfig.json` and `tsconfig.app.json`.
- Configure Vite with Tailwind plugin, path aliases, and a unique dev port to avoid conflicts.
- Port or create the API client and TypeScript types for backend communication.
- Set up routing with the resource-oriented URL structure (identity in path, not search params).

#### 2. Visual Identity Bootstrap (design-in-browser)
- **Do NOT write design docs on paper first.** Build a `/theme` dev-only route that showcases the design system live in the browser.
- Generate 3–4 theme variations as CSS variable configs. Each theme is a set of `oklch()` color values for the shadcn/ui CSS variables (`--background`, `--foreground`, `--primary`, `--card`, `--muted`, `--border`, etc.).
- The showcase page should render: typography scale, color swatches, buttons (all variants), cards, badges (status states), input fields, a sample layout skeleton with the planned panel arrangement.
- Add a theme switcher at the top so the user can toggle between variations instantly.
- **Checkpoint with user**: They pick a direction. Iterate if needed. Once chosen, lock in design tokens.

#### 3. Build Loop (screenshot-verified)
- Build one component or page at a time.
- Before changing a state-specific screen, confirm that the view is actually wired into the active route tree. This repo still contains alternate components that are not the live path (for example, `AnalyzedView` in `ui/src/pages/ProjectHome.tsx`), so code in the wrong branch can look finished while users never see it.
- After each significant change: take a screenshot via Chrome MCP → inspect the result → fix issues → screenshot again.
- **Never generate large amounts of UI code without visual verification.** This is the #1 anti-pattern — blind CSS/HTML generation produces garbage.
- **After wiring pages to real API data**, reload the app with the backend running and click through every modified page. Check `read_console_messages` for runtime errors. `npm run build` passing does NOT mean the UI works — runtime data mismatches (e.g., backend sends `'done'` but switch handles `'completed'`) only crash in the browser.
- Use the Chrome MCP tools: `screenshot` to see results, `read_page` to inspect DOM, `read_console_messages` to catch errors, `find` to locate elements.
- If browser MCP tooling is unavailable or failing, follow `docs/runbooks/browser-automation-and-mcp.md`.

#### 4. Checkpoints
- After the app shell is built (layout, navigation, routing), checkpoint with the user.
- After core pages are wired up and the golden path works end-to-end, checkpoint with the user.
- Users react better to real running UI than to descriptions or wireframes.

#### Key Principles
- **Design tokens are the source of truth** for visual consistency. All colors, spacing, and typography come from CSS variables defined once and referenced everywhere via Tailwind.
- **shadcn/ui components are copied into the codebase** (not imported from a package). This means they can be customized freely.
- **Resource-oriented URLs**: Project/Run/Artifact identity belongs in the URL path, not search params or localStorage. Makes the UI stateless, shareable, and multi-tab friendly.
- **v0.dev for exploration**: When unsure what a component should look like, generate variations in v0, copy the code into the codebase, and adapt to real data. Code transfers directly since v0 uses the same React + shadcn/ui + Tailwind stack.

#### 5. Mandatory Reuse Directives

Before writing **any** new UI code, you MUST follow this checklist:

1. **Read the UI Component Registry below** — check if a shared component or utility already handles your use case.
2. **Grep `ui/src/components/` and `ui/src/lib/`** for existing patterns before creating new abstractions.
3. **If a similar component exists, extend it** — do NOT create a parallel one.

| Rule | Detail |
|------|--------|
| **MUST** use `ui/src/lib/format.ts` | Never define `timeAgo` or `formatDuration` inline |
| **MUST** use `ui/src/lib/artifact-meta.ts` | Never duplicate `artifactMeta` config |
| **MUST** use `ui/src/components/HealthBadge.tsx` | Never inline health badge rendering |
| **MUST** use `ui/src/components/StatusBadge.tsx` | Never inline status badge/icon rendering |
| **MUST** use `ui/src/components/PageHeader.tsx` | Never duplicate page headers across state branches |
| **MUST** use `EntityListPage` pattern | For any new entity list views, extend the config map |
| **MUST** use `ui/src/lib/use-long-running-action.ts` | Never manually orchestrate chat messages + button state for long-running operations |
| **MUST** use `ui/src/components/OperationBanner.tsx` | Never build inline status banners for operations — the global banner handles all operations |
| **MUST NOT** define utility functions inline in page files | Extract to `ui/src/lib/` |
| **MUST NOT** copy-paste JSX blocks across pages | Extract a shared component instead |
| **MUST NOT** manually create `ai_status` messages for long-running operations | Use `useLongRunningAction` — it handles chat, banner, and button state automatically |

Run `pnpm --dir ui run lint:duplication` after UI changes to catch regressions. Threshold: 5%.

#### UI Component Registry

Shared components and utilities — the **single source of truth** for each concern. Check here before building anything new.

| Component / Utility | Path | Purpose |
|---|---|---|
| `timeAgo()`, `formatDuration()` | `ui/src/lib/format.ts` | Time display helpers (ms input for timeAgo, seconds input for formatDuration) |
| `artifactMeta`, `getArtifactMeta()` | `ui/src/lib/artifact-meta.ts` | Artifact type display metadata (icon, label, color) |
| `HealthBadge` | `ui/src/components/HealthBadge.tsx` | Artifact health status badge (valid/stale/needs_review) |
| `StatusBadge`, `StatusIcon`, `getStatusConfig` | `ui/src/components/StatusBadge.tsx` | Pipeline run/stage status rendering |
| `PageHeader` | `ui/src/components/PageHeader.tsx` | Page title + subtitle (render once, above state branching) |
| `EntityListPage` | `ui/src/pages/EntityListPage.tsx` | Parameterized entity list (characters/locations/props/scenes) |
| `EntityDetailPage` | `ui/src/pages/EntityDetailPage.tsx` | Parameterized entity detail view |
| `EntityListControls` | `ui/src/components/EntityListControls.tsx` | Sort/density/direction controls |
| `EmptyState`, `ErrorState`, `ListSkeleton` | `ui/src/components/StateViews.tsx` | Shared loading/error/empty states |
| `ExportModal` | `ui/src/components/ExportModal.tsx` | Export dialog |
| `DirectionAnnotation` | `ui/src/components/DirectionAnnotation.tsx` | Word/Docs-style comment for creative direction (parameterized by DirectionType) |
| `DirectionTab`, `RolePresenceIndicators` | `ui/src/components/DirectionTab.tsx` | Scene direction tab content + role avatar badges |
| `TaskProgressCard` | `ui/src/components/TaskProgressCard.tsx` | Compact multi-item progress card for chat (propagation, exports, etc.) |
| `RunProgressCard` | `ui/src/components/RunProgressCard.tsx` | Pipeline run stage progress card for chat |
| `OperationBanner` | `ui/src/components/OperationBanner.tsx` | Global status banner for all active operations (pipeline runs + direct API calls). Rendered in AppShell. |
| `useLongRunningAction` | `ui/src/lib/use-long-running-action.ts` | Hook for long-running direct API calls — manages button state, operation store, and chat messages automatically |
| `useOperationStore` | `ui/src/lib/operation-store.ts` | Zustand store tracking active operations per project (used by OperationBanner and useLongRunningAction) |

#### 6. User Feedback Contract for Long-Running Operations

Every operation that takes more than ~1 second MUST provide three forms of feedback:

1. **Button disabled + spinner** while the operation runs
2. **Status banner** at top of page (global `OperationBanner` in AppShell handles this automatically)
3. **Chat timeline entries** showing what's happening and what completed (permanent record)

**How to implement**: Use `useLongRunningAction` from `ui/src/lib/use-long-running-action.ts`. It handles all three automatically.

```typescript
import { useLongRunningAction } from '@/lib/use-long-running-action'

// Multi-item operation (e.g., propagation across concern groups)
const { isRunning, start } = useLongRunningAction({
  projectId,
  label: 'Propagating creative intent',
  items: groups.map(g => ({ label: g.label })),  // optional: for multi-item progress
  action: () => api.propagate(projectId, payload),
  onSuccess: (result, meta) => {
    // meta.chatMessageId lets you customize the chat message
    queryClient.invalidateQueries({ queryKey: ['directions'] })
  },
})

// In JSX:
<Button onClick={start} disabled={isRunning}>
  {isRunning ? 'Propagating...' : 'Save & Propagate'}
</Button>
```

The hook automatically:
- Registers the operation in the global store (drives `OperationBanner`)
- Creates a `task_progress` chat message (multi-item) or `ai_status` message (single-item)
- Updates chat messages to done/failed on completion
- Auto-removes the operation from the store after a brief "done" flash

**For pipeline runs**: These are handled by `useRunProgressChat` + `setActiveRun()` (not the hook). The `OperationBanner` reads `activeRunId` from the chat store to display run progress.

**Implementation reference:**
| Operation | Mechanism | Code |
|---|---|---|
| Pipeline run | `setActiveRun()` → `useRunProgressChat` → `OperationBanner` | `ui/src/lib/use-run-progress.ts` |
| Propagation | `useLongRunningAction` → `OperationBanner` + chat | `ui/src/pages/IntentMoodPage.tsx` |
| Direction gen | `setActiveRun()` (triggers pipeline run tracking) | `ui/src/components/DirectionTab.tsx` |
| Export | Instant (clipboard/download) — no hook needed | `ui/src/components/ExportModal.tsx` |

**The rule**: If the user clicks a button and something takes time, they must see (a) what's happening *right now* and (b) a permanent record that it happened. No silent background work. No spinners-only. No "it just worked" without evidence. Use `useLongRunningAction` — it's simpler than rolling your own.

### Repo Map
- `src/cine_forge/driver/`: Orchestration runtime.
- `src/cine_forge/modules/`: Pipeline modules by stage.
- `src/cine_forge/schemas/`: Pydantic artifact schemas.
- `src/cine_forge/artifacts/`: Storage, versioning, and dependency graph.
- `src/cine_forge/pipeline/`: Pipeline capability graph (static definition + dynamic status).
- `src/cine_forge/api/`: Backend API for the UI.
- `ui/`: Production React frontend (shadcn/ui + React 19 + Zustand).
- `docs/evals/`: Eval registry, attempt stories, and improvement tracking. See `docs/evals/README.md`.
- `scripts/discover-models.py`: Query provider APIs for available models (used by `/improve-eval`).
- `scripts/check-compromises.py`: Check compromise eval gates against registry data (C2–C7).

### Golden References (Test Fixtures)

Hand-curated ground truth for regression testing. These are the source of truth — if the code disagrees with the golden file, the code is wrong.

| File | Purpose | Source Script |
|---|---|---|
| `tests/fixtures/golden/the_mariner_scene_entities.json` | Per-scene character + prop extraction from action lines | The Mariner |
| `benchmarks/golden/the-mariner-characters.json` | Character bible extraction (promptfoo eval) | The Mariner |
| `benchmarks/golden/the-mariner-locations.json` | Location bible extraction (promptfoo eval) | The Mariner |
| `benchmarks/golden/the-mariner-props.json` | Prop bible extraction (promptfoo eval) | The Mariner |
| `benchmarks/golden/the-mariner-relationships.json` | Relationship discovery (promptfoo eval) | The Mariner |
| `benchmarks/golden/the-mariner-scenes.json` | Scene boundaries & headings (promptfoo eval) | The Mariner |
| `benchmarks/golden/the-mariner-config.json` | Project config detection (promptfoo eval) | The Mariner |
| `benchmarks/golden/continuity-extraction-golden.json` | Entity state tracking between scenes (promptfoo eval) | The Mariner |
| `benchmarks/golden/enrich-scenes-golden.json` | Scene-level metadata enrichment (promptfoo eval) | The Mariner |
| `benchmarks/golden/normalize-signal-golden.json` | Prose/broken Fountain normalization (promptfoo eval) | The Mariner |
| `benchmarks/golden/qa-pass-golden.json` | QA gate calibration — accept good, reject bad (promptfoo eval) | The Mariner |
| `benchmarks/golden/the-mariner-script-bible.json` | Script bible extraction — required fields, themes, title, act structure (promptfoo eval) | The Mariner |
| `benchmarks/golden/the-mariner-entity-discovery.json` | Entity discovery — recall-focused: required chars/locs/props with aliases (promptfoo eval) | The Mariner |

When adding a new screenplay for testing, create a corresponding golden reference following the same structure. Validate golden files by having a human read the screenplay and cross-check every entry. See `docs/runbooks/golden-build.md` for the full build methodology, common failure patterns, and audit process.

### Worktree Strategy

The user runs multiple agent sessions in parallel. To prevent git conflicts between sessions, we use **git worktrees** — each session works in its own directory on its own branch.

**Preferred model:** one task = one branch = one worktree = one agent.

`main` is the stable integration branch. Feature or story work should normally happen on a task branch in its own worktree. Working directly on `main` is allowed as an exception when the user chooses it, but it is not the preferred development path.

#### Orientation: Which Worktree Am I In?

When starting a session, run `git worktree list` to understand the layout. Common setup:

| Directory | Branch | Purpose |
|---|---|---|
| `cine-forge/` | `main` | Production code — pipeline, modules, UI, backend |
| `cine-forge-sidequests/` | `codex/<topic>` or existing user-managed sidequest branch | Research, tooling, docs-only stories, benchmark experiments |

**If you are in `cine-forge/`** — you may be on `main` or another branch. Check `git branch --show-current` before assuming. If you are on `main`, treat it as the stable integration branch unless the user explicitly chose to work there.

**If you are in `cine-forge-sidequests/`** (or similar) — you are on a feature or sidequest branch. This may be a new `codex/*` branch or an older user-managed sidequest branch. Stay within that worktree's scope. When done, use `/check-in-diff` if the user explicitly requests check-in.

#### Rules

1. **Never do ordinary work across worktrees.** Each session stays in its own directory and does not edit project files in sibling worktrees. Narrow exception: `/check-in-diff` may run git-only landing commands in the existing `main` worktree when that is the only safe way to fast-forward `main`.
2. **Preferred structure**: create a task branch per workstream and keep one agent in that worktree at a time.
3. **Agent-created branches**: when the agent creates a new branch itself, use the `codex/` prefix. Existing user branches do not need to be renamed.
4. **Check-in flow**: `/check-in-diff` owns commit/push/integrate/land when the user explicitly requests check-in. The preferred landing path is task branch → sync with latest `origin/main` → validate → fast-forward `main`.
5. **Main fallback**: if the user chose to work on `main`, do not panic. But do not push `main` before validation, and do not resolve integration conflicts directly on `main`; use a temporary integration branch if sync with `origin/main` is required.
6. **Landing exception only**: if another worktree already has `main` checked out, `/check-in-diff` may use git commands there for the final fast-forward landing step only. Do not do implementation edits or conflict resolution in that sibling worktree.
7. **Shared files**: AGENTS.md, CLAUDE.md, and other root config files are tracked by git and shared across worktrees at their respective commit points. Avoid conflicting edits to these files across sessions — coordinate with the user.

#### Creating a New Worktree

When the user wants to start a new parallel workstream:

```bash
# From the main repo
git worktree add ../cine-forge-sidequests -b codex/<topic-name>
```

When a side quest is done and merged:

```bash
# Clean up
git worktree remove ../cine-forge-sidequests
git branch -d codex/<topic-name>
```

## Production Deployment

CineForge is deployed on **Fly.io** at **https://cineforge.copper-dog.com** (single Docker container, Cloudflare DNS).

- **To deploy**: Use the `/deploy` skill
- **Full reference** (architecture, DNS, troubleshooting, setup): `docs/deployment.md`
- **Browser automation + MCP troubleshooting runbook**: `docs/runbooks/browser-automation-and-mcp.md`
- **Quick commands**: `fly deploy --depot=false --yes` | `fly status -a cineforge-app` | `fly logs -a cineforge-app`

## Agent Memory: AI Self-Improvement Log

Treat this section as a living memory. Entry format: `YYYY-MM-DD — short title`: summary plus explanation including file paths.

### Effective Patterns
- 2026-02-19 — Canonical skills root with thin adapters: Keep `.agents/skills` as the only source of truth, then wire `.claude/skills` and `.cursor/skills` as symlinks and generate `.gemini/commands/*.toml` wrappers from canonical `SKILL.md` files via `scripts/sync-agent-skills.sh`. This removes prompt duplication and keeps cross-CLI behavior aligned with one edit surface.
- 2026-02-15 — Design-in-browser with theme showcase: Instead of writing design docs, build a `/theme` route with live-switchable CSS variable themes. Showcase real shadcn/ui components (buttons, cards, badges, inputs, layout skeleton) so the user reacts to actual rendered UI, not descriptions. This produces better feedback, faster decisions, and a working design token system as a side effect. See `AGENTS.md > UI Development Workflow` for the full process (`ui/src/pages/ThemeShowcase.tsx`).
- 2026-02-11 — Story-first implementation: Implement stories in dependency order and validate each with focused smoke checks.
- 2026-02-12 — FDX-first screenplay intake: detect Final Draft XML early and normalize to Fountain before AI routing.
- 2026-02-12 — Multi-output module validation: Resolve schema per artifact by explicit `schema_name` to avoid false failures.
- 2026-02-13 — Reflow tokenized PDF text: Reconstruct boundaries before classification to keep heuristics stable.
- 2026-02-13 — Cast-quality filters: Remove pronouns and derivative noise before ranking characters.
- 2026-02-14 — Cross-recipe artifact reuse via `store_inputs`: Downstream recipes declare `store_inputs: {input_key: artifact_type}` to resolve inputs from the artifact store instead of re-executing upstream stages. Validated against registered schemas, rejects stale/unhealthy artifacts, and included in stage fingerprints for cache correctness (`src/cine_forge/driver/recipe.py`, `src/cine_forge/driver/engine.py`, `configs/recipes/recipe-world-building.yaml`).

- 2026-02-22 — Config-driven parameterized pages with mandatory reuse directives: Replacing 4 near-identical list pages with a single `EntityListPage` parameterized by config map eliminated ~650 duplicated lines. Prevention requires explicit file-path directives in AGENTS.md (agents don't know where abstractions live unless told) plus `jscpd` automated detection. See `AGENTS.md > UI Development Workflow > Mandatory Reuse Directives`.
- 2026-02-15 — Dual evaluation catches what code can't: Python scorers measure structural quality (JSON validity, field coverage, trait matching) but miss semantic issues. LLM rubric judges catch shallow reasoning, over-segmentation, and missed subtext. Always use both. Example: GPT-4.1 Mini scored 0.915 on Python scorer but 0.62 on LLM judge for the same character extraction — the judge caught that it found all the right fields but missed the character's emotional arc entirely.
- 2026-02-15 — Cross-provider judging reduces bias: When evaluating model outputs, use a judge from a different provider than the model being tested. Claude Opus 4.6 as default judge works well for evaluating both OpenAI and Anthropic models.

### Known Pitfalls
- 2026-02-11 — Hidden schema drift: adding output fields without schema updates can silently drop data.
- 2026-02-12 — Runtime-only inputs bypass cache: Include CLI params in stage fingerprints or reuse returns stale data.
- 2026-02-12 — CORS/Vite Port shifts: Allow localhost across local ports by regex to prevent "Failed to fetch".
- 2026-02-13 — Schema-valid placeholder outputs: Structurally valid but useless data must fail semantic quality gates.
- 2026-02-13 — Stale processes: Long-running API servers must be restarted after Pydantic schema changes.
- 2026-02-13 — Directory depth fragility: Discovery logic assuming fixed depth (e.g. `artifacts/{type}/{id}/`) fails on nested/folder-based types.
- 2026-02-13 — Project Directory Pollution: Reusing the same project directory for manual testing and user runs can lead to "ghost" artifacts appearing if cache reuse is not explicitly invalidated after recipe or input changes.
- 2026-02-13 — Deceptive "Zero-Second" Success: Mock models finish in microseconds, making a run appear to "pass" instantly while producing only stubs. Always verify `cost_usd` or `runtime_params` before declaring a high-fidelity success.
- 2026-02-15 — promptfoo `max_tokens` trap: OpenAI providers don't require `max_tokens` but will silently truncate long outputs (producing invalid JSON that fails every scorer). Always set `max_tokens: 4096` or `8192` for all providers.
- 2026-02-16 — Gemini extended thinking eats output tokens: Gemini 2.5 Flash/Pro use chain-of-thought "thinking" tokens that count against `maxOutputTokens`. With 4096 limit, thinking consumes 3000+ tokens, leaving insufficient space for the actual JSON output. Set `maxOutputTokens: 16384` for all Gemini providers in promptfoo configs.
- 2026-02-16 — Gemini model IDs have no preview dates: Use `gemini-2.5-flash-lite`, `gemini-2.5-flash`, `gemini-2.5-pro`, `gemini-3-flash-preview`, `gemini-3-pro-preview`. The dated preview suffixes (e.g., `-preview-06-17`) return 404.
- 2026-02-21 — slow `npx` execution: `npx afterwriting` may take up to 60-90s on first execution as it fetches the package. Set conservative timeouts in `subprocess.run` to avoid premature failures.
- 2026-02-15 — promptfoo `---` separator trap: Three dashes in prompt files are interpreted as a prompt separator, splitting one prompt into two. The second fragment may lack required instructions (e.g., missing "return JSON"), causing confusing failures. Use `==========` or similar instead.
- 2026-02-19 — `tsc --noEmit` ≠ `tsc -b`: The root `tsconfig.json` has `"files": []` with no linting rules. `tsc --noEmit` doesn't follow `references`, so it skips strict checks like `noUnusedLocals` from `tsconfig.app.json`. `tsc -b` follows references and matches what `npm run build` does in production. **Always use `tsc -b` for validation, never `tsc --noEmit`.**
- 2026-02-22 — AI agents duplicate UI code silently: When building similar pages, agents copy-paste rather than abstracting. Every new page or component must check the UI Component Registry in `AGENTS.md > UI Development Workflow` first. Run `pnpm --dir ui run lint:duplication` to catch regressions. See Story 066 for the full audit.
- 2026-02-15 — Build Pass ≠ Working UI: `tsc --noEmit` and `npm run build` only prove static types and bundling. They cannot catch runtime crashes from data mismatches (e.g., backend sends `'done'` but UI switch only handles `'completed'` — both are `string`, so TypeScript is silent). **After any UI change that touches data flow, open the app in a browser with the real backend and click through every affected page before declaring done.** A green build is necessary but not sufficient.
- 2026-02-28 — Stale model selection: Never pick models from training data — query `/v1/models` or provider docs and check current pricing before model decisions. Cost differences can be 10-20x. Model lineups change rapidly; a model that was expensive last month may have been superseded by a cheaper alternative.
- 2026-02-28 — Silent long-running operations: Any button that triggers work taking >1s MUST provide both a status banner on-page and per-item chat timeline entries (spinners → checkmarks). Users cannot tell if something is working, stuck, or failed without this feedback. See `AGENTS.md > UI Development Workflow > User Feedback Contract` for the mandatory pattern. This applies to ALL async operations — pipeline runs, propagation, AI calls, exports, etc.
- 2026-03-01 — LLM resolution degrades from synthetic to real data: Small-scale synthetic test fixtures (10-20 entities) can produce excellent scores (P=1.00, R=0.91) while the same approach struggles on real-world data (40-80+ entities). A passing eval on a small fixture does not guarantee production readiness. Always test against realistic-scale inputs before declaring a capability works.
- 2026-03-14 — Dead UI branches can hide regressions: before calling a UI story complete, verify the changed view is part of the active route switch and not just a dormant alternate component. Story 031 initially updated `AnalyzedView` while `ProjectHome` still rendered `FreshImportView` for every non-empty state, which would have left the new attention UX invisible.

### Lessons Learned
- 2026-02-12 — Build the pipeline spine before AI modules: Land immutable store and graph first.
- 2026-02-13 — Patch shared dependencies in integration tests: Monkeypatching `pypdf` is more reliable than module-local helpers.
- 2026-02-13 — Validate the Service Layer: Passing a module test does not guarantee the UI can see or run it. Test through the `OperatorConsoleService` boundary.
- 2026-02-13 — Prefer Dynamic Discovery: UI services should scan folders for recipes/actions rather than hardcoding paths.
- 2026-02-13 — Ensure Cache Invalidation across Recipe Changes: When moving from a partial recipe (MVP) to a broader one (World Building) in the same project folder, verify that upstream artifacts are either explicitly forced to rerun or are strictly compatible with the new pipeline's expectations.
- 2026-02-14 — Establish LLM Resilience: LLM calls for long documents are prone to truncation and malformed JSON. Implement catch-and-retry logic that increments `max_tokens` and escalates to stronger models (e.g., Mini -> SOTA) on failure (`src/cine_forge/ai/llm.py`).
- 2026-02-14 — 3-Recipe Architecture: Partition the pipeline into Intake, Synthesis, and Analysis. This limits the "blast radius" of AI failures and provides natural human-in-the-loop verification gates between expensive world-building steps.
- 2026-02-14 — Resource-Oriented UI: Identity (Project, Run, Artifact) belongs in the URL Path, not Search Params or LocalStorage. This makes the UI stateless, shareable, and multi-tab friendly.
- 2026-02-19 — Role-runtime foundation first, behavior second: Land strict role schemas, hierarchy/capability gates, style-pack injection, and invocation audit logging before implementing role-specific behavior. This keeps Story 015+ focused on role intelligence instead of foundational plumbing (`src/cine_forge/schemas/role.py`, `src/cine_forge/roles/runtime.py`).
- 2026-02-20 — Canon gating as immutable artifact, not transient state: Stage readiness decisions should be persisted as first-class artifacts (`stage_review`) containing guardian sign-offs, director decision, disagreement records, and checkpoint approval state so progression logic remains auditable and replayable (`src/cine_forge/schemas/role.py`, `src/cine_forge/roles/canon.py`).
- 2026-02-20 — Built-in Style Packs in `src`: Store built-in style packs alongside role definitions in `src/cine_forge/roles/style_packs` rather than `configs/`. This treats them as first-class code artifacts that deploy with the package, while leaving `configs/` for user-overridable settings.
- 2026-02-20 — Multiline Strings in Tests: When generating test files with `write_text`, always use triple-quoted strings for content containing newlines to avoid syntax errors in the generated or generating code.
- 2026-02-20 — Suggestions as first-class immutable artifacts: Roles emit suggestions in their response payload, which are persisted as versioned artifacts. This allows for a creative backlog that persists across sessions and enables automated resurfacing during review stages (`src/cine_forge/schemas/suggestion.py`, `src/cine_forge/roles/suggestion.py`).
- 2026-02-20 — Decision tracking with lineage: Decisions are recorded as explicit artifacts that link back to the suggestions that informed them and forward to the artifacts they affect, ensuring full creative auditability.
- 2026-02-20 — Conversations as first-class artifacts: Inter-role communication is recorded as immutable `conversation` artifacts with raw transcripts, linked suggestions, and topic metadata. This provides creative-archaeological value and reasoning transparency (`src/cine_forge/schemas/conversation.py`, `src/cine_forge/roles/communication.py`).
- 2026-02-20 — Disagreement protocol with dual-position preservation: Detailed disagreements are recorded as artifacts, capturing both the original objection and the resolution (override rationale), linked to the affected artifacts and the conversation where they occurred.
- 2026-02-21 — Screenplay Fidelity: FDX round-trip requires careful handling of non-standard headings via forced headings ('.' prefix in Fountain) and strict spacing rules (no blank line between character and dialogue) to preserve structural integrity. PDF extraction fidelity is significantly improved by using `pdfplumber` with `layout=True` compared to `pypdf`, as it preserves visual columns and whitespace better.
- 2026-03-01 — Eval-first applies to implementation decisions, not just pipeline stages: Stories can pre-decide "pure code" for tasks that AI handles better. The `create-story` "AI Considerations" section asked "can AI do this?" and accepted "no" without evidence. Fix: renamed to "Approach Evaluation" — lists candidate approaches without pre-deciding, with the eval that distinguishes them. Approach selection happens during `build-story`'s eval-first gate with measured baselines.
- 2026-03-14 — Artifact writers must create parent directories for nested payload files: Once bible/artifact manifests can carry structured children like `user_assets/...`, thumbnails, or waveform JSON, any write path that assumes flat filenames will fail at runtime. Create parent folders immediately before writing versioned sidecar files (`src/cine_forge/artifacts/store.py`, `src/cine_forge/services/injected_assets.py`).

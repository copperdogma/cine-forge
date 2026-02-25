# AGENTS.md

This file is the project-wide source of truth for agent behavior and engineering principles. It serves as both a core directive and a living memory for AI agents working on this codebase.

## Core Agent Mandates

- **GREENFIELD PROJECT — NO BACKWARDS COMPATIBILITY**: This app is under active development with zero real users, zero valuable user data, and zero old processes or file formats to preserve. Do NOT waste time on backwards compatibility shims, migration paths, deprecation warnings, old format support, or "gentle" transitions. When something needs to change, **change it directly**. Delete the old code. Update all call sites. If a schema changes, change it — don't version it. If an API changes, change it — don't keep the old endpoint. The only cost is a `git revert` away.
- **No Implicit Commits**: NEVER commit or push changes unless explicitly requested by the user.
- **Security First**: NEVER stage or commit secrets, API keys, or sensitive credentials.
- **Permissioned Actions**: NEVER run `git commit`, `git push`, or modify remotes without explicit user permission.
- **Verify, Don't Assume**: NEVER assume a library is available or a file has a specific content. Use `read_file` and dependency checks (`package.json`, `pyproject.toml`) to ground your work.
- **Immutability**: Versioned artifacts are immutable. NEVER mutate an existing version in place; always produce a new version with incremented metadata.
- **AI-First Engineering**: Prefer roles, prompts, and structured artifacts over rigid hard-coded business rules. Architecture should facilitate AI reasoning.
- **Headless Operation**: All core application capabilities (e.g., export, analysis, remediation) MUST be performable via CLI scripts or direct backend calls, bypassing the UI. This ensures AI agents can autonomously operate the system.
- **Definition of Done**: A task is complete ONLY when:
  1. Relevant tests pass (`make test-unit` minimum).
  2. Artifacts are produced and manually inspected for semantic correctness.
  3. Schema validation passes.
  4. The active story's work log is updated with evidence and next actions.

## General Agent Engineering Principles

- **Semantic Quality over Structural Validity**: A JSON that passes a schema but contains "UNKNOWN" or placeholder data is a failure. Assert semantic quality predicates in tests.
- **Boundary Awareness**: Code that works in a unit test can fail in a long-running service (due to state, cache, or import-time definitions). Validate through the service layer or API boundary.
- **Process Lifecycle**: Restart long-running backend/API processes after changing schemas or core logic. Hot-reloading is a tool, but a clean restart is the source of truth.
- **Regression Fixes start with Fixtures**: When a real-world run fails, capture the failing input as a deterministic test fixture BEFORE implementing the fix.
- **Conservative Heuristics**: When building classifiers (screenplay vs. prose), use weighted evidence and confidence scores. Favor "needs_review" over silent incorrectness.
- **Lineage Tracking**: Every transformation must record its upstream sources. Data without provenance is noise.
- **Context Traceability**: Every run must persist its full execution context (e.g., `runtime_params`, recipe fingerprints) in its core artifacts (`run_state.json`). Never leave the operator guessing which model or flag produced an outcome.
- **Project-Scoped Preferences**: Store user preferences and settings in `project.json`, not `localStorage`. `localStorage` is ephemeral — it doesn't survive browser clears, doesn't sync across machines, and isn't visible to the backend. Only use `localStorage` for truly throwaway UI state (e.g., collapsed panel memory within a single session). Anything the user would miss if it vanished belongs in project settings.

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
- **Parallelize independent work**: If building 3 pages that don't depend on each other, launch 3 subagents simultaneously.
- **Opus orchestrates, delegates, reviews**: The main agent reads results, spots issues, and iterates — never blindly trusts.
- **Context protection**: Use subagents for tasks that produce large output (exploration, research) to avoid flooding the main context.
- **Fail fast**: If a subagent produces bad output, don't retry the same prompt — adjust the approach or do it yourself.

### Running Log
Track model performance observations in `/memory/subagent-log.md` to refine the table above over time.

## Operational Guide

### Common Driver Commands
- **Validate only**: `PYTHONPATH=src python -m cine_forge.driver --recipe configs/recipes/recipe-test-echo.yaml --dry-run`
- **Execute recipe**: `PYTHONPATH=src python -m cine_forge.driver --recipe configs/recipes/recipe-test-echo.yaml --run-id test-001`
- **Resume from stage**: `PYTHONPATH=src python -m cine_forge.driver --recipe configs/recipes/recipe-test-echo.yaml --start-from echo --run-id test-002`

### Test Commands
- **Unit tests**: `.venv/bin/python -m pytest -m unit` (not system pytest — version mismatch)
- **Lint**: `.venv/bin/python -m ruff check src/ tests/`

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

We use [promptfoo](https://www.promptfoo.dev/) for evaluating AI model quality across pipeline tasks. Benchmark workspace lives in a separate git worktree (`cine-forge-sidequests` on `sidequests/model-benchmarking`).

#### Prerequisites
- **Node.js 24 LTS** (v24.13.1+). Promptfoo requires Node 22+. Installed via nvm.
- **promptfoo** installed globally: `npm install -g promptfoo` (v0.120.24+).
- Shell sessions need nvm loaded: `source ~/.nvm/nvm.sh && nvm use 24`.
- API keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, and `GEMINI_API_KEY` must be set in environment.

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

#### Pitfalls and Gotchas

- **`max_tokens` is NOT set by default for OpenAI models.** Always set `max_tokens` in provider config or outputs will truncate silently (producing invalid JSON). Anthropic requires it; OpenAI doesn't enforce it but needs it for long outputs.
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

#### Eval Catalog (Feb 2026)

Quick reference for every promptfoo eval. Re-run these when new models drop.

| Eval | Config | Summary | Tests | Top Model |
|------|--------|---------|-------|-----------|
| Character Extraction | `tasks/character-extraction.yaml` | Structured character bible: traits, arc, relationships, evidence | 3 (Mariner, Rose, Dad) | **Sonnet 4.6 (0.942)** |
| Location Extraction | `tasks/location-extraction.yaml` | Structured location bible: physical detail, narrative function, scene refs | 3 (Ruddy & Greene, 15th Floor, Coastline) | Opus 4.6 (0.898) |
| Prop Extraction | `tasks/prop-extraction.yaml` | Structured prop bible: description, symbolism, plot function | 3 (Oar, Purse, Flare Gun) | Opus 4.6 (0.880) |
| Relationship Discovery | `tasks/relationship-discovery.yaml` | Narrative relationships: family, adversary, ownership edges | 1 (all entities) | 7-way tie (0.995) |
| Config Detection | `tasks/config-detection.yaml` | Auto-detect project metadata: title, genre, tone, format, duration, cast | 1 (full screenplay) | Haiku 4.5 (0.886) |
| Scene Extraction | `tasks/scene-extraction.yaml` | Scene boundaries, headings, characters, summaries | 1 (full screenplay) | **Sonnet 4.6 (0.815)** |
| Normalization | `tasks/normalization.yaml` | Prose/broken Fountain → valid Fountain screenplay | 2 (prose, broken fountain) | **Sonnet 4.6 (0.955)** |
| Scene Enrichment | `tasks/scene-enrichment.yaml` | Scene-level metadata: beats, tone, characters, location | 2 (elevator, flashback) | **Sonnet 4.6 (0.890)** |
| QA Pass | `tasks/qa-pass.yaml` | QA gate: detect good/bad extractions (seeded pairs) | 2 (good scene, bad scene) | **Sonnet 4.6 (0.998)** |

All evals: 13 providers (4 OpenAI, 4 Anthropic, 5 Google), dual scoring (Python + LLM rubric), judge = Opus 4.6. Last updated: 2026-02-18 (full 13-provider matrix on all 9 evals).

**To re-run for a new model:** add provider block to each `tasks/*.yaml` → `promptfoo eval -c tasks/<name>.yaml --no-cache --filter-providers "ModelName" -j 3` → compare against existing results → update table above.

### Ideas Backlog
- `docs/inbox.md` captures features, patterns, and design concepts that are good but not in scope for current work.
- When a feature is deferred during story work, move it to `docs/inbox.md` rather than losing it.
- When a conversation surfaces a good idea that's out of scope, add it to `docs/inbox.md`.

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
| **MUST NOT** define utility functions inline in page files | Extract to `ui/src/lib/` |
| **MUST NOT** copy-paste JSX blocks across pages | Extract a shared component instead |

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

### Repo Map
- `src/cine_forge/driver/`: Orchestration runtime.
- `src/cine_forge/modules/`: Pipeline modules by stage.
- `src/cine_forge/schemas/`: Pydantic artifact schemas.
- `src/cine_forge/artifacts/`: Storage, versioning, and dependency graph.
- `src/cine_forge/api/`: Backend API for the UI.
- `ui/`: Production React frontend (shadcn/ui + React 19 + Zustand).

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

When adding a new screenplay for testing, create a corresponding golden reference following the same structure. Validate golden files by having a human read the screenplay and cross-check every entry.

### Worktree Strategy

The user runs multiple Claude Code sessions in parallel. To prevent git conflicts between sessions, we use **git worktrees** — each session works in its own directory on its own branch.

#### Orientation: Which Worktree Am I In?

When starting a session, run `git worktree list` to understand the layout. Common setup:

| Directory | Branch | Purpose |
|---|---|---|
| `cine-forge/` | `main` | Production code — pipeline, modules, UI, backend |
| `cine-forge-sidequests/` | `sidequests/<topic>` | Research, tooling, docs-only stories |

**If you are in `cine-forge/`** — you are on the main branch. Do code work here. Do NOT touch files that belong to an active side quest branch.

**If you are in `cine-forge-sidequests/`** (or similar) — you are on a feature branch. Do research, tooling evaluation, and documentation here. When done, tell the user so they can merge.

#### Rules

1. **Never work across worktrees.** Each session stays in its own directory. Don't read or write files in sibling worktrees.
2. **Branch naming**: `sidequests/<topic>` for research/tooling, `feature/<topic>` for code features.
3. **Merging**: Only the user (or the main session at the user's request) merges branches. Side quest sessions do NOT merge into main.
4. **Commits**: Each session commits to its own branch per the normal "No Implicit Commits" mandate. Commits on side quest branches are fine when the user requests them — they won't affect main.
5. **Shared files**: AGENTS.md, CLAUDE.md, and other root config files are tracked by git and shared across worktrees at their respective commit points. Avoid conflicting edits to these files across sessions — coordinate with the user.

#### Creating a New Worktree

When the user wants to start a new parallel workstream:

```bash
# From the main repo
git worktree add ../cine-forge-sidequests -b sidequests/<topic-name>
```

When a side quest is done and merged:

```bash
# Clean up
git worktree remove ../cine-forge-sidequests
git branch -d sidequests/<topic-name>
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

# Story 001: Project Setup and Scaffolding

**Status**: In Progress
**Created**: 2026-02-11
**Spec Refs**: All (foundation for everything); specifically 2.1–2.8 (design principles), 3 (pipeline overview), 20 (metadata & auditing)

---

## Goal

Bootstrap the cine-forge workspace so that it is immediately productive for agentic AI coding across Cursor, Claude Code, and Codex. Every structural decision must optimize for traceability, inspectability, provenance, TDD, and AI self-improvement.

This story produces zero pipeline functionality — it produces the scaffolding that makes all subsequent stories fast, consistent, and correct.

## Acceptance Criteria

- [x] Git repository initialized with a comprehensive `.gitignore` (Python, Node, output artifacts, secrets, OS files, IDE caches).
- [x] Project directory structure established per the layout below, with placeholder `__init__.py` files and README stubs where appropriate.
- [x] `AGENTS.md` at project root: comprehensive agentic coding guide following cross-agent standard (see AGENTS.md section below for full requirements).
- [ ] Cross-agent compatibility verified (runtime checks in all three tools still require manual verification):
  - [x] `AGENTS.md` at project root is the single source of truth for project-wide agent instructions (Cursor and Codex read natively).
  - [x] `CLAUDE.md` created with `@AGENTS.md` reference (Claude Code does not read AGENTS.md natively; this is the official recommended approach).
  - [x] Subdirectory `AGENTS.md` files used for directory-scoped guidance (e.g., `src/cine_forge/modules/AGENTS.md` for module development conventions). This is the cross-agent standard — works natively in Codex, supported by Cursor and Claude Code.
  - [x] `.cursor/rules/` used only if Cursor-specific activation modes are needed beyond what AGENTS.md covers (e.g., glob-scoped rules for specific file types). Not duplicating AGENTS.md content.
  - [x] No tool-specific duplication of core instructions — one file hierarchy (`AGENTS.md`), multiple consumers.
- [x] Cross-platform skills created in `skills/` directory using the Agent Skills spec (`SKILL.md` format with proper frontmatter):
  - [x] `create-module` — scaffold a new pipeline module (directory, `module.yaml`, `main.py`, test stub, schema registration).
  - [x] `create-story` — scaffold a new story file from template with proper numbering and index update.
  - [x] `create-role` — scaffold a new AI role definition (prompt persona, capability declaration, style pack slot).
  - [x] `run-pipeline` — execute a recipe via the driver with common flags documented.
- [x] Python project configuration: `pyproject.toml` with project metadata, dependencies section, and tool configs (pytest, ruff/linting).
- [x] TDD infrastructure:
  - [x] `tests/` directory with `unit/`, `integration/`, and `smoke/` subdirectories.
  - [x] `pytest` configured as test runner with markers for `unit`, `integration`, `smoke`.
  - [x] A trivial passing test (`tests/unit/test_placeholder.py`) to verify the test harness works.
  - [x] `Makefile` (or `justfile`) with `test`, `test-unit`, `test-integration`, `test-smoke`, `lint`, and `format` targets.
- [x] `README.md` with project overview, setup instructions, and quick-start for agentic development.
- [ ] All files committed as the initial commit.

## Project Directory Layout

```
cine-forge/
├── AGENTS.md                        # Cross-agent instructions (single source of truth)
├── CLAUDE.md                        # References AGENTS.md via @AGENTS.md (Claude Code convention)
├── README.md                        # Project overview and setup
├── Makefile                         # Common dev commands
├── pyproject.toml                   # Python project config, deps, tool settings
├── .gitignore
├── .cursor/
│   └── rules/                       # Cursor-specific rules (only if needed beyond AGENTS.md)
├── skills/                          # Cross-platform Agent Skills (SKILL.md format)
│   ├── create-module/
│   │   └── SKILL.md
│   ├── create-story/
│   │   └── SKILL.md
│   ├── create-role/
│   │   └── SKILL.md
│   └── run-pipeline/
│       └── SKILL.md
├── docs/
│   ├── spec.md                      # Project specification (exists)
│   ├── stories.md                   # Story index (exists)
│   └── stories/                     # Individual story files
├── src/
│   └── cine_forge/
│       ├── __init__.py
│       ├── driver/                  # Pipeline driver / orchestrator
│       │   └── __init__.py
│       ├── modules/                 # Pipeline stage modules
│       │   └── __init__.py
│       ├── schemas/                 # Pydantic schemas for all artifact types
│       │   └── __init__.py
│       ├── artifacts/               # Artifact store (versioning, deps, metadata)
│       │   └── __init__.py
│       └── roles/                   # AI role definitions and prompts
│           └── __init__.py
├── configs/
│   ├── recipes/                     # Pipeline recipes (YAML)
│   └── engine_packs/                # Render adapter engine packs (future)
├── style_packs/                     # Style pack library (future)
│   └── _generic/                    # Default generic packs (future)
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Shared fixtures
│   ├── unit/
│   │   └── __init__.py
│   ├── integration/
│   │   └── __init__.py
│   └── smoke/
│       └── __init__.py
├── scripts/                         # Utility scripts (non-skill helpers)
└── output/                          # Pipeline output (git-ignored)
    └── runs/                        # Per-run isolated output
```

## AGENTS.md Requirements

The `AGENTS.md` file is the single most important file in this project for agentic coding. It must include:

### Prime Directives
- **Do NOT run `git commit`, `git push`, or modify remotes unless the user explicitly requests it.**
- **AI-first project**: most processing steps are AI calls, not traditional code. Think in terms of prompts, roles, and artifacts — not just functions and classes.
- **Immutability is law**: no artifact is ever modified in place. All changes produce new versioned artifacts with lineage. If you find yourself editing an artifact file, stop — you're violating the core design principle.
- **Inspect outputs, not just logs**: a passing test or non-crashing run is not evidence of correctness. Always verify artifact content.

### Definition of Done
A task is NOT complete until:
1. Code passes all relevant tests (`make test-unit` at minimum).
2. If it produces artifacts: artifacts exist in `output/runs/` and have been manually inspected for correctness.
3. Schema validation passes on all produced artifacts.
4. The work log in the story file has been updated with results, evidence, and next steps.

### AI Self-Improvement Protocol (Critical)
**This section must be prominently placed and strongly worded.**

The AGENTS.md file is a living document. AI agents working on this project MUST update it when they learn something. Specifically:

- **When you stumble**: add a note under `## Lessons Learned` describing what went wrong, why, and how to avoid it. Be specific — include file paths, error messages, and the fix.
- **When you find a good approach**: add it under `## Effective Patterns` so you (and other agents) reuse it instead of reinventing.
- **When you make a mistake**: add it under `## Known Pitfalls` with the mistake, the symptom, and the correct approach. **You must not repeat the same mistake twice.**
- **When you discover a project-specific convention**: add it under `## Project Conventions` so it becomes standard.
- **Format**: each entry should be a dated, one-line summary with a short explanation. Example:
  ```
  ### Known Pitfalls
  - **2026-02-15 — Schema fields dropped on stamping**: If you add new fields to a module output, you MUST add them to the Pydantic schema or they'll be silently dropped during artifact validation. Always verify the validated artifact contains your new fields.
  ```

This protocol turns every mistake into a permanent improvement. The AGENTS.md grows smarter over time.

### Project Context
- Brief description of CineForge (film reasoning + production pipeline)
- Tech stack: Python 3.12+, Pydantic for schemas, YAML recipes, AI-driven pipeline
- Pointer to `docs/spec.md` for full specification
- Pointer to `docs/stories.md` for current work

### Architecture Overview
- Pipeline model: driver orchestrates modules via recipes; modules consume and produce immutable artifacts
- Artifact store: versioned snapshots with dependency graph and audit metadata
- Role system: AI roles are prompt personas with defined permissions and hierarchy
- Human interaction: approve/reject, creative sessions, direct editing

### Repo Map
- Key directories and what they contain
- How to find things (modules, schemas, recipes, stories, tests)

### Development Workflow
- TDD: write tests first when possible; `make test-unit` must pass before declaring done
- Module development: use `create-module` skill to scaffold; standalone test first, then integration
- Story workflow: use `create-story` skill; update work log as you go; mark acceptance criteria
- Common commands (via Makefile targets)

### Cross-Agent Notes
- `AGENTS.md` at root is the single source of truth for project-wide agent instructions
- Subdirectory `AGENTS.md` files provide directory-scoped guidance (cross-agent standard)
- Cursor and Codex read `AGENTS.md` natively (including subdirectory files)
- Claude Code reads `CLAUDE.md` which contains `@AGENTS.md` to pull in the shared instructions; also supports `.claude/rules/` for additional focused rule files
- Codex supports subdirectory `AGENTS.md` with proximity-based resolution (closest file to the code wins)
- Codex `.codex/rules/` is for execution policy (allow/prompt/forbid commands) — NOT behavioral guidance. Use only if needed for sandboxing.
- Cursor `.cursor/rules/` is for passive behavioral rules with activation modes (always-apply, intelligent, glob-scoped). Use only if AGENTS.md coverage is insufficient.
- Skills in `skills/` work across all three agents (Agent Skills SKILL.md format)
- For Cursor: rules (passive/persistent) and skills (active/on-demand) are complementary

## Skills Specifications

Each skill follows the Agent Skills spec (SKILL.md with YAML frontmatter + markdown body).

### create-module

Scaffolds a new pipeline module directory with:
- `module.yaml` (module manifest: id, stage, input/output schemas, description)
- `main.py` (entry point with argument parsing, artifact loading/saving, schema validation stubs)
- `tests/test_{module_id}.py` (test file with import check and placeholder test)
- Registration in the module index if one exists

Instructions should include the naming convention (`{stage}/{module_id}/`), required fields in `module.yaml`, and how to wire into a recipe.

### create-story

Scaffolds a new story file from template:
- Determines next story number from existing files
- Creates `docs/stories/story-{NNN}-{slug}.md` with standard sections (Status, Goal, Acceptance Criteria, Tasks, Notes, Work Log)
- Reminds the agent to update `docs/stories.md` index

### create-role

Scaffolds a new AI role definition:
- Role prompt template (system prompt with persona, permissions, style pack slot)
- Capability declaration (text, image, video, audio+video)
- Hierarchy position and review relationships
- Style pack creation prompt template (`_create.md`)

### run-pipeline

Documents how to execute the pipeline:
- Basic run: `python -m cine_forge.driver --recipe <path> --run-id <id>`
- Common flags: `--force`, `--start-from`, `--dry-run`, `--instrument`
- How to resume from a specific stage
- How to inspect output artifacts
- Cost monitoring during runs

## Tasks

- [x] Initialize git repository (`git init`) and create `.gitignore`.
- [x] Create the full directory structure with placeholder files.
- [x] Create `pyproject.toml` with project metadata, dependencies (pytest, pydantic, pyyaml, ruff), and tool configuration.
- [x] Create `Makefile` with dev targets (test, lint, format, etc.).
- [x] Write `AGENTS.md` following the requirements above. Include all sections with real content, not stubs.
- [x] Create `CLAUDE.md` with `@AGENTS.md` reference (Claude Code's official approach for AGENTS.md integration).
- [x] Create subdirectory `AGENTS.md` files for key directories (e.g., `src/cine_forge/modules/AGENTS.md` for module conventions, `tests/AGENTS.md` for testing conventions).
- [x] Create `.cursor/rules/` only if needed for Cursor-specific glob-scoped rules beyond AGENTS.md coverage. Otherwise, skip — AGENTS.md + subdirectory files are sufficient.
- [x] Create the four skills (`create-module`, `create-story`, `create-role`, `run-pipeline`) with proper SKILL.md frontmatter and actionable instructions.
- [x] Write `README.md` with project overview, prerequisites, setup instructions, and quick-start guide.
- [x] Create `tests/conftest.py` with shared fixtures and pytest markers.
- [x] Create `tests/unit/test_placeholder.py` with a trivial passing test.
- [x] Verify: `make test-unit` passes.
- [x] Verify: `make lint` passes (or produces only acceptable pre-existing warnings).
- [ ] Verify: all three agents (Cursor, Claude Code, Codex) can read the AGENTS.md. For Cursor, confirm the rule loads. For Claude Code, confirm the symlink resolves. For Codex, confirm AGENTS.md is at root. (Manual runtime verification pending in each tool UI.)
- [ ] Initial commit with all scaffolding.

## Notes

### Cross-Agent Compatibility Research (Feb 2026)

As of February 2026, the AI coding agent landscape has converged on two key cross-platform standards:

**AGENTS.md** — The dominant standard for AI agent configuration (originated from OpenAI, Aug 2025). A single markdown file at the project root. Natively supported by Cursor, Codex, OpenCode, GitHub Copilot, Zed, and 25+ other tools. **Notable exception**: Claude Code does NOT read AGENTS.md natively — it uses its own `CLAUDE.md` convention. The official workaround is to put `@AGENTS.md` inside your `CLAUDE.md` file, which causes Claude Code to load the AGENTS.md content. This maintains a single source of truth.

**Agent Skills** (SKILL.md format) — Cross-platform packages that teach agents domain-specific tasks. Open spec maintained by Anthropic. A skill is a directory with a `SKILL.md` file (YAML frontmatter + markdown instructions), optional `scripts/`, `references/`, and `assets/` directories. Skills use progressive disclosure: agents load name/description at startup (~100 tokens), full instructions when activated (<5000 tokens recommended), and resources only when needed. Works across Claude Code, Cursor, Codex, and other compatible agents.

**Directory-scoped guidance** — All three agents support directory-scoped instructions, but via different mechanisms:

| Concern | Cursor | Claude Code | Codex |
|---------|--------|-------------|-------|
| Project-wide guidance | `AGENTS.md` (native) | `CLAUDE.md` + `@AGENTS.md` | `AGENTS.md` (native) |
| Directory-scoped guidance | `.cursor/rules/` (glob patterns) OR subdirectory `AGENTS.md` | `.claude/rules/` (focused files) OR subdirectory `CLAUDE.md` | Subdirectory `AGENTS.md` (proximity resolution) |
| Execution policy | N/A | N/A | `.codex/rules/` (allow/prompt/forbid commands) |
| Skills | SKILL.md (on-demand) | SKILL.md (on-demand) | SKILL.md (on-demand) |

**Harmonization strategy**: Use `AGENTS.md` at root + subdirectory `AGENTS.md` files as the cross-agent standard for behavioral guidance. This works natively in Cursor and Codex, and Claude Code picks them up via `@AGENTS.md` references. Tool-specific rule directories (`.cursor/rules/`, `.claude/rules/`) should only be used for features that AGENTS.md cannot express (e.g., Cursor's glob-scoped activation modes). Codex `.codex/rules/` is unrelated — it's command sandboxing, not behavioral guidance.

**Key agent characteristics:**
- **Cursor**: reads AGENTS.md natively. Supports rules (passive) + skills (active). Instruction adherence can degrade in long sessions — front-load critical rules.
- **Claude Code**: does NOT read AGENTS.md natively. Use `CLAUDE.md` with `@AGENTS.md` reference. Has `.claude/rules/` for focused rule files. Best complex reasoning (200K token context). Strong instruction adherence.
- **Codex**: reads AGENTS.md natively with subdirectory proximity resolution. Has `.codex/rules/` for execution policy only. Went GA across all ChatGPT tiers. Supports MCP.
- **All three**: support the Agent Skills SKILL.md format for reusable workflows.

### Design Decisions

- **`src/` layout**: Using `src/cine_forge/` to prevent accidental imports from the project root. Standard Python packaging practice.
- **Pydantic for schemas**: Every artifact type gets a Pydantic model. Structural validation (QA tier 1 per spec 2.8) is automatic — just validate against the schema.
- **YAML recipes**: Pipeline workflows defined declaratively. Recipes reference module IDs, not code paths. Modules are discovered by convention (`src/cine_forge/modules/{stage}/{module_id}/`).
- **`output/` git-ignored**: All pipeline output is ephemeral and reproducible. Never commit artifacts.
- **Skills over scripts**: Common operations (scaffolding, running) are skills, not bash scripts. Skills are self-documenting, cross-agent, and follow the progressive disclosure pattern.

## Work Log

- 2026-02-11 — Initialized git repository and created scaffolding baseline files (`.gitignore`, `pyproject.toml`, `Makefile`, `README.md`, `AGENTS.md`, `CLAUDE.md`).
- 2026-02-11 — Created source tree under `src/cine_forge/` with package placeholders for `driver`, `modules`, `schemas`, `artifacts`, and `roles`.
- 2026-02-11 — Added directory-scoped guidance files: `src/cine_forge/modules/AGENTS.md` and `tests/AGENTS.md`.
- 2026-02-11 — Added cross-agent skills: `skills/create-module/SKILL.md`, `skills/create-story/SKILL.md`, `skills/create-role/SKILL.md`, and `skills/run-pipeline/SKILL.md`.
- 2026-02-11 — Added TDD baseline (`tests/conftest.py`, unit/integration/smoke packages, `tests/unit/test_placeholder.py`).
- 2026-02-11 — Verification: created local virtual environment (`.venv`), installed editable dev dependencies, and passed `make test-unit` and `make lint` using `PYTHON=.venv/bin/python`.
- 2026-02-11 — Remaining items intentionally not executed here: cross-agent runtime verification in Cursor/Claude/Codex and initial git commit (commit deferred until explicitly requested by user).

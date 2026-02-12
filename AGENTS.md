# AGENTS.md

This file is the project-wide source of truth for agent behavior in CineForge.

## Prime Directives

- Do not run `git commit`, `git push`, or modify remotes unless the user explicitly asks.
- This is an AI-first system: prefer prompt/role/artifact thinking over ad-hoc business rules.
- Immutability is mandatory: never mutate existing artifact versions in place.
- Inspect outputs, not only logs: correctness requires reviewing produced artifacts.

## Definition of Done

A task is not complete until all applicable items are true:

1. Relevant tests pass (`make test-unit` at minimum).
2. If artifacts are produced, artifact files exist and are manually inspected.
3. Schema validation passes for produced artifacts.
4. The active story's work log is updated with evidence and next actions.

## AI Self-Improvement Protocol (Critical)

Treat this file as a living memory. Update it when you learn.

- When you stumble, add an entry under `## Lessons Learned`.
- When you find a reliable technique, add it under `## Effective Patterns`.
- When you make a mistake, add it under `## Known Pitfalls` with symptom and correction.
- When a new repo convention emerges, document it under `## Project Conventions`.

Entry format:

- `YYYY-MM-DD — short title`: one-line summary plus a short explanation including file paths.

## Project Context

- CineForge is a film reasoning and production pipeline with immutable artifacts.
- Core stack: Python 3.12+, Pydantic schemas, YAML recipes, AI-driven module processing.
- Product specification: `docs/spec.md`
- Story plan and execution queue: `docs/stories.md`

## Architecture Overview

- Driver orchestrates modules from recipes.
- Modules consume and produce immutable, versioned artifacts.
- Artifact store tracks lineage, metadata, and dependency health.
- Roles represent AI personas with permissions/review responsibilities.
- Human interaction supports approve/reject, creative sessions, and direct edits.

## Repo Map

- `src/cine_forge/driver/`: orchestration runtime
- `src/cine_forge/modules/`: pipeline modules by stage
- `src/cine_forge/schemas/`: Pydantic artifact schemas
- `src/cine_forge/artifacts/`: artifact storage/versioning/dependency machinery
- `src/cine_forge/roles/`: role definitions and prompt assets
- `configs/recipes/`: YAML pipeline recipes
- `tests/`: unit, integration, smoke test suites
- `skills/`: cross-agent skill definitions

## Development Workflow

- Use TDD where practical; at minimum, add/adjust tests with implementation.
- Prefer small, composable modules with explicit schema IO contracts.
- Keep recipes declarative; modules should be referenced by module id.
- Run `make test-unit` and `make lint` before declaring completion.
- Update active story files with acceptance progress and work notes.

## Cross-Agent Notes

- Root `AGENTS.md` is the shared behavior contract across agents.
- Subdirectory `AGENTS.md` files are used for scoped guidance.
- Cursor and Codex read `AGENTS.md` natively.
- Claude Code should load this file through `CLAUDE.md` using `@AGENTS.md`.
- `.cursor/rules/` may be used only for Cursor-specific activation behavior not expressible here.
- `.codex/rules/` is execution policy only (allow/prompt/forbid), not behavior guidance.
- Skills in `skills/` are cross-platform and preferred for recurring workflows.

## Project Conventions

- Use `src/` layout to avoid accidental local-import behavior.
- Name module directories as `src/cine_forge/modules/{stage}/{module_id}/`.
- Keep artifact metadata explicit (intent, rationale, confidence, lineage, cost data).
- Keep generated outputs under `output/` and never commit them.

## Effective Patterns

- 2026-02-11 — Story-first implementation: Implement stories in dependency order and validate each with focused smoke checks.

## Known Pitfalls

- 2026-02-11 — Hidden schema drift: adding output fields without schema updates can silently drop data after validation.

## Lessons Learned

- 2026-02-11 — Keep cross-agent instructions centralized in `AGENTS.md` and reference from tool-specific files to avoid divergence.

# CineForge

CineForge is an AI-first film reasoning and production pipeline. It ingests creative input,
normalizes it into canonical screenplay form, extracts scene-level structure, and carries
forward immutable artifacts with full provenance.

## Tech Stack

- Python 3.12+
- Pydantic for schemas
- YAML recipes for pipeline orchestration
- Pytest + Ruff for quality checks

## Repository Layout

- `docs/spec.md`: product specification
- `docs/stories.md`: story index
- `docs/stories/`: individual story files
- `src/cine_forge/`: application code
- `tests/`: unit, integration, smoke tests
- `configs/recipes/`: pipeline recipes
- `skills/`: cross-agent reusable skills
- `output/`: runtime artifacts (git-ignored)

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
python3 -m pip install -e ".[dev]"
```

## Quick Start (Agentic Development)

- Read `AGENTS.md` first; it is the project-wide source of truth for AI agents.
- Use skills under `skills/` for common tasks.
- Run the baseline checks:

```bash
make test-unit
make lint
```

## Notes

- Artifacts are immutable snapshots. Never mutate an existing artifact in place.
- Prefer tests first (or tests alongside implementation) for all module work.

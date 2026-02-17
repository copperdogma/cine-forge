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

## MVP Pipeline Smoke Run

Run the full Story 007 MVP pipeline (ingest -> normalize -> scene extract -> project config)
using mocked AI calls and the canonical Story 007 fixture:

```bash
PYTHONPATH=src python -m cine_forge.driver \
  --recipe configs/recipes/recipe-mvp-ingest.yaml \
  --run-id smoke-test-001 \
  --param input_file=tests/fixtures/sample_screenplay.fountain \
  --param default_model=mock \
  --param qa_model=mock \
  --param accept_config=true
```

Equivalent convenience target:

```bash
make smoke-test
```

Optional live-model run (manual only; requires `OPENAI_API_KEY`):

```bash
make live-test
```

## Quality Gates and Semantic Validation

CineForge employs semantic quality gates to ensure that the pipeline produces meaningful artifacts
rather than structurally valid but empty or placeholder-heavy outputs.

### Automated Checks

- **Ingest Fidelity**: Detects and repairs tokenized or compact PDF layouts (e.g., from OCR or one-token-per-line extraction) to ensure scene-bearing structure is preserved.
- **Normalization Safeguards**: Rejects "degenerate" screenplay outputs (e.g., those defaulting to `UNKNOWN LOCATION` or `NARRATOR` when source content contains real scene headings).
- **Extraction Precision**: Validates scene counts and location/character presence against source expectations. Character extraction includes pronoun/noise filtering and derivative OCR suppression.
- **Metadata Health**: Artifacts failing semantic predicates are marked with `health: needs_review`.

### Known Limitations

- **Severely Mangled OCR**: While CineForge repairs common PDF extraction artifacts (merged tokens, token-per-line), extremely noisy OCR without recognizable screenplay signals may still fallback to `prose` classification or `needs_review` health.
- **Non-Standard Formatting**: Scripts with highly unconventional scene heading formats may require manual normalization or custom role-prompt adjustments.

## Produced Artifacts

The MVP recipe produces immutable artifacts under `output/project/artifacts/`:

- `raw_input/project/vN.json`: source text and format classification.
- `canonical_script/project/vN.json`: normalized screenplay with QA/cost metadata.
- `scene/scene_XXX/vN.json`: per-scene structured extraction artifacts.
- `scene_index/project/vN.json`: scene index and aggregate scene QA summary.
- `project_config/project/vN.json`: confirmed project configuration.

Per-run execution state is written to `output/runs/<run_id>/`:

- `run_state.json`: stage statuses, artifact refs, durations, and total cost.
- `pipeline_events.jsonl`: ordered stage start/finish events.

## Running the App

Start the API and UI in two terminals:

```bash
# Terminal 1: API (hot-reloads on save)
PYTHONPATH=src python -m cine_forge.api

# Terminal 2: UI
cd ui && npm install && npm run dev
```

- **API**: http://localhost:8000 (OpenAPI docs at `/docs`)
- **UI**: http://localhost:5174

## Notes

- Artifacts are immutable snapshots. Never mutate an existing artifact in place.
- Prefer tests first (or tests alongside implementation) for all module work.

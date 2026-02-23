---
name: run-pipeline
description: Run a CineForge recipe through the driver with standard flags and inspection steps.
user-invocable: true
---

# run-pipeline

Use this skill to execute pipeline recipes consistently.

## CLI Driver (standard runs)

```bash
PYTHONPATH=src .venv/bin/python -m cine_forge.driver --recipe <recipe-path> --run-id <run-id>
```

**Important**: The CLI driver always writes artifacts to `output/project/` in the workspace root. There is **no `--project-dir` flag**. For smoke tests or isolated runs that need a fresh directory, use the Programmatic API below.

### Common Flags

- `--dry-run`: validate recipe and stage plan without execution.
- `--start-from <stage_id>`: resume from a stage using existing upstream artifacts.
- `--force`: re-run stages even when output artifacts already exist.
- `--param key=value`: override recipe parameters.

### Execution Checklist

1. Validate recipe path and module ids.
2. Run with explicit `run-id`.
3. Capture and review stage-by-stage logs.
4. Inspect output artifacts under `output/project/`.
5. Confirm schema validation and metadata presence.
6. Check run-level cost summary.

---

## Recipe `runtime_params` Reference

| Recipe | Required params | Notes |
|--------|----------------|-------|
| `recipe-ingest-extract.yaml` | `input_file`, `model`, `qa_model` | `input_file` = absolute path to script |
| `recipe-world-building.yaml` | *(none)* | Models hardcoded in recipe yaml |
| `recipe-narrative-analysis.yaml` | `utility_model` | Used for entity_graph and continuity stages |

---

## Programmatic API (custom project dir, smoke tests)

Use `DriverEngine` directly when you need an isolated project directory (e.g. `output/smoke-NNN/`). This is the correct approach for smoke tests — it avoids polluting `output/project/` with test artifacts.

**Note**: Directories under `output/` are discovered by the UI's project scanner and will appear as projects. Smoke test projects will show no associated script (since `project.json` and `inputs/` are only written by the API layer), but the artifacts are fully inspectable via the UI.

```python
import sys
sys.path.insert(0, "src")

from pathlib import Path
from cine_forge.driver.engine import DriverEngine

project_dir = Path("output/smoke-045")
project_dir.mkdir(parents=True, exist_ok=True)

engine = DriverEngine(
    workspace_root=Path("/Users/cam/Documents/Projects/cine-forge"),
    project_dir=project_dir,
)

state = engine.run(
    recipe_path=Path("configs/recipes/recipe-ingest-extract.yaml"),
    run_id="smoke-045-ingest",
    runtime_params={
        "input_file": "/abs/path/to/script.md",
        "model": "claude-haiku-4-5-20251001",
        "qa_model": "claude-haiku-4-5-20251001",
    },
)

# Inspect results
for stage_id, s in state["stages"].items():
    print(f"  {stage_id}: {s['status']} ({len(s['artifact_refs'])} refs)")
```

Run multi-recipe pipelines sequentially against the same `project_dir` — downstream recipes resolve their `store_inputs` from that directory:

```python
# 1. Ingest
engine.run(recipe_path=Path("configs/recipes/recipe-ingest-extract.yaml"), run_id="smoke-ingest", runtime_params={...})

# 2. World-building (reads ingest artifacts from project_dir automatically)
engine.run(recipe_path=Path("configs/recipes/recipe-world-building.yaml"), run_id="smoke-worldbuild", runtime_params={})

# 3. Narrative analysis
engine.run(recipe_path=Path("configs/recipes/recipe-narrative-analysis.yaml"), run_id="smoke-graph", runtime_params={"utility_model": "claude-haiku-4-5-20251001"})
```

---

## Artifact Inspection

Use `ArtifactStore` to inspect output after a run. Note: there is **no `load_latest()` method** — use `list_versions()` + `load_artifact()`:

```python
from cine_forge.artifacts.store import ArtifactStore

store = ArtifactStore(project_dir=project_dir)

def load_latest(artifact_type: str, entity_id: str):
    refs = store.list_versions(artifact_type=artifact_type, entity_id=entity_id)
    if not refs:
        return None
    return store.load_artifact(refs[-1])  # refs sorted oldest→newest

# List all entities of a type
scene_ids = store.list_entities("scene")         # ["scene_001", "scene_002", ...]
prop_ids  = store.list_entities("prop_bible")    # ["bandolier", "oar", ...]
char_ids  = store.list_entities("character_bible")

# Load an artifact and inspect its data
art = load_latest("prop_bible", "bandolier")
print(art.data)      # dict — the artifact's payload
print(art.metadata)  # ArtifactMetadata

# Load entity graph
graph = load_latest("entity_graph", "project")
edges = graph.data["edges"]
prop_edges = [e for e in edges if e.get("source_type") == "prop"]
```

### Common `artifact_type` values

| Type | entity_id pattern | Produced by |
|------|-------------------|-------------|
| `scene` | `scene_001`, `scene_002`, … | `scene_breakdown_v1`, `scene_analysis_v1` |
| `scene_index` | `project` | `scene_breakdown_v1` |
| `character_bible` | `mariner`, `rose`, … | `character_bible_v1` |
| `location_bible` | `ruddy_green_building`, … | `location_bible_v1` |
| `prop_bible` | `bandolier`, `oar`, … | `prop_bible_v1` |
| `entity_graph` | `project` | `entity_graph_v1` |
| `canonical_script` | `script` | `normalize_v1` |

---

## Troubleshooting

- **`ValueError: Missing runtime parameter for placeholder '${...}'`** — grep the recipe yaml for `${...}` placeholders and ensure all are provided in `runtime_params`.
- **Schema validation fails** — inspect module output vs declared schema; check if new fields were added without schema update.
- **Dependency resolution fails** — inspect `needs` graph for missing/cyclic references.
- **`store_inputs` stage fails** — ensure the upstream recipe ran against the same `project_dir` and its artifacts are present and `VALID` health.
- **Project directory pollution** — reusing `output/project/` across recipe changes can cause stale artifact reuse. Use a fresh `output/smoke-NNN/` dir for testing.

---
name: run-pipeline
description: Run a CineForge recipe through the driver with standard flags and inspection steps.
---

# run-pipeline

Use this skill to execute pipeline recipes consistently.

## Basic Command

```bash
python -m cine_forge.driver --recipe <recipe-path> --run-id <run-id>
```

## Common Flags

- `--dry-run`: validate recipe and stage plan without execution.
- `--start-from <stage_id>`: resume from a stage using existing upstream artifacts.
- `--force`: re-run stages even when output artifacts already exist.
- `--param key=value`: override recipe parameters.

## Execution Checklist

1. Validate recipe path and module ids.
2. Run with explicit `run-id`.
3. Capture and review stage-by-stage logs.
4. Inspect output artifacts under `output/runs/<run-id>/`.
5. Confirm schema validation and metadata presence.
6. Check run-level cost summary.

## Troubleshooting

- If schema validation fails, inspect module output vs declared schema.
- If dependency resolution fails, inspect `needs` graph for missing/cyclic references.
- If run resumes incorrectly, verify `--start-from` stage id exists in recipe.

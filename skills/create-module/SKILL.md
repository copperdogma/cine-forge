---
name: create-module
description: Scaffold a new pipeline module with manifest, entry point, and tests.
user-invocable: true
---

# create-module

Use this skill to scaffold a module at `src/cine_forge/modules/{stage}/{module_id}/`.

## Inputs

- `stage`: pipeline stage directory (for example `ingest`, `bibles`, `direction`).
- `module_id`: stable module identifier ending with `_vN` for versioning.
- `input_schemas`: list of schema ids consumed.
- `output_schemas`: list of schema ids produced.

## Steps

1. Create module directory:
   - `src/cine_forge/modules/{stage}/{module_id}/`
2. Create `module.yaml` with:
   - `module_id`
   - `stage`
   - `description`
   - `input_schemas`
   - `output_schemas`
   - `parameters` (optional)
3. Create `main.py` with:
   - module entry function
   - parameter parsing
   - input artifact loading hooks
   - output schema validation hooks
4. Add a test file:
   - `tests/unit/test_{module_id}.py`
   - include import test and placeholder behavior test
5. If a schema registry file exists, register new schema ids.
6. Add an example recipe stage snippet in module docstring or README comment.

## Conventions

- Keep module logic single-purpose and composable.
- Do not hardcode file paths outside artifact store APIs.
- Always return explicit metadata and lineage.

---
name: create-role
description: Scaffold an AI role definition with persona, capabilities, and style pack slot.
---

# create-role

Use this skill to scaffold a new AI role in `src/cine_forge/roles/`.

## Inputs

- `role_id`: canonical identifier (for example `script_supervisor_v1`).
- `display_name`: human-readable role name.
- `capabilities`: media and reasoning capabilities.
- `reports_to`: supervising role (if any).

## Steps

1. Create role directory:
   - `src/cine_forge/roles/{role_id}/`
2. Add `role.yaml` including:
   - `role_id`
   - `display_name`
   - `purpose`
   - `permissions`
   - `capabilities`
   - `reports_to`
   - `style_pack_slot`
3. Add prompt files:
   - `system.md` (persona and operating contract)
   - `review.md` (quality gate expectations)
   - `_create.md` (instructions for style-pack generation workflows)
4. Add role test stub:
   - `tests/unit/test_role_{role_id}.py`
5. Document where this role participates in pipeline stages.

## Conventions

- Keep role prompts explicit about confidence and rationale requirements.
- Separate persona guidance from policy constraints.
- Include escalation behavior for low-confidence outputs.

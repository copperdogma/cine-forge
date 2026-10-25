"""Inspect selected scene media, or confirm an immutable plan through the driver.

Inspection performs no inference. Execution requires an explicitly supplied plan
response JSON and uses the same source, scope, claim and stale-plan gates as the API.
"""

from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path

from cine_forge.driver.engine import DriverEngine
from cine_forge.schemas.media_execution_plan import (
    MediaExecutionPlanRequest,
    MediaExecutionPlanResponse,
)
from cine_forge.services.media_execution_plans import save_media_execution_plan
from cine_forge.services.media_plan_execution import checked_execution, claim_media_plan


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", required=True, type=Path)
    parser.add_argument("--project-id", required=True)
    parser.add_argument("--recipe-id", choices=["render_generation", "ai_previz_generation"])
    parser.add_argument("--scene-id")
    parser.add_argument("--clip-id", action="append")
    parser.add_argument("--execute-plan", type=Path, help="JSON response from a prior inspection")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    project = args.project_dir.resolve()
    if args.execute_plan:
        if args.recipe_id or args.scene_id or args.clip_id:
            parser.error("Confirmation accepts the stored plan only, without scope overrides")
        response = MediaExecutionPlanResponse.model_validate_json(args.execute_plan.read_text())
        prepared = checked_execution(
            workspace_root=root,
            project_dir=project,
            project_id=args.project_id,
            ref=response.plan_ref,
        )
        run_id = f"run-{uuid.uuid4().hex[:8]}"
        claim_media_plan(project, response.plan_ref, run_id)
        runtime = {
            **prepared.runtime,
            "media_execution_plan_ref": response.plan_ref.model_dump(mode="json"),
        }
        state = DriverEngine(root, project_dir=project).run(
            recipe_path=root
            / "configs/recipes"
            / f"recipe-{prepared.plan.recipe_id.replace('_', '-')}.yaml",
            run_id=run_id,
            runtime_params=runtime,
            start_from=prepared.stage.id,
            end_at=prepared.request["end_at"],
        )
        print(json.dumps(state, indent=2))
    else:
        if not args.recipe_id or not args.scene_id:
            parser.error("Inspection requires --recipe-id and --scene-id")
        response = save_media_execution_plan(
            workspace_root=root,
            project_dir=project,
            project_id=args.project_id,
            request=MediaExecutionPlanRequest(
                recipe_id=args.recipe_id, scene_id=args.scene_id, render_clip_ids=args.clip_id
            ),
        )
        print(response.model_dump_json(indent=2))


if __name__ == "__main__":
    main()

"""CLI entry point for the CineForge driver."""

from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path
from typing import Any

import yaml

from cine_forge.driver.engine import DriverEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run CineForge pipeline recipes.")
    parser.add_argument("--recipe", required=True, help="Path to recipe YAML file.")
    parser.add_argument("--run-id", help="Optional run identifier.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and plan only.")
    parser.add_argument("--start-from", help="Start execution from a stage id.")
    parser.add_argument("--force", action="store_true", help="Force stage execution.")
    parser.add_argument(
        "--input-file",
        help="Optional runtime input file path exposed to modules as runtime params.",
    )
    parser.add_argument(
        "--instrument",
        action="store_true",
        help="Enable instrumentation marker in run state.",
    )
    parser.add_argument(
        "--accept-config",
        action="store_true",
        help="Auto-confirm draft project configuration output.",
    )
    parser.add_argument(
        "--config-file",
        help="Path to a user-edited project config draft to apply and confirm.",
    )
    parser.add_argument(
        "--autonomous",
        action="store_true",
        help="Set autonomous human control mode and auto-confirm config draft.",
    )
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="Runtime parameter override; repeatable (example: --param default_model=gpt-4o).",
    )
    parser.add_argument(
        "--params-file",
        help="YAML/JSON file containing runtime parameter key-value pairs.",
    )
    return parser


def _parse_param_overrides(raw_params: list[str]) -> dict[str, Any]:
    parsed: dict[str, Any] = {}
    for item in raw_params:
        if "=" not in item:
            raise ValueError(f"Invalid --param '{item}'. Expected KEY=VALUE format.")
        key, raw_value = item.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError(f"Invalid --param '{item}'. Key cannot be empty.")
        parsed[key] = yaml.safe_load(raw_value)
    return parsed


def _load_params_file(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    payload = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError("--params-file must contain a top-level mapping/object.")
    return payload


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    workspace_root = Path.cwd()
    engine = DriverEngine(workspace_root=workspace_root)
    runtime_params: dict[str, Any] = {}
    runtime_params.update(_load_params_file(args.params_file))
    runtime_params.update(_parse_param_overrides(args.param))
    if args.input_file:
        runtime_params["input_file"] = args.input_file
    if args.accept_config:
        runtime_params["accept_config"] = True
    if args.config_file:
        runtime_params["config_file"] = args.config_file
    if args.autonomous:
        runtime_params["autonomous"] = True

    run_id = args.run_id or f"run-{uuid.uuid4().hex[:8]}"
    try:
        state = engine.run(
            recipe_path=Path(args.recipe),
            run_id=run_id,
            dry_run=args.dry_run,
            start_from=args.start_from,
            force=args.force,
            instrument=args.instrument,
            runtime_params=runtime_params or None,
        )
    except Exception as exc:  # noqa: BLE001
        state_path = workspace_root / "output" / "runs" / run_id / "run_state.json"
        if state_path.exists():
            state = json.loads(state_path.read_text(encoding="utf-8"))
            completed = [
                stage_id
                for stage_id, stage_data in state["stages"].items()
                if stage_data["status"] in {"done", "skipped_reused"}
            ]
            print(f"[{run_id}] Run failed: {exc}")
            print(f"[{run_id}] Completed stages before failure: {', '.join(completed) or 'none'}")
        raise SystemExit(1) from exc

    produced = sum(len(stage["artifact_refs"]) for stage in state["stages"].values())
    print(f"[{run_id}] Success. Produced {produced} artifact refs.")


if __name__ == "__main__":
    main()

"""CLI entry point for the CineForge driver."""

from __future__ import annotations

import argparse
from pathlib import Path

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
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    workspace_root = Path.cwd()
    engine = DriverEngine(workspace_root=workspace_root)
    runtime_params = {}
    if args.input_file:
        runtime_params["input_file"] = args.input_file
    if args.accept_config:
        runtime_params["accept_config"] = True
    if args.config_file:
        runtime_params["config_file"] = args.config_file
    if args.autonomous:
        runtime_params["autonomous"] = True

    engine.run(
        recipe_path=Path(args.recipe),
        run_id=args.run_id,
        dry_run=args.dry_run,
        start_from=args.start_from,
        force=args.force,
        instrument=args.instrument,
        runtime_params=runtime_params or None,
    )


if __name__ == "__main__":
    main()

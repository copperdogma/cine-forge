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
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    workspace_root = Path.cwd()
    engine = DriverEngine(workspace_root=workspace_root)
    engine.run(
        recipe_path=Path(args.recipe),
        run_id=args.run_id,
        dry_run=args.dry_run,
        start_from=args.start_from,
        force=args.force,
        instrument=args.instrument,
        runtime_params={"input_file": args.input_file} if args.input_file else None,
    )


if __name__ == "__main__":
    main()

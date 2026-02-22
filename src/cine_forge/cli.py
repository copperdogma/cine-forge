import argparse
import json
import sys
import uuid
from pathlib import Path
from typing import Any

import yaml

from cine_forge.api.routers.export import load_all_artifacts
from cine_forge.artifacts.store import ArtifactStore
from cine_forge.driver.engine import DriverEngine
from cine_forge.export.markdown import MarkdownExporter
from cine_forge.export.pdf import PDFGenerator


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

def handle_run(args):
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
        sys.exit(1)

    produced = sum(len(stage["artifact_refs"]) for stage in state["stages"].values())
    print(f"[{run_id}] Success. Produced {produced} artifact refs.")

def handle_export(args):
    project_dir = Path("output") / args.project
    if not project_dir.exists():
        print(f"Error: Project '{args.project}' not found in output/")
        sys.exit(1)

    store = ArtifactStore(project_dir)
    scenes, characters, locations, props = load_all_artifacts(store)
    
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if args.format == "markdown":
        exporter = MarkdownExporter()
        if args.scope == "everything":
            content = exporter.generate_project_markdown(
                project_name=args.project, 
                project_id=args.project, 
                scenes=scenes, 
                characters=characters, 
                locations=locations, 
                props=props
            )
            out_path.write_text(content, encoding="utf-8")
            print(f"Exported project markdown to {out_path}")
        else:
            # TODO: Implement other scopes for CLI if needed, for now defaulting to everything
            print("CLI currently only supports 'everything' scope for markdown.")
            
    elif args.format == "pdf":
        pdf_gen = PDFGenerator()
        if args.layout == "call-sheet":
            pdf_gen.generate_call_sheet(
                project_name=args.project,
                scenes=scenes,
                output_path=str(out_path)
            )
            print(f"Exported call sheet PDF to {out_path}")
        else:
            pdf_gen.generate_project_pdf(
                project_name=args.project,
                project_id=args.project,
                scenes=scenes,
                characters=characters,
                locations=locations,
                props=props,
                output_path=str(out_path)
            )
            print(f"Exported project report PDF to {out_path}")

def main():
    parser = argparse.ArgumentParser(description="CineForge CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Run Command
    run_parser = subparsers.add_parser("run", help="Execute a pipeline recipe")
    run_parser.add_argument("--recipe", required=True, help="Path to recipe YAML file.")
    run_parser.add_argument("--run-id", help="Optional run identifier.")
    run_parser.add_argument("--dry-run", action="store_true", help="Validate and plan only.")
    run_parser.add_argument("--start-from", help="Start execution from a stage id.")
    run_parser.add_argument("--force", action="store_true", help="Force stage execution.")
    run_parser.add_argument("--input-file", help="Optional runtime input file path.")
    run_parser.add_argument("--instrument", action="store_true", help="Enable instrumentation.")
    run_parser.add_argument("--accept-config", action="store_true", help="Auto-confirm config.")
    run_parser.add_argument("--config-file", help="Path to config draft.")
    run_parser.add_argument("--autonomous", action="store_true", help="Autonomous mode.")
    run_parser.add_argument(
        "--param", action="append", default=[], 
        help="Runtime parameter override."
    )
    run_parser.add_argument("--params-file", help="Params file.")
    run_parser.set_defaults(func=handle_run)

    # Export Command
    export_parser = subparsers.add_parser("export", help="Export project artifacts")
    export_parser.add_argument("--project", required=True, help="Project ID")
    export_parser.add_argument(
        "--format", required=True, choices=["markdown", "pdf"], 
        help="Export format"
    )
    export_parser.add_argument(
        "--scope", default="everything", 
        help="Export scope (default: everything)"
    )
    export_parser.add_argument(
        "--layout", default="report", choices=["report", "call-sheet"], 
        help="PDF layout (default: report)"
    )
    export_parser.add_argument("--out", required=True, help="Output file path")
    export_parser.set_defaults(func=handle_export)

    args = parser.parse_args()
    args.func(args)

if __name__ == "__main__":
    main()

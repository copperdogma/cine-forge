from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Annotated, Literal

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, Response
from starlette.background import BackgroundTask

from cine_forge.artifacts.store import ArtifactStore
from cine_forge.export.call_sheet import generate_call_sheet_pdf
from cine_forge.export.cost_report import render_project_cost_csv, render_run_cost_csv
from cine_forge.export.interchange_fcpxml import (
    build_narrative_interchange_export,
    render_fcpxml,
)
from cine_forge.export.markdown import MarkdownExporter
from cine_forge.export.pdf import PDFGenerator
from cine_forge.export.project_loader import (
    load_all_artifacts,
    load_exportable_script_content,
    load_pre_scene_text,
    load_project_title,
)
from cine_forge.export.screenplay import ScreenplayRenderer
from cine_forge.export.shot_list import (
    generate_shot_list_pdf,
    load_shot_plans,
    render_shot_list_csv,
)
from cine_forge.services.cost_tracking import CostTrackingService

if TYPE_CHECKING:
    from cine_forge.api.service import OperatorConsoleService

router = APIRouter(prefix="/projects/{project_id}/export", tags=["export"])

ExportScope = Literal["everything", "scenes", "characters", "locations", "props", "single"]
ExportFormat = Literal["markdown", "pdf", "call-sheet", "fountain", "docx"]

_service: OperatorConsoleService | None = None
_REPORT_EXPORT_PRECONDITION = (
    "Project data PDF export requires basic breakdown artifacts. Run basic breakdown first."
)
_CALL_SHEET_PRECONDITION = (
    "Call sheet export requires scene breakdown artifacts. Run basic breakdown first."
)


def set_service(svc: OperatorConsoleService) -> None:
    """Called by create_app to inject the service instance."""
    global _service  # noqa: PLW0603
    _service = svc


def get_store(project_id: str) -> ArtifactStore:
    if _service is None:
        raise HTTPException(status_code=500, detail="Export router not initialized")
    project_dir = _service.require_project_path(project_id)
    return ArtifactStore(project_dir)


def get_cost_tracking_service() -> CostTrackingService:
    if _service is None:
        raise HTTPException(status_code=500, detail="Export router not initialized")
    return CostTrackingService(_service.workspace_root)

@router.get("/markdown")
def export_markdown(
    project_id: str,
    scope: Annotated[ExportScope, Query()] = "everything",
    entity_id: str | None = None,
    entity_type: str | None = None, # scene, character, location, prop
    include: Annotated[list[str] | None, Query()] = None
):
    store = get_store(project_id)
    exporter = MarkdownExporter()
    project_title = load_project_title(store, project_id)
    
    # Simple single entity case
    if scope == "single":
        if not entity_id or not entity_type:
            raise HTTPException(
                status_code=400, 
                detail="entity_id and entity_type required for single scope"
            )
        
        artifact_type = "scene" if entity_type == "scene" else f"{entity_type}_bible"
        versions = store.list_versions(artifact_type, entity_id)
        if not versions:
            raise HTTPException(status_code=404, detail="Entity not found")
        
        latest = sorted(versions, key=lambda r: r.version)[-1]
        data = store.load_artifact(latest).data
        
        if entity_type == "scene":
            md = exporter.generate_scene_markdown(data, data.get("scene_number", 0))
        else:
            md = exporter.generate_entity_markdown(data, entity_id, entity_type.title())
            
        return Response(content=md, media_type="text/markdown", headers={
            "Content-Disposition": f"attachment; filename={entity_id}.md"
        })

    # Collection cases
    scenes, characters, locations, props = load_all_artifacts(store)
    
    md = ""
    filename = f"{project_id}-export.md"

    if scope == "everything":
        try:
            script_content = load_exportable_script_content(store)
        except ValueError:
            script_content = ""
        
        md = exporter.generate_project_markdown(
            project_name=project_title,
            project_id=project_id,
            scenes=scenes,
            characters=characters,
            locations=locations,
            props=props,
            script_content=script_content,
            include=include
        )
    elif scope == "scenes":
        md = exporter.generate_header("Scenes", 1)
        for i, s in enumerate(scenes):
            md += exporter.generate_scene_markdown(s, s.get("scene_number", i+1)) + "---\n\n"
        filename = f"{project_id}-scenes.md"
    elif scope == "characters":
        md = exporter.generate_header("Characters", 1)
        for cid, c in characters.items():
            md += exporter.generate_entity_markdown(c, cid, "Character") + "---\n\n"
        filename = f"{project_id}-characters.md"
    elif scope == "locations":
        md = exporter.generate_header("Locations", 1)
        for lid, loc in locations.items():
            md += exporter.generate_entity_markdown(loc, lid, "Location") + "---\n\n"
        filename = f"{project_id}-locations.md"
    elif scope == "props":
        md = exporter.generate_header("Props", 1)
        for pid, p in props.items():
            md += exporter.generate_entity_markdown(p, pid, "Prop") + "---\n\n"
        filename = f"{project_id}-props.md"

    return Response(content=md, media_type="text/markdown", headers={
        "Content-Disposition": f"attachment; filename={filename}"
    })

@router.get("/fountain")
def export_fountain(project_id: str):
    store = get_store(project_id)
    try:
        content = load_exportable_script_content(store)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    
    return Response(
        content=content, 
        media_type="text/plain", 
        headers={"Content-Disposition": f"attachment; filename={project_id}.fountain"}
    )

@router.get("/pdf")
def export_pdf(
    project_id: str,
    layout: Annotated[Literal["report", "call-sheet", "screenplay"], Query()] = "report",
    include: Annotated[list[str] | None, Query()] = None
):
    store = get_store(project_id)
    scenes, characters, locations, props = load_all_artifacts(store)
    project_title = load_project_title(store, project_id)
    
    # Temp file for PDF
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        output_path = tmp.name

    pdf_gen = PDFGenerator()
    
    try:
        if layout == "call-sheet":
            if not scenes:
                raise HTTPException(status_code=409, detail=_CALL_SHEET_PRECONDITION)
            generate_call_sheet_pdf(
                project_name=project_title, 
                scenes=scenes, 
                output_path=output_path
            )
            filename = f"{project_id}-call-sheet.pdf"
        elif layout == "screenplay":
            renderer = ScreenplayRenderer()
            
            # If exporting the full script, use the canonical script text directly
            # for 100% fidelity (no reconstruction loss).
            only_script = (
                include and "script" in include 
                and not (include and "scenes" in include and len(include) > 1)
            )
            if only_script:
                try:
                    script_text = load_exportable_script_content(store)
                except ValueError as exc:
                    raise HTTPException(status_code=409, detail=str(exc)) from exc
                renderer.render_script_pdf(script_text, output_path)
            elif not scenes:
                try:
                    script_text = load_exportable_script_content(store)
                except ValueError as exc:
                    raise HTTPException(status_code=409, detail=str(exc)) from exc
                renderer.render_script_pdf(script_text, output_path)
            else:
                pre_scene_text = ""
                if scenes:
                    first_scene_line = scenes[0].get("source_span", {}).get("start_line", 1)
                    pre_scene_text = load_pre_scene_text(store, first_scene_line)
                
                renderer.render_pdf(
                    scenes=scenes, 
                    output_path=output_path, 
                    pre_scene_text=pre_scene_text, 
                    project_title=project_title
                )
            filename = f"{project_id}-screenplay.pdf"
        else:
            if not any((scenes, characters, locations, props)):
                raise HTTPException(status_code=409, detail=_REPORT_EXPORT_PRECONDITION)
            pdf_gen.generate_project_pdf(
                project_name=project_title, project_id=project_id,
                scenes=scenes, characters=characters, locations=locations, props=props,
                output_path=output_path
            )
            filename = f"{project_id}-report.pdf"
            
        return FileResponse(
            output_path, 
            filename=filename, 
            media_type="application/pdf",
            background=BackgroundTask(Path(output_path).unlink, missing_ok=True)
        )
    except HTTPException:
        Path(output_path).unlink(missing_ok=True)
        raise
    except Exception as e:
        Path(output_path).unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}") from e


@router.get("/fcpxml")
def export_fcpxml(project_id: str):
    store = get_store(project_id)
    project_title = load_project_title(store, project_id)

    try:
        payload = build_narrative_interchange_export(
            store,
            project_id=project_id,
            project_title=project_title,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    xml_content = render_fcpxml(payload)
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={
            "Content-Disposition": f"attachment; filename={project_id}-timeline.fcpxml"
        },
    )

@router.get("/docx")
def export_docx(
    project_id: str,
    include: Annotated[list[str] | None, Query()] = None
):
    store = get_store(project_id)
    scenes, _, _, _ = load_all_artifacts(store)
    project_title = load_project_title(store, project_id)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        output_path = tmp.name

    try:
        renderer = ScreenplayRenderer()
        only_script = (
            include and "script" in include
            and not (include and "scenes" in include and len(include) > 1)
        )
        if only_script or not scenes:
            try:
                script_text = load_exportable_script_content(store)
            except ValueError as exc:
                raise HTTPException(status_code=409, detail=str(exc)) from exc
            renderer.render_docx(
                scenes=[],
                output_path=output_path,
                pre_scene_text=script_text,
                project_title=project_title,
            )
        else:
            pre_scene_text = ""
            if scenes:
                first_scene_line = scenes[0].get("source_span", {}).get("start_line", 1)
                pre_scene_text = load_pre_scene_text(store, first_scene_line)

            renderer.render_docx(
                scenes=scenes,
                output_path=output_path,
                pre_scene_text=pre_scene_text,
                project_title=project_title,
            )
        filename = f"{project_id}-screenplay.docx"
            
        return FileResponse(
            output_path, 
            filename=filename, 
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            background=BackgroundTask(Path(output_path).unlink, missing_ok=True)
        )
    except HTTPException:
        Path(output_path).unlink(missing_ok=True)
        raise
    except Exception as e:
        Path(output_path).unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Docx generation failed: {str(e)}") from e


@router.get("/shot-list.csv")
def export_shot_list_csv(project_id: str):
    store = get_store(project_id)
    plans = load_shot_plans(store)
    if not plans:
        raise HTTPException(status_code=404, detail="Shot plans not found")

    csv_content = render_shot_list_csv(plans)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={project_id}-shot-list.csv"},
    )


@router.get("/shot-list.pdf")
def export_shot_list_pdf(project_id: str):
    store = get_store(project_id)
    plans = load_shot_plans(store)
    if not plans:
        raise HTTPException(status_code=404, detail="Shot plans not found")

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        output_path = tmp.name

    try:
        generate_shot_list_pdf(
            project_name=load_project_title(store, project_id),
            plans=plans,
            output_path=output_path,
        )
        return FileResponse(
            output_path,
            filename=f"{project_id}-shot-list.pdf",
            media_type="application/pdf",
            background=BackgroundTask(Path(output_path).unlink, missing_ok=True),
        )
    except Exception as exc:
        Path(output_path).unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail=f"Shot-list PDF generation failed: {str(exc)}",
        ) from exc


@router.get("/costs.csv")
def export_costs_csv(project_id: str, run_id: str | None = None):
    project_path = _service.require_project_path(project_id) if _service is not None else None
    if project_path is None:
        raise HTTPException(status_code=500, detail="Export router not initialized")

    cost_tracking = get_cost_tracking_service()
    if run_id:
        run_data = cost_tracking.load_run_data(run_id)
        if run_data.project_path != project_path:
            raise HTTPException(status_code=404, detail="Run not found for project")
        content = render_run_cost_csv(
            cost_tracking.build_run_summary(
                run_id=run_id,
                project_id=project_id,
                project_path=project_path,
            )
        )
        filename = f"{run_id}-costs.csv"
    else:
        content = render_project_cost_csv(
            cost_tracking.build_project_summary(
                project_id=project_id,
                project_path=project_path,
            )
        )
        filename = f"{project_id}-costs.csv"

    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/costs.json")
def export_costs_json(project_id: str, run_id: str | None = None):
    project_path = _service.require_project_path(project_id) if _service is not None else None
    if project_path is None:
        raise HTTPException(status_code=500, detail="Export router not initialized")

    cost_tracking = get_cost_tracking_service()
    if run_id:
        run_data = cost_tracking.load_run_data(run_id)
        if run_data.project_path != project_path:
            raise HTTPException(status_code=404, detail="Run not found for project")
        payload = cost_tracking.build_run_summary(
            run_id=run_id,
            project_id=project_id,
            project_path=project_path,
        ).model_dump(mode="json")
        filename = f"{run_id}-costs.json"
    else:
        payload = cost_tracking.build_project_summary(
            project_id=project_id,
            project_path=project_path,
        ).model_dump(mode="json")
        filename = f"{project_id}-costs.json"

    return Response(
        content=json.dumps(payload, indent=2, sort_keys=True),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

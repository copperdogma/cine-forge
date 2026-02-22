from typing import Annotated, Literal, List, Optional
from pathlib import Path
import tempfile
import shutil

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, Response

from cine_forge.artifacts.store import ArtifactStore
from cine_forge.export.markdown import MarkdownExporter
from cine_forge.export.pdf import PDFGenerator
from cine_forge.export.screenplay import ScreenplayRenderer

router = APIRouter(prefix="/projects/{project_id}/export", tags=["export"])

ExportScope = Literal["everything", "scenes", "characters", "locations", "props", "single"]
ExportFormat = Literal["markdown", "pdf", "call-sheet", "fountain", "docx"]

def get_store(project_id: str) -> ArtifactStore:
    project_dir = Path(f"output/{project_id}")
    if not project_dir.exists():
        raise HTTPException(status_code=404, detail="Project not found")
    return ArtifactStore(project_dir)

def load_all_artifacts(store: ArtifactStore):
    scenes = []
    characters = {}
    locations = {}
    props = {}

    # Load Scenes
    scene_ids = store.list_entities("scene")
    for sid in scene_ids:
        versions = store.list_versions("scene", sid)
        if versions:
            latest = sorted(versions, key=lambda r: r.version)[-1]
            data = store.load_artifact(latest).data
            if data:
                scenes.append(data)
    scenes.sort(key=lambda s: s.get("scene_number", 0))

    # Load Characters
    char_ids = store.list_entities("character_bible")
    for cid in char_ids:
        versions = store.list_versions("character_bible", cid)
        if versions:
            latest = sorted(versions, key=lambda r: r.version)[-1]
            data = store.load_artifact(latest).data
            if data:
                characters[cid] = data

    # Load Locations
    loc_ids = store.list_entities("location_bible")
    for lid in loc_ids:
        versions = store.list_versions("location_bible", lid)
        if versions:
            latest = sorted(versions, key=lambda r: r.version)[-1]
            data = store.load_artifact(latest).data
            if data:
                locations[lid] = data

    # Load Props
    prop_ids = store.list_entities("prop_bible")
    for pid in prop_ids:
        versions = store.list_versions("prop_bible", pid)
        if versions:
            latest = sorted(versions, key=lambda r: r.version)[-1]
            data = store.load_artifact(latest).data
            if data:
                props[pid] = data

    return scenes, characters, locations, props

def load_script_content(store: ArtifactStore) -> str:
    versions = store.list_versions("canonical_script", "project")
    if versions:
        latest = sorted(versions, key=lambda r: r.version)[-1]
        data = store.load_artifact(latest).data
        # Fix: added script_text
        return data.get("script_text") or data.get("content") or data.get("text") or ""
    return ""

def load_pre_scene_text(store: ArtifactStore, first_scene_start_line: int) -> str:
    versions = store.list_versions("canonical_script", "project")
    if versions:
        latest = sorted(versions, key=lambda r: r.version)[-1]
        data = store.load_artifact(latest).data
        full_text = data.get("script_text") or ""
        lines = full_text.splitlines()
        if first_scene_start_line > 1:
            return "\n".join(lines[:first_scene_start_line-1])
    return ""

@router.get("/markdown")
def export_markdown(
    project_id: str,
    scope: Annotated[ExportScope, Query()] = "everything",
    entity_id: str | None = None,
    entity_type: str | None = None, # scene, character, location, prop
    include: Annotated[List[str] | None, Query()] = None
):
    store = get_store(project_id)
    exporter = MarkdownExporter()
    
    if scope == "single":
        if not entity_id or not entity_type:
            raise HTTPException(status_code=400, detail="entity_id and entity_type required for single scope")
        
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

    scenes, characters, locations, props = load_all_artifacts(store)
    
    md = ""
    filename = f"{project_id}-export.md"

    if scope == "everything":
        script_content = load_script_content(store)
        
        md = exporter.generate_project_markdown(
            project_name=project_id,
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
        for lid, l in locations.items():
            md += exporter.generate_entity_markdown(l, lid, "Location") + "---\n\n"
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
    content = load_script_content(store)
    if not content:
        raise HTTPException(status_code=404, detail="Script not found")
    
    return Response(
        content=content, 
        media_type="text/plain", 
        headers={"Content-Disposition": f"attachment; filename={project_id}.fountain"}
    )

@router.get("/pdf")
def export_pdf(
    project_id: str,
    layout: Annotated[Literal["report", "call-sheet", "screenplay"], Query()] = "report"
):
    store = get_store(project_id)
    scenes, characters, locations, props = load_all_artifacts(store)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        output_path = tmp.name

    try:
        if layout == "call-sheet":
            pdf_gen = PDFGenerator()
            pdf_gen.generate_call_sheet(project_name=project_id, scenes=scenes, output_path=output_path)
            filename = f"{project_id}-call-sheet.pdf"
        elif layout == "screenplay":
            renderer = ScreenplayRenderer()
            # Extract pre-scene content
            pre_scene_text = ""
            if scenes:
                first_scene_line = scenes[0].get("source_span", {}).get("start_line", 1)
                pre_scene_text = load_pre_scene_text(store, first_scene_line)
            
            renderer.render_pdf(scenes=scenes, output_path=output_path, pre_scene_text=pre_scene_text)
            filename = f"{project_id}-screenplay.pdf"
        else:
            pdf_gen = PDFGenerator()
            pdf_gen.generate_project_pdf(
                project_name=project_id, project_id=project_id,
                scenes=scenes, characters=characters, locations=locations, props=props,
                output_path=output_path
            )
            filename = f"{project_id}-report.pdf"
            
        return FileResponse(
            output_path, 
            filename=filename, 
            media_type="application/pdf",
            background=lambda: Path(output_path).unlink(missing_ok=True)
        )
    except Exception as e:
        Path(output_path).unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")

@router.get("/docx")
def export_docx(project_id: str):
    store = get_store(project_id)
    scenes, _, _, _ = load_all_artifacts(store)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        output_path = tmp.name

    try:
        renderer = ScreenplayRenderer()
        # Extract pre-scene content
        pre_scene_text = ""
        if scenes:
            first_scene_line = scenes[0].get("source_span", {}).get("start_line", 1)
            pre_scene_text = load_pre_scene_text(store, first_scene_line)
            
        renderer.render_docx(scenes=scenes, output_path=output_path, pre_scene_text=pre_scene_text)
        filename = f"{project_id}-screenplay.docx"
            
        return FileResponse(
            output_path, 
            filename=filename, 
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            background=lambda: Path(output_path).unlink(missing_ok=True)
        )
    except Exception as e:
        Path(output_path).unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Docx generation failed: {str(e)}")

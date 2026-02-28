"""FastAPI app for CineForge API."""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, StreamingResponse

from cine_forge.api.models import (
    ArtifactDetailResponse,
    ArtifactEditRequest,
    ArtifactEditResponse,
    ArtifactGroupSummary,
    ArtifactVersionSummary,
    ChatMessagePayload,
    ChatStreamRequest,
    ErrorPayload,
    InputFileSummary,
    InsightRequest,
    IntentMoodInput,
    IntentMoodResponse,
    IntentMoodSuggestion,
    ProjectCreateRequest,
    ProjectPathRequest,
    ProjectSettingsUpdate,
    ProjectSummary,
    PropagatedGroupResponse,
    PropagateRequest,
    PropagationResponse,
    RecentProjectSummary,
    RecipeSummary,
    RunEventsResponse,
    RunStartRequest,
    RunStartResponse,
    RunStateResponse,
    RunSummary,
    ScriptContextResponse,
    SearchResponse,
    SlugPreviewRequest,
    SlugPreviewResponse,
    StylePresetResponse,
    UploadedInputResponse,
)
from cine_forge.api.routers import export
from cine_forge.api.service import OperatorConsoleService, ServiceError

UPLOAD_FILE_PARAM = File(...)


def _parse_version(workspace: Path) -> str:
    """Extract CalVer version (YYYY.MM.DD[-NN]) from the latest CHANGELOG.md entry."""
    changelog = workspace / "CHANGELOG.md"
    if changelog.exists():
        # Match YYYY-MM-DD or YYYY-MM-DD-NN
        pattern = r"^## \[(\d{4}-\d{2}-\d{2}(?:-\d{2})?)\]"
        match = re.search(pattern, changelog.read_text(), re.MULTILINE)
        if match:
            # Convert YYYY-MM-DD-02 -> 2026.02.20.02 or 2026.02.20-02
            # Let's stick to replacing dashes with dots for the main date part, 
            # but keep the suffix dash if present, or dot?
            # User asked for "v2026.02.20-02".
            # The regex capture group is "2026-02-20-02"
            raw = match.group(1)
            # Split date and suffix
            parts = raw.split("-")
            date_part = ".".join(parts[:3])
            if len(parts) > 3:
                return f"{date_part}-{parts[3]}"
            return date_part
    return "0.0.0"


def create_app(workspace_root: Path | None = None) -> FastAPI:
    resolved_workspace = workspace_root or Path(__file__).resolve().parents[3]
    service = OperatorConsoleService(workspace_root=resolved_workspace)
    app_version = _parse_version(resolved_workspace)
    app = FastAPI(title="CineForge API", version=app_version)
    app.state.console_service = service
    app.include_router(export.router, prefix="/api")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_origin_regex=(
            r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
            r"|^https://cineforge\.copper-dog\.com$"
        ),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(ServiceError)
    async def _handle_service_error(_, exc: ServiceError) -> JSONResponse:
        payload = ErrorPayload(code=exc.code, message=exc.message, hint=exc.hint)
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump())

    @app.exception_handler(RequestValidationError)
    async def _handle_validation_error(_, exc: RequestValidationError) -> JSONResponse:
        payload = ErrorPayload(
            code="invalid_request",
            message="Request validation failed.",
            hint=str(exc),
        )
        return JSONResponse(status_code=422, content=payload.model_dump())

    @app.get("/api/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "version": app_version}

    @app.get("/api/changelog")
    async def changelog() -> PlainTextResponse:
        changelog_path = resolved_workspace / "CHANGELOG.md"
        if not changelog_path.exists():
            return PlainTextResponse("No changelog available.", status_code=404)
        return PlainTextResponse(changelog_path.read_text())

    @app.get("/api/recipes", response_model=list[RecipeSummary])
    async def list_recipes() -> list[RecipeSummary]:
        return [RecipeSummary.model_validate(r) for r in service.list_recipes()]

    @app.get("/api/roles")
    async def list_roles() -> list[dict]:
        return service.list_roles()

    @app.get("/api/projects/recent", response_model=list[RecentProjectSummary])
    async def list_recent_projects() -> list[RecentProjectSummary]:
        return [
            RecentProjectSummary.model_validate(item)
            for item in service.list_recent_projects()
        ]

    @app.post("/api/projects/preview-slug", response_model=SlugPreviewResponse)
    async def preview_slug(request: SlugPreviewRequest) -> SlugPreviewResponse:
        result = service.generate_slug(request.content_snippet, request.original_filename)
        return SlugPreviewResponse.model_validate(result)

    @app.post("/api/projects/quick-scan", response_model=SlugPreviewResponse)
    async def quick_scan(
        file: UploadFile = UPLOAD_FILE_PARAM,
    ) -> SlugPreviewResponse:
        """Extract title and slug from an uploaded script snippet."""
        if not file.filename:
            raise ServiceError(
                code="missing_filename",
                message="Uploaded file must include a filename.",
                status_code=422,
            )
        # Read a reasonable chunk for quick-scan (e.g. up to 1MB)
        content = await file.read(1024 * 1024)
        result = service.quick_scan(file.filename, content)
        return SlugPreviewResponse.model_validate(result)

    @app.post("/api/projects/new", response_model=ProjectSummary)
    async def new_project(request: ProjectCreateRequest) -> ProjectSummary:
        if request.project_path:
            slug = service.create_project(request.project_path)
        elif request.slug and request.display_name:
            slug = service.create_project_from_slug(request.slug, request.display_name)
        else:
            raise HTTPException(
                status_code=400,
                detail="Either project_path or both slug and display_name must be provided."
            )
        return ProjectSummary.model_validate(service.project_summary(slug))

    @app.post("/api/projects/open", response_model=ProjectSummary)
    async def open_project(request: ProjectPathRequest) -> ProjectSummary:
        project_id = service.open_project(request.project_path)
        return ProjectSummary.model_validate(service.project_summary(project_id))

    @app.get("/api/projects/{project_id}", response_model=ProjectSummary)
    async def get_project(project_id: str) -> ProjectSummary:
        return ProjectSummary.model_validate(service.project_summary(project_id))

    @app.patch("/api/projects/{project_id}/settings", response_model=ProjectSummary)
    async def update_project_settings(
        project_id: str, request: ProjectSettingsUpdate,
    ) -> ProjectSummary:
        log = logging.getLogger("cine_forge.api.settings")
        log.info("Updating settings for project %s: %s", project_id, request.model_dump())
        try:
            return ProjectSummary.model_validate(
                service.update_project_settings(
                    project_id,
                    display_name=request.display_name,
                    human_control_mode=request.human_control_mode,
                    interaction_mode=request.interaction_mode,
                    style_packs=request.style_packs,
                    ui_preferences=request.ui_preferences,
                )
            )
        except Exception as exc:
            log.exception("Failed to update project settings")
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    @app.post(
        "/api/projects/{project_id}/inputs/upload",
        response_model=UploadedInputResponse,
    )
    async def upload_project_input(
        project_id: str,
        file: UploadFile = UPLOAD_FILE_PARAM,
    ) -> UploadedInputResponse:
        if not file.filename:
            raise ServiceError(
                code="missing_filename",
                message="Uploaded file must include a filename.",
                hint="Choose a local script/story file and retry.",
                status_code=422,
            )
        content = await file.read()
        if not content:
            raise ServiceError(
                code="empty_upload",
                message="Uploaded file is empty.",
                hint="Choose a non-empty script/story file and retry.",
                status_code=422,
            )
        return UploadedInputResponse.model_validate(
            service.save_project_input(project_id, file.filename, content)
        )

    @app.get(
        "/api/projects/{project_id}/inputs",
        response_model=list[InputFileSummary],
    )
    async def list_project_inputs(project_id: str) -> list[InputFileSummary]:
        return [
            InputFileSummary.model_validate(item)
            for item in service.list_project_inputs(project_id)
        ]

    @app.get("/api/projects/{project_id}/inputs/{filename}")
    async def get_project_input_content(project_id: str, filename: str) -> PlainTextResponse:
        content = service.read_project_input(project_id, filename)
        return PlainTextResponse(content)

    @app.get("/api/projects/{project_id}/search", response_model=SearchResponse)
    async def search_project(project_id: str, q: str = "") -> SearchResponse:
        return SearchResponse.model_validate(service.search_entities(project_id, q))

    @app.get("/api/projects/{project_id}/pipeline-graph")
    async def get_pipeline_graph(project_id: str) -> dict:
        return service.get_pipeline_graph(project_id)

    @app.get("/api/projects/{project_id}/chat")
    async def list_chat_messages(project_id: str) -> list[dict]:
        return service.list_chat_messages(project_id)

    @app.post("/api/projects/{project_id}/chat")
    async def append_chat_message(
        project_id: str, message: ChatMessagePayload,
    ) -> dict:
        return service.append_chat_message(project_id, message.model_dump(exclude_none=True))

    @app.get("/api/projects/{project_id}/runs", response_model=list[RunSummary])
    async def list_runs(project_id: str) -> list[RunSummary]:
        service.require_project_path(project_id)
        return [RunSummary.model_validate(item) for item in service.list_runs(project_id)]

    @app.get(
        "/api/projects/{project_id}/artifacts",
        response_model=list[ArtifactGroupSummary],
    )
    async def list_artifacts(project_id: str) -> list[ArtifactGroupSummary]:
        return [
            ArtifactGroupSummary.model_validate(item)
            for item in service.list_artifact_groups(project_id)
        ]

    @app.get(
        "/api/projects/{project_id}/artifacts/{artifact_type}/{entity_id}",
        response_model=list[ArtifactVersionSummary],
    )
    async def list_artifact_versions(
        project_id: str, artifact_type: str, entity_id: str
    ) -> list[ArtifactVersionSummary]:
        return [
            ArtifactVersionSummary.model_validate(item)
            for item in service.list_artifact_versions(project_id, artifact_type, entity_id)
        ]

    @app.get(
        "/api/projects/{project_id}/artifacts/{artifact_type}/{entity_id}/{version}",
        response_model=ArtifactDetailResponse,
    )
    async def get_artifact(
        project_id: str,
        artifact_type: str,
        entity_id: str,
        version: int,
    ) -> ArtifactDetailResponse:
        return ArtifactDetailResponse.model_validate(
            service.read_artifact(project_id, artifact_type, entity_id, version)
        )

    @app.post(
        "/api/projects/{project_id}/artifacts/{artifact_type}/{entity_id}/edit",
        response_model=ArtifactEditResponse,
    )
    async def edit_artifact(
        project_id: str,
        artifact_type: str,
        entity_id: str,
        request: ArtifactEditRequest,
    ) -> ArtifactEditResponse:
        return ArtifactEditResponse.model_validate(
            service.edit_artifact(
                project_id, artifact_type, entity_id, request.data, request.rationale
            )
        )

    # ------------------------------------------------------------------
    # Intent / Mood endpoints (Story 095)
    # ------------------------------------------------------------------

    @app.get(
        "/api/projects/{project_id}/style-presets",
        response_model=list[StylePresetResponse],
    )
    async def list_style_presets(project_id: str) -> list[StylePresetResponse]:
        """List all available style presets (vibe packages)."""
        from cine_forge.presets import list_presets

        # Validate project exists
        service.require_project_path(project_id)
        return [
            StylePresetResponse(
                preset_id=p.preset_id,
                display_name=p.display_name,
                description=p.description,
                mood_descriptors=p.mood_descriptors,
                reference_films=p.reference_films,
                thumbnail_emoji=p.thumbnail_emoji,
                concern_group_ids=list(p.concern_group_hints.keys()),
            )
            for p in list_presets()
        ]

    @app.get("/api/projects/{project_id}/intent-mood")
    async def get_intent_mood(
        project_id: str,
        scene_id: str | None = None,
    ) -> IntentMoodResponse | None:
        """Get current intent/mood for project or scene."""
        from cine_forge.artifacts import ArtifactStore

        project_path = service.require_project_path(project_id)
        store = ArtifactStore(project_dir=project_path)
        entity = scene_id or "project"
        refs = store.list_versions(artifact_type="intent_mood", entity_id=entity)
        if not refs:
            return None
        latest = refs[-1]
        artifact = store.load_artifact(latest)
        d = artifact.data
        version = latest.version
        return IntentMoodResponse(
            scope=d.get("scope", "project"),
            scene_id=d.get("scene_id"),
            mood_descriptors=d.get("mood_descriptors", []),
            reference_films=d.get("reference_films", []),
            style_preset_id=d.get("style_preset_id"),
            natural_language_intent=d.get("natural_language_intent"),
            user_approved=d.get("user_approved", False),
            version=version,
        )

    @app.post("/api/projects/{project_id}/intent-mood")
    async def save_intent_mood(
        project_id: str,
        request: IntentMoodInput,
    ) -> IntentMoodResponse:
        """Save (create or update) intent/mood for project or scene."""
        from cine_forge.artifacts import ArtifactStore
        from cine_forge.schemas import ArtifactMetadata

        project_path = service.require_project_path(project_id)
        store = ArtifactStore(project_dir=project_path)

        entity = request.scene_id or "project"
        data = {
            "scope": request.scope,
            "scene_id": request.scene_id,
            "mood_descriptors": request.mood_descriptors,
            "reference_films": request.reference_films,
            "style_preset_id": request.style_preset_id,
            "natural_language_intent": request.natural_language_intent,
            "user_approved": False,
        }

        # Check for existing versions to set lineage
        refs = store.list_versions(artifact_type="intent_mood", entity_id=entity)
        lineage = [refs[-1]] if refs else []

        metadata = ArtifactMetadata(
            lineage=lineage,
            intent="Set creative intent and mood",
            rationale="User-authored intent/mood for propagation to concern groups",
            confidence=1.0,
            source="human",
            producing_module="operator_console.intent_mood",
        )

        ref = store.save_artifact(
            artifact_type="intent_mood",
            entity_id=entity,
            data=data,
            metadata=metadata,
        )

        return IntentMoodResponse(
            **data,
            version=ref.version,
        )

    @app.post("/api/projects/{project_id}/intent-mood/propagate")
    async def propagate_mood(
        project_id: str,
        request: PropagateRequest,
    ) -> PropagationResponse:
        """Propagate intent/mood to all concern groups via Director AI."""
        from cine_forge.artifacts import ArtifactStore
        from cine_forge.presets import load_preset
        from cine_forge.schemas import ArtifactMetadata
        from cine_forge.schemas.concern_groups import IntentMood
        from cine_forge.services.intent_mood import propagate_intent

        project_path = service.require_project_path(project_id)
        store = ArtifactStore(project_dir=project_path)

        # Load current intent/mood
        entity = request.scene_id or "project"
        refs = store.list_versions(artifact_type="intent_mood", entity_id=entity)
        if not refs:
            raise ServiceError(
                code="no_intent_mood",
                message="No intent/mood set. Save intent/mood before propagating.",
                status_code=400,
            )
        artifact = store.load_artifact(refs[-1])
        intent = IntentMood.model_validate(artifact.data)

        # Load preset if specified
        preset = None
        if intent.style_preset_id:
            preset = load_preset(intent.style_preset_id)

        # Load script context (script bible or scene text)
        script_context = None
        bible_refs = store.list_versions(
            artifact_type="script_bible", entity_id="project"
        )
        if bible_refs:
            bible_artifact = store.load_artifact(bible_refs[-1])
            script_context = bible_artifact.data.get("summary", "")

        # Run propagation
        model = request.model or "claude-sonnet-4-6"
        result, _cost = propagate_intent(
            intent=intent,
            script_context=script_context,
            scene_id=request.scene_id,
            preset=preset,
            model=model,
        )

        # Save propagated drafts as concern group artifacts
        artifacts_created: list[str] = []
        concern_groups = {
            "look_and_feel": result.look_and_feel,
            "sound_and_music": result.sound_and_music,
            "rhythm_and_flow": result.rhythm_and_flow,
            "character_and_performance": result.character_and_performance,
            "story_world": result.story_world,
        }

        for group_id, group_data in concern_groups.items():
            if group_data is None:
                continue

            # Build artifact data from propagated fields
            artifact_data = dict(group_data.fields)
            artifact_data["user_approved"] = False

            # Set scope fields
            if request.scene_id:
                artifact_data["scope"] = "scene"
                artifact_data["scene_id"] = request.scene_id
            else:
                artifact_data["scope"] = "project"

            # Determine entity_id — project-wide groups use "project"
            artifact_entity = request.scene_id or "project"

            # Check for existing versions
            existing = store.list_versions(
                artifact_type=group_id, entity_id=artifact_entity
            )
            lineage = [existing[-1]] if existing else []

            metadata = ArtifactMetadata(
                lineage=lineage,
                intent="Propagated from intent/mood layer",
                rationale=group_data.rationale,
                confidence=result.confidence,
                source="ai",
                producing_module="intent_mood.propagation",
            )

            store.save_artifact(
                artifact_type=group_id,
                entity_id=artifact_entity,
                data=artifact_data,
                metadata=metadata,
            )
            artifacts_created.append(group_id)

        # Build response
        resp_groups: dict[str, PropagatedGroupResponse | None] = {}
        for gid in [
            "look_and_feel",
            "sound_and_music",
            "rhythm_and_flow",
            "character_and_performance",
            "story_world",
        ]:
            src = concern_groups.get(gid)
            resp_groups[gid] = (
                PropagatedGroupResponse(fields=src.fields, rationale=src.rationale)
                if src
                else None
            )

        return PropagationResponse(
            **resp_groups,
            overall_rationale=result.overall_rationale,
            confidence=result.confidence,
            artifacts_created=artifacts_created,
        )

    @app.get("/api/projects/{project_id}/script-context")
    async def get_script_context(
        project_id: str,
    ) -> ScriptContextResponse | None:
        """Get script bible context for the Intent page."""
        from cine_forge.artifacts import ArtifactStore

        project_path = service.require_project_path(project_id)
        store = ArtifactStore(project_dir=project_path)
        refs = store.list_versions(
            artifact_type="script_bible", entity_id="project"
        )
        if not refs:
            return None
        artifact = store.load_artifact(refs[-1])
        d = artifact.data
        # Extract theme names from ThematicElement objects
        raw_themes = d.get("themes", [])
        theme_names = []
        for t in raw_themes:
            if isinstance(t, dict):
                theme_names.append(t.get("theme", str(t)))
            else:
                theme_names.append(str(t))
        return ScriptContextResponse(
            title=d.get("title", "Untitled"),
            logline=d.get("logline", ""),
            genre=d.get("genre", ""),
            tone=d.get("tone", ""),
            themes=theme_names[:8],
        )

    @app.post("/api/projects/{project_id}/intent-mood/suggest")
    async def suggest_intent_mood(
        project_id: str,
    ) -> IntentMoodSuggestion:
        """Suggest an IntentMood from script bible analysis via LLM."""
        from cine_forge.ai.llm import call_llm
        from cine_forge.artifacts import ArtifactStore
        from cine_forge.presets import list_presets

        project_path = service.require_project_path(project_id)
        store = ArtifactStore(project_dir=project_path)
        refs = store.list_versions(
            artifact_type="script_bible", entity_id="project"
        )
        if not refs:
            raise ServiceError(
                code="no_script_bible",
                message="No script bible found. Run ingest first.",
                status_code=400,
            )
        artifact = store.load_artifact(refs[-1])
        d = artifact.data

        # Build preset summary for the prompt
        presets = list_presets()
        preset_lines = []
        for p in presets:
            preset_lines.append(
                f"- {p.preset_id}: {p.display_name} — "
                f"{p.description} "
                f"Moods: {', '.join(p.mood_descriptors)}. "
                f"Films: {', '.join(p.reference_films)}."
            )
        preset_catalog = "\n".join(preset_lines)

        # Extract theme names for context
        raw_themes = d.get("themes", [])
        theme_names = []
        for t in raw_themes:
            if isinstance(t, dict):
                theme_names.append(t.get("theme", str(t)))
            else:
                theme_names.append(str(t))

        prompt = f"""\
You are a creative film director. Given a script's metadata, suggest \
the best creative mood and style for this project.

SCRIPT CONTEXT:
- Title: {d.get("title", "Untitled")}
- Genre: {d.get("genre", "Unknown")}
- Tone: {d.get("tone", "Unknown")}
- Themes: {', '.join(theme_names[:5]) or 'None specified'}
- Logline: {d.get("logline", "")}

AVAILABLE STYLE PRESETS:
{preset_catalog}

INSTRUCTIONS:
1. Pick the single best-matching preset from the list above. Use its \
exact preset_id.
2. Choose 4-8 mood descriptors — evocative single words that capture \
the film's feeling. Include some from the matched preset but also add \
words specific to this script.
3. Suggest 3-5 reference films that match this script's tone and genre. \
You may use films from the preset or suggest others that fit better.
4. Write a brief natural language description of the creative direction \
(1-2 sentences).
5. Write a brief rationale explaining why you chose this preset and \
these mood words (1-2 sentences).

Return valid JSON matching the schema."""

        result, _meta = call_llm(
            prompt=prompt,
            model="claude-haiku-4-5-20251001",
            response_schema=IntentMoodSuggestion,
            max_tokens=1024,
            temperature=0.7,
        )
        if isinstance(result, IntentMoodSuggestion):
            return result
        # Fallback: if structured output failed, return a basic suggestion
        return IntentMoodSuggestion(
            mood_descriptors=[
                w.strip() for w in d.get("tone", "").split()[:5]
            ],
            rationale="Could not generate AI suggestion.",
        )

    @app.post("/api/projects/{project_id}/reviews/{scene_id}/{stage_id}/respond")
    async def respond_to_review(
        project_id: str,
        scene_id: str,
        stage_id: str,
        request: dict, # { "approved": bool, "feedback": str | None }
    ) -> ArtifactEditResponse:
        ref = service.respond_to_review(
            project_id=project_id,
            scene_id=scene_id,
            stage_id=stage_id,
            approved=request.get("approved", True),
            feedback=request.get("feedback"),
        )
        return ArtifactEditResponse(
            artifact_type=ref.artifact_type,
            entity_id=ref.entity_id,
            version=ref.version,
            path=ref.path,
        )

    @app.post("/api/runs/start", response_model=RunStartResponse)
    async def start_run(request: RunStartRequest) -> RunStartResponse:
        if request.retry_failed_stage_for_run_id:
            run_id = service.retry_failed_stage(request.retry_failed_stage_for_run_id)
        else:
            run_id = service.start_run(request.project_id, request.model_dump())
        return RunStartResponse(
            run_id=run_id,
            state_url=f"/api/runs/{run_id}/state",
            events_url=f"/api/runs/{run_id}/events",
        )

    @app.post("/api/runs/{run_id}/retry-failed-stage", response_model=RunStartResponse)
    async def retry_failed_stage(run_id: str) -> RunStartResponse:
        new_run_id = service.retry_failed_stage(run_id)
        return RunStartResponse(
            run_id=new_run_id,
            state_url=f"/api/runs/{new_run_id}/state",
            events_url=f"/api/runs/{new_run_id}/events",
        )

    @app.post("/api/runs/{run_id}/resume", response_model=RunStartResponse)
    async def resume_run(run_id: str) -> RunStartResponse:
        new_run_id = service.resume_run(run_id)
        return RunStartResponse(
            run_id=new_run_id,
            state_url=f"/api/runs/{new_run_id}/state",
            events_url=f"/api/runs/{new_run_id}/events",
        )

    @app.get("/api/runs/{run_id}/state", response_model=RunStateResponse)
    async def run_state(run_id: str) -> RunStateResponse:
        return RunStateResponse.model_validate(service.read_run_state(run_id))

    @app.get("/api/runs/{run_id}/events", response_model=RunEventsResponse)
    async def run_events(run_id: str) -> RunEventsResponse:
        return RunEventsResponse.model_validate(service.read_run_events(run_id))

    @app.get("/api/projects/{project_id}/characters")
    async def list_project_characters(project_id: str):
        """List characters available for @-mention chat.

        Returns characters from bible_manifest artifacts with their handles
        (entity_id stripped of 'character_' prefix) and display names.
        """
        groups = service.list_artifact_groups(project_id)
        characters = []
        for g in groups:
            if (g["artifact_type"] == "bible_manifest"
                    and (g.get("entity_id") or "").startswith("character_")):
                entity_id = g["entity_id"]
                handle = entity_id.replace("character_", "")
                # Try to get display name from the artifact
                display_name = handle.replace("_", " ").title()
                try:
                    detail = service.read_artifact(
                        project_id, "bible_manifest", entity_id,
                        g["latest_version"],
                    )
                    payload = detail.get("payload", {})
                    data = payload.get("data", payload)
                    display_name = data.get("name", display_name)
                except Exception:
                    pass
                characters.append({
                    "id": handle,
                    "entity_id": entity_id,
                    "name": display_name,
                    "prominence": "secondary",  # Default; enriched if available
                })
        return characters

    @app.post("/api/projects/{project_id}/chat/stream")
    async def chat_stream(project_id: str, request: ChatStreamRequest) -> StreamingResponse:
        """Stream AI chat responses using SSE with group chat routing.

        Detects @-mentions in the message to route to specific creative roles
        and/or project characters. Characters use Haiku model with no tools.
        """
        from cine_forge.ai.chat import (
            compute_project_state,
            resolve_target_roles,
            stream_group_chat,
        )
        from cine_forge.roles.runtime import RoleCatalog

        log = logging.getLogger("cine_forge.api.chat")

        # Assemble minimal context
        try:
            summary = service.project_summary(project_id)
            groups = service.list_artifact_groups(project_id)
            runs = service.list_runs(project_id)
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError(
                code="context_assembly_failed",
                message=f"Failed to assemble project context: {exc}",
                status_code=500,
            ) from exc

        state_info = compute_project_state(summary, groups, runs)

        # Load role catalog for routing and prompt building
        catalog = RoleCatalog()
        catalog.load_definitions()

        # Build character handle list from bible_manifest artifacts
        character_ids = [
            g["entity_id"].replace("character_", "")
            for g in groups
            if g["artifact_type"] == "bible_manifest"
            and (g.get("entity_id") or "").startswith("character_")
        ]

        # Resolve which roles/characters should respond
        targets = resolve_target_roles(
            request.message, request.active_role,
            character_ids=character_ids,
        )

        # If cap exceeded, return error immediately
        if targets.error:
            def error_stream():
                yield f"data: {json.dumps({'type': 'error', 'content': targets.error})}\n\n"
            return StreamingResponse(
                error_stream(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )

        # Read style pack selections from project.json
        try:
            project_path = service.require_project_path(project_id)
            pj = service._read_project_json(project_path) or {}
            style_packs = pj.get("style_packs", {})
        except Exception:
            style_packs = {}

        # Build messages array — full conversation thread
        # Activity notes are mapped to user role with [Activity] prefix
        # so the AI sees them as context it doesn't need to respond to.
        # Messages with a speaker are labeled for group chat context.
        api_messages: list[dict] = []
        for msg in request.chat_history:
            msg_type = msg.get("type", "")
            content = msg.get("content", "")
            speaker = msg.get("speaker", "")
            if not content:
                continue

            if msg_type == "activity":
                api_messages.append({
                    "role": "user",
                    "content": f"[Activity] {content}",
                })
            elif msg_type.startswith("user"):
                api_messages.append({"role": "user", "content": content})
            elif msg_type in ("ai_response", "ai_welcome", "ai_suggestion"):
                # Label role responses so the LLM knows who said what.
                # Strip any existing [@speaker]: prefixes the model may have
                # echoed back — prevents stacking ([@char:x]: [@char:x]: ...).
                clean = re.sub(r'^(\[@[\w:]+\]:\s*)+', '', content).lstrip()
                if speaker and speaker != "assistant":
                    labeled = f"[@{speaker}]: {clean}"
                else:
                    labeled = f"[@assistant]: {clean}"
                api_messages.append({"role": "assistant", "content": labeled})
            # Skip status/status_done/tool messages — they're UI chrome

        # Add the current user message
        api_messages.append({"role": "user", "content": request.message})

        # Ensure messages alternate correctly (Anthropic requires this)
        cleaned: list[dict] = []
        for msg in api_messages:
            if cleaned and cleaned[-1]["role"] == msg["role"]:
                cleaned[-1]["content"] += "\n" + msg["content"]
            else:
                cleaned.append(msg)
        if cleaned and cleaned[0]["role"] != "user":
            cleaned = cleaned[1:]

        def event_stream():
            try:
                for chunk in stream_group_chat(
                    messages=cleaned,
                    targets=targets,
                    project_summary=summary,
                    state_info=state_info,
                    service=service,
                    project_id=project_id,
                    catalog=catalog,
                    style_pack_selections=style_packs,
                    page_context=request.page_context,
                ):
                    yield f"data: {json.dumps(chunk)}\n\n"
            except Exception as exc:
                log.exception("Chat stream error")
                yield f"data: {json.dumps({'type': 'error', 'content': str(exc)})}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    @app.post("/api/projects/{project_id}/chat/insight")
    async def chat_insight(project_id: str, request: InsightRequest) -> StreamingResponse:
        """Generate a proactive AI insight (e.g., after a run completes).

        Unlike /chat/stream, this endpoint does not require a visible user message.
        The AI generates commentary based on the trigger type and project context.
        """
        from cine_forge.ai.chat import (
            build_insight_prompt,
            build_system_prompt,
            compute_project_state,
            stream_chat_response,
        )

        log = logging.getLogger("cine_forge.api.chat")

        try:
            summary = service.project_summary(project_id)
            groups = service.list_artifact_groups(project_id)
            runs = service.list_runs(project_id)
        except ServiceError:
            raise
        except Exception as exc:
            raise ServiceError(
                code="context_assembly_failed",
                message=f"Failed to assemble project context: {exc}",
                status_code=500,
            ) from exc

        state_info = compute_project_state(summary, groups, runs)

        system_prompt = build_system_prompt(summary, state_info)

        # Build the insight prompt based on trigger
        insight_prompt = build_insight_prompt(request.trigger, request.context)
        messages = [{"role": "user", "content": insight_prompt}]

        def event_stream():
            try:
                for chunk in stream_chat_response(
                    messages=messages,
                    system_prompt=system_prompt,
                    service=service,
                    project_id=project_id,
                ):
                    yield f"data: {json.dumps(chunk)}\n\n"
            except Exception as exc:
                log.exception("Insight stream error")
                yield f"data: {json.dumps({'type': 'error', 'content': str(exc)})}\n\n"

        return StreamingResponse(
            event_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no",
            },
        )

    @app.exception_handler(HTTPException)
    async def _handle_http_exception(_, exc: HTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "HTTP error"
        payload = ErrorPayload(code="http_error", message=detail, hint=None)
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump())

    # --- Static file serving for production (SPA) ---
    static_dir_env = os.environ.get("CINEFORGE_STATIC_DIR", "")
    static_dir = Path(static_dir_env) if static_dir_env else resolved_workspace / "static"
    if static_dir.exists() and (static_dir / "index.html").exists():
        _log = logging.getLogger("cine_forge.api.static")
        _log.info("Serving frontend from %s", static_dir)

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str) -> FileResponse:
            """Serve static files or fall back to index.html for SPA routing."""
            if full_path:
                file_path = (static_dir / full_path).resolve()
                if (
                    file_path.is_relative_to(static_dir.resolve())
                    and file_path.exists()
                    and file_path.is_file()
                ):
                    return FileResponse(file_path)
            return FileResponse(static_dir / "index.html")

    return app


app = create_app()

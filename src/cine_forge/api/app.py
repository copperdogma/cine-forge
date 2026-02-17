"""FastAPI app for CineForge API."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse

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
    ProjectCreateRequest,
    ProjectPathRequest,
    ProjectSettingsUpdate,
    ProjectSummary,
    RecentProjectSummary,
    RecipeSummary,
    RunEventsResponse,
    RunStartRequest,
    RunStartResponse,
    RunStateResponse,
    RunSummary,
    SearchResponse,
    SlugPreviewRequest,
    SlugPreviewResponse,
    UploadedInputResponse,
)
from cine_forge.api.service import OperatorConsoleService, ServiceError

UPLOAD_FILE_PARAM = File(...)


def create_app(workspace_root: Path | None = None) -> FastAPI:
    resolved_workspace = workspace_root or Path(__file__).resolve().parents[3]
    service = OperatorConsoleService(workspace_root=resolved_workspace)
    app = FastAPI(title="CineForge API", version="0.1.0")
    app.state.console_service = service

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[],
        allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
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
        return {"status": "ok"}

    @app.get("/api/recipes", response_model=list[RecipeSummary])
    async def list_recipes() -> list[RecipeSummary]:
        return [RecipeSummary.model_validate(r) for r in service.list_recipes()]

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

    @app.post("/api/projects/new", response_model=ProjectSummary)
    async def new_project(request: ProjectCreateRequest) -> ProjectSummary:
        slug = service.create_project_from_slug(request.slug, request.display_name)
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
        return ProjectSummary.model_validate(
            service.update_project_settings(project_id, display_name=request.display_name)
        )

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

    @app.post("/api/runs/start", response_model=RunStartResponse)
    async def start_run(request: RunStartRequest) -> RunStartResponse:
        run_id = service.start_run(request.project_id, request.model_dump())
        return RunStartResponse(
            run_id=run_id,
            state_url=f"/api/runs/{run_id}/state",
            events_url=f"/api/runs/{run_id}/events",
        )

    @app.get("/api/runs/{run_id}/state", response_model=RunStateResponse)
    async def run_state(run_id: str) -> RunStateResponse:
        return RunStateResponse.model_validate(service.read_run_state(run_id))

    @app.get("/api/runs/{run_id}/events", response_model=RunEventsResponse)
    async def run_events(run_id: str) -> RunEventsResponse:
        return RunEventsResponse.model_validate(service.read_run_events(run_id))

    @app.post("/api/projects/{project_id}/chat/stream")
    async def chat_stream(project_id: str, request: ChatStreamRequest) -> StreamingResponse:
        """Stream an AI chat response using SSE.

        Sends the full conversation thread (not windowed). The system prompt
        is lean and stable — dynamic project state is fetched via tools.
        """
        from cine_forge.ai.chat import (
            build_system_prompt,
            compute_project_state,
            stream_chat_response,
        )

        log = logging.getLogger("cine_forge.api.chat")

        # Assemble minimal context for the system prompt
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

        # Build messages array — full conversation thread
        # Activity notes are mapped to user role with [Activity] prefix
        # so the AI sees them as context it doesn't need to respond to.
        api_messages: list[dict] = []
        for msg in request.chat_history:
            msg_type = msg.get("type", "")
            content = msg.get("content", "")
            if not content:
                continue

            if msg_type == "activity":
                # Activity notes: compact context for the AI
                api_messages.append({
                    "role": "user",
                    "content": f"[Activity] {content}",
                })
            elif msg_type.startswith("user"):
                api_messages.append({"role": "user", "content": content})
            elif msg_type in ("ai_response", "ai_welcome", "ai_suggestion"):
                api_messages.append({"role": "assistant", "content": content})
            # Skip status/status_done/tool messages — they're UI chrome

        # Add the current user message
        api_messages.append({"role": "user", "content": request.message})

        # Ensure messages alternate correctly (Anthropic requires this)
        cleaned: list[dict] = []
        for msg in api_messages:
            if cleaned and cleaned[-1]["role"] == msg["role"]:
                # Merge consecutive same-role messages
                cleaned[-1]["content"] += "\n" + msg["content"]
            else:
                cleaned.append(msg)
        # Ensure first message is from user
        if cleaned and cleaned[0]["role"] != "user":
            cleaned = cleaned[1:]

        def event_stream():
            try:
                for chunk in stream_chat_response(
                    messages=cleaned,
                    system_prompt=system_prompt,
                    service=service,
                    project_id=project_id,
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

    return app


app = create_app()

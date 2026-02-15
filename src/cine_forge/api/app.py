"""FastAPI app for CineForge API."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from cine_forge.api.models import (
    ArtifactDetailResponse,
    ArtifactEditRequest,
    ArtifactEditResponse,
    ArtifactGroupSummary,
    ArtifactVersionSummary,
    ErrorPayload,
    ProjectPathRequest,
    ProjectSummary,
    RecentProjectSummary,
    RecipeSummary,
    RunEventsResponse,
    RunStartRequest,
    RunStartResponse,
    RunStateResponse,
    RunSummary,
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

    @app.post("/api/projects/new", response_model=ProjectSummary)
    async def new_project(request: ProjectPathRequest) -> ProjectSummary:
        project_id = service.create_project(request.project_path)
        return ProjectSummary.model_validate(service.project_summary(project_id))

    @app.post("/api/projects/open", response_model=ProjectSummary)
    async def open_project(request: ProjectPathRequest) -> ProjectSummary:
        project_id = service.open_project(request.project_path)
        return ProjectSummary.model_validate(service.project_summary(project_id))

    @app.get("/api/projects/{project_id}", response_model=ProjectSummary)
    async def get_project(project_id: str) -> ProjectSummary:
        return ProjectSummary.model_validate(service.project_summary(project_id))

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

    @app.exception_handler(HTTPException)
    async def _handle_http_exception(_, exc: HTTPException) -> JSONResponse:
        detail = exc.detail if isinstance(exc.detail, str) else "HTTP error"
        payload = ErrorPayload(code="http_error", message=detail, hint=None)
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump())

    return app


app = create_app()

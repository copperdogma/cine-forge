"""App liveness and provider dependency health routes."""

from __future__ import annotations

from fastapi import APIRouter, Query, Request

from cine_forge.api.exceptions import ServiceError
from cine_forge.schemas import (
    AppHealthResponse,
    ProviderCapabilitySmokeSnapshot,
    ProviderDependencyHealthSnapshot,
)

router = APIRouter(tags=["health"])


def _require_provider_health_service(request: Request):
    service = getattr(request.app.state, "provider_dependency_health_service", None)
    if service is None or not hasattr(service, "get_snapshot"):
        raise ServiceError(
            code="provider_dependency_health_uninitialized",
            message="Provider dependency health service is not initialized.",
            status_code=500,
        )
    return service


def _require_capability_smoke_service(request: Request):
    service = getattr(request.app.state, "provider_capability_smoke_service", None)
    if service is None or not hasattr(service, "get_snapshot") or not hasattr(service, "refresh"):
        raise ServiceError(
            code="provider_capability_smoke_uninitialized",
            message="Provider capability smoke service is not initialized.",
            status_code=500,
        )
    return service


@router.get("/health", response_model=AppHealthResponse)
async def health(request: Request) -> AppHealthResponse:
    version = str(getattr(request.app.state, "app_version", "0.0.0"))
    return AppHealthResponse(version=version)


@router.get(
    "/health/dependencies",
    response_model=ProviderDependencyHealthSnapshot,
)
async def dependency_health(
    request: Request,
    refresh: bool = Query(default=False),
) -> ProviderDependencyHealthSnapshot:
    service = _require_provider_health_service(request)
    return service.get_snapshot(refresh=refresh)


@router.get(
    "/health/live-smoke",
    response_model=ProviderCapabilitySmokeSnapshot,
)
async def capability_smoke_snapshot(
    request: Request,
) -> ProviderCapabilitySmokeSnapshot:
    service = _require_capability_smoke_service(request)
    return service.get_snapshot()


@router.post(
    "/health/live-smoke",
    response_model=ProviderCapabilitySmokeSnapshot,
)
async def capability_smoke_refresh(
    request: Request,
) -> ProviderCapabilitySmokeSnapshot:
    service = _require_capability_smoke_service(request)
    return service.refresh()

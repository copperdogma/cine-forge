"""Typed provider dependency health and live smoke contracts."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ProviderDependencyStatus = Literal[
    "ok",
    "missing",
    "auth_failed",
    "permission_failed",
    "quota_failed",
    "rate_limited",
    "unknown",
]
ProviderDependencyOverallStatus = Literal["ok", "degraded", "unknown"]
ProviderKey = Literal["anthropic", "google", "openai"]
ProviderCapabilityTested = Literal[
    "text_generation",
    "image_generation",
    "video_generation",
]


class AppHealthResponse(BaseModel):
    """App-local liveness response used by Fly."""

    status: Literal["ok"] = "ok"
    version: str


class ProviderDependencyCheck(BaseModel):
    """Cached readiness result for one required provider."""

    provider: ProviderKey
    configured: bool
    status: ProviderDependencyStatus
    preferred_env_var: str
    accepted_env_vars: list[str] = Field(default_factory=list)
    model_tested: str
    capability_tested: Literal["model_access"] = "model_access"
    last_checked_at: datetime | None = None
    latency_ms: int | None = Field(default=None, ge=0)
    failure_message: str | None = None
    request_id: str | None = None


class ProviderDependencyHealthSnapshot(BaseModel):
    """Top-level dependency health snapshot for required providers."""

    status: ProviderDependencyOverallStatus
    checked_at: datetime | None = None
    providers: dict[ProviderKey, ProviderDependencyCheck]


class ProviderCapabilitySmokeCheck(BaseModel):
    """Cached result for one real generation capability probe."""

    probe_id: str
    label: str
    provider: ProviderKey
    configured: bool
    status: ProviderDependencyStatus
    preferred_env_var: str
    accepted_env_vars: list[str] = Field(default_factory=list)
    capability_tested: ProviderCapabilityTested
    model_tested: str
    engine_pack_id: str | None = None
    surface_tested: str
    last_checked_at: datetime | None = None
    latency_ms: int | None = Field(default=None, ge=0)
    failure_message: str | None = None
    request_id: str | None = None


class ProviderCapabilitySmokeSnapshot(BaseModel):
    """Top-level cached snapshot for the expensive live capability smoke."""

    status: ProviderDependencyOverallStatus
    checked_at: datetime | None = None
    checks: list[ProviderCapabilitySmokeCheck] = Field(default_factory=list)

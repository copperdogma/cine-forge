from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cine_forge.api.app import create_app
from cine_forge.schemas import (
    ProviderCapabilitySmokeCheck,
    ProviderCapabilitySmokeSnapshot,
    ProviderDependencyCheck,
    ProviderDependencyHealthSnapshot,
)


class _FakeProviderHealthService:
    def __init__(self, snapshot: ProviderDependencyHealthSnapshot) -> None:
        self.snapshot = snapshot
        self.calls: list[bool] = []

    def get_snapshot(self, *, refresh: bool = False) -> ProviderDependencyHealthSnapshot:
        self.calls.append(refresh)
        return self.snapshot


class _FakeCapabilitySmokeService:
    def __init__(self, snapshot: ProviderCapabilitySmokeSnapshot) -> None:
        self.snapshot = snapshot
        self.get_calls = 0
        self.refresh_calls = 0

    def get_snapshot(self, *, refresh: bool = False) -> ProviderCapabilitySmokeSnapshot:
        self.get_calls += 1
        assert refresh is False
        return self.snapshot

    def refresh(self) -> ProviderCapabilitySmokeSnapshot:
        self.refresh_calls += 1
        return self.snapshot


def _make_client(workspace_root: Path) -> TestClient:
    return TestClient(create_app(workspace_root=workspace_root))


def _snapshot() -> ProviderDependencyHealthSnapshot:
    return ProviderDependencyHealthSnapshot(
        status="degraded",
        checked_at=None,
        providers={
            "anthropic": ProviderDependencyCheck(
                provider="anthropic",
                configured=True,
                status="ok",
                preferred_env_var="CINE_FORGE_ANTHROPIC_API_KEY",
                accepted_env_vars=["CINE_FORGE_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY"],
                model_tested="claude-sonnet-4-6",
            ),
            "google": ProviderDependencyCheck(
                provider="google",
                configured=False,
                status="missing",
                preferred_env_var="CINE_FORGE_GEMINI_API_KEY",
                accepted_env_vars=["CINE_FORGE_GEMINI_API_KEY", "GEMINI_API_KEY"],
                model_tested="gemini-2.5-flash-lite",
                failure_message="CINE_FORGE_GEMINI_API_KEY (or legacy GEMINI_API_KEY) is not set",
            ),
            "openai": ProviderDependencyCheck(
                provider="openai",
                configured=True,
                status="auth_failed",
                preferred_env_var="CINE_FORGE_OPENAI_API_KEY",
                accepted_env_vars=["CINE_FORGE_OPENAI_API_KEY", "OPENAI_API_KEY"],
                model_tested="gpt-4.1-mini",
                failure_message="Invalid API key provided.",
            ),
            "xai": ProviderDependencyCheck(
                provider="xai",
                configured=False,
                status="missing",
                preferred_env_var="CINE_FORGE_XAI_API_KEY",
                accepted_env_vars=["CINE_FORGE_XAI_API_KEY", "XAI_API_KEY"],
                model_tested="grok-imagine-video",
                failure_message="CINE_FORGE_XAI_API_KEY (or legacy XAI_API_KEY) is not set",
            ),
        },
    )


def _capability_snapshot() -> ProviderCapabilitySmokeSnapshot:
    return ProviderCapabilitySmokeSnapshot(
        status="degraded",
        checked_at=None,
        checks=[
            ProviderCapabilitySmokeCheck(
                probe_id="anthropic_text_default",
                label="Anthropic text generation",
                provider="anthropic",
                configured=True,
                status="ok",
                preferred_env_var="CINE_FORGE_ANTHROPIC_API_KEY",
                accepted_env_vars=["CINE_FORGE_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY"],
                capability_tested="text_generation",
                model_tested="claude-sonnet-4-6",
                surface_tested="Default text analysis lane",
            ),
            ProviderCapabilitySmokeCheck(
                probe_id="google_storyboard_image_default",
                label="Google storyboard image generation",
                provider="google",
                configured=True,
                status="auth_failed",
                preferred_env_var="CINE_FORGE_GEMINI_API_KEY",
                accepted_env_vars=["CINE_FORGE_GEMINI_API_KEY", "GEMINI_API_KEY"],
                capability_tested="image_generation",
                model_tested="imagen-4.0-generate-001",
                surface_tested="Storyboard generation default lane",
                failure_message="Imagen API returned HTTP 400: API key not valid.",
            ),
            ProviderCapabilitySmokeCheck(
                probe_id="xai_ai_previz_video_default",
                label="xAI AI previz video generation",
                provider="xai",
                configured=False,
                status="missing",
                preferred_env_var="CINE_FORGE_XAI_API_KEY",
                accepted_env_vars=["CINE_FORGE_XAI_API_KEY", "XAI_API_KEY"],
                capability_tested="video_generation",
                model_tested="grok-imagine-video",
                engine_pack_id="xai_grok_imagine_video",
                surface_tested="AI Previz shipped default lane",
                failure_message="CINE_FORGE_XAI_API_KEY (or legacy XAI_API_KEY) is not set",
            ),
        ],
    )


@pytest.mark.unit
def test_health_endpoint_returns_app_local_liveness(tmp_path: Path) -> None:
    client = _make_client(tmp_path)

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.0.0"}


@pytest.mark.unit
def test_dependency_health_endpoint_returns_typed_snapshot_and_refresh_flag(tmp_path: Path) -> None:
    client = _make_client(tmp_path)
    fake_service = _FakeProviderHealthService(_snapshot())
    client.app.state.provider_dependency_health_service = fake_service

    response = client.get("/api/health/dependencies?refresh=true")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["providers"]["anthropic"]["status"] == "ok"
    assert payload["providers"]["google"]["status"] == "missing"
    assert payload["providers"]["openai"]["status"] == "auth_failed"
    assert payload["providers"]["xai"]["accepted_env_vars"] == [
        "CINE_FORGE_XAI_API_KEY",
        "XAI_API_KEY",
    ]
    assert fake_service.calls == [True]


@pytest.mark.unit
def test_live_capability_smoke_endpoints_return_cached_and_refreshed_snapshots(
    tmp_path: Path,
) -> None:
    client = _make_client(tmp_path)
    fake_service = _FakeCapabilitySmokeService(_capability_snapshot())
    client.app.state.provider_capability_smoke_service = fake_service

    cached = client.get("/api/health/live-smoke")
    refreshed = client.post("/api/health/live-smoke")

    assert cached.status_code == 200
    assert refreshed.status_code == 200
    cached_payload = cached.json()
    refreshed_payload = refreshed.json()
    assert cached_payload["status"] == "degraded"
    assert refreshed_payload["checks"][1]["status"] == "auth_failed"
    assert refreshed_payload["checks"][2]["engine_pack_id"] == "xai_grok_imagine_video"
    assert fake_service.get_calls == 1
    assert fake_service.refresh_calls == 1

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from cine_forge.api.app import create_app
from cine_forge.schemas import ProviderDependencyCheck, ProviderDependencyHealthSnapshot


class _FakeProviderHealthService:
    def __init__(self, snapshot: ProviderDependencyHealthSnapshot) -> None:
        self.snapshot = snapshot
        self.calls: list[bool] = []

    def get_snapshot(self, *, refresh: bool = False) -> ProviderDependencyHealthSnapshot:
        self.calls.append(refresh)
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
        },
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
    assert fake_service.calls == [True]

from __future__ import annotations

import pytest

from cine_forge.services.provider_dependency_health import (
    ProviderDependencyHealthService,
    _HttpJsonError,
    _HttpJsonResponse,
)


def _clear_provider_envs(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "ANTHROPIC_API_KEY",
        "CINE_FORGE_ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "CINE_FORGE_GEMINI_API_KEY",
        "OPENAI_API_KEY",
        "CINE_FORGE_OPENAI_API_KEY",
        "XAI_API_KEY",
        "CINE_FORGE_XAI_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.mark.unit
def test_refresh_marks_missing_provider_keys_without_hitting_network(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_provider_envs(monkeypatch)
    calls: list[tuple[str, dict[str, str], float]] = []

    def fake_http_get_json(
        url: str,
        headers: dict[str, str],
        timeout_seconds: float,
    ) -> _HttpJsonResponse:
        calls.append((url, headers, timeout_seconds))
        return _HttpJsonResponse(headers={}, payload={})

    service = ProviderDependencyHealthService(http_get_json=fake_http_get_json)
    snapshot = service.get_snapshot(refresh=True)

    assert calls == []
    assert snapshot.status == "degraded"
    assert snapshot.providers["anthropic"].status == "missing"
    assert snapshot.providers["google"].status == "missing"
    assert snapshot.providers["openai"].status == "missing"
    assert snapshot.providers["xai"].status == "missing"
    assert snapshot.providers["xai"].accepted_env_vars == [
        "CINE_FORGE_XAI_API_KEY",
        "XAI_API_KEY",
    ]
    assert snapshot.providers["google"].accepted_env_vars == [
        "CINE_FORGE_GEMINI_API_KEY",
        "GEMINI_API_KEY",
    ]


@pytest.mark.unit
def test_refresh_classifies_provider_health_results(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_provider_envs(monkeypatch)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anth-key")
    monkeypatch.setenv("CINE_FORGE_GEMINI_API_KEY", "google-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("CINE_FORGE_XAI_API_KEY", "xai-key")

    def fake_http_get_json(
        url: str,
        headers: dict[str, str],
        timeout_seconds: float,
    ) -> _HttpJsonResponse:
        assert timeout_seconds == 10.0
        if "api.anthropic.com" in url:
            raise _HttpJsonError(
                status_code=403,
                message="Model access forbidden for this key.",
                headers={"request-id": "req-anthropic"},
                payload={},
            )
        if "generativelanguage.googleapis.com" in url:
            return _HttpJsonResponse(headers={"x-request-id": "req-google"}, payload={"name": "ok"})
        if "api.openai.com" in url:
            raise _HttpJsonError(
                status_code=401,
                message="Invalid API key provided.",
                headers={"x-request-id": "req-openai"},
                payload={},
            )
        if "api.x.ai" in url:
            assert url.endswith("/v1/video-generation-models/grok-imagine-video")
            assert headers["Authorization"] == "Bearer xai-key"
            return _HttpJsonResponse(headers={"x-request-id": "req-xai"}, payload={"id": "ok"})
        raise AssertionError(f"Unexpected probe URL: {url}")

    service = ProviderDependencyHealthService(http_get_json=fake_http_get_json)
    snapshot = service.get_snapshot(refresh=True)

    assert snapshot.status == "degraded"
    assert snapshot.checked_at is not None
    assert snapshot.providers["anthropic"].status == "permission_failed"
    assert snapshot.providers["anthropic"].request_id == "req-anthropic"
    assert snapshot.providers["google"].status == "ok"
    assert snapshot.providers["google"].request_id == "req-google"
    assert snapshot.providers["openai"].status == "auth_failed"
    assert snapshot.providers["openai"].request_id == "req-openai"
    assert snapshot.providers["xai"].status == "ok"
    assert snapshot.providers["xai"].preferred_env_var == "CINE_FORGE_XAI_API_KEY"
    assert snapshot.providers["xai"].request_id == "req-xai"


@pytest.mark.unit
def test_get_snapshot_reuses_cached_results_until_refresh_requested(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_provider_envs(monkeypatch)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anth-key")
    monkeypatch.setenv("GEMINI_API_KEY", "google-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    monkeypatch.setenv("XAI_API_KEY", "xai-key")
    calls: list[str] = []

    def fake_http_get_json(
        url: str,
        headers: dict[str, str],
        timeout_seconds: float,
    ) -> _HttpJsonResponse:
        calls.append(url)
        return _HttpJsonResponse(headers={}, payload={"ok": True})

    service = ProviderDependencyHealthService(http_get_json=fake_http_get_json)

    first = service.get_snapshot(refresh=True)
    second = service.get_snapshot()

    assert len(calls) == 4
    assert first.model_dump(mode="json") == second.model_dump(mode="json")

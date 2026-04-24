from __future__ import annotations

import pytest

from cine_forge.ai.image import ImageGenerationError
from cine_forge.ai.video import VideoGenerationError
from cine_forge.services.provider_capability_smoke import ProviderCapabilitySmokeService


def _clear_provider_envs(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "ANTHROPIC_API_KEY",
        "CINE_FORGE_ANTHROPIC_API_KEY",
        "GEMINI_API_KEY",
        "CINE_FORGE_GEMINI_API_KEY",
        "OPENAI_API_KEY",
        "CINE_FORGE_OPENAI_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.mark.unit
def test_refresh_marks_missing_provider_keys_without_hitting_live_probes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_provider_envs(monkeypatch)
    calls: list[str] = []

    def fake_text_probe(spec, timeout_seconds: float) -> dict[str, str]:
        calls.append(f"text:{spec.probe_id}:{timeout_seconds}")
        return {"model_used": spec.model}

    def fake_image_probe(spec) -> dict[str, str]:
        calls.append(f"image:{spec.probe_id}")
        return {"model_used": spec.model}

    def fake_video_probe(spec, engine_pack_loader) -> dict[str, str]:
        calls.append(f"video:{spec.probe_id}")
        return {"model_used": spec.model}

    service = ProviderCapabilitySmokeService(
        text_probe=fake_text_probe,
        image_probe=fake_image_probe,
        video_probe=fake_video_probe,
    )
    snapshot = service.get_snapshot(refresh=True)

    assert calls == []
    assert snapshot.status == "degraded"
    assert all(check.status == "missing" for check in snapshot.checks)


@pytest.mark.unit
def test_refresh_classifies_live_probe_results(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_provider_envs(monkeypatch)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anth-key")
    monkeypatch.setenv("CINE_FORGE_GEMINI_API_KEY", "google-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")

    def fake_text_probe(spec, timeout_seconds: float) -> dict[str, str]:
        assert timeout_seconds == 30.0
        if spec.provider == "anthropic":
            return {"model_used": spec.model, "request_id": "req-anthropic"}
        if spec.provider == "google":
            raise RuntimeError("request failed: temporarily unavailable")
        return {"model_used": spec.model, "request_id": "req-openai"}

    def fake_image_probe(spec) -> dict[str, str]:
        if spec.provider == "google":
            raise ImageGenerationError("Imagen API returned HTTP 400: API key not valid.")
        return {"model_used": spec.model}

    def fake_video_probe(spec, engine_pack_loader) -> dict[str, str]:
        raise VideoGenerationError("rate limit", retryable=True, status_code=429)

    service = ProviderCapabilitySmokeService(
        text_probe=fake_text_probe,
        image_probe=fake_image_probe,
        video_probe=fake_video_probe,
    )
    snapshot = service.get_snapshot(refresh=True)
    checks = {check.probe_id: check for check in snapshot.checks}

    assert snapshot.status == "degraded"
    assert checks["anthropic_text_default"].status == "ok"
    assert checks["anthropic_text_default"].request_id == "req-anthropic"
    assert checks["google_text_default"].status == "rate_limited"
    assert checks["openai_text_default"].status == "ok"
    assert checks["openai_storyboard_image_default"].status == "ok"
    assert checks["google_design_study_image_default"].status == "auth_failed"
    assert checks["openai_design_study_image_alt"].status == "ok"
    assert checks["google_render_video_default"].status == "rate_limited"


@pytest.mark.unit
def test_get_snapshot_reuses_cached_results_until_refresh_requested(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_provider_envs(monkeypatch)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "anth-key")
    monkeypatch.setenv("GEMINI_API_KEY", "google-key")
    monkeypatch.setenv("OPENAI_API_KEY", "openai-key")
    calls: list[str] = []

    def fake_text_probe(spec, timeout_seconds: float) -> dict[str, str]:
        calls.append(spec.probe_id)
        return {"model_used": spec.model}

    def fake_image_probe(spec) -> dict[str, str]:
        calls.append(spec.probe_id)
        return {"model_used": spec.model}

    def fake_video_probe(spec, engine_pack_loader) -> dict[str, str]:
        calls.append(spec.probe_id)
        return {"model_used": spec.model}

    service = ProviderCapabilitySmokeService(
        text_probe=fake_text_probe,
        image_probe=fake_image_probe,
        video_probe=fake_video_probe,
    )

    first = service.get_snapshot(refresh=True)
    second = service.get_snapshot()

    assert len(calls) == len(first.checks)
    assert first.model_dump(mode="json") == second.model_dump(mode="json")

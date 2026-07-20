from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
DISCOVER_MODELS_PATH = REPO_ROOT / "scripts" / "discover-models.py"


def _load_discover_models_module() -> Any:
    spec = importlib.util.spec_from_file_location("discover_models", DISCOVER_MODELS_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.unit
def test_xai_provider_is_discoverable() -> None:
    module = _load_discover_models_module()

    assert "xai" in module.PROVIDERS
    assert module.PROVIDERS["xai"]["env_key"] == "XAI_API_KEY"
    assert module.classify_tier("grok-4.3") == "sota"
    assert module.classify_tier("grok-4.5") == "sota"


@pytest.mark.unit
def test_query_xai_uses_language_models_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_discover_models_module()
    seen: dict[str, Any] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {
                "models": [
                    {"id": "grok-4.3", "created": 1_776_000_000},
                    {"id": "grok-imagine-video", "created": 1_776_000_000},
                    {"id": "grok-code-fast-1", "created": 1_776_000_000},
                ]
            }

    def fake_get(url: str, *, headers: dict[str, str], timeout: int) -> FakeResponse:
        seen["url"] = url
        seen["headers"] = headers
        seen["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(module.httpx, "get", fake_get)

    models = module.query_xai("xai-test-key")

    assert seen["url"] == "https://api.x.ai/v1/language-models"
    assert seen["headers"] == {"Authorization": "Bearer xai-test-key"}
    assert seen["timeout"] == 15
    assert [model["id"] for model in models] == ["grok-4.3"]
    assert models[0]["provider"] == "xai"
    assert models[0]["tier"] == "sota"


@pytest.mark.unit
def test_grok_registry_matching_handles_human_label() -> None:
    module = _load_discover_models_module()

    assert module._matches_registry(
        "grok-4.3",
        "grok-4.3",
        {"Grok 4.3"},
    )


@pytest.mark.unit
def test_grok_registry_matching_does_not_cross_model_families() -> None:
    module = _load_discover_models_module()

    assert not module._matches_registry(
        "grok-4.5",
        "grok-4.5",
        {"Haiku 4.5", "Claude Opus 4.5"},
    )


@pytest.mark.unit
def test_moonshot_provider_is_discoverable() -> None:
    module = _load_discover_models_module()

    assert "moonshot" in module.PROVIDERS
    assert module.PROVIDERS["moonshot"]["env_key"] == "MOONSHOT_API_KEY"
    assert module.classify_tier("kimi-k2.6") == "sota"
    assert module.classify_tier("kimi-k2-thinking") == "reasoning"


@pytest.mark.unit
def test_query_moonshot_uses_models_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_discover_models_module()
    seen: dict[str, Any] = {}

    class FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, Any]:
            return {
                "data": [
                    {
                        "id": "moonshot-v1-8k",
                        "context_length": 8192,
                    },
                    {
                        "id": "kimi-k2.6",
                        "context_length": 262144,
                        "supports_image_in": True,
                        "supports_video_in": True,
                        "supports_reasoning": True,
                    },
                ]
            }

    def fake_get(url: str, *, headers: dict[str, str], timeout: int) -> FakeResponse:
        seen["url"] = url
        seen["headers"] = headers
        seen["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(module.httpx, "get", fake_get)

    models = module.query_moonshot("moonshot-test-key")

    assert seen["url"] == "https://api.moonshot.ai/v1/models"
    assert seen["headers"] == {"Authorization": "Bearer moonshot-test-key"}
    assert seen["timeout"] == 15
    assert [model["id"] for model in models] == ["moonshot-v1-8k", "kimi-k2.6"]
    assert models[1]["provider"] == "moonshot"
    assert models[1]["tier"] == "sota"
    assert models[1]["input_token_limit"] == 262144

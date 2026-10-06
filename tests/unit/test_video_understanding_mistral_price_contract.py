from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "benchmarks/providers"))
provider = importlib.import_module("video_understanding_provider")


@pytest.mark.unit
@pytest.mark.parametrize("invalid", [True, -1, "0.68"])
def test_invalid_price_bound_never_dispatches(monkeypatch, invalid):
    def forbidden(*args, **kwargs):
        pytest.fail("Invalid price bound reached paid transport")

    monkeypatch.setattr(provider, "_request_json", forbidden)
    with pytest.raises(RuntimeError, match="max_price"):
        provider._call_openrouter_strict(
            model="mistralai/mistral-large-4-0", user_text="Inspect frames",
            frames=[{"mime_type": "image/jpeg", "base64": "abc"}] * 5,
            max_tokens=4096, upstream_provider="Mistral",
            raw_output_path=ROOT / "output/.price-test.json", timeout_seconds=60,
            max_price={"prompt": invalid, "completion": 2.09},
        )


@pytest.mark.unit
def test_mistral_price_bound_and_all_images_reach_native_transport(monkeypatch):
    def capture(url, **kwargs):
        body = kwargs["body"]
        assert body["model"] == "mistralai/mistral-large-4-0"
        assert body["provider"] == {
            "order": ["Mistral"], "allow_fallbacks": False,
            "require_parameters": True, "max_price": {"prompt": .68, "completion": 2.09},
        }
        assert body["response_format"]["json_schema"]["strict"] is True
        assert body["max_completion_tokens"] == 4096 and "reasoning" not in body
        assert sum(x["type"] == "image_url" for x in body["messages"][0]["content"]) == 5
        assert kwargs["raw_output_path"] == ROOT / "output/.price-test.json"
        raise RuntimeError("Captured without inference")

    monkeypatch.setattr(provider, "_require_env", lambda _: "test-key")
    monkeypatch.setattr(provider, "_request_json", capture)
    with pytest.raises(RuntimeError, match="Captured without inference"):
        provider._call_openrouter_strict(
            model="mistralai/mistral-large-4-0", user_text="Inspect frames",
            frames=[{"mime_type": "image/jpeg", "base64": "abc"}] * 5,
            max_tokens=4096, upstream_provider="Mistral",
            raw_output_path=ROOT / "output/.price-test.json", timeout_seconds=60,
            max_price={"prompt": .68, "completion": 2.09},
        )

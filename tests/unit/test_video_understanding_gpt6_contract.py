"""Offline contract checks before paid GPT-6 ordered-frame calls."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[2]
PROVIDER = ROOT / "benchmarks/providers/video_understanding_provider.py"
sys.path.insert(0, str(PROVIDER.parent))
spec = importlib.util.spec_from_file_location("video_gpt6_contract", PROVIDER)
provider = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provider)


def _output() -> dict:
    return {
        "clip_id": "vfp_active_001", "summary": "A blue room is visible.",
        "tone_tags": [], "emotion_tags": [], "color_tags": [],
        "camera_tags": [], "motion_tags": [], "continuity_status": "ambiguous",
        "continuity_notes": [], "audio_tags": [], "audio_notes": [],
        "evidence": [
            {"frame_index": 0, "cue": "blue room"},
            {"frame_index": 4, "cue": "two figures"},
        ],
        "overall_confidence": 0.5,
    }


def test_direct_responses_sends_five_images_strict_schema_and_store_false(tmp_path, monkeypatch):
    captured = {}

    def fake_request(url, *, headers, body, raw_output_path):
        captured.update(url=url, body=body)
        return {
            "id": "resp_test", "model": "gpt-6-sol", "status": "completed",
            "service_tier": "default", "error": None,
            "output": [{"type": "message", "status": "completed", "content": [
                {"type": "output_text", "text": json.dumps(_output())}
            ]}],
            "usage": {
                "input_tokens": 4500, "output_tokens": 300, "total_tokens": 4800,
                "input_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 1000},
                "output_tokens_details": {"reasoning_tokens": 100},
            },
        }

    monkeypatch.setattr(provider, "_request_json", fake_request)
    monkeypatch.setattr(provider, "_require_env", lambda _: "test-only")
    monkeypatch.setattr(provider, "REPO_ROOT", tmp_path)
    raw_path = tmp_path / "output/raw.json"
    result = provider._vision.call_openai_responses_strict(
        vars(provider), model="gpt-6-sol", user_text="synthetic prompt",
        frames=[{"mime_type": "image/jpeg", "base64": "synthetic"}] * 5,
        max_tokens=1400, reasoning_effort="low", raw_output_path=raw_path,
    )
    assert captured["url"] == provider.OPENAI_RESPONSES_URL
    body = captured["body"]
    assert body["store"] is False
    assert body["service_tier"] == "default"
    assert body["reasoning"] == {"effort": "low"}
    assert body["text"]["format"]["strict"] is True
    assert len([x for x in body["input"][0]["content"] if x["type"] == "input_image"]) == 5
    assert raw_path.exists() and json.loads(raw_path.read_text())["id"] == "resp_test"
    assert result["reported_cost_usd"] == pytest.approx(0.0125)


def test_incomplete_response_is_retained_and_rejected(tmp_path, monkeypatch):
    monkeypatch.setattr(provider, "_require_env", lambda _: "test-only")
    monkeypatch.setattr(provider, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(provider, "_request_json", lambda *a, **kw: {
        "id": "resp_partial", "model": "gpt-6-luna", "status": "incomplete",
        "incomplete_details": {"reason": "max_output_tokens"}, "output": [],
    })
    raw_path = tmp_path / "output/raw.json"
    with pytest.raises(RuntimeError, match="did not complete"):
        provider._vision.call_openai_responses_strict(
            vars(provider), model="gpt-6-luna", user_text="synthetic prompt",
            frames=[{"mime_type": "image/jpeg", "base64": "synthetic"}] * 5,
            max_tokens=1400, reasoning_effort="low", raw_output_path=raw_path,
        )
    assert json.loads(raw_path.read_text())["id"] == "resp_partial"

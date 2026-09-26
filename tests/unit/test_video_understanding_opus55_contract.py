"""Offline contract checks for the direct Opus 5.5 frame evaluation."""

import importlib.util
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


REPO_ROOT = Path(__file__).resolve().parents[2]
PROVIDER_PATH = REPO_ROOT / "benchmarks/providers/video_understanding_provider.py"
sys.path.insert(0, str(PROVIDER_PATH.parent))
spec = importlib.util.spec_from_file_location(
    "video_understanding_provider_opus_test", PROVIDER_PATH
)
provider = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provider)


def test_opus_schema_keeps_prompt_required_shape_and_local_limits():
    schema = provider._anthropic_video_schema()
    properties = schema["properties"]
    assert schema["required"] == list(properties)
    assert schema["additionalProperties"] is False
    assert set(properties) == {
        "clip_id",
        "summary",
        "tone_tags",
        "emotion_tags",
        "color_tags",
        "camera_tags",
        "motion_tags",
        "continuity_status",
        "continuity_notes",
        "audio_tags",
        "audio_notes",
        "evidence",
        "overall_confidence",
    }
    assert properties["evidence"]["items"]["required"] == ["frame_index", "cue"]
    assert (
        "maximum=4" in properties["evidence"]["items"]["properties"]["frame_index"]["description"]
    )
    assert "minimum=0.0" in properties["overall_confidence"]["description"]


def test_opus_http_error_retains_complete_request_before_raise(tmp_path, monkeypatch):
    raw_path = tmp_path / "raw.json"
    monkeypatch.setattr(provider, "_require_env", lambda _: "test-only")
    monkeypatch.setattr(
        provider,
        "_request_json",
        lambda *a, **kw: (_ for _ in ()).throw(
            provider.ProviderHTTPError(
                url="https://api.anthropic.com/v1/messages",
                status_code=400,
                body='{"error":"invalid"}',
            )
        ),
    )
    frames = [{"mime_type": "image/jpeg", "base64": "synthetic"}] * 5
    with pytest.raises(provider.ProviderHTTPError):
        provider._call_anthropic(
            model="claude-opus-5-5",
            user_text="synthetic prompt",
            frames=frames,
            max_tokens=1400,
            temperature=None,
            effort="medium",
            raw_output_path=raw_path,
        )
    saved = __import__("json").loads(raw_path.read_text())
    assert saved["response_error"]["status"] == 400
    assert saved["request"]["output_config"]["effort"] == "medium"
    assert (
        len(
            [part for part in saved["request"]["messages"][0]["content"] if part["type"] == "image"]
        )
        == 5
    )
    assert "test-only" not in raw_path.read_text()


def test_opus_success_retains_envelope_usage_and_cost(tmp_path, monkeypatch):
    import json

    raw_path = tmp_path / "raw.json"
    monkeypatch.setattr(provider, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(provider, "_require_env", lambda _: "test-only")
    output = {
        "clip_id": "vfp_active_001",
        "summary": "A room is visible.",
        "tone_tags": [],
        "emotion_tags": [],
        "color_tags": [],
        "camera_tags": [],
        "motion_tags": [],
        "continuity_status": "ambiguous",
        "continuity_notes": [],
        "audio_tags": [],
        "audio_notes": [],
        "evidence": [{"frame_index": 0, "cue": "A room"}, {"frame_index": 4, "cue": "A window"}],
        "overall_confidence": 0.5,
    }
    envelope = {
        "id": "msg_test",
        "model": "claude-opus-5-5",
        "stop_reason": "end_turn",
        "content": [{"type": "text", "text": json.dumps(output)}],
        "usage": {
            "input_tokens": 100,
            "output_tokens": 200,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
        },
    }
    monkeypatch.setattr(provider, "_request_json", lambda *a, **kw: envelope)
    result = provider._call_anthropic(
        model="claude-opus-5-5",
        user_text="synthetic prompt",
        frames=[{"mime_type": "image/jpeg", "base64": "synthetic"}] * 5,
        max_tokens=1400,
        temperature=None,
        effort="medium",
        raw_output_path=raw_path,
    )
    assert result["reported_cost_usd"] == 0.0044
    assert result["raw"]["raw_envelope_path"] == "raw.json"
    assert json.loads(raw_path.read_text()) == envelope

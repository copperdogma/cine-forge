"""Exact native Sonnet 5.5 transport and failure quarantine."""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

PROVIDER = (
    Path(__file__).resolve().parents[2] / "benchmarks/providers/video_understanding_provider.py"
)
sys.path.insert(0, str(PROVIDER.parent))
spec = importlib.util.spec_from_file_location("video_sonnet55_contract", PROVIDER)
provider = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provider)

pytestmark = pytest.mark.unit


def test_sonnet_adaptive_strict_request_and_complete_envelope(tmp_path, monkeypatch):
    captured = {}
    output = {
        "clip_id": "vfp_active_001",
        "summary": "Two blue figures grow across samples.",
        "tone_tags": [],
        "emotion_tags": [],
        "color_tags": ["navy"],
        "camera_tags": [],
        "motion_tags": ["measured"],
        "continuity_status": "intact",
        "continuity_notes": [],
        "audio_tags": [],
        "audio_notes": [],
        "evidence": [
            {"frame_index": 0, "cue": "blue figures"},
            {"frame_index": 4, "cue": "larger bodies"},
        ],
        "overall_confidence": 0.8,
    }
    envelope = {
        "id": "msg_test_sonnet",
        "model": "claude-sonnet-5-5",
        "stop_reason": "end_turn",
        "content": [
            {"type": "thinking", "thinking": "private internal"},
            {"type": "text", "text": json.dumps(output)},
        ],
        "usage": {
            "input_tokens": 100,
            "output_tokens": 200,
            "cache_creation_input_tokens": 0,
            "cache_read_input_tokens": 0,
        },
    }

    def fake_request(url, *, headers, body):
        captured.update(body)
        return envelope

    monkeypatch.setattr(provider, "_request_json", fake_request)
    monkeypatch.setattr(provider, "_require_env", lambda _: "test-only")
    monkeypatch.setattr(provider, "REPO_ROOT", tmp_path)
    result = provider._call_anthropic(
        model="claude-sonnet-5-5",
        user_text="frozen prompt",
        frames=[{"mime_type": "image/jpeg", "base64": "synthetic"}] * 5,
        max_tokens=4096,
        temperature=None,
        effort="medium",
        raw_output_path=tmp_path / "raw.json",
    )
    assert captured["thinking"] == {"type": "adaptive"}
    assert captured["output_config"]["effort"] == "medium"
    assert captured["output_config"]["format"]["type"] == "json_schema"
    assert "temperature" not in captured
    assert len([x for x in captured["messages"][0]["content"] if x["type"] == "image"]) == 5
    assert result["reported_cost_usd"] == pytest.approx(0.0022)
    assert json.loads((tmp_path / "raw.json").read_text()) == envelope


@pytest.mark.parametrize("terminal", ["max_tokens", "refusal"])
def test_sonnet_terminal_failure_retained_and_rejected(tmp_path, monkeypatch, terminal):
    monkeypatch.setattr(provider, "_require_env", lambda _: "test-only")
    monkeypatch.setattr(
        provider,
        "_request_json",
        lambda *a, **kw: {
            "id": "msg_bad",
            "model": "claude-sonnet-5-5",
            "stop_reason": terminal,
            "content": [],
        },
    )
    path = tmp_path / "raw.json"
    with pytest.raises(RuntimeError, match="did not finish"):
        provider._call_anthropic(
            model="claude-sonnet-5-5",
            user_text="frozen prompt",
            frames=[{"mime_type": "image/jpeg", "base64": "synthetic"}] * 5,
            max_tokens=4096,
            temperature=None,
            effort="medium",
            raw_output_path=path,
        )
    assert json.loads(path.read_text())["stop_reason"] == terminal

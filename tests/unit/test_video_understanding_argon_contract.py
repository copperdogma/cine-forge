"""Fail-closed native Argon contract and raw-envelope custody checks."""

import copy
import importlib.util
import json
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "benchmarks/providers"))
spec = importlib.util.spec_from_file_location(
    "argon_contract_provider", ROOT / "benchmarks/providers/video_understanding_provider.py"
)
provider = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provider)
from video_understanding_provider_argon import call_argon  # noqa: E402


def invoke(tmp_path, monkeypatch, envelope):
    captured = {}
    monkeypatch.setattr(provider, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(provider, "_require_env", lambda _: "synthetic-test-key")

    def fake_request(url, **kwargs):
        captured.update(url=url, **kwargs)
        return envelope

    monkeypatch.setattr(provider, "_request_json", fake_request)
    request = {
        "config": {"reasoning_effort": "medium", "raw_output_dir": "output/test"},
        "model": "gemini-4-argon",
        "max_tokens": 32768,
        "evaluation_id": "vfp_active_001",
        "user_text": "synthetic",
        "packet": {"frames": [{"mime_type": "image/jpeg", "base64": "test"}] * 5},
    }
    return call_argon(vars(provider), request), captured


def valid_envelope():
    saved = ROOT / "docs/evals/evidence/story-226-argon20261013/native/argon"
    return json.loads((saved / "vfp_active_001-raw-envelope.json").read_text())


def test_exact_wire_shape_and_all_billable_thinking(tmp_path, monkeypatch):
    result, captured = invoke(tmp_path, monkeypatch, valid_envelope())
    assert "key=" not in captured["url"]
    body = captured["body"]
    config = body["generationConfig"]
    assert config["thinkingConfig"] == {"thinkingLevel": "medium"}
    assert config["maxOutputTokens"] == 32768
    assert config["responseSchema"]["required"]
    assert config["responseMimeType"] == "application/json"
    assert not {"temperature", "topP", "topK", "cachedContent"} & config.keys()
    parts = body["contents"][0]["parts"]
    assert len([p for p in parts if "inline_data" in p]) == 5
    assert result["reported_cost_usd"] == pytest.approx(0.020128)
    assert result["token_usage"]["billed_completion"] == 506


@pytest.mark.parametrize("fault", ["truncated", "wrong_model", "bad_usage", "bad_schema"])
def test_invalid_envelope_retained_before_rejection(tmp_path, monkeypatch, fault):
    envelope = copy.deepcopy(valid_envelope())
    if fault == "truncated":
        envelope["candidates"][0]["finishReason"] = "MAX_TOKENS"
    elif fault == "wrong_model":
        envelope["modelVersion"] = "gemini-other"
    elif fault == "bad_usage":
        envelope["usageMetadata"]["totalTokenCount"] += 1
    else:
        envelope["candidates"][0]["content"]["parts"] = [{"text": "{}"}]
    with pytest.raises((RuntimeError, ValueError)):
        invoke(tmp_path, monkeypatch, envelope)
    raw = tmp_path / "output/test/vfp_active_001-raw-envelope.json"
    assert json.loads(raw.read_text()) == envelope

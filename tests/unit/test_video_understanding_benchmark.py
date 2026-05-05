from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_PROVIDER_ROOT = REPO_ROOT / "benchmarks" / "providers"
BENCHMARK_SCORER_ROOT = REPO_ROOT / "benchmarks" / "scorers"
BENCHMARK_SCRIPT_ROOT = REPO_ROOT / "benchmarks" / "scripts"
for path in (BENCHMARK_PROVIDER_ROOT, BENCHMARK_SCORER_ROOT, BENCHMARK_SCRIPT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

provider = importlib.import_module("video_understanding_provider")
scorer = importlib.import_module("video_understanding_scorer")
report = importlib.import_module("video_understanding_report")


@pytest.mark.unit
def test_provider_builds_clip_brief_from_meta() -> None:
    meta = {
        "clip_id": "dialogue_confession_push_in",
        "title": "Dialogue confession push-in",
        "source_type": "synthetic_previz",
        "duration_seconds": 4.0,
        "resolution": "640x360",
        "has_audio": True,
        "tags": ["dialogue", "quiet_emotion"],
        "transcript": "I should have told you before the train left.",
        "audio_description": "Soft piano under a single confession line.",
    }
    user_text = provider._build_user_text(
        "Return JSON.",
        meta,
        prompt_version="video-understanding-v1",
    )
    assert "clip_id: dialogue_confession_push_in" in user_text
    assert "transcript: I should have told you before the train left." in user_text
    assert "audio_description: Soft piano under a single confession line." in user_text


@pytest.mark.unit
def test_provider_payload_builders_include_all_frames() -> None:
    frames = [
        {"mime_type": "image/jpeg", "base64": "abc"},
        {"mime_type": "image/jpeg", "base64": "def"},
    ]
    openai_payload = provider._build_openai_payload(
        model="gpt-4.1",
        user_text="Inspect this clip.",
        frames=frames,
        max_tokens=1200,
        temperature=0.0,
    )
    anthropic_payload = provider._build_anthropic_payload(
        model="claude-sonnet-4-6",
        user_text="Inspect this clip.",
        frames=frames,
        max_tokens=1200,
        temperature=0.0,
    )
    gemini_payload = provider._build_gemini_payload(
        user_text="Inspect this clip.",
        frames=frames,
        max_tokens=1200,
        temperature=0.0,
    )

    assert len(openai_payload["messages"][0]["content"]) == 3
    assert len(anthropic_payload["messages"][0]["content"]) == 3
    assert len(gemini_payload["contents"][0]["parts"]) == 3


@pytest.mark.unit
def test_provider_xai_call_uses_openai_compatible_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}

    def fake_require_env(name: str) -> str:
        seen["env"] = name
        return "xai-test-key"

    def fake_request_json(
        url: str,
        *,
        headers: dict[str, str],
        body: dict[str, object],
    ) -> dict[str, object]:
        seen["url"] = url
        seen["headers"] = headers
        seen["body"] = body
        return {
            "choices": [{"message": {"content": '{"clip_id":"clip_1"}'}}],
            "usage": {"prompt_tokens": 80, "completion_tokens": 12, "total_tokens": 92},
        }

    monkeypatch.setattr(provider, "_require_env", fake_require_env)
    monkeypatch.setattr(provider, "_request_json", fake_request_json)

    result = provider._call_xai(
        model="grok-4.3",
        user_text="Inspect this clip.",
        frames=[{"mime_type": "image/jpeg", "base64": "abc"}],
        max_tokens=1200,
        temperature=0.0,
    )

    assert seen["env"] == "XAI_API_KEY"
    assert seen["url"] == provider.XAI_CHAT_URL
    assert seen["headers"]["Authorization"] == "Bearer xai-test-key"
    assert seen["body"]["model"] == "grok-4.3"
    assert result["output"] == '{"clip_id":"clip_1"}'
    assert result["token_usage"] == {"prompt": 80, "completion": 12, "total": 92}


@pytest.mark.unit
def test_provider_resolves_candidate_variant_clip_dir(tmp_path: Path) -> None:
    clip_dir = provider._resolve_clip_dir(
        base_path=tmp_path,
        config={
            "clip_root": "../previz_usefulness",
            "candidate_variant": "annotated_symbolic",
        },
        vars_data={"clip_id": "dialogue_confession_push_in"},
    )
    expected = (
        tmp_path
        / "../previz_usefulness"
        / "annotated_symbolic"
        / "dialogue_confession_push_in"
    ).resolve()
    assert clip_dir == expected


@pytest.mark.unit
def test_scorer_parses_fenced_json() -> None:
    prediction = scorer.parse_prediction(
        """```json
        {
          "clip_id": "clip_1",
          "summary": "Blue confession push-in.",
          "tone_tags": ["regretful"],
          "emotion_tags": ["hesitation"],
          "color_tags": ["teal"],
          "camera_tags": ["slow_push_in"],
          "motion_tags": ["measured"],
          "continuity_status": "intact",
          "continuity_notes": [],
          "audio_tags": ["speech"],
          "audio_notes": [],
          "evidence": [{"timestamp_seconds": 1.2, "cue": "Camera pushes toward the speaker."}],
          "overall_confidence": 0.7
        }
        ```"""
    )
    assert prediction.clip_id == "clip_1"
    assert prediction.camera_tags == ["slow_push_in"]


@pytest.mark.unit
def test_scorer_rewards_matching_prediction(tmp_path: Path) -> None:
    target_path = tmp_path / "target.json"
    target_path.write_text(
        json.dumps(
            {
                "clip_id": "clip_1",
                "title": "Clip 1",
                "source_type": "synthetic_previz",
                "source_description": "Synthetic",
                "rights": "Owned",
                "duration_seconds": 4.0,
                "resolution": "640x360",
                "has_audio": True,
                "transcript": "Hold position.",
                "audio_description": "Radio dispatch over a pulsing alarm bed.",
                "summary_reference": "Urgent command under red pulsing light.",
                "required_keywords": ["urgent", "red", "command"],
                "tone_tags": ["urgent", "tense"],
                "emotion_tags": ["panic"],
                "color_tags": ["red"],
                "camera_tags": ["whip_pan"],
                "motion_tags": ["escalating"],
                "continuity_status": "intact",
                "continuity_notes": ["The red bag stays with the runner."],
                "audio_tags": ["alarm", "radio", "speech"],
                "clip_tags": ["action"],
                "anchor_subset": True,
                "weights": {
                    "summary": 0.18,
                    "tone": 0.14,
                    "emotion": 0.12,
                    "color": 0.10,
                    "camera": 0.12,
                    "motion": 0.10,
                    "continuity": 0.12,
                    "audio": 0.08,
                    "evidence": 0.04,
                },
            }
        )
    )
    output = {
        "clip_id": "clip_1",
        "summary": "An urgent red command scene with a runner under alarm lights.",
        "tone_tags": ["urgent", "tense"],
        "emotion_tags": ["panic"],
        "color_tags": ["red"],
        "camera_tags": ["whip_pan"],
        "motion_tags": ["escalating"],
        "continuity_status": "intact",
        "continuity_notes": ["The red bag stays with the runner throughout the cut."],
        "audio_tags": ["alarm", "radio", "speech"],
        "audio_notes": ["A radio command rides over the alarm bed."],
        "evidence": [
            {"timestamp_seconds": 0.8, "cue": "Red pulse floods the hallway."},
            {
                "timestamp_seconds": 2.1,
                "cue": "The bag remains with the runner during the whip pan.",
            },
        ],
        "overall_confidence": 0.86,
    }

    score = scorer.score_output_against_target(
        output=output,
        target_path=target_path,
        model_label="Fixture",
        prompt_version="video-understanding-v1",
    )

    assert score.overall_score > 0.8
    assert score.hard_constraints_passed is True


@pytest.mark.unit
def test_report_summary_tolerates_parse_failures(tmp_path: Path) -> None:
    target_path = tmp_path / "target.json"
    target_path.write_text(
        json.dumps(
            {
                "clip_id": "clip_1",
                "title": "Clip 1",
                "source_type": "synthetic_previz",
                "source_description": "Synthetic",
                "rights": "Owned",
                "duration_seconds": 4.0,
                "resolution": "640x360",
                "has_audio": True,
                "transcript": "Hold position.",
                "audio_description": "Radio dispatch over a pulsing alarm bed.",
                "summary_reference": "Urgent command under red pulsing light.",
                "required_keywords": ["urgent", "red", "command"],
                "tone_tags": ["urgent", "tense"],
                "emotion_tags": ["panic"],
                "color_tags": ["red"],
                "camera_tags": ["whip_pan"],
                "motion_tags": ["escalating"],
                "continuity_status": "intact",
                "continuity_notes": ["The red bag stays with the runner."],
                "audio_tags": ["alarm", "radio", "speech"],
                "clip_tags": ["action"],
                "anchor_subset": True,
                "weights": {
                    "summary": 0.18,
                    "tone": 0.14,
                    "emotion": 0.12,
                    "color": 0.10,
                    "camera": 0.12,
                    "motion": 0.10,
                    "continuity": 0.12,
                    "audio": 0.08,
                    "evidence": 0.04,
                },
            }
        )
    )

    summary = report.build_summary(
        [
            {
                "provider": {"label": "Gemini 2.5 Flash"},
                "vars": {"target_path": str(target_path)},
                "response": {
                    "output": "not json at all",
                    "metadata": {"prompt_version": "video-understanding-v1"},
                },
                "gradingResult": {
                    "componentResults": [
                        {
                            "assertion": {"type": "python"},
                            "score": 0.0,
                            "pass": False,
                            "reason": "Scorer parse failure: Could not parse model output as JSON",
                        },
                        {
                            "assertion": {"type": "llm-rubric"},
                            "score": 0.4,
                            "pass": False,
                            "reason": "Shallow summary and missing audio.",
                        },
                    ]
                },
                "latencyMs": 1234,
                "cost": 0.0015,
            }
        ]
    )

    row = summary["models"][0]
    assert row["model"] == "Gemini 2.5 Flash"
    assert row["python_overall"] == 0.0
    assert row["rubric_overall"] == 0.4
    assert row["overall"] == 0.2
    assert row["dimension_scores"]["summary"] == 0.0
    assert row["dimension_scores"]["hard_constraints"] == 0.0

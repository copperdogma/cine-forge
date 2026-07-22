from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from cine_forge.ai.errors import LLMCallError

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
def test_provider_builds_answer_neutral_frame_packet_brief() -> None:
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
        evaluation_id="frame_case_001",
        prompt_version="video-understanding-v1",
        frame_count=5,
        sample_times=[0.0, 1.0, 2.0, 3.0, 3.875],
    )
    assert "clip_id: frame_case_001" in user_text
    assert "dialogue_confession_push_in" not in user_text
    assert "frame_count: 5" in user_text
    assert "ordered_frame_indices: [0, 1, 2, 3, 4]" in user_text
    assert "ordered_sample_times_seconds: [0, 1, 2, 3, 3.875]" in user_text
    assert "audio_available_to_model: false" in user_text
    assert "Dialogue confession push-in" not in user_text
    assert "I should have told you" not in user_text
    assert "Soft piano" not in user_text
    assert "quiet_emotion" not in user_text


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

    assert len(openai_payload["messages"][0]["content"]) == 5
    assert len(anthropic_payload["messages"][0]["content"]) == 5
    assert len(gemini_payload["contents"][0]["parts"]) == 5
    assert openai_payload["messages"][0]["content"][1]["text"] == "frame_index: 0"
    assert anthropic_payload["messages"][0]["content"][3]["text"] == "frame_index: 1"
    assert gemini_payload["contents"][0]["parts"][3]["text"] == "frame_index: 1"
    assert "temperature" not in gemini_payload["generationConfig"]


@pytest.mark.unit
def test_gemini_cost_includes_hidden_thinking_but_keeps_visible_completion() -> None:
    token_usage = {"prompt": 100, "completion": 10, "total": 1110}

    billed_completion = provider._completion_tokens_for_cost("google", token_usage)

    assert billed_completion == 1010
    assert token_usage["completion"] == 10
    assert provider.estimate_cost_usd(
        "gemini-3.5-flash-lite",
        token_usage["prompt"],
        billed_completion,
    ) == pytest.approx(0.002555)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("token_usage", "message"),
    [
        ({}, "prompt_tokens must be a nonnegative integer"),
        (
            {"prompt": -1, "completion": 0},
            "prompt_tokens must be a nonnegative integer",
        ),
        (
            {"prompt": True, "completion": 0},
            "prompt_tokens must be a nonnegative integer",
        ),
        (
            {"prompt": 1, "completion": 2.5},
            "visible_completion_tokens must be a nonnegative integer",
        ),
        (
            {"prompt": 100, "completion": 10, "total": 109},
            "total_tokens must be at least",
        ),
        (
            {
                "prompt": 100,
                "completion": 10,
                "total": 1110,
                "billed_completion": 10,
            },
            "billed_completion_tokens does not match",
        ),
    ],
)
def test_gemini_cost_rejects_malformed_or_inconsistent_usage(
    token_usage: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        provider._completion_tokens_for_cost("google", token_usage)


@pytest.mark.unit
def test_gemini_transport_rejects_impossible_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(provider, "_require_env", lambda _: "test-key")
    monkeypatch.setattr(
        provider,
        "_request_json",
        lambda *args, **kwargs: {
            "responseId": "gemini-video-reasoning",
            "candidates": [{"content": {"parts": [{"text": "{}"}]}}],
            "modelVersion": "gemini-3.6-flash",
            "usageMetadata": {
                "promptTokenCount": 100,
                "candidatesTokenCount": 10,
                "totalTokenCount": 109,
            },
        },
    )

    with pytest.raises(ValueError, match="total_tokens must be at least"):
        provider._call_gemini(
            model="gemini-3.6-flash",
            user_text="Inspect.",
            frames=[],
            max_tokens=65_536,
        )


@pytest.mark.unit
def test_gemini_transport_bills_reasoning_when_total_is_absent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(provider, "_require_env", lambda _: "test-key")
    monkeypatch.setattr(
        provider,
        "_request_json",
        lambda *args, **kwargs: {
            "responseId": "gemini-video-reasoning",
            "candidates": [{"content": {"parts": [{"text": "{}"}]}}],
            "modelVersion": "gemini-3.6-flash",
            "usageMetadata": {
                "promptTokenCount": 100,
                "candidatesTokenCount": 10,
                "thoughtsTokenCount": 1000,
            },
        },
    )

    result = provider._call_gemini(
        model="gemini-3.6-flash",
        user_text="Inspect.",
        frames=[],
        max_tokens=65_536,
    )

    assert result["token_usage"] == {
        "prompt": 100,
        "completion": 10,
        "total": 1110,
        "billed_completion": 1010,
        "reasoning_completion": 1000,
    }
    assert result["raw"] == {
        "responseId": "gemini-video-reasoning",
        "modelVersion": "gemini-3.6-flash",
        "usageMetadata": {
            "promptTokenCount": 100,
            "candidatesTokenCount": 10,
            "thoughtsTokenCount": 1000,
        }
    }


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
            "id": "xai-video-1",
            "choices": [{"message": {"content": '{"clip_id":"clip_1"}'}}],
            "model": "grok-4.3",
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
    assert result["raw"] == {
        "id": "xai-video-1",
        "model": "grok-4.3",
        "usage": {"prompt_tokens": 80, "completion_tokens": 12, "total_tokens": 92},
    }


@pytest.mark.unit
@pytest.mark.parametrize("missing", ["responseId", "modelVersion"])
def test_gemini_video_transport_requires_returned_call_and_model_identity(
    monkeypatch: pytest.MonkeyPatch,
    missing: str,
) -> None:
    monkeypatch.setattr(provider, "_require_env", lambda _: "test-key")
    response = {
        "responseId": "gemini-video-identity",
        "modelVersion": "gemini-3.6-flash",
        "candidates": [{"content": {"parts": [{"text": "{}"}]}}],
        "usageMetadata": {"promptTokenCount": 1, "candidatesTokenCount": 1},
    }
    response.pop(missing)
    monkeypatch.setattr(provider, "_request_json", lambda *_a, **_k: response)

    with pytest.raises(LLMCallError, match="must be a non-empty string"):
        provider._call_gemini(
            model="gemini-3.6-flash",
            user_text="Inspect.",
            frames=[],
            max_tokens=65_536,
        )


@pytest.mark.unit
def test_gemini_video_transport_rejects_returned_model_substitution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(provider, "_require_env", lambda _: "test-key")
    monkeypatch.setattr(
        provider,
        "_request_json",
        lambda *_a, **_k: {
            "responseId": "gemini-video-substitute",
            "modelVersion": "gemini-3.5-flash-lite",
            "candidates": [{"content": {"parts": [{"text": "{}"}]}}],
            "usageMetadata": {"promptTokenCount": 1, "candidatesTokenCount": 1},
        },
    )

    with pytest.raises(LLMCallError, match="does not match requested model"):
        provider._call_gemini(
            model="gemini-3.6-flash",
            user_text="Inspect.",
            frames=[],
            max_tokens=65_536,
        )


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
@pytest.mark.parametrize(
    "wrapped",
    [
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
          "evidence": [{"frame_index": 1, "cue": "Camera pushes toward the speaker."}],
          "overall_confidence": 0.7
        }
        ```""",
        """Here is the result:
        {
          "clip_id": "clip_1"
        }""",
    ],
)
def test_scorer_rejects_json_wrapped_in_fences_or_prose(wrapped: str) -> None:
    with pytest.raises(ValueError, match="strict JSON object"):
        scorer.parse_prediction(wrapped)


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
        "audio_tags": [],
        "audio_notes": [],
        "evidence": [
            {"frame_index": 0, "cue": "Red pulse floods the hallway."},
            {
                "frame_index": 2,
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
    assert row["data_complete"] is False
    assert summary["recommendation"]["decision"] == "retest"


@pytest.mark.unit
def test_report_regrades_python_score_with_current_scorer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, object] = {}
    current_score = SimpleNamespace(
        overall_score=0.25,
        dimensions=[SimpleNamespace(dimension="summary", score=0.25)],
    )

    def current_scorer(**kwargs):
        seen.update(kwargs)
        return current_score

    monkeypatch.setattr(
        report,
        "score_output_against_target",
        current_scorer,
    )
    entry = {
        "provider": {"label": "Model A"},
        "vars": {
            "clip_id": "case_a",
            "evaluation_id": "opaque_001",
            "target_path": "target.json",
        },
        "response": {"output": "{}", "metadata": {}},
        "gradingResult": {
            "componentResults": [
                {"assertion": {"type": "python"}, "score": 1.0, "pass": True},
                {
                    "assertion": {"type": "llm-rubric"},
                    "score": 0.75,
                    "pass": True,
                },
            ]
        },
        "latencyMs": 100,
        "cost": 0.01,
    }

    summary = report.build_summary([entry], expected_cases={"case_a"})

    row = summary["models"][0]
    assert row["python_overall"] == 0.25
    assert row["overall"] == 0.5
    assert row["data_complete"] is True
    assert seen["expected_clip_id"] == "opaque_001"
    assert summary["recommendation"]["decision"] == "retest"


@pytest.mark.unit
def test_report_rejects_duplicate_or_missing_cases(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current_score = SimpleNamespace(
        overall_score=0.9,
        dimensions=[SimpleNamespace(dimension="summary", score=0.9)],
    )
    monkeypatch.setattr(
        report,
        "score_output_against_target",
        lambda **_kwargs: current_score,
    )

    def entry(case_id: str) -> dict:
        return {
            "provider": {"label": "Model A"},
            "vars": {"clip_id": case_id, "target_path": "target.json"},
            "response": {"output": "{}", "metadata": {}},
            "gradingResult": {
                "componentResults": [
                    {"assertion": {"type": "python"}, "score": 0.9, "pass": True},
                    {
                        "assertion": {"type": "llm-rubric"},
                        "score": 0.9,
                        "pass": True,
                    },
                ]
            },
            "latencyMs": 100,
            "cost": 0.01,
        }

    summary = report.build_summary(
        [entry("case_a") for _ in range(6)],
        expected_cases={"case_a", "case_b"},
    )

    row = summary["models"][0]
    assert row["calls"] == 6
    assert row["observed_cases"] == ["case_a"]
    assert row["missing_cases"] == ["case_b"]
    assert row["duplicate_cases"] == ["case_a"]
    assert row["data_complete"] is False
    assert summary["recommendation"]["decision"] == "retest"


@pytest.mark.unit
def test_report_requires_both_dual_scoring_components(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    current_score = SimpleNamespace(
        overall_score=0.9,
        dimensions=[SimpleNamespace(dimension="summary", score=0.9)],
    )
    monkeypatch.setattr(
        report,
        "score_output_against_target",
        lambda **_kwargs: current_score,
    )
    entry = {
        "provider": {"label": "Model A"},
        "vars": {"clip_id": "case_a", "target_path": "target.json"},
        "response": {"output": "{}", "metadata": {}},
        "gradingResult": {"componentResults": []},
        "latencyMs": 100,
        "cost": 0.01,
    }

    summary = report.build_summary([entry], expected_cases={"case_a"})

    row = summary["models"][0]
    assert row["overall"] is None
    assert row["incomplete_cases"] == ["case_a"]
    assert row["data_complete"] is False
    assert summary["recommendation"]["decision"] == "retest"

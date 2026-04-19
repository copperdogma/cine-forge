from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_SCRIPT_ROOT = REPO_ROOT / "benchmarks" / "scripts"
BENCHMARK_SCORER_ROOT = REPO_ROOT / "benchmarks" / "scorers"
for path in (BENCHMARK_SCRIPT_ROOT, BENCHMARK_SCORER_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

report = importlib.import_module("previz_usefulness_report")


@pytest.mark.unit
def test_build_summary_holds_ai_primary_when_best_ai_trails_fast_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset_root = tmp_path / "previz_usefulness"
    dataset_root.mkdir(parents=True, exist_ok=True)
    for variant, label, latency_ms, cost_usd in (
        ("annotated_symbolic", "Annotated Animatic", 2200, 0.0),
        ("openai_sora2_previz", "Sora 2 Previz", 54000, 0.8),
    ):
        variant_dir = dataset_root / variant / "clip_1"
        variant_dir.mkdir(parents=True, exist_ok=True)
        (variant_dir / "meta.json").write_text(
            json.dumps(
                {
                    "candidate_variant": variant,
                    "candidate_label": label,
                    "duration_seconds": 4.0,
                    "resolution": "720p",
                    "generation_latency_ms": latency_ms,
                    "estimated_generation_cost_usd": cost_usd,
                    "operator_lane": (
                        "deterministic_baseline" if variant == "annotated_symbolic" else "ai_previz"
                    ),
                    "latency_budget_ms": 6000 if variant == "annotated_symbolic" else 180000,
                    "consistency_strategy": "prompt_only" if cost_usd else "deterministic",
                    "style_profile_id": "cineforge_low_fidelity_previz_v1",
                    "style_profile_title": "CineForge Low-Fidelity Previz",
                    "engine_pack_id": "fixture_pack",
                    "target_model": "fixture-model",
                }
            )
        )

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
                "audio_description": "Radio dispatch over room tone.",
                "summary_reference": "A cool blue two-shot with a slow push-in.",
                "required_keywords": ["cool", "blue", "push-in"],
                "tone_tags": ["intimate"],
                "emotion_tags": ["hesitation"],
                "color_tags": ["navy"],
                "camera_tags": ["slow_push_in"],
                "motion_tags": ["measured"],
                "continuity_status": "intact",
                "continuity_notes": ["The prop stays in hand."],
                "audio_tags": ["speech"],
                "clip_tags": ["dialogue"],
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
                "provider": {"label": "Annotated Animatic"},
                "vars": {"clip_id": "clip_1", "target_path": str(target_path)},
                "response": {
                    "output": json.dumps(
                        {
                            "clip_id": "clip_1",
                            "summary": "A cool blue two-shot with a slow push-in.",
                            "tone_tags": ["intimate"],
                            "emotion_tags": ["hesitation"],
                            "color_tags": ["navy"],
                            "camera_tags": ["slow_push_in"],
                            "motion_tags": ["measured"],
                            "continuity_status": "intact",
                            "continuity_notes": ["The prop stays in hand."],
                            "audio_tags": ["speech"],
                            "audio_notes": [],
                            "evidence": [
                                {
                                    "timestamp_seconds": 1.0,
                                    "cue": "The push-in holds on the pair.",
                                }
                            ],
                            "overall_confidence": 0.8,
                        }
                    ),
                    "metadata": {"clip_id": "clip_1", "candidate_variant": "annotated_symbolic"},
                },
                "gradingResult": {
                    "componentResults": [
                        {"assertion": {"type": "python"}, "score": 0.84},
                        {"assertion": {"type": "llm-rubric"}, "score": 0.80},
                    ]
                },
                "latencyMs": 7000,
                "cost": 0.01,
            },
            {
                "provider": {"label": "Sora 2 Previz"},
                "vars": {"clip_id": "clip_1", "target_path": str(target_path)},
                "response": {
                    "output": json.dumps(
                        {
                            "clip_id": "clip_1",
                            "summary": "A blue two-shot with a push-in and simplified staging.",
                            "tone_tags": ["intimate"],
                            "emotion_tags": ["hesitation"],
                            "color_tags": ["navy"],
                            "camera_tags": ["slow_push_in"],
                            "motion_tags": ["measured"],
                            "continuity_status": "intact",
                            "continuity_notes": ["The prop stays in hand."],
                            "audio_tags": ["speech"],
                            "audio_notes": [],
                            "evidence": [
                                {
                                    "timestamp_seconds": 1.0,
                                    "cue": "The push-in holds on the pair.",
                                }
                            ],
                            "overall_confidence": 0.78,
                        }
                    ),
                    "metadata": {"clip_id": "clip_1", "candidate_variant": "openai_sora2_previz"},
                },
                "gradingResult": {
                    "componentResults": [
                        {"assertion": {"type": "python"}, "score": 0.80},
                        {"assertion": {"type": "llm-rubric"}, "score": 0.78},
                    ]
                },
                "latencyMs": 7200,
                "cost": 0.01,
            },
        ]
        * 3,
        dataset_root=dataset_root,
    )

    assert summary["recommendation"]["decision"] == "hold_ai_primary_blocked"
    assert summary["recommendation"]["primary_lane"] == "Sora 2 Previz"
    assert summary["recommendation"]["fallback_lane"] == "Annotated Animatic"
    assert "Deterministic baseline measured 2200 ms" in summary["recommendation"]["rationale"]


@pytest.mark.unit
def test_build_summary_treats_xai_variant_as_ai_previz_candidate(
    tmp_path: Path,
) -> None:
    dataset_root = tmp_path / "previz_usefulness"
    dataset_root.mkdir(parents=True, exist_ok=True)
    for variant, label, latency_ms, cost_usd, operator_lane in (
        ("annotated_symbolic", "Annotated Animatic", 500, 0.0, "deterministic_baseline"),
        (
            "xai_grok_imagine_video_previz",
            "Grok Imagine Previz",
            65000,
            0.25,
            "ai_previz",
        ),
    ):
        variant_dir = dataset_root / variant / "clip_1"
        variant_dir.mkdir(parents=True, exist_ok=True)
        (variant_dir / "meta.json").write_text(
            json.dumps(
                {
                    "candidate_variant": variant,
                    "candidate_label": label,
                    "duration_seconds": 4.0,
                    "resolution": "480p",
                    "generation_latency_ms": latency_ms,
                    "estimated_generation_cost_usd": cost_usd,
                    "operator_lane": operator_lane,
                    "latency_budget_ms": (
                        6000 if operator_lane == "deterministic_baseline" else 180000
                    ),
                    "consistency_strategy": (
                        "deterministic"
                        if operator_lane == "deterministic_baseline"
                        else "prompt_only"
                    ),
                    "style_profile_id": "cineforge_low_fidelity_previz_v1",
                    "style_profile_title": "CineForge Low-Fidelity Previz",
                    "engine_pack_id": "xai_grok_imagine_video",
                    "target_model": "grok-imagine-video",
                }
            )
        )

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
                "audio_description": "Radio dispatch over room tone.",
                "summary_reference": "A cool blue two-shot with a slow push-in.",
                "required_keywords": ["cool", "blue", "push-in"],
                "tone_tags": ["intimate"],
                "emotion_tags": ["hesitation"],
                "color_tags": ["navy"],
                "camera_tags": ["slow_push_in"],
                "motion_tags": ["measured"],
                "continuity_status": "intact",
                "continuity_notes": ["The prop stays in hand."],
                "audio_tags": ["speech"],
                "clip_tags": ["dialogue"],
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

    results = []
    for label, variant, python_score, rubric_score in (
        ("Annotated Animatic", "annotated_symbolic", 0.84, 0.80),
        ("Grok Imagine Previz", "xai_grok_imagine_video_previz", 0.82, 0.79),
    ):
        results.extend(
            [
                {
                    "provider": {"label": label},
                    "vars": {"clip_id": "clip_1", "target_path": str(target_path)},
                    "response": {
                        "output": json.dumps(
                            {
                                "clip_id": "clip_1",
                                "summary": "A cool blue two-shot with a slow push-in.",
                                "tone_tags": ["intimate"],
                                "emotion_tags": ["hesitation"],
                                "color_tags": ["navy"],
                                "camera_tags": ["slow_push_in"],
                                "motion_tags": ["measured"],
                                "continuity_status": "intact",
                                "continuity_notes": ["The prop stays in hand."],
                                "audio_tags": ["speech"],
                                "audio_notes": [],
                                "evidence": [
                                    {
                                        "timestamp_seconds": 1.0,
                                        "cue": "The push-in holds on the pair.",
                                    }
                                ],
                                "overall_confidence": 0.8,
                            }
                        ),
                        "metadata": {"clip_id": "clip_1", "candidate_variant": variant},
                    },
                    "gradingResult": {
                        "componentResults": [
                            {"assertion": {"type": "python"}, "score": python_score},
                            {"assertion": {"type": "llm-rubric"}, "score": rubric_score},
                        ]
                    },
                    "latencyMs": 7000,
                    "cost": 0.01,
                }
            ]
            * 3
        )

    summary = report.build_summary(results, dataset_root=dataset_root)

    xai_row = next(
        row for row in summary["candidates"] if row["candidate"] == "Grok Imagine Previz"
    )
    assert xai_row["candidate_class"] == "ai_previz"
    assert xai_row["candidate_variant"] == "xai_grok_imagine_video_previz"

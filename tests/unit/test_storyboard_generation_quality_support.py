from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_SCRIPT_ROOT = REPO_ROOT / "benchmarks" / "scripts"
if str(BENCHMARK_SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_SCRIPT_ROOT))

support = importlib.import_module("storyboard_generation_quality_support")
report = importlib.import_module("storyboard_generation_quality_report")


@pytest.mark.unit
def test_storyboard_quality_manifest_parses_reference_case() -> None:
    manifest = support.StoryboardQualityManifest.model_validate_json(
        json.dumps(
            {
                "cases": [
                    {
                        "case_id": "fixture_case",
                        "label": "Fixture case",
                        "input_fixture": "tests/fixtures/sample_screenplay.fountain",
                        "scene_ids": ["scene_001", "scene_002"],
                        "attach_visual_references": True,
                        "reference_assets": [
                            {
                                "entity_type": "character",
                                "entity_name": "ARIA",
                                "display_name": "ARIA",
                                "filename": "aria.jpg",
                                "label": "Aria character reference",
                                "descriptor": "A determined lead in storm gear.",
                                "accent_rgb": [84, 154, 255]
                            }
                        ],
                        "analysis_target": {
                            "storyboard_id": "fixture_case",
                            "title": "Fixture case",
                            "source_type": "project_owned_internal",
                            "source_description": "Fixture",
                            "rights": "Owned",
                            "scene_ids": ["scene_001", "scene_002"],
                            "summary_reference": "Storm-night radio rescue.",
                            "required_keywords": ["radio"],
                            "recurring_characters": [
                                {"name": "ARIA", "descriptor_keywords": ["storm gear"]}
                            ],
                            "reference_expectations": [
                                {
                                    "label": "Aria character reference",
                                    "entity_name": "ARIA",
                                    "descriptor_keywords": ["storm gear"],
                                    "direct_reference_required": True,
                                }
                            ],
                            "expected_available_reference_min": 1,
                            "expected_prompt_reference_min": 1,
                            "expected_direct_reference_min": 1
                        }
                    }
                ]
            }
        )
    )
    assert len(manifest.cases) == 1
    assert manifest.cases[0].attach_visual_references is True
    assert manifest.cases[0].reference_assets[0].label == "Aria character reference"


@pytest.mark.unit
def test_gpt_image_2_is_default_storyboard_quality_candidate() -> None:
    assert support.DEFAULT_CANDIDATES == ("gpt_image_2_template_grid_storyboards",)
    assert support.CANDIDATE_SPECS["gpt_image_2_storyboards"].image_model == "gpt-image-2"
    assert (
        support.CANDIDATE_SPECS["gpt_image_2_square_storyboards"].runtime_params["image_size"]
        == "1024x1024"
    )
    assert (
        support.CANDIDATE_SPECS["gpt_image_2_template_grid_storyboards"].runtime_params[
            "storyboard_grid_mode"
        ]
        == "template"
    )
    reference_anchors = support.CANDIDATE_SPECS[
        "gpt_image_2_template_grid_reference_anchors"
    ]
    assert reference_anchors.image_model == "gpt-image-2"
    assert reference_anchors.label == "GPT Image 2 Template Grid Reference Anchors"
    assert reference_anchors.runtime_params == {
        "storyboard_grid_mode": "template",
        "storyboard_grid_max_panels": 8,
        "storyboard_grid_reference_anchors": True,
    }
    beat_grid = support.CANDIDATE_SPECS["gpt_image_2_beat_grid_storyboards"]
    assert beat_grid.image_model == "gpt-image-2"
    assert beat_grid.label == "GPT Image 2 Beat Grid Storyboards"
    assert beat_grid.runtime_params == {
        "storyboard_grid_mode": "beat_template",
        "storyboard_grid_max_panels": 9,
    }
    assert "imagen_4_storyboards" in support.CANDIDATE_SPECS


@pytest.mark.unit
def test_summarize_runtime_runs_tracks_reference_counts() -> None:
    runs = [
        support.StoryboardQualityRunSummary(
            case_id="case_a",
            case_label="Case A",
            scene_ids=["scene_001"],
            input_fixture="tests/fixtures/sample_screenplay.fountain",
            candidate_variant="gpt_image_2_storyboards",
            candidate_label="GPT Image 2 Storyboards",
            image_model="gpt-image-2",
            project_dir="output/case-a",
            success=True,
            preparation_elapsed_ms=1000,
            storyboard_elapsed_ms=2000,
            total_elapsed_ms=3000,
            total_cost_usd=0.12,
            storyboard_stage_elapsed_ms=1800,
            total_frames=4,
            available_reference_image_count=4,
            prompt_reference_frame_count=0,
            direct_reference_input_count=0,
        ),
        support.StoryboardQualityRunSummary(
            case_id="case_b",
            case_label="Case B",
            scene_ids=["scene_001"],
            input_fixture="tests/fixtures/sample_screenplay.fountain",
            candidate_variant="gpt_image_2_storyboards",
            candidate_label="GPT Image 2 Storyboards",
            image_model="gpt-image-2",
            project_dir="output/case-b",
            success=True,
            preparation_elapsed_ms=1200,
            storyboard_elapsed_ms=2200,
            total_elapsed_ms=3400,
            total_cost_usd=0.16,
            storyboard_stage_elapsed_ms=2000,
            total_frames=5,
            available_reference_image_count=0,
            prompt_reference_frame_count=0,
            direct_reference_input_count=0,
        ),
    ]
    summary = support.summarize_runtime_runs(runs)
    assert len(summary) == 1
    assert summary[0].mean_total_frames == 4.5
    assert summary[0].mean_available_reference_image_count == 2.0


@pytest.mark.unit
def test_report_flags_reference_flow_gap(tmp_path: Path) -> None:
    dataset_root = tmp_path / "storyboard_generation_quality"
    sequence_dir = dataset_root / "gpt_image_2_template_grid_storyboards" / "fixture_case"
    sequence_dir.mkdir(parents=True, exist_ok=True)
    (sequence_dir / "meta.json").write_text(
        json.dumps({"candidate_label": "GPT Image 2 Template Grid Storyboards"}),
        encoding="utf-8",
    )
    target_dir = dataset_root / "targets" / "fixture_case"
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "target.json").write_text(
        json.dumps(
            {
                "storyboard_id": "fixture_case",
                "title": "Fixture case",
                "source_type": "project_owned_internal",
                "source_description": "Fixture",
                "rights": "Owned",
                "scene_ids": ["scene_001"],
                "summary_reference": "Radio storm sequence.",
                "required_keywords": ["radio", "storm"],
                "recurring_characters": [],
                "reference_expectations": [],
                "expected_available_reference_min": 0,
                "expected_prompt_reference_min": 0,
                "expected_direct_reference_min": 0,
                "should_avoid_readable_text": False,
                "should_avoid_prop_only_non_insert": True,
            }
        ),
        encoding="utf-8",
    )
    runtime_payload = {
        "summary": {
            "candidates": [
                {
                    "candidate_variant": "gpt_image_2_template_grid_storyboards",
                    "candidate_label": "GPT Image 2 Template Grid Storyboards",
                    "image_model": "gpt-image-2",
                    "total_cases": 2,
                    "successful_cases": 2,
                    "success_ratio": 1.0,
                    "mean_total_elapsed_ms": 3200.0,
                    "mean_storyboard_stage_elapsed_ms": 1900.0,
                    "mean_total_cost_usd": 0.14,
                    "mean_total_frames": 4.5,
                    "mean_available_reference_image_count": 2.0,
                    "mean_prompt_reference_frame_count": 0.0,
                    "mean_direct_reference_input_count": 0.0
                }
            ]
        }
    }
    promptfoo_payload = {
        "results": {
            "results": [
                {
                    "vars": {
                        "storyboard_id": "fixture_case",
                        "target_path": str(target_dir / "target.json"),
                    },
                    "score": 0.61,
                    "response": {
                        "metadata": {"candidate_variant": "gpt_image_2_template_grid_storyboards"},
                        "output": json.dumps(
                            {
                                "storyboard_id": "fixture_case",
                                "summary": "Radio storm sequence.",
                                "keywords": ["radio", "storm"],
                                "style_assessment": {
                                    "consistency_status": "consistent",
                                    "observed_mediums": ["monochrome storyboard sketch"],
                                    "evidence": "All frames use the same drawn medium.",
                                },
                                "character_assessments": [],
                                "reference_assessments": [],
                                "readable_text_present": False,
                                "prop_only_non_insert_present": False,
                                "evidence": [
                                    {
                                        "frame_id": "scene_001_frame_01",
                                        "cue": "Radio consoles under storm light.",
                                    }
                                ],
                                "overall_confidence": 0.8,
                            }
                        ),
                    },
                    "gradingResult": {
                        "componentResults": [
                            {"assertion": {"type": "python"}, "score": 0.58},
                            {"assertion": {"type": "llm-rubric"}, "score": 0.64}
                        ]
                    },
                    "latencyMs": 900,
                    "cost": 0.01
                }
            ]
        }
    }
    summary = report.build_summary(
        runtime_payload=runtime_payload,
        promptfoo_payload=promptfoo_payload,
        dataset_root=dataset_root,
    )
    assert summary["recommendation"]["decision"] == "lane_drops_references_before_generation"
    row = summary["candidates"][0]
    assert row["dimension_scores"]["style_consistency"] == 1.0


@pytest.mark.unit
def test_report_recommendation_uses_registry_default_candidate(tmp_path: Path) -> None:
    dataset_root = tmp_path / "storyboard_generation_quality"
    runtime_payload = {
        "summary": {
            "candidates": [
                {
                    "candidate_variant": "gpt_image_2_storyboards",
                    "candidate_label": "GPT Image 2 Storyboards",
                    "image_model": "gpt-image-2",
                    "success_ratio": 1.0,
                    "mean_total_elapsed_ms": 4000.0,
                    "mean_storyboard_stage_elapsed_ms": 2000.0,
                    "mean_total_cost_usd": 0.44,
                    "mean_total_frames": 4.0,
                    "mean_available_reference_image_count": 2.0,
                    "mean_prompt_reference_frame_count": 0.0,
                    "mean_direct_reference_input_count": 0.0,
                },
                {
                    "candidate_variant": "gpt_image_2_template_grid_storyboards",
                    "candidate_label": "GPT Image 2 Template Grid Storyboards",
                    "image_model": "gpt-image-2",
                    "success_ratio": 1.0,
                    "mean_total_elapsed_ms": 3000.0,
                    "mean_storyboard_stage_elapsed_ms": 1500.0,
                    "mean_total_cost_usd": 0.27,
                    "mean_total_frames": 4.0,
                    "mean_available_reference_image_count": 2.0,
                    "mean_prompt_reference_frame_count": 2.0,
                    "mean_direct_reference_input_count": 2.0,
                },
            ]
        }
    }
    promptfoo_payload = {
        "results": {
            "results": [
                {
                    "vars": {"storyboard_id": "fixture_case"},
                    "score": 0.9,
                    "response": {
                        "metadata": {"candidate_variant": "gpt_image_2_storyboards"},
                        "output": "{}",
                    },
                    "gradingResult": {"componentResults": []},
                },
                {
                    "vars": {"storyboard_id": "fixture_case"},
                    "score": 0.8,
                    "response": {
                        "metadata": {"candidate_variant": "gpt_image_2_template_grid_storyboards"},
                        "output": "{}",
                    },
                    "gradingResult": {"componentResults": []},
                },
            ]
        }
    }

    summary = report.build_summary(
        runtime_payload=runtime_payload,
        promptfoo_payload=promptfoo_payload,
        dataset_root=dataset_root,
        baseline_variant="gpt_image_2_template_grid_storyboards",
    )

    assert summary["previous_default"] == "gpt_image_2_template_grid_storyboards"
    assert summary["recommendation"]["decision"] == "lane_clears_initial_floor"

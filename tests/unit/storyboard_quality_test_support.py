from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]


def maintained_manifest_payload() -> dict[str, Any]:
    return json.loads(
        (
            REPO_ROOT / "benchmarks" / "fixtures" / "storyboard_generation_quality_cases.json"
        ).read_text(encoding="utf-8")
    )


def target_for(case_id: str) -> dict[str, Any]:
    return next(
        case["analysis_target"]
        for case in maintained_manifest_payload()["cases"]
        if case["case_id"] == case_id
    )


def good_analysis(
    *,
    case_id: str,
    frame_count: int = 8,
    reference_count: int | None = None,
) -> dict[str, Any]:
    if reference_count is None:
        reference_count = 4 if case_id == "sbq_case_002" else 0
    return {
        "storyboard_id": case_id,
        "packet_frame_count": frame_count,
        "packet_reference_count": reference_count,
        "summary": (
            "A grayscale radio-studio storyboard moves into a stormy water-tower "
            "catwalk sequence with recurring technicians."
        ),
        "keywords": [
            "radio studio",
            "storm night",
            "water tower catwalk",
            "portable antenna",
            "lantern",
        ],
        "style_assessment": {
            "first_half_mediums": ["monochrome pencil storyboard sketch"],
            "second_half_mediums": ["grayscale pencil storyboard sketch"],
            "first_half_frame_ids": ["frame_001", "frame_002"],
            "second_half_frame_ids": [f"frame_{frame_count - 1:03d}", f"frame_{frame_count:03d}"],
        },
        "character_assessments": [
            {
                "name": "subject_001",
                "first_half_traits": ["dark hair", "practical work jacket"],
                "second_half_traits": ["dark hair", "practical work jacket"],
                "first_half_frame_ids": ["frame_001", "frame_002"],
                "second_half_frame_ids": [f"frame_{frame_count - 1:03d}"],
            },
            {
                "name": "subject_002",
                "first_half_traits": ["short hair", "dark work shirt"],
                "second_half_traits": ["short hair", "dark work shirt"],
                "first_half_frame_ids": ["frame_001", "frame_002"],
                "second_half_frame_ids": [f"frame_{frame_count:03d}"],
            },
        ],
        "reference_assessments": [
            {
                "label": f"reference_{index:03d}",
                "observed_similarities": [],
                "generated_frame_ids": [],
            }
            for index in range(1, reference_count + 1)
        ],
        "readable_text_frame_ids": [],
        "prop_only_frame_ids": [],
        "evidence": [
            {
                "frame_id": "frame_001",
                "cue": "Monochrome radio studio with mixer console and tape equipment.",
            },
            {
                "frame_id": "frame_002",
                "cue": "Portable antenna and receiver appear during storm preparation.",
            },
            {
                "frame_id": f"frame_{frame_count - 1:03d}",
                "cue": "Night wind surrounds a water tower catwalk and antenna rail.",
            },
            {
                "frame_id": f"frame_{frame_count:03d}",
                "cue": "Lantern light falls across two technicians beside the receiver.",
            },
        ],
        "overall_confidence": 0.84,
    }


def promptfoo_entry(
    *,
    case_id: str,
    target_path: Path,
    output: dict[str, Any],
    variant: str = "gpt_image_2_template_grid_storyboards",
    rubric_score: float = 0.8,
    stored_python_score: float = 0.0,
    dataset_manifest_sha256: str = "",
    asset_manifest_sha256: str = "",
) -> dict[str, Any]:
    return {
        "vars": {"storyboard_id": case_id, "target_path": str(target_path)},
        "score": 0.01,
        "response": {
            "metadata": {
                "candidate_variant": variant,
                "prompt_version": "storyboard-understanding-v3",
                "dataset_manifest_sha256": dataset_manifest_sha256,
                "asset_manifest_sha256": asset_manifest_sha256,
            },
            "output": json.dumps(output),
        },
        "gradingResult": {
            "componentResults": [
                {
                    "assertion": {"type": "python"},
                    "score": stored_python_score,
                    "pass": True,
                },
                {
                    "assertion": {"type": "llm-rubric"},
                    "score": rubric_score,
                    "pass": True,
                },
            ]
        },
        "latencyMs": 900,
        "cost": 0.01,
    }

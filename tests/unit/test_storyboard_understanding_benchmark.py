from __future__ import annotations

import importlib
import io
import json
import sys
from pathlib import Path

import pytest
from PIL import Image

from cine_forge.modules.visualization.storyboard_v1 import generation as storyboard_generation
from cine_forge.modules.visualization.storyboard_v1.main import run_module
from tests.storyboard_fixtures import metadata, seed_storyboard_project

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_PROVIDER_ROOT = REPO_ROOT / "benchmarks" / "providers"
BENCHMARK_SCORER_ROOT = REPO_ROOT / "benchmarks" / "scorers"
BENCHMARK_SCRIPT_ROOT = REPO_ROOT / "benchmarks" / "scripts"
for path in (BENCHMARK_PROVIDER_ROOT, BENCHMARK_SCORER_ROOT, BENCHMARK_SCRIPT_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

provider = importlib.import_module("storyboard_understanding_provider")
scorer = importlib.import_module("storyboard_understanding_scorer")
runtime_eval = importlib.import_module("storyboard_generation_quality_eval")


def _write_jpeg(path: Path, color: tuple[int, int, int]) -> None:
    image = Image.new("RGB", (64, 64), color=color)
    image.save(path, format="JPEG", quality=90)


def _jpeg_bytes(size: str = "1536x1024") -> bytes:
    width, height = (int(part) for part in size.split("x", maxsplit=1))
    image = Image.new("RGB", (width, height), color=(240, 240, 240))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


@pytest.mark.unit
def test_provider_builds_storyboard_brief_from_meta() -> None:
    meta = {
        "storyboard_id": "open_frequency_sequence_reference_conditioned",
        "title": "Open Frequency storyboard sequence",
        "scene_ids": ["scene_001", "scene_002"],
        "frame_count": 4,
        "available_reference_image_count": 4,
        "prompt_reference_frame_count": 0,
        "direct_reference_input_count": 0,
        "reference_transport_supported": False,
        "recurring_character_names": ["ARIA", "NOAH"],
        "reference_images": [
            {"label": "Aria character reference", "entity_name": "ARIA"},
            {"label": "Radio studio location reference", "entity_name": "COMMUNITY RADIO STUDIO"},
        ],
    }
    user_text = provider._build_user_text(
        "Return JSON.",
        meta,
        prompt_version="storyboard-understanding-v1",
    )
    assert "storyboard_id: open_frequency_sequence_reference_conditioned" in user_text
    assert "scene_ids: scene_001, scene_002" in user_text
    assert (
        "reference_labels: Aria character reference, Radio studio location reference"
        in user_text
    )


@pytest.mark.unit
def test_provider_payload_builders_include_frames_and_references() -> None:
    images = [
        {
            "kind": "storyboard_frame",
            "label": "01_frame_001",
            "mime_type": "image/jpeg",
            "base64": "abc",
        },
        {
            "kind": "storyboard_frame",
            "label": "02_frame_002",
            "mime_type": "image/jpeg",
            "base64": "def",
        },
        {
            "kind": "reference_image",
            "label": "aria_reference",
            "mime_type": "image/jpeg",
            "base64": "ghi",
        },
    ]
    openai_payload = provider._build_openai_payload(
        model="gpt-5.4",
        user_text="Inspect this storyboard sequence.",
        images=images,
        max_tokens=1200,
        temperature=0.0,
    )
    anthropic_payload = provider._build_anthropic_payload(
        model="claude-sonnet-4-6",
        user_text="Inspect this storyboard sequence.",
        images=images,
        max_tokens=1200,
        temperature=0.0,
    )
    gemini_payload = provider._build_gemini_payload(
        user_text="Inspect this storyboard sequence.",
        images=images,
        max_tokens=1200,
        temperature=0.0,
    )

    assert len(openai_payload["messages"][0]["content"]) == 7
    assert len(anthropic_payload["messages"][0]["content"]) == 7
    assert len(gemini_payload["contents"][0]["parts"]) == 7
    assert openai_payload["messages"][0]["content"][1]["text"] == (
        "Generated storyboard frame: 01_frame_001"
    )


@pytest.mark.unit
def test_provider_resolves_candidate_variant_sequence_dir(tmp_path: Path) -> None:
    sequence_dir = provider._resolve_sequence_dir(
        base_path=tmp_path,
        config={
            "sequence_root": "../storyboard_generation_quality",
            "candidate_variant": "imagen_4_storyboards",
        },
        vars_data={"storyboard_id": "open_frequency_sequence_prompt_only"},
    )
    expected = (
        tmp_path
        / "../storyboard_generation_quality"
        / "imagen_4_storyboards"
        / "open_frequency_sequence_prompt_only"
    ).resolve()
    assert sequence_dir == expected


@pytest.mark.unit
def test_provider_loads_frames_and_references(tmp_path: Path) -> None:
    sequence_dir = tmp_path / "storyboard"
    frames_dir = sequence_dir / "frames"
    refs_dir = sequence_dir / "references"
    frames_dir.mkdir(parents=True)
    refs_dir.mkdir(parents=True)
    _write_jpeg(frames_dir / "01.jpg", (20, 40, 80))
    _write_jpeg(frames_dir / "02.jpg", (80, 40, 20))
    _write_jpeg(refs_dir / "aria.jpg", (40, 80, 20))
    (sequence_dir / "meta.json").write_text(
        json.dumps(
            {
                "storyboard_id": "fixture",
                "title": "Fixture",
                "scene_ids": ["scene_001"],
                "frame_count": 2,
                "available_reference_image_count": 1,
                "prompt_reference_frame_count": 0,
                "direct_reference_input_count": 0,
                "reference_transport_supported": False,
                "recurring_character_names": ["ARIA"],
                "reference_images": [{"label": "Aria character reference", "entity_name": "ARIA"}],
            }
        ),
        encoding="utf-8",
    )
    packet = provider._load_storyboard_packet(
        sequence_dir=sequence_dir,
        max_frames=6,
        max_references=4,
    )
    assert packet["meta"]["storyboard_id"] == "fixture"
    assert len(packet["frames"]) == 2
    assert len(packet["references"]) == 1
    assert packet["frames"][0]["kind"] == "storyboard_frame"
    assert packet["frames"][0]["label"] == "01"
    assert packet["references"][0]["kind"] == "reference_image"


@pytest.mark.unit
def test_provider_samples_frames_across_full_sequence(tmp_path: Path) -> None:
    sequence_dir = tmp_path / "storyboard"
    frames_dir = sequence_dir / "frames"
    frames_dir.mkdir(parents=True)
    for idx in range(1, 16):
        _write_jpeg(frames_dir / f"{idx:02d}.jpg", (idx * 10 % 255, 40, 80))
    (sequence_dir / "meta.json").write_text(
        json.dumps(
            {
                "storyboard_id": "fixture",
                "title": "Fixture",
                "scene_ids": ["scene_001", "scene_002"],
                "frame_count": 15,
                "available_reference_image_count": 0,
                "prompt_reference_frame_count": 0,
                "direct_reference_input_count": 0,
                "reference_transport_supported": False,
                "recurring_character_names": ["ARIA"],
                "reference_images": [],
            }
        ),
        encoding="utf-8",
    )

    packet = provider._load_storyboard_packet(
        sequence_dir=sequence_dir,
        max_frames=6,
        max_references=4,
    )

    assert [frame["label"] for frame in packet["frames"]] == [
        "01",
        "04",
        "07",
        "09",
        "12",
        "15",
    ]


@pytest.mark.unit
def test_runtime_collector_reads_direct_reference_inputs_from_storyboard_artifact(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeded = seed_storyboard_project(tmp_path, scene_count=1)

    def fake_generate_image(
        prompt: str,
        entity_type: str = "character",
        model: str = "gpt-image-1",
        aspect_ratio: str | None = None,
        quality: str = "auto",
        reference_image_paths: list[str] | None = None,
        size: str | None = None,
    ) -> tuple[bytes, str]:
        assert reference_image_paths
        return _jpeg_bytes(str(size or "1536x1024")), model

    monkeypatch.setattr(storyboard_generation, "generate_image", fake_generate_image)

    result = run_module(
        inputs=seeded["inputs"],
        params={"image_model": "imagen-4.0-generate-001", "style": "clean_line"},
        context={"project_dir": str(seeded["project_dir"]), "run_id": "collector-test"},
    )
    storyboard_artifact = next(
        artifact for artifact in result["artifacts"] if artifact["artifact_type"] == "storyboard"
    )
    seeded["store"].save_artifact(
        artifact_type="storyboard",
        entity_id="scene_001",
        data=storyboard_artifact["data"],
        metadata=metadata("collector test storyboard"),
    )

    collected = runtime_eval._collect_storyboard_outputs(
        project_dir=seeded["project_dir"],
        scene_ids=["scene_001"],
    )

    assert collected["available_reference_image_count"] >= 1
    assert collected["prompt_reference_frame_count"] >= 1
    assert collected["direct_reference_input_count"] >= 1
    assert collected["reference_transport_supported"] is True


@pytest.mark.unit
def test_scorer_parses_fenced_json() -> None:
    prediction = scorer.parse_prediction(
        """```json
        {
          "storyboard_id": "fixture",
          "summary": "A storm-night radio sequence with recurring leads.",
          "keywords": ["radio", "storm"],
          "style_assessment": {
            "consistency_status": "consistent",
            "observed_mediums": ["monochrome storyboard sketch"],
            "evidence": "All frames share the same drawn storyboard medium."
          },
          "character_assessments": [
            {
              "name": "ARIA",
              "consistency_status": "consistent",
              "observed_traits": ["dark weather gear"],
              "evidence": "Aria keeps the same silhouette."
            }
          ],
          "reference_assessments": [],
          "readable_text_present": false,
          "prop_only_non_insert_present": false,
          "evidence": [
            {
              "frame_id": "scene_001_frame_01",
              "cue": "Radio consoles under storm light."
            }
          ],
          "overall_confidence": 0.82
        }
        ```"""
    )
    assert prediction.storyboard_id == "fixture"
    assert prediction.character_assessments[0].consistency_status == "consistent"


@pytest.mark.unit
def test_scorer_coerces_numeric_evidence_frame_ids_to_strings() -> None:
    prediction = scorer.parse_prediction(
        {
            "storyboard_id": "fixture",
            "summary": "A storm-night radio sequence with recurring leads.",
            "keywords": ["radio", "storm"],
            "character_assessments": [],
            "reference_assessments": [],
            "readable_text_present": False,
            "prop_only_non_insert_present": False,
            "evidence": [{"frame_id": 1, "cue": "Radio consoles under storm light."}],
            "overall_confidence": 0.82,
        }
    )
    assert prediction.evidence[0].frame_id == "1"


@pytest.mark.unit
def test_scorer_rewards_matching_prediction(tmp_path: Path) -> None:
    target_path = tmp_path / "target.json"
    target_path.write_text(
        json.dumps(
            {
                "storyboard_id": "fixture",
                "title": "Fixture",
                "source_type": "project_owned_internal",
                "source_description": "Synthetic fixture",
                "rights": "Owned",
                "scene_ids": ["scene_001", "scene_002"],
                "summary_reference": "A storm-night radio sequence with a lantern and antenna.",
                "required_keywords": ["radio", "storm", "lantern"],
                "recurring_characters": [
                    {"name": "ARIA", "descriptor_keywords": ["storm gear"]},
                    {"name": "NOAH", "descriptor_keywords": ["technician"]}
                ],
                "reference_expectations": [
                    {
                        "label": "Aria character reference",
                        "entity_name": "ARIA",
                        "descriptor_keywords": ["storm gear"],
                        "direct_reference_required": True
                    }
                ],
                "expected_available_reference_min": 1,
                "expected_prompt_reference_min": 1,
                "expected_direct_reference_min": 1,
                "should_avoid_readable_text": True,
                "should_avoid_prop_only_non_insert": True
            }
        ),
        encoding="utf-8",
    )
    output = {
        "storyboard_id": "fixture",
        "summary": "A storm-night radio sequence with a lantern and tense catwalk action.",
        "keywords": ["radio", "storm", "lantern"],
        "style_assessment": {
            "consistency_status": "consistent",
            "observed_mediums": ["monochrome storyboard sketch"],
            "evidence": "All frames use one drawn storyboard medium."
        },
        "character_assessments": [
            {
                "name": "ARIA",
                "consistency_status": "consistent",
                "observed_traits": ["dark weather gear"],
                "evidence": "Aria keeps the same silhouette."
            },
            {
                "name": "NOAH",
                "consistency_status": "minor_drift",
                "observed_traits": ["technician workwear"],
                "evidence": "Noah is mostly consistent."
            }
        ],
        "reference_assessments": [
            {
                "label": "Aria character reference",
                "entity_name": "ARIA",
                "status": "matched",
                "evidence": "The recurring lead matches the supplied portrait silhouette."
            }
        ],
        "readable_text_present": False,
        "prop_only_non_insert_present": False,
        "evidence": [
            {"frame_id": "scene_001_frame_01", "cue": "Radio studio consoles under storm light."},
            {"frame_id": "scene_002_frame_02", "cue": "Lantern and antenna on the catwalk."}
        ],
        "overall_confidence": 0.86,
    }

    score = scorer.score_output_against_target(
        output=output,
        target_path=target_path,
        model_label="Fixture",
        prompt_version="storyboard-understanding-v1",
    )

    assert score.overall_score > 0.8
    assert score.hard_constraints_passed is True
    dimensions = {dimension.dimension: dimension.score for dimension in score.dimensions}
    assert dimensions["story_specificity"] == 1.0
    assert dimensions["style_consistency"] == 1.0
    assert dimensions["identity_consistency"] == 0.75
    assert dimensions["reference_fidelity"] == 1.0


@pytest.mark.unit
def test_scorer_resolves_promptfoo_relative_target_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    target_dir = tmp_path / "benchmarks" / "storyboard_generation_quality" / "targets" / "fixture"
    target_dir.mkdir(parents=True)
    target_path = target_dir / "target.json"
    target_path.write_text(
        json.dumps(
            {
                "storyboard_id": "fixture",
                "title": "Fixture",
                "source_type": "project_owned_internal",
                "source_description": "Synthetic fixture",
                "rights": "Owned",
                "scene_ids": ["scene_001"],
                "summary_reference": "Radio scene.",
                "required_keywords": ["radio"],
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
    monkeypatch.setattr(scorer, "REPO_ROOT", tmp_path)

    resolved = scorer._resolve_relative("storyboard_generation_quality/targets/fixture/target.json")

    assert resolved == target_path.resolve()

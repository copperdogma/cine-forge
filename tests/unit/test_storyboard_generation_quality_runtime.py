from __future__ import annotations

import importlib
import io
import sys
from pathlib import Path

import pytest
from PIL import Image

from cine_forge.modules.visualization.storyboard_v1 import generation as storyboard_generation
from cine_forge.modules.visualization.storyboard_v1.main import run_module
from tests.storyboard_fixtures import metadata, seed_storyboard_project

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "benchmarks" / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

runtime_eval = importlib.import_module("storyboard_generation_quality_eval")


def _jpeg_bytes(size: str = "1536x1024") -> bytes:
    width, height = (int(part) for part in size.split("x", maxsplit=1))
    image = Image.new("RGB", (width, height), color=(240, 240, 240))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


@pytest.mark.unit
def test_runtime_candidates_resolve_to_distinct_per_frame_and_template_modes(
    tmp_path: Path,
) -> None:
    input_file = tmp_path / "source.fountain"
    input_file.write_text("INT. ROOM - DAY\n", encoding="utf-8")

    per_frame = runtime_eval._build_runtime_params(
        input_file=input_file,
        scene_ids=["scene_001"],
        candidate=runtime_eval.CANDIDATE_SPECS["gpt_image_2_storyboards"],
    )
    template_grid = runtime_eval._build_runtime_params(
        input_file=input_file,
        scene_ids=["scene_001"],
        candidate=runtime_eval.CANDIDATE_SPECS[
            "gpt_image_2_template_grid_storyboards"
        ],
    )

    assert per_frame["storyboard_grid_mode"] == "off"
    assert template_grid["storyboard_grid_mode"] == "template"


@pytest.mark.unit
def test_runtime_collector_reads_direct_reference_inputs_from_artifact(
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
        del prompt, entity_type, aspect_ratio, quality
        assert reference_image_paths
        return _jpeg_bytes(str(size or "1536x1024")), model

    monkeypatch.setattr(storyboard_generation, "generate_image", fake_generate_image)
    result = run_module(
        inputs=seeded["inputs"],
        params={
            "image_model": "imagen-4.0-generate-001",
            "style": "clean_line",
            "storyboard_grid_mode": "template",
            "storyboard_grid_max_panels": 8,
        },
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
    assert collected["source_grids"]
    assert all(item.relative_path.endswith("_full.jpg") for item in collected["source_grids"])

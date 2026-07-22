from __future__ import annotations

import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "benchmarks" / "scripts"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from real_render_provider_floor_runner_support import (  # noqa: E402
    generated_video_request_notes,
    load_generated_video_artifact,
)


def _generated_video_envelope() -> dict[str, object]:
    return {
        "metadata": {
            "intent": "retain exact provider evidence",
            "rationale": "exercise the live final-render runner boundary",
            "confidence": 1.0,
            "source": "code",
            "annotations": {
                "request_notes": ["Reference image sent as a provider input."],
            },
        },
        "data": {
            "scene_id": "scene_001",
            "scene_number": 1,
            "scene_heading": "INT. STUDIO - NIGHT",
            "scene_ref": {
                "artifact_type": "scene",
                "entity_id": "scene_001",
                "version": 1,
                "path": "artifacts/scene/scene_001/v1/artifact.json",
            },
            "shot_plan_ref": {
                "artifact_type": "shot_plan",
                "entity_id": "scene_001",
                "version": 1,
                "path": "artifacts/shot_plan/scene_001/v1/artifact.json",
            },
            "prompt_ref": {
                "artifact_type": "render_prompt",
                "entity_id": "scene_001",
                "version": 1,
                "path": "artifacts/render_prompt/scene_001/v1/artifact.json",
            },
            "video": {
                "relative_path": "media/scene_001.mp4",
                "media_type": "video/mp4",
                "duration_seconds": 4.0,
            },
            "duration_seconds": 4.0,
            "resolution": "720p",
            "aspect_ratio": "16:9",
            "target_provider": "google",
            "target_model": "veo-3.1-fast-generate-preview",
            "engine_pack_id": "google_veo31_fast",
            "request_id": "request-123",
            "cost": {
                "model": "veo-3.1-fast-generate-preview",
                "input_tokens": 1,
                "output_tokens": 1,
                "estimated_cost_usd": 0.01,
                "request_id": "request-123",
            },
        },
    }


@pytest.mark.unit
def test_generated_video_loader_retains_envelope_request_notes(tmp_path: Path) -> None:
    relative_path = "artifacts/generated_video/scene_001/v1/artifact.json"
    artifact_path = tmp_path / relative_path
    artifact_path.parent.mkdir(parents=True)
    artifact_path.write_text(json.dumps(_generated_video_envelope()), encoding="utf-8")

    envelope, generated = load_generated_video_artifact(
        project_dir=tmp_path,
        relative_path=relative_path,
    )

    assert generated.request_id == "request-123"
    assert generated_video_request_notes(envelope) == [
        "Reference image sent as a provider input."
    ]


@pytest.mark.unit
@pytest.mark.parametrize(
    "invalid_notes",
    ("not-a-list", [""], ["valid", 7]),
)
def test_generated_video_request_notes_reject_malformed_provenance(
    invalid_notes: object,
) -> None:
    payload = deepcopy(_generated_video_envelope())
    payload["metadata"]["annotations"]["request_notes"] = invalid_notes  # type: ignore[index]

    from cine_forge.schemas import Artifact

    envelope = Artifact.model_validate(payload)
    with pytest.raises(ValueError, match="request_notes"):
        generated_video_request_notes(envelope)

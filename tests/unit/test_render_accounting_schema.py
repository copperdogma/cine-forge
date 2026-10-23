"""Generated-video accounting truth is carried by its consumer-facing schema."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from cine_forge.schemas import GeneratedVideoArtifact


def _payload():
    ref = {
        "artifact_type": "scene",
        "entity_id": "scene_001",
        "version": 1,
        "path": "scene/v1.json",
    }
    return {
        "scene_id": "scene_001",
        "scene_number": 1,
        "scene_heading": "INT. LAB - NIGHT",
        "scene_ref": ref,
        "shot_plan_ref": ref,
        "prompt_ref": ref,
        "video": {"relative_path": "media/v1.mp4", "media_type": "video/mp4"},
        "duration_seconds": 8,
        "resolution": "480p",
        "aspect_ratio": "16:9",
        "target_provider": "xai",
        "target_model": "grok-imagine-video",
        "engine_pack_id": "fixture",
        "cost": {
            "model": "fixture",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.4,
        },
    }


def _receipt(**updates):
    receipt = {
        "receipt_id": "fixture-video",
        "component": "video",
        "model": "fixture",
        "cost": {
            "model": "fixture",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.4,
        },
    }
    return receipt | updates


@pytest.mark.unit
def test_historical_video_without_receipts_is_readable_but_incomplete():
    raw = _payload()
    artifact = GeneratedVideoArtifact.model_validate(raw)
    assert artifact.cost_is_complete is False
    assert artifact.cost_receipts == []
    assert artifact.cost.estimated_cost_usd == 0.4
    assert "cost_is_complete" not in raw  # reading does not mutate historical source


@pytest.mark.unit
def test_complete_video_receipts_round_trip_with_consumer_fields():
    raw = _payload() | {"cost_is_complete": True, "cost_receipts": [_receipt()]}
    artifact = GeneratedVideoArtifact.model_validate(raw)
    restored = GeneratedVideoArtifact.model_validate_json(artifact.model_dump_json())
    assert restored == artifact
    assert restored.cost_is_complete is True
    assert restored.cost_receipts[0].component == "video"


@pytest.mark.unit
@pytest.mark.parametrize(
    "receipts",
    [
        [],
        [_receipt(component="compiler")],
        [
            _receipt(
                status="uncertain",
                cost=None,
                reason="Synthetic unresolved charge",
            )
        ],
    ],
)
def test_complete_video_requires_video_receipt_without_uncertainty(receipts):
    with pytest.raises(ValidationError, match="complete video cost requires"):
        GeneratedVideoArtifact.model_validate(
            _payload()
            | {
                "cost_is_complete": True,
                "cost_receipts": receipts,
            }
        )


@pytest.mark.unit
@pytest.mark.parametrize(
    "change, match",
    [
        ({"estimated_cost_usd": 0.41}, "receipt subtotal"),
        ({"input_tokens": 1}, "token counts"),
        ({"output_tokens": 1}, "token counts"),
    ],
)
def test_artifact_cost_must_equal_known_receipts(change, match):
    raw = _payload() | {"cost_receipts": [_receipt()]}
    raw["cost"] |= change
    with pytest.raises(ValidationError, match=match):
        GeneratedVideoArtifact.model_validate(raw)


@pytest.mark.unit
def test_uncertain_video_keeps_only_known_compiler_subtotal():
    known = _receipt(component="compiler")
    uncertain = _receipt(
        receipt_id="unresolved-video",
        status="uncertain",
        cost=None,
        reason="Synthetic unresolved charge",
    )
    artifact = GeneratedVideoArtifact.model_validate(
        _payload()
        | {
            "cost_receipts": [known, uncertain],
            "cost_is_complete": False,
        }
    )
    assert artifact.cost.estimated_cost_usd == 0.4
    assert artifact.cost_receipts[-1].status == "uncertain"
    assert artifact.cost_is_complete is False


@pytest.mark.unit
def test_artifact_rejects_duplicate_receipt_identity():
    with pytest.raises(ValidationError, match="unique identities"):
        GeneratedVideoArtifact.model_validate(
            _payload() | {"cost_receipts": [_receipt(), _receipt()]}
        )

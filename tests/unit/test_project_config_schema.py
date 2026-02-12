from __future__ import annotations

import pytest
from pydantic import ValidationError

from cine_forge.schemas import ProjectConfig, SchemaRegistry


def _payload() -> dict[str, object]:
    return {
        "title": "Pilot",
        "format": "short_film",
        "genre": ["comedy"],
        "tone": ["grounded"],
        "estimated_duration_minutes": 8.0,
        "primary_characters": ["MARA", "JON"],
        "supporting_characters": ["CLERK"],
        "location_count": 2,
        "locations_summary": ["LAB", "STREET"],
        "target_audience": None,
        "aspect_ratio": "16:9",
        "production_mode": "ai_generated",
        "human_control_mode": "checkpoint",
        "style_packs": {},
        "budget_cap_usd": None,
        "default_model": "gpt-4o",
        "detection_details": {
            "title": {
                "value": "Pilot",
                "confidence": 0.9,
                "rationale": "Title from canonical script.",
                "source": "auto_detected",
            }
        },
        "confirmed": True,
        "confirmed_at": "2026-02-12T15:00:00Z",
    }


@pytest.mark.unit
def test_project_config_schema_accepts_valid_payload() -> None:
    config = ProjectConfig.model_validate(_payload())
    assert config.title == "Pilot"
    assert config.detection_details["title"].source == "auto_detected"


@pytest.mark.unit
def test_project_config_schema_requires_detected_value_rationale() -> None:
    payload = _payload()
    payload["detection_details"] = {
        "title": {
            "value": "Pilot",
            "confidence": 0.9,
            "source": "auto_detected",
        }
    }
    with pytest.raises(ValidationError):
        ProjectConfig.model_validate(payload)


@pytest.mark.unit
def test_project_config_schema_registered_in_registry() -> None:
    registry = SchemaRegistry()
    registry.register("project_config", ProjectConfig)
    result = registry.validate("project_config", _payload())
    assert result.valid is True

"""Tests for RuntimeParams Pydantic model — field validation, defaults, round-trip.

Story 118, Phase 3.
"""

from __future__ import annotations

import pytest

from cine_forge.schemas.runtime_params import RuntimeParams


def _minimal_params(**overrides) -> dict:
    """Return the minimum required fields for constructing RuntimeParams."""
    base = {
        "input_file": "test.fountain",
        "default_model": "claude-sonnet-4-6",
        "model": "claude-sonnet-4-6",
        "utility_model": "claude-sonnet-4-6",
        "sota_model": "claude-opus-4-6",
    }
    base.update(overrides)
    return base


@pytest.mark.unit
def test_required_fields_present() -> None:
    params = RuntimeParams(**_minimal_params())
    assert params.input_file == "test.fountain"
    assert params.default_model == "claude-sonnet-4-6"
    assert params.model == "claude-sonnet-4-6"
    assert params.utility_model == "claude-sonnet-4-6"
    assert params.sota_model == "claude-opus-4-6"


@pytest.mark.unit
def test_optional_field_defaults() -> None:
    params = RuntimeParams(**_minimal_params())
    assert params.human_control_mode == "autonomous"
    assert params.work_model is None
    assert params.verify_model is None
    assert params.qa_model is None
    assert params.escalate_model is None
    assert params.accept_config is False
    assert params.skip_qa is False
    assert params.user_approved is False
    assert params.config_file is None
    assert params.style_packs == {}
    assert params.resume_artifact_refs_by_stage == {}


@pytest.mark.unit
def test_model_dump_by_alias_preserves_dunder_key() -> None:
    """The engine expects __resume_artifact_refs_by_stage (with dunder prefix)."""
    refs = {"ingest": [{"artifact_type": "raw_input", "version": 1}]}
    params = RuntimeParams(**_minimal_params(resume_artifact_refs_by_stage=refs))
    dumped = params.model_dump(by_alias=True, exclude_none=True)
    assert "__resume_artifact_refs_by_stage" in dumped
    assert dumped["__resume_artifact_refs_by_stage"] == refs
    assert "resume_artifact_refs_by_stage" not in dumped


@pytest.mark.unit
def test_round_trip_preserves_types() -> None:
    params = RuntimeParams(
        **_minimal_params(
            work_model="haiku",
            verify_model="sonnet",
            qa_model="sonnet",
            accept_config=True,
            skip_qa=True,
            style_packs={"director": "kubrick"},
        )
    )
    dumped = params.model_dump(by_alias=True)
    assert isinstance(dumped["accept_config"], bool)
    assert isinstance(dumped["skip_qa"], bool)
    assert isinstance(dumped["style_packs"], dict)
    assert dumped["work_model"] == "haiku"
    assert dumped["verify_model"] == "sonnet"


@pytest.mark.unit
def test_missing_required_field_raises() -> None:
    with pytest.raises(ValueError):
        RuntimeParams(input_file="test.fountain")  # Missing other required fields


@pytest.mark.unit
def test_exclude_none_drops_unset_optional_models() -> None:
    params = RuntimeParams(**_minimal_params())
    dumped = params.model_dump(by_alias=True, exclude_none=True)
    assert "work_model" not in dumped
    assert "verify_model" not in dumped
    assert "qa_model" not in dumped
    assert "escalate_model" not in dumped
    assert "config_file" not in dumped

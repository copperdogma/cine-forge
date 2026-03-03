"""Unit tests for ArtifactPersister."""

from __future__ import annotations

import threading
from typing import Any
from unittest.mock import MagicMock

import pytest

from cine_forge.driver.artifact_persister import ArtifactPersister

_TEST_METADATA: dict[str, Any] = {
    "intent": "test artifact",
    "rationale": "unit test",
    "confidence": 0.9,
    "source": "code",
}
"""Minimal metadata satisfying ArtifactMetadata required fields."""


def _artifact(
    artifact_type: str = "scene",
    entity_id: str | None = None,
    data: dict[str, Any] | None = None,
    **extra: Any,
) -> dict[str, Any]:
    """Build a test artifact dict with required metadata."""
    result: dict[str, Any] = {
        "artifact_type": artifact_type,
        "data": data or {"heading": "INT. ROOM"},
        "metadata": {**_TEST_METADATA},
    }
    if entity_id is not None:
        result["entity_id"] = entity_id
    result.update(extra)
    return result


def _make_persister(
    store: Any = None,
    schemas: Any = None,
    module_id: str = "test_module_v1",
    output_schemas: list[str] | None = None,
    stage_id: str = "test_stage",
) -> ArtifactPersister:
    """Create a persister with mock dependencies."""
    if store is None:
        store = MagicMock()
        store.save_artifact.return_value = MagicMock(
            model_dump=lambda: {
                "artifact_type": "scene",
                "version": 1,
                "entity_id": "s1",
            }
        )
    if schemas is None:
        schemas = MagicMock()
        schemas.validate.return_value = MagicMock(valid=True)
    stage_state: dict[str, Any] = {
        "artifact_refs": [],
        "model_used": "gpt-4.1",
    }
    run_state: dict[str, Any] = {"total_cost_usd": 0.0}
    emitter = MagicMock()
    write_run_state = MagicMock()
    return ArtifactPersister(
        store=store,
        schemas=schemas,
        module_id=module_id,
        output_schemas=output_schemas or ["scene"],
        upstream_refs=[],
        stage_id=stage_id,
        stage_state=stage_state,
        run_state=run_state,
        state_lock=threading.Lock(),
        emitter=emitter,
        write_run_state=write_run_state,
    )


@pytest.mark.unit
def test_announce_saves_artifact_and_emits_event() -> None:
    persister = _make_persister()
    artifact_dict = _artifact(
        entity_id="s1",
        data={"heading": "INT. HOUSE - DAY"},
    )
    persister.announce(artifact_dict)

    persister.store.save_artifact.assert_called_once()
    persister.emitter.emit.assert_called_once()
    assert artifact_dict["pre_saved"] is True
    assert "pre_saved_ref" in artifact_dict
    assert len(persister.stage_state["artifact_refs"]) == 1


@pytest.mark.unit
def test_announce_calls_write_run_state() -> None:
    persister = _make_persister()
    artifact_dict = _artifact(data={"heading": "EXT. PARK - NIGHT"})
    persister.announce(artifact_dict)
    persister.write_run_state.assert_called_once()


@pytest.mark.unit
def test_announce_raises_on_schema_validation_failure() -> None:
    schemas = MagicMock()
    schemas.validate.return_value = MagicMock(valid=False)
    persister = _make_persister(schemas=schemas)
    with pytest.raises(ValueError, match="schema validation failed"):
        persister.announce(_artifact(data={"bad": "data"}))


@pytest.mark.unit
def test_persist_batch_returns_persisted_outputs() -> None:
    persister = _make_persister()
    outputs = [
        _artifact(entity_id="s1", data={"heading": "INT. ROOM"}),
        _artifact(entity_id="s2", data={"heading": "EXT. YARD"}),
    ]
    result = persister.persist_batch(outputs, cost_record=None)
    assert len(result) == 2
    assert all("ref" in item and "data" in item for item in result)


@pytest.mark.unit
def test_persist_batch_skips_pre_saved() -> None:
    persister = _make_persister()
    outputs = [
        _artifact(
            entity_id="s1",
            data={"heading": "INT. ROOM"},
            pre_saved=True,
            pre_saved_ref={
                "artifact_type": "scene",
                "version": 1,
                "entity_id": "s1",
                "path": "artifacts/scene/s1/v1",
            },
        ),
    ]
    result = persister.persist_batch(outputs, cost_record=None)
    assert len(result) == 1
    # save_artifact should NOT be called for pre_saved artifacts
    persister.store.save_artifact.assert_not_called()


@pytest.mark.unit
def test_persist_batch_emits_events() -> None:
    persister = _make_persister()
    outputs = [
        _artifact(entity_id="s1", data={"heading": "INT. ROOM"}),
    ]
    persister.persist_batch(outputs, cost_record=None)
    persister.emitter.emit.assert_called_once()

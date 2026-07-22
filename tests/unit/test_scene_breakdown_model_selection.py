from __future__ import annotations

import pytest

from cine_forge.modules.ingest.scene_breakdown_v1.model_selection import (
    DEFAULT_WORK_MODEL,
    resolve_work_model,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("params", "runtime_params", "expected"),
    [
        ({"work_model": "stage-work"}, {"default_model": "runtime"}, "stage-work"),
        ({"model": "stage-model"}, {"default_model": "runtime"}, "stage-model"),
        ({}, {"work_model": "runtime-work", "default_model": "runtime"}, "runtime-work"),
        ({}, {"default_model": "fixture"}, "fixture"),
        ({}, {}, DEFAULT_WORK_MODEL),
    ],
)
def test_resolve_work_model_obeys_stage_then_runtime_precedence(
    params: dict[str, str],
    runtime_params: dict[str, str],
    expected: str,
) -> None:
    assert resolve_work_model(
        params=params,
        context={"runtime_params": runtime_params},
    ) == expected

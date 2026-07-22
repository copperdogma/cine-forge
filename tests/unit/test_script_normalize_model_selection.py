from __future__ import annotations

import pytest

from cine_forge.modules.ingest.script_normalize_v1.model_selection import (
    DEFAULT_VERIFY_MODEL,
    DEFAULT_WORK_MODEL,
    resolve_normalization_models,
)

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("params", "runtime_params", "expected"),
    [
        (
            {"model": "fixture"},
            {},
            ("fixture", DEFAULT_VERIFY_MODEL, "fixture"),
        ),
        (
            {"work_model": "stage-work", "qa_model": "stage-qa"},
            {"sota_model": "runtime-sota"},
            ("stage-work", "stage-qa", "runtime-sota"),
        ),
        (
            {},
            {"default_model": "runtime-work", "qa_model": "runtime-qa"},
            ("runtime-work", "runtime-qa", "runtime-work"),
        ),
        (
            {"escalate_model": "stage-sota"},
            {"default_model": "runtime-work", "sota_model": "runtime-sota"},
            ("runtime-work", DEFAULT_VERIFY_MODEL, "stage-sota"),
        ),
        ({}, {}, (DEFAULT_WORK_MODEL, DEFAULT_VERIFY_MODEL, DEFAULT_WORK_MODEL)),
    ],
)
def test_resolve_normalization_models_requires_explicit_escalation(
    params: dict[str, str],
    runtime_params: dict[str, str],
    expected: tuple[str, str, str],
) -> None:
    assert resolve_normalization_models(
        params=params,
        context={"runtime_params": runtime_params},
    ) == expected

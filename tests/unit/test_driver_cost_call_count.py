from __future__ import annotations

import pytest

from cine_forge.driver.engine import _cost_call_count

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (None, 0),
        ({}, 0),
        ({"model": "fixture"}, 1),
        ({"model": "fixture", "call_count": 8}, 8),
        ({"model": "code", "call_count": 0}, 0),
        (
            [
                {"model": "fixture", "call_count": 3},
                {"model": "fixture"},
            ],
            4,
        ),
    ],
)
def test_cost_call_count_preserves_aggregate_call_truth(
    payload: dict[str, object] | list[dict[str, object]] | None,
    expected: int,
) -> None:
    assert _cost_call_count(payload) == expected

"""Safety boundary for the explicit paid live-capability CLI."""

from __future__ import annotations

import pytest
from scripts import live_ai_capability_smoke

pytestmark = pytest.mark.unit


def test_live_capability_cli_refuses_implicit_paid_calls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False

    def fail_if_created():
        nonlocal called
        called = True
        raise AssertionError("service must not be created without --run-live")

    monkeypatch.setattr(
        live_ai_capability_smoke,
        "ProviderCapabilitySmokeService",
        fail_if_created,
    )

    assert live_ai_capability_smoke.main([]) == 2
    assert called is False


def test_live_capability_cli_parses_explicit_authorization() -> None:
    args = live_ai_capability_smoke._parse_args(["--run-live"])

    assert args.run_live is True

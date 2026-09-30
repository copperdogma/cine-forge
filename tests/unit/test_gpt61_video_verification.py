"""Tracked Story 226 evidence must be reproducible without ignored local output."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "benchmarks/scripts"))
verifier = importlib.import_module("verify_gpt61_video_comparison")


@pytest.mark.unit
def test_tracked_verification_needs_no_local_receipts_or_provider_calls(monkeypatch):
    monkeypatch.setattr(verifier.run, "OUT", ROOT / "output/evals/absent-story226-verifier-test")

    def reject_network(*args, **kwargs):
        raise AssertionError("Offline verification attempted a provider call")

    monkeypatch.setattr(verifier.run.provider.urllib.request, "urlopen", reject_network)
    original_result = verifier.run.RESULT.read_bytes()
    verifier.main()
    assert verifier.run.RESULT.read_bytes() == original_result
    assert not verifier.run.OUT.exists()

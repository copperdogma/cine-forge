"""Keep paid-call code identity auditable after post-run style cleanup."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "benchmarks/scripts/rejudge_video_understanding_truth_v4.py"
PROVENANCE = ROOT / "docs/evals/story-222-truth-v4-postrun-provenance.json"


def _hash(path: Path) -> dict[str, int | str]:
    data = path.read_bytes()
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


@pytest.mark.unit
def test_call_time_archives_and_post_run_scripts_have_distinct_pinned_identities() -> None:
    provenance = json.loads(PROVENANCE.read_text())
    freeze = json.loads((ROOT / provenance["original_freeze"]["path"]).read_text())
    assert _hash(ROOT / provenance["original_freeze"]["path"]) == provenance["original_freeze"]
    assert _hash(ROOT / provenance["original_evidence"]["path"]) == provenance["original_evidence"]
    assert _hash(ROOT / provenance["derived_result"]["path"]) == provenance["derived_result"]

    expected_archives = {}
    for row in provenance["archive_mapping"]:
        original = next(
            item
            for item in freeze["frozen_contract_files"]
            if item["path"] == row["original_freeze_path"]
        )
        archive = row["call_time_archive"]
        active = row["post_run_active"]
        assert _hash(ROOT / archive["path"]) == archive
        assert archive["bytes"] == original["bytes"]
        assert archive["sha256"] == original["sha256"]
        assert _hash(ROOT / active["path"]) == active
        assert active["sha256"] != original["sha256"]
        expected_archives[row["original_freeze_path"]] = archive["path"]

    spec = importlib.util.spec_from_file_location("v4_rejudge", RUNNER)
    assert spec and spec.loader
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    assert runner.CALL_TIME_ARCHIVES == expected_archives
    assert runner._check_freeze() == freeze

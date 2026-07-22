"""Registry contracts for scored evals whose reports must survive red assertions."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = REPO_ROOT / "docs" / "evals" / "registry.yaml"
REPORTS = {
    "video-understanding": "benchmarks/scripts/video_understanding_report.py",
    "previz-usefulness": "benchmarks/scripts/previz_usefulness_report.py",
    "final-render-provider-floor": (
        "benchmarks/scripts/final_render_provider_floor_report.py"
    ),
    "storyboard-generation-quality": (
        "benchmarks/scripts/storyboard_generation_quality_report.py"
    ),
}


@pytest.mark.parametrize(("eval_id", "report_path"), REPORTS.items())
def test_promptfoo_report_runs_after_pass_or_assertion_failure(
    eval_id: str,
    report_path: str,
) -> None:
    registry = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    entry = next(item for item in registry["evals"] if item["id"] == eval_id)
    command = entry["command"]
    report_name = Path(report_path).name

    assert entry["script"] == report_path
    assert "promptfoo eval" in command
    assert "--output" in command
    assert "status=$?" in command
    assert "$status -ne 100" in command
    assert f"{report_name} " in command
    assert command.index("promptfoo eval") < command.index(report_name)
    assert command.rstrip().endswith("exit $status")

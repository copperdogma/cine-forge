from __future__ import annotations

from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_ROOT = REPO_ROOT / "benchmarks" / "tasks"
FRAME_TASKS = (
    "video-understanding.yaml",
    "previz-usefulness.yaml",
    "final-render-provider-floor.yaml",
)


def _load_task(name: str) -> dict:
    return yaml.safe_load((TASK_ROOT / name).read_text())


@pytest.mark.unit
@pytest.mark.parametrize("task_name", FRAME_TASKS)
def test_frame_tasks_use_opaque_evaluation_ids(task_name: str) -> None:
    task = _load_task(task_name)
    tests = task["tests"]

    assert tests
    for test in tests:
        vars_data = test["vars"]
        evaluation_id = vars_data.get("evaluation_id", "")
        semantic_clip_id = vars_data.get("clip_id", "")
        assert evaluation_id
        assert evaluation_id != semantic_clip_id
        assert semantic_clip_id not in evaluation_id


@pytest.mark.unit
@pytest.mark.parametrize("task_name", FRAME_TASKS)
def test_frame_judges_match_the_subject_modality(task_name: str) -> None:
    task = _load_task(task_name)
    assertions = task["tests"][0]["assert"]
    rubric = next(item["value"] for item in assertions if item["type"] == "llm-rubric")
    normalized = rubric.lower()

    assert "ordered jpeg" in normalized
    assert "opaque identifier" in normalized
    assert "ignore every" in normalized and "audio" in normalized
    assert "pass only at score >= 0.8" in normalized


@pytest.mark.unit
def test_google_frame_provider_configs_omit_sampling_controls() -> None:
    task = _load_task("video-understanding.yaml")
    google_configs = [
        provider["config"]
        for provider in task["providers"]
        if provider["config"]["provider"] == "google"
    ]

    assert google_configs
    for config in google_configs:
        assert "temperature" not in config
        assert "top_p" not in config
        assert "top_k" not in config


@pytest.mark.unit
def test_video_provider_records_the_repaired_frame_packet_prompt_version() -> None:
    task = _load_task("video-understanding.yaml")

    assert {
        provider["config"]["prompt_version"] for provider in task["providers"]
    } == {"video-understanding-frame-packet-v2"}

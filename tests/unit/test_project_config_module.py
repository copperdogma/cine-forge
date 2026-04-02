from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from cine_forge.artifacts import ArtifactStore
from cine_forge.modules.ingest.project_config_v1.main import run_module
from cine_forge.schemas import ArtifactMetadata


def _canonical_script(title: str, text: str) -> dict[str, Any]:
    return {
        "title": title,
        "script_text": text,
        "line_count": text.count("\n") + 1,
        "scene_count": 1,
        "normalization": {
            "source_format": "screenplay",
            "strategy": "passthrough_cleanup",
            "inventions": [],
            "assumptions": [],
            "overall_confidence": 0.9,
            "rationale": "fixture",
        },
    }


def _scene_index(
    minutes: float,
    characters: list[str],
    locations: list[str],
    total_scenes: int,
    entries: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "total_scenes": total_scenes,
        "unique_locations": locations,
        "unique_characters": characters,
        "estimated_runtime_minutes": minutes,
        "scenes_passed_qa": total_scenes,
        "scenes_need_review": 0,
        "entries": entries or [],
    }


def _save_project_config(
    *,
    tmp_path: Path,
    project_dir: Path,
    source: str = "hybrid",
    config_file: str | None = None,
    confirmed: bool = True,
) -> None:
    artifact = run_module(
        inputs={
            "normalize": _canonical_script("Original", "INT. ROOM - NIGHT\nMARA\nGo."),
            "extract": _scene_index(8.0, ["MARA"], ["ROOM"], 8),
        },
        params={"model": "mock", "qa_model": "mock", "accept_config": confirmed},
        context={
            "run_id": "seed",
            "stage_id": "config",
            "runtime_params": {"accept_config": confirmed},
        },
    )["artifacts"][0]

    metadata = dict(artifact["metadata"])
    annotations = dict(metadata.get("annotations", {}))
    annotations["config_file"] = config_file
    metadata["annotations"] = annotations
    metadata["source"] = source
    metadata["producing_module"] = "project_config_v1"

    store = ArtifactStore(project_dir=project_dir)
    store.save_artifact(
        artifact_type="project_config" if confirmed else "draft_project_config",
        entity_id="project",
        data=artifact["data"],
        metadata=ArtifactMetadata.model_validate(metadata),
    )


@pytest.mark.unit
def test_mock_detection_feature_length_classification(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = run_module(
        inputs={
            "normalize": _canonical_script("Epic", "INT. LAB - NIGHT\nMARA\nMove."),
            "extract": _scene_index(95.0, ["MARA", "JON", "DEA"], ["LAB"], 90),
        },
        params={"model": "mock", "qa_model": "mock", "accept_config": True},
        context={"run_id": "unit", "stage_id": "config", "runtime_params": {}},
    )
    artifact = result["artifacts"][0]
    assert artifact["data"]["format"] == "feature"
    assert artifact["data"]["estimated_duration_minutes"] == 95.0
    assert artifact["data"]["confirmed"] is True


@pytest.mark.unit
def test_mock_detection_short_script_and_comedy_signal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = run_module(
        inputs={
            "normalize": _canonical_script(
                "Short", "INT. CAFE - DAY\nMARA\nThat joke lands.\nEveryone laughs."
            ),
            "extract": _scene_index(5.0, ["MARA", "JON"], ["CAFE"], 5),
        },
        params={"model": "mock", "qa_model": "mock", "accept_config": True},
        context={"run_id": "unit", "stage_id": "config", "runtime_params": {}},
    )
    data = result["artifacts"][0]["data"]
    assert data["format"] == "short_film"
    assert "comedy" in data["genre"]


@pytest.mark.unit
def test_mock_detection_splits_primary_and_supporting_characters(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = run_module(
        inputs={
            "normalize": _canonical_script(
                "Cast",
                (
                    "INT. ROOM - NIGHT\n"
                    "MARA\nGo.\n"
                    "JON\nNow.\n"
                    "MARA\nAgain.\n"
                    "EXT. STREET - DAY\n"
                    "DEA\nWatch.\n"
                ),
            ),
            "extract": _scene_index(
                20.0,
                ["MARA", "JON", "DEA", "TECH"],
                ["ROOM"],
                18,
                entries=[
                    {"characters_present": ["MARA", "JON"]},
                    {"characters_present": ["MARA", "DEA"]},
                    {"characters_present": ["MARA", "JON"]},
                ],
            ),
        },
        params={"model": "mock", "qa_model": "mock", "accept_config": True},
        context={"run_id": "unit", "stage_id": "config", "runtime_params": {}},
    )
    data = result["artifacts"][0]["data"]
    assert data["primary_characters"] == ["MARA", "JON"]
    assert data["supporting_characters"] == ["DEA", "TECH"]
    assert "scene*2 + dialogue" in data["detection_details"]["primary_characters"]["rationale"]


@pytest.mark.unit
def test_mock_detection_filters_pronoun_and_noise_characters(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = run_module(
        inputs={
            "normalize": _canonical_script(
                "Noise",
                (
                    "INT. ROOM - NIGHT\n"
                    "MARINER\nGo.\n"
                    "ROSE\nNow.\n"
                    "HE\nNo.\n"
                    "IT\nWait.\n"
                ),
            ),
            "extract": _scene_index(
                12.0,
                ["MARINER", "ROSE", "HE", "IT", "GO", "ENDFLASHBACK."],
                ["ROOM"],
                10,
                entries=[
                    {"characters_present": ["MARINER", "ROSE", "HE"]},
                    {"characters_present": ["MARINER", "IT"]},
                ],
            ),
        },
        params={"model": "mock", "qa_model": "mock", "accept_config": True},
        context={"run_id": "unit", "stage_id": "config", "runtime_params": {}},
    )
    data = result["artifacts"][0]["data"]
    assert "MARINER" in data["primary_characters"] + data["supporting_characters"]
    assert "ROSE" in data["primary_characters"] + data["supporting_characters"]
    assert "HE" not in data["primary_characters"] + data["supporting_characters"]
    assert "IT" not in data["primary_characters"] + data["supporting_characters"]
    assert "GO" not in data["primary_characters"] + data["supporting_characters"]


@pytest.mark.unit
def test_mock_detection_filters_derivative_noise_names(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = run_module(
        inputs={
            "normalize": _canonical_script(
                "Derivative",
                "INT. ROOM - NIGHT\nMARINER\nGo.\nROSE\nNow.\n",
            ),
            "extract": _scene_index(
                10.0,
                ["MARINER", "ROSE", "ROSESWALLOWS", "MARINERAIRTAG"],
                ["ROOM"],
                8,
                entries=[
                    {"characters_present": ["MARINER", "ROSESWALLOWS"]},
                    {"characters_present": ["ROSE", "MARINERAIRTAG"]},
                ],
            ),
        },
        params={"model": "mock", "qa_model": "mock", "accept_config": True},
        context={"run_id": "unit", "stage_id": "config", "runtime_params": {}},
    )
    merged = result["artifacts"][0]["data"]["primary_characters"] + result["artifacts"][0]["data"][
        "supporting_characters"
    ]
    assert "MARINER" in merged
    assert "ROSE" in merged
    assert "ROSESWALLOWS" not in merged
    assert "MARINERAIRTAG" not in merged


@pytest.mark.unit
def test_config_file_overrides_values_and_marks_user_specified(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "edited.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "title": "Edited Project",
                "aspect_ratio": "2.39:1",
                "budget_cap_usd": 123.45,
            }
        ),
        encoding="utf-8",
    )

    result = run_module(
        inputs={
            "normalize": _canonical_script("Original", "INT. ROOM - NIGHT\nMARA\nGo."),
            "extract": _scene_index(8.0, ["MARA"], ["ROOM"], 8),
        },
        params={"model": "mock", "qa_model": "mock"},
        context={
            "run_id": "unit",
            "stage_id": "config",
            "runtime_params": {"config_file": str(config_path)},
        },
    )
    data = result["artifacts"][0]["data"]
    assert data["title"] == "Edited Project"
    assert data["aspect_ratio"] == "2.39:1"
    assert data["budget_cap_usd"] == 123.45
    assert data["detection_details"]["title"]["source"] == "user_specified"
    assert data["confirmed"] is True


@pytest.mark.unit
def test_unconfirmed_config_sets_pause_reason_and_writes_draft(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = run_module(
        inputs={
            "normalize": _canonical_script("Original", "INT. ROOM - NIGHT\nMARA\nGo."),
            "extract": _scene_index(8.0, ["MARA"], ["ROOM"], 8),
        },
        params={"model": "mock", "qa_model": "mock"},
        context={"run_id": "unit", "stage_id": "config", "runtime_params": {}},
    )
    artifact = result["artifacts"][0]
    assert artifact["artifact_type"] == "draft_project_config"
    assert artifact["schema_name"] == "project_config"
    assert artifact["data"]["confirmed"] is False
    assert "pause_reason" in result
    assert (tmp_path / "output" / "project" / "draft_config.yaml").exists()


@pytest.mark.unit
def test_accept_config_runtime_flag_confirms_draft(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    result = run_module(
        inputs={
            "normalize": _canonical_script("Original", "INT. ROOM - NIGHT\nMARA\nGo."),
            "extract": _scene_index(8.0, ["MARA"], ["ROOM"], 8),
        },
        params={"model": "mock", "qa_model": "mock", "accept_config": False},
        context={
            "run_id": "unit",
            "stage_id": "config",
            "runtime_params": {"accept_config": True},
        },
    )
    assert result["artifacts"][0]["artifact_type"] == "project_config"
    assert result["artifacts"][0]["data"]["confirmed"] is True


@pytest.mark.unit
def test_refresh_existing_only_skips_without_confirmed_latest_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    project_dir = tmp_path / "project"

    result = run_module(
        inputs={
            "normalize": _canonical_script("Original", "INT. ROOM - NIGHT\nMARA\nGo."),
            "extract": _scene_index(8.0, ["MARA"], ["ROOM"], 8),
        },
        params={
            "model": "mock",
            "qa_model": "mock",
            "accept_config": True,
            "refresh_existing_only": True,
        },
        context={
            "run_id": "unit",
            "stage_id": "config",
            "project_dir": str(project_dir),
            "runtime_params": {"accept_config": True},
        },
    )

    assert result["artifacts"] == []
    assert result["model"] == "code"


@pytest.mark.unit
def test_refresh_existing_only_skips_user_owned_latest_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    project_dir = tmp_path / "project"
    _save_project_config(
        tmp_path=tmp_path,
        project_dir=project_dir,
        source="human",
    )

    result = run_module(
        inputs={
            "normalize": _canonical_script("Original", "INT. ROOM - NIGHT\nMARA\nGo."),
            "extract": _scene_index(8.0, ["MARA", "JON"], ["ROOM"], 8),
        },
        params={
            "model": "mock",
            "qa_model": "mock",
            "accept_config": True,
            "refresh_existing_only": True,
            "skip_if_latest_user_owned": True,
        },
        context={
            "run_id": "unit",
            "stage_id": "config",
            "project_dir": str(project_dir),
            "runtime_params": {"accept_config": True},
        },
    )

    assert result["artifacts"] == []
    assert result["model"] == "code"


@pytest.mark.unit
def test_refresh_existing_only_rebuilds_system_owned_latest_config(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    project_dir = tmp_path / "project"
    _save_project_config(
        tmp_path=tmp_path,
        project_dir=project_dir,
        source="hybrid",
    )

    result = run_module(
        inputs={
            "normalize": _canonical_script("Original", "INT. ROOM - NIGHT\nMARA\nGo."),
            "extract": _scene_index(8.0, ["MARA", "JON"], ["ROOM"], 8),
        },
        params={
            "model": "mock",
            "qa_model": "mock",
            "accept_config": True,
            "refresh_existing_only": True,
            "skip_if_latest_user_owned": True,
        },
        context={
            "run_id": "unit",
            "stage_id": "config",
            "project_dir": str(project_dir),
            "runtime_params": {"accept_config": True},
        },
    )

    assert len(result["artifacts"]) == 1
    assert result["artifacts"][0]["artifact_type"] == "project_config"

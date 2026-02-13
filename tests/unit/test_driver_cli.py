from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.driver import __main__ as driver_cli


@pytest.mark.unit
def test_driver_main_merges_params_file_and_cli_overrides(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    captured: dict[str, object] = {}
    params_file = tmp_path / "params.yaml"
    params_file.write_text(
        "\n".join(
            [
                "input_file: tests/fixtures/sample_screenplay.fountain",
                "default_model: mock",
                "accept_config: false",
            ]
        ),
        encoding="utf-8",
    )

    class _FakeEngine:
        def __init__(self, workspace_root: Path) -> None:
            captured["workspace_root"] = workspace_root

        def run(
            self,
            recipe_path: Path,
            run_id: str | None = None,
            dry_run: bool = False,
            start_from: str | None = None,
            force: bool = False,
            instrument: bool = False,
            runtime_params: dict[str, object] | None = None,
        ) -> dict[str, object]:
            captured["recipe_path"] = recipe_path
            captured["run_id"] = run_id
            captured["dry_run"] = dry_run
            captured["start_from"] = start_from
            captured["force"] = force
            captured["instrument"] = instrument
            captured["runtime_params"] = runtime_params or {}
            return {"stages": {"only": {"artifact_refs": []}}}

    monkeypatch.setattr(driver_cli, "DriverEngine", _FakeEngine)
    monkeypatch.setattr(
        "sys.argv",
        [
            "driver",
            "--recipe",
            "configs/recipes/recipe-mvp-ingest.yaml",
            "--run-id",
            "cli-params-test",
            "--params-file",
            str(params_file),
            "--param",
            "accept_config=true",
            "--param",
            "default_model=fixture",
        ],
    )

    driver_cli.main()

    runtime_params = captured["runtime_params"]
    assert runtime_params["input_file"] == "tests/fixtures/sample_screenplay.fountain"
    assert runtime_params["accept_config"] is True
    assert runtime_params["default_model"] == "fixture"
    assert captured["run_id"] == "cli-params-test"
    assert captured["recipe_path"] == Path("configs/recipes/recipe-mvp-ingest.yaml")


@pytest.mark.unit
def test_load_params_file_requires_mapping(tmp_path: Path) -> None:
    params_file = tmp_path / "params.yaml"
    params_file.write_text("- one\n- two\n", encoding="utf-8")

    with pytest.raises(ValueError, match="top-level mapping"):
        driver_cli._load_params_file(str(params_file))

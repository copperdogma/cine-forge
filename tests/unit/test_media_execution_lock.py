"""Offline driver admission and output-persistence serialization checks."""

from __future__ import annotations

import json

import pytest

from cine_forge.driver.engine import DriverEngine
from cine_forge.driver.media_execution_lock import media_execution_lock
from cine_forge.services import media_plan_execution
from cine_forge.services.media_plan_execution import checked_execution
from tests.unit.test_media_execution_plans import _metadata, _save

pytestmark = pytest.mark.unit


@pytest.fixture
def media_case(tmp_path):
    from tests.unit.test_media_execution_plans import media_case as shared_fixture

    return shared_fixture.__wrapped__(tmp_path)


def _recipe(case):
    return case["workspace_root"] / "configs/recipes/recipe-ai-previz-generation.yaml"


def _runtime(case, saved):
    prepared = checked_execution(
        **{k: case[k] for k in ("workspace_root", "project_dir", "project_id")},
        ref=saved.plan_ref,
    )
    return prepared.runtime | {
        "media_execution_plan_ref": saved.plan_ref.model_dump(mode="json"),
    }


def _run(engine, case, run_id, runtime, **kwargs):
    return engine.run(
        recipe_path=_recipe(case),
        run_id=run_id,
        runtime_params=runtime,
        start_from="ai_previz",
        end_at="validate_media",
        **kwargs,
    )


def test_distinct_approved_workers_serialize_until_outputs_and_final_state_are_persisted(
    media_case,
    monkeypatch,
):
    first, second = _save(media_case), _save(media_case)
    assert first.plan_ref != second.plan_ref
    runtime_first, runtime_second = _runtime(media_case, first), _runtime(media_case, second)
    engines = [
        DriverEngine(media_case["workspace_root"], media_case["project_dir"]) for _ in range(2)
    ]
    calls = []
    original_guard = media_plan_execution.validate_media_run_envelope

    def guard(**kwargs):
        calls.append(kwargs["run_id"])
        return original_guard(**kwargs)

    monkeypatch.setattr(media_plan_execution, "validate_media_run_envelope", guard)
    versions = []
    first_write = engines[0]._write_run_state
    terminal_probe = []

    def write_with_contention_probe(path, state):
        first_write(path, state)
        if state.get("finished_at"):
            with pytest.raises(ValueError, match="Another media run is executing"):
                _run(engines[1], media_case, "run-contender", runtime_second)
            terminal_probe.append(True)
            # Rejection happened before consuming the second approval.
            assert calls == ["run-first"]

    monkeypatch.setattr(engines[0], "_write_run_state", write_with_contention_probe)

    def execute_stub(engine, **kwargs):
        ref = kwargs["runtime_params"]["media_execution_plan_ref"]
        from cine_forge.schemas import ArtifactRef

        snapshot = checked_execution(
            **{k: media_case[k] for k in ("workspace_root", "project_dir", "project_id")},
            ref=ArtifactRef.model_validate(ref),
        )
        unit = snapshot.units[media_case["clip"].clip_id]
        versions.append(unit.video_ref.version)
        # Mechanical artifacts only: prove allocation/persistence, not media quality.
        for kind in ("ai_previz_prompt", "ai_previz_video"):
            written = engine.store.save_artifact(kind, unit.entity_id, {}, _metadata())
            assert written.version == unit.video_ref.version
        state_path = (
            media_case["workspace_root"] / "output/runs" / kwargs["run_id"] / "run_state.json"
        )
        state = {
            **json.loads(state_path.read_text()),
            "run_id": kwargs["run_id"],
            "recipe_id": "ai_previz_generation",
            "stages": {"ai_previz": {"status": "done"}},
            "finished_at": 1,
            "runtime_params": kwargs["runtime_params"],
        }
        engine._write_run_state(
            media_case["workspace_root"] / "output/runs" / kwargs["run_id"] / "run_state.json",
            state,
        )
        return state

    for engine in engines:
        monkeypatch.setattr(
            engine, "_run_recipe", lambda _engine=engine, **kw: execute_stub(_engine, **kw)
        )
    _run(engines[0], media_case, "run-first", runtime_first)
    assert terminal_probe == [True]
    assert calls == ["run-first"]
    claim_folder = media_case["project_dir"] / "media_plan_claims"
    assert len(list(claim_folder.glob("*.started"))) == 1
    rejected = json.loads(
        (media_case["workspace_root"] / "output/runs/run-contender/run_state.json").read_text()
    )
    assert rejected["stages"]["ai_previz"]["status"] == "failed"
    _run(engines[1], media_case, "run-second", runtime_second)
    assert calls == ["run-first", "run-second"]
    assert versions == [1, 2]
    assert len(list(claim_folder.glob("*.started"))) == 2


def test_legacy_media_driver_uses_the_same_project_lock(media_case, monkeypatch):
    engine = DriverEngine(media_case["workspace_root"], media_case["project_dir"])
    observed = []

    def legacy_stub(**kwargs):
        with pytest.raises(ValueError, match="Another media run is executing"):
            with media_execution_lock(
                project_dir=media_case["project_dir"],
                recipe_path=_recipe(media_case),
                start_from="ai_previz",
                end_at="ai_previz",
                dry_run=False,
                run_id="competing-approved",
            ):
                pytest.fail("Legacy driver must hold the media output lock")
        observed.append(True)
        return {"mechanical_stub": True}

    monkeypatch.setattr(engine, "_run_recipe", legacy_stub)
    _run(engine, media_case, "legacy-run", {})
    assert observed == [True]


@pytest.mark.parametrize("kind", ["preparation", "dry_run"])
def test_preparation_and_dry_run_do_not_contend_with_media_execution(
    media_case,
    monkeypatch,
    kind,
):
    engine = DriverEngine(media_case["workspace_root"], media_case["project_dir"])
    monkeypatch.setattr(engine, "_run_recipe", lambda **kw: {"entered": True})
    with media_execution_lock(
        project_dir=media_case["project_dir"],
        recipe_path=_recipe(media_case),
        start_from="ai_previz",
        end_at="ai_previz",
        dry_run=False,
        run_id="active-media",
    ):
        result = engine.run(
            recipe_path=_recipe(media_case),
            run_id=f"run-{kind}",
            runtime_params={},
            start_from="timeline" if kind == "preparation" else "ai_previz",
            end_at="render_clip_planning" if kind == "preparation" else "ai_previz",
            dry_run=kind == "dry_run",
        )
    assert result == {"entered": True}


def test_project_lock_releases_after_worker_failure(media_case, monkeypatch):
    engine = DriverEngine(media_case["workspace_root"], media_case["project_dir"])

    def failed_worker(**kwargs):
        raise ValueError("mechanical persistence failure")

    monkeypatch.setattr(engine, "_run_recipe", failed_worker)
    with pytest.raises(ValueError, match="mechanical persistence failure"):
        _run(engine, media_case, "failed-worker", {})
    with media_execution_lock(
        project_dir=media_case["project_dir"],
        recipe_path=_recipe(media_case),
        start_from="ai_previz",
        end_at="ai_previz",
        dry_run=False,
        run_id="after-failure",
    ):
        assert (media_case["project_dir"] / ".media_execution.lock").read_text() == "after-failure"

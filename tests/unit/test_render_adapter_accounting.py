"""Deterministic adapter accounting regressions; synthetic prices are not live quotes."""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from cine_forge.execution_errors import ModuleCostError
from cine_forge.modules.generation.render_adapter_v1 import main, render_unit, unit_prompt
from cine_forge.modules.generation.render_adapter_v1.accounting import record_media_receipts
from cine_forge.modules.generation.render_adapter_v1.prompting import compile_render_prompt
from cine_forge.schemas.media_cost import CostReceipt
from tests.render_fixtures import seed_render_project
from tests.storyboard_fixtures import seed_storyboard_project

FIXTURE = Path(__file__).parents[1] / "fixtures" / "render_accounting.json"


@pytest.mark.unit
def test_media_receipt_identity_rejects_changed_amount_but_dedupes_exact_copy():
    raw = json.loads(FIXTURE.read_text())["video_receipt"]
    receipt = CostReceipt.model_validate(raw)
    rows = []
    for _ in range(2):
        record_media_receipts(rows, [receipt], scene_id="scene_001", entity_id="unit_001")
    assert len(rows) == 1
    raw["cost"]["estimated_cost_usd"] += .1
    conflicting = CostReceipt.model_validate(raw)
    with pytest.raises(ValueError, match="conflicting cost receipt"):
        record_media_receipts(rows, [conflicting], scene_id="scene_001", entity_id="unit_001")
    assert rows[0].cost.estimated_cost_usd == receipt.cost.estimated_cost_usd


def _compiler(**kwargs):
    print("fixture compiler called")
    kwargs["compiler_model"] = "mock"
    draft, _, categories = compile_render_prompt(**kwargs)
    cost = json.loads(FIXTURE.read_text())["compiler_cost"]
    return draft, cost, categories


def _video_result(engine_pack, number=1):
    print("fixture video returned", number)
    raw = json.loads(FIXTURE.read_text())["video_receipt"]
    raw["receipt_id"] = f"fixture-video-{number}"
    raw["provider_job_id"] = f"fixture-job-{number}"
    raw["model"] = engine_pack.target_model
    raw["cost"]["model"] = engine_pack.target_model
    return SimpleNamespace(
        video_bytes=b"synthetic media; not quality evidence",
        media_type="video/mp4",
        model_used=engine_pack.target_model,
        request_id=f"fixture-job-{number}",
        provider_job_id=f"fixture-job-{number}",
        cost_receipts=[CostReceipt.model_validate(raw)],
    )


@pytest.mark.unit
def test_render_success_includes_video_receipt_once(tmp_path, monkeypatch):
    seeded = seed_render_project(tmp_path, include_keyframe=False, include_scene_image=False)
    monkeypatch.setattr(unit_prompt, "compile_render_prompt", _compiler)
    monkeypatch.setattr(
        render_unit, "generate_video", lambda **kw: _video_result(kw["engine_pack"])
    )
    result = main.run_module(
        inputs=seeded["inputs"],
        params={"engine_pack_id": "xai_grok_imagine_video"},
        context={"project_dir": str(seeded["project_dir"])},
    )
    assert result["artifacts"], "render completed through compiler and transport"
    assert result["cost"]["estimated_cost_usd"] == pytest.approx(0.412)
    video = next(a for a in result["artifacts"] if a["artifact_type"] == "generated_video")
    assert video["data"]["cost"]["estimated_cost_usd"] == pytest.approx(0.412)
    assert len(result["cost_receipts"]) == 2
    assert video["data"]["cost_is_complete"] is True
    assert video["data"]["cost_receipts"] == result["cost_receipts"]


@pytest.mark.unit
def test_compiler_receipt_survives_video_failure(tmp_path, monkeypatch):
    seeded = seed_render_project(tmp_path, include_keyframe=False, include_scene_image=False)
    monkeypatch.setattr(unit_prompt, "compile_render_prompt", _compiler)

    def fail(**kwargs):
        print("fixture video failed after compiler")
        raise RuntimeError("synthetic transport failure")

    monkeypatch.setattr(render_unit, "generate_video", fail)
    with pytest.raises(ModuleCostError, match="synthetic transport failure") as caught:
        main.run_module(
            inputs=seeded["inputs"],
            params={"engine_pack_id": "xai_grok_imagine_video"},
            context={"project_dir": str(seeded["project_dir"])},
        )
    assert len(caught.value.cost_receipts) == 1
    assert caught.value.cost_receipts[0].component == "compiler"
    assert caught.value.cost_receipts[0].cost.estimated_cost_usd == pytest.approx(0.012)


@pytest.mark.unit
def test_partial_failure_retains_compilers_and_successful_video(tmp_path, monkeypatch):
    seeded = seed_storyboard_project(tmp_path, scene_count=2)
    monkeypatch.setattr(unit_prompt, "compile_render_prompt", _compiler)
    calls = []

    def generate(**kwargs):
        calls.append(kwargs)
        print("fixture video called", len(calls))
        if len(calls) == 2:
            raise RuntimeError("synthetic second-scene failure")
        return _video_result(kwargs["engine_pack"], len(calls))

    monkeypatch.setattr(render_unit, "generate_video", generate)
    with pytest.raises(ModuleCostError, match="preserved 1 successful") as caught:
        main.run_module(
            inputs=seeded["inputs"],
            params={"engine_pack_id": "xai_grok_imagine_video"},
            context={"project_dir": str(seeded["project_dir"])},
        )
    receipts = caught.value.cost_receipts
    assert [r.component for r in receipts] == ["compiler", "video", "compiler"]
    assert sum(r.cost.estimated_cost_usd for r in receipts) == pytest.approx(0.424)
    assert len({r.receipt_id for r in receipts}) == 3


@pytest.mark.unit
def test_previz_includes_video_cost_and_provenance(tmp_path, monkeypatch):
    seeded = seed_render_project(tmp_path, include_keyframe=False, include_scene_image=False)
    monkeypatch.setattr(
        unit_prompt,
        "compile_render_prompt",
        lambda **kw: pytest.fail("previz is deterministic"),
    )
    monkeypatch.setattr(
        render_unit, "generate_video", lambda **kw: _video_result(kw["engine_pack"])
    )
    result = main.run_module(
        inputs=seeded["inputs"],
        params={"prompt_mode": "ai_previz"},
        context={"project_dir": str(seeded["project_dir"])},
    )
    video = next(a for a in result["artifacts"] if a["artifact_type"] == "ai_previz_video")
    assert result["cost"]["estimated_cost_usd"] == pytest.approx(0.4)
    assert video["data"]["cost"]["estimated_cost_usd"] == pytest.approx(0.4)
    assert video["data"]["preview_provenance"]["estimated_cost_usd"] == pytest.approx(0.4)
    receipts = [
        CostReceipt.model_validate(r) for r in video["metadata"]["annotations"]["cost_receipts"]
    ]
    assert len(receipts) == 1 and receipts[0].component == "video"
    assert video["data"]["cost_is_complete"] is True
    assert video["data"]["cost_receipts"] == result["cost_receipts"]


@pytest.mark.unit
def test_compiler_receipt_survives_prompt_finalization_failure(tmp_path, monkeypatch):
    seeded = seed_render_project(tmp_path, include_keyframe=False, include_scene_image=False)
    monkeypatch.setattr(unit_prompt, "compile_render_prompt", _compiler)

    def fail(**kwargs):
        raise ValueError("synthetic finalization failure")

    monkeypatch.setattr(unit_prompt, "_finalize_prompt_sections", fail)
    monkeypatch.setattr(
        render_unit, "generate_video", lambda **kw: pytest.fail("must not generate")
    )
    with pytest.raises(ModuleCostError, match="finalization failure") as caught:
        main.run_module(
            inputs=seeded["inputs"],
            params={"engine_pack_id": "xai_grok_imagine_video"},
            context={"project_dir": str(seeded["project_dir"])},
        )
    assert len(caught.value.cost_receipts) == 1
    assert caught.value.cost_receipts[0].cost.estimated_cost_usd == pytest.approx(0.012)


@pytest.mark.unit
def test_video_receipt_survives_media_persistence_failure(tmp_path, monkeypatch):
    seeded = seed_render_project(tmp_path, include_keyframe=False, include_scene_image=False)
    monkeypatch.setattr(unit_prompt, "compile_render_prompt", _compiler)
    monkeypatch.setattr(
        render_unit, "generate_video", lambda **kw: _video_result(kw["engine_pack"])
    )
    impossible_dir = tmp_path / "existing-file"
    impossible_dir.write_text("directory creation must fail")
    monkeypatch.setattr(render_unit, "render_media_dir", lambda *a, **kw: impossible_dir)
    with pytest.raises(ModuleCostError) as caught:
        main.run_module(
            inputs=seeded["inputs"],
            params={"engine_pack_id": "xai_grok_imagine_video"},
            context={"project_dir": str(seeded["project_dir"])},
        )
    assert [r.component for r in caught.value.cost_receipts] == ["compiler", "video"]
    assert sum(r.cost.estimated_cost_usd for r in caught.value.cost_receipts) == pytest.approx(
        0.412
    )


@pytest.mark.unit
@pytest.mark.parametrize("safe_media", [True, False])
def test_uncertain_cost_stops_remaining_clips_and_scenes(tmp_path, monkeypatch, safe_media):
    from cine_forge.ai.video import VideoGenerationError
    from cine_forge.modules.generation.render_clip_plan_v1.main import run_module as plan_clips

    seeded = seed_storyboard_project(tmp_path, scene_count=2)
    planning_inputs = dict(seeded["inputs"])
    for artifact_type in ("scene_index", "timeline"):
        ref = seeded["store"].latest_ref(artifact_type, "project")
        planning_inputs[artifact_type] = seeded["store"].load_artifact(ref).data
    planned = plan_clips(
        inputs=planning_inputs,
        params={"planner_model": "mock", "engine_pack_id": "google_veo31"},
        context={"project_dir": str(seeded["project_dir"])},
    )
    seeded["inputs"]["render_clip_plan"] = [a["data"] for a in planned["artifacts"]]
    assert len(seeded["inputs"]["render_clip_plan"][0]["clips"]) > 1
    calls = {"compiler": 0, "video": 0}

    def compile_counted(**kwargs):
        calls["compiler"] += 1
        return _compiler(**kwargs)

    def generate(**kwargs):
        calls["video"] += 1
        receipt = CostReceipt(
            receipt_id="fixture-uncertain-job",
            component="video",
            model=kwargs["engine_pack"].target_model,
            status="uncertain",
            provider_job_id="retained-job",
            reason="Synthetic unresolved bill",
        )
        if not safe_media:
            raise VideoGenerationError(
                "Synthetic accepted-job poll failure", cost_receipts=[receipt]
            )
        result = _video_result(kwargs["engine_pack"])
        result.cost_receipts = [receipt]
        return result

    announced = []
    monkeypatch.setattr(unit_prompt, "compile_render_prompt", compile_counted)
    monkeypatch.setattr(render_unit, "generate_video", generate)
    with pytest.raises(ModuleCostError, match="unresolved") as caught:
        main.run_module(
            inputs=seeded["inputs"],
            params={"engine_pack_id": "xai_grok_imagine_video"},
            context={
                "project_dir": str(seeded["project_dir"]),
                "announce_artifact": announced.append,
            },
        )
    assert calls == {"compiler": 1, "video": 1}
    receipts = caught.value.cost_receipts
    assert [r.component for r in receipts] == ["compiler", "video"]
    assert receipts[-1].status == "uncertain" and receipts[-1].provider_job_id == "retained-job"
    videos = [a for a in announced if a["artifact_type"] == "generated_video"]
    assert len(videos) == int(safe_media)
    if safe_media:
        assert (seeded["project_dir"] / videos[0]["data"]["video"]["relative_path"]).exists()
        assert videos[0]["metadata"]["annotations"]["cost_is_complete"] is False
        assert videos[0]["data"]["cost_is_complete"] is False
        assert videos[0]["data"]["cost_receipts"][-1]["status"] == "uncertain"
        assert videos[0]["data"]["preview_provenance"]["estimated_cost_usd"] is None
        assert videos[0]["data"]["cost"]["estimated_cost_usd"] == pytest.approx(0.012)
        assert any("Media cost is incomplete" in note for note in videos[0]["data"]["notes"])


@pytest.mark.unit
def test_missing_video_receipts_fail_with_explicit_uncertainty(tmp_path, monkeypatch):
    seeded = seed_render_project(tmp_path, include_keyframe=False, include_scene_image=False)
    monkeypatch.setattr(unit_prompt, "compile_render_prompt", _compiler)

    def unaccounted(**kwargs):
        result = _video_result(kwargs["engine_pack"])
        result.cost_receipts = []
        return result

    monkeypatch.setattr(render_unit, "generate_video", unaccounted)
    with pytest.raises(ModuleCostError, match="unresolved") as caught:
        main.run_module(
            inputs=seeded["inputs"],
            params={"engine_pack_id": "xai_grok_imagine_video"},
            context={"project_dir": str(seeded["project_dir"])},
        )
    assert caught.value.cost_receipts[-1].status == "uncertain"
    assert "without any cost receipt" in caught.value.cost_receipts[-1].reason


@pytest.mark.unit
@pytest.mark.parametrize("pack", ["openai_sora2", "google_veo31"])
def test_retired_video_targets_fail_before_compiler_or_media(tmp_path, monkeypatch, pack):
    seeded = seed_render_project(tmp_path, include_keyframe=False, include_scene_image=False)
    monkeypatch.setattr(
        unit_prompt, "compile_render_prompt", lambda **kw: pytest.fail("paid compiler")
    )
    monkeypatch.setattr(render_unit, "generate_video", lambda **kw: pytest.fail("paid media"))
    with pytest.raises(ValueError, match="unavailable"):
        main.run_module(
            inputs=seeded["inputs"],
            params={"engine_pack_id": pack},
            context={"project_dir": str(seeded["project_dir"])},
        )


@pytest.mark.unit
def test_backfill_work_check_is_read_only_and_allows_existing_selection(tmp_path):
    from cine_forge.schemas import Scene
    from cine_forge.schemas.design_study import DesignStudyState
    from cine_forge.services.design_study_backfill import DefaultDesignStudyBackfillService
    from cine_forge.services.design_study_backfill_store import bible_dir, write_design_study_state
    from tests.storyboard_fixtures import metadata

    seeded = seed_render_project(tmp_path, include_keyframe=False, include_scene_image=False)
    store = seeded["store"]
    scene_ref = store.latest_ref("scene", "scene_001")
    scene = Scene.model_validate(store.load_artifact(scene_ref).data)
    # Existing refs plus targets with no master definition need no new image generation.
    service = DefaultDesignStudyBackfillService(seeded["project_dir"])
    assert service.generation_required(scene) is False
    store.save_bible_entry(
        entity_type="character",
        entity_id="mara",
        display_name="Mara",
        files=[
            {
                "filename": "master.json",
                "purpose": "master_definition",
                "version": 1,
                "provenance": "system",
            }
        ],
        data_files={"master.json": '{"name":"Mara"}'},
        metadata=metadata("accounting fixture"),
        visual_reference_image=None,
    )
    assert service.generation_required(scene) is True
    selected = bible_dir(seeded["project_dir"], "character_mara") / "existing-selected.jpg"
    selected.write_bytes(b"fixture image")
    write_design_study_state(
        seeded["project_dir"],
        "character_mara",
        DesignStudyState(
            entity_id="character_mara",
            entity_type="character",
            selected_final_filename=selected.name,
        ),
    )
    before = {str(p): p.read_bytes() for p in seeded["project_dir"].rglob("*") if p.is_file()}
    assert service.generation_required(scene) is False
    after = {str(p): p.read_bytes() for p in seeded["project_dir"].rglob("*") if p.is_file()}
    assert after == before


@pytest.mark.unit
@pytest.mark.parametrize(
    ("image_model", "expected_error"),
    [
        (None, "No qualified current automatic image-backfill price for gemini-nano-banana-2.1"),
        ("imagen-4.0-generate-001", "Imagen 4.*shut down"),
    ],
)
def test_unqualified_backfill_with_actual_work_fails_before_compiler(
    tmp_path, monkeypatch, image_model, expected_error,
):
    from cine_forge.services.design_study_backfill import DefaultDesignStudyBackfillService
    from tests.storyboard_fixtures import metadata

    seeded = seed_render_project(tmp_path, include_keyframe=False, include_scene_image=False)
    seeded["store"].save_bible_entry(
        entity_type="character",
        entity_id="mara",
        display_name="Mara",
        files=[
            {
                "filename": "master.json",
                "purpose": "master_definition",
                "version": 1,
                "provenance": "system",
            }
        ],
        data_files={"master.json": '{"name":"Mara"}'},
        metadata=metadata("accounting fixture"),
        visual_reference_image=None,
    )
    monkeypatch.setattr(
        unit_prompt, "compile_render_prompt", lambda **kw: pytest.fail("paid compiler")
    )
    monkeypatch.setattr(render_unit, "generate_video", lambda **kw: pytest.fail("paid media"))
    monkeypatch.setattr(
        DefaultDesignStudyBackfillService, "backfill_scene", lambda *a: pytest.fail("image")
    )
    params = {
        "engine_pack_id": "xai_grok_imagine_video",
        "default_design_study_backfill": True,
    }
    if image_model is not None:
        params["default_design_study_backfill_model"] = image_model
    with pytest.raises(ValueError, match=expected_error):
        main.run_module(
            inputs=seeded["inputs"],
            params=params,
            context={"project_dir": str(seeded["project_dir"])},
        )


@pytest.mark.unit
def test_unqualified_video_model_fails_before_compiler_or_media(tmp_path, monkeypatch):
    seeded = seed_render_project(tmp_path, include_keyframe=False, include_scene_image=False)
    pack = main.load_engine_pack("xai_grok_imagine_video").model_copy(
        update={"target_model": "unknown"}
    )
    monkeypatch.setattr(main, "load_engine_pack", lambda _: pack)
    monkeypatch.setattr(
        unit_prompt, "compile_render_prompt", lambda **kw: pytest.fail("paid compiler")
    )
    monkeypatch.setattr(render_unit, "generate_video", lambda **kw: pytest.fail("paid media"))
    with pytest.raises(ValueError, match="No qualified current video price"):
        main.run_module(
            inputs=seeded["inputs"],
            params={"engine_pack_id": "xai_grok_imagine_video"},
            context={"project_dir": str(seeded["project_dir"])},
        )


@pytest.mark.unit
def test_retired_backfill_can_reuse_existing_references_without_generation(tmp_path, monkeypatch):
    from cine_forge.services import design_study_backfill

    seeded = seed_render_project(tmp_path, include_keyframe=False, include_scene_image=False)
    monkeypatch.setattr(unit_prompt, "compile_render_prompt", _compiler)
    monkeypatch.setattr(
        render_unit, "generate_video", lambda **kw: _video_result(kw["engine_pack"])
    )
    monkeypatch.setattr(
        design_study_backfill, "generate_image", lambda **kw: pytest.fail("paid image")
    )
    result = main.run_module(
        inputs=seeded["inputs"],
        params={
            "engine_pack_id": "xai_grok_imagine_video",
            "default_design_study_backfill": True,
        },
        context={"project_dir": str(seeded["project_dir"])},
    )
    assert result["cost"]["estimated_cost_usd"] == pytest.approx(0.412)

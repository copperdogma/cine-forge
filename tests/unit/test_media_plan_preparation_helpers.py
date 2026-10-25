"""Offline preparation parity and approved-input execution boundaries."""
from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.ai.video_pricing import VideoPricingError
from cine_forge.modules.generation.render_adapter_v1 import orchestration
from cine_forge.modules.generation.render_adapter_v1.source_inputs import (
    _build_source_maps,
    _output_contract,
)
from cine_forge.modules.generation.render_adapter_v1.support import load_engine_pack
from cine_forge.modules.generation.render_adapter_v1.unit_preparation import prepare_render_unit
from cine_forge.schemas import RenderClip, RenderClipPlan, Scene, ShotPlan
from tests.render_fixtures import seed_render_project

pytestmark = pytest.mark.unit


def _prepared_fixture(tmp_path: Path):
    seeded = seed_render_project(tmp_path, include_keyframe=False, include_scene_image=False)
    plan = ShotPlan.model_validate(seeded['inputs']['shot_plan'][0])
    scene = Scene.model_validate(seeded['store'].load_artifact(plan.scene_ref).data)
    clip = RenderClip(
        clip_id=f'{scene.scene_id}_clip_001', scene_id=scene.scene_id,
        source_shot_ids=[plan.shots[0].shot_id], start_time_seconds=0,
        end_time_seconds=3.2, target_duration_seconds=3.2,
        derivation='shot_plan', rationale='One short reviewed beat.', confidence=1,
    )
    clip_plan = RenderClipPlan(
        scene_id=scene.scene_id, scene_number=scene.scene_number,
        scene_heading=scene.heading, scene_ref=plan.scene_ref,
        selected_engine_pack_id='xai_grok_imagine_video', engine_max_clip_duration_seconds=15,
        target_dramatic_duration_seconds=3.2, duration_rationale='One short beat.',
        confidence=1, source='code', provenance_mode='shot_plan_code',
        deterministic_lower_bound_seconds=3.2, clips=[clip],
    )
    source_maps = _build_source_maps(seeded['inputs'])
    source_maps['render_clip_plan'][scene.scene_id] = clip_plan
    common = dict(
        store=seeded['store'], scene=scene, plan=plan, source_maps=source_maps,
        engine_pack=load_engine_pack('xai_grok_imagine_video'),
        requested_duration_seconds=8, requested_resolution='480p',
        requested_aspect_ratio='16:9',
        output_contract=_output_contract(params={'prompt_mode': 'ai_previz'}, runtime_params={}),
    )
    return common, clip


def test_single_clip_selection_preserves_its_duration_and_identity(tmp_path: Path):
    common, clip = _prepared_fixture(tmp_path)
    selected = orchestration._render_clips_for_scene(
        scene_id=common['scene'].scene_id,
        render_clip_plan=common['source_maps']['render_clip_plan'][common['scene'].scene_id],
        output_contract={}, selected_render_clip_ids={clip.clip_id},
    )
    assert selected == [clip]
    unit = prepare_render_unit(**common, render_clip=selected[0])
    assert unit.entity_id == clip.clip_id
    assert unit.requested_duration_seconds == 3.2
    assert unit.duration_seconds == 4
    assert len(unit.plan.shots) == 1


def test_single_clip_rejects_unknown_selection(tmp_path: Path):
    common, _clip = _prepared_fixture(tmp_path)
    with pytest.raises(ValueError, match='could not find requested render clip'):
        orchestration._render_clips_for_scene(
            scene_id=common['scene'].scene_id,
            render_clip_plan=common['source_maps']['render_clip_plan'][common['scene'].scene_id],
            output_contract={}, selected_render_clip_ids={'unknown'},
        )


def test_inspection_can_shape_unpriced_target_without_weakening_execution(tmp_path: Path):
    common, clip = _prepared_fixture(tmp_path)
    common['engine_pack'] = load_engine_pack('google_veo31')
    common['requested_resolution'] = '720p'
    with pytest.raises(VideoPricingError, match='unavailable'):
        prepare_render_unit(**common, render_clip=clip)
    unit = prepare_render_unit(**common, render_clip=clip, validate_price=False)
    assert unit.duration_seconds == 4
    assert unit.request.resolution == '720p'
    assert unit.request.prompt == ''


def _run_approved(common, clip, monkeypatch, *, units, requires_backfill=False):
    calls = []
    monkeypatch.setattr(
        orchestration, '_backfill_default_design_studies',
        lambda **kwargs: pytest.fail('Approved execution must not generate references'),
    )
    monkeypatch.setattr(
        orchestration.DefaultDesignStudyBackfillService, 'generation_required',
        lambda self, scene: requires_backfill,
    )
    result = orchestration._render_scene_outputs(
        **common, render_scene=lambda **kwargs: calls.append(kwargs) or ({}, {}, {}),
        compiler_model='code', scene_action_preflight=None,
        selected_render_clip_ids={clip.clip_id}, default_design_study_backfill=True,
        default_design_study_backfill_model='gemini-nano-banana-2.1',
        cost_receipts=[], prepared_units=units,
    )
    return result, calls


def test_approved_execution_reuses_exact_prepared_unit_without_backfill(tmp_path, monkeypatch):
    common, clip = _prepared_fixture(tmp_path)
    unit = prepare_render_unit(**common, render_clip=clip)
    result, calls = _run_approved(common, clip, monkeypatch, units={unit.entity_id: unit})
    assert not result[1]
    assert len(calls) == 1
    assert calls[0]['prepared_unit'] is unit


def test_approved_execution_does_not_fall_back_to_live_preparation(tmp_path, monkeypatch):
    common, clip = _prepared_fixture(tmp_path)
    with pytest.raises(ValueError, match='missing units'):
        _run_approved(common, clip, monkeypatch, units={})


def test_approved_execution_stops_if_reference_generation_becomes_required(tmp_path, monkeypatch):
    common, clip = _prepared_fixture(tmp_path)
    unit = prepare_render_unit(**common, render_clip=clip)
    with pytest.raises(ValueError, match='requires new reference images'):
        _run_approved(
            common, clip, monkeypatch, units={unit.entity_id: unit}, requires_backfill=True,
        )

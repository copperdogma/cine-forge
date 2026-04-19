from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_SCRIPT_ROOT = REPO_ROOT / "benchmarks" / "scripts"
if str(BENCHMARK_SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_SCRIPT_ROOT))

runtime_support = importlib.import_module("real_ai_previz_runtime_support")


def _case_result(
    *,
    case_id: str,
    attempt_index: int,
    success: bool,
    prerequisite_elapsed_ms: int,
    ai_previz_elapsed_ms: int,
    time_to_first_playable_ms: int,
    post_playable_overhead_ms: int,
    total_elapsed_ms: int,
    error: str | None = None,
    existing_clip_state: bool = False,
    requested_start_from: str | None = None,
) -> object:
    return runtime_support.RuntimeCaseResult(
        case_id=case_id,
        label=case_id,
        prerequisite_mode="scene_ready",
        recipe_mode="patched",
        engine_pack_id="fixture_pack",
        prompt_profile="standard",
        duration_seconds=4,
        resolution="720p",
        scene_id="scene_001",
        input_fixture="tests/fixtures/sample_screenplay.fountain",
        existing_clip_state=existing_clip_state,
        requested_start_from=requested_start_from,
        attempt_index=attempt_index,
        project_dir=f"output/{case_id}-{attempt_index}",
        success=success,
        error=error,
        prerequisite_elapsed_ms=prerequisite_elapsed_ms,
        ai_previz_elapsed_ms=ai_previz_elapsed_ms,
        time_to_first_playable_ms=time_to_first_playable_ms,
        post_playable_overhead_ms=post_playable_overhead_ms,
        total_elapsed_ms=total_elapsed_ms,
    )


@pytest.mark.unit
def test_runtime_eval_manifest_parses_shipped_and_patched_cases() -> None:
    manifest = runtime_support.RuntimeEvalManifest.model_validate_json(
        json.dumps(
            {
                "cases": [
                    {
                        "case_id": "shipped_lite_4_scene_ready",
                        "label": "Shipped scene-ready",
                        "input_fixture": "tests/fixtures/sample_screenplay.fountain",
                        "scene_id": "scene_001",
                        "prerequisite_mode": "scene_ready",
                        "recipe_mode": "shipped",
                    },
                    {
                        "case_id": "xai_4_480p_mvp_ingest_only",
                        "label": "xAI ingest-only",
                        "input_fixture": "tests/fixtures/sample_screenplay.fountain",
                        "scene_id": "scene_001",
                        "prerequisite_mode": "mvp_ingest_only",
                        "recipe_mode": "patched",
                        "ai_previz": {
                            "engine_pack_id": "xai_grok_imagine_video",
                            "duration_seconds": 4,
                            "resolution": "480p",
                            "consistency_strategy": "prompt_only",
                            "prompt_profile": "compact",
                        },
                    },
                    {
                        "case_id": "xai_regen_reuse",
                        "label": "xAI regenerate reuse",
                        "input_fixture": "tests/fixtures/sample_screenplay.fountain",
                        "scene_id": "scene_001",
                        "prerequisite_mode": "mvp_ingest_only",
                        "recipe_mode": "shipped",
                        "existing_clip_state": True,
                        "requested_start_from": "ai_previz",
                    },
                ]
            }
        )
    )

    assert len(manifest.cases) == 3
    assert manifest.cases[0].recipe_mode == "shipped"
    assert manifest.cases[0].ai_previz is None
    assert manifest.cases[1].prerequisite_mode == "mvp_ingest_only"
    assert manifest.cases[1].prerequisite_strategy is None
    assert manifest.cases[1].ai_previz is not None
    assert manifest.cases[1].ai_previz.engine_pack_id == "xai_grok_imagine_video"
    assert manifest.cases[1].ai_previz.prompt_profile == "compact"
    assert manifest.cases[2].existing_clip_state is True
    assert manifest.cases[2].requested_start_from == "ai_previz"


@pytest.mark.unit
def test_aggregate_attempts_and_summary_use_successful_medians() -> None:
    attempts = [
        _case_result(
            case_id="fast_4_scene_ready",
            attempt_index=1,
            success=True,
            prerequisite_elapsed_ms=111_000,
            ai_previz_elapsed_ms=53_000,
            time_to_first_playable_ms=164_000,
            post_playable_overhead_ms=4_000,
            total_elapsed_ms=168_000,
        ),
        _case_result(
            case_id="fast_4_scene_ready",
            attempt_index=2,
            success=True,
            prerequisite_elapsed_ms=109_000,
            ai_previz_elapsed_ms=51_000,
            time_to_first_playable_ms=160_000,
            post_playable_overhead_ms=3_000,
            total_elapsed_ms=163_000,
        ),
        _case_result(
            case_id="lite_4_scene_ready",
            attempt_index=1,
            success=False,
            prerequisite_elapsed_ms=120_000,
            ai_previz_elapsed_ms=56_000,
            time_to_first_playable_ms=176_000,
            post_playable_overhead_ms=5_000,
            total_elapsed_ms=181_000,
            error="provider timeout",
        ),
        _case_result(
            case_id="lite_4_scene_ready",
            attempt_index=2,
            success=True,
            prerequisite_elapsed_ms=118_000,
            ai_previz_elapsed_ms=55_000,
            time_to_first_playable_ms=173_000,
            post_playable_overhead_ms=4_000,
            total_elapsed_ms=177_000,
        ),
    ]

    aggregates = runtime_support.aggregate_attempts(attempts)
    summary = runtime_support.summarize_results(
        aggregates,
        fast_previz_target_ms=6_000,
    )

    fast_case = next(case for case in aggregates if case.case_id == "fast_4_scene_ready")
    lite_case = next(case for case in aggregates if case.case_id == "lite_4_scene_ready")

    assert fast_case.success is True
    assert fast_case.time_to_first_playable_ms == 162_000
    assert fast_case.ai_previz_elapsed_ms == 52_000
    assert fast_case.total_elapsed_ms == 165_500

    assert lite_case.success is False
    assert lite_case.successful_attempts == 1
    assert lite_case.time_to_first_playable_ms == 173_000
    assert lite_case.total_elapsed_ms == 177_000
    assert lite_case.ai_previz_elapsed_ms == 55_000

    assert summary["successful_cases"] == 1
    assert summary["fully_successful_cases"] == 1
    assert summary["focus_prerequisite_mode"] == "scene_ready"
    assert summary["fastest_focus_case_id"] == "fast_4_scene_ready"
    assert summary["fastest_focus_ms"] == 162_000
    assert summary["fastest_scene_ready_case_id"] == "fast_4_scene_ready"
    assert summary["fastest_scene_ready_ms"] == 162_000
    assert summary["fastest_isolated_ai_previz_ms"] == 52_000
    assert summary["fastest_scene_ready_full_completion_ms"] == 165_500
    assert summary["overall"] == 0.5


@pytest.mark.unit
def test_summarize_results_falls_back_to_partial_success_when_needed() -> None:
    aggregates = [
        runtime_support.RuntimeCaseAggregate(
            case_id="fast_partial",
            label="Fast partial",
            prerequisite_mode="scene_ready",
            recipe_mode="patched",
            engine_pack_id="fixture_fast",
            prompt_profile="standard",
            duration_seconds=4,
            resolution="720p",
            scene_id="scene_001",
            input_fixture="tests/fixtures/sample_screenplay.fountain",
            repeat_count=2,
            successful_attempts=1,
            success=False,
            prerequisite_elapsed_ms=100_000,
            ai_previz_elapsed_ms=40_000,
            time_to_first_playable_ms=140_000,
            post_playable_overhead_ms=4_000,
            total_elapsed_ms=144_000,
            min_time_to_first_playable_ms=139_000,
            max_time_to_first_playable_ms=141_000,
            min_total_elapsed_ms=143_000,
            max_total_elapsed_ms=145_000,
            min_ai_previz_elapsed_ms=39_000,
            max_ai_previz_elapsed_ms=41_000,
        ),
        runtime_support.RuntimeCaseAggregate(
            case_id="slow_partial",
            label="Slow partial",
            prerequisite_mode="scene_ready",
            recipe_mode="patched",
            engine_pack_id="fixture_slow",
            prompt_profile="compact",
            duration_seconds=4,
            resolution="720p",
            scene_id="scene_001",
            input_fixture="tests/fixtures/sample_screenplay.fountain",
            repeat_count=2,
            successful_attempts=1,
            success=False,
            prerequisite_elapsed_ms=130_000,
            ai_previz_elapsed_ms=60_000,
            time_to_first_playable_ms=190_000,
            post_playable_overhead_ms=6_000,
            total_elapsed_ms=196_000,
            min_time_to_first_playable_ms=189_000,
            max_time_to_first_playable_ms=191_000,
            min_total_elapsed_ms=195_000,
            max_total_elapsed_ms=197_000,
            min_ai_previz_elapsed_ms=59_000,
            max_ai_previz_elapsed_ms=61_000,
        ),
    ]

    summary = runtime_support.summarize_results(
        aggregates,
        fast_previz_target_ms=6_000,
    )

    assert summary["successful_cases"] == 2
    assert summary["fully_successful_cases"] == 0
    assert summary["focus_prerequisite_mode"] == "scene_ready"
    assert summary["fastest_focus_case_id"] == "fast_partial"
    assert summary["fastest_scene_ready_case_id"] == "fast_partial"
    assert summary["fastest_total_case_id"] == "fast_partial"


@pytest.mark.unit
def test_summarize_results_uses_one_pass_focus_when_only_ingest_only_cases_are_selected() -> None:
    aggregates = [
        runtime_support.RuntimeCaseAggregate(
            case_id="shipped_lite_4_mvp_ingest_only",
            label="Shipped lite",
            prerequisite_mode="mvp_ingest_only",
            recipe_mode="shipped",
            engine_pack_id="google_veo31_lite",
            prompt_profile="standard",
            duration_seconds=4,
            resolution="720p",
            scene_id="scene_001",
            input_fixture="tests/fixtures/sample_screenplay.fountain",
            repeat_count=1,
            successful_attempts=1,
            success=True,
            prerequisite_elapsed_ms=44_000,
            ai_previz_elapsed_ms=52_000,
            time_to_first_playable_ms=96_000,
            post_playable_overhead_ms=8_000,
            total_elapsed_ms=104_000,
            min_time_to_first_playable_ms=96_000,
            max_time_to_first_playable_ms=96_000,
            min_total_elapsed_ms=104_000,
            max_total_elapsed_ms=104_000,
            min_ai_previz_elapsed_ms=52_000,
            max_ai_previz_elapsed_ms=52_000,
        ),
        runtime_support.RuntimeCaseAggregate(
            case_id="xai_4_480p_mvp_ingest_only",
            label="xAI",
            prerequisite_mode="mvp_ingest_only",
            recipe_mode="patched",
            engine_pack_id="xai_grok_imagine_video",
            prompt_profile="standard",
            duration_seconds=4,
            resolution="480p",
            scene_id="scene_001",
            input_fixture="tests/fixtures/sample_screenplay.fountain",
            repeat_count=1,
            successful_attempts=1,
            success=True,
            prerequisite_elapsed_ms=43_000,
            ai_previz_elapsed_ms=22_000,
            time_to_first_playable_ms=65_000,
            post_playable_overhead_ms=0,
            total_elapsed_ms=65_000,
            min_time_to_first_playable_ms=65_000,
            max_time_to_first_playable_ms=65_000,
            min_total_elapsed_ms=65_000,
            max_total_elapsed_ms=65_000,
            min_ai_previz_elapsed_ms=22_000,
            max_ai_previz_elapsed_ms=22_000,
        ),
    ]

    summary = runtime_support.summarize_results(
        aggregates,
        fast_previz_target_ms=6_000,
    )

    assert summary["focus_prerequisite_mode"] == "mvp_ingest_only"
    assert summary["fastest_focus_case_id"] == "xai_4_480p_mvp_ingest_only"
    assert summary["fastest_focus_ms"] == 65_000
    assert summary["fastest_focus_prerequisite_ms"] == 43_000
    assert summary["fastest_focus_ai_previz_ms"] == 22_000
    assert summary["fastest_focus_isolated_ai_previz_ms"] == 22_000
    assert summary["fastest_scene_ready_case_id"] is None
    assert summary["overall"] == 0.5


@pytest.mark.unit
def test_summarize_results_reports_regenerate_reuse_and_full_control_metrics() -> None:
    aggregates = runtime_support.aggregate_attempts([
        _case_result(
            case_id="shipped_xai_regen_full",
            attempt_index=1,
            success=True,
            prerequisite_elapsed_ms=24_000,
            ai_previz_elapsed_ms=18_000,
            time_to_first_playable_ms=42_000,
            post_playable_overhead_ms=5_000,
            total_elapsed_ms=47_000,
            existing_clip_state=True,
            requested_start_from=None,
        ),
        _case_result(
            case_id="shipped_xai_regen_reuse",
            attempt_index=1,
            success=True,
            prerequisite_elapsed_ms=0,
            ai_previz_elapsed_ms=18_000,
            time_to_first_playable_ms=18_000,
            post_playable_overhead_ms=4_000,
            total_elapsed_ms=22_000,
            existing_clip_state=True,
            requested_start_from="ai_previz",
        ),
    ])

    summary = runtime_support.summarize_results(
        aggregates,
        fast_previz_target_ms=6_000,
    )

    assert summary["fastest_regenerate_reuse_case_id"] == "shipped_xai_regen_reuse"
    assert summary["fastest_regenerate_reuse_ms"] == 18_000
    assert summary["fastest_regenerate_reuse_ai_previz_ms"] == 18_000
    assert summary["fastest_regenerate_reuse_full_completion_ms"] == 22_000
    assert summary["fastest_regenerate_full_case_id"] == "shipped_xai_regen_full"
    assert summary["fastest_regenerate_full_ms"] == 42_000
    assert summary["fastest_regenerate_full_ai_previz_ms"] == 18_000
    assert summary["fastest_regenerate_full_completion_ms"] == 47_000

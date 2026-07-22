from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from cine_forge.schemas import EnginePack
from cine_forge.services.previz_adoption import PrevizAdoptionService

pytestmark = pytest.mark.unit


def _write_recipe(
    path: Path,
    *,
    engine_pack_id: str,
    duration_seconds: int = 8,
    resolution: str = "1280x720",
    with_validation: bool = True,
) -> None:
    stages: list[dict[str, object]] = [
        {
            "id": "ai_previz",
            "module": "render_adapter_v1",
            "params": {
                "engine_pack_id": engine_pack_id,
                "duration_seconds": duration_seconds,
                "resolution": resolution,
                "consistency_strategy": "prompt_only",
            },
        }
    ]
    if with_validation:
        stages.append(
            {
                "id": "validate_media",
                "module": "media_validation_v1",
                "params": {"target_artifact_type": "ai_previz_video"},
                "after": ["ai_previz"],
                "store_inputs_all": {"generated_video": "ai_previz_video"},
            }
        )
    path.write_text(
        yaml.safe_dump(
            {
                "recipe_id": "ai_previz_generation",
                "description": "test fixture",
                "project": {},
                "stages": stages,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _write_registry(
    path: Path,
    *,
    candidate_label: str,
    candidate_overall: float,
    baseline_overall: float,
    latency_ms: int,
    runtime_latency_ms: int | None = None,
    runtime_metrics: dict[str, int] | None = None,
    candidate_evidence_status: str | None = "decision-grade",
    baseline_evidence_status: str | None = "decision-grade",
    runtime_evidence_status: str | None = "decision-grade",
    historical_evidence_status: str | None = None,
) -> None:
    candidate_score = {
        "model": candidate_label,
        "metrics": {"overall": candidate_overall},
        "latency_ms": latency_ms,
        "measured": "2026-04-03",
    }
    baseline_score = {
        "model": "Annotated Animatic",
        "metrics": {"overall": baseline_overall},
        "latency_ms": 0,
        "measured": "2026-04-03",
    }
    if candidate_evidence_status is not None:
        candidate_score["evidence_status"] = candidate_evidence_status
    if baseline_evidence_status is not None:
        baseline_score["evidence_status"] = baseline_evidence_status
    previz_eval: dict[str, object] = {
        "id": "previz-usefulness",
        "scores": [candidate_score, baseline_score],
    }
    if historical_evidence_status is not None:
        previz_eval["historical_evidence_status"] = historical_evidence_status
    evals: list[dict[str, object]] = [
        previz_eval
    ]
    if runtime_latency_ms is not None:
        metrics: dict[str, object] = {"overall": 0.5}
        if runtime_metrics:
            metrics.update(runtime_metrics)
        runtime_score = {
            "model": "Current shipped runtime",
            "metrics": metrics,
            "latency_ms": runtime_latency_ms,
            "measured": "2026-04-19",
        }
        if runtime_evidence_status is not None:
            runtime_score["evidence_status"] = runtime_evidence_status
        evals.append({"id": "real-ai-previz-runtime", "scores": [runtime_score]})
    path.write_text(
        yaml.safe_dump(
            {"evals": evals},
            sort_keys=False,
        ),
        encoding="utf-8",
    )


def _engine_pack(
    *,
    pack_id: str,
    target_model: str,
    cost_per_second: float | None,
    pricing_note: str,
    provider: str = "google",
    default_resolution: str = "1280x720",
    benchmark_default_duration_seconds: int = 8,
) -> EnginePack:
    request_defaults: dict[str, object] = {
        "default_resolution": default_resolution,
        "benchmark_default_duration_seconds": benchmark_default_duration_seconds,
    }
    if cost_per_second is not None:
        request_defaults["benchmark_cost_per_second_usd"] = cost_per_second
    return EnginePack.model_validate(
        {
            "pack_id": pack_id,
            "provider": provider,
            "target_model": target_model,
            "description": "fixture pack",
            "preferred_prompt_style": "fixture",
            "known_strengths": [],
            "known_limitations": [pricing_note],
            "limits": {
                "supported_durations_seconds": [4, 6, 8],
                "supported_resolutions": [default_resolution],
                "supported_aspect_ratios": ["16:9"],
            },
            "request_defaults": request_defaults,
        }
    )


def test_previz_adoption_service_keeps_ai_previz_primary_when_cost_is_blocked(
    tmp_path: Path,
) -> None:
    recipe_path = tmp_path / "recipe-ai-previz-generation.yaml"
    registry_path = tmp_path / "registry.yaml"
    _write_recipe(recipe_path, engine_pack_id="google_veo31_lite")
    _write_registry(
        registry_path,
        candidate_label="Veo 3.1 Lite Previz",
        candidate_overall=0.828,
        baseline_overall=0.803,
        latency_ms=39273,
    )

    service = PrevizAdoptionService(
        recipe_path=recipe_path,
        registry_path=registry_path,
        engine_pack_loader=lambda _pack_id: _engine_pack(
            pack_id="google_veo31_lite",
            target_model="veo-3.1-lite-generate-preview",
            cost_per_second=None,
            pricing_note="Public per-second pricing was not listed for this pack.",
        ),
    )

    status = service.build_status()

    assert status.ai_previz.adoption_state == "default"
    assert status.ai_previz.cost.status == "blocked"
    assert status.ai_previz.validation_stage_enabled is True
    assert status.ai_previz.baseline_score == 0.803
    assert status.ai_previz.score_margin == 0.025
    assert any(
        "outside the 6000 ms fast-previz target" in blocker
        for blocker in status.ai_previz.blocker_reasons
    )
    assert any("pricing" in blocker.lower() for blocker in status.ai_previz.blocker_reasons)
    assert "only shipped operator-facing lane" in status.policy_summary.lower()


def test_previz_adoption_service_can_clear_default_gate_when_cost_and_margin_are_verified(
    tmp_path: Path,
) -> None:
    recipe_path = tmp_path / "recipe-ai-previz-generation.yaml"
    registry_path = tmp_path / "registry.yaml"
    _write_recipe(recipe_path, engine_pack_id="google_veo31_fast")
    _write_registry(
        registry_path,
        candidate_label="Veo 3.1 Fast Previz",
        candidate_overall=0.86,
        baseline_overall=0.80,
        latency_ms=3200,
    )

    service = PrevizAdoptionService(
        recipe_path=recipe_path,
        registry_path=registry_path,
        engine_pack_loader=lambda _pack_id: _engine_pack(
            pack_id="google_veo31_fast",
            target_model="veo-3.1-fast-generate-preview",
            cost_per_second=0.05,
            pricing_note="Prompt-only fixture limitation.",
        ),
    )

    status = service.build_status()

    assert status.ai_previz.adoption_state == "default"
    assert status.ai_previz.cost.status == "estimated"
    assert status.ai_previz.cost.estimated_cost_usd == 0.4
    assert status.ai_previz.blocker_reasons == []
    assert "honest operator-facing previz lane" in status.ai_previz.reason


def test_previz_adoption_service_keeps_ai_previz_primary_even_when_it_is_too_slow(
    tmp_path: Path,
) -> None:
    recipe_path = tmp_path / "recipe-ai-previz-generation.yaml"
    registry_path = tmp_path / "registry.yaml"
    _write_recipe(recipe_path, engine_pack_id="google_veo31_fast")
    _write_registry(
        registry_path,
        candidate_label="Veo 3.1 Fast Previz",
        candidate_overall=0.86,
        baseline_overall=0.80,
        latency_ms=32000,
    )

    service = PrevizAdoptionService(
        recipe_path=recipe_path,
        registry_path=registry_path,
        engine_pack_loader=lambda _pack_id: _engine_pack(
            pack_id="google_veo31_fast",
            target_model="veo-3.1-fast-generate-preview",
            cost_per_second=0.05,
            pricing_note="Prompt-only fixture limitation.",
        ),
    )

    status = service.build_status()

    assert status.ai_previz.adoption_state == "default"
    assert "outside the 6000 ms fast-previz target" in status.ai_previz.reason


def test_previz_adoption_service_prefers_honest_runtime_latency_when_available(
    tmp_path: Path,
) -> None:
    recipe_path = tmp_path / "recipe-ai-previz-generation.yaml"
    registry_path = tmp_path / "registry.yaml"
    _write_recipe(recipe_path, engine_pack_id="google_veo31_fast")
    _write_registry(
        registry_path,
        candidate_label="Veo 3.1 Fast Previz",
        candidate_overall=0.86,
        baseline_overall=0.80,
        latency_ms=3200,
        runtime_latency_ms=186659,
    )

    service = PrevizAdoptionService(
        recipe_path=recipe_path,
        registry_path=registry_path,
        engine_pack_loader=lambda _pack_id: _engine_pack(
            pack_id="google_veo31_fast",
            target_model="veo-3.1-fast-generate-preview",
            cost_per_second=0.05,
            pricing_note="Prompt-only fixture limitation.",
        ),
    )

    status = service.build_status()

    assert status.ai_previz.latency_ms == 186659
    assert any(
        "186659 ms" in blocker for blocker in status.ai_previz.blocker_reasons
    )


def test_previz_adoption_service_supports_shipped_xai_lane_when_it_clears_quality_floor(
    tmp_path: Path,
) -> None:
    recipe_path = tmp_path / "recipe-ai-previz-generation.yaml"
    registry_path = tmp_path / "registry.yaml"
    _write_recipe(
        recipe_path,
        engine_pack_id="xai_grok_imagine_video",
        duration_seconds=4,
        resolution="480p",
    )
    _write_registry(
        registry_path,
        candidate_label="Grok Imagine Previz",
        candidate_overall=0.8413,
        baseline_overall=0.8380,
        latency_ms=17611,
        runtime_latency_ms=61387,
        runtime_metrics={
            "fastest_regenerate_reuse_ms": 17611,
            "fastest_regenerate_full_ms": 47865,
        },
    )

    service = PrevizAdoptionService(
        recipe_path=recipe_path,
        registry_path=registry_path,
        engine_pack_loader=lambda _pack_id: _engine_pack(
            pack_id="xai_grok_imagine_video",
            target_model="grok-imagine-video",
            cost_per_second=None,
            pricing_note="Provider pricing rate is not yet recorded for this xAI fixture.",
            provider="xai",
            default_resolution="480p",
            benchmark_default_duration_seconds=4,
        ),
    )

    status = service.build_status()

    assert status.ai_previz.candidate_label == "Grok Imagine Previz"
    assert status.ai_previz.engine_pack_id == "xai_grok_imagine_video"
    assert status.ai_previz.resolution == "480p"
    assert status.ai_previz.duration_seconds == 4.0
    assert status.ai_previz.adoption_state == "default"
    assert status.ai_previz.score_margin == 0.0033
    assert status.ai_previz.latency_ms == 61387
    assert status.ai_previz.regenerate_reuse_latency_ms == 17611
    assert status.ai_previz.regenerate_full_latency_ms == 47865
    assert any(
        "61387 ms" in blocker for blocker in status.ai_previz.blocker_reasons
    )
    assert any("pricing" in blocker.lower() for blocker in status.ai_previz.blocker_reasons)


@pytest.mark.parametrize(
    ("candidate_status", "baseline_status"),
    [
        ("contaminated-non-decision-grade", "contaminated-non-decision-grade"),
        (None, None),
    ],
)
def test_previz_adoption_service_rejects_non_decision_grade_registry_evidence(
    tmp_path: Path,
    candidate_status: str | None,
    baseline_status: str | None,
) -> None:
    recipe_path = tmp_path / "recipe-ai-previz-generation.yaml"
    registry_path = tmp_path / "registry.yaml"
    _write_recipe(recipe_path, engine_pack_id="google_veo31_fast")
    _write_registry(
        registry_path,
        candidate_label="Veo 3.1 Fast Previz",
        candidate_overall=0.99,
        baseline_overall=0.98,
        latency_ms=100,
        runtime_latency_ms=100,
        candidate_evidence_status=candidate_status,
        baseline_evidence_status=baseline_status,
        runtime_evidence_status="superseded-non-decision-grade",
        historical_evidence_status="contaminated-non-decision-grade",
    )
    service = PrevizAdoptionService(
        recipe_path=recipe_path,
        registry_path=registry_path,
        engine_pack_loader=lambda _pack_id: _engine_pack(
            pack_id="google_veo31_fast",
            target_model="veo-3.1-fast-generate-preview",
            cost_per_second=0.05,
            pricing_note="Prompt-only fixture limitation.",
        ),
    )

    status = service.build_status()

    assert status.ai_previz.adoption_state == "experimental_manual"
    assert status.ai_previz.overall_score is None
    assert status.ai_previz.baseline_score is None
    assert status.ai_previz.latency_ms is None
    assert any("No previz-usefulness score" in item for item in status.ai_previz.blocker_reasons)


def test_explicit_repaired_score_can_override_contaminated_history(
    tmp_path: Path,
) -> None:
    recipe_path = tmp_path / "recipe-ai-previz-generation.yaml"
    registry_path = tmp_path / "registry.yaml"
    _write_recipe(recipe_path, engine_pack_id="google_veo31_fast")
    _write_registry(
        registry_path,
        candidate_label="Veo 3.1 Fast Previz",
        candidate_overall=0.86,
        baseline_overall=0.80,
        latency_ms=3200,
        historical_evidence_status="contaminated-non-decision-grade",
    )
    service = PrevizAdoptionService(
        recipe_path=recipe_path,
        registry_path=registry_path,
        engine_pack_loader=lambda _pack_id: _engine_pack(
            pack_id="google_veo31_fast",
            target_model="veo-3.1-fast-generate-preview",
            cost_per_second=0.05,
            pricing_note="Prompt-only fixture limitation.",
        ),
    )

    status = service.build_status()

    assert status.ai_previz.adoption_state == "default"
    assert status.ai_previz.overall_score == 0.86

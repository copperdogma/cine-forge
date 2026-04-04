from __future__ import annotations

from pathlib import Path

import yaml

from cine_forge.schemas import EnginePack
from cine_forge.services.previz_adoption import PrevizAdoptionService


def _write_recipe(path: Path, *, engine_pack_id: str, with_validation: bool = True) -> None:
    stages: list[dict[str, object]] = [
        {
            "id": "ai_previz",
            "module": "render_adapter_v1",
            "params": {
                "engine_pack_id": engine_pack_id,
                "duration_seconds": 8,
                "resolution": "1280x720",
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
) -> None:
    path.write_text(
        yaml.safe_dump(
            {
                "evals": [
                    {
                        "id": "previz-usefulness",
                        "scores": [
                            {
                                "model": candidate_label,
                                "metrics": {"overall": candidate_overall},
                                "latency_ms": latency_ms,
                                "measured": "2026-04-03",
                            },
                            {
                                "model": "Annotated Animatic",
                                "metrics": {"overall": baseline_overall},
                                "latency_ms": 0,
                                "measured": "2026-04-03",
                            },
                        ],
                    }
                ]
            },
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
) -> EnginePack:
    request_defaults: dict[str, object] = {
        "default_resolution": "1280x720",
        "benchmark_default_duration_seconds": 8,
    }
    if cost_per_second is not None:
        request_defaults["benchmark_cost_per_second_usd"] = cost_per_second
    return EnginePack.model_validate(
        {
            "pack_id": pack_id,
            "provider": "google",
            "target_model": target_model,
            "description": "fixture pack",
            "preferred_prompt_style": "fixture",
            "known_strengths": [],
            "known_limitations": [pricing_note],
            "limits": {
                "supported_durations_seconds": [4, 6, 8],
                "supported_resolutions": ["1280x720"],
                "supported_aspect_ratios": ["16:9"],
            },
            "request_defaults": request_defaults,
        }
    )


def test_previz_adoption_service_marks_lite_as_recommended_optional_when_cost_is_blocked(
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

    assert status.default_lane == "annotated_animatic"
    assert status.ai_previz.adoption_state == "recommended_optional"
    assert status.ai_previz.cost.status == "blocked"
    assert status.ai_previz.validation_stage_enabled is True
    assert any("0.03" in blocker for blocker in status.ai_previz.blocker_reasons)
    assert any("pricing" in blocker.lower() for blocker in status.ai_previz.blocker_reasons)


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

    assert status.default_lane == "ai_previz"
    assert status.ai_previz.adoption_state == "default"
    assert status.ai_previz.cost.status == "estimated"
    assert status.ai_previz.cost.estimated_cost_usd == 0.4
    assert status.ai_previz.blocker_reasons == []

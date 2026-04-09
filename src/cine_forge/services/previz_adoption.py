"""Shared previz policy derived from current repo evidence and product truth."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from cine_forge.modules.generation.render_adapter_v1.support import load_engine_pack
from cine_forge.schemas import (
    EnginePack,
    PrevizAdoptionStatus,
    PrevizCostEvidence,
    PrevizLaneStatus,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]
_QUALITY_FLOOR = 0.75
_FAST_AI_PREVIZ_TARGET_MS = 6_000
_AI_OPTIONAL_LATENCY_LIMIT_MS = 180_000
_ANNOTATED_LABEL = "Annotated Animatic"
_CANDIDATE_LABELS = {
    "google_veo31": "Veo 3.1 Previz",
    "google_veo31_fast": "Veo 3.1 Fast Previz",
    "google_veo31_lite": "Veo 3.1 Lite Previz",
    "openai_sora2": "Sora 2 Previz",
}


class PrevizAdoptionService:
    """Resolve the current AI-previz adoption/default state for operators."""

    def __init__(
        self,
        *,
        recipe_path: Path | None = None,
        registry_path: Path | None = None,
        engine_pack_loader: Any = load_engine_pack,
    ) -> None:
        self._recipe_path = recipe_path or (
            _REPO_ROOT / "configs" / "recipes" / "recipe-ai-previz-generation.yaml"
        )
        self._registry_path = registry_path or (_REPO_ROOT / "docs" / "evals" / "registry.yaml")
        self._engine_pack_loader = engine_pack_loader

    def build_status(self, *, project_path: Path | None = None) -> PrevizAdoptionStatus:
        _ = project_path
        recipe = self._load_yaml(self._recipe_path)
        params = self._recipe_params(recipe)
        engine_pack_id = str(params.get("engine_pack_id") or "").strip()
        engine_pack = self._engine_pack_loader(engine_pack_id)
        score_entry = self._candidate_score(engine_pack_id)
        baseline_entry = self._baseline_score()

        blockers = self._blockers_for(
            recipe=recipe,
            params=params,
            engine_pack=engine_pack,
            score_entry=score_entry,
        )
        cost = self._cost_evidence(params=params, engine_pack=engine_pack)
        overall_score = self._overall_score(score_entry)
        baseline_score = self._overall_score(baseline_entry)
        baseline_latency_ms = self._latency_ms(baseline_entry)
        margin = (
            round(overall_score - baseline_score, 4)
            if overall_score is not None and baseline_score is not None
            else None
        )
        latency_ms = self._latency_ms(score_entry)
        primary_lane = "ai_previz"
        ai_viable = self._validation_stage_enabled(recipe) and (
            overall_score is not None and overall_score >= _QUALITY_FLOOR
        )
        adoption_state = "default" if ai_viable else "experimental_manual"

        deterministic_lane = PrevizLaneStatus(
            lane_id="deterministic_previz",
            label="Deterministic Baseline",
            candidate_label=_ANNOTATED_LABEL,
            latency_class="fast",
            adoption_state="recommended_optional",
            reason=self._deterministic_lane_reason(
                baseline_entry=baseline_entry,
            ),
            intended_use=(
                "Fallback/control arm for timing, pacing, blocking, and pipeline sanity checks "
                "while real AI previz is still too slow or missing."
            ),
            fidelity_disclosure=(
                "Deterministic annotated animatic assembled from shot plans and storyboards. "
                "Not AI-generated motion."
            ),
            blocker_reasons=self._deterministic_lane_blockers(baseline_entry),
            overall_score=baseline_score,
            measured_at=self._measured_at(baseline_entry),
            latency_ms=baseline_latency_ms,
            latency_budget_ms=_FAST_AI_PREVIZ_TARGET_MS,
            consistency_strategy="deterministic",
            cost=PrevizCostEvidence(
                status="verified",
                estimated_cost_usd=0.0,
                reason=(
                    "Deterministic previz baseline generated locally without "
                    "provider cost."
                ),
            ),
            validation_stage_enabled=True,
            upgrade_lane_id="ai_previz",
            upgrade_label="Generate AI Previz",
            upgrade_description=(
                "Use AI Previz when you want generated motion. The deterministic baseline is "
                "fallback/control only and does not satisfy the real previz goal."
            ),
        )
        ai_lane = PrevizLaneStatus(
            lane_id="ai_previz",
            label="AI Previz",
            candidate_label=_CANDIDATE_LABELS.get(engine_pack_id),
            latency_class=(
                "fast"
                if latency_ms is not None and latency_ms <= _FAST_AI_PREVIZ_TARGET_MS
                else "slow"
            ),
            adoption_state=adoption_state,
            reason=self._reason_for(
                adoption_state=adoption_state,
                engine_pack=engine_pack,
                blockers=blockers,
                latency_ms=latency_ms,
            ),
            intended_use=(
                "Primary operator-facing previz lane for generated motion, staging, pacing, and "
                "camera review before final renders."
            ),
            fidelity_disclosure=(
                "Low-fidelity AI planning clip. This is the intended previz lane, but it remains "
                "explicitly non-final footage."
            ),
            blocker_reasons=blockers,
            overall_score=overall_score,
            baseline_score=baseline_score,
            score_margin=margin,
            measured_at=self._measured_at(score_entry),
            latency_ms=latency_ms,
            latency_budget_ms=_AI_OPTIONAL_LATENCY_LIMIT_MS,
            engine_pack_id=engine_pack.pack_id,
            target_model=engine_pack.target_model,
            resolution=self._resolution(params=params, engine_pack=engine_pack),
            duration_seconds=self._duration_seconds(params=params, engine_pack=engine_pack),
            consistency_strategy=self._consistency_strategy(params=params),
            cost=cost,
            validation_stage_enabled=self._validation_stage_enabled(recipe),
            upgrade_lane_id="deterministic_previz",
            upgrade_label="Generate Deterministic Baseline",
            upgrade_description=(
                "Deterministic baseline remains available as a fallback/control lane when you "
                "need an instant non-AI planning artifact."
            ),
        )
        return PrevizAdoptionStatus(
            primary_lane=primary_lane,
            policy_summary=self._policy_summary(
                primary_lane=primary_lane,
                ai_lane=ai_lane,
                deterministic_lane=deterministic_lane,
            ),
            deterministic_previz=deterministic_lane,
            ai_previz=ai_lane,
        )

    def _blockers_for(
        self,
        *,
        recipe: dict[str, Any],
        params: dict[str, Any],
        engine_pack: EnginePack,
        score_entry: dict[str, Any] | None,
    ) -> list[str]:
        blockers: list[str] = []
        if not self._validation_stage_enabled(recipe):
            blockers.append(
                "AI previz recipe is not yet wired to emit media validation artifacts."
            )

        overall_score = self._overall_score(score_entry)
        if score_entry is None or overall_score is None:
            blockers.append(
                f"No previz-usefulness score was found for the active engine pack "
                f"`{engine_pack.pack_id}`."
            )
        elif overall_score < _QUALITY_FLOOR:
            blockers.append(
                f"Current AI previz usefulness is {overall_score:.3f}, below the "
                f"{_QUALITY_FLOOR:.2f} adoption floor."
            )

        latency_ms = self._latency_ms(score_entry)
        if latency_ms is not None and latency_ms > _FAST_AI_PREVIZ_TARGET_MS:
            blockers.append(
                f"Measured AI previz latency is {latency_ms} ms, outside the "
                f"{_FAST_AI_PREVIZ_TARGET_MS} ms fast-previz target."
            )
        if latency_ms is not None and latency_ms > _AI_OPTIONAL_LATENCY_LIMIT_MS:
            blockers.append(
                f"Measured AI previz latency is {latency_ms} ms, above the "
                f"{_AI_OPTIONAL_LATENCY_LIMIT_MS} ms optional-lane envelope."
            )

        cost = self._cost_evidence(params=params, engine_pack=engine_pack)
        if cost.status == "blocked" and cost.reason:
            blockers.append(cost.reason)
        return blockers

    def _reason_for(
        self,
        *,
        adoption_state: str,
        engine_pack: EnginePack,
        blockers: list[str],
        latency_ms: int | None,
    ) -> str:
        if adoption_state == "default":
            if latency_ms is not None and latency_ms > _FAST_AI_PREVIZ_TARGET_MS:
                return (
                    f"{_CANDIDATE_LABELS.get(engine_pack.pack_id, 'AI previz')} is the intended "
                    "operator-facing previz lane and the strongest current generated-motion "
                    f"candidate, but the latest measured runtime is {latency_ms} ms, outside the "
                    f"{_FAST_AI_PREVIZ_TARGET_MS} ms fast-previz target."
                )
            if blockers:
                return (
                    f"{_CANDIDATE_LABELS.get(engine_pack.pack_id, 'AI previz')} remains the "
                    "intended previz lane, but it still carries blocker truth that must stay "
                    "visible while deterministic baseline remains fallback/control only."
                )
            return (
                f"{_CANDIDATE_LABELS.get(engine_pack.pack_id, 'AI previz')} currently clears "
                "the current usefulness, latency, and cost gates, so it can serve as the honest "
                "operator-facing previz lane."
            )
        if blockers:
            return (
                f"{_CANDIDATE_LABELS.get(engine_pack.pack_id, 'AI previz')} is still the "
                "intended previz lane, but it remains blocked. "
                f"{blockers[0]}"
            )
        return (
            f"{_CANDIDATE_LABELS.get(engine_pack.pack_id, 'AI previz')} remains a manual lane "
            "until the usefulness, latency, and cost evidence improves."
        )

    def _deterministic_lane_blockers(self, entry: dict[str, Any] | None) -> list[str]:
        blockers: list[str] = []
        latency_ms = self._latency_ms(entry)
        if latency_ms is None or latency_ms <= 0:
            blockers.append(
                "Deterministic baseline latency still needs a real measurement; the old 0 ms "
                "placeholder is not honest enough for the control-arm budget."
            )
        elif latency_ms > _FAST_AI_PREVIZ_TARGET_MS:
            blockers.append(
                f"Measured deterministic baseline latency is {latency_ms} ms, above the "
                f"{_FAST_AI_PREVIZ_TARGET_MS} ms control-arm budget."
            )
        if self._overall_score(entry) is None:
            blockers.append("Annotated Animatic is missing a current previz-usefulness score.")
        return blockers

    def _deterministic_lane_reason(self, *, baseline_entry: dict[str, Any] | None) -> str:
        latency_ms = self._latency_ms(baseline_entry)
        if latency_ms is None or latency_ms <= 0:
            return (
                "Deterministic baseline remains available as a fallback/control arm, but its "
                "latency still needs a real measurement."
            )
        if latency_ms <= _FAST_AI_PREVIZ_TARGET_MS:
            return (
                f"Deterministic baseline measured {latency_ms} ms and remains useful for instant "
                "fallback/control, but it is not a substitute for generated previz motion."
            )
        return (
            f"Deterministic baseline still serves as fallback/control, but the latest measured "
            f"Annotated Animatic latency is {latency_ms} ms and even the control arm needs "
            "attention."
        )

    def _policy_summary(
        self,
        *,
        primary_lane: str,
        ai_lane: PrevizLaneStatus,
        deterministic_lane: PrevizLaneStatus,
    ) -> str:
        if primary_lane != "ai_previz":
            return (
                "Deterministic previz is only a fallback/control surface. The product previz lane "
                "should be AI-generated motion."
            )
        if ai_lane.blocker_reasons:
            return (
                "AI Previz is the intended operator-facing lane, but current generated-motion "
                "runtime or evidence still misses the product bar. Deterministic baseline remains "
                "available as fallback/control only."
            )
        return (
            "AI Previz is the primary operator-facing lane. Deterministic baseline remains a "
            "fallback/control path for instant non-AI review."
        )

    def _cost_evidence(
        self,
        *,
        params: dict[str, Any],
        engine_pack: EnginePack,
    ) -> PrevizCostEvidence:
        raw_rate = engine_pack.request_defaults.get("benchmark_cost_per_second_usd")
        if raw_rate not in (None, ""):
            duration_seconds = self._duration_seconds(params=params, engine_pack=engine_pack) or 0.0
            return PrevizCostEvidence(
                status="estimated",
                estimated_cost_usd=round(float(raw_rate) * duration_seconds, 4),
                reason=(
                    "Estimated from the recorded engine-pack benchmark rate and the current "
                    "recipe duration."
                ),
            )
        return PrevizCostEvidence(
            status="blocked",
            estimated_cost_usd=None,
            reason=self._pricing_blocker_reason(engine_pack),
        )

    def _pricing_blocker_reason(self, engine_pack: EnginePack) -> str:
        for note in engine_pack.known_limitations:
            if "pricing" in note.lower():
                return note
        return (
            f"{engine_pack.pack_id} does not have a recorded benchmark or provider pricing rate, "
            "so AI-previz cost cannot yet be estimated honestly."
        )

    def _candidate_score(self, engine_pack_id: str) -> dict[str, Any] | None:
        label = _CANDIDATE_LABELS.get(engine_pack_id)
        if label is None:
            return None
        return self._score_by_label(label)

    def _baseline_score(self) -> dict[str, Any] | None:
        return self._score_by_label(_ANNOTATED_LABEL)

    def _score_by_label(self, label: str) -> dict[str, Any] | None:
        registry = self._load_yaml(self._registry_path)
        evals = registry.get("evals", []) if isinstance(registry, dict) else []
        for entry in evals:
            if not isinstance(entry, dict) or entry.get("id") != "previz-usefulness":
                continue
            for score in entry.get("scores", []):
                if isinstance(score, dict) and score.get("model") == label:
                    return score
        return None

    def _overall_score(self, entry: dict[str, Any] | None) -> float | None:
        if not isinstance(entry, dict):
            return None
        metrics = entry.get("metrics")
        if not isinstance(metrics, dict):
            return None
        value = metrics.get("overall")
        if isinstance(value, (int, float)):
            return float(value)
        return None

    def _latency_ms(self, entry: dict[str, Any] | None) -> int | None:
        value = entry.get("latency_ms") if isinstance(entry, dict) else None
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return round(value)
        return None

    def _measured_at(self, entry: dict[str, Any] | None) -> str | None:
        value = entry.get("measured") if isinstance(entry, dict) else None
        return value if isinstance(value, str) and value.strip() else None

    def _recipe_params(self, recipe: dict[str, Any]) -> dict[str, Any]:
        for stage in recipe.get("stages", []):
            if isinstance(stage, dict) and stage.get("id") == "ai_previz":
                params = stage.get("params")
                return params if isinstance(params, dict) else {}
        raise ValueError("recipe-ai-previz-generation.yaml is missing the `ai_previz` stage")

    def _validation_stage_enabled(self, recipe: dict[str, Any]) -> bool:
        for stage in recipe.get("stages", []):
            if not isinstance(stage, dict) or stage.get("module") != "media_validation_v1":
                continue
            inputs = stage.get("store_inputs_all")
            if not isinstance(inputs, dict):
                continue
            if inputs.get("generated_video") == "ai_previz_video":
                return True
        return False

    def _resolution(self, *, params: dict[str, Any], engine_pack: EnginePack) -> str | None:
        value = params.get("resolution") or engine_pack.request_defaults.get("default_resolution")
        return str(value) if value not in (None, "") else None

    def _duration_seconds(self, *, params: dict[str, Any], engine_pack: EnginePack) -> float | None:
        value = params.get("duration_seconds") or engine_pack.request_defaults.get(
            "benchmark_default_duration_seconds"
        )
        if isinstance(value, (int, float)):
            return float(value)
        return None

    def _consistency_strategy(self, params: dict[str, Any]) -> str | None:
        value = params.get("consistency_strategy")
        return str(value) if value not in (None, "") else None

    def _load_yaml(self, path: Path) -> dict[str, Any]:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}

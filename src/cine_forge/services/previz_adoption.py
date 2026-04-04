"""Shared AI-previz adoption/default policy derived from current repo evidence."""

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
_DEFAULT_MARGIN = 0.03
_QUALITY_FLOOR = 0.75
_LATENCY_LIMIT_MS = 180_000
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
            baseline_entry=baseline_entry,
        )
        cost = self._cost_evidence(params=params, engine_pack=engine_pack)
        overall_score = self._overall_score(score_entry)
        baseline_score = self._overall_score(baseline_entry)
        margin = (
            round(overall_score - baseline_score, 4)
            if overall_score is not None and baseline_score is not None
            else None
        )
        default_lane = "annotated_animatic"
        adoption_state = "experimental_manual"
        if overall_score is not None:
            beats_baseline = baseline_score is None or overall_score > baseline_score
            if not blockers and beats_baseline and overall_score >= _QUALITY_FLOOR:
                default_lane = "ai_previz"
                adoption_state = "default"
            elif beats_baseline and overall_score >= _QUALITY_FLOOR:
                adoption_state = "recommended_optional"

        lane = PrevizLaneStatus(
            lane_id="ai_previz",
            label="AI Previz",
            candidate_label=_CANDIDATE_LABELS.get(engine_pack_id),
            adoption_state=adoption_state,
            reason=self._reason_for(
                adoption_state=adoption_state,
                engine_pack=engine_pack,
                blockers=blockers,
            ),
            blocker_reasons=blockers,
            overall_score=overall_score,
            baseline_score=baseline_score,
            score_margin=margin,
            measured_at=self._measured_at(score_entry),
            latency_ms=self._latency_ms(score_entry),
            engine_pack_id=engine_pack.pack_id,
            target_model=engine_pack.target_model,
            resolution=self._resolution(params=params, engine_pack=engine_pack),
            duration_seconds=self._duration_seconds(params=params, engine_pack=engine_pack),
            consistency_strategy=self._consistency_strategy(params=params),
            cost=cost,
            validation_stage_enabled=self._validation_stage_enabled(recipe),
        )
        return PrevizAdoptionStatus(default_lane=default_lane, ai_previz=lane)

    def _blockers_for(
        self,
        *,
        recipe: dict[str, Any],
        params: dict[str, Any],
        engine_pack: EnginePack,
        score_entry: dict[str, Any] | None,
        baseline_entry: dict[str, Any] | None,
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

        baseline_score = self._overall_score(baseline_entry)
        if overall_score is not None and baseline_score is not None:
            margin = overall_score - baseline_score
            if margin < _DEFAULT_MARGIN:
                blockers.append(
                    f"AI previz leads Annotated Animatic by only {margin:.3f}; the "
                    f"default-switch gate requires at least {_DEFAULT_MARGIN:.2f}."
                )

        latency_ms = self._latency_ms(score_entry)
        if latency_ms is not None and latency_ms > _LATENCY_LIMIT_MS:
            blockers.append(
                f"Measured AI previz latency is {latency_ms} ms, above the "
                f"{_LATENCY_LIMIT_MS} ms fast-previz envelope."
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
    ) -> str:
        if adoption_state == "default":
            return (
                f"{_CANDIDATE_LABELS.get(engine_pack.pack_id, 'AI previz')} currently clears "
                "the usefulness, latency, and cost gates, so AI previz can be the default lane."
            )
        if adoption_state == "recommended_optional":
            return (
                f"{_CANDIDATE_LABELS.get(engine_pack.pack_id, 'AI previz')} is strong enough to "
                "recommend as an optional lane, but the deterministic default should stay in place "
                "until the remaining blockers clear."
            )
        if blockers:
            return blockers[0]
        return (
            f"{_CANDIDATE_LABELS.get(engine_pack.pack_id, 'AI previz')} remains a manual lane "
            "until the adoption evidence improves."
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

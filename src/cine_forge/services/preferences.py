"""Transparent preference-learning helpers for design-study decisions."""

from __future__ import annotations

import json
import uuid
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import (
    ArtifactMetadata,
    ArtifactRef,
    PreferenceCue,
    PreferenceLearningSettings,
    PreferenceProfile,
    PreferenceSignal,
)
from cine_forge.schemas.design_study import EntityType as DesignStudyEntityType
from cine_forge.schemas.design_study import ImageDecision

_ACTIVE_DECISIONS: frozenset[ImageDecision] = frozenset(
    {"selected_final", "favorite", "rejected", "seed_for_variants"}
)

_DECISION_WEIGHT: dict[ImageDecision, float] = {
    "pending": 0.0,
    "selected_final": 2.0,
    "favorite": 1.0,
    "rejected": 1.5,
    "seed_for_variants": 1.5,
}


def _normalize_text(value: str) -> str:
    return " ".join(value.strip().lower().split())


def _clean_text(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.strip().split())
    return cleaned or None


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _decision_polarity(decision: ImageDecision) -> str:
    if decision in {"selected_final", "favorite"}:
        return "positive"
    if decision == "rejected":
        return "negative"
    if decision == "seed_for_variants":
        return "directional"
    return "neutral"


class PreferenceService:
    """Persist preference signals and derive transparent project-level profiles."""

    def __init__(self, project_dir: Path) -> None:
        self.project_dir = project_dir
        self.store = ArtifactStore(project_dir=project_dir)

    def get_settings(self) -> PreferenceLearningSettings:
        project_json_path = self.project_dir / "project.json"
        if not project_json_path.exists():
            return PreferenceLearningSettings()

        try:
            project_json = json.loads(project_json_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return PreferenceLearningSettings()

        raw_enabled = project_json.get("preference_learning_enabled", True)
        enabled = raw_enabled if isinstance(raw_enabled, bool) else True
        cleared_at = _parse_datetime(project_json.get("preference_learning_cleared_at"))
        return PreferenceLearningSettings(enabled=enabled, cleared_at=cleared_at)

    def record_design_study_signal(
        self,
        *,
        entity_id: str,
        entity_type: DesignStudyEntityType,
        round_number: int,
        image_filename: str,
        decision: ImageDecision,
        guidance: str | None,
        round_guidance: str | None,
        prompt_used: str,
        prompt_sources_used: list[str],
        model: str | None,
        lineage_refs: list[ArtifactRef] | None = None,
    ) -> PreferenceSignal:
        signal = PreferenceSignal(
            signal_id=f"prefsig-{uuid.uuid4().hex[:12]}",
            entity_id=entity_id,
            entity_type=entity_type,
            round_number=round_number,
            image_filename=image_filename,
            decision=decision,
            polarity=_decision_polarity(decision),
            guidance=_clean_text(guidance),
            round_guidance=_clean_text(round_guidance),
            prompt_used=prompt_used,
            prompt_sources_used=list(prompt_sources_used),
            model=model,
        )
        metadata = ArtifactMetadata(
            lineage=list(lineage_refs or []),
            intent="Record a user preference-learning signal from a design-study decision.",
            rationale=(
                f"Captured decision '{decision}' for image '{image_filename}' in"
                f" design-study round {round_number}."
            ),
            confidence=1.0,
            source="human",
            producing_module="operator_console.preference_learning",
        )
        self.store.save_artifact(
            artifact_type="preference_signal",
            entity_id="project",
            data=signal.model_dump(mode="json"),
            metadata=metadata,
        )
        return signal

    def list_preference_signals(self) -> list[PreferenceSignal]:
        refs = self.store.list_versions("preference_signal", "project")
        signals: list[PreferenceSignal] = []
        for ref in refs:
            artifact = self.store.load_artifact(ref)
            signals.append(PreferenceSignal.model_validate(artifact.data))
        signals.sort(key=lambda signal: signal.created_at)
        return signals

    def list_active_signals(
        self,
        settings: PreferenceLearningSettings | None = None,
    ) -> list[PreferenceSignal]:
        effective_settings = settings or self.get_settings()
        signals = self.list_preference_signals()
        if effective_settings.cleared_at is not None:
            signals = [
                signal
                for signal in signals
                if signal.created_at > effective_settings.cleared_at
            ]

        latest_by_image: dict[tuple[str, str], PreferenceSignal] = {}
        for signal in signals:
            latest_by_image[(signal.entity_id, signal.image_filename)] = signal

        active_signals = [
            signal
            for signal in latest_by_image.values()
            if signal.decision in _ACTIVE_DECISIONS
        ]
        active_signals.sort(key=lambda signal: signal.created_at, reverse=True)
        return active_signals

    def build_profile(self) -> PreferenceProfile:
        settings = self.get_settings()
        active_signals = self.list_active_signals(settings)
        preferred_cues = self._build_cues(active_signals, cue_type="preferred")
        avoid_cues = self._build_cues(active_signals, cue_type="avoid")
        variation_cues = self._build_cues(active_signals, cue_type="variation")
        summary_lines = self._build_summary_lines(
            active_signals=active_signals,
            preferred_cues=preferred_cues,
            avoid_cues=avoid_cues,
            variation_cues=variation_cues,
        )
        entity_count = len({signal.entity_id for signal in active_signals})
        return PreferenceProfile(
            enabled=settings.enabled,
            last_cleared_at=settings.cleared_at,
            active_signal_count=len(active_signals),
            entity_count=entity_count,
            summary_lines=summary_lines,
            preferred_cues=preferred_cues,
            avoid_cues=avoid_cues,
            variation_cues=variation_cues,
            recent_signals=active_signals[:12],
        )

    def build_prompt_context_for_entity(
        self,
        *,
        entity_id: str,
        entity_type: DesignStudyEntityType,
    ) -> list[str]:
        settings = self.get_settings()
        if not settings.enabled:
            return []

        active_signals = [
            signal
            for signal in self.list_active_signals(settings)
            if signal.entity_id == entity_id and signal.entity_type == entity_type
        ]
        if not active_signals:
            return []

        lines: list[str] = []
        positive_signals = [
            signal for signal in active_signals if signal.decision in {"selected_final", "favorite"}
        ]
        preferred_texts = self._texts_for_signals(positive_signals, include_round_guidance=True)
        if preferred_texts:
            lines.append(
                "Lean toward these previously approved directions: "
                f"{'; '.join(preferred_texts[:3])}."
            )
        elif positive_signals:
            lines.append(
                "Preserve continuity with the user's recently approved and favorited"
                " design direction for this entity."
            )

        variation_signals = [
            signal for signal in active_signals if signal.decision == "seed_for_variants"
        ]
        variation_texts = self._texts_for_signals(variation_signals, include_round_guidance=True)
        if variation_texts:
            lines.append(
                "Carry forward these requested refinements: "
                f"{'; '.join(variation_texts[:3])}."
            )

        rejected_signals = [
            signal for signal in active_signals if signal.decision == "rejected"
        ]
        rejected_texts = self._texts_for_signals(rejected_signals, include_round_guidance=False)
        if rejected_texts:
            lines.append(
                "Avoid previously rejected directions such as: "
                f"{'; '.join(rejected_texts[:3])}."
            )

        return lines[:3]

    def _build_cues(
        self,
        active_signals: list[PreferenceSignal],
        *,
        cue_type: str,
    ) -> list[PreferenceCue]:
        grouped: dict[tuple[str, str, str], PreferenceCue] = {}
        for signal in active_signals:
            texts: list[str] = []
            if cue_type == "preferred" and signal.decision in {"selected_final", "favorite"}:
                texts = self._texts_for_signals([signal], include_round_guidance=True)
            elif cue_type == "avoid" and signal.decision == "rejected":
                texts = self._texts_for_signals([signal], include_round_guidance=False)
            elif cue_type == "variation" and signal.decision == "seed_for_variants":
                texts = self._texts_for_signals([signal], include_round_guidance=True)

            for text in texts:
                key = (signal.entity_id, cue_type, _normalize_text(text))
                cue = grouped.get(key)
                if cue is None:
                    grouped[key] = PreferenceCue(
                        cue_type=cue_type,
                        entity_id=signal.entity_id,
                        entity_type=signal.entity_type,
                        text=text,
                        weight=_DECISION_WEIGHT[signal.decision],
                        signal_count=1,
                        source_signal_ids=[signal.signal_id],
                        source_image_filenames=[signal.image_filename],
                    )
                    continue
                cue.weight += _DECISION_WEIGHT[signal.decision]
                cue.signal_count += 1
                cue.source_signal_ids.append(signal.signal_id)
                if signal.image_filename not in cue.source_image_filenames:
                    cue.source_image_filenames.append(signal.image_filename)

        cues = list(grouped.values())
        cues.sort(key=lambda cue: (-cue.weight, cue.text.lower()))
        return cues[:8]

    def _build_summary_lines(
        self,
        *,
        active_signals: list[PreferenceSignal],
        preferred_cues: list[PreferenceCue],
        avoid_cues: list[PreferenceCue],
        variation_cues: list[PreferenceCue],
    ) -> list[str]:
        if not active_signals:
            return ["No active learned preferences yet."]

        counts = Counter(signal.decision for signal in active_signals)
        lines: list[str] = []
        if counts["selected_final"] or counts["favorite"]:
            lines.append(
                "Approved references tracked: "
                f"{counts['selected_final']} final, {counts['favorite']} favorite."
            )
        if variation_cues:
            lines.append(
                "Requested refinements: "
                + "; ".join(cue.text for cue in variation_cues[:3])
                + "."
            )
        elif counts["seed_for_variants"]:
            lines.append(
                f"Variant-direction signals recorded: {counts['seed_for_variants']}."
            )
        if avoid_cues:
            lines.append(
                "Avoided directions: " + "; ".join(cue.text for cue in avoid_cues[:3]) + "."
            )
        elif counts["rejected"]:
            lines.append(f"Rejected directions tracked: {counts['rejected']}.")
        if preferred_cues:
            lines.append(
                "Positive direction cues: "
                + "; ".join(cue.text for cue in preferred_cues[:3])
                + "."
            )
        return lines

    def _texts_for_signals(
        self,
        signals: list[PreferenceSignal],
        *,
        include_round_guidance: bool,
    ) -> list[str]:
        texts: list[str] = []
        seen: set[str] = set()
        for signal in signals:
            candidates = [signal.guidance]
            if include_round_guidance:
                candidates.append(signal.round_guidance)
            for candidate in candidates:
                cleaned = _clean_text(candidate)
                if not cleaned:
                    continue
                normalized = _normalize_text(cleaned)
                if normalized in seen:
                    continue
                seen.add(normalized)
                texts.append(cleaned)
        return texts

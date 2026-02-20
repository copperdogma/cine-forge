"""Director + canon-guardian stage gating workflow."""

from __future__ import annotations

from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import (
    ArtifactMetadata,
    ArtifactRef,
    DirectorReview,
    DisagreementRecord,
    GuardianReview,
    ReviewDecision,
    ReviewReadiness,
    RoleResponse,
    StageReviewArtifact,
)

from .runtime import RoleContext, RoleRuntimeError
from .suggestion import SuggestionManager

CANON_GUARDIANS: tuple[str, ...] = ("script_supervisor", "continuity_supervisor")


class CanonGateError(RuntimeError):
    """Raised when canon-gating invariants are violated."""


class CanonGate:
    """Execute guardian + director review and persist immutable stage review artifacts."""

    def __init__(self, role_context: RoleContext, store: ArtifactStore) -> None:
        self.role_context = role_context
        self.store = store

    def review_stage(
        self,
        *,
        stage_id: str,
        scene_id: str,
        artifact_refs: list[ArtifactRef],
        control_mode: str,
        user_approved: bool | None = None,
        input_payload: dict[str, Any] | None = None,
    ) -> ArtifactRef:
        if control_mode not in {"autonomous", "checkpoint", "advisory"}:
            raise CanonGateError(f"Unsupported control mode: {control_mode}")

        payload = input_payload or {}
        guardian_reviews = [
            self._guardian_review(
                guardian_role_id=guardian_role_id,
                stage_id=stage_id,
                scene_id=scene_id,
                artifact_refs=artifact_refs,
                input_payload=payload,
            )
            for guardian_role_id in CANON_GUARDIANS
        ]

        director_review = self._director_review(
            stage_id=stage_id,
            scene_id=scene_id,
            artifact_refs=artifact_refs,
            guardian_reviews=guardian_reviews,
            control_mode=control_mode,
            input_payload=payload,
        )

        disagreements = self._build_disagreements(
            director_review=director_review,
            guardian_reviews=guardian_reviews,
            artifact_refs=artifact_refs,
        )
        readiness = self._resolve_readiness(
            guardian_reviews=guardian_reviews,
            director_review=director_review,
            control_mode=control_mode,
            user_approved=user_approved,
        )

        # Resurface deferred suggestions
        suggestion_manager = SuggestionManager(self.store)
        deferred_models = suggestion_manager.list_deferred_suggestions(scene_id=scene_id)
        # Convert to ArtifactRef list
        deferred_refs: list[ArtifactRef] = []
        for sugg in deferred_models:
            versions = self.store.list_versions(
                artifact_type="suggestion", entity_id=sugg.suggestion_id
            )
            if versions:
                deferred_refs.append(versions[-1])

        stage_review = StageReviewArtifact(
            stage_id=stage_id,
            scene_id=scene_id,
            control_mode=control_mode,
            reviewed_artifacts=artifact_refs,
            guardian_reviews=guardian_reviews,
            director_review=director_review,
            disagreements=disagreements,
            deferred_suggestions=deferred_refs,
            user_approved=user_approved,
            readiness=readiness,
        )
        metadata = ArtifactMetadata(
            lineage=list(artifact_refs),
            intent=f"Canon gate review for scene '{scene_id}' at stage '{stage_id}'.",
            rationale="Guardians reviewed narrative/continuity and Director resolved progression.",
            confidence=min(review.confidence for review in guardian_reviews + [director_review]),
            source="ai",
            producing_module="canon_gate_v1",
            producing_role="director",
            health="valid",
            annotations={
                "control_mode": control_mode,
                "readiness": stage_review.readiness.value,
                "guardian_roles": [review.role_id for review in guardian_reviews],
            },
        )
        return self.store.save_artifact(
            artifact_type="stage_review",
            entity_id=f"{scene_id}_{stage_id}",
            data=stage_review.model_dump(mode="json"),
            metadata=metadata,
        )

    def _guardian_review(
        self,
        *,
        guardian_role_id: str,
        stage_id: str,
        scene_id: str,
        artifact_refs: list[ArtifactRef],
        input_payload: dict[str, Any],
    ) -> GuardianReview:
        response = self.role_context.invoke(
            role_id=guardian_role_id,
            prompt=(
                "Review scene-stage canon consistency and return decision `sign_off` or `block`. "
                "Include concise objections for anything that must block progression."
            ),
            inputs={
                "media_types": ["text"],
                "stage_id": stage_id,
                "scene_id": scene_id,
                "artifact_refs": [ref.model_dump(mode="json") for ref in artifact_refs],
                "context": input_payload,
            },
        )
        decision = self._resolve_decision(response=response, allow_override=False)
        return GuardianReview(
            role_id=guardian_role_id,  # type: ignore[arg-type]
            decision=decision,
            summary=response.content,
            rationale=response.rationale,
            confidence=response.confidence,
            objections=list(response.objections),
        )

    def _director_review(
        self,
        *,
        stage_id: str,
        scene_id: str,
        artifact_refs: list[ArtifactRef],
        guardian_reviews: list[GuardianReview],
        control_mode: str,
        input_payload: dict[str, Any],
    ) -> DirectorReview:
        response = self.role_context.invoke(
            role_id="director",
            prompt=(
                "Review guardian assessments and return decision "
                "`sign_off`, `block`, or `override` "
                "for scene-stage progression."
            ),
            inputs={
                "media_types": ["text"],
                "stage_id": stage_id,
                "scene_id": scene_id,
                "control_mode": control_mode,
                "artifact_refs": [ref.model_dump(mode="json") for ref in artifact_refs],
                "guardian_reviews": [review.model_dump(mode="json") for review in guardian_reviews],
                "context": input_payload,
            },
        )
        decision = self._resolve_decision(response=response, allow_override=True)
        override_justification = (
            response.override_justification.strip()
            if response.override_justification
            else None
        )
        if decision == ReviewDecision.OVERRIDE and not override_justification:
            raise CanonGateError("Director override requires explicit override_justification.")
        return DirectorReview(
            decision=decision,
            summary=response.content,
            rationale=response.rationale,
            confidence=response.confidence,
            included_roles=list(response.included_roles),
            override_justification=override_justification,
        )

    @staticmethod
    def _resolve_decision(*, response: RoleResponse, allow_override: bool) -> ReviewDecision:
        raw_decision = (response.decision or "").strip().lower()
        if raw_decision == "sign_off":
            return ReviewDecision.SIGN_OFF
        if raw_decision == "block":
            return ReviewDecision.BLOCK
        if raw_decision == "override" and allow_override:
            return ReviewDecision.OVERRIDE

        # Conservative fallback: any unresolved objection blocks progression.
        if response.objections:
            return ReviewDecision.BLOCK
        return ReviewDecision.SIGN_OFF

    @staticmethod
    def _build_disagreements(
        *,
        director_review: DirectorReview,
        guardian_reviews: list[GuardianReview],
        artifact_refs: list[ArtifactRef],
    ) -> list[DisagreementRecord]:
        if director_review.decision != ReviewDecision.OVERRIDE:
            return []
        if not director_review.override_justification:
            raise CanonGateError("Director override missing explicit justification.")

        disagreements: list[DisagreementRecord] = []
        for guardian_review in guardian_reviews:
            if guardian_review.decision != ReviewDecision.BLOCK:
                continue
            disagreements.append(
                DisagreementRecord(
                    guardian_role_id=guardian_review.role_id,
                    objection_summary=guardian_review.summary,
                    objection_rationale=guardian_review.rationale,
                    director_override_rationale=director_review.override_justification,
                    linked_artifacts=list(artifact_refs),
                )
            )
        return disagreements

    @staticmethod
    def _resolve_readiness(
        *,
        guardian_reviews: list[GuardianReview],
        director_review: DirectorReview,
        control_mode: str,
        user_approved: bool | None,
    ) -> ReviewReadiness:
        blocked_guardians = [
            review for review in guardian_reviews if review.decision == ReviewDecision.BLOCK
        ]
        if blocked_guardians and director_review.decision != ReviewDecision.OVERRIDE:
            return ReviewReadiness.BLOCKED
        if director_review.decision == ReviewDecision.BLOCK:
            return ReviewReadiness.BLOCKED
        if control_mode == "checkpoint" and user_approved is not True:
            return ReviewReadiness.AWAITING_USER
        return ReviewReadiness.READY


def assert_director_can_override(
    *, role_context: RoleContext, blocked_by_role_id: str, justification: str
) -> bool:
    """Reusable override-authorization check with explicit justification requirement."""
    if not justification.strip():
        raise CanonGateError("Director override requires explicit justification.")
    try:
        return role_context.catalog.validate_override(
            overriding_role_id="director",
            blocked_by_role_id=blocked_by_role_id,
            justification=justification,
        )
    except RoleRuntimeError as exc:
        raise CanonGateError(str(exc)) from exc

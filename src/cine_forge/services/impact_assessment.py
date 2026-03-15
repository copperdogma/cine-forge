"""Semantic impact assessment service for Story 031."""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

from pydantic import BaseModel, Field

from cine_forge.ai import call_llm, estimate_cost_usd
from cine_forge.artifacts import ArtifactStore
from cine_forge.roles.runtime import RoleCatalog, RoleRuntimeError
from cine_forge.schemas import (
    ArtifactHealth,
    ArtifactImpact,
    ArtifactMetadata,
    ArtifactRef,
    CostRecord,
    Decision,
    ImpactAssessment,
)

DEFAULT_IMPACT_MODEL = "claude-sonnet-4-6"
DEFAULT_ASSESSING_ROLE = "director"
_PROMPT_CHAR_LIMIT = 12_000
_ESTIMATED_OUTPUT_TOKENS_PER_ARTIFACT = 300


class ImpactAssessmentError(RuntimeError):
    """Raised when an impact assessment request is invalid."""


class ImpactPreviewTarget(BaseModel):
    """UI/API preview entry for one stale artifact."""

    artifact_ref: ArtifactRef
    artifact_type: str
    entity_id: str | None = None
    current_health: str


class ImpactPreview(BaseModel):
    """Preview of stale scope and estimated assessment cost."""

    trigger_artifact_ref: ArtifactRef
    requested_artifact_ref: ArtifactRef
    total_stale: int = Field(ge=0)
    affected_types: list[str] = Field(default_factory=list)
    estimated_cost: CostRecord
    budget_cap_usd: float | None = Field(default=None, ge=0.0)
    within_budget: bool = True
    targets: list[ImpactPreviewTarget] = Field(default_factory=list)


class _ArtifactImpactVerdict(BaseModel):
    assessed_health: str = Field(pattern="^(needs_revision|confirmed_valid)$")
    rationale: str = Field(min_length=1)
    upstream_change_summary: str = Field(min_length=1)
    suggested_revision: str | None = None
    confidence: float = Field(ge=0.0, le=1.0)


class ImpactAssessmentService:
    """Run semantic impact assessment and manual health transitions."""

    def __init__(
        self,
        *,
        project_dir: Any,
        store: ArtifactStore | None = None,
        role_catalog: RoleCatalog | None = None,
        llm_callable: Any = call_llm,
    ) -> None:
        self.store = store or ArtifactStore(project_dir=project_dir)
        self.role_catalog = role_catalog or RoleCatalog()
        self.role_catalog.load_definitions()
        self._llm_callable = llm_callable

    def preview_scope(
        self,
        artifact_ref: ArtifactRef,
        *,
        selected_refs: list[ArtifactRef] | None = None,
        model: str | None = None,
        budget_cap_usd: float | None = None,
    ) -> ImpactPreview:
        """Return stale scope and estimated cost for the relevant trigger."""
        requested_ref = self._require_latest_ref(artifact_ref)
        trigger_ref = self._resolve_trigger_ref(requested_ref)
        stale_refs = self._get_pending_stale_refs(trigger_ref)
        refs_to_preview = self._resolve_assessment_scope(
            trigger_ref, stale_refs, selected_refs=selected_refs
        )
        model_name = model or DEFAULT_IMPACT_MODEL

        estimated_cost = self._estimate_cost_record(trigger_ref, refs_to_preview, model_name)
        affected_types = sorted({ref.artifact_type for ref in refs_to_preview})
        targets = [
            ImpactPreviewTarget(
                artifact_ref=ref,
                artifact_type=ref.artifact_type,
                entity_id=ref.entity_id,
                current_health=self.store.graph.get_health(ref).value
                if self.store.graph.get_health(ref)
                else ArtifactHealth.VALID.value,
            )
            for ref in refs_to_preview
        ]
        return ImpactPreview(
            trigger_artifact_ref=trigger_ref,
            requested_artifact_ref=requested_ref,
            total_stale=len(refs_to_preview),
            affected_types=affected_types,
            estimated_cost=estimated_cost,
            budget_cap_usd=budget_cap_usd,
            within_budget=(
                budget_cap_usd is None
                or estimated_cost.estimated_cost_usd <= budget_cap_usd
            ),
            targets=targets,
        )

    def run_assessment(
        self,
        artifact_ref: ArtifactRef,
        *,
        selected_refs: list[ArtifactRef] | None = None,
        model: str | None = None,
        role_id: str | None = None,
        budget_cap_usd: float | None = None,
    ) -> tuple[ArtifactRef, ImpactAssessment]:
        """Run semantic impact assessment for stale artifacts tied to one trigger."""
        requested_ref = self._require_latest_ref(artifact_ref)
        trigger_ref = self._resolve_trigger_ref(requested_ref)
        stale_refs = self._get_pending_stale_refs(trigger_ref)
        if not stale_refs:
            raise ImpactAssessmentError("No stale artifacts remain for this trigger.")

        model_name = model or DEFAULT_IMPACT_MODEL
        refs_to_assess = self._resolve_assessment_scope(
            trigger_ref, stale_refs, selected_refs=selected_refs
        )
        estimated_cost = self._estimate_cost_record(trigger_ref, refs_to_assess, model_name)
        self._enforce_budget_cap(estimated_cost, budget_cap_usd)
        assessing_role = role_id or DEFAULT_ASSESSING_ROLE
        role_prompt = self._build_role_prompt(assessing_role)
        trigger_ref_previous = self._previous_ref(trigger_ref)
        if trigger_ref_previous is None:
            raise ImpactAssessmentError(
                f"Trigger artifact {trigger_ref.key()} has no previous version to diff."
            )

        diff = self.store.diff_versions(trigger_ref_previous, trigger_ref)
        diff_summary = self._format_diff_summary(diff)

        assessments: list[ArtifactImpact] = []
        total_input_tokens = 0
        total_output_tokens = 0
        total_cost_usd = 0.0

        for downstream_ref in refs_to_assess:
            verdict, cost_meta = self._assess_artifact(
                trigger_previous_ref=trigger_ref_previous,
                trigger_ref=trigger_ref,
                downstream_ref=downstream_ref,
                diff_summary=diff_summary,
                role_prompt=role_prompt,
                model=model_name,
            )
            cost = CostRecord.model_validate(cost_meta)
            total_input_tokens += cost.input_tokens
            total_output_tokens += cost.output_tokens
            total_cost_usd += cost.estimated_cost_usd
            assessments.append(
                ArtifactImpact(
                    artifact_ref=downstream_ref,
                    previous_health=ArtifactHealth.STALE.value,
                    assessed_health=verdict.assessed_health,
                    rationale=verdict.rationale,
                    upstream_change_summary=verdict.upstream_change_summary,
                    suggested_revision=verdict.suggested_revision,
                    confidence=verdict.confidence,
                    assessing_role=assessing_role,
                )
            )

        assessment = ImpactAssessment(
            trigger_artifact_ref=trigger_ref,
            trigger_diff_summary=diff_summary,
            assessments=assessments,
            total_stale=len(stale_refs),
            total_needs_revision=sum(
                1
                for item in assessments
                if item.assessed_health == ArtifactHealth.NEEDS_REVISION.value
            ),
            total_confirmed_valid=sum(
                1
                for item in assessments
                if item.assessed_health == ArtifactHealth.CONFIRMED_VALID.value
            ),
            assessment_cost=CostRecord(
                model=model_name,
                input_tokens=total_input_tokens,
                output_tokens=total_output_tokens,
                estimated_cost_usd=round(total_cost_usd, 8),
            ),
        )

        metadata = ArtifactMetadata(
            lineage=[trigger_ref, *refs_to_assess],
            intent="Assess semantic impact of an upstream artifact change.",
            rationale=(
                "AI triage determines which downstream artifacts still need work after an "
                "upstream revision."
            ),
            confidence=(
                sum(item.confidence for item in assessments) / len(assessments)
                if assessments
                else 1.0
            ),
            source="ai",
            producing_module="impact_assessment_v1",
            producing_role=assessing_role,
            cost_data=assessment.assessment_cost,
        )
        assessment_ref = self.store.save_artifact(
            artifact_type="impact_assessment",
            entity_id=self._artifact_group_id(trigger_ref),
            data=assessment.model_dump(mode="json"),
            metadata=metadata,
        )

        for item in assessments:
            self.store.graph.set_assessment_result(
                item.artifact_ref,
                assessed_health=ArtifactHealth(item.assessed_health),
                trigger_ref=trigger_ref,
                source_artifact_ref=assessment_ref,
                rationale=item.rationale,
                upstream_change_summary=item.upstream_change_summary,
                suggested_revision=item.suggested_revision,
                confidence=item.confidence,
                assessing_role=item.assessing_role,
            )

        return assessment_ref, assessment

    def manual_override(
        self,
        artifact_ref: ArtifactRef,
        *,
        target_health: ArtifactHealth,
        rationale: str,
        decided_by: str = "human",
    ) -> ArtifactRef:
        """Persist and apply a manual health override."""
        if target_health == ArtifactHealth.STALE:
            raise ImpactAssessmentError("Manual override cannot set an artifact back to stale.")
        target_ref = self._require_latest_ref(artifact_ref)
        health_info = self.store.graph.get_health_info(target_ref) or {}
        trigger_ref = self._ref_from_payload(health_info.get("trigger_ref"))
        decision = Decision(
            decision_id=f"impact-{uuid.uuid4().hex[:8]}",
            decided_by=decided_by,
            summary=self._manual_summary(target_health),
            rationale=rationale,
            alternatives_considered=[],
            informed_by_suggestions=[],
            affected_artifacts=[target_ref],
        )
        metadata = ArtifactMetadata(
            lineage=[target_ref],
            intent="Record a manual health decision for an artifact.",
            rationale=rationale,
            confidence=1.0,
            source="human" if decided_by == "human" else "hybrid",
            producing_module="impact_assessment_v1",
            producing_role=None if decided_by == "human" else decided_by,
        )
        decision_ref = self.store.save_artifact(
            artifact_type="decision",
            entity_id=self._artifact_group_id(target_ref),
            data=decision.model_dump(mode="json"),
            metadata=metadata,
        )
        self.store.graph.set_manual_health_override(
            target_ref,
            health=target_health,
            trigger_ref=trigger_ref,
            source_artifact_ref=decision_ref,
            rationale=rationale,
            decided_by=decided_by,
        )
        return decision_ref

    def _assess_artifact(
        self,
        *,
        trigger_previous_ref: ArtifactRef,
        trigger_ref: ArtifactRef,
        downstream_ref: ArtifactRef,
        diff_summary: str,
        role_prompt: str,
        model: str,
    ) -> tuple[_ArtifactImpactVerdict, dict[str, Any]]:
        previous_trigger = self.store.load_artifact(trigger_previous_ref)
        current_trigger = self.store.load_artifact(trigger_ref)
        downstream = self.store.load_artifact(downstream_ref)

        prompt = (
            f"{role_prompt}\n\n"
            "You are evaluating semantic change propagation.\n"
            "Decide whether the downstream artifact still holds after the upstream change.\n"
            "Return JSON with fields: assessed_health, rationale, upstream_change_summary, "
            "suggested_revision, confidence.\n"
            "Choose `confirmed_valid` only when the downstream artifact remains correct despite "
            "the change. Choose `needs_revision` when the downstream artifact's content, framing, "
            "or logic depends on the old upstream state. When in doubt, choose needs_revision.\n\n"
            f"Upstream previous version ({trigger_previous_ref.key()}):\n"
            f"{self._truncate_json(previous_trigger.data)}\n\n"
            f"Upstream current version ({trigger_ref.key()}):\n"
            f"{self._truncate_json(current_trigger.data)}\n\n"
            f"Structured diff summary:\n{diff_summary}\n\n"
            f"Downstream artifact ({downstream_ref.key()}):\n"
            f"{self._truncate_json(downstream.data)}"
        )
        verdict, cost_meta = self._llm_callable(
            prompt=prompt,
            model=model,
            response_schema=_ArtifactImpactVerdict,
            max_tokens=900,
            temperature=0.1,
            fail_on_truncation=True,
        )
        if isinstance(verdict, _ArtifactImpactVerdict):
            return verdict, cost_meta
        return _ArtifactImpactVerdict.model_validate(verdict), cost_meta

    def _build_role_prompt(self, role_id: str) -> str:
        try:
            role = self.role_catalog.get_role(role_id)
        except RoleRuntimeError as exc:
            raise ImpactAssessmentError(f"Unknown assessing role: {role_id}") from exc
        return role.system_prompt

    def _resolve_trigger_ref(self, artifact_ref: ArtifactRef) -> ArtifactRef:
        health_info = self.store.graph.get_health_info(artifact_ref) or {}
        trigger_ref = self._ref_from_payload(health_info.get("trigger_ref"))
        return trigger_ref or artifact_ref

    def _get_pending_stale_refs(self, trigger_ref: ArtifactRef) -> list[ArtifactRef]:
        refs = self.store.graph.get_refs_for_trigger(trigger_ref, ArtifactHealth.STALE)
        return sorted(refs, key=lambda ref: (ref.artifact_type, ref.entity_id or "", ref.version))

    def _resolve_assessment_scope(
        self,
        trigger_ref: ArtifactRef,
        stale_refs: list[ArtifactRef],
        *,
        selected_refs: list[ArtifactRef] | None = None,
    ) -> list[ArtifactRef]:
        if not selected_refs:
            return stale_refs

        allowed_keys = {ref.key() for ref in stale_refs}
        refs_to_assess = sorted(
            (self._require_latest_ref(ref) for ref in selected_refs),
            key=lambda ref: (ref.artifact_type, ref.entity_id or "", ref.version),
        )
        invalid = [ref.key() for ref in refs_to_assess if ref.key() not in allowed_keys]
        if invalid:
            raise ImpactAssessmentError(
                "Selected artifacts must be currently stale descendants of the trigger "
                f"{trigger_ref.key()}: " + ", ".join(invalid)
            )
        return refs_to_assess

    def _require_latest_ref(self, artifact_ref: ArtifactRef) -> ArtifactRef:
        if not self.store.is_latest_ref(artifact_ref):
            latest = self.store.latest_ref(artifact_ref.artifact_type, artifact_ref.entity_id)
            if latest is None:
                raise ImpactAssessmentError(f"Artifact does not exist: {artifact_ref.key()}")
            raise ImpactAssessmentError(
                f"Impact actions only operate on the latest artifact version. "
                f"Open {latest.key()} instead of {artifact_ref.key()}."
            )
        return artifact_ref

    def _previous_ref(self, artifact_ref: ArtifactRef) -> ArtifactRef | None:
        if artifact_ref.version <= 1:
            return None
        versions = self.store.list_versions(artifact_ref.artifact_type, artifact_ref.entity_id)
        previous = next((ref for ref in versions if ref.version == artifact_ref.version - 1), None)
        return previous

    def _format_diff_summary(self, diff: dict[str, Any]) -> str:
        if not diff:
            return "No structured field-level differences were detected."
        lines: list[str] = []
        for path, change in list(diff.items())[:12]:
            kind = change.get("kind")
            if kind == "changed":
                lines.append(f"- {path}: {change.get('from')} -> {change.get('to')}")
            elif kind == "added":
                lines.append(f"- {path}: added {change.get('to')}")
            elif kind == "removed":
                lines.append(f"- {path}: removed {change.get('from')}")
        if len(diff) > 12:
            lines.append(f"- ...and {len(diff) - 12} more changes")
        return "\n".join(lines)

    def _estimate_prompt_tokens(self, trigger_ref: ArtifactRef, downstream_ref: ArtifactRef) -> int:
        trigger_previous_ref = self._previous_ref(trigger_ref)
        if trigger_previous_ref is None:
            return 0
        trigger_previous = self.store.load_artifact(trigger_previous_ref)
        trigger_current = self.store.load_artifact(trigger_ref)
        downstream = self.store.load_artifact(downstream_ref)
        total_chars = sum(
            len(self._truncate_json(artifact.data))
            for artifact in (trigger_previous, trigger_current, downstream)
        )
        return max(200, total_chars // 4)

    def _estimate_cost_record(
        self,
        trigger_ref: ArtifactRef,
        downstream_refs: list[ArtifactRef],
        model_name: str,
    ) -> CostRecord:
        estimated_input_tokens = sum(
            self._estimate_prompt_tokens(trigger_ref, downstream_ref)
            for downstream_ref in downstream_refs
        )
        estimated_output_tokens = (
            len(downstream_refs) * _ESTIMATED_OUTPUT_TOKENS_PER_ARTIFACT
        )
        return CostRecord(
            model=model_name,
            input_tokens=estimated_input_tokens,
            output_tokens=estimated_output_tokens,
            estimated_cost_usd=estimate_cost_usd(
                model_name,
                estimated_input_tokens,
                estimated_output_tokens,
            ),
        )

    def _enforce_budget_cap(
        self,
        estimated_cost: CostRecord,
        budget_cap_usd: float | None,
    ) -> None:
        if budget_cap_usd is None:
            return
        if estimated_cost.estimated_cost_usd <= budget_cap_usd:
            return
        raise ImpactAssessmentError(
            "Estimated assessment cost "
            f"{self._format_usd(estimated_cost.estimated_cost_usd)} exceeds the "
            f"budget cap {self._format_usd(budget_cap_usd)}. "
            "Reduce the selected scope or raise the cap."
        )

    def _truncate_json(self, payload: dict[str, Any]) -> str:
        serialized = json.dumps(payload, indent=2, sort_keys=True)
        if len(serialized) <= _PROMPT_CHAR_LIMIT:
            return serialized
        return serialized[:_PROMPT_CHAR_LIMIT] + "\n...[truncated]"

    def _artifact_group_id(self, artifact_ref: ArtifactRef) -> str:
        key = artifact_ref.key().replace(":", "_")
        return re.sub(r"[^a-zA-Z0-9_]+", "_", key)

    def _manual_summary(self, target_health: ArtifactHealth) -> str:
        if target_health == ArtifactHealth.VALID:
            return "Manual acknowledgement marked the artifact current."
        if target_health == ArtifactHealth.NEEDS_REVISION:
            return "Manual triage marked the artifact as needing revision."
        if target_health == ArtifactHealth.CONFIRMED_VALID:
            return "Manual triage confirmed the artifact remains valid."
        return "Manual health override recorded."

    def _ref_from_payload(self, payload: Any) -> ArtifactRef | None:
        if not payload:
            return None
        try:
            return ArtifactRef.model_validate(payload)
        except Exception:
            return None

    def _format_usd(self, value: float) -> str:
        return f"${value:.4f}"

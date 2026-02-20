"""Runtime loader and invocation contract for CineForge AI roles."""

from __future__ import annotations

import json
import threading
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from cine_forge.ai.llm import call_llm
from cine_forge.artifacts import ArtifactStore
from cine_forge.schemas import (
    ArtifactMetadata,
    CostRecord,
    PerceptionCapability,
    RoleDefinition,
    RoleResponse,
    RoleTier,
    StylePack,
    StylePackSlot,
    Suggestion,
)

TIER_ORDER: dict[RoleTier, int] = {
    RoleTier.PERFORMANCE: 1,
    RoleTier.STRUCTURAL_ADVISOR: 2,
    RoleTier.CANON_GUARDIAN: 3,
    RoleTier.CANON_AUTHORITY: 4,
}

ACTION_MIN_TIER: dict[str, RoleTier] = {
    "suggest": RoleTier.PERFORMANCE,
    "propose_change": RoleTier.STRUCTURAL_ADVISOR,
    "block_progression": RoleTier.CANON_GUARDIAN,
    "finalize_canon": RoleTier.CANON_AUTHORITY,
    "override_objection": RoleTier.CANON_AUTHORITY,
}

# Current runtime transport supports text-only prompting.
MODEL_CAPABILITIES: dict[str, set[PerceptionCapability]] = {
    "mock": {PerceptionCapability.TEXT},
    "fixture": {PerceptionCapability.TEXT},
}


class _StructuredRoleAnswer(BaseModel):
    content: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(min_length=1)
    decision: str | None = None
    override_justification: str | None = None
    included_roles: list[str] = Field(default_factory=list)
    objections: list[str] = Field(default_factory=list)
    suggestions: list[dict[str, Any]] = Field(default_factory=list)


class RoleRuntimeError(RuntimeError):
    """Raised when role loading or invocation invariants are violated."""


class RoleCatalog:
    """Load role definitions and style packs from disk."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or Path(__file__).resolve().parent
        self._roles: dict[str, RoleDefinition] = {}

    def load_definitions(self) -> dict[str, RoleDefinition]:
        roles: dict[str, RoleDefinition] = {}
        for role_file in sorted(self.root.glob("*/role.yaml")):
            payload = yaml.safe_load(role_file.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise RoleRuntimeError(f"Invalid role definition format: {role_file}")
            role = RoleDefinition.model_validate(payload)
            if role.role_id in roles:
                raise RoleRuntimeError(f"Duplicate role_id '{role.role_id}' in {role_file}")
            roles[role.role_id] = role
        if not roles:
            raise RoleRuntimeError(f"No role definitions found in {self.root}")
        self._roles = roles
        return roles

    def list_roles(self) -> dict[str, RoleDefinition]:
        if not self._roles:
            return self.load_definitions()
        return dict(self._roles)

    def get_role(self, role_id: str) -> RoleDefinition:
        roles = self.list_roles()
        try:
            return roles[role_id]
        except KeyError as exc:
            raise RoleRuntimeError(f"Unknown role_id: {role_id}") from exc

    def get_hierarchy_tier(self, role_id: str) -> RoleTier:
        return self.get_role(role_id).tier

    def can_role_perform(self, role_id: str, action: str) -> bool:
        role = self.get_role(role_id)
        required_tier = ACTION_MIN_TIER.get(action)
        if required_tier is None:
            return False
        return TIER_ORDER[role.tier] >= TIER_ORDER[required_tier]

    def can_propose_artifact(self, role_id: str, artifact_type: str) -> bool:
        role = self.get_role(role_id)
        return artifact_type in set(role.permissions)

    def validate_override(
        self,
        *,
        overriding_role_id: str,
        blocked_by_role_id: str,
        justification: str,
    ) -> bool:
        if not justification.strip():
            raise RoleRuntimeError("Override requires explicit justification")
        overriding_tier = self.get_hierarchy_tier(overriding_role_id)
        blocked_tier = self.get_hierarchy_tier(blocked_by_role_id)
        if TIER_ORDER[overriding_tier] <= TIER_ORDER[blocked_tier]:
            raise RoleRuntimeError(
                "Override denied: overriding role must be higher tier than blocking role"
            )
        return True

    def check_capability(self, role_id: str, media_type: str) -> bool:
        role = self.get_role(role_id)
        return any(cap.value == media_type for cap in role.capabilities)

    def load_style_pack(self, role_id: str, style_pack_id: str = "generic") -> StylePack:
        role = self.get_role(role_id)
        if role.style_pack_slot == StylePackSlot.FORBIDDEN:
            raise RoleRuntimeError(f"Role '{role_id}' does not accept style packs")

        manifest_path = (
            self.root
            / "style_packs"
            / role_id
            / style_pack_id
            / "manifest.yaml"
        )
        if not manifest_path.exists():
            raise RoleRuntimeError(f"Missing style pack manifest: {manifest_path}")
        payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise RoleRuntimeError(f"Invalid style pack manifest: {manifest_path}")
        style_pack = StylePack.model_validate(payload)
        if style_pack.role_id != role_id:
            raise RoleRuntimeError(
                f"Style pack role mismatch for '{manifest_path}': expected {role_id}"
            )
        return style_pack

    def list_style_packs(self, role_id: str) -> list[StylePack]:
        role = self.get_role(role_id)
        if role.style_pack_slot == StylePackSlot.FORBIDDEN:
            return []

        style_dir = self.root / "style_packs" / role_id
        if not style_dir.exists():
            return []

        style_packs: list[StylePack] = []
        for pack_dir in style_dir.iterdir():
            if not pack_dir.is_dir():
                continue
            manifest_path = pack_dir / "manifest.yaml"
            if not manifest_path.exists():
                continue
            try:
                payload = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
                style_pack = StylePack.model_validate(payload)
                if style_pack.role_id == role_id:
                    style_packs.append(style_pack)
            except Exception:
                # Skip invalid manifests during listing to be robust
                continue
        return sorted(style_packs, key=lambda p: p.style_pack_id)


class RoleContext:
    """Module-facing role invocation interface."""

    def __init__(
        self,
        *,
        catalog: RoleCatalog,
        project_dir: Path,
        store: ArtifactStore | None = None,
        model_resolver: Callable[[str], str] | None = None,
        style_pack_selections: dict[str, str] | None = None,
        llm_callable: Callable[..., tuple[str | BaseModel, dict[str, Any]]] = call_llm,
    ) -> None:
        self.catalog = catalog
        self.project_dir = project_dir
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.store = store
        self._log_path = self.project_dir / "role_invocations.jsonl"
        self._log_lock = threading.Lock()
        self._model_resolver = model_resolver or (lambda _role_id: "mock")
        self._style_pack_selections = style_pack_selections or {}
        self._llm_callable = llm_callable

        # Validate style-pack assignments on startup.
        for role_id, style_pack_id in self._style_pack_selections.items():
            role = self.catalog.get_role(role_id)
            if role.style_pack_slot == StylePackSlot.FORBIDDEN:
                raise RoleRuntimeError(
                    f"Role '{role_id}' rejects style packs but was assigned '{style_pack_id}'"
                )

    def invoke(self, role_id: str, prompt: str, inputs: dict[str, Any]) -> RoleResponse:
        role = self.catalog.get_role(role_id)
        media_types = inputs.get("media_types", ["text"])
        if not isinstance(media_types, list) or not media_types:
            raise RoleRuntimeError("inputs.media_types must be a non-empty list")

        for media_type in media_types:
            if not self.check_capability(role_id, str(media_type)):
                raise RoleRuntimeError(
                    f"Role '{role_id}' lacks declared capability for media '{media_type}'"
                )

        model = self._model_resolver(role_id)
        required_capabilities = [PerceptionCapability(str(item)) for item in media_types]
        self._assert_model_supports_request(
            role_id=role.role_id,
            model=model,
            required_capabilities=required_capabilities,
        )

        system_prompt = self._compose_system_prompt(role)
        task_payload = {
            "task": prompt,
            "inputs": inputs,
        }
        final_prompt = (
            f"{system_prompt}\n\n"
            "Return JSON with fields: content (string), confidence (0..1), rationale (string).\n"
            f"Task payload:\n{json.dumps(task_payload, sort_keys=True)}"
        )

        response_obj, cost_meta = self._llm_callable(
            prompt=final_prompt,
            model=model,
            response_schema=_StructuredRoleAnswer,
            max_tokens=1200,
            fail_on_truncation=True,
        )
        if isinstance(response_obj, BaseModel):
            response_payload = response_obj.model_dump(mode="json")
        elif isinstance(response_obj, dict):
            response_payload = response_obj
        else:
            raise RoleRuntimeError("Role invocation expected structured response")
        structured_response = _StructuredRoleAnswer.model_validate(response_payload)

        response = RoleResponse(
            role_id=role_id,
            content=structured_response.content,
            confidence=structured_response.confidence,
            rationale=structured_response.rationale,
            decision=structured_response.decision,
            override_justification=structured_response.override_justification,
            included_roles=list(structured_response.included_roles),
            objections=list(structured_response.objections),
            suggestions=list(structured_response.suggestions),
            cost_data=CostRecord.model_validate(cost_meta),
        )

        if self.store and response.suggestions:
            for sugg_payload in response.suggestions:
                # Augment payload with system metadata if missing
                sugg_id = f"sugg-{uuid.uuid4().hex[:8]}"
                suggestion = Suggestion(
                    suggestion_id=sugg_id,
                    source_role=role_id,
                    proposal=sugg_payload.get("proposal", "No proposal provided"),
                    rationale=sugg_payload.get("rationale", "No rationale provided"),
                    confidence=sugg_payload.get("confidence", response.confidence),
                    related_scene_id=sugg_payload.get("related_scene_id"),
                    related_entity_id=sugg_payload.get("related_entity_id"),
                    related_artifact_ref=sugg_payload.get("related_artifact_ref"),
                )
                metadata = ArtifactMetadata(
                    intent="Capture creative suggestion from role invocation.",
                    rationale="Roles continuously generate insights recorded as suggestions.",
                    confidence=suggestion.confidence,
                    source="ai",
                    producing_module="role_runtime_v1",
                    producing_role=role_id,
                )
                self.store.save_artifact(
                    artifact_type="suggestion",
                    entity_id=suggestion.suggestion_id,
                    data=suggestion.model_dump(mode="json"),
                    metadata=metadata,
                )
                response.suggestion_ids.append(sugg_id)

        self._log_invocation(
            role=role,
            model=model,
            style_pack_id=self._style_pack_selections.get(role_id),
            prompt=prompt,
            inputs=inputs,
            response=response,
        )
        return response

    def check_capability(self, role_id: str, media_type: str) -> bool:
        return self.catalog.check_capability(role_id=role_id, media_type=media_type)

    def get_hierarchy_tier(self, role_id: str) -> str:
        return self.catalog.get_hierarchy_tier(role_id).value

    def _compose_system_prompt(self, role: RoleDefinition) -> str:
        if role.style_pack_slot == StylePackSlot.FORBIDDEN:
            return role.system_prompt
        style_pack_id = self._style_pack_selections.get(role.role_id, "generic")
        style_pack = self.catalog.load_style_pack(role.role_id, style_pack_id=style_pack_id)
        return (
            f"{role.system_prompt}\n\n"
            f"Style Pack ({style_pack.display_name}):\n"
            f"{style_pack.prompt_injection}"
        )

    def _assert_model_supports_request(
        self,
        *,
        role_id: str,
        model: str,
        required_capabilities: list[PerceptionCapability],
    ) -> None:
        model_caps = MODEL_CAPABILITIES.get(model, {PerceptionCapability.TEXT})
        missing = [cap.value for cap in required_capabilities if cap not in model_caps]
        if missing:
            raise RoleRuntimeError(
                f"Model '{model}' lacks capabilities required for role '{role_id}': {missing}"
            )

    def _log_invocation(
        self,
        *,
        role: RoleDefinition,
        model: str,
        style_pack_id: str | None,
        prompt: str,
        inputs: dict[str, Any],
        response: RoleResponse,
    ) -> None:
        log_record = {
            "created_at": datetime.now(UTC).isoformat(),
            "role_id": role.role_id,
            "tier": role.tier.value,
            "model": model,
            "style_pack_id": style_pack_id,
            "prompt": prompt,
            "inputs": inputs,
            "response": response.model_dump(mode="json"),
            "cost_usd": response.cost_data.estimated_cost_usd if response.cost_data else 0.0,
        }
        with self._log_lock:
            with self._log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(log_record, sort_keys=True) + "\n")

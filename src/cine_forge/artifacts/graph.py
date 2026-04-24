"""Artifact dependency graph for structural invalidation."""

from __future__ import annotations

import json
import threading
import time
from collections import deque
from datetime import UTC, datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from cine_forge.schemas import ArtifactHealth, ArtifactRef


class DependencyGraph:
    """Persistent artifact dependency graph.

    Thread-safe: all read-modify-write cycles are serialised by ``_lock``.
    """

    _lock_registry_guard = threading.Lock()
    _lock_registry: dict[Path, threading.Lock] = {}

    def __init__(self, project_dir: Path) -> None:
        self._graph_path = project_dir / "graph" / "dependency_graph.json"
        self._graph_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = self._shared_lock_for_path(self._graph_path)
        if not self._graph_path.exists():
            self._write_graph({"nodes": {}})

    def register_artifact(
        self,
        artifact_ref: ArtifactRef,
        upstream_refs: list[ArtifactRef],
    ) -> None:
        with self._lock:
            graph = self._read_graph()
            nodes = graph["nodes"]
            node_key = artifact_ref.key()
            nodes.setdefault(
                node_key,
                {
                    "ref": artifact_ref.model_dump(),
                    "upstream": [],
                    "downstream": [],
                    "health": ArtifactHealth.VALID.value,
                },
            )
            nodes[node_key]["upstream"] = [upstream.key() for upstream in upstream_refs]
            nodes[node_key]["ref"] = artifact_ref.model_dump()

            for upstream in upstream_refs:
                upstream_key = upstream.key()
                nodes.setdefault(
                    upstream_key,
                    {
                        "ref": upstream.model_dump(),
                        "upstream": [],
                        "downstream": [],
                        "health": ArtifactHealth.VALID.value,
                    },
                )
                if node_key not in nodes[upstream_key]["downstream"]:
                    nodes[upstream_key]["downstream"].append(node_key)

            self._write_graph(graph)

    def propagate_stale_for_new_version(self, new_ref: ArtifactRef) -> list[ArtifactRef]:
        """Mark dependents of the previous version as stale."""
        if new_ref.version <= 1:
            return []
        previous_ref = ArtifactRef(
            artifact_type=new_ref.artifact_type,
            entity_id=new_ref.entity_id,
            version=new_ref.version - 1,
            path=new_ref.path,
        )
        previous_key = previous_ref.key()
        with self._lock:
            graph = self._read_graph()
            nodes = graph["nodes"]
            if previous_key not in nodes:
                return []

            # Build latest-version lookup for each (artifact_type, entity_id) pair.
            # Used below to stop BFS at superseded intermediate nodes and prevent
            # sibling cross-contamination: if idx:v2 is the intermediate and idx:v3
            # already exists, the downstream was rebuilt from idx:v3 — BFS stops at v2.
            latest_version: dict[tuple[str, str | None], int] = {}
            for node in nodes.values():
                ref = ArtifactRef.model_validate(node["ref"])
                ek = (ref.artifact_type, ref.entity_id)
                if ref.version > latest_version.get(ek, 0):
                    latest_version[ek] = ref.version

            stale_refs: list[ArtifactRef] = []
            new_key = new_ref.key()
            queue = deque(nodes[previous_key]["downstream"])
            seen: set[str] = {new_key}  # never mark the new version itself as stale
            while queue:
                node_key = queue.popleft()
                if node_key in seen or node_key not in nodes:
                    continue
                seen.add(node_key)
                nodes[node_key]["health"] = ArtifactHealth.STALE.value
                nodes[node_key]["stale_cause"] = new_ref.key()
                nodes[node_key]["health_context"] = self._build_health_context(
                    source_kind="structural_invalidation",
                    trigger_ref=new_ref,
                    source_artifact_ref=None,
                    reason="Upstream artifact changed and this artifact now needs review.",
                )
                stale_refs.append(ArtifactRef.model_validate(nodes[node_key]["ref"]))
                # If a newer version of this node exists, its downstream was already
                # rebuilt from fresh data — mark stale here but stop BFS propagation
                # to prevent contaminating sibling artifacts via shared intermediates.
                ref = ArtifactRef.model_validate(nodes[node_key]["ref"])
                ek = (ref.artifact_type, ref.entity_id)
                if ref.version < latest_version.get(ek, ref.version):
                    continue
                queue.extend(nodes[node_key]["downstream"])

            self._write_graph(graph)
        return stale_refs

    def get_dependencies(self, artifact_ref: ArtifactRef) -> list[ArtifactRef]:
        with self._lock:
            graph = self._read_graph()
        node = graph["nodes"].get(artifact_ref.key())
        if not node:
            return []
        return [ArtifactRef.model_validate(graph["nodes"][key]["ref"]) for key in node["upstream"]]

    def get_dependents(self, artifact_ref: ArtifactRef) -> list[ArtifactRef]:
        with self._lock:
            graph = self._read_graph()
        node = graph["nodes"].get(artifact_ref.key())
        if not node:
            return []
        return [
            ArtifactRef.model_validate(graph["nodes"][key]["ref"]) for key in node["downstream"]
        ]

    def get_stale(self) -> list[ArtifactRef]:
        with self._lock:
            graph = self._read_graph()
        return self._collect_refs_by_health(
            graph=graph,
            healths={ArtifactHealth.STALE},
        )

    def get_refs_by_health(self, *healths: ArtifactHealth) -> list[ArtifactRef]:
        """Return artifact refs whose live graph health matches any provided state."""
        if not healths:
            return []
        with self._lock:
            graph = self._read_graph()
        return self._collect_refs_by_health(graph=graph, healths=set(healths))

    def get_stale_with_causes(self) -> list[tuple[ArtifactRef, str | None]]:
        """Return stale artifacts with the cause key that triggered staleness.

        Returns list of (stale_ref, cause_key) tuples where cause_key is the
        artifact ref key (e.g., "canonical_script:__project__:v3") of the
        upstream artifact whose new version triggered the staleness cascade.
        """
        with self._lock:
            graph = self._read_graph()
        return [
            (
                ArtifactRef.model_validate(node["ref"]),
                node.get("stale_cause"),
            )
            for node in graph["nodes"].values()
            if node["health"] == ArtifactHealth.STALE.value
        ]

    def get_health(self, artifact_ref: ArtifactRef) -> ArtifactHealth | None:
        with self._lock:
            graph = self._read_graph()
        node = graph["nodes"].get(artifact_ref.key())
        if not node:
            return None
        return ArtifactHealth(node["health"])

    def get_health_info(self, artifact_ref: ArtifactRef) -> dict[str, Any] | None:
        """Return current graph health plus provenance context for one artifact."""
        with self._lock:
            graph = self._read_graph()
        node = graph["nodes"].get(artifact_ref.key())
        if not node:
            return None
        context = dict(node.get("health_context") or {})
        return {
            "health": node["health"],
            "trigger_ref": context.get("trigger_ref"),
            "source_artifact_ref": context.get("source_artifact_ref"),
            "source_kind": context.get("source_kind"),
            "reason": context.get("reason"),
            "upstream_change_summary": context.get("upstream_change_summary"),
            "suggested_revision": context.get("suggested_revision"),
            "confidence": context.get("confidence"),
            "assessing_role": context.get("assessing_role"),
            "decided_by": context.get("decided_by"),
            "updated_at": context.get("updated_at"),
        }

    def get_refs_for_trigger(
        self,
        trigger_ref: ArtifactRef,
        *healths: ArtifactHealth,
    ) -> list[ArtifactRef]:
        """Return refs whose live health context points at *trigger_ref*."""
        with self._lock:
            graph = self._read_graph()
        allowed = set(healths) if healths else None
        refs: list[ArtifactRef] = []
        trigger_key = trigger_ref.key()
        for node in graph["nodes"].values():
            node_health = ArtifactHealth(node["health"])
            if allowed and node_health not in allowed:
                continue
            context = node.get("health_context") or {}
            context_trigger = context.get("trigger_ref")
            if isinstance(context_trigger, dict):
                try:
                    if ArtifactRef.model_validate(context_trigger).key() != trigger_key:
                        continue
                except Exception:
                    continue
            elif node.get("stale_cause") != trigger_key:
                continue
            refs.append(ArtifactRef.model_validate(node["ref"]))
        return refs

    def set_assessment_result(
        self,
        artifact_ref: ArtifactRef,
        *,
        assessed_health: ArtifactHealth,
        trigger_ref: ArtifactRef,
        source_artifact_ref: ArtifactRef,
        rationale: str,
        upstream_change_summary: str,
        suggested_revision: str | None,
        confidence: float,
        assessing_role: str,
    ) -> None:
        """Persist the live outcome of an impact assessment in graph state."""
        if assessed_health not in {
            ArtifactHealth.NEEDS_REVISION,
            ArtifactHealth.CONFIRMED_VALID,
        }:
            raise ValueError(f"Unsupported assessed health: {assessed_health}")
        with self._lock:
            graph = self._read_graph()
            node = graph["nodes"].get(artifact_ref.key())
            if not node:
                raise KeyError(f"Unknown artifact ref: {artifact_ref.key()}")
            node["health"] = assessed_health.value
            node["health_context"] = self._build_health_context(
                source_kind="impact_assessment",
                trigger_ref=trigger_ref,
                source_artifact_ref=source_artifact_ref,
                reason=rationale,
                upstream_change_summary=upstream_change_summary,
                suggested_revision=suggested_revision,
                confidence=confidence,
                assessing_role=assessing_role,
            )
            self._write_graph(graph)

    def set_manual_health_override(
        self,
        artifact_ref: ArtifactRef,
        *,
        health: ArtifactHealth,
        trigger_ref: ArtifactRef | None,
        source_artifact_ref: ArtifactRef | None,
        rationale: str,
        decided_by: str,
    ) -> None:
        """Apply a manual health decision while preserving provenance context."""
        with self._lock:
            graph = self._read_graph()
            node = graph["nodes"].get(artifact_ref.key())
            if not node:
                raise KeyError(f"Unknown artifact ref: {artifact_ref.key()}")
            node["health"] = health.value
            if health == ArtifactHealth.VALID:
                node["stale_cause"] = None
            node["health_context"] = self._build_health_context(
                source_kind="manual_override",
                trigger_ref=trigger_ref,
                source_artifact_ref=source_artifact_ref,
                reason=rationale,
                decided_by=decided_by,
            )
            self._write_graph(graph)

    def _read_graph(self) -> dict:
        last_error: json.JSONDecodeError | None = None
        for attempt in range(4):
            try:
                with self._graph_path.open("r", encoding="utf-8") as file:
                    return json.load(file)
            except json.JSONDecodeError as exc:
                last_error = exc
                if attempt == 3:
                    raise
                # Another graph instance may still be finishing an atomic replace.
                time.sleep(0.01 * (attempt + 1))
        assert last_error is not None
        raise last_error

    def _write_graph(self, graph: dict) -> None:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=self._graph_path.parent,
            prefix=f"{self._graph_path.stem}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            json.dump(graph, file, indent=2, sort_keys=True)
            file.flush()
            temp_path = Path(file.name)
        temp_path.replace(self._graph_path)

    @classmethod
    def _shared_lock_for_path(cls, graph_path: Path) -> threading.Lock:
        with cls._lock_registry_guard:
            return cls._lock_registry.setdefault(graph_path.resolve(), threading.Lock())

    def _collect_refs_by_health(
        self,
        *,
        graph: dict[str, Any],
        healths: set[ArtifactHealth],
    ) -> list[ArtifactRef]:
        health_values = {health.value for health in healths}
        return [
            ArtifactRef.model_validate(node["ref"])
            for node in graph["nodes"].values()
            if node["health"] in health_values
        ]

    def _build_health_context(
        self,
        *,
        source_kind: str,
        trigger_ref: ArtifactRef | None,
        source_artifact_ref: ArtifactRef | None,
        reason: str | None,
        upstream_change_summary: str | None = None,
        suggested_revision: str | None = None,
        confidence: float | None = None,
        assessing_role: str | None = None,
        decided_by: str | None = None,
    ) -> dict[str, Any]:
        return {
            "source_kind": source_kind,
            "trigger_ref": trigger_ref.model_dump(mode="json") if trigger_ref else None,
            "source_artifact_ref": (
                source_artifact_ref.model_dump(mode="json") if source_artifact_ref else None
            ),
            "reason": reason,
            "upstream_change_summary": upstream_change_summary,
            "suggested_revision": suggested_revision,
            "confidence": confidence,
            "assessing_role": assessing_role,
            "decided_by": decided_by,
            "updated_at": datetime.now(UTC).isoformat(),
        }

"""Artifact dependency graph for structural invalidation."""

from __future__ import annotations

import json
import threading
from collections import deque
from pathlib import Path

from cine_forge.schemas import ArtifactHealth, ArtifactRef


class DependencyGraph:
    """Persistent artifact dependency graph.

    Thread-safe: all read-modify-write cycles are serialised by ``_lock``.
    """

    def __init__(self, project_dir: Path) -> None:
        self._graph_path = project_dir / "graph" / "dependency_graph.json"
        self._graph_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
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
        return [
            ArtifactRef.model_validate(node["ref"])
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

    def _read_graph(self) -> dict:
        with self._graph_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def _write_graph(self, graph: dict) -> None:
        with self._graph_path.open("w", encoding="utf-8") as file:
            json.dump(graph, file, indent=2, sort_keys=True)

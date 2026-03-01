"""Pipeline capability graph: static definition + dynamic status computation.

The graph has two levels:
1. **Nodes** — individual pipeline capabilities (script_import, scene_extraction,
   character_bibles, editorial_direction, etc.). Each maps to one or more artifact
   types and has dependencies on other nodes.
2. **Phases** — user-facing groups of related nodes (Script, World, Direction,
   Shots, etc.). The pipeline bar shows phases; the AI and future DAG view use nodes.

Graph structure is STATIC (defined in code, same for all projects).
Node status is DYNAMIC (computed from artifact store at query time).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from cine_forge.artifacts import ArtifactStore

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class NodeStatus(StrEnum):
    """Status of an individual pipeline node."""

    COMPLETED = "completed"
    STALE = "stale"
    IN_PROGRESS = "in_progress"
    AVAILABLE = "available"
    BLOCKED = "blocked"
    NOT_IMPLEMENTED = "not_implemented"


class PhaseStatus(StrEnum):
    """Status of a user-facing pipeline phase."""

    COMPLETED = "completed"
    PARTIAL = "partial"
    AVAILABLE = "available"
    BLOCKED = "blocked"
    NOT_STARTED = "not_started"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PipelineNode:
    """A single pipeline capability (e.g., scene extraction, character bibles)."""

    id: str
    label: str
    phase_id: str
    # Artifact types whose existence indicates this node has output.
    artifact_types: list[str]
    # How to check existence: "project" = list_versions(type, "project"),
    # "bible" = list_bible_entries(entity_type), "entity" = list_entities(type).
    check_mode: str = "project"
    # For bible checks: which entity type to query.
    bible_entity_type: str | None = None
    # IDs of nodes that must be completed before this node is available.
    dependencies: list[str] = field(default_factory=list)
    # Frontend navigation route when clicked.
    nav_route: str | None = None
    # Whether the module actually exists in the codebase.
    implemented: bool = True


@dataclass(frozen=True)
class PipelinePhase:
    """A user-facing group of related pipeline nodes."""

    id: str
    label: str
    icon: str  # Lucide icon name
    node_ids: list[str]
    nav_route: str | None = None


# ---------------------------------------------------------------------------
# Static graph definition
# ---------------------------------------------------------------------------

PIPELINE_NODES: list[PipelineNode] = [
    # --- Script phase ---
    PipelineNode(
        id="script_import",
        label="Script Import",
        phase_id="script",
        artifact_types=["raw_input"],
        nav_route="/",
    ),
    PipelineNode(
        id="normalization",
        label="Normalization",
        phase_id="script",
        artifact_types=["canonical_script"],
        dependencies=["script_import"],
    ),
    PipelineNode(
        id="script_bible",
        label="Script Bible",
        phase_id="script",
        artifact_types=["script_bible"],
        dependencies=["normalization"],
        nav_route="/",
    ),
    PipelineNode(
        id="scene_extraction",
        label="Scene Extraction",
        phase_id="script",
        artifact_types=["scene_index"],
        dependencies=["normalization"],
        nav_route="/scenes",
    ),
    PipelineNode(
        id="project_config",
        label="Project Config",
        phase_id="script",
        artifact_types=["project_config"],
        dependencies=["script_import"],
    ),

    # --- World phase ---
    PipelineNode(
        id="entity_discovery",
        label="Entity Discovery",
        phase_id="world",
        artifact_types=["entity_discovery_results"],
        dependencies=["scene_extraction"],
    ),
    PipelineNode(
        id="characters",
        label="Characters",
        phase_id="world",
        artifact_types=["character_bible"],
        check_mode="bible",
        bible_entity_type="character",
        dependencies=["entity_discovery"],
        nav_route="/characters",
    ),
    PipelineNode(
        id="locations",
        label="Locations",
        phase_id="world",
        artifact_types=["location_bible"],
        check_mode="bible",
        bible_entity_type="location",
        dependencies=["entity_discovery"],
        nav_route="/locations",
    ),
    PipelineNode(
        id="props",
        label="Props",
        phase_id="world",
        artifact_types=["prop_bible"],
        check_mode="bible",
        bible_entity_type="prop",
        dependencies=["entity_discovery"],
        nav_route="/props",
    ),
    PipelineNode(
        id="entity_graph",
        label="Relationships",
        phase_id="world",
        artifact_types=["entity_graph"],
        dependencies=["characters", "locations", "props"],
    ),
    PipelineNode(
        id="continuity",
        label="Continuity",
        phase_id="world",
        artifact_types=["continuity_index"],
        dependencies=["characters", "locations", "props", "scene_extraction"],
    ),

    # --- Direction phase (concern groups, ADR-003) ---
    PipelineNode(
        id="intent_mood",
        label="Intent & Mood",
        phase_id="direction",
        artifact_types=["intent_mood"],
        dependencies=["scene_extraction"],
        nav_route="/intent",
    ),
    PipelineNode(
        id="rhythm_and_flow",
        label="Rhythm & Flow",
        phase_id="direction",
        artifact_types=["rhythm_and_flow_index", "rhythm_and_flow"],
        dependencies=["scene_extraction", "characters"],
    ),
    PipelineNode(
        id="look_and_feel",
        label="Look & Feel",
        phase_id="direction",
        artifact_types=["look_and_feel_index", "look_and_feel"],
        dependencies=["scene_extraction", "characters", "locations"],
        implemented=True,
    ),
    PipelineNode(
        id="sound_and_music",
        label="Sound & Music",
        phase_id="direction",
        artifact_types=["sound_and_music", "sound_and_music_index"],
        dependencies=["scene_extraction"],
        implemented=True,
    ),
    PipelineNode(
        id="character_and_performance",
        label="Character & Performance",
        phase_id="direction",
        artifact_types=["character_and_performance"],
        dependencies=["scene_extraction", "characters"],
        implemented=True,
    ),
    PipelineNode(
        id="story_world",
        label="Story World",
        phase_id="direction",
        artifact_types=["story_world"],
        dependencies=["characters", "locations", "props"],
        implemented=True,
    ),

    # --- Shots phase (future) ---
    PipelineNode(
        id="shot_planning",
        label="Shot Planning",
        phase_id="shots",
        artifact_types=["shot_plan"],
        dependencies=["rhythm_and_flow", "look_and_feel", "sound_and_music"],
        implemented=False,
    ),
    PipelineNode(
        id="coverage",
        label="Coverage Analysis",
        phase_id="shots",
        artifact_types=["coverage_report"],
        dependencies=["shot_planning"],
        implemented=False,
    ),

    # --- Storyboards phase (future) ---
    PipelineNode(
        id="storyboard_gen",
        label="Storyboards",
        phase_id="storyboards",
        artifact_types=["storyboard"],
        dependencies=["shot_planning"],
        implemented=False,
    ),
    PipelineNode(
        id="animatics",
        label="Animatics",
        phase_id="storyboards",
        artifact_types=["animatic"],
        dependencies=["storyboard_gen"],
        implemented=False,
    ),

    # --- Production phase (future) ---
    PipelineNode(
        id="render",
        label="Render",
        phase_id="production",
        artifact_types=["render_output"],
        dependencies=["storyboard_gen"],
        implemented=False,
    ),
    PipelineNode(
        id="final_output",
        label="Final Output",
        phase_id="production",
        artifact_types=["final_output"],
        dependencies=["render"],
        implemented=False,
    ),
]

PIPELINE_PHASES: list[PipelinePhase] = [
    PipelinePhase(
        id="script",
        label="Script",
        icon="FileText",
        node_ids=[
            "script_import", "normalization", "script_bible",
            "scene_extraction", "project_config",
        ],
        nav_route="/",
    ),
    PipelinePhase(
        id="world",
        label="World",
        icon="Globe",
        node_ids=[
            "entity_discovery", "characters", "locations", "props",
            "entity_graph", "continuity",
        ],
        nav_route="/characters",
    ),
    PipelinePhase(
        id="direction",
        label="Direction",
        icon="Compass",
        node_ids=[
            "intent_mood", "rhythm_and_flow", "look_and_feel",
            "sound_and_music", "character_and_performance", "story_world",
        ],
        nav_route="/scenes",
    ),
    PipelinePhase(
        id="shots",
        label="Shots",
        icon="Camera",
        node_ids=["shot_planning", "coverage"],
    ),
    PipelinePhase(
        id="storyboards",
        label="Storyboards",
        icon="LayoutGrid",
        node_ids=["storyboard_gen", "animatics"],
    ),
    PipelinePhase(
        id="production",
        label="Production",
        icon="Film",
        node_ids=["render", "final_output"],
    ),
]

# Index for O(1) lookup.
_NODE_MAP: dict[str, PipelineNode] = {n.id: n for n in PIPELINE_NODES}
_PHASE_MAP: dict[str, PipelinePhase] = {p.id: p for p in PIPELINE_PHASES}

# Node → recipe mapping: which recipe to run to fix/produce a given node.
NODE_FIX_RECIPES: dict[str, str] = {
    "script_import": "mvp_ingest",
    "normalization": "mvp_ingest",
    "script_bible": "mvp_ingest",
    "scene_extraction": "mvp_ingest",
    "project_config": "mvp_ingest",
    "entity_discovery": "world_building",
    "characters": "world_building",
    "locations": "world_building",
    "props": "world_building",
    "entity_graph": "world_building",
    "continuity": "world_building",
    "intent_mood": "creative_direction",
    "rhythm_and_flow": "creative_direction",
    "look_and_feel": "creative_direction",
    "sound_and_music": "creative_direction",
}


# ---------------------------------------------------------------------------
# Status computation
# ---------------------------------------------------------------------------

def _check_node_artifacts(
    node: PipelineNode,
    store: ArtifactStore,
) -> tuple[bool, int]:
    """Check whether a node has output artifacts.

    Returns (has_output, artifact_count).
    """
    if node.check_mode == "bible" and node.bible_entity_type:
        entries = store.list_bible_entries(node.bible_entity_type)
        return len(entries) > 0, len(entries)

    # Default: project-level artifact check.
    for atype in node.artifact_types:
        refs = store.list_versions(atype, "project")
        if refs:
            return True, len(refs)
    return False, 0


def _check_node_staleness(
    node: PipelineNode,
    store: ArtifactStore,
) -> bool:
    """Return True if any of this node's latest artifacts are stale."""
    stale_refs = store.graph.get_stale()
    stale_types = {r.artifact_type for r in stale_refs}
    return bool(stale_types & set(node.artifact_types))


def trace_staleness(
    node: PipelineNode,
    store: ArtifactStore,
) -> str | None:
    """Return a human-readable explanation of why a node is stale.

    Queries the dependency graph for stale artifacts matching this node's
    artifact types, then looks up the cause key to identify which upstream
    artifact was updated.

    Returns None if the node is not stale or no cause is recorded.
    """
    stale_with_causes = store.graph.get_stale_with_causes()
    node_types = set(node.artifact_types)

    for ref, cause_key in stale_with_causes:
        if ref.artifact_type in node_types and cause_key:
            # Parse cause_key: "artifact_type:entity_id:vN"
            parts = cause_key.split(":")
            if len(parts) >= 1:
                cause_type = parts[0]
                # Find a human-readable label for the cause.
                cause_node = next(
                    (n for n in PIPELINE_NODES if cause_type in n.artifact_types),
                    None,
                )
                cause_label = cause_node.label if cause_node else cause_type
                return f"{cause_label} was updated"

    return None


def compute_node_status(
    node: PipelineNode,
    store: ArtifactStore,
    resolved: dict[str, NodeStatus],
    active_stages: set[str] | None = None,
) -> tuple[NodeStatus, int]:
    """Compute the status for a single node.

    Returns (status, artifact_count).
    """
    if not node.implemented:
        return NodeStatus.NOT_IMPLEMENTED, 0

    if active_stages and node.id in active_stages:
        return NodeStatus.IN_PROGRESS, 0

    has_output, count = _check_node_artifacts(node, store)

    if has_output:
        if _check_node_staleness(node, store):
            return NodeStatus.STALE, count
        return NodeStatus.COMPLETED, count

    # No output — check if all dependencies are met.
    for dep_id in node.dependencies:
        dep_node = _NODE_MAP.get(dep_id)
        if dep_node and not dep_node.implemented:
            # Unimplemented dependency — blocked.
            return NodeStatus.BLOCKED, 0
        dep_status = resolved.get(dep_id)
        if dep_status not in (NodeStatus.COMPLETED, NodeStatus.STALE):
            return NodeStatus.BLOCKED, 0

    return NodeStatus.AVAILABLE, 0


def compute_phase_status(
    phase: PipelinePhase,
    node_statuses: dict[str, NodeStatus],
) -> PhaseStatus:
    """Derive phase status from its constituent node statuses."""
    statuses = [node_statuses[nid] for nid in phase.node_ids if nid in node_statuses]
    if not statuses:
        return PhaseStatus.NOT_STARTED

    implemented = [s for s in statuses if s != NodeStatus.NOT_IMPLEMENTED]
    if not implemented:
        # All nodes are unimplemented.
        return PhaseStatus.NOT_STARTED

    if all(s in (NodeStatus.COMPLETED, NodeStatus.STALE) for s in implemented):
        return PhaseStatus.COMPLETED

    active = (NodeStatus.COMPLETED, NodeStatus.STALE, NodeStatus.IN_PROGRESS)
    if any(s in active for s in implemented):
        return PhaseStatus.PARTIAL

    if any(s == NodeStatus.AVAILABLE for s in implemented):
        return PhaseStatus.AVAILABLE

    return PhaseStatus.BLOCKED


def compute_pipeline_graph(
    store: ArtifactStore,
    active_run_stages: set[str] | None = None,
) -> dict[str, Any]:
    """Compute the full pipeline graph with dynamic status.

    Returns a serializable dict:
    {
        "phases": [...],
        "nodes": [...],
        "edges": [{"from": node_id, "to": node_id}, ...],
    }
    """
    node_statuses: dict[str, NodeStatus] = {}
    node_counts: dict[str, int] = {}

    # Resolve statuses in dependency order (topological).
    # Since dependencies always reference earlier nodes, iterating in
    # definition order is sufficient (the list is pre-sorted).
    for node in PIPELINE_NODES:
        status, count = compute_node_status(
            node, store, node_statuses, active_run_stages,
        )
        node_statuses[node.id] = status
        node_counts[node.id] = count

    # Build phase data.
    phases: list[dict[str, Any]] = []
    for phase in PIPELINE_PHASES:
        p_status = compute_phase_status(phase, node_statuses)
        phase_nodes = [nid for nid in phase.node_ids if nid in node_statuses]
        completed_count = sum(
            1 for nid in phase_nodes
            if node_statuses[nid] in (NodeStatus.COMPLETED, NodeStatus.STALE)
        )
        implemented_count = sum(
            1 for nid in phase_nodes
            if node_statuses[nid] != NodeStatus.NOT_IMPLEMENTED
        )
        phases.append({
            "id": phase.id,
            "label": phase.label,
            "icon": phase.icon,
            "status": p_status.value,
            "nav_route": phase.nav_route,
            "completed_count": completed_count,
            "implemented_count": implemented_count,
            "total_count": len(phase_nodes),
        })

    # Build node data.
    nodes: list[dict[str, Any]] = []
    for node in PIPELINE_NODES:
        node_data: dict[str, Any] = {
            "id": node.id,
            "label": node.label,
            "phase_id": node.phase_id,
            "status": node_statuses[node.id].value,
            "artifact_count": node_counts[node.id],
            "dependencies": list(node.dependencies),
            "nav_route": node.nav_route,
            "implemented": node.implemented,
        }
        # Add staleness reason and fix recipe for stale nodes.
        if node_statuses[node.id] == NodeStatus.STALE:
            reason = trace_staleness(node, store)
            if reason:
                node_data["stale_reason"] = reason
            fix = NODE_FIX_RECIPES.get(node.id)
            if fix:
                node_data["fix_recipe"] = fix
        nodes.append(node_data)

    # Build edges.
    edges: list[dict[str, str]] = []
    for node in PIPELINE_NODES:
        for dep_id in node.dependencies:
            edges.append({"from": dep_id, "to": node.id})

    return {
        "phases": phases,
        "nodes": nodes,
        "edges": edges,
    }


# ---------------------------------------------------------------------------
# Navigation helpers
# ---------------------------------------------------------------------------

def get_available_actions(graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Return a prioritized list of actionable next steps from a computed graph.

    Each action includes the node info plus a human-readable reason.
    Results are sorted by priority: nodes whose phase is partially complete
    come first (finish what you started), then nodes in earlier phases.
    """
    phase_order = {p.id: i for i, p in enumerate(PIPELINE_PHASES)}
    phase_status = {p["id"]: p["status"] for p in graph["phases"]}

    available = [
        n for n in graph["nodes"]
        if n["status"] == "available" and n["implemented"]
    ]

    def _priority(node: dict[str, Any]) -> tuple[int, int, str]:
        # Nodes in a partial phase first (finish what you started).
        is_partial = phase_status.get(node["phase_id"]) == "partial"
        return (
            0 if is_partial else 1,
            phase_order.get(node["phase_id"], 99),
            node["label"],
        )

    available.sort(key=_priority)

    actions: list[dict[str, Any]] = []
    for node in available:
        is_partial = phase_status.get(node["phase_id"]) == "partial"
        reason = (
            f"Continue {node['phase_id']} phase (partially complete)"
            if is_partial
            else "All prerequisites met"
        )
        actions.append({
            "node_id": node["id"],
            "label": node["label"],
            "phase_id": node["phase_id"],
            "reason": reason,
        })
    return actions


def check_prerequisites(
    node_id: str,
    graph: dict[str, Any],
) -> dict[str, Any]:
    """Check what's met and what's unmet for a specific node.

    Returns:
        {
            "node_id": str,
            "label": str,
            "is_ready": bool,
            "met": [{"id": str, "label": str, "status": str, "artifact_count": int}],
            "unmet": [{"id": str, "label": str, "status": str, "reason": str}],
        }
    """
    node_def = _NODE_MAP.get(node_id)
    if not node_def:
        return {"node_id": node_id, "label": "?", "is_ready": False, "met": [], "unmet": [
            {"id": node_id, "label": "?", "status": "unknown", "reason": "Node not found"},
        ]}

    node_lookup = {n["id"]: n for n in graph["nodes"]}

    met: list[dict[str, Any]] = []
    unmet: list[dict[str, Any]] = []

    for dep_id in node_def.dependencies:
        dep = node_lookup.get(dep_id, {})
        dep_status = dep.get("status", "unknown")

        if dep_status in ("completed", "stale"):
            met.append({
                "id": dep_id,
                "label": dep.get("label", dep_id),
                "status": dep_status,
                "artifact_count": dep.get("artifact_count", 0),
            })
        else:
            reason_map = {
                "blocked": "Waiting on its own upstream dependencies",
                "available": "Ready to run but hasn't been run yet",
                "in_progress": "Currently running",
                "not_implemented": "Not yet built in CineForge",
            }
            unmet.append({
                "id": dep_id,
                "label": dep.get("label", dep_id),
                "status": dep_status,
                "reason": reason_map.get(dep_status, f"Status: {dep_status}"),
            })

    return {
        "node_id": node_id,
        "label": node_def.label,
        "is_ready": len(unmet) == 0,
        "met": met,
        "unmet": unmet,
    }

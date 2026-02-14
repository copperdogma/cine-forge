"""Extract entity relationship graph from bibles and scene artifacts."""

from __future__ import annotations

from typing import Any

from cine_forge.schemas import (
    EntityEdge,
    EntityGraph,
)


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Execute entity relationship graph extraction."""
    # 1. Extract inputs
    # inputs[stage_id] is a list of artifact data since we used needs_all
    character_bibles = []
    location_bibles = []
    prop_bibles = []
    scene_index = None

    for _stage_id, data_list in inputs.items():
        if not isinstance(data_list, list):
            # Check for single inputs (like scene_index)
            if isinstance(data_list, dict) and "unique_locations" in data_list:
                scene_index = data_list
            continue
            
        for data in data_list:
            if not isinstance(data, dict):
                continue
            # Filter by keys or schema hints since we don't have explicit schema names in data
            if "character_id" in data:
                character_bibles.append(data)
            elif "location_id" in data:
                location_bibles.append(data)
            elif "prop_id" in data:
                prop_bibles.append(data)
            elif "unique_locations" in data:
                scene_index = data

    if not scene_index:
        raise ValueError("entity_graph_v1 requires scene_index input")

    # Tiered Model Strategy
    work_model = params.get("work_model") or params.get("model") or "gpt-4o-mini"
    # verify_model = params.get("verify_model") or "gpt-4o-mini"
    # escalate_model = params.get("escalate_model") or "gpt-4o"
    # skip_qa = bool(params.get("skip_qa", False))

    edges: list[EntityEdge] = []

    # 2. Generate Co-occurrence Edges (Deterministic)
    edges.extend(_generate_co_occurrence_edges(scene_index))

    # 3. Merge Relationship Stubs from Bibles
    edges.extend(_merge_bible_stubs(character_bibles, location_bibles, prop_bibles))

    # 4. AI Extraction Pass (Optional for MVP but required by story)
    # For now, we'll implement a simple pass that looks for missed connections
    if work_model != "mock":
        new_edges, cost = _extract_new_relationships(
            character_bibles, location_bibles, prop_bibles, scene_index, work_model
        )
        edges.extend(new_edges)
    else:
        cost = {"model": "mock", "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0}

    # 5. Deduplicate and Resolve Conflicts
    final_edges = _deduplicate_edges(edges)

    # 6. Build final graph artifact
    entity_counts = {
        "character": len(character_bibles),
        "location": len(location_bibles),
        "prop": len(prop_bibles),
    }
    
    graph = EntityGraph(
        edges=final_edges,
        entity_count=entity_counts,
        edge_count=len(final_edges),
        extraction_confidence=0.85, # aggregate
    )

    return {
        "artifacts": [
            {
                "artifact_type": "entity_graph",
                "entity_id": "project",
                "data": graph.model_dump(mode="json"),
                "metadata": {
                    "intent": "Consolidate all entity relationships into a unified graph.",
                    "rationale": (
                        "Merged relationship stubs from bibles and co-occurrence "
                        "data from scene index."
                    ),
                    "confidence": graph.extraction_confidence,
                    "source": "hybrid",
                },
            }
        ],
        "cost": cost,
    }


def _generate_co_occurrence_edges(scene_index: dict[str, Any]) -> list[EntityEdge]:
    """Create edges between entities that share scenes."""
    edges: list[EntityEdge] = []
    # Simplified co-occurrence: characters in scenes
    for entry in scene_index.get("entries", []):
        scene_id = entry["scene_id"]
        location = entry.get("location")
        characters = entry.get("characters_present", [])
        
        # Character <-> Location
        if location:
            for char in characters:
                edges.append(EntityEdge(
                    source_type="character",
                    source_id=char.lower(), # assume id is slugified name
                    target_type="location",
                    target_id=_slugify(location),
                    relationship_type="presence",
                    direction="symmetric",
                    evidence=[f"Present in scene {scene_id}"],
                    scene_refs=[scene_id],
                    confidence=1.0,
                ))
        
        # Character <-> Character co-occurrence
        for i, char_a in enumerate(characters):
            for char_b in characters[i+1:]:
                edges.append(EntityEdge(
                    source_type="character",
                    source_id=char_a.lower(),
                    target_type="character",
                    target_id=char_b.lower(),
                    relationship_type="co-occurrence",
                    direction="symmetric",
                    evidence=[f"Share scene {scene_id}"],
                    scene_refs=[scene_id],
                    confidence=1.0,
                ))
    return edges


def _merge_bible_stubs(
    characters: list[dict[str, Any]], 
    locations: list[dict[str, Any]], 
    props: list[dict[str, Any]]
) -> list[EntityEdge]:
    """Extract edges from relationship stubs defined in bibles."""
    edges: list[EntityEdge] = []
    
    for char in characters:
        source_id = char["character_id"]
        for stub in char.get("relationships", []):
            edges.append(EntityEdge(
                source_type="character",
                source_id=source_id,
                target_type="character",
                target_id=_slugify(stub["target_character"]),
                relationship_type=stub["relationship_type"],
                direction="source_to_target", # Usually bibles define outgoing
                evidence=[stub["evidence"]],
                confidence=stub["confidence"],
            ))
            
    # Location stubs (containment/adjacency) if implemented in schema
    # ...
    
    return edges


def _extract_new_relationships(
    characters: list[dict[str, Any]],
    locations: list[dict[str, Any]],
    props: list[dict[str, Any]],
    index: dict[str, Any],
    model: str
) -> tuple[list[EntityEdge], dict[str, Any]]:
    """Use AI to find deeper narrative relationships."""
    # This would involve a complex prompt summarizing all entities.
    # For MVP, we return empty or simple stub.
    return [], {"model": model, "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0}


def _deduplicate_edges(edges: list[EntityEdge]) -> list[EntityEdge]:
    """Merge edges between same entities with same type."""
    seen: dict[tuple[str, str, str, str, str], EntityEdge] = {}
    
    for edge in edges:
        # Normalize key for symmetric relationships
        pair = sorted([(edge.source_type, edge.source_id), (edge.target_type, edge.target_id)])
        key = (pair[0][0], pair[0][1], pair[1][0], pair[1][1], edge.relationship_type)
        
        if key in seen:
            existing = seen[key]
            # Merge evidence and scenes
            existing.evidence = list(set(existing.evidence + edge.evidence))
            existing.scene_refs = list(set(existing.scene_refs + edge.scene_refs))
            existing.confidence = max(existing.confidence, edge.confidence)
        else:
            seen[key] = edge
            
    return list(seen.values())


def _slugify(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")

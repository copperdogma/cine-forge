"""Extract entity relationship graph from bibles and scene artifacts."""

from __future__ import annotations

from typing import Any

from pydantic import RootModel

from cine_forge.ai.llm import call_llm
from cine_forge.schemas import (
    EntityEdge,
    EntityGraph,
)


class EdgeList(RootModel):
    """Temporary container for list of edges."""

    root: list[EntityEdge]


EdgeList.model_rebuild()


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
    work_model = params.get("work_model") or params.get("model") or "claude-haiku-4-5-20251001"

    # Build resolver to canonicalize AI-written character IDs → character_bible entity_ids
    char_resolver = _build_char_resolver(character_bibles)

    edges: list[EntityEdge] = []

    # 2. Generate Co-occurrence Edges (Deterministic)
    # Scene-derived IDs are already canonical slugs — no resolver needed here.
    edges.extend(_generate_co_occurrence_edges(scene_index, prop_bibles))

    # 3. Signature prop edges (AI-extracted ownership relationships)
    edges.extend(_generate_signature_edges(prop_bibles, char_resolver))

    # 4. Merge Relationship Stubs from Bibles
    edges.extend(_merge_bible_stubs(character_bibles, location_bibles, prop_bibles, char_resolver))

    # 5. AI Extraction Pass
    total_cost = {
        "model": work_model,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }
    if work_model != "mock":
        new_edges, cost = _extract_new_relationships(
            character_bibles, location_bibles, prop_bibles, scene_index, work_model
        )
        edges.extend(new_edges)
        total_cost = cost
    
    # 6. Deduplicate and Resolve Conflicts
    final_edges = _deduplicate_edges(edges)

    # 7. Build final graph artifact
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
        "cost": total_cost,
    }


def _generate_co_occurrence_edges(
    scene_index: dict[str, Any],
    prop_bibles: list[dict[str, Any]] | None = None,
) -> list[EntityEdge]:
    """Create edges between entities that share scenes."""
    edges: list[EntityEdge] = []

    # Build a lookup from scene_id → scene entry for prop co-occurrence use below
    scene_lookup: dict[str, dict[str, Any]] = {
        e["scene_id"]: e for e in scene_index.get("entries", [])
    }

    for entry in scene_index.get("entries", []):
        scene_id = entry["scene_id"]
        location = entry.get("location")
        # Prefer pre-slugified IDs; fall back to slugifying display names
        char_ids = entry.get("characters_present_ids") or [
            _slugify(c) for c in entry.get("characters_present", [])
        ]

        # Character <-> Location
        if location:
            for char_id in char_ids:
                edges.append(EntityEdge(
                    source_type="character",
                    source_id=char_id,
                    target_type="location",
                    target_id=_slugify(location),
                    relationship_type="presence",
                    direction="symmetric",
                    evidence=[f"Present in scene {scene_id}"],
                    scene_refs=[scene_id],
                    confidence=1.0,
                ))

        # Character <-> Character co-occurrence
        for i, char_a in enumerate(char_ids):
            for char_b in char_ids[i+1:]:
                edges.append(EntityEdge(
                    source_type="character",
                    source_id=char_a,
                    target_type="character",
                    target_id=char_b,
                    relationship_type="co-occurrence",
                    direction="symmetric",
                    evidence=[f"Share scene {scene_id}"],
                    scene_refs=[scene_id],
                    confidence=1.0,
                ))

    # Prop co-occurrence edges derived from prop bible scene_presence
    for prop in (prop_bibles or []):
        prop_id = prop.get("prop_id", "")
        if not prop_id:
            continue
        for scene_id in prop.get("scene_presence", []):
            entry = scene_lookup.get(scene_id)
            if not entry:
                continue
            location = entry.get("location")
            char_ids = entry.get("characters_present_ids") or [
                _slugify(c) for c in entry.get("characters_present", [])
            ]
            for char_id in char_ids:
                edges.append(EntityEdge(
                    source_type="prop",
                    source_id=prop_id,
                    target_type="character",
                    target_id=char_id,
                    relationship_type="co-occurrence",
                    direction="symmetric",
                    evidence=[f"Prop present in scene {scene_id} with character"],
                    scene_refs=[scene_id],
                    confidence=0.9,
                ))
            if location:
                edges.append(EntityEdge(
                    source_type="prop",
                    source_id=prop_id,
                    target_type="location",
                    target_id=_slugify(location),
                    relationship_type="co-occurrence",
                    direction="symmetric",
                    evidence=[f"Prop present in scene {scene_id} at location"],
                    scene_refs=[scene_id],
                    confidence=0.9,
                ))

    return edges


def _generate_signature_edges(
    prop_bibles: list[dict[str, Any]],
    char_resolver: dict[str, str] | None = None,
) -> list[EntityEdge]:
    """Emit signature_prop_of edges from AI-extracted associated_characters."""
    edges: list[EntityEdge] = []
    for prop in prop_bibles:
        prop_id = prop.get("prop_id", "")
        if not prop_id:
            continue
        for raw_char_id in prop.get("associated_characters", []):
            # Resolve AI-written ID (e.g. "the_mariner") to canonical ID (e.g. "mariner")
            char_id = (char_resolver or {}).get(raw_char_id, raw_char_id)
            edges.append(EntityEdge(
                source_type="prop",
                source_id=prop_id,
                target_type="character",
                target_id=char_id,
                relationship_type="signature_prop_of",
                direction="source_to_target",
                evidence=[f"'{prop.get('name', prop_id)}' is a signature prop of this character"],
                confidence=0.95,
            ))
    return edges


def _merge_bible_stubs(
    characters: list[dict[str, Any]],
    locations: list[dict[str, Any]],
    props: list[dict[str, Any]],
    char_resolver: dict[str, str] | None = None,
) -> list[EntityEdge]:
    """Extract edges from relationship stubs defined in bibles."""
    edges: list[EntityEdge] = []

    for char in characters:
        source_id = char["character_id"]
        for stub in char.get("relationships", []):
            raw_target = _slugify(stub["target_character"])
            target_id = (char_resolver or {}).get(raw_target, raw_target)
            edges.append(EntityEdge(
                source_type="character",
                source_id=source_id,
                target_type="character",
                target_id=target_id,
                relationship_type=stub["relationship_type"],
                direction="source_to_target",
                evidence=[stub["evidence"]],
                confidence=stub["confidence"],
            ))

    return edges


def _extract_new_relationships(
    characters: list[dict[str, Any]],
    locations: list[dict[str, Any]],
    props: list[dict[str, Any]],
    index: dict[str, Any],
    model: str
) -> tuple[list[EntityEdge], dict[str, Any]]:
    """Use AI to find deeper narrative relationships."""
    
    # 1. Build a summary of what we know
    char_list = ", ".join([c["name"] for c in characters])
    loc_list = ", ".join([loc["name"] for loc in locations])
    prop_list = ", ".join([p["name"] for p in props])

    prompt = (
        "You are a narrative architect. Review the following entities from a story "
        "and identify significant narrative relationships that might have been missed "
        "in individual analysis.\n\n"
        f"Characters: {char_list}\n"
        f"Locations: {loc_list}\n"
        f"Props: {prop_list}\n\n"
        "Task: Identify exactly 3-5 high-impact relationships.\n"
        "Focus on: Familial links, Secret rivalries, Ownership of key props, "
        "Primary locations for specific characters.\n\n"
        "Return JSON matching a list of EntityEdge schemas."
    )
    
    result, cost = call_llm(
        prompt=prompt,
        model=model,
        response_schema=EdgeList
    )
    
    return result.root, cost


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
            new_evidence = list(set((existing.evidence or []) + (edge.evidence or [])))
            new_scenes = list(set((existing.scene_refs or []) + (edge.scene_refs or [])))
            existing.evidence = new_evidence
            existing.scene_refs = new_scenes
            existing.confidence = max(existing.confidence, edge.confidence)
        else:
            seen[key] = edge
            
    return list(seen.values())


def _slugify(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


_ARTICLE_PREFIXES = ("the_", "a_", "an_")


def _build_char_resolver(
    character_bibles: list[dict[str, Any]],
) -> dict[str, str]:
    """Build a mapping from any plausible name slug → canonical character_id.

    The AI often writes ``the_mariner`` in associated_characters when the
    canonical character_bible entity_id is ``mariner`` (slugified from the
    dialogue cue ``MARINER``).  This resolver catches that mismatch by
    indexing every character under:
      - its canonical ``character_id``
      - ``_slugify(name)``
      - article-stripped variants (``the_mariner`` → ``mariner``)
    """
    mapping: dict[str, str] = {}
    for char in character_bibles:
        cid = char.get("character_id", "")
        if not cid:
            continue
        # canonical ID maps to itself
        mapping[cid] = cid
        # slugified display name → canonical ID
        name_slug = _slugify(char.get("name", ""))
        if name_slug:
            mapping[name_slug] = cid
        # article-stripped variants of both the canonical ID and name slug
        for slug in (cid, name_slug):
            for prefix in _ARTICLE_PREFIXES:
                if slug.startswith(prefix):
                    mapping[slug[len(prefix):]] = cid
            # also add the article-prefixed form pointing to canonical
            # so "the_mariner" → cid when cid == "mariner"
            for prefix in _ARTICLE_PREFIXES:
                mapping[prefix + slug] = cid
    return mapping

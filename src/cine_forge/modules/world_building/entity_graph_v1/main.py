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
    runtime_params = context.get("runtime_params", {}) if isinstance(context, dict) else {}
    if not isinstance(runtime_params, dict):
        runtime_params = {}

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
    work_model = (
        runtime_params.get("work_model")
        or runtime_params.get("utility_model")
        or params.get("work_model")
        or params.get("model")
        or params.get("default_model")
        or runtime_params.get("default_model")
        or runtime_params.get("model")
        or "gemini-2.5-flash"
    )

    # Build resolver to canonicalize AI-written character IDs → character_bible entity_ids
    char_resolver = _build_char_resolver(character_bibles)

    edges: list[EntityEdge] = []

    # 2. Generate Co-occurrence Edges (Deterministic)
    edges.extend(_generate_co_occurrence_edges(scene_index, prop_bibles, char_resolver))

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
    
    # 6. Resolve IDs, deduplicate, and resolve conflicts
    final_edges = _deduplicate_edges(_resolve_character_edge_ids(edges, char_resolver))

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
    char_resolver: dict[str, str] | None = None,
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
        char_ids = _scene_character_ids(entry, char_resolver)

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
                if char_a == char_b:
                    continue
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
            char_ids = _scene_character_ids(entry, char_resolver)
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


def _scene_character_ids(
    entry: dict[str, Any],
    char_resolver: dict[str, str] | None = None,
) -> list[str]:
    raw_ids = entry.get("characters_present_ids") or [
        _slugify(c) for c in entry.get("characters_present", [])
    ]
    resolved_ids: list[str] = []
    seen: set[str] = set()
    for raw_char_id in raw_ids:
        raw_text = str(raw_char_id).strip()
        if not raw_text:
            continue
        char_id = _resolve_char_id(raw_text, char_resolver)
        if char_id in seen:
            continue
        seen.add(char_id)
        resolved_ids.append(char_id)
    return resolved_ids


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
            char_id = _resolve_char_id(str(raw_char_id), char_resolver)
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


def _resolve_character_edge_ids(
    edges: list[EntityEdge],
    char_resolver: dict[str, str] | None = None,
) -> list[EntityEdge]:
    resolved_edges: list[EntityEdge] = []
    for edge in edges:
        edge_data = edge.model_dump(mode="json")
        if edge.source_type == "character":
            edge_data["source_id"] = _resolve_char_id(edge.source_id, char_resolver)
        if edge.target_type == "character":
            edge_data["target_id"] = _resolve_char_id(edge.target_id, char_resolver)
        if (
            edge_data["source_type"] == "character"
            and edge_data["target_type"] == "character"
            and edge_data["source_id"] == edge_data["target_id"]
        ):
            continue
        resolved_edges.append(EntityEdge.model_validate(edge_data))
    return resolved_edges


def _slugify(name: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def _resolve_char_id(
    raw_char_id: str,
    char_resolver: dict[str, str] | None = None,
) -> str:
    if not char_resolver:
        return raw_char_id
    normalized = raw_char_id.strip()
    if not normalized:
        return normalized
    return char_resolver.get(normalized) or char_resolver.get(_slugify(normalized), normalized)


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
      - exact display text for ``name`` and ``aliases``
      - ``_slugify(name)``
      - ``_slugify(alias)`` for known aliases
      - article-stripped variants (``the_mariner`` → ``mariner``)
    """
    mapping: dict[str, str] = {}
    for char in character_bibles:
        cid = char.get("character_id", "")
        if not cid:
            continue
        _add_char_resolver_text(mapping, cid, cid)
        _add_char_resolver_text(mapping, char.get("name", ""), cid)
        for alias in char.get("aliases", []) or []:
            _add_char_resolver_text(mapping, alias, cid)
    return mapping


def _add_char_resolver_text(mapping: dict[str, str], value: Any, canonical_id: str) -> None:
    text = str(value).strip()
    if not text:
        return
    mapping[text] = canonical_id
    _add_char_resolver_slug(mapping, _slugify(text), canonical_id)


def _add_char_resolver_slug(mapping: dict[str, str], slug: str, canonical_id: str) -> None:
    if not slug:
        return
    mapping[slug] = canonical_id
    for prefix in _ARTICLE_PREFIXES:
        if slug.startswith(prefix):
            mapping[slug[len(prefix):]] = canonical_id
        mapping[prefix + slug] = canonical_id

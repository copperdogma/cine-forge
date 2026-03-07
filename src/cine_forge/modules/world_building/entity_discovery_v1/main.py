"""Incremental AI-first entity discovery module."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

from cine_forge.ai.llm import call_llm
from cine_forge.schemas import EntityDiscoveryResults


class _IncrementalDiscovery(BaseModel):
    items: list[str] = Field(default_factory=list)


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    canonical_script = inputs.get("normalize") or inputs.get("canonical_script")
    if not canonical_script:
        raise ValueError("entity_discovery_v1 requires canonical_script input")

    script_text = canonical_script["script_text"]
    script_title = canonical_script.get("title", "Untitled")

    chunk_size = params.get("chunk_size", 12000)
    model = params.get("discovery_model", "gemini-2.5-flash-lite")

    # Divide into chunks
    chunks = [script_text[i:i+chunk_size] for i in range(0, len(script_text), chunk_size)]

    results: dict[str, list[str]] = {
        "characters": [],
        "locations": [],
        "props": []
    }

    total_cost = {
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
        "model": model
    }

    # Scene index is the canonical character source (Story 081).
    # If available, use its unique_characters directly instead of LLM re-scanning.
    scene_index = inputs.get("breakdown_scenes")
    character_source = "llm"

    if scene_index and scene_index.get("unique_characters"):
        raw_names = scene_index["unique_characters"]
        normalized = list(
            dict.fromkeys(_normalize_character_name(n) for n in raw_names)
        )
        # Filter empty strings from normalization edge cases
        results["characters"] = [n for n in normalized if n]
        character_source = "scene_index"
        print(
            f"[entity_discovery] Characters from scene_index: "
            f"{len(results['characters'])} (from {len(raw_names)} raw names)"
        )

    # Taxonomy configuration — only scan taxonomies that need LLM discovery
    taxonomies = []
    if character_source == "llm" and params.get("enable_characters", True):
        desc = "CHARACTER (speaking roles or silent roles with plot impact)"
        taxonomies.append(("characters", desc))
    if params.get("enable_locations", True):
        desc = "LOCATION (distinct physical settings)"
        taxonomies.append(("locations", desc))
    if params.get("enable_props", True):
        desc = "PROP (objects handled by actors or central to plot, NOT costumes or set dressing)"
        taxonomies.append(("props", desc))

    for key, description in taxonomies:
        # Initialize from existing artifacts if available (Refine mode)
        current_list: list[str] = []
        bible_input_key = f"{key[:-1]}_bible"  # character_bible, location_bible, prop_bible
        existing_bible = inputs.get(bible_input_key)

        if existing_bible:
            # existing_bible is a list of artifact data dicts (from store_inputs_all)
            for item in existing_bible:
                name = item.get("name") or item.get("canonical_name")
                if name:
                    current_list.append(name)
            print(
                f"[entity_discovery] Bootstrapped {len(current_list)} items from "
                f"existing {bible_input_key}"
            )

        print(f"[entity_discovery] Starting pass for {key}...")

        for i, chunk in enumerate(chunks):
            prompt = _build_discovery_prompt(key, description, current_list, chunk)

            payload, cost = call_llm(
                prompt=prompt,
                model=model,
                response_schema=_IncrementalDiscovery,
                temperature=0
            )

            _update_cost(total_cost, cost)
            current_list = payload.items

            # Normalize character names to ensure consistency with parser
            if key == "characters":
                current_list = list(
                    dict.fromkeys([_normalize_character_name(n) for n in current_list])
                )

            print(f"  Chunk {i+1}/{len(chunks)}: {len(current_list)} items found so far")

        results[key] = current_list

    # ── Recall verification (Story 124) ──────────────────────────────
    # Cross-reference discovered locations/props against scene_index signals.
    # Re-prompt only when gaps are detected (zero cost on happy path).
    verification_meta: dict[str, Any] = {
        "verification_ran": False,
        "locations_gap_count": 0,
        "props_gap_count": 0,
        "verification_cost_usd": 0.0,
    }

    if scene_index:
        si_signals = _extract_scene_index_signals(scene_index)

        for key, si_entities in si_signals.items():
            if key not in results or not si_entities:
                continue
            gaps = _find_recall_gaps(results[key], si_entities, key)
            verification_meta[f"{key}_gap_count"] = len(gaps)

            if gaps:
                verification_meta["verification_ran"] = True
                desc_map = {t[0]: t[1] for t in taxonomies}
                description = desc_map.get(key, key.upper())
                prompt = _build_verification_prompt(
                    key, description, results[key], gaps, script_text
                )
                payload, cost = call_llm(
                    prompt=prompt,
                    model=model,
                    response_schema=_IncrementalDiscovery,
                    temperature=0,
                )
                _update_cost(total_cost, cost)
                verification_meta["verification_cost_usd"] += cost.get(
                    "estimated_cost_usd", 0.0
                )
                results[key] = payload.items
                print(
                    f"[entity_discovery] Verification for {key}: "
                    f"{len(gaps)} gaps found, re-prompted → "
                    f"{len(results[key])} items"
                )

    # Final artifact
    discovery_artifact = EntityDiscoveryResults(
        characters=results["characters"],
        locations=results["locations"],
        props=results["props"],
        script_title=script_title,
        processing_metadata={
            "chunk_count": len(chunks),
            "chunk_size": chunk_size,
            "model": model,
            "character_source": character_source,
            **verification_meta,
        }
    )

    return {
        "artifacts": [
            {
                "artifact_type": "entity_discovery_results",
                "entity_id": "project",
                "data": discovery_artifact.model_dump(mode="json"),
                "metadata": {
                    "intent": (
                        "Discover characters (from scene_index), locations, and props."
                    ),
                    "rationale": (
                        "Characters from scene_index (canonical source); locations/props "
                        "via incremental AI passes."
                    ),
                    "confidence": 0.9,
                    "source": "ai"
                }
            }
        ],
        "cost": total_cost
    }


def _build_discovery_prompt(
    entity_type: str, description: str, current_list: list[str], chunk: str
) -> str:
    list_str = ", ".join(current_list) if current_list else "None"
    
    return f"""You are a professional Script Supervisor performing an inventory of {entity_type}.

TAXONOMY DEFINITION: {description}

EXISTING / USER-VETTED LIST:
{list_str}

NEW SCRIPT CHUNK:
{chunk}

TASK:
1. Identify any NEW {entity_type} in this script chunk that are not in the list.
2. DEDUPLICATION: If you see an alias, nickname, or slight spelling variation of an item 
   already in the list, do NOT add it as new. The "EXISTING" list contains items already 
   accepted by the user; prioritize their naming conventions.
3. PRUNING: Only include items that meet the definition above.
4. Return the complete, updated list of ALL {entity_type} found so far
   (including the existing ones).

Return valid JSON: {{ "items": ["NAME 1", "NAME 2", ...] }}
"""


def _update_cost(total: dict[str, Any], call_cost: dict[str, Any]) -> None:
    total["input_tokens"] += call_cost.get("input_tokens", 0)
    total["output_tokens"] += call_cost.get("output_tokens", 0)
    total["estimated_cost_usd"] += call_cost.get("estimated_cost_usd", 0.0)


def _normalize_character_name(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"\s*\((V\.O\.|O\.S\.|CONT'D|CONT’D|OFF|ON RADIO)\)\s*$", "", text)
    
    # Strip non-alphanumeric except spaces and apostrophes (e.g. MR. SALVATORI -> MR SALVATORI)
    text = re.sub(r"[^A-Z0-9' ]+", "", text)
    
    # Strip leading "THE " prefix if it's followed by 4+ letters
    # (e.g. THE MARINER -> MARINER)
    if text.startswith("THE "):
        remainder = text[4:].strip()
        if len(remainder) >= 4:
            text = remainder
    
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _normalize_entity_name(name: str, entity_type: str = "generic") -> str:
    """Normalize an entity name for comparison across sources."""
    text = str(name or "").strip().upper()
    if entity_type == "characters":
        return _normalize_character_name(name)
    if entity_type == "locations":
        # Strip INT./EXT. prefixes common in scene headings
        text = re.sub(
            r"^(INT\./EXT\.|INT/EXT|INT\.|EXT\.)\s*", "", text
        )
        # Strip trailing time-of-day markers
        _tod = r"DAY|NIGHT|DAWN|DUSK|EVENING|MORNING|LATER|CONTINUOUS"
        text = re.sub(rf"\s*-\s*({_tod})\s*$", "", text)
    # General: strip non-alphanumeric except spaces/apostrophes, collapse whitespace
    text = re.sub(r"[^A-Z0-9' ]+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_scene_index_signals(
    scene_index: dict[str, Any],
) -> dict[str, list[str]]:
    """Extract location and prop signals from scene_index for recall verification."""
    signals: dict[str, list[str]] = {}

    # Locations from unique_locations
    locs = scene_index.get("unique_locations", [])
    if locs:
        signals["locations"] = list(dict.fromkeys(
            _normalize_entity_name(loc, "locations") for loc in locs if loc
        ))

    # Props aggregated from per-scene entries
    all_props: list[str] = []
    for entry in scene_index.get("entries", []):
        for prop in entry.get("props_mentioned", []):
            if prop:
                all_props.append(prop)
    if all_props:
        signals["props"] = list(dict.fromkeys(
            _normalize_entity_name(p, "props") for p in all_props if p
        ))

    return signals


def _find_recall_gaps(
    discovered: list[str],
    reference: list[str],
    entity_type: str,
) -> list[str]:
    """Find reference entities not matched by any discovered entity."""
    norm_discovered = [
        _normalize_entity_name(d, entity_type) for d in discovered
    ]
    gaps = []
    for ref in reference:
        norm_ref = _normalize_entity_name(ref, entity_type)
        if not norm_ref:
            continue
        # Substring match in both directions (handles aliases)
        matched = any(
            norm_ref in nd or nd in norm_ref
            for nd in norm_discovered
            if nd
        )
        if not matched:
            gaps.append(ref)
    return gaps


def _build_verification_prompt(
    entity_type: str,
    description: str,
    current_list: list[str],
    missing_hints: list[str],
    script_text: str,
) -> str:
    """Build a targeted re-prompt with specific missing-entity hints."""
    list_str = ", ".join(current_list) if current_list else "None"
    hints_str = ", ".join(missing_hints)
    # Use a bounded excerpt to keep cost reasonable
    max_context = 30000
    context = script_text[:max_context]
    if len(script_text) > max_context:
        context += "\n\n[... screenplay continues ...]"

    return f"""You are a professional Script Supervisor performing \
a recall verification for {entity_type}.

TAXONOMY DEFINITION: {description}

YOUR CURRENT LIST:
{list_str}

POTENTIALLY MISSING (from scene index cross-reference):
{hints_str}

SCREENPLAY TEXT:
{context}

TASK:
The scene index suggests the above items may be missing from your list.
1. Review each potentially missing item against the screenplay text.
2. If it meets the taxonomy definition, ADD it to the list.
3. If it is an alias or variant of an existing item, do NOT add it.
4. If it does not meet the taxonomy definition, do NOT add it.
5. Return the complete, updated list of ALL {entity_type}.

Return valid JSON: {{ "items": ["NAME 1", "NAME 2", ...] }}
"""

"""Incremental AI-first entity discovery module."""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

from cine_forge.ai.llm import call_llm
from cine_forge.schemas import EntityDiscoveryResults


class _IncrementalDiscovery(BaseModel):
    items: list[str] = Field(default_factory=list)


_CHARACTER_DISCOVERY_DESCRIPTION = (
    "CHARACTER (narratively specific people with direct plot impact. Exclude "
    "unnamed background extras, crowd labels, and generic role labels such as "
    "WAITER, GUARD, SECURITY, or THUG unless the screenplay gives them a "
    "specific narrative identity, recurring relationship, or clear story "
    "consequence.)"
)

_LOCATION_DISCOVERY_DESCRIPTION = (
    "LOCATION (distinct physical settings, including specific sublocations such as "
    "floors, stairwells, or elevators when the screenplay stages action there separately)"
)

_PROP_DISCOVERY_DESCRIPTION = (
    "PROP (objects characters handle, use, exchange, seek, or that materially "
    "change the story. Exclude ordinary wardrobe/costumes, set dressing, "
    "furniture, decor, and generic environmental objects unless the screenplay "
    "treats that exact item as distinctive or plot-significant. Exclude generic "
    "weapons/tools like GUN unless the specific object clearly matters.)"
)


def _taxonomy_description(entity_type: str) -> str:
    descriptions = {
        "characters": _CHARACTER_DISCOVERY_DESCRIPTION,
        "locations": _LOCATION_DISCOVERY_DESCRIPTION,
        "props": _PROP_DISCOVERY_DESCRIPTION,
    }
    try:
        return descriptions[entity_type]
    except KeyError as exc:
        raise ValueError(f"Unknown entity type: {entity_type}") from exc


def _taxonomy_rules(entity_type: str) -> str:
    rules = {
        "characters": (
            "- Only include people who would deserve their own character bible entry.\n"
            "- Exclude unnamed background extras, crowd labels, and generic job labels unless "
            "the screenplay individualizes that person or gives them direct plot consequences.\n"
            "- Do not include numbered extras such as THUG 2 or GUARD #1 unless they recur as "
            "a distinct participant with clear narrative identity.\n"
            "- Keep specific story identities such as named family members, villains, or "
            "recurring henchmen with individual names. Drop bare labels like CROWD or THUG 2.\n"
            "- If the person is only scenery for an action beat, leave them out."
        ),
        "locations": (
            "- Include distinct physical settings where story action happens.\n"
            "- Keep specific sublocations inside a larger place when the screenplay stages them "
            "as separate action spaces, such as a 15TH FLOOR, STAIRWELL, or ELEVATOR.\n"
            "- Merge obvious heading variants of the same place instead of creating duplicate "
            "locations."
        ),
        "props": (
            "- Only include items that would deserve their own prop bible entry.\n"
            "- Only include a prop if changing or removing it would alter story comprehension, "
            "blocking, or continuity.\n"
            "- Include worn gear only when the screenplay treats that exact item as a distinctive "
            "signature object or plot-significant equipment.\n"
            "- Exclude ordinary wardrobe, costume pieces, furniture, decor, room fixtures, "
            "scenery, environmental clutter, injuries, sounds, materials, inscriptions, and "
            "parts or descriptors of another prop.\n"
            "- Exclude generic objects even if briefly handled: gun, desk, rug, chair, rope, "
            "bottle, painting, bookcase, or shot.\n"
            "- Good prop examples: OAR, AIRTAG, PURSE, FLARE GUN, MEMORY STICK.\n"
            "- Reject examples: SWEATER, BOOTS, DESK, RUG, PAINTINGS, MINTS, generic GUN.\n"
            "- If the item is borderline set dressing, leave it out."
        ),
    }
    try:
        return rules[entity_type]
    except KeyError as exc:
        raise ValueError(f"Unknown entity type: {entity_type}") from exc


def _discovery_caution(entity_type: str) -> str:
    cautions = {
        "characters": (
            "Character noise hurts downstream bibles. A shorter list of specific people "
            "is better than inventing bibles for extras."
        ),
        "locations": (
            "Use one canonical entry per setting when obvious; do not multiply near-duplicate "
            "headings."
        ),
        "props": (
            "Prop noise hurts downstream prop bibles. A short, clean list is better than a "
            "bloated list of wardrobe and set dressing."
        ),
    }
    try:
        return cautions[entity_type]
    except KeyError as exc:
        raise ValueError(f"Unknown entity type: {entity_type}") from exc


def _enabled_taxonomies(
    character_source: str, params: dict[str, Any]
) -> list[tuple[str, str]]:
    taxonomies: list[tuple[str, str]] = []
    if character_source == "llm" and params.get("enable_characters", True):
        taxonomies.append(("characters", _taxonomy_description("characters")))
    if params.get("enable_locations", True):
        taxonomies.append(("locations", _taxonomy_description("locations")))
    if params.get("enable_props", True):
        taxonomies.append(("props", _taxonomy_description("props")))
    return taxonomies


def _load_scene_index_characters(scene_index: dict[str, Any] | None) -> tuple[list[str], int]:
    raw_names = list((scene_index or {}).get("unique_characters") or [])
    normalized = list(dict.fromkeys(_normalize_character_name(name) for name in raw_names))
    return [name for name in normalized if name], len(raw_names)


def _bootstrap_existing_items(inputs: dict[str, Any], key: str) -> list[str]:
    current_list: list[str] = []
    bible_input_key = f"{key[:-1]}_bible"
    existing_bible = inputs.get(bible_input_key)
    if not existing_bible:
        return current_list

    for item in existing_bible:
        name = item.get("name") or item.get("canonical_name")
        if name:
            current_list.append(name)

    print(
        f"[entity_discovery] Bootstrapped {len(current_list)} items from existing {bible_input_key}"
    )
    return current_list


def _run_incremental_discovery_pass(
    key: str,
    description: str,
    current_list: list[str],
    chunks: list[str],
    model: str,
    total_cost: dict[str, Any],
) -> list[str]:
    print(f"[entity_discovery] Starting pass for {key}...")

    for i, chunk in enumerate(chunks):
        prompt = _build_discovery_prompt(key, description, current_list, chunk)
        payload, cost = call_llm(
            prompt=prompt,
            model=model,
            response_schema=_IncrementalDiscovery,
            temperature=0,
        )

        _update_cost(total_cost, cost)
        current_list = payload.items

        if key == "characters":
            current_list = list(
                dict.fromkeys(_normalize_character_name(name) for name in current_list)
            )

        print(f"  Chunk {i+1}/{len(chunks)}: {len(current_list)} items found so far")

    return current_list


def _run_recall_verification(
    scene_index: dict[str, Any] | None,
    results: dict[str, list[str]],
    taxonomies: list[tuple[str, str]],
    script_text: str,
    model: str,
    total_cost: dict[str, Any],
) -> dict[str, Any]:
    verification_meta: dict[str, Any] = {
        "verification_ran": False,
        "locations_gap_count": 0,
        "props_gap_count": 0,
        "verification_cost_usd": 0.0,
    }
    if not scene_index:
        return verification_meta

    si_signals = _extract_scene_index_signals(scene_index)
    desc_map = {key: description for key, description in taxonomies}

    for key, si_entities in si_signals.items():
        if key not in results or not si_entities:
            continue

        gaps = _find_recall_gaps(results[key], si_entities, key)
        verification_meta[f"{key}_gap_count"] = len(gaps)
        if not gaps:
            continue

        verification_meta["verification_ran"] = True
        prompt = _build_verification_prompt(
            key,
            desc_map.get(key, _taxonomy_description(key)),
            results[key],
            gaps,
            script_text,
        )
        payload, cost = call_llm(
            prompt=prompt,
            model=model,
            response_schema=_IncrementalDiscovery,
            temperature=0,
        )
        _update_cost(total_cost, cost)
        verification_meta["verification_cost_usd"] += cost.get("estimated_cost_usd", 0.0)
        results[key] = payload.items
        print(
            f"[entity_discovery] Verification for {key}: "
            f"{len(gaps)} gaps found, re-prompted -> "
            f"{len(results[key])} items"
        )

    return verification_meta


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    canonical_script = inputs.get("normalize") or inputs.get("canonical_script")
    if not canonical_script:
        raise ValueError("entity_discovery_v1 requires canonical_script input")

    script_text = canonical_script["script_text"]
    script_title = canonical_script.get("title", "Untitled")
    runtime_params = context.get("runtime_params", {}) if isinstance(context, dict) else {}
    if not isinstance(runtime_params, dict):
        runtime_params = {}

    chunk_size = params.get("chunk_size", 12000)
    model = (
        runtime_params.get("discovery_model")
        or runtime_params.get("work_model")
        or runtime_params.get("utility_model")
        or params.get("discovery_model")
        or params.get("work_model")
        or params.get("model")
        or params.get("default_model")
        or runtime_params.get("default_model")
        or runtime_params.get("model")
        or "gemini-2.5-flash-lite"
    )

    chunks = [script_text[i:i+chunk_size] for i in range(0, len(script_text), chunk_size)]

    results: dict[str, list[str]] = {"characters": [], "locations": [], "props": []}
    total_cost = {"input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0, "model": model}

    # Scene index is the canonical character source (Story 081).
    # If available, use its unique_characters directly instead of LLM re-scanning.
    scene_index = inputs.get("breakdown_scenes")
    character_source = "llm"

    scene_index_characters, raw_character_count = _load_scene_index_characters(scene_index)
    if scene_index_characters:
        results["characters"] = scene_index_characters
        character_source = "scene_index"
        print(
            f"[entity_discovery] Characters from scene_index: "
            f"{len(results['characters'])} (from {raw_character_count} raw names)"
        )

    taxonomies = _enabled_taxonomies(character_source, params)

    for key, description in taxonomies:
        current_list = _bootstrap_existing_items(inputs, key)
        results[key] = _run_incremental_discovery_pass(
            key, description, current_list, chunks, model, total_cost
        )

    verification_meta = _run_recall_verification(
        scene_index, results, taxonomies, script_text, model, total_cost
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
    decision_filter = _taxonomy_rules(entity_type)
    caution = _discovery_caution(entity_type)

    return f"""You are a professional Script Supervisor performing an inventory of {entity_type}.

TAXONOMY DEFINITION: {description}

DECISION FILTER:
{decision_filter}

IMPORTANT:
{caution}

EXISTING / USER-VETTED LIST:
{list_str}

NEW SCRIPT CHUNK:
{chunk}

TASK:
1. Identify any NEW {entity_type} in this script chunk that are not in the list.
2. DEDUPLICATION: If you see an alias, nickname, or slight spelling variation of an item 
   already in the list, do NOT add it as new. The "EXISTING" list contains items already 
   accepted by the user; prioritize their naming conventions.
3. PRUNING: Apply the taxonomy definition and decision filter before adding each item.
   If an item is borderline or does not deserve its own bible entry, leave it out.
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

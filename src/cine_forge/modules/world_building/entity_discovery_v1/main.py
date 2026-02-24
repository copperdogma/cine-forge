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
    model = params.get("discovery_model", "claude-haiku-4-5-20251001")

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

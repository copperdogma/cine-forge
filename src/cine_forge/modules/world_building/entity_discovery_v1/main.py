"""Incremental AI-first entity discovery module."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from cine_forge.ai.llm import call_llm
from cine_forge.schemas import EntityDiscoveryResults


class _IncrementalDiscovery(BaseModel):
    items: list[str] = Field(default_factory=list)


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    canonical_script = inputs["canonical_script"]
    script_text = canonical_script["script_text"]
    script_title = canonical_script.get("title", "Untitled")
    
    chunk_size = params.get("chunk_size", 12000)
    model = params.get("discovery_model", "claude-haiku-4-5-20251001")
    
    # Divide into chunks
    chunks = [script_text[i:i+chunk_size] for i in range(0, len(script_text), chunk_size)]
    
    results = {
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

    # Taxonomy configuration
    taxonomies = []
    if params.get("enable_characters", True):
        desc = "CHARACTER (speaking roles or silent roles with plot impact)"
        taxonomies.append(("characters", desc))
    if params.get("enable_locations", True):
        desc = "LOCATION (distinct physical settings)"
        taxonomies.append(("locations", desc))
    if params.get("enable_props", True):
        desc = "PROP (objects handled by actors or central to plot, NOT costumes or set dressing)"
        taxonomies.append(("props", desc))

    for key, description in taxonomies:
        current_list = []
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
            "model": model
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
                        "Discover all characters, locations, and props using incremental AI passes."
                    ),
                    "rationale": (
                        "Overcomes long-context attention fade and regex limitations."
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

CURRENT DISCOVERED LIST:
{list_str}

NEW SCRIPT CHUNK:
{chunk}

TASK:
1. Identify any NEW {entity_type} in this script chunk that are not in the list.
2. DEDUPLICATION: If you see an alias, nickname, or slight spelling variation of an item 
   already in the list, do NOT add it as new.
3. PRUNING: Only include items that meet the definition above.
4. Return the complete, updated list of ALL {entity_type} found so far.

Return valid JSON: {{ "items": ["NAME 1", "NAME 2", ...] }}
"""


def _update_cost(total: dict[str, Any], call_cost: dict[str, Any]) -> None:
    total["input_tokens"] += call_cost.get("input_tokens", 0)
    total["output_tokens"] += call_cost.get("output_tokens", 0)
    total["estimated_cost_usd"] += call_cost.get("estimated_cost_usd", 0.0)

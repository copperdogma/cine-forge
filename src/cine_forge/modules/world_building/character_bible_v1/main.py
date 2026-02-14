"""Extract character bibles and manifests from screenplay artifacts."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from cine_forge.ai.llm import call_llm
from cine_forge.schemas import (
    CharacterBible,
)

CHARACTER_STOPWORDS = {
    "A",
    "AN",
    "AND",
    "AS",
    "AT",
    "BACK",
    "BLACK",
    "BEGIN",
    "CONTINUOUS",
    "CUT",
    "DAY",
    "END",
    "ENDFLASHBACK",
    "EXT",
    "FADE",
    "FOR",
    "FROM",
    "GO",
    "HE",
    "HER",
    "HIS",
    "I",
    "IN",
    "INT",
    "IT",
    "LATER",
    "NIGHT",
    "NO",
    "NOBODY",
    "NOW",
    "OF",
    "ON",
    "OUT",
    "PRESENT",
    "SHE",
    "THE",
    "THEY",
    "THWACK",
    "TO",
    "UNKNOWN",
    "UNSPECIFIED",
    "WE",
    "YOU",
    "LUXURIOUS",
}


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Execute character bible extraction."""
    canonical_script, scene_index = _extract_inputs(inputs)
    model = str(params.get("model", "gpt-4o"))
    min_appearances = int(params.get("min_scene_appearances", 1))

    # 1. Aggregate and Filter
    characters = _aggregate_characters(scene_index)
    ranked = _rank_characters(characters, canonical_script, scene_index)
    
    # Filter by minimum appearances
    candidates = [c for c in ranked if c["scene_count"] >= min_appearances]

    artifacts = []
    total_cost = {"model": model, "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0}

    # 2. Extract for each candidate
    for entry in candidates:
        char_name = entry["name"]
        slug = _slugify(char_name)
        
        definition, cost = _extract_character_definition(
            char_name=char_name,
            entry=entry,
            canonical_script=canonical_script,
            scene_index=scene_index,
            model=model,
        )
        
        # Update cost
        total_cost["input_tokens"] += cost["input_tokens"]
        total_cost["output_tokens"] += cost["output_tokens"]
        total_cost["estimated_cost_usd"] += cost["estimated_cost_usd"]

        # 3. Build manifest and artifact bundle
        version = 1  # Module currently only produces v1 for new bibles
        master_filename = f"master_v{version}.json"
        
        manifest_data = {
            "entity_type": "character",
            "entity_id": slug,
            "display_name": char_name,
            "files": [
                {
                    "filename": master_filename,
                    "purpose": "master_definition",
                    "version": version,
                    "provenance": "ai_extracted",
                    "created_at": datetime.now(UTC).isoformat(),
                }
            ],
            "version": version,
            "created_at": datetime.now(UTC).isoformat(),
        }

        artifacts.append({
            "artifact_type": "bible_manifest",
            "entity_id": f"character_{slug}",
            "data": manifest_data,
            "metadata": {
                "intent": f"Establish master bible for character '{char_name}'",
                "rationale": (
                    "Consolidate character traits, evidence, and relationships from script."
                ),
                "confidence": definition.overall_confidence,
                "source": "ai",
            },
            "bible_files": {
                master_filename: definition.model_dump_json(indent=2)
            }
        })

    return {
        "artifacts": artifacts,
        "cost": total_cost,
    }


def _extract_inputs(inputs: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    canonical_script = None
    scene_index = None
    for payload in inputs.values():
        if isinstance(payload, dict) and "script_text" in payload:
            canonical_script = payload
        if isinstance(payload, dict) and "unique_characters" in payload and "entries" in payload:
            scene_index = payload
    
    if not canonical_script or not scene_index:
        raise ValueError("character_bible_v1 requires canonical_script and scene_index inputs")
    return canonical_script, scene_index


def _aggregate_characters(scene_index: dict[str, Any]) -> list[str]:
    raw_names = scene_index.get("unique_characters", [])
    normalized = [_normalize_character_name(n) for n in raw_names]
    # Filter noise
    plausible = [n for n in normalized if _is_plausible_character_name(n)]
    # Filter derivative
    base_tokens = {n for n in plausible if " " not in n and len(n) >= 4}
    unique = [n for n in plausible if not _looks_like_derivative_noise(n, base_tokens)]
    return sorted(list(set(unique)))


def _rank_characters(
    names: list[str], script: dict[str, Any], index: dict[str, Any]
) -> list[dict[str, Any]]:
    scene_counts = {name: 0 for name in names}
    scene_presence = {name: [] for name in names}
    for entry in index.get("entries", []):
        for raw_char in entry.get("characters_present", []):
            norm = _normalize_character_name(raw_char)
            if norm in scene_counts:
                scene_counts[norm] += 1
                if entry["scene_id"] not in scene_presence[norm]:
                    scene_presence[norm].append(entry["scene_id"])

    # Dialogue counts
    script_text = script.get("script_text", "")
    dialogue_counts = {name: 0 for name in names}
    for line in script_text.splitlines():
        norm = _normalize_character_name(line)
        if norm in dialogue_counts:
            dialogue_counts[norm] += 1

    results = []
    for name in names:
        results.append(
            {
                "name": name,
                "scene_count": scene_counts[name],
                "scene_presence": scene_presence[name],
                "dialogue_count": dialogue_counts[name],
                "score": (scene_counts[name] * 2) + dialogue_counts[name],
            }
        )

    results.sort(key=lambda x: x["score"], reverse=True)
    return results


def _extract_character_definition(
    char_name: str,
    entry: dict[str, Any],
    canonical_script: dict[str, Any],
    scene_index: dict[str, Any],
    model: str,
) -> tuple[CharacterBible, dict[str, Any]]:
    if model == "mock":
        return _mock_extract(char_name, entry), {
            "model": "mock",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    prompt = _build_extraction_prompt(char_name, entry, canonical_script, scene_index)
    definition, cost = call_llm(
        prompt=prompt,
        model=model,
        response_schema=CharacterBible,
    )
    return definition, cost


def _build_extraction_prompt(
    char_name: str, entry: dict[str, Any], script: dict[str, Any], index: dict[str, Any]
) -> str:
    # Ideally we'd only send relevant scenes to save context
    # For now, we'll send the whole thing if it's small, or just a summary
    return f"""You are a character analyst. Extract a master definition for character: {char_name}.
    
    Return JSON matching CharacterBible schema.
    
    Character Context:
    - Name: {char_name}
    - Scene Count: {entry['scene_count']}
    - Dialogue Count: {entry['dialogue_count']}
    
    Script Text:
    {script['script_text']}
    """


def _mock_extract(char_name: str, entry: dict[str, Any]) -> CharacterBible:
    return CharacterBible(
        character_id=_slugify(char_name),
        name=char_name,
        aliases=[],
        description=f"A character named {char_name}.",
        explicit_evidence=[],
        inferred_traits=[],
        scene_presence=entry["scene_presence"],
        dialogue_summary=f"Speaking in {entry['dialogue_count']} lines.",
        narrative_role="supporting",
        narrative_role_confidence=0.8,
        relationships=[],
        overall_confidence=0.9,
    )


def _normalize_character_name(value: Any) -> str:
    text = str(value or "").strip().upper()
    text = re.sub(r"\s*\((V\.O\.|O\.S\.|CONT'D|CONT’D|OFF|ON RADIO)\)\s*$", "", text)
    text = re.sub(r"^[^A-Z0-9]+|[^A-Z0-9']+$", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _is_plausible_character_name(name: str) -> bool:
    if not name or len(name) < 2 or len(name) > 28:
        return False
    tokens = [t.rstrip(".") for t in name.split()]
    if any(token in CHARACTER_STOPWORDS for token in tokens):
        return False
    if not any(char.isalpha() for char in name):
        return False
    return True


def _looks_like_derivative_noise(name: str, base_tokens: set[str]) -> bool:
    for token in name.split():
        for base in base_tokens:
            if token == base:
                continue
            if token.startswith(base) and len(token) >= len(base) + 3:
                return True
    return False


def _slugify(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")

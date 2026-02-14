"""Extract character bibles and manifests from screenplay artifacts."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

from cine_forge.ai.llm import call_llm
from cine_forge.schemas import (
    CharacterBible,
    QAResult,
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
    "CLEAN",
    "DIMLY",
    "LIT",
    "DISCARDED",
    "BOTTLES",
    "RUG",
    "RUSTY",
    "WEIGHTS",
    "WEEDS",
    "OPENING",
    "TITLE",
    "THUG",
}


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Execute character bible extraction."""
    canonical_script, scene_index = _extract_inputs(inputs)
    
    # Tiered Model Strategy (Subsumption)
    work_model = params.get("work_model") or params.get("model") or "gpt-4o-mini"
    verify_model = params.get("verify_model") or "gpt-4o-mini"
    escalate_model = params.get("escalate_model") or "gpt-4o"
    skip_qa = bool(params.get("skip_qa", False))
    
    # Higher default for bibles to avoid noise pollution
    min_appearances = int(params.get("min_scene_appearances", 3))

    # 1. Aggregate and Filter
    characters = _aggregate_characters(scene_index)
    ranked = _rank_characters(characters, canonical_script, scene_index)

    # Filter by minimum appearances OR presence of dialogue
    # Ghost characters usually have 0 dialogue
    candidates = [
        c
        for c in ranked
        if (c["scene_count"] >= min_appearances) or (c["dialogue_count"] >= 1)
    ]
    # Final sanity check: skip anything that is JUST stopwords after filtering
    candidates = [c for c in candidates if _is_plausible_character_name(c["name"])]

    artifacts = []
    models_seen: set[str] = set()
    total_cost = {
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
    }

    # 2. Extract for each candidate
    for entry in candidates:
        char_name = entry["name"]
        slug = _slugify(char_name)
        
        # Pass 1: Work
        definition, cost = _extract_character_definition(
            char_name=char_name,
            entry=entry,
            canonical_script=canonical_script,
            scene_index=scene_index,
            model=work_model,
        )
        _update_total_cost(total_cost, cost)
        if cost.get("model") and cost["model"] != "code":
            models_seen.add(cost["model"])

        qa_result: QAResult | None = None
        if not skip_qa and work_model != "mock":
            # Pass 2: Verify
            qa_result, qa_cost = _run_character_qa(
                char_name=char_name,
                definition=definition,
                script_text=canonical_script["script_text"],
                model=verify_model,
            )
            _update_total_cost(total_cost, qa_cost)
            if qa_cost.get("model") and qa_cost["model"] != "code":
                models_seen.add(qa_cost["model"])

            if not qa_result.passed:
                # Pass 3: Escalate
                definition, esc_cost = _extract_character_definition(
                    char_name=char_name,
                    entry=entry,
                    canonical_script=canonical_script,
                    scene_index=scene_index,
                    model=escalate_model,
                    feedback=qa_result.summary,
                )
                _update_total_cost(total_cost, esc_cost)
                if esc_cost.get("model") and esc_cost["model"] != "code":
                    models_seen.add(esc_cost["model"])
        
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

    model_label = "+".join(sorted(list(models_seen))) if models_seen else "code"
    total_cost["model"] = model_label

    return {
        "artifacts": artifacts,
        "cost": total_cost,
    }


def _update_total_cost(total: dict[str, Any], call_cost: dict[str, Any]) -> None:
    total["input_tokens"] += call_cost.get("input_tokens", 0)
    total["output_tokens"] += call_cost.get("output_tokens", 0)
    total["estimated_cost_usd"] += call_cost.get("estimated_cost_usd", 0.0)


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
    feedback: str = "",
) -> tuple[CharacterBible, dict[str, Any]]:
    if model == "mock":
        return _mock_extract(char_name, entry), {
            "model": "mock",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }

    prompt = _build_extraction_prompt(char_name, entry, canonical_script, scene_index, feedback)
    definition, cost = call_llm(
        prompt=prompt,
        model=model,
        response_schema=CharacterBible,
    )
    return definition, cost


def _run_character_qa(
    char_name: str,
    definition: CharacterBible,
    script_text: str,
    model: str,
) -> tuple[QAResult, dict[str, Any]]:
    from cine_forge.ai import qa_check

    return qa_check(
        original_input=script_text[:5000],  # Give enough for context
        prompt_used="Character extraction prompt",
        output_produced=definition.model_dump_json(),
        model=model,
        criteria=["accuracy", "depth", "vividness"],
    )


def _build_extraction_prompt(
    char_name: str,
    entry: dict[str, Any],
    script: dict[str, Any],
    index: dict[str, Any],
    feedback: str = "",
) -> str:
    # Ideally we'd only send relevant scenes to save context
    # For now, we'll send the whole thing if it's small, or just a summary
    feedback_block = f"\nQA Feedback to address: {feedback}\n" if feedback else ""
    return f"""You are a character analyst. Extract a master definition for character: {char_name}.
    
    Return JSON matching CharacterBible schema.
    {feedback_block}
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
    if re.match(r"^THE[A-Z]{4,}$", text):
        text = text[3:]
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _is_plausible_character_name(name: str) -> bool:
    if not name:
        return False
    if len(name) < 2 or len(name) > 28:
        return False
    tokens = name.split()
    if len(tokens) > 3:
        return False
    if any(not re.match(r"^[A-Z']+$", token) for token in tokens):
        return False
    if any(len(token) > 12 for token in tokens):
        return False
    if any(token in CHARACTER_STOPWORDS for token in tokens):
        return False
    if not any(char.isalpha() for char in name):
        return False
    if re.match(r"^\d+$", name):
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

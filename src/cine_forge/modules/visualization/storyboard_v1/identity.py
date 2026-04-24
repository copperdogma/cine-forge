"""Scene-level character identity locks for storyboard generation."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from cine_forge.ai.llm import call_llm
from cine_forge.modules.visualization.storyboard_v1.support import (
    empty_cost,
    merge_cost,
    resolve_character_bible,
    slugify,
)
from cine_forge.schemas import Scene, ShotPlan, StoryboardCharacterIdentityLock

_VISUAL_TRAIT_HINTS = (
    "appearance",
    "age",
    "build",
    "height",
    "hair",
    "eye",
    "skin",
    "costume",
    "wardrobe",
    "clothing",
    "physical",
    "facial hair",
    "mustache",
    "moustache",
    "beard",
    "silhouette",
)
_VISUAL_CONTINUITY_KEYS = {
    "appearance",
    "wardrobe",
    "clothing",
    "costume",
    "hair",
    "facial_hair",
    "mustache",
    "moustache",
    "beard",
    "build",
    "silhouette",
    "uniform",
}


class _StoryboardIdentityResponse(BaseModel):
    appearance_summary: str
    distinguishing_features: list[str] = Field(default_factory=list)
    wardrobe_summary: str | None = None


def build_scene_character_identity_locks(
    *,
    scene: Scene,
    plan: ShotPlan,
    character_bibles: dict[str, dict[str, Any]],
    continuity_states: list[dict[str, Any]],
    project_config_data: dict[str, Any] | None,
    model: str,
) -> tuple[dict[str, StoryboardCharacterIdentityLock], dict[str, Any]]:
    locks: dict[str, StoryboardCharacterIdentityLock] = {}
    total_cost = empty_cost(model=model)
    ordered_character_ids = list(
        dict.fromkeys(
            character_id for shot in plan.shots for character_id in shot.characters_in_frame
        )
    )

    for character_id in ordered_character_ids:
        character_bible = resolve_character_bible(character_bibles, character_id)
        if not character_bible:
            continue

        lock, cost = _build_identity_lock(
            scene=scene,
            character_id=character_id,
            character_bible=character_bible,
            continuity_states=continuity_states,
            project_config_data=project_config_data,
            model=model,
        )
        locks[slugify(character_id)] = lock
        merge_cost(total_cost, cost)

    return locks, total_cost


def _build_identity_lock(
    *,
    scene: Scene,
    character_id: str,
    character_bible: dict[str, Any],
    continuity_states: list[dict[str, Any]],
    project_config_data: dict[str, Any] | None,
    model: str,
) -> tuple[StoryboardCharacterIdentityLock, dict[str, Any]]:
    if model == "mock":
        return _fallback_identity_lock(
            character_id=character_id,
            character_bible=character_bible,
            continuity_states=continuity_states,
        ), empty_cost(model="mock")

    prompt = _build_identity_prompt(
        scene=scene,
        character_id=character_id,
        character_bible=character_bible,
        continuity_states=continuity_states,
        project_config_data=project_config_data,
    )

    try:
        response, cost = call_llm(
            prompt=prompt,
            model=model,
            response_schema=_StoryboardIdentityResponse,
            max_tokens=500,
            temperature=0.2,
            fail_on_truncation=True,
            enable_caching=True,
        )
        parsed = (
            response
            if isinstance(response, _StoryboardIdentityResponse)
            else _StoryboardIdentityResponse.model_validate(response)
        )
        return (
            StoryboardCharacterIdentityLock(
                character_id=slugify(character_id),
                name=str(character_bible.get("name") or character_id).strip(),
                appearance_summary=parsed.appearance_summary.strip(),
                distinguishing_features=[
                    item.strip()
                    for item in parsed.distinguishing_features
                    if isinstance(item, str) and item.strip()
                ][:4],
                wardrobe_summary=(
                    parsed.wardrobe_summary.strip()
                    if isinstance(parsed.wardrobe_summary, str) and parsed.wardrobe_summary.strip()
                    else None
                ),
                source="llm",
            ),
            cost,
        )
    except Exception:
        return _fallback_identity_lock(
            character_id=character_id,
            character_bible=character_bible,
            continuity_states=continuity_states,
        ), empty_cost(model="heuristic")


def _build_identity_prompt(
    *,
    scene: Scene,
    character_id: str,
    character_bible: dict[str, Any],
    continuity_states: list[dict[str, Any]],
    project_config_data: dict[str, Any] | None,
) -> str:
    name = str(character_bible.get("name") or character_id).strip()
    description = _scene_relevant_sentence(character_bible.get("description"))
    visual_traits = _character_visual_traits(character_bible, continuity_states)
    explicit_evidence = _explicit_visual_evidence(character_bible)
    genres = _clean_list(
        project_config_data.get("genre") if isinstance(project_config_data, dict) else None
    )
    tones = _clean_list(
        project_config_data.get("tone") if isinstance(project_config_data, dict) else None
    )

    parts = [
        "You are defining a canonical visual identity lock for storyboard generation.",
        (
            "Goal: make independently generated storyboard frames keep the same "
            "character face, age band, hair, facial hair, build, and wardrobe silhouette."
        ),
        "Rules:",
        "- Use explicit source facts when present.",
        (
            "- If the screenplay is visually under-specified, choose grounded "
            "defaults for age band, build, hair, facial hair, and wardrobe "
            "silhouette so later image prompts can stay consistent."
        ),
        "- Do not mention race or ethnicity unless the source text explicitly establishes it.",
        (
            "- Keep the output visual-only. No plot recap, camera language, "
            "actor casting, or emotional analysis."
        ),
        "- Return concise grounded design language suitable for reuse across many image prompts.",
        "",
        f"Scene heading: {scene.heading}",
        f"Character: {name}",
        f"Scene-relevant description: {description or 'No reliable summary available.'}",
    ]
    if explicit_evidence:
        parts.append(f"Explicit visual evidence: {'; '.join(explicit_evidence)}.")
    if visual_traits:
        parts.append(f"Inferred or continuity visual cues: {'; '.join(visual_traits)}.")
    if genres:
        parts.append(f"Project genre context: {', '.join(genres)}.")
    if tones:
        parts.append(f"Project tone context: {', '.join(tones)}.")
    parts.append("")
    parts.append("Return JSON matching the schema.")
    return "\n".join(parts)


def _fallback_identity_lock(
    *,
    character_id: str,
    character_bible: dict[str, Any],
    continuity_states: list[dict[str, Any]],
) -> StoryboardCharacterIdentityLock:
    name = str(character_bible.get("name") or character_id).strip()
    description = _scene_relevant_sentence(character_bible.get("description"))
    visual_traits = _character_visual_traits(character_bible, continuity_states)
    wardrobe_summary = _first_matching_trait(
        visual_traits, ("wardrobe", "coat", "shirt", "jacket", "uniform")
    )
    distinguishing_features = [item for item in visual_traits if item != wardrobe_summary][:4]

    if distinguishing_features:
        appearance_summary = (
            f"{description or name}. "
            f"Lock the recurring visual design to: {'; '.join(distinguishing_features[:3])}."
        )
    else:
        appearance_summary = (
            f"{description or name}. "
            "Keep the character grounded, adult, naturalistic, and visually "
            "stable across every frame."
        )

    return StoryboardCharacterIdentityLock(
        character_id=slugify(character_id),
        name=name,
        appearance_summary=appearance_summary.strip(),
        distinguishing_features=distinguishing_features,
        wardrobe_summary=wardrobe_summary,
        source="heuristic",
    )


def _scene_relevant_sentence(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    parts = [part.strip() for part in text.split(".") if part.strip()]
    return parts[0] if parts else text


def _clean_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if isinstance(item, str) and item.strip()]


def _explicit_visual_evidence(character_bible: dict[str, Any]) -> list[str]:
    evidence = character_bible.get("explicit_evidence")
    if not isinstance(evidence, list):
        return []
    lines: list[str] = []
    for item in evidence:
        if not isinstance(item, dict):
            continue
        trait = str(item.get("trait") or "").strip()
        quote = str(item.get("quote") or "").strip()
        lowered = trait.lower()
        if not quote:
            continue
        if any(hint in lowered for hint in _VISUAL_TRAIT_HINTS) or "wear" in quote.lower():
            label = trait if trait else "visual cue"
            lines.append(f"{label}: {quote}")
    return lines[:6]


def _character_visual_traits(
    character_bible: dict[str, Any],
    continuity_states: list[dict[str, Any]],
) -> list[str]:
    traits: list[str] = []
    inferred_traits = character_bible.get("inferred_traits")
    if isinstance(inferred_traits, list):
        for item in inferred_traits:
            if not isinstance(item, dict):
                continue
            trait_name = str(item.get("trait") or "").lower()
            value = str(item.get("value") or "").strip()
            if not value:
                continue
            if any(hint in trait_name for hint in _VISUAL_TRAIT_HINTS):
                traits.append(value)

    character_key = slugify(
        str(character_bible.get("character_id") or character_bible.get("name") or "").strip()
    )
    for state in continuity_states:
        if slugify(str(state.get("entity_id") or "").strip()) != character_key:
            continue
        properties = state.get("properties")
        if not isinstance(properties, list):
            continue
        for item in properties:
            if not isinstance(item, dict):
                continue
            key = str(item.get("key") or "").strip().lower()
            value = str(item.get("value") or "").strip()
            if key in _VISUAL_CONTINUITY_KEYS and value:
                traits.append(value)
    return list(dict.fromkeys(traits))


def _first_matching_trait(traits: list[str], hints: tuple[str, ...]) -> str | None:
    for trait in traits:
        lowered = trait.lower()
        if any(hint in lowered for hint in hints):
            return trait
    return None

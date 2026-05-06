"""Still-image prompt compilation for design studies and render backfill."""

from __future__ import annotations

from typing import Any, Literal

from cine_forge.schemas import VisualCreativeBrief
from cine_forge.services.creative_brief import creative_brief_prompt_lines

StillImageGenerationMode = Literal["manual_design_study", "default_backfill"]


def _ensure_sentence(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    if value.endswith((".", "!", "?")):
        return value
    return f"{value}."


def _string_list(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    cleaned: list[str] = []
    for item in values:
        if isinstance(item, str) and item.strip():
            cleaned.append(item.strip())
    return cleaned


def _look_and_feel_context(look_and_feel_data: dict[str, Any] | None) -> list[str]:
    if not isinstance(look_and_feel_data, dict):
        return []

    lines: list[str] = []
    field_labels = (
        ("lighting_concept", "Lighting concept"),
        ("color_palette", "Color palette"),
        ("composition_philosophy", "Composition philosophy"),
        ("camera_personality", "Camera personality"),
        ("costume_notes", "Costume notes"),
        ("production_design_notes", "Production design notes"),
    )
    for field_name, label in field_labels:
        value = look_and_feel_data.get(field_name)
        if isinstance(value, str) and value.strip():
            lines.append(f"{label}: {_ensure_sentence(value)}")

    reference_imagery = _string_list(look_and_feel_data.get("reference_imagery"))
    if reference_imagery:
        lines.append(f"Reference imagery anchors: {', '.join(reference_imagery)}.")

    return lines


def _creative_brief_context(
    creative_brief_data: VisualCreativeBrief | dict[str, Any] | None,
) -> tuple[list[str], list[str]]:
    if isinstance(creative_brief_data, VisualCreativeBrief):
        brief = creative_brief_data
    elif isinstance(creative_brief_data, dict):
        brief = VisualCreativeBrief.model_validate(creative_brief_data)
    else:
        return [], []
    return creative_brief_prompt_lines(brief), list(brief.sources_used)


def synthesize_image_prompt(entity_type: str, bible_data: dict[str, Any]) -> str:
    """Build a cinematic concept art prompt from a bible dict.

    Pulls description, physical traits, and inferred traits to create a
    detailed visual brief. No LLM call - direct field synthesis.
    """
    name = bible_data.get("name", "Unknown")
    description = bible_data.get("description", "")

    trait_lines: list[str] = []

    if entity_type == "character":
        inferred = bible_data.get("inferred_traits", [])
        physical_keys = {
            "appearance",
            "age",
            "build",
            "height",
            "hair",
            "eyes",
            "skin",
            "costume",
            "wardrobe",
            "clothing",
            "physical",
        }
        for trait in inferred:
            trait_name = str(trait.get("trait", "")).lower()
            if any(k in trait_name for k in physical_keys):
                value = trait.get("value", "")
                if value:
                    trait_lines.append(value)

        scene_count = len(bible_data.get("scene_presence", []))
        narrative_role = bible_data.get("narrative_role", "")
        role_note = (
            f"{narrative_role} character"
            if narrative_role and narrative_role != "minor"
            else "character"
        )

        parts = [
            f"Cinematic concept art of {name}, a {role_note}.",
            description,
        ]
        if trait_lines:
            parts.append("Physical appearance: " + ". ".join(trait_lines) + ".")
        if scene_count:
            parts.append(f"Featured in {scene_count} scenes.")
        parts.append(
            "Style: film production character design, detailed concept art,"
            " dramatic lighting, photorealistic. Clean character art, no text."
        )

    elif entity_type == "location":
        physical_traits = bible_data.get("physical_traits", [])
        narrative_sig = bible_data.get("narrative_significance", "")

        parts = [
            f"Cinematic establishing shot of {name}.",
            description,
        ]
        if physical_traits:
            parts.append("Key features: " + "; ".join(physical_traits[:5]) + ".")
        if narrative_sig:
            parts.append(f"Narrative role: {narrative_sig}")
        parts.append(
            "Style: film production design, wide establishing shot,"
            " atmospheric lighting, photorealistic."
        )

    elif entity_type == "prop":
        narrative_sig = bible_data.get("narrative_significance", "")
        assoc_chars = bible_data.get("associated_characters", [])

        parts = [
            f"Prop design concept for {name}.",
            description,
        ]
        if narrative_sig:
            parts.append(f"Significance: {narrative_sig}")
        if assoc_chars:
            parts.append(f"Associated with: {', '.join(assoc_chars[:3])}.")
        parts.append(
            "Style: film prop design sheet, clean product photography,"
            " neutral background, detailed."
        )

    else:
        parts = [description, "Style: cinematic concept art, film production design."]

    return " ".join(p.strip() for p in parts if p.strip())


def _reference_contract(entity_type: str, generation_mode: StillImageGenerationMode) -> str:
    mode_line = (
        "This is an automatic default reference for downstream AI video generation; "
        "make conservative, source-grounded choices and avoid inventing extra lore."
        if generation_mode == "default_backfill"
        else "This is a design-study still that may become a downstream AI video reference."
    )
    if entity_type == "character":
        shape = (
            "Show one clear subject, three-quarter or full-body framing, readable face, "
            "hair, silhouette, costume, age, and posture. Use a clean uncluttered "
            "background. Do not create a poster, collage, multiple variants, labels, "
            "captions, typography, watermarks, or UI overlays."
        )
    elif entity_type == "location":
        shape = (
            "Show a wide establishing reference plate with clear geography, scale, "
            "architecture, materials, lighting, and atmosphere. Avoid text, signage "
            "emphasis, maps, labels, split panels, watermarks, or UI overlays unless "
            "the story specifically requires readable text."
        )
    elif entity_type == "prop":
        shape = (
            "Show one centered prop reference with clear silhouette, materials, scale "
            "cues, wear, and story-relevant details on a neutral production-design "
            "background. Avoid catalog labels, typography, watermarks, hands obscuring "
            "the prop, split panels, or UI overlays unless the story specifically "
            "requires them."
        )
    else:
        shape = (
            "Show a clean production reference still with one coherent subject and "
            "no labels, typography, watermarks, split panels, or UI overlays."
        )
    return f"Reference still contract: {mode_line} {shape}"


def build_image_prompt(
    entity_type: str,
    bible_data: dict[str, Any],
    *,
    directive: str | None = None,
    positive_reference_lines: list[str] | None = None,
    negative_reference_lines: list[str] | None = None,
    seed_image_filename: str | None = None,
    learned_preferences_lines: list[str] | None = None,
    look_and_feel_data: dict[str, Any] | None = None,
    creative_brief_data: VisualCreativeBrief | dict[str, Any] | None = None,
    generation_mode: StillImageGenerationMode = "manual_design_study",
) -> tuple[str, list[str]]:
    """Build a still-image prompt plus a provenance list for the prompt sources used."""
    base_prompt = synthesize_image_prompt(entity_type, bible_data)
    prompt_parts: list[str] = []
    sources_used = ["entity_bible", "still_image_reference_contract"]

    if generation_mode == "default_backfill":
        sources_used.append("default_backfill_contract")

    if directive:
        prompt_parts.append(f"Composition directive: {_ensure_sentence(directive)}")
        sources_used.append("directive")

    positive_reference_lines = [
        _ensure_sentence(line)
        for line in positive_reference_lines or []
        if line and line.strip()
    ]
    if positive_reference_lines:
        prompt_parts.append(
            "Carry forward visual cues from these positive references: "
            + " ".join(positive_reference_lines)
        )
        sources_used.append("positive_refs")

    negative_reference_lines = [
        _ensure_sentence(line)
        for line in negative_reference_lines or []
        if line and line.strip()
    ]
    if negative_reference_lines:
        prompt_parts.append(
            "Avoid the visual cues present in these negative references: "
            + " ".join(negative_reference_lines)
        )
        sources_used.append("negative_refs")

    if seed_image_filename:
        prompt_parts.append(
            "Variation of the previously approved design direction while preserving the"
            " same subject identity and core design language."
        )
        sources_used.append("seed_image")

    if learned_preferences_lines:
        prompt_parts.extend(
            _ensure_sentence(line) for line in learned_preferences_lines if line and line.strip()
        )
        sources_used.append("learned_preferences")

    prompt_parts.append(base_prompt)

    look_and_feel_lines = _look_and_feel_context(look_and_feel_data)
    if look_and_feel_lines:
        prompt_parts.extend(look_and_feel_lines)
        sources_used.append("look_and_feel")

    creative_brief_lines, creative_brief_sources = _creative_brief_context(creative_brief_data)
    if creative_brief_lines:
        prompt_parts.extend(creative_brief_lines)
        for source in creative_brief_sources:
            if source not in sources_used:
                sources_used.append(source)

    prompt_parts.append(_reference_contract(entity_type, generation_mode))

    prompt = " ".join(part.strip() for part in prompt_parts if part and part.strip())
    return prompt, sources_used

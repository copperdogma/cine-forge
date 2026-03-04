"""Image generation via Google Imagen 4 and OpenAI gpt-image-1.

Provides two functions:
  - synthesize_image_prompt: build a rich visual prompt from a bible dict
  - generate_image: dispatch to the appropriate provider and return raw image bytes + model used

Provider routing:
  - Models starting with "gpt-" → OpenAI Images API (OPENAI_API_KEY)
  - All others → Google Imagen API (GEMINI_API_KEY)
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from typing import Any

IMAGEN_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
OPENAI_BASE_URL = "https://api.openai.com/v1"

# Default model and aspect ratios by entity type.
DEFAULT_MODEL = "imagen-4.0-generate-001"

ASPECT_RATIO_BY_ENTITY_TYPE: dict[str, str] = {
    "character": "9:16",   # portrait orientation
    "location": "16:9",    # wide establishing shot
    "prop": "4:3",         # product/design sheet
}

# OpenAI gpt-image-1 size mappings (closest to Imagen aspect ratios).
OPENAI_SIZE_BY_ENTITY_TYPE: dict[str, str] = {
    "character": "1024x1536",  # portrait (≈9:16)
    "location": "1536x1024",   # landscape (≈16:9)
    "prop": "1024x1024",       # square (closest to 4:3)
}

# Models that route to OpenAI instead of Google.
_OPENAI_MODELS: frozenset[str] = frozenset({"gpt-image-1"})


class ImageGenerationError(Exception):
    """Raised when the image generation API call fails."""


def synthesize_image_prompt(entity_type: str, bible_data: dict[str, Any]) -> str:
    """Build a cinematic concept art prompt from a bible dict.

    Pulls description, physical traits, and inferred traits to create a
    detailed visual brief. No LLM call — direct field synthesis.
    """
    name = bible_data.get("name", "Unknown")
    description = bible_data.get("description", "")

    trait_lines: list[str] = []

    if entity_type == "character":
        # Pull explicit physical traits from inferred_traits
        inferred = bible_data.get("inferred_traits", [])
        physical_keys = {
            "appearance", "age", "build", "height", "hair",
            "eyes", "skin", "costume", "wardrobe", "clothing", "physical",
        }
        for trait in inferred:
            trait_name = str(trait.get("trait", "")).lower()
            if any(k in trait_name for k in physical_keys):
                value = trait.get("value", "")
                if value:
                    trait_lines.append(value)

        # Scene context
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


def _generate_image_openai(
    prompt: str,
    entity_type: str = "character",
    model: str = "gpt-image-1",
) -> tuple[bytes, str]:
    """Generate an image via OpenAI gpt-image-1 and return (image_bytes, model_used).

    Returns JPEG-encoded image data (requests output_format=jpeg).
    """
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise ImageGenerationError("OPENAI_API_KEY environment variable is not set")

    size = OPENAI_SIZE_BY_ENTITY_TYPE.get(entity_type, "1024x1024")

    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "n": 1,
        "size": size,
        "output_format": "jpeg",
    }

    url = f"{OPENAI_BASE_URL}/images/generations"
    request_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=request_bytes,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            response_data = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise ImageGenerationError(
            f"OpenAI Images API returned HTTP {exc.code}: {body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise ImageGenerationError(
            f"OpenAI Images API request failed: {exc.reason}"
        ) from exc

    data = response_data.get("data", [])
    if not data:
        raise ImageGenerationError(
            f"OpenAI Images API returned no data. Response: {response_data}"
        )

    b64_data = data[0].get("b64_json", "")
    if not b64_data:
        raise ImageGenerationError(
            "OpenAI Images API response missing b64_json field"
        )

    image_bytes = base64.b64decode(b64_data)
    return image_bytes, model


def _generate_image_imagen(
    prompt: str,
    entity_type: str = "character",
    model: str = DEFAULT_MODEL,
    aspect_ratio: str | None = None,
) -> tuple[bytes, str]:
    """Generate an image via Google Imagen and return (image_bytes, model_used)."""
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ImageGenerationError("GEMINI_API_KEY environment variable is not set")

    ratio = aspect_ratio or ASPECT_RATIO_BY_ENTITY_TYPE.get(entity_type, "1:1")

    payload: dict[str, Any] = {
        "instances": [{"prompt": prompt}],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": ratio,
        },
    }

    url = f"{IMAGEN_BASE_URL}/{model}:predict?key={api_key}"
    request_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=request_bytes,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            response_data = json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise ImageGenerationError(
            f"Imagen API returned HTTP {exc.code}: {body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise ImageGenerationError(f"Imagen API request failed: {exc.reason}") from exc

    predictions = response_data.get("predictions", [])
    if not predictions:
        raise ImageGenerationError(
            f"Imagen API returned no predictions. Response: {response_data}"
        )

    b64_data = predictions[0].get("bytesBase64Encoded", "")
    if not b64_data:
        raise ImageGenerationError(
            "Imagen API prediction missing bytesBase64Encoded field"
        )

    image_bytes = base64.b64decode(b64_data)
    return image_bytes, model


def generate_image(
    prompt: str,
    entity_type: str = "character",
    model: str = DEFAULT_MODEL,
    aspect_ratio: str | None = None,
) -> tuple[bytes, str]:
    """Generate an image and return (image_bytes, model_used).

    Routes to the appropriate provider based on model ID:
      - "gpt-image-1" → OpenAI Images API (OPENAI_API_KEY)
      - All others → Google Imagen API (GEMINI_API_KEY)

    Args:
        prompt: The visual description to generate from.
        entity_type: Used to pick default aspect ratio / size if not specified.
        model: Model ID — determines provider routing.
        aspect_ratio: Override aspect ratio (Imagen only). Defaults by entity_type:
            character → "9:16", location → "16:9", prop → "4:3".

    Returns:
        (image_bytes, model_used) where image_bytes is JPEG-encoded image data.

    Raises:
        ImageGenerationError: If the API call fails or returns no image.
    """
    if model in _OPENAI_MODELS:
        return _generate_image_openai(prompt, entity_type, model)
    return _generate_image_imagen(prompt, entity_type, model, aspect_ratio)

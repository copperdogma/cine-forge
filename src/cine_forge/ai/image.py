"""Image generation via Google Imagen and OpenAI GPT Image models.

Provides provider dispatch:
  - generate_image: dispatch to the appropriate provider and return raw image bytes + model used

Provider routing:
  - OpenAI GPT image models (for example ``gpt-image-1``) → OpenAI Images API
  - Google Imagen models (for example ``imagen-4.0-generate-001``) → Google Imagen API

Provider keys prefer ``CINE_FORGE_*`` env names and fall back to the generic
provider names inside this repo process when needed.
"""

from __future__ import annotations

import base64
import json
import mimetypes
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any, Literal

from cine_forge.ai.image_errors import ImageGenerationError, provider_http_error
from cine_forge.env import require_env

IMAGEN_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
OPENAI_BASE_URL = "https://api.openai.com/v1"

# Default model and aspect ratios by entity type.
DEFAULT_MODEL = "imagen-4.0-generate-001"

ASPECT_RATIO_BY_ENTITY_TYPE: dict[str, str] = {
    "character": "9:16",   # portrait orientation
    "location": "16:9",    # wide establishing shot
    "prop": "4:3",         # product/design sheet
}

# OpenAI GPT image size mappings (closest to Imagen aspect ratios).
OPENAI_SIZE_BY_ENTITY_TYPE: dict[str, str] = {
    "character": "1024x1536",  # portrait (≈9:16)
    "location": "1536x1024",   # landscape (≈16:9)
    "prop": "1024x1024",       # square (closest to 4:3)
}

REFERENCE_IMAGE_FALLBACK_MODEL = "gpt-image-1"

_OPENAI_IMAGE_COST_BY_MODEL: dict[str, dict[str, dict[str, float]]] = {
    "gpt-image-1": {
        "low": {"1024x1024": 0.011, "1024x1536": 0.016, "1536x1024": 0.016},
        "medium": {"1024x1024": 0.042, "1024x1536": 0.063, "1536x1024": 0.063},
        "high": {"1024x1024": 0.167, "1024x1536": 0.25, "1536x1024": 0.25},
    },
    "gpt-image-1.5": {
        "low": {"1024x1024": 0.009, "1024x1536": 0.013, "1536x1024": 0.013},
        "medium": {"1024x1024": 0.034, "1024x1536": 0.05, "1536x1024": 0.05},
        "high": {"1024x1024": 0.133, "1024x1536": 0.2, "1536x1024": 0.2},
    },
    "chatgpt-image-latest": {
        "low": {"1024x1024": 0.009, "1024x1536": 0.013, "1536x1024": 0.013},
        "medium": {"1024x1024": 0.034, "1024x1536": 0.05, "1536x1024": 0.05},
        "high": {"1024x1024": 0.133, "1024x1536": 0.2, "1536x1024": 0.2},
    },
    "gpt-image-2": {
        "low": {"1024x1024": 0.00816, "1024x1536": 0.01224, "1536x1024": 0.012},
        "medium": {"1024x1024": 0.03168, "1024x1536": 0.04752, "1536x1024": 0.04704},
        "high": {"1024x1024": 0.1248, "1024x1536": 0.1872, "1536x1024": 0.18624},
    },
}

_MOCK_IMAGE_BYTES = (
    b'<svg xmlns="http://www.w3.org/2000/svg" width="1536" height="1024" '
    b'viewBox="0 0 1536 1024"><rect width="1536" height="1024" fill="#f2efe7"/>'
    b'<rect x="96" y="96" width="1344" height="832" rx="24" fill="#ffffff" '
    b'stroke="#1f2937" stroke-width="12"/><line x1="128" y1="220" x2="1408" '
    b'y2="220" stroke="#1f2937" stroke-width="10"/><line x1="128" y1="804" '
    b'x2="1408" y2="804" stroke="#1f2937" stroke-width="10"/><circle cx="440" '
    b'cy="530" r="92" fill="#cbd5e1"/><circle cx="1088" cy="486" r="116" '
    b'fill="#94a3b8"/><path d="M560 680c96-128 240-176 420-132" fill="none" '
    b'stroke="#1f2937" stroke-width="16"/><text x="768" y="150" text-anchor="middle" '
    b'font-size="60" font-family="Helvetica, Arial, sans-serif" fill="#1f2937">'
    b'Storyboard Mock</text></svg>'
)

def is_openai_image_model(model: str) -> bool:
    return model.startswith("gpt-image-") or model == "chatgpt-image-latest"


def is_google_imagen_model(model: str) -> bool:
    return model.startswith("imagen-")


def _generate_image_openai(
    prompt: str,
    entity_type: str = "character",
    model: str = "gpt-image-1",
    quality: Literal["auto", "low", "medium", "high"] = "auto",
    reference_image_paths: list[str] | None = None,
    size: str | None = None,
) -> tuple[bytes, str]:
    """Generate an image via OpenAI gpt-image-1 and return (image_bytes, model_used).

    Returns JPEG-encoded image data (requests output_format=jpeg).
    """
    try:
        api_key = require_env("OPENAI_API_KEY")
    except RuntimeError as exc:
        raise ImageGenerationError(str(exc), provider="openai", model=model) from exc

    resolved_size = size or OPENAI_SIZE_BY_ENTITY_TYPE.get(entity_type, "1024x1024")

    cleaned_reference_paths = [
        str(Path(path))
        for path in (reference_image_paths or [])
        if isinstance(path, str) and path.strip()
    ]
    if cleaned_reference_paths:
        if len(cleaned_reference_paths) > 16:
            raise ImageGenerationError(
                "OpenAI image edit supports at most 16 reference images per request",
                provider="openai",
                model=model,
            )
        multipart_body, boundary = _build_openai_edit_multipart(
            model=model,
            prompt=prompt,
            size=resolved_size,
            quality=quality,
            output_format="jpeg",
            reference_image_paths=cleaned_reference_paths,
        )
        url = f"{OPENAI_BASE_URL}/images/edits"
        req = urllib.request.Request(
            url,
            data=multipart_body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
    else:
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": resolved_size,
            "quality": quality,
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
        if cleaned_reference_paths and "Unknown parameter:" in body:
            response_data = _retry_openai_edit_with_optional_fields_removed(
                api_key=api_key,
                model=model,
                prompt=prompt,
                size=resolved_size,
                reference_image_paths=cleaned_reference_paths,
            )
        else:
            raise provider_http_error(
                provider="openai",
                provider_label="OpenAI Images API",
                model=model,
                status_code=exc.code,
                headers=exc.headers,
                body=body,
            ) from exc
    except urllib.error.URLError as exc:
        raise ImageGenerationError(
            f"OpenAI Images API request failed: {exc.reason}",
            provider="openai",
            model=model,
            is_transient=True,
        ) from exc

    data = response_data.get("data", [])
    if not data:
        raise ImageGenerationError(
            f"OpenAI Images API returned no data. Response: {response_data}",
            provider="openai",
            model=model,
            response_body=json.dumps(response_data),
        )

    b64_data = data[0].get("b64_json", "")
    if not b64_data:
        raise ImageGenerationError(
            "OpenAI Images API response missing b64_json field",
            provider="openai",
            model=model,
            response_body=json.dumps(response_data),
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
    try:
        api_key = require_env("GEMINI_API_KEY")
    except RuntimeError as exc:
        raise ImageGenerationError(str(exc), provider="google", model=model) from exc

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
        raise provider_http_error(
            provider="google",
            provider_label="Imagen API",
            model=model,
            status_code=exc.code,
            headers=exc.headers,
            body=body,
        ) from exc
    except urllib.error.URLError as exc:
        raise ImageGenerationError(
            f"Imagen API request failed: {exc.reason}",
            provider="google",
            model=model,
            is_transient=True,
        ) from exc

    predictions = response_data.get("predictions", [])
    if not predictions:
        raise ImageGenerationError(
            f"Imagen API returned no predictions. Response: {response_data}",
            provider="google",
            model=model,
            response_body=json.dumps(response_data),
        )

    b64_data = predictions[0].get("bytesBase64Encoded", "")
    if not b64_data:
        raise ImageGenerationError(
            "Imagen API prediction missing bytesBase64Encoded field",
            provider="google",
            model=model,
            response_body=json.dumps(response_data),
        )

    image_bytes = base64.b64decode(b64_data)
    return image_bytes, model


def supports_direct_reference_images(model: str) -> bool:
    return is_openai_image_model(model)


def _build_openai_edit_multipart(
    *,
    model: str,
    prompt: str,
    size: str,
    quality: Literal["auto", "low", "medium", "high"] | None,
    output_format: str | None,
    reference_image_paths: list[str],
) -> tuple[bytes, str]:
    boundary = f"----CineForge{uuid.uuid4().hex}"
    body = bytearray()

    def add_field(name: str, value: str) -> None:
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode()
        )
        body.extend(value.encode("utf-8"))
        body.extend(b"\r\n")

    def add_file(name: str, path: str) -> None:
        file_path = Path(path)
        mime_type = mimetypes.guess_type(file_path.name)[0] or "image/jpeg"
        file_bytes = file_path.read_bytes()
        body.extend(f"--{boundary}\r\n".encode())
        body.extend(
            (
                f'Content-Disposition: form-data; name="{name}"; '
                f'filename="{file_path.name}"\r\n'
            ).encode()
        )
        body.extend(f"Content-Type: {mime_type}\r\n\r\n".encode())
        body.extend(file_bytes)
        body.extend(b"\r\n")

    add_field("model", model)
    add_field("prompt", prompt)
    add_field("size", size)
    if quality is not None:
        add_field("quality", quality)
    if output_format is not None:
        add_field("output_format", output_format)
    for path in reference_image_paths:
        add_file("image[]", path)

    body.extend(f"--{boundary}--\r\n".encode())
    return bytes(body), boundary


def _retry_openai_edit_with_optional_fields_removed(
    *,
    api_key: str,
    model: str,
    prompt: str,
    size: str,
    reference_image_paths: list[str],
) -> dict[str, Any]:
    attempts = [
        {"quality": None, "output_format": "jpeg"},
        {"quality": None, "output_format": None},
    ]
    last_error: tuple[int, str] | None = None
    for fields in attempts:
        multipart_body, boundary = _build_openai_edit_multipart(
            model=model,
            prompt=prompt,
            size=size,
            quality=fields["quality"],
            output_format=fields["output_format"],
            reference_image_paths=reference_image_paths,
        )
        req = urllib.request.Request(
            f"{OPENAI_BASE_URL}/images/edits",
            data=multipart_body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Authorization": f"Bearer {api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return json.loads(resp.read())
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            last_error = (exc.code, body)
            if "Unknown parameter:" not in body:
                break
        except urllib.error.URLError as exc:
            raise ImageGenerationError(
                f"OpenAI Images API request failed: {exc.reason}",
                provider="openai",
                model=model,
                is_transient=True,
            ) from exc
    if last_error is None:
        raise ImageGenerationError(
            "OpenAI Images API edit retry failed",
            provider="openai",
            model=model,
            is_transient=True,
        )
    raise provider_http_error(
        provider="openai",
        provider_label="OpenAI Images API",
        model=model,
        status_code=last_error[0],
        headers=None,
        body=last_error[1],
    )


def generate_image(
    prompt: str,
    entity_type: str = "character",
    model: str = DEFAULT_MODEL,
    aspect_ratio: str | None = None,
    quality: Literal["auto", "low", "medium", "high"] = "auto",
    reference_image_paths: list[str] | None = None,
    size: str | None = None,
) -> tuple[bytes, str]:
    """Generate an image and return (image_bytes, model_used).

    Routes to the appropriate provider based on model ID:
      - OpenAI GPT image models → OpenAI Images API
      - Imagen models → Google Imagen API

    Args:
        prompt: The visual description to generate from.
        entity_type: Used to pick default aspect ratio / size if not specified.
        model: Model ID — determines provider routing.
        aspect_ratio: Override aspect ratio (Imagen only). Defaults by entity_type:
            character -> "9:16", location -> "16:9", prop -> "4:3".
        reference_image_paths: Optional absolute file paths to reference images.
            Currently supported for OpenAI GPT Image models only.
        size: Optional OpenAI image size override. When omitted, the default
            size is derived from entity_type.

    Returns:
        (image_bytes, model_used) where image_bytes is JPEG-encoded image data.

    Raises:
        ImageGenerationError: If the API call fails or returns no image.
    """
    if model == "mock":
        return _MOCK_IMAGE_BYTES, model
    if is_openai_image_model(model):
        return _generate_image_openai(
            prompt,
            entity_type,
            model,
            quality,
            reference_image_paths=reference_image_paths,
            size=size,
        )
    if is_google_imagen_model(model):
        return _generate_image_imagen(prompt, entity_type, model, aspect_ratio)
    raise ImageGenerationError(
        f"Unsupported image model '{model}'. "
        "Expected an OpenAI GPT image model or Google Imagen model.",
        model=model,
    )


def estimate_image_generation_cost_usd(
    model: str,
    *,
    entity_type: str = "character",
    quality: Literal["auto", "low", "medium", "high"] = "auto",
    size: str | None = None,
) -> float:
    """Return a best-effort per-image cost estimate for supported providers."""
    if model == "mock":
        return 0.0

    if is_openai_image_model(model):
        resolved_size = size or OPENAI_SIZE_BY_ENTITY_TYPE.get(entity_type, "1024x1024")
        effective_quality = "medium" if quality == "auto" else quality
        return (
            _OPENAI_IMAGE_COST_BY_MODEL.get(model, {})
            .get(effective_quality, {})
            .get(resolved_size, 0.0)
        )

    if model.startswith("imagen-4.0-ultra"):
        return 0.06
    if model.startswith("imagen-4.0-fast"):
        return 0.02
    if model.startswith("imagen-4.0"):
        return 0.04
    if model.startswith("imagen-3") and "fast" in model:
        return 0.02
    if model.startswith("imagen-3"):
        return 0.04
    if model.startswith("imagen-2") or model.startswith("imagen-1"):
        return 0.02
    return 0.0

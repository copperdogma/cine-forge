"""Native Gemini image transport, with the application's JPEG output contract.

REST contract: https://ai.google.dev/gemini-api/docs/generate-content/image-generation
Pricing: https://ai.google.dev/gemini-api/docs/pricing (2026-10-06).
"""

from __future__ import annotations

import base64
import binascii
import io
import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

from cine_forge.ai.image_errors import ImageGenerationError, provider_http_error
from cine_forge.env import require_env

MODEL = "gemini-nano-banana-2.1"
BASE_URL = "https://generativelanguage.googleapis.com/v1/models"
ASPECT_RATIOS = {
    "1:1",
    "1:4",
    "1:8",
    "2:3",
    "3:2",
    "3:4",
    "4:1",
    "4:3",
    "4:5",
    "5:4",
    "8:1",
    "9:16",
    "16:9",
    "21:9",
}
# Existing OpenAI callers pass these sizes. Preserve orientation, not exact pixels.
_PIXEL_SIZE_ASPECTS = {"1024x1024": "1:1", "1024x1536": "2:3", "1536x1024": "3:2"}
_THINKING_LEVELS = {"auto": "medium", "low": "minimal", "medium": "medium", "high": "high"}
OUTPUT_COST_USD = {"1K": 0.0336, "2K": 0.0504, "4K": 0.1134}


def resolve_image_options(
    size: str | None,
    aspect_ratio: str | None,
    quality: str,
) -> tuple[str, str, str]:
    """Map public options to native resolution, aspect, and thinking level."""
    resolution = "1K"
    size_aspect = None
    if size is not None:
        if size in OUTPUT_COST_USD:
            resolution = size
        elif size in _PIXEL_SIZE_ASPECTS:
            size_aspect = _PIXEL_SIZE_ASPECTS[size]
        else:
            raise ImageGenerationError(
                f"Unsupported Gemini image size '{size}'; use 1K, 2K, 4K "
                "or 1024x1024, 1024x1536, 1536x1024",
                provider="google",
                model=MODEL,
            )
    resolved_aspect = aspect_ratio or size_aspect or "1:1"
    if resolved_aspect not in ASPECT_RATIOS:
        raise ImageGenerationError(
            f"Unsupported Gemini image aspect ratio '{resolved_aspect}'",
            provider="google",
            model=MODEL,
        )
    if quality not in _THINKING_LEVELS:
        raise ImageGenerationError(
            f"Unsupported Gemini image quality '{quality}'",
            provider="google",
            model=MODEL,
        )
    return resolution, resolved_aspect, _THINKING_LEVELS[quality]


def _reference_part(path: str, model: str) -> dict[str, Any]:
    try:
        data = Path(path).read_bytes()
        with Image.open(io.BytesIO(data)) as image:
            mime_type = Image.MIME.get(image.format or "")
            image.verify()
        if mime_type not in {"image/png", "image/jpeg", "image/webp", "image/heic", "image/heif"}:
            raise ValueError(f"unsupported image MIME type {mime_type}")
    except (OSError, ValueError, UnidentifiedImageError) as exc:
        raise ImageGenerationError(
            f"Cannot read Gemini reference image '{path}': {exc}",
            provider="google",
            model=model,
        ) from exc
    return {"inlineData": {"mimeType": mime_type, "data": base64.b64encode(data).decode("ascii")}}


def _decode_image(response: dict[str, Any], model: str) -> bytes:
    feedback = response.get("promptFeedback") or {}
    if not isinstance(feedback, dict):
        raise TypeError("promptFeedback must be an object")
    if feedback.get("blockReason"):
        raise ImageGenerationError(
            f"Gemini image prompt blocked: {feedback['blockReason']}",
            provider="google",
            model=model,
            error_code=str(feedback["blockReason"]),
            response_body=json.dumps(response),
        )
    reasons: list[str] = []
    candidates = response.get("candidates") or []
    if not isinstance(candidates, list):
        raise TypeError("candidates must be an array")
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise TypeError("candidate must be an object")
        reason = candidate.get("finishReason")
        if reason:
            reasons.append(str(reason))
            if reason != "STOP":
                # Never publish blocked or incomplete candidate output, even if
                # the provider included an image part alongside its finish reason.
                continue
        content = candidate.get("content") or {}
        if not isinstance(content, dict):
            raise TypeError("candidate content must be an object")
        parts = content.get("parts") or []
        if not isinstance(parts, list):
            raise TypeError("content parts must be an array")
        for part in parts:
            if not isinstance(part, dict):
                raise TypeError("part must be an object")
            # Interim thought images are not the requested final asset.
            if part.get("thought"):
                continue
            inline = part.get("inlineData") or {}
            if not isinstance(inline, dict):
                raise TypeError("inlineData must be an object")
            if not str(inline.get("mimeType", "")).startswith("image/"):
                continue
            try:
                data = base64.b64decode(inline.get("data", ""), validate=True)
                with Image.open(io.BytesIO(data)) as image:
                    output = io.BytesIO()
                    image.convert("RGB").save(output, format="JPEG", quality=95)
                return output.getvalue()
            except (OSError, ValueError, TypeError, binascii.Error) as exc:
                raise ImageGenerationError(
                    "Gemini returned invalid image data",
                    provider="google",
                    model=model,
                ) from exc
    detail = ", ".join(reasons) or "no image part"
    raise ImageGenerationError(
        f"Gemini returned no image ({detail})",
        provider="google",
        model=model,
        error_code=reasons[0] if reasons else None,
        response_body=json.dumps(response),
    )


def generate_gemini_image(
    prompt: str,
    *,
    model: str = MODEL,
    aspect_ratio: str | None = None,
    quality: str = "auto",
    reference_image_paths: list[str] | None = None,
    size: str | None = None,
) -> tuple[bytes, str]:
    resolution, aspect, thinking = resolve_image_options(size, aspect_ratio, quality)
    paths = reference_image_paths or []
    if len(paths) > 14:
        raise ImageGenerationError(
            "Gemini image generation supports at most 14 reference images per request",
            provider="google",
            model=model,
        )
    if any(not isinstance(path, str) or not path.strip() for path in paths):
        raise ImageGenerationError(
            "Invalid Gemini reference image path", provider="google", model=model
        )
    parts = [{"text": prompt}, *[_reference_part(path, model) for path in paths]]
    try:
        api_key = require_env("GEMINI_API_KEY")
    except RuntimeError as exc:
        raise ImageGenerationError(str(exc), provider="google", model=model) from exc
    payload = {
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "responseFormat": {"image": {"aspectRatio": aspect, "imageSize": resolution}},
            "thinkingConfig": {"thinkingLevel": thinking},
        },
    }
    request = urllib.request.Request(
        f"{BASE_URL}/{model}:generateContent",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "x-goog-api-key": api_key},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        raise provider_http_error(
            provider="google",
            provider_label="Gemini Images API",
            model=model,
            status_code=exc.code,
            headers=exc.headers,
            body=exc.read().decode("utf-8", errors="replace"),
        ) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise ImageGenerationError(
            "Gemini Images API request failed",
            provider="google",
            model=model,
            is_transient=True,
        ) from exc
    except (ValueError, UnicodeDecodeError) as exc:
        raise ImageGenerationError(
            "Gemini Images API returned invalid JSON",
            provider="google",
            model=model,
        ) from exc
    if not isinstance(result, dict):
        raise ImageGenerationError(
            "Gemini Images API returned an invalid response",
            provider="google",
            model=model,
        )
    try:
        return _decode_image(result, model), model
    except (AttributeError, TypeError) as exc:
        raise ImageGenerationError(
            "Gemini Images API returned an invalid response",
            provider="google",
            model=model,
        ) from exc

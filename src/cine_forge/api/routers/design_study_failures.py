"""Failure normalization helpers for design-study generation."""

from __future__ import annotations

import hashlib

from cine_forge.ai.image import ImageGenerationError
from cine_forge.ai.provider_failures import classify_provider_failure_status
from cine_forge.schemas.design_study import DesignStudyGenerationFailure

_PROMPT_EXCERPT_CHARS = 700


def design_study_failure_from_exception(
    exc: ImageGenerationError,
    *,
    prompt: str,
    model: str,
    failed_image_index: int,
    requested_count: int,
) -> DesignStudyGenerationFailure:
    provider = exc.provider or _provider_from_model(exc.model or model)
    model_used = exc.model or model
    classification = _classify_image_generation_failure(exc)
    request_fragment = f" Request ID: {exc.request_id}." if exc.request_id else ""
    status_fragment = (
        f" HTTP {exc.status_code}." if exc.status_code is not None else ""
    )
    operator_message = (
        f"{_provider_label(provider)} failed while generating design-study image "
        f"{failed_image_index}/{requested_count} with `{model_used}` "
        f"({classification}).{status_fragment}{request_fragment} "
        f"Provider message: {str(exc)}"
    )
    return DesignStudyGenerationFailure(
        provider=provider,
        model=model_used,
        message=str(exc),
        operator_message=operator_message,
        classification=classification,
        status_code=exc.status_code,
        request_id=exc.request_id,
        error_code=exc.error_code,
        error_type=exc.error_type,
        failed_image_index=failed_image_index,
        prompt_sha256=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        prompt_excerpt=_prompt_excerpt(prompt),
    )


def _provider_from_model(model: str) -> str:
    if model.startswith("gpt-image-") or model == "chatgpt-image-latest":
        return "openai"
    if model.startswith("imagen-"):
        return "google"
    return "provider"


def _provider_label(provider: str) -> str:
    return {
        "google": "Google Imagen",
        "openai": "OpenAI Images",
    }.get(provider, provider.title())


def _prompt_excerpt(prompt: str) -> str:
    compact = " ".join(prompt.split())
    if len(compact) <= _PROMPT_EXCERPT_CHARS:
        return compact
    return f"{compact[:_PROMPT_EXCERPT_CHARS].rstrip()}..."


def _classify_image_generation_failure(exc: ImageGenerationError) -> str:
    error_code = exc.error_code or (str(exc.status_code) if exc.status_code is not None else None)
    classification = classify_provider_failure_status(
        message=str(exc),
        error_code=error_code,
        is_transient=exc.is_transient,
    )
    if classification is not None:
        return classification
    if exc.status_code is None and exc.is_transient:
        return "network_error"
    return "provider_error"

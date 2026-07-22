"""Provider identity normalization and maintained-model label binding."""

from __future__ import annotations

import re

from cine_forge.ai.errors import LLMCallError
from cine_forge.ai.model_identity import validate_provider_response_identity

MAINTAINED_PROVIDER_LABELS: dict[str, str] = {
    "gemini-3.5-flash": "Gemini 3.5 Flash",
    "gemini-3.5-flash-lite": "Gemini 3.5 Flash-Lite",
    "gemini-3.6-flash": "Gemini 3.6 Flash",
}


def normalize_label(label: str) -> str:
    """Convert a provider label to the model name used by the eval registry."""
    return re.sub(r"^Claude\s+", "", label)


def provider_model_slug(provider: dict, response: dict) -> str | None:
    """Resolve the requested model while rejecting contradictory response identity.

    This helper remains usable for print-only historical diagnostics, where raw
    provider identity may be absent. Registry promotion applies the stricter
    current-task contract in :mod:`cine_forge.evals.task_provenance`.
    """
    provider_id = provider.get("id")
    requested: str | None = None
    provider_family: str | None = None
    if isinstance(provider_id, str) and provider_id.strip():
        normalized_id = provider_id.strip()
        if not normalized_id.startswith("file://"):
            requested = normalized_id.rsplit(":", 1)[-1]
            provider_family = normalized_id.split(":", 1)[0]

    metadata = response.get("metadata")
    returned_evidence: list[tuple[str, str]] = []
    metadata_model: str | None = None
    explicit_returned_model = False
    if metadata is not None:
        if not isinstance(metadata, dict):
            raise ValueError("response metadata must be a mapping")
        if requested is None and "requested_model" in metadata:
            requested = _nonempty_string(
                metadata["requested_model"],
                "requested_model",
            )
        if provider_family is None and "provider" in metadata:
            provider_family = _nonempty_string(metadata["provider"], "provider")
        if "returned_model" in metadata:
            explicit_returned_model = True
            returned_evidence.append(
                (
                    "response.metadata.returned_model",
                    _nonempty_string(metadata["returned_model"], "returned_model"),
                )
            )
        if "model" in metadata:
            metadata_model = _nonempty_string(metadata["model"], "model")
            if not explicit_returned_model and "requested_model" not in metadata:
                returned_evidence.append(("response.metadata.model", metadata_model))

    raw = response.get("raw")
    if isinstance(raw, dict):
        for key in ("modelVersion", "model"):
            if key in raw:
                returned_evidence.append(
                    (f"response.raw.{key}", _nonempty_string(raw[key], key))
                )

    returned_slugs = {slug for _, slug in returned_evidence}
    if len(returned_slugs) > 1:
        rendered = ", ".join(
            f"{source}={slug}" for source, slug in returned_evidence
        )
        raise ValueError(f"provider model identity mismatch: {rendered}")
    returned = next(iter(returned_slugs), None)
    if metadata_model is not None and metadata_model not in {requested, returned}:
        raise ValueError(
            "provider model identity mismatch: response.metadata.model="
            f"{metadata_model} is neither requested nor returned identity"
        )
    if requested is not None and returned is not None:
        if provider_family in {"openai", "anthropic", "google", "xai"}:
            try:
                validate_provider_response_identity(
                    provider=provider_family,
                    requested_model=requested,
                    returned_model=returned,
                    request_id=None,
                    require_returned=False,
                )
            except LLMCallError as exc:
                raise ValueError(f"provider model identity mismatch: {exc}") from exc
        elif requested != returned:
            raise ValueError(
                "provider model identity mismatch: "
                f"requested_model={requested}, returned_model={returned}"
            )
    return requested or returned


def provider_display_name(provider: dict, model_slug: str | None = None) -> str:
    """Resolve and bind maintained provider labels to exact model slugs."""
    label = provider.get("label")
    normalized_label = label.strip() if isinstance(label, str) else ""

    if model_slug in MAINTAINED_PROVIDER_LABELS:
        expected_label = MAINTAINED_PROVIDER_LABELS[model_slug]
        if normalized_label != expected_label:
            raise ValueError(
                f"provider label/model mismatch: {model_slug} requires "
                f"label {expected_label!r}, found {normalized_label!r}"
            )
        return normalize_label(expected_label)

    maintained_slugs_for_label = {
        slug
        for slug, expected_label in MAINTAINED_PROVIDER_LABELS.items()
        if normalized_label == expected_label
    }
    if maintained_slugs_for_label:
        expected = ", ".join(sorted(maintained_slugs_for_label))
        raise ValueError(
            "provider label/model mismatch: "
            f"label {normalized_label!r} requires model {expected}, "
            f"found {model_slug!r}"
        )

    if normalized_label:
        return normalize_label(normalized_label)

    provider_id = provider.get("id")
    if not isinstance(provider_id, str) or not provider_id.strip():
        raise ValueError("provider has no non-empty label or id")
    model_id = model_slug or provider_id.rsplit(":", 1)[-1]
    if model_id.startswith("grok-"):
        words = model_id.split("-")
        if len(words) >= 3 and words[1].isdigit() and words[2].isdigit():
            words[1:3] = [f"{words[1]}.{words[2]}"]
        return " ".join(word.capitalize() for word in words)
    return model_id


def _nonempty_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value.strip()

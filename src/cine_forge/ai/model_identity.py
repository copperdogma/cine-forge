"""Fail-closed model and call identity checks for provider responses."""

from __future__ import annotations

import re
from dataclasses import dataclass

from cine_forge.ai.errors import LLMCallError

_OPENAI_SNAPSHOT = re.compile(r"^(?P<alias>.+)-(?P<date>\d{4}-\d{2}-\d{2})$")
_ANTHROPIC_ALIAS_SNAPSHOTS = {
    "claude-sonnet-4-5": frozenset({"claude-sonnet-4-5-20250929"}),
}


@dataclass(frozen=True)
class ProviderResponseIdentity:
    """Validated request/response identity and its safe billing key."""

    provider: str
    requested_model: str
    returned_model: str | None
    request_id: str | None
    billing_model: str


def validate_provider_response_identity(
    *,
    provider: str,
    requested_model: str,
    returned_model: object,
    request_id: object,
    require_returned: bool,
) -> ProviderResponseIdentity:
    """Validate a provider response without laundering model substitutions.

    Injected/offline transports may omit provider-owned identity fields by
    passing ``require_returned=False``. If they do supply identity, it is still
    validated. Live transports must set ``require_returned=True``.
    """
    normalized_provider = _required_string(provider, "provider")
    requested = _required_string(requested_model, "requested model")
    returned = _optional_identity(
        returned_model,
        name="returned model",
        required=require_returned,
    )
    normalized_request_id = _optional_identity(
        request_id,
        name="response id",
        required=require_returned,
    )
    if returned is not None and not _compatible_model_identity(
        provider=normalized_provider,
        requested=requested,
        returned=returned,
    ):
        raise LLMCallError(
            f"{normalized_provider} response model does not match requested model: "
            f"expected {requested}, received {returned}"
        )
    return ProviderResponseIdentity(
        provider=normalized_provider,
        requested_model=requested,
        returned_model=returned,
        request_id=normalized_request_id,
        billing_model=requested,
    )


def _compatible_model_identity(*, provider: str, requested: str, returned: str) -> bool:
    if requested == returned:
        return True
    if provider == "anthropic":
        # Anthropic's current 4.6+ model IDs are already pinned identities, not
        # rolling aliases. Keep the one repository-supported legacy alias
        # explicit so a future-looking fabricated snapshot cannot pass merely
        # because it has the same prefix.
        return returned in _ANTHROPIC_ALIAS_SNAPSHOTS.get(requested, ())
    pattern = {
        "openai": _OPENAI_SNAPSHOT,
    }.get(provider)
    if pattern is None:
        return False
    if pattern.fullmatch(requested) is not None:
        return False
    match = pattern.fullmatch(returned)
    # Only an undated alias may resolve to its exact dated snapshot. A pinned
    # request never accepts a different snapshot, and suffix/prefix family
    # matches never accept mini, pro, or other variant substitutions.
    return match is not None and match.group("alias") == requested


def _optional_identity(value: object, *, name: str, required: bool) -> str | None:
    if value is None:
        if required:
            raise LLMCallError(f"provider response {name} must be a non-empty string")
        return None
    return _required_string(value, f"provider response {name}")


def _required_string(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LLMCallError(f"{name} must be a non-empty string")
    return value.strip()

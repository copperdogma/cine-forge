"""Environment helpers for provider credentials.

Prefers repo-scoped ``CINE_FORGE_*`` variables while still tolerating the
legacy generic provider names for older tooling and tests.
"""

from __future__ import annotations

import os

_PROVIDER_ENV_ALIASES: dict[str, tuple[str, ...]] = {
    "OPENAI_API_KEY": ("CINE_FORGE_OPENAI_API_KEY", "OPENAI_API_KEY"),
    "ANTHROPIC_API_KEY": ("CINE_FORGE_ANTHROPIC_API_KEY", "ANTHROPIC_API_KEY"),
    "GEMINI_API_KEY": ("CINE_FORGE_GEMINI_API_KEY", "GEMINI_API_KEY"),
    "MISTRAL_API_KEY": ("CINE_FORGE_MISTRAL_API_KEY", "MISTRAL_API_KEY"),
    "XAI_API_KEY": ("CINE_FORGE_XAI_API_KEY", "XAI_API_KEY"),
}


def provider_env_names(name: str) -> tuple[str, ...]:
    """Return the accepted env var names for a provider credential."""
    return _PROVIDER_ENV_ALIASES.get(name, (name,))


def preferred_env_name(name: str) -> str:
    """Return the preferred env var name for a provider credential."""
    return provider_env_names(name)[0]


def resolve_env(name: str) -> str | None:
    """Resolve a provider env var, preferring the CineForge-scoped alias.

    When only the preferred ``CINE_FORGE_*`` alias is present, this also seeds
    the legacy generic name into the current process so external libraries that
    still expect it can continue to work inside this repo context.
    """
    aliases = provider_env_names(name)
    for alias in aliases:
        value = os.environ.get(alias)
        if value:
            if alias != name:
                os.environ.setdefault(name, value)
            return value
    return None


def require_env(name: str) -> str:
    """Return a required provider credential or raise a descriptive error."""
    value = resolve_env(name)
    if value:
        return value
    aliases = provider_env_names(name)
    if aliases == (name,):
        raise RuntimeError(f"{name} is not set")
    preferred = aliases[0]
    raise RuntimeError(f"{preferred} (or legacy {name}) is not set")


def export_legacy_provider_envs() -> dict[str, str]:
    """Populate generic provider env vars from CineForge-scoped aliases."""
    exported: dict[str, str] = {}
    for generic_name in _PROVIDER_ENV_ALIASES:
        value = resolve_env(generic_name)
        if value:
            exported[generic_name] = value
    return exported

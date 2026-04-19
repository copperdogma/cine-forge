from __future__ import annotations

from cine_forge.env import (
    export_legacy_provider_envs,
    preferred_env_name,
    require_env,
    resolve_env,
)


def test_resolve_env_prefers_cine_forge_alias(monkeypatch) -> None:
    monkeypatch.setenv("CINE_FORGE_OPENAI_API_KEY", "repo-key")
    monkeypatch.setenv("OPENAI_API_KEY", "legacy-key")

    assert resolve_env("OPENAI_API_KEY") == "repo-key"


def test_resolve_env_seeds_legacy_name_when_only_cine_forge_alias_exists(monkeypatch) -> None:
    monkeypatch.setenv("CINE_FORGE_GEMINI_API_KEY", "repo-key")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    assert resolve_env("GEMINI_API_KEY") == "repo-key"
    assert require_env("GEMINI_API_KEY") == "repo-key"


def test_export_legacy_provider_envs_sets_generic_aliases(monkeypatch) -> None:
    monkeypatch.setenv("CINE_FORGE_ANTHROPIC_API_KEY", "repo-key")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    exported = export_legacy_provider_envs()

    assert exported["ANTHROPIC_API_KEY"] == "repo-key"
    assert preferred_env_name("ANTHROPIC_API_KEY") == "CINE_FORGE_ANTHROPIC_API_KEY"

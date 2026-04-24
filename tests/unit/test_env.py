from __future__ import annotations

import os
from pathlib import Path

from cine_forge.env import (
    export_legacy_provider_envs,
    load_cine_forge_dotenv,
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
    assert os.environ["GEMINI_API_KEY"] == "repo-key"


def test_resolve_env_overrides_stale_legacy_name_with_cine_forge_alias(monkeypatch) -> None:
    monkeypatch.setenv("CINE_FORGE_GEMINI_API_KEY", "repo-key")
    monkeypatch.setenv("GEMINI_API_KEY", "stale-key")

    assert resolve_env("GEMINI_API_KEY") == "repo-key"
    assert os.environ["GEMINI_API_KEY"] == "repo-key"


def test_export_legacy_provider_envs_sets_generic_aliases(monkeypatch) -> None:
    monkeypatch.setenv("CINE_FORGE_ANTHROPIC_API_KEY", "repo-key")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    exported = export_legacy_provider_envs()

    assert exported["ANTHROPIC_API_KEY"] == "repo-key"
    assert preferred_env_name("ANTHROPIC_API_KEY") == "CINE_FORGE_ANTHROPIC_API_KEY"


def test_load_cine_forge_dotenv_uses_worktree_and_shared_checkout_roots(
    monkeypatch,
    tmp_path: Path,
) -> None:
    worktree_root = tmp_path / "worktree"
    shared_root = tmp_path / "main-checkout"
    gitdir = shared_root / ".git" / "worktrees" / "wt1"
    gitdir.mkdir(parents=True)
    worktree_root.mkdir()

    (worktree_root / ".git").write_text(f"gitdir: {gitdir}\n", encoding="utf-8")
    (gitdir / "commondir").write_text("../..\n", encoding="utf-8")
    (worktree_root / ".env").write_text(
        "CINE_FORGE_GEMINI_API_KEY=worktree-key\n",
        encoding="utf-8",
    )
    (shared_root / ".env").write_text(
        "CINE_FORGE_OPENAI_API_KEY=shared-openai\n"
        "CINE_FORGE_GEMINI_API_KEY=shared-gemini\n",
        encoding="utf-8",
    )

    for name in (
        "GEMINI_API_KEY",
        "CINE_FORGE_GEMINI_API_KEY",
        "OPENAI_API_KEY",
        "CINE_FORGE_OPENAI_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)

    loaded = load_cine_forge_dotenv(worktree_root)

    assert loaded == (
        worktree_root / ".env",
        shared_root / ".env",
    )
    assert resolve_env("GEMINI_API_KEY") == "worktree-key"
    assert resolve_env("OPENAI_API_KEY") == "shared-openai"
    assert os.environ["GEMINI_API_KEY"] == "worktree-key"
    assert os.environ["OPENAI_API_KEY"] == "shared-openai"

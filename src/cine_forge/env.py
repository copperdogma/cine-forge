"""Environment helpers for provider credentials.

Prefers repo-scoped ``CINE_FORGE_*`` variables while still tolerating the
legacy generic provider names for older tooling and tests.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

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
                os.environ[name] = value
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
    gemini_value = os.environ.get("GEMINI_API_KEY")
    if gemini_value:
        os.environ["GOOGLE_API_KEY"] = gemini_value
        exported["GOOGLE_API_KEY"] = gemini_value
    return exported


def _shared_checkout_root(repo_root: Path) -> Path | None:
    """Return the shared/main checkout root for a git worktree, if one exists."""
    git_path = repo_root / ".git"
    if git_path.is_dir() or not git_path.exists():
        return None
    try:
        git_pointer = git_path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not git_pointer.startswith("gitdir:"):
        return None

    gitdir = Path(git_pointer.split(":", 1)[1].strip())
    if not gitdir.is_absolute():
        gitdir = (repo_root / gitdir).resolve()

    commondir_path = gitdir / "commondir"
    if not commondir_path.is_file():
        return None
    try:
        commondir = commondir_path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    common_git_dir = Path(commondir)
    if not common_git_dir.is_absolute():
        common_git_dir = (gitdir / common_git_dir).resolve()

    shared_root = common_git_dir.parent
    if shared_root == repo_root:
        return None
    return shared_root


def load_cine_forge_dotenv(repo_root: Path | None = None) -> tuple[Path, ...]:
    """Load repo-scoped env files for this checkout and its shared worktree root."""
    resolved_root = (repo_root or Path(__file__).resolve().parents[2]).resolve()
    roots = [resolved_root]
    shared_root = _shared_checkout_root(resolved_root)
    if shared_root is not None:
        roots.append(shared_root)

    loaded_paths: list[Path] = []
    for root in roots:
        for filename in (".env", ".env.local"):
            dotenv_path = root / filename
            if dotenv_path.is_file():
                load_dotenv(dotenv_path)
                loaded_paths.append(dotenv_path)

    export_legacy_provider_envs()
    return tuple(loaded_paths)

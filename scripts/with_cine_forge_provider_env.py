#!/usr/bin/env python3
"""Exec a command with legacy provider env vars hydrated from CineForge keys."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

load_dotenv(REPO_ROOT / ".env")
load_dotenv(REPO_ROOT / ".env.local")

from cine_forge.env import export_legacy_provider_envs  # noqa: E402


def main() -> None:
    if len(sys.argv) < 2:
        raise SystemExit(
            "Usage: with_cine_forge_provider_env.py <command> [args...]"
        )
    export_legacy_provider_envs()
    os.execvpe(sys.argv[1], sys.argv[1:], os.environ)


if __name__ == "__main__":
    main()

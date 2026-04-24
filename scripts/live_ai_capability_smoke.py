#!/usr/bin/env python3
"""Run the expensive live AI capability smoke from the CLI."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from cine_forge.env import load_cine_forge_dotenv  # noqa: E402

load_cine_forge_dotenv(REPO_ROOT)

from cine_forge.services.provider_capability_smoke import (  # noqa: E402
    ProviderCapabilitySmokeService,
)


def main() -> int:
    snapshot = ProviderCapabilitySmokeService().refresh()
    print(json.dumps(snapshot.model_dump(mode="json"), indent=2))
    return 0 if snapshot.status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())

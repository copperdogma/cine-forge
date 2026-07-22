#!/usr/bin/env python3
"""Run the expensive live AI capability smoke from the CLI."""

from __future__ import annotations

import argparse
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


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--run-live",
        action="store_true",
        help="Explicitly authorize the paid live text, image, and video probes.",
    )
    parser.add_argument("--output", type=Path, help="Optional JSON evidence output path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    if not args.run_live:
        print(
            "Refusing to run paid provider calls without explicit --run-live.",
            file=sys.stderr,
        )
        return 2
    snapshot = ProviderCapabilitySmokeService().refresh()
    payload = {
        "contract_version": "provider-capability-smoke-v2",
        "evidence_scope": (
            "Provider credential, transport, model access, and non-empty generation only; "
            "not model quality, value, or default-adoption evidence."
        ),
        "cost_evidence": (
            "Per-call provider cost is not returned by this smoke harness; do not use this "
            "output for cost or value decisions."
        ),
        "snapshot": snapshot.model_dump(mode="json"),
    }
    output = json.dumps(payload, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0 if snapshot.status == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: scripts/uv-safe.sh <uv-subcommand> [args...]" >&2
  exit 2
fi

DAYS="${CINE_FORGE_EXCLUDE_NEWER_DAYS:-7}"
CUTOFF="$(
  python3 - "$DAYS" <<'PY'
from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta

days = int(sys.argv[1])
cutoff = datetime.now(UTC) - timedelta(days=days)
print(cutoff.replace(microsecond=0).isoformat().replace("+00:00", "Z"))
PY
)"

SUBCOMMAND="$1"
shift

exec uv "$SUBCOMMAND" --exclude-newer "$CUTOFF" "$@"

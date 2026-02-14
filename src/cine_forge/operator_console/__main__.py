"""CLI entrypoint to run Operator Console Lite API."""

from __future__ import annotations

import uvicorn

from cine_forge.operator_console.app import create_app


def main() -> None:
    # Use import string for hot-reloading support
    uvicorn.run(
        "cine_forge.operator_console.app:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    main()

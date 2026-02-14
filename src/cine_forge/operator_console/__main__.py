"""CLI entrypoint to run Operator Console Lite API."""

from __future__ import annotations

import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Operator Console Lite API")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument(
        "--reload", action="store_true", default=True, help="Enable hot-reloading"
    )
    parser.add_argument(
        "--no-reload", action="store_false", dest="reload", help="Disable hot-reloading"
    )
    args = parser.parse_args()

    # Use import string for hot-reloading support.
    # Scope reload to source dirs only — watching output/ would kill
    # the pipeline daemon thread on every artifact write.
    reload_kwargs = {}
    if args.reload:
        reload_kwargs["reload_dirs"] = ["src"]

    uvicorn.run(
        "cine_forge.operator_console.app:app",
        host="127.0.0.1",
        port=args.port,
        reload=args.reload,
        **reload_kwargs,
    )


if __name__ == "__main__":
    main()

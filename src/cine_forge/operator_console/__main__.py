"""CLI entrypoint to run Operator Console Lite API."""

from __future__ import annotations

import uvicorn

from cine_forge.operator_console.app import create_app


def main() -> None:
    uvicorn.run(create_app(), host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()

"""Model selection for scene-breakdown fallback reasoning."""

from __future__ import annotations

from typing import Any

DEFAULT_WORK_MODEL = "claude-haiku-4-5-20251001"


def resolve_work_model(*, params: dict[str, Any], context: dict[str, Any]) -> str:
    """Honor explicit stage settings before project-wide runtime defaults."""

    runtime_params = context.get("runtime_params", {}) if isinstance(context, dict) else {}
    if not isinstance(runtime_params, dict):
        runtime_params = {}
    return str(
        params.get("work_model")
        or params.get("model")
        or params.get("default_model")
        or runtime_params.get("work_model")
        or runtime_params.get("default_model")
        or runtime_params.get("model")
        or DEFAULT_WORK_MODEL
    )

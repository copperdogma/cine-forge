"""Model selection for script normalization and retry routing."""

from __future__ import annotations

from typing import Any

DEFAULT_WORK_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_VERIFY_MODEL = "gpt-4.1-mini"


def resolve_normalization_models(
    *, params: dict[str, Any], context: dict[str, Any]
) -> tuple[str, str, str]:
    """Resolve work, verification, and escalation models without hidden upgrades.

    A retry must not escape a caller's explicit fixture or work-model boundary.
    An escalation model is therefore opt-in through stage or runtime parameters;
    otherwise retries stay on the selected work model.
    """

    runtime_params = context.get("runtime_params", {}) if isinstance(context, dict) else {}
    if not isinstance(runtime_params, dict):
        runtime_params = {}

    work_model = str(
        params.get("work_model")
        or params.get("model")
        or params.get("default_model")
        or runtime_params.get("work_model")
        or runtime_params.get("default_model")
        or runtime_params.get("model")
        or DEFAULT_WORK_MODEL
    )
    verify_model = str(
        params.get("verify_model")
        or params.get("qa_model")
        or params.get("utility_model")
        or runtime_params.get("verify_model")
        or runtime_params.get("qa_model")
        or runtime_params.get("utility_model")
        or DEFAULT_VERIFY_MODEL
    )
    escalate_model = str(
        params.get("escalate_model")
        or params.get("sota_model")
        or runtime_params.get("escalate_model")
        or runtime_params.get("sota_model")
        or work_model
    )
    return work_model, verify_model, escalate_model

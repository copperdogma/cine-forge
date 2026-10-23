"""Stop run replay while an accepted provider job has unresolved cost."""

from __future__ import annotations

from typing import Any

from cine_forge.api.exceptions import ServiceError
from cine_forge.services.cost_summary_stages import summarize_stages


def require_complete_media_cost(state: dict[str, Any], run_id: str) -> None:
    """Fail before a resume/retry creates a second run with uncertain spend."""
    # The same stage summarizer used by CostTrackingService infers historical
    # media gaps from output refs even when old run states have no receipt flag.
    summary = summarize_stages(state, [], run_id=run_id)
    if summary.cost_is_complete:
        return
    job_ids = sorted({
        receipt.provider_job_id
        for receipt in summary.uncertain if receipt.provider_job_id
    })
    jobs = f" Provider job ID(s): {', '.join(job_ids)}." if job_ids else ""
    historical = any(
        receipt.receipt_id.startswith("historical-media:")
        for receipt in summary.uncertain
    )
    historical_note = (
        " Historical media output has no recorded charge."
        if historical else ""
    )
    raise ServiceError(
        code="unresolved_media_cost",
        message=f"Run '{run_id}' has unresolved media cost and cannot be replayed safely.",
        hint=(
            "Reconcile the original provider job and its charge before resuming or retrying."
            + historical_note + jobs
        ),
        status_code=409,
    )

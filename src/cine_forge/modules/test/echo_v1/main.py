"""Echo test module used for foundational pipeline checks."""

from __future__ import annotations

from typing import Any


def run_module(
    inputs: dict[str, Any],
    params: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    del context
    if inputs:
        first_input_key = sorted(inputs.keys())[0]
        payload = inputs[first_input_key]
    else:
        payload = params.get("payload", {"message": "echo"})

    artifact_type = params.get("artifact_type", "echo_payload")
    entity_id = params.get("entity_id")
    return {
        "artifacts": [
            {
                "artifact_type": artifact_type,
                "entity_id": entity_id,
                "data": payload,
                "metadata": {
                    "lineage": [],
                    "intent": "Echo input payload for deterministic pipeline verification",
                    "rationale": "Provides a no-AI module to validate driver flow",
                    "alternatives_considered": ["direct fixture writes"],
                    "confidence": 1.0,
                    "source": "human",
                    "schema_version": "1.0.0",
                },
            }
        ],
        "cost": {
            "model": "none",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        },
    }

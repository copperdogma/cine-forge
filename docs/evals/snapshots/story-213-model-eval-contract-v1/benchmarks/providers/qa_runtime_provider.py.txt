"""Promptfoo provider for CineForge's production QA prompt and schema boundary."""

from __future__ import annotations

import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from cine_forge.ai.llm import _parse_provider, call_llm  # noqa: E402
from cine_forge.ai.model_identity import (  # noqa: E402
    validate_provider_response_identity,
)
from cine_forge.ai.qa import _build_qa_prompt  # noqa: E402
from cine_forge.env import load_cine_forge_dotenv  # noqa: E402
from cine_forge.schemas import QAResult  # noqa: E402

load_cine_forge_dotenv(REPO_ROOT)

QA_CRITERIA = [
    "heading metadata fidelity",
    "character completeness and precision",
    "summary fidelity and material coverage",
    "narrative beat accuracy and material coverage",
    "tone consistency with scene content",
    "no hallucinated story elements",
    "candidate confidence calibration against actual source fidelity",
]
GEMINI_37_INPUT_PER_M = 0.75
GEMINI_37_OUTPUT_PER_M = 3.75
PRODUCING_PROMPT = (
    "Extract scene heading metadata, complete character list, a faithful summary, "
    "narrative beats, tone, and calibrated confidence from the supplied source scene."
)


def call_api(prompt: str, options: dict, context: dict) -> dict:
    """Run one case through the exact shared qa_check prompt/schema call shape."""
    del prompt
    started = time.perf_counter()
    config = options.get("config", {})
    model = str(config.get("model", "")).strip()

    try:
        if not model:
            raise ValueError("QA runtime provider config.model is required")
        variables = context.get("vars", {})
        scene_text = variables.get("scene_text")
        extracted_data = variables.get("extracted_data")
        if not isinstance(scene_text, str) or not scene_text.strip():
            raise ValueError("QA runtime provider scene_text is required")
        if not isinstance(extracted_data, str) or not extracted_data.strip():
            raise ValueError("QA runtime provider extracted_data is required")

        provider, bare_model = _parse_provider(model)
        call_options = {
            "prompt": _build_qa_prompt(
                original_input=scene_text,
                prompt_used=PRODUCING_PROMPT,
                output_produced=extracted_data,
                criteria=QA_CRITERIA,
            ),
            "model": model,
            "response_schema": QAResult,
            "max_retries": int(config.get("max_retries", 2)),
            "max_tokens": int(config.get("max_tokens", 1200)),
            "fail_on_truncation": True,
            "request_timeout_seconds": float(
                config.get("request_timeout_seconds", 120)
            ),
        }
        result, metadata = call_llm(**call_options)
        if not isinstance(result, QAResult):
            raise TypeError("QA runtime provider expected QAResult output")
        identity = validate_provider_response_identity(
            provider=provider,
            requested_model=bare_model,
            returned_model=metadata.get("returned_model"),
            request_id=metadata.get("request_id"),
            require_returned=True,
        )
        if metadata.get("finish_reason") != "stop":
            raise ValueError("QA runtime provider did not reach terminal stop")
    except Exception as exc:
        return {
            "output": "",
            "error": str(exc),
            "latencyMs": round((time.perf_counter() - started) * 1000),
            "metadata": {
                "provider": "runtime-qa",
                "requested_model": model or None,
            },
        }

    prompt_tokens = int(metadata.get("input_tokens") or 0)
    completion_tokens = int(metadata.get("output_tokens") or 0)
    reasoning_tokens = int(metadata.get("reasoning_output_tokens") or 0)
    visible_tokens = int(metadata.get("visible_output_tokens") or completion_tokens)
    token_usage = {
        "total": prompt_tokens + completion_tokens,
        "prompt": prompt_tokens,
        "completion": visible_tokens,
    }
    if reasoning_tokens:
        token_usage["completionDetails"] = {"reasoning": reasoning_tokens}

    estimated_cost = float(metadata.get("estimated_cost_usd") or 0.0)
    if bare_model == "gemini-3.7-flash":
        estimated_cost = round(
            prompt_tokens / 1_000_000 * GEMINI_37_INPUT_PER_M
            + completion_tokens / 1_000_000 * GEMINI_37_OUTPUT_PER_M,
            8,
        )

    return {
        "output": result.model_dump_json(),
        "tokenUsage": token_usage,
        "cost": estimated_cost,
        "latencyMs": round(float(metadata.get("latency_seconds") or 0.0) * 1000),
        "cached": False,
        "metadata": {
            "provider": metadata.get("provider"),
            "model": identity.returned_model,
            "requested_model": identity.requested_model,
            "returned_model": identity.returned_model,
            "request_id": identity.request_id,
            "finish_reason": metadata.get("finish_reason"),
            "cost_estimated": True,
            "runtime_prompt": "cine_forge.ai.qa._build_qa_prompt",
            "runtime_schema": "cine_forge.schemas.QAResult",
            "runtime_max_tokens": call_options["max_tokens"],
            "runtime_max_retries": call_options["max_retries"],
            "thinking_level": None,
        },
        "raw": {
            "id": identity.request_id,
            "model": identity.returned_model,
            "usage": {
                "input_tokens": prompt_tokens,
                "output_tokens": completion_tokens,
                "reasoning_output_tokens": reasoning_tokens,
            },
        },
    }

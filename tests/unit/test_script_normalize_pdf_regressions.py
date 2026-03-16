from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from cine_forge.modules.ingest.script_normalize_v1.main import run_module
from cine_forge.modules.ingest.story_ingest_v1.main import run_module as run_story_ingest_module

_BRICK_AND_STEEL_FIXTURE_DIR = (
    Path(__file__).resolve().parents[1] / "fixtures" / "round_trip" / "brick-and-steel"
)
_BRICK_AND_STEEL_PDF = _BRICK_AND_STEEL_FIXTURE_DIR / "Brick-&-Steel.pdf"
_BRICK_AND_STEEL_FOUNTAIN = _BRICK_AND_STEEL_FIXTURE_DIR / "Brick-&-Steel.fountain"


def _fixture_ingest_payload(input_file: Path) -> dict[str, Any]:
    result = run_story_ingest_module(
        inputs={},
        params={"input_file": str(input_file)},
        context={"run_id": "unit", "stage_id": "story_ingest"},
    )
    return result["artifacts"][0]["data"]


@pytest.mark.unit
def test_run_module_routes_screenplay_pdf_away_from_smart_chunk_skip(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_input = _fixture_ingest_payload(_BRICK_AND_STEEL_PDF)
    expected_excerpt = (
        "BRICK\n"
        "To retirement.\n\n"
        "They drink long and well from the beers."
    )
    assert expected_excerpt in _BRICK_AND_STEEL_FOUNTAIN.read_text(encoding="utf-8").replace(
        "\r\n", "\n"
    )
    corrected_script = (
        "EXT. BRICK'S PATIO - DAY\n\n"
        "A gorgeous day.\n\n"
        "STEEL\n"
        "(beer raised)\n"
        "To retirement.\n\n"
        f"{expected_excerpt}\n\n"
        "INT. TRAILER HOME - DAY\n\n"
        "JACK\n"
        "Did you know Brick and Steel are retired?\n"
    )
    prompts_seen: list[str] = []

    def fake_call_llm(
        *,
        prompt: str,
        model: str,
        response_schema: Any | None = None,
        **_: Any,
    ) -> tuple[Any, dict[str, Any]]:
        prompts_seen.append(prompt)
        cost = {
            "model": model,
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }
        if response_schema is not None:
            return (
                response_schema.model_validate(
                    {
                        "source_format": "screenplay",
                        "strategy": "passthrough_cleanup",
                        "inventions": [],
                        "assumptions": [],
                        "overall_confidence": 0.9,
                        "rationale": "Regression stub metadata.",
                        "title": "BRICK & STEEL",
                    }
                ),
                cost,
            )
        if "Chunk to fix:\n" in prompt:
            return prompt.split("Chunk to fix:\n", maxsplit=1)[1], cost
        if "Source content:\n" in prompt:
            return corrected_script, cost
        raise AssertionError(f"Unexpected LLM prompt: {prompt[:120]}")

    monkeypatch.setattr(
        "cine_forge.modules.ingest.script_normalize_v1.main.call_llm",
        fake_call_llm,
    )

    result = run_module(
        inputs={"ingest": raw_input},
        params={
            "model": "claude-haiku-4-5-20251001",
            "qa_model": "mock",
            "max_retries": 0,
            "skip_qa": True,
        },
        context={"run_id": "unit", "stage_id": "normalize"},
    )

    artifact = result["artifacts"][0]
    annotations = artifact["metadata"]["annotations"]
    assert annotations["long_doc_strategy"] == "single_pass"
    assert not any("Chunk to fix:\n" in prompt for prompt in prompts_seen)
    assert expected_excerpt in artifact["data"]["script_text"]

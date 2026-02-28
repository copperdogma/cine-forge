"""Script bible extraction from canonical screenplay text.

Story-lane artifact (Spec §4.5) — cheap, always generated on import.
Single LLM call: reads the full canonical script and produces a ScriptBible
with logline, synopsis, act structure, themes, narrative arc, genre/tone.
"""

from __future__ import annotations

import logging
from typing import Any

from cine_forge.ai import call_llm
from cine_forge.schemas import ArtifactHealth, ScriptBible

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """\
You are a professional script reader and story analyst. Read the following \
screenplay and produce a comprehensive script bible.

SCREENPLAY:
{script_text}

==========

Analyze the screenplay above and extract:

1. **title** — The title of the screenplay.
2. **logline** — A single compelling sentence that captures the story's premise, \
protagonist, conflict, and stakes.
3. **synopsis** — A 1-3 paragraph synopsis covering the full story arc. Include \
key plot points but keep it concise.
4. **act_structure** — Break the screenplay into its dramatic acts (typically 3, \
but use whatever structure the script supports). For each act:
   - act_number (1, 2, 3...)
   - title (short label like "Setup", "Confrontation", "Resolution")
   - start_scene (the scene heading or description where the act begins)
   - end_scene (where the act ends)
   - summary (1-2 sentences)
   - turning_points (key plot beats within the act)
5. **themes** — Major thematic concerns. For each:
   - theme (name)
   - description (how it manifests)
   - evidence (scene references or brief quotes, 2-4 items)
6. **narrative_arc** — Describe the overall story shape and dramatic movement.
7. **genre** — Primary genre (e.g. "Action-Thriller", "Drama", "Sci-Fi Horror").
8. **tone** — Dominant tone (e.g. "Gritty and intense", "Darkly comedic").
9. **protagonist_journey** — The protagonist's transformation arc.
10. **central_conflict** — The core dramatic conflict.
11. **setting_overview** — Time period, locations, and world context.
12. **confidence** — Your confidence in this analysis (0.0-1.0).

Return valid JSON matching the provided schema. Be specific and evidence-grounded.\
"""


def run_module(
    inputs: dict[str, Any], params: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    announce = context.get("announce_artifact")
    canonical = _extract_canonical_script(inputs)
    script_text = canonical["script_text"]

    work_model = params.get("work_model") or "claude-sonnet-4-6"
    max_tokens = int(params.get("max_tokens", 4096))

    logger.info("Extracting script bible via %s...", work_model)

    prompt = EXTRACTION_PROMPT.format(script_text=script_text)

    if work_model == "mock":
        bible_data = _mock_script_bible()
        cost = _empty_cost(work_model)
    else:
        bible, cost = call_llm(
            prompt=prompt,
            model=work_model,
            response_schema=ScriptBible,
            max_tokens=max_tokens,
            temperature=0.0,
            fail_on_truncation=True,
        )
        assert isinstance(bible, ScriptBible)
        bible_data = bible.model_dump(mode="json")

    logger.info(
        "Script bible extracted: %s (%d acts, %d themes, confidence=%.2f)",
        bible_data.get("title", "?"),
        len(bible_data.get("act_structure", [])),
        len(bible_data.get("themes", [])),
        bible_data.get("confidence", 0),
    )

    artifact = {
        "artifact_type": "script_bible",
        "entity_id": "project",
        "data": bible_data,
        "metadata": {
            "intent": "Extract high-level story understanding from canonical script",
            "rationale": "Script bible is the story's identity document (ADR-003 §12)",
            "confidence": bible_data.get("confidence", 0.8),
            "source": "ai",
            "schema_version": "1.0.0",
            "health": ArtifactHealth.VALID.value,
        },
    }

    if announce:
        announce(artifact)

    return {"artifacts": [artifact], "cost": cost}


def _extract_canonical_script(inputs: dict[str, Any]) -> dict[str, Any]:
    """Extract canonical_script data from module inputs."""
    if not inputs:
        raise ValueError("script_bible_v1 requires upstream canonical_script artifact")
    payload = list(inputs.values())[-1]
    if not isinstance(payload, dict) or "script_text" not in payload:
        raise ValueError("script_bible_v1 requires canonical_script input data")
    script_text = payload.get("script_text")
    if not isinstance(script_text, str) or not script_text.strip():
        raise ValueError(
            "script_bible_v1 requires non-empty canonical script text. "
            "Upstream normalize output is blank."
        )
    return payload


def _mock_script_bible() -> dict[str, Any]:
    """Return a minimal valid ScriptBible for testing with model='mock'."""
    return ScriptBible(
        title="Test Screenplay",
        logline="A test story about testing.",
        synopsis="This is a test screenplay used for validation.",
        act_structure=[
            {
                "act_number": 1,
                "title": "Setup",
                "start_scene": "INT. ROOM - DAY",
                "end_scene": "EXT. STREET - NIGHT",
                "summary": "The story begins.",
                "turning_points": ["The inciting incident occurs."],
            }
        ],
        themes=[
            {
                "theme": "Testing",
                "description": "The importance of validation.",
                "evidence": ["Scene 1: character tests something."],
            }
        ],
        narrative_arc="A simple arc from start to finish.",
        genre="Test",
        tone="Neutral",
        protagonist_journey="The protagonist learns to test.",
        central_conflict="Man vs. Bug.",
        setting_overview="A testing environment.",
        confidence=0.7,
    ).model_dump(mode="json")


def _empty_cost(model: str) -> dict[str, Any]:
    return {
        "model": model,
        "input_tokens": 0,
        "output_tokens": 0,
        "estimated_cost_usd": 0.0,
        "latency_seconds": 0.0,
        "request_id": None,
    }

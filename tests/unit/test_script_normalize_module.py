from __future__ import annotations

from typing import Any

import pytest

from cine_forge.modules.ingest.script_normalize_v1.main import (
    _build_normalization_prompt,
    _is_screenplay_path,
    run_module,
)
from cine_forge.schemas import QAResult


def _raw_input_payload(
    content: str,
    detected_format: str = "screenplay",
    confidence: float = 0.9,
) -> dict[str, Any]:
    return {
        "content": content,
        "source_info": {
            "original_filename": "sample.fountain",
            "file_size_bytes": len(content.encode("utf-8")),
            "character_count": len(content),
            "line_count": content.count("\n") + 1,
            "file_format": "fountain",
        },
        "classification": {
            "detected_format": detected_format,
            "confidence": confidence,
            "evidence": ["test fixture"],
        },
    }


@pytest.mark.unit
def test_prompt_strategy_cleanup_for_high_confidence_screenplay() -> None:
    prompt = _build_normalization_prompt(
        content="INT. ROOM - NIGHT",
        source_format="screenplay",
        target_strategy="passthrough_cleanup",
        long_doc_strategy="single_pass",
        feedback="",
    )
    assert "clean and validate screenplay formatting" in prompt
    assert "Detected source format: screenplay." in prompt


@pytest.mark.unit
def test_prompt_strategy_conversion_for_prose() -> None:
    prompt = _build_normalization_prompt(
        content="She walked through the market.",
        source_format="prose",
        target_strategy="full_conversion",
        long_doc_strategy="single_pass",
        feedback="",
    )
    assert "convert source into screenplay format while preserving intent" in prompt


@pytest.mark.unit
def test_is_screenplay_path_uses_parser_signal(monkeypatch: pytest.MonkeyPatch) -> None:
    raw = _raw_input_payload("random text", detected_format="prose", confidence=0.2)

    class FakeResult:
        parseable = True
        coverage = 0.8
        parser_backend = "test"
        issues: list[str] = []

    monkeypatch.setattr(
        "cine_forge.modules.ingest.script_normalize_v1.main.validate_fountain_structure",
        lambda _: FakeResult(),
    )
    assert _is_screenplay_path(raw) is True


@pytest.mark.unit
def test_is_screenplay_path_handles_compact_scene_headings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = _raw_input_payload(
        "EXT.CITYCENTRE- NIGHT\nMARA\nGo.\nINT.RUDDY& GREENBUILDING- ELEVATOR\nROSE\nNow.",
        detected_format="prose",
        confidence=0.2,
    )

    class FakeResult:
        parseable = False
        coverage = 0.0
        parser_backend = "test"
        issues: list[str] = []

    monkeypatch.setattr(
        "cine_forge.modules.ingest.script_normalize_v1.main.validate_fountain_structure",
        lambda _: FakeResult(),
    )

    assert _is_screenplay_path(raw) is True


@pytest.mark.unit
def test_run_module_with_mock_model_produces_canonical_script() -> None:
    result = run_module(
        inputs={"ingest": _raw_input_payload("INT. LAB - NIGHT\nMARA\nWe begin.")},
        params={"model": "mock", "qa_model": "mock", "max_retries": 1, "skip_qa": False},
        context={"run_id": "unit", "stage_id": "normalize"},
    )

    artifact = result["artifacts"][0]
    assert artifact["artifact_type"] == "canonical_script"
    assert "script_text" in artifact["data"]
    assert artifact["data"]["line_count"] > 0
    assert artifact["metadata"]["annotations"]["qa_result"]["passed"] is True
    assert result["cost"]["estimated_cost_usd"] == 0.0


@pytest.mark.unit
def test_run_module_retries_after_qa_error(monkeypatch: pytest.MonkeyPatch) -> None:
    call_counter = {"count": 0}

    def fake_run_qa(**_: Any):
        call_counter["count"] += 1
        if call_counter["count"] == 1:
            return (
                QAResult(
                    passed=False,
                    confidence=0.4,
                    issues=[
                        {
                            "severity": "error",
                            "description": "Missing key dialogue",
                            "location": "Scene 1",
                        }
                    ],
                    summary="Needs fix",
                ),
                [],
                {"model": "mock", "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0},
            )
        return (
            QAResult(passed=True, confidence=0.9, issues=[], summary="Good"),
            [],
            {"model": "mock", "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0},
        )

    monkeypatch.setattr("cine_forge.modules.ingest.script_normalize_v1.main._run_qa", fake_run_qa)

    result = run_module(
        inputs={
            "ingest": _raw_input_payload(
                "A prose paragraph.", detected_format="prose", confidence=0.6
            )
        },
        params={"model": "mock", "qa_model": "gpt-4o-mini", "max_retries": 2, "skip_qa": False},
        context={"run_id": "unit", "stage_id": "normalize"},
    )

    assert result["artifacts"][0]["metadata"]["annotations"]["qa_result"]["passed"] is True
    assert call_counter["count"] == 2


@pytest.mark.unit
def test_run_module_skip_qa_does_not_call_qa(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_if_called(**_: Any):
        raise AssertionError("QA should not be called when skip_qa=true")

    monkeypatch.setattr(
        "cine_forge.modules.ingest.script_normalize_v1.main._run_qa", fail_if_called
    )

    result = run_module(
        inputs={
            "ingest": _raw_input_payload(
                "A prose paragraph.", detected_format="prose", confidence=0.6
            )
        },
        params={"model": "mock", "qa_model": "mock", "max_retries": 1, "skip_qa": True},
        context={"run_id": "unit", "stage_id": "normalize"},
    )

    annotations = result["artifacts"][0]["metadata"]["annotations"]
    assert "qa_result" not in annotations


@pytest.mark.unit
def test_run_module_marks_needs_review_after_qa_retries_exhausted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_qa(**_: Any):
        return (
            QAResult(
                passed=False,
                confidence=0.4,
                issues=[
                    {
                        "severity": "error",
                        "description": "Format invalid",
                        "location": "Scene 2",
                    }
                ],
                summary="Still broken",
            ),
            [],
            {"model": "mock", "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0},
        )

    monkeypatch.setattr("cine_forge.modules.ingest.script_normalize_v1.main._run_qa", fail_qa)

    result = run_module(
        inputs={
            "ingest": _raw_input_payload(
                "A prose paragraph.", detected_format="prose", confidence=0.6
            )
        },
        params={"model": "mock", "qa_model": "gpt-4o-mini", "max_retries": 1, "skip_qa": False},
        context={"run_id": "unit", "stage_id": "normalize"},
    )

    metadata = result["artifacts"][0]["metadata"]
    assert metadata["health"] == "needs_review"
    assert metadata["annotations"]["qa_result"]["passed"] is False


@pytest.mark.unit
def test_run_module_keeps_valid_health_when_qa_has_only_warnings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def warning_qa(**_: Any):
        return (
            QAResult(
                passed=True,
                confidence=0.75,
                issues=[
                    {
                        "severity": "warning",
                        "description": "Scene transition abrupt",
                        "location": "Scene 3",
                    }
                ],
                summary="Pass with warning",
            ),
            [],
            {"model": "mock", "input_tokens": 0, "output_tokens": 0, "estimated_cost_usd": 0.0},
        )

    monkeypatch.setattr("cine_forge.modules.ingest.script_normalize_v1.main._run_qa", warning_qa)

    result = run_module(
        inputs={
            "ingest": _raw_input_payload(
                "A prose paragraph.", detected_format="prose", confidence=0.6
            )
        },
        params={"model": "mock", "qa_model": "gpt-4o-mini", "max_retries": 1, "skip_qa": False},
        context={"run_id": "unit", "stage_id": "normalize"},
    )

    metadata = result["artifacts"][0]["metadata"]
    assert metadata["health"] == "valid"
    assert metadata["annotations"]["qa_result"]["issues"][0]["severity"] == "warning"


@pytest.mark.unit
def test_run_module_marks_needs_review_when_cost_ceiling_exceeded() -> None:
    result = run_module(
        inputs={"ingest": _raw_input_payload("INT. LAB - NIGHT\nMARA\nWe begin.")},
        params={
            "model": "mock",
            "qa_model": "mock",
            "max_retries": 1,
            "skip_qa": True,
            "cost_ceiling_usd": -1.0,
        },
        context={"run_id": "unit", "stage_id": "normalize"},
    )
    metadata = result["artifacts"][0]["metadata"]
    assert metadata["health"] == "needs_review"
    assert metadata["annotations"]["cost_ceiling_exceeded"] is True


@pytest.mark.unit
def test_normalization_prevents_degenerate_output_from_degraded_input() -> None:
    # Simulating the case where ingestion repair has worked, or we have compact headings
    content = "\n".join(
        [
            "EXT. CITY CENTRE - NIGHT",
            "A ruined city.",
            "EXT. RUDDY& GREENEBUILDING - FRONT - NIGHT",
            "MARINER",
            "Move.",
        ]
    )
    # If the input is correctly identified as screenplay, normalization should preserve it
    result = run_module(
        inputs={"ingest": _raw_input_payload(content, detected_format="screenplay")},
        params={"model": "mock", "qa_model": "mock", "skip_qa": True},
        context={"run_id": "unit", "stage_id": "normalize"},
    )
    artifact = result["artifacts"][0]
    script_text = artifact["data"]["script_text"]
    assert "UNKNOWN LOCATION" not in script_text
    assert "EXT. CITY CENTRE - NIGHT" in script_text
    assert "EXT. RUDDY& GREENEBUILDING - FRONT - NIGHT" in script_text


@pytest.mark.unit
def test_run_module_detects_fdx_and_records_export_annotations() -> None:
    fdx_input = """<?xml version="1.0" encoding="UTF-8"?>
<FinalDraft DocumentType="Script">
  <Content>
    <Paragraph Type="Scene Heading"><Text>INT. LAB - NIGHT</Text></Paragraph>
    <Paragraph Type="Character"><Text>MARA</Text></Paragraph>
    <Paragraph Type="Dialogue"><Text>We begin.</Text></Paragraph>
  </Content>
</FinalDraft>
"""
    raw = _raw_input_payload(fdx_input, detected_format="unknown", confidence=0.1)
    raw["source_info"]["original_filename"] = "sample.fdx"

    result = run_module(
        inputs={"ingest": raw},
        params={
            "model": "mock",
            "qa_model": "mock",
            "max_retries": 1,
            "skip_qa": False,
            "export_formats": ["fdx", "pdf"],
        },
        context={"run_id": "unit", "stage_id": "normalize"},
    )

    artifact = result["artifacts"][0]
    assert artifact["data"]["normalization"]["source_format"] == "fdx"
    annotations = artifact["metadata"]["annotations"]
    assert annotations["fdx_input_detected"] is True
    assert annotations["interop_exports"][0]["format"] == "fdx"
    assert annotations["interop_exports"][0]["success"] is True

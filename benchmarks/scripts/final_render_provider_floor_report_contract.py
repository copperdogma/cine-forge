"""Fail-closed evidence loading for the final-render provider-floor report."""

from __future__ import annotations

import math
from collections import defaultdict
from pathlib import Path
from statistics import mean
from typing import Any

from final_render_provider_floor_packet_evidence import validated_dataset_packets
from final_render_provider_floor_quality_metrics import validated_response_metrics
from final_render_provider_floor_runtime_evidence import validated_runtime_rows
from final_render_provider_floor_task_contract import load_task_contract

RUBRIC_PASS_THRESHOLD = 0.8


def validated_evidence(
    *,
    promptfoo_entries: list[dict[str, Any]],
    runtime_payload: dict[str, Any],
    dataset_root: Path,
    task_path: Path,
    scorer: Any,
) -> dict[str, Any] | None:
    """Return only task-complete, replayed, internally consistent evidence."""
    contract = load_task_contract(task_path)
    if contract is None:
        return None
    benchmark_root = task_path.parent.parent
    dataset = validated_dataset_packets(
        dataset_root=dataset_root,
        benchmark_root=benchmark_root,
        repo_root=benchmark_root.parent,
        contract=contract,
        runtime_payload=runtime_payload,
    )
    if dataset is None:
        return None
    packets, provenance = dataset
    runtime_rows = validated_runtime_rows(
        payload=runtime_payload,
        contract=contract,
        packets=packets,
        provenance=provenance,
    )
    quality_rows = _quality_rows(
        promptfoo_entries,
        contract=contract,
        benchmark_root=benchmark_root,
        packets=packets,
        scorer=scorer,
    )
    if runtime_rows is None or quality_rows is None:
        return None
    return {
        "variants": contract["variants"],
        "runtime_rows": runtime_rows,
        "quality_rows": quality_rows,
        "runtime_result": {
            key: provenance[key]
            for key in (
                "runtime_result_scope",
                "runtime_result_path",
                "runtime_result_sha256",
                "runtime_payload_sha256",
            )
        },
    }


def _quality_rows(
    entries: list[dict[str, Any]],
    *,
    contract: dict[str, Any],
    benchmark_root: Path,
    packets: dict[tuple[str, str], dict[str, Any]],
    scorer: Any,
) -> dict[str, dict[str, Any]] | None:
    observed: list[tuple[str, str]] = []
    buckets: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {"python": [], "rubric": [], "overall": [], "latency": [], "cost": []}
    )
    for entry in entries:
        result = _regraded_entry(
            entry,
            contract=contract,
            benchmark_root=benchmark_root,
            packets=packets,
            scorer=scorer,
        )
        if result is None:
            return None
        variant, case_id, scores = result
        observed.append((variant, case_id))
        for key, value in scores.items():
            buckets[variant][key].append(value)
    if len(observed) != len(contract["pairs"]) or set(observed) != contract["pairs"]:
        return None
    if any(observed.count(pair) != 1 for pair in set(observed)):
        return None
    return {
        variant: {
            "python_overall": round(mean(bucket["python"]), 4),
            "rubric_overall": round(mean(bucket["rubric"]), 4),
            "overall": round(mean(bucket["overall"]), 4),
            "analysis_latency_ms": round(mean(bucket["latency"]), 6),
            "analysis_cost_usd": round(mean(bucket["cost"]), 6),
            "calls": len(bucket["overall"]),
        }
        for variant, bucket in buckets.items()
    }


def _regraded_entry(
    entry: object,
    *,
    contract: dict[str, Any],
    benchmark_root: Path,
    packets: dict[tuple[str, str], dict[str, Any]],
    scorer: Any,
) -> tuple[str, str, dict[str, float]] | None:
    if not isinstance(entry, dict):
        return None
    response = entry.get("response")
    provider = entry.get("provider")
    vars_data = entry.get("vars")
    metadata = response.get("metadata") if isinstance(response, dict) else None
    output = response.get("output") if isinstance(response, dict) else None
    if not all(isinstance(value, dict) for value in (provider, vars_data, metadata)):
        return None
    if not isinstance(output, (str, dict)) or not output:
        return None
    variant = metadata.get("candidate_variant")
    case_id = vars_data.get("clip_id")
    if variant not in contract["variants"] or case_id not in contract["cases"]:
        return None
    case = contract["cases"][case_id]
    variant_contract = contract["variants"][variant]
    packet = packets.get((str(variant), str(case_id)))
    if packet is None or not _entry_contract_matches(
        entry=entry,
        response=response,
        metadata=metadata,
        provider=provider,
        vars_data=vars_data,
        variant_contract=variant_contract,
        case=case,
        packet=packet,
        grader=contract["grader"],
        prompt_text=contract["prompt_text"],
    ):
        return None
    python_component = _component(entry, case["assertions"][0])
    rubric_component = _component(
        entry,
        case["assertions"][1],
        expected_rendered=case["rendered_rubric"],
    )
    grading = entry.get("gradingResult")
    components = grading.get("componentResults") if isinstance(grading, dict) else None
    if (
        python_component is None
        or rubric_component is None
        or not isinstance(components, list)
        or len(components) != 2
        or entry.get("success") is not True
        or grading.get("pass") is not True
    ):
        return None
    rubric_score, rubric_pass = rubric_component
    if not rubric_pass or rubric_score < RUBRIC_PASS_THRESHOLD:
        return None
    finalized = _replayed_python_score(
        output=output,
        benchmark_root=benchmark_root,
        case=case,
        model_label=str(provider.get("label") or variant),
        prompt_version=metadata["prompt_version"],
        scorer=scorer,
    )
    if finalized is None:
        return None
    python_score = float(finalized["score"])
    stored_python_score, stored_python_pass = python_component
    expected_overall = (python_score + rubric_score) / 2
    response_metrics = validated_response_metrics(
        entry=entry,
        response=response,
        max_completion_tokens=variant_contract["max_tokens"],
    )
    if (
        finalized["pass"] is not True
        or stored_python_pass is not True
        or not _same_value(stored_python_score, python_score)
        or not _same_value(entry.get("score"), expected_overall)
        or not _same_value(grading.get("score"), expected_overall)
        or response_metrics is None
    ):
        return None
    latency_ms, cost_usd = response_metrics
    return (
        str(variant),
        str(case_id),
        {
            "python": python_score,
            "rubric": rubric_score,
            "overall": expected_overall,
            "latency": latency_ms,
            "cost": cost_usd,
        },
    )


def _replayed_python_score(
    *,
    output: str | dict[str, Any],
    benchmark_root: Path,
    case: dict[str, Any],
    model_label: str,
    prompt_version: str,
    scorer: Any,
) -> dict[str, Any] | None:
    try:
        score = scorer.score_output_against_target(
            output=output,
            target_path=(benchmark_root / case["target_path"]).resolve(),
            model_label=model_label,
            prompt_version=prompt_version,
            expected_clip_id=case["evaluation_id"],
        )
        return scorer.finalize_score(
            score.overall_score,
            pass_threshold=scorer.PASS_THRESHOLD,
            hard_gates=score.hard_constraints_passed,
            reason=scorer.format_score_reason(score),
        )
    except Exception:
        return None


def _entry_contract_matches(
    *,
    entry: dict[str, Any],
    response: dict[str, Any],
    metadata: dict[str, Any],
    provider: dict[str, Any],
    vars_data: dict[str, Any],
    variant_contract: dict[str, Any],
    case: dict[str, Any],
    packet: dict[str, Any],
    grader: str,
    prompt_text: str,
) -> bool:
    test_case = entry.get("testCase")
    test_options = test_case.get("options") if isinstance(test_case, dict) else None
    top_metadata = entry.get("metadata")
    prompt = entry.get("prompt")
    prompt_config = prompt.get("config") if isinstance(prompt, dict) else None
    expected_metadata = {
        "clip_id": case["vars"]["clip_id"],
        "evaluation_id": case["evaluation_id"],
        "candidate_variant": packet["meta"]["candidate_variant"],
        "prompt_version": variant_contract["prompt_version"],
        "frame_policy": variant_contract["frame_policy"],
        "model": variant_contract["model"],
        "requested_model": variant_contract["model"],
        "returned_model": (
            response.get("raw", {}).get("model")
            if isinstance(response.get("raw"), dict)
            else None
        ),
        "request_id": (
            response.get("raw", {}).get("id")
            if isinstance(response.get("raw"), dict)
            else None
        ),
        "provider": variant_contract["provider"],
        "modality": "ordered_jpeg_frame_packet",
        "audio_submitted": False,
        "frame_count": packet["frame_count"],
        "sample_times_seconds": packet["sample_times_seconds"],
        "frame_sha256": packet["frame_sha256"],
        "meta_sha256": packet["meta_sha256"],
        "subject_contract_sha256": variant_contract["subject_contract_sha256"],
    }
    return (
        vars_data == case["vars"]
        and isinstance(prompt, dict)
        and prompt.get("raw") == prompt_text
        and prompt_config == {"provider": grader}
        and provider
        == {
            "id": variant_contract["provider_id"],
            "label": variant_contract["label"],
        }
        and response.get("error") in (None, "")
        and response.get("cached") is False
        and metadata == expected_metadata
        and _exact_top_metadata(top_metadata, expected_metadata)
        and isinstance(test_case, dict)
        and test_case.get("vars") == case["vars"]
        and test_case.get("assert") == case["assertions"]
        and test_options == {"provider": grader}
    )


def _exact_top_metadata(value: object, expected: dict[str, Any]) -> bool:
    if value == expected:
        return True
    return isinstance(value, dict) and value == {
        **expected,
        "_promptfooFileMetadata": {},
    }


def _component(
    entry: dict[str, Any],
    expected_assertion: dict[str, Any],
    *,
    expected_rendered: str | None = None,
) -> tuple[float, bool] | None:
    grading = entry.get("gradingResult")
    components = grading.get("componentResults") if isinstance(grading, dict) else None
    if not isinstance(components, list):
        return None
    matches = [
        component
        for component in components
        if isinstance(component, dict)
        and component.get("assertion") == expected_assertion
    ]
    if len(matches) != 1 or not _finite_bounded_score(matches[0].get("score")):
        return None
    component = matches[0]
    metadata = component.get("metadata")
    if expected_rendered is not None and (
        not isinstance(metadata, dict)
        or metadata.get("renderedAssertionValue") != expected_rendered
    ):
        return None
    passed = component.get("pass")
    return (float(component["score"]), passed) if isinstance(passed, bool) else None


def _nonnegative_fields(payload: dict[str, Any], fields: tuple[str, ...]) -> bool:
    return all(_finite_nonnegative(payload.get(field)) for field in fields)


def _finite_nonnegative(value: object) -> bool:
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(float(value))
        and float(value) >= 0.0
    )


def _finite_bounded_score(value: object) -> bool:
    return _finite_nonnegative(value) and float(value) <= 1.0


def _rounded_mean(values: Any) -> float:
    return round(mean(values), 3)


def _same_value(actual: object, expected: object) -> bool:
    if isinstance(expected, dict):
        return isinstance(actual, dict) and set(actual) == set(expected) and all(
            _same_value(actual[key], value) for key, value in expected.items()
        )
    if isinstance(expected, (int, float)) and not isinstance(expected, bool):
        return _finite_nonnegative(actual) and math.isclose(
            float(actual), float(expected), rel_tol=0.0, abs_tol=1e-6
        )
    return actual == expected

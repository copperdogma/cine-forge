"""Quality-response mutations for final-render fail-closed report tests."""

from __future__ import annotations


def apply_quality_entry_mutation(name: str, *, entries: list[dict], entry: dict) -> bool:
    if name == "missing_quality_row":
        entries.pop()
    elif name == "duplicate_quality_row":
        entries.append(dict(entries[0]))
    elif name == "missing_output":
        entry["response"].pop("output")
    elif name == "unregradable_output":
        entry["response"]["output"] = "{}"
    elif name == "rubric_below_numeric_floor":
        set_component(entry, "llm-rubric", score=0.79, passed=True)
        entry["score"] = 0.895
    elif name == "stored_python_score_mismatch":
        set_component(entry, "python", score=0.99, passed=True)
        entry["score"] = 0.945
    elif name == "stored_python_pass_mismatch":
        set_component(entry, "python", score=1.0, passed=False)
    elif name == "top_level_score_mismatch":
        entry["score"] = 0.99
    elif name == "extra_failing_component":
        entry["gradingResult"]["componentResults"].append(
            {"assertion": {"type": "extra"}, "score": 0.0, "pass": False}
        )
        entry["gradingResult"]["pass"] = False
        entry["success"] = False
    elif name == "missing_response_token_usage":
        entry["response"].pop("tokenUsage")
    elif name == "response_latency_contradiction":
        entry["response"]["latencyMs"] = -50
    elif name == "response_cost_contradiction":
        entry["response"]["cost"] = 999
    elif name == "response_cost_understatement":
        entry["response"]["cost"] = entry["cost"] = 0.000001
    elif name == "response_zero_usage_and_cost":
        entry["response"]["tokenUsage"].update(prompt=0, completion=0, total=0)
        entry["response"]["cost"] = entry["cost"] = 0.0
    elif name == "response_zero_latency":
        entry["response"]["latencyMs"] = entry["latencyMs"] = 0
    elif name == "response_token_total_contradiction":
        entry["response"]["tokenUsage"].update(
            prompt=100_000, completion=100_000, total=1
        )
    elif name == "response_completion_cap_contradiction":
        entry["response"]["tokenUsage"].update(
            prompt=100, completion=1_401, total=1_501
        )
    elif name == "response_reasoning_contradiction":
        entry["response"]["tokenUsage"]["completionDetails"] = {"reasoning": 21}
    elif name == "response_request_count_contradiction":
        entry["response"]["tokenUsage"]["numRequests"] = 2
    elif name == "response_extra_usage_field":
        entry["response"]["tokenUsage"]["untrusted"] = 0
    elif name == "response_missing_raw":
        entry["response"].pop("raw")
    elif name == "response_raw_request_id_missing":
        entry["response"]["raw"].pop("id")
    elif name == "response_request_id_contradiction":
        entry["response"]["metadata"]["request_id"] = "contradictory-request"
    elif name == "response_returned_model_contradiction":
        entry["response"]["metadata"]["returned_model"] = "gpt-4o-mini"
    elif name == "response_raw_model_contradiction":
        entry["response"]["raw"]["model"] = "gpt-5.4-unrequested"
    elif name == "response_raw_usage_contradiction":
        entry["response"]["raw"]["usage"]["total_tokens"] += 1
    elif name == "response_cached_true":
        entry["response"]["cached"] = True
    elif name == "response_metadata_extra":
        entry["response"]["metadata"]["untrusted"] = "value"
    elif name == "top_metadata_extra":
        entry["metadata"]["untrusted"] = "value"
    elif name == "prompt_config_extra":
        entry["prompt"]["config"]["untrusted"] = "value"
    elif name == "provider_extra":
        entry["provider"]["untrusted"] = "value"
    elif name == "test_options_extra":
        entry["testCase"]["options"]["untrusted"] = "value"
    elif name == "subject_contract_fingerprint_contradiction":
        entry["response"]["metadata"]["subject_contract_sha256"] = "0" * 64
    else:
        return False
    return True


def set_component(entry: dict, assertion_type: str, *, score: float, passed: bool) -> None:
    component = next(
        item
        for item in entry["gradingResult"]["componentResults"]
        if item["assertion"]["type"] == assertion_type
    )
    component.update(score=score, **{"pass": passed})

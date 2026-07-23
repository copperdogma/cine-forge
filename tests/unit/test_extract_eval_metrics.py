"""Truth contracts for the retained-result metrics extractor."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "extract-eval-metrics.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("extract_eval_metrics", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _result_entry(
    *,
    label: str = "Gemini 3.6 Flash",
    provider_id: str = "google:gemini-3.6-flash",
    latency_ms: int | None = 1200,
    cost: float | None = 0.0003,
    case_vars: dict | None = None,
) -> dict:
    if case_vars is None:
        case_vars = {
            "screenplay": "file://../input/the-mariner.md",
            "golden_path": "golden/the-mariner-config.json",
        }
    entry = {
        "provider": {"label": label, "id": provider_id},
        "response": {
            "tokenUsage": {"prompt": 100, "completion": 20, "total": 120},
            "raw": {
                "responseId": "gemini-response-123",
                "modelVersion": provider_id.rsplit(":", 1)[-1],
                "usageMetadata": {
                    "promptTokenCount": 100,
                    "candidatesTokenCount": 20,
                    "totalTokenCount": 120,
                },
            },
        },
        "vars": case_vars,
        "testCase": {"vars": case_vars},
    }
    if latency_ms is not None:
        entry["latencyMs"] = latency_ms
    if cost is not None:
        entry["cost"] = cost
    return entry


def _write_task(repo_root: Path, eval_id: str, cases: list[dict]) -> Path:
    task_path = repo_root / "benchmarks" / "tasks" / f"{eval_id}.yaml"
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(json.dumps({"tests": [{"vars": case} for case in cases]}))
    return task_path


def _write_contract_task(
    repo_root: Path,
    eval_id: str,
    cases: list[dict],
) -> tuple[Path, dict]:
    prompt_text = "Evaluate this case against the current exact contract."
    prompt_path = repo_root / "benchmarks" / "prompts" / f"{eval_id}.txt"
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(f"{prompt_text}\n")
    task = {
        "defaultTest": {
            "options": {"provider": "anthropic:messages:claude-opus-4-6"}
        },
        "prompts": [f"file://../prompts/{eval_id}.txt"],
        "providers": [
            {
                "id": "google:gemini-3.6-flash",
                "label": "Gemini 3.6 Flash",
                "config": {
                    "maxOutputTokens": 65536,
                    "inputCost": 0.0000015,
                    "outputCost": 0.0000075,
                    "apiKeyEnvar": "GEMINI_API_KEY",
                },
            },
            {
                "id": "anthropic:messages:claude-haiku-4-5-20251001",
                "label": "Claude Haiku 4.5",
                "config": {"temperature": 0, "max_tokens": 4096},
            },
        ],
        "tests": [
            {
                "description": f"current case {index}",
                "vars": case,
                "assert": [
                    {
                        "type": "llm-rubric",
                        "value": "Judge only against the current source contract.",
                    }
                ],
            }
            for index, case in enumerate(cases)
        ],
    }
    task_path = repo_root / "benchmarks" / "tasks" / f"{eval_id}.yaml"
    task_path.parent.mkdir(parents=True, exist_ok=True)
    task_path.write_text(json.dumps(task))
    return task_path, task


def _result_payload_with_current_contract(rows: list[dict], task: dict) -> dict:
    default_options = task["defaultTest"]["options"]
    prompt_text = "Evaluate this case against the current exact contract."
    tests_by_vars = {
        json.dumps(test["vars"], sort_keys=True): test for test in task["tests"]
    }
    for row in rows:
        test = tests_by_vars[json.dumps(row["vars"], sort_keys=True)]
        row["testCase"] = {
            **test,
            "vars": test["vars"],
            "assert": test["assert"],
            "options": default_options,
            "metadata": {},
        }
        row["promptIdx"] = 0
        row["prompt"] = {
            "raw": prompt_text,
            "label": f"prompts/task.txt: {prompt_text}",
            "config": default_options,
        }
    selected = {
        (row["provider"]["id"], row["provider"]["label"]) for row in rows
    }
    saved_providers = json.loads(
        json.dumps(
            [
                provider
                for provider in task["providers"]
                if (provider["id"], provider["label"]) in selected
            ]
        )
    )
    for provider in saved_providers:
        if "apiKeyEnvar" in provider["config"]:
            provider["config"]["apiKeyEnvar"] = "[REDACTED]"
    return {
        "results": {
            "results": rows,
            "prompts": [
                {
                    "raw": prompt_text,
                    "label": f"prompts/task.txt: {prompt_text}",
                    "provider": provider["label"] or provider["id"],
                }
                for provider in saved_providers
            ],
        },
        "config": {
            "defaultTest": task["defaultTest"],
            "prompts": task["prompts"],
            "providers": saved_providers,
            "tests": task["tests"],
        },
    }


def _identity_contract_payload(
    repo_root: Path,
    *,
    provider: dict,
    returned_model: str,
) -> tuple[Path, dict]:
    cases = [{"case": "identity"}]
    task_path, task = _write_contract_task(repo_root, "qa-pass", cases)
    task["providers"] = [provider]
    task_path.write_text(json.dumps(task))
    row = _result_entry(
        label=provider["label"],
        provider_id=provider["id"],
        case_vars=cases[0],
    )
    configured_family = provider["config"].get("provider")
    provider_family = configured_family or provider["id"].split(":", 1)[0]
    if provider_family == "google":
        row["response"]["raw"] = {
            "responseId": "provider-call-123",
            "modelVersion": returned_model,
            "usageMetadata": {
                "promptTokenCount": 100,
                "candidatesTokenCount": 20,
                "totalTokenCount": 120,
            },
        }
    else:
        row["response"]["raw"] = {
            "id": "provider-call-123",
            "model": returned_model,
            "usage": {
                "input_tokens": 100,
                "output_tokens": 20,
                "total_tokens": 120,
            },
        }
    return task_path, _result_payload_with_current_contract([row], task)


def test_extract_accepts_current_and_legacy_result_envelopes(tmp_path: Path) -> None:
    module = _load_module()
    entry = _result_entry()
    current = tmp_path / "config-detection-current.json"
    legacy = tmp_path / "config-detection-legacy.json"
    current.write_text(json.dumps({"results": {"results": [entry]}}))
    legacy.write_text(json.dumps({"results": [entry]}))

    assert module.extract_from_file(current) == module.extract_from_file(legacy)


def test_wrapped_filename_and_blank_provider_label_keep_identity(
    tmp_path: Path,
) -> None:
    module = _load_module()
    path = tmp_path / "gpt55-config-detection-2026-04-24.json"
    entry = _result_entry(
        label="",
        provider_id="xai:grok-4-1-fast-reasoning",
    )
    path.write_text(json.dumps({"results": {"results": [entry]}}))

    assert module.filename_to_eval_id(path.name) == "config-detection"
    assert list(module.extract_from_file(path)) == ["Grok 4.1 Fast Reasoning"]


def test_extract_rejects_unknown_or_non_mapping_result_rows(tmp_path: Path) -> None:
    module = _load_module()
    unknown = tmp_path / "config-detection-unknown.json"
    malformed = tmp_path / "config-detection-malformed.json"
    unknown.write_text(json.dumps({"summary": {"results": []}}))
    malformed.write_text(json.dumps({"results": {"results": ["not-a-row"]}}))

    with pytest.raises(ValueError, match="recognized Promptfoo result envelope"):
        module.extract_from_file(unknown)
    with pytest.raises(ValueError, match="result row 0"):
        module.extract_from_file(malformed)


def test_extract_rejects_duplicate_nested_result_keys(tmp_path: Path) -> None:
    module = _load_module()
    path = tmp_path / "config-detection-duplicate-key.json"
    path.write_text(
        '{"results":{"results":[],"results":[]}}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="duplicate key 'results'"):
        module.extract_from_file(path)


def test_incomplete_samples_are_not_reported_as_complete_averages(
    tmp_path: Path,
) -> None:
    module = _load_module()
    path = tmp_path / "config-detection-incomplete.json"
    path.write_text(
        json.dumps(
            {
                "results": {
                    "results": [
                        _result_entry(),
                        _result_entry(latency_ms=None, cost=None),
                    ]
                }
            }
        )
    )

    raw = module.extract_from_file(path)["Gemini 3.6 Flash"]
    averages = module.compute_averages(raw)

    assert averages["sample_count"] == 2
    assert averages["latency_sample_count"] == 1
    assert averages["cost_sample_count"] == 2  # the priced provider is estimated
    assert averages["latency_ms"] is None
    assert averages["cost_usd"] is not None


def test_gemini_cost_estimate_bills_hidden_thinking_tokens(tmp_path: Path) -> None:
    module = _load_module()
    path = tmp_path / "script-bible-gemini-thinking.json"
    entry = _result_entry(
        label="Gemini 3.5 Flash-Lite",
        provider_id="google:gemini-3.5-flash-lite",
        cost=None,
    )
    entry["response"]["tokenUsage"] = {
        "prompt": 100,
        "completion": 10,
        "total": 1110,
    }
    entry["response"]["raw"]["usageMetadata"] = {
        "promptTokenCount": 100,
        "candidatesTokenCount": 10,
        "totalTokenCount": 1110,
    }
    path.write_text(json.dumps({"results": {"results": [entry]}}))

    raw = module.extract_from_file(path)["Gemini 3.5 Flash-Lite"]

    assert entry["response"]["tokenUsage"]["completion"] == 10
    assert module.completion_tokens_for_cost(
        "google:gemini-3.5-flash-lite",
        entry["response"]["tokenUsage"],
    ) == 1010
    assert raw["costs"] == [pytest.approx(0.002555)]


def test_gemini_reasoning_is_billed_when_total_is_absent(tmp_path: Path) -> None:
    module = _load_module()
    path = tmp_path / "script-bible-gemini-reasoning-only.json"
    entry = _result_entry(
        label="Gemini 3.5 Flash-Lite",
        provider_id="google:gemini-3.5-flash-lite",
        cost=None,
    )
    entry["response"]["tokenUsage"] = {
        "prompt": 100,
        "completion": 10,
        "completionDetails": {"reasoning": 1000},
    }
    entry["response"]["raw"]["usageMetadata"] = {
        "promptTokenCount": 100,
        "candidatesTokenCount": 10,
        "thoughtsTokenCount": 1000,
    }
    path.write_text(json.dumps({"results": {"results": [entry]}}))

    raw = module.extract_from_file(path)["Gemini 3.5 Flash-Lite"]

    assert raw["costs"] == [pytest.approx(0.002555)]


def test_raw_gemini_usage_must_match_normalized_token_usage(tmp_path: Path) -> None:
    module = _load_module()
    path = tmp_path / "script-bible-gemini-raw-mismatch.json"
    entry = _result_entry(cost=None)
    entry["response"]["tokenUsage"] = {
        "prompt": 100,
        "completion": 10,
        "total": 1110,
        "completionDetails": {"reasoning": 1000},
    }
    entry["response"]["raw"]["usageMetadata"] = {
        "promptTokenCount": 100,
        "candidatesTokenCount": 10,
        "thoughtsTokenCount": 1000,
        "totalTokenCount": 1110,
    }
    entry["response"]["raw"] = {
        "responseId": "gemini-response-raw-mismatch",
        "modelVersion": "gemini-3.6-flash",
        "usageMetadata": {
            "promptTokenCount": 100,
            "candidatesTokenCount": 11,
            "thoughtsTokenCount": 999,
            "totalTokenCount": 1110,
        },
    }
    path.write_text(json.dumps({"results": {"results": [entry]}}))

    with pytest.raises(ValueError, match="raw Gemini usageMetadata does not match"):
        module.extract_from_file(path)


def test_matching_raw_and_normalized_gemini_usage_is_accepted(tmp_path: Path) -> None:
    module = _load_module()
    path = tmp_path / "script-bible-gemini-raw-match.json"
    entry = _result_entry(cost=None)
    entry["response"]["tokenUsage"] = {
        "prompt": 100,
        "completion": 10,
        "total": 1110,
        "completionDetails": {"reasoning": 1000},
    }
    entry["response"]["raw"] = {
        "responseId": "gemini-response-raw-match",
        "modelVersion": "gemini-3.6-flash",
        "usageMetadata": {
            "promptTokenCount": 100,
            "candidatesTokenCount": 10,
            "thoughtsTokenCount": 1000,
            "totalTokenCount": 1110,
        },
    }
    path.write_text(json.dumps({"results": {"results": [entry]}}))

    raw = module.extract_from_file(path)["Gemini 3.6 Flash"]

    assert raw["costs"] == [pytest.approx(0.007725)]


@pytest.mark.parametrize(
    ("reported_cost", "should_pass"),
    [
        (0.00256, True),
        (0.0028, False),
    ],
)
def test_known_model_reported_cost_must_match_derived_usage_within_tolerance(
    tmp_path: Path,
    reported_cost: float,
    should_pass: bool,
) -> None:
    module = _load_module()
    path = tmp_path / "script-bible-gemini-reported-cost.json"
    entry = _result_entry(
        label="Gemini 3.5 Flash-Lite",
        provider_id="google:gemini-3.5-flash-lite",
        cost=reported_cost,
    )
    entry["response"]["tokenUsage"] = {
        "prompt": 100,
        "completion": 10,
        "total": 1110,
        "completionDetails": {"reasoning": 1000},
    }
    entry["response"]["raw"]["usageMetadata"] = {
        "promptTokenCount": 100,
        "candidatesTokenCount": 10,
        "thoughtsTokenCount": 1000,
        "totalTokenCount": 1110,
    }
    path.write_text(json.dumps({"results": {"results": [entry]}}))

    if should_pass:
        raw = module.extract_from_file(path)["Gemini 3.5 Flash-Lite"]
        assert raw["costs"] == [reported_cost]
    else:
        with pytest.raises(ValueError, match="does not match derived usage cost"):
            module.extract_from_file(path)


def test_custom_provider_reported_cost_is_marked_estimated(tmp_path: Path) -> None:
    module = _load_module()
    path = tmp_path / "video-understanding-custom-cost.json"
    entry = _result_entry(cost=0.0003)
    entry["provider"]["id"] = "file://../providers/video_understanding_provider.py"
    entry["response"]["raw"]["modelVersion"] = "gemini-3.6-flash"
    path.write_text(json.dumps({"results": {"results": [entry]}}))

    raw = module.extract_from_file(path)["Gemini 3.6 Flash"]

    assert raw["cost_estimated"] is True


def test_declared_cost_estimation_provenance_must_be_boolean(tmp_path: Path) -> None:
    module = _load_module()
    path = tmp_path / "config-detection-invalid-cost-provenance.json"
    entry = _result_entry(cost=0.0003)
    entry["response"]["metadata"] = {"cost_estimated": "yes"}
    path.write_text(json.dumps({"results": {"results": [entry]}}))

    with pytest.raises(ValueError, match="cost_estimated must be a boolean"):
        module.extract_from_file(path)


@pytest.mark.parametrize(
    ("provider", "response"),
    [
        (
            {
                "id": "google:gemini-3.6-flash",
                "label": "Gemini 3.5 Flash-Lite",
            },
            {},
        ),
        (
            {
                "id": "file://../providers/video_understanding_provider.py",
                "label": "Gemini 3.6 Flash",
            },
            {"metadata": {"model": "gemini-3.5-flash-lite"}},
        ),
        (
            {
                "id": "google:gemini-3.6-flash",
                "label": "Gemini 3.6 Flash",
            },
            {"raw": {"modelVersion": "gemini-3.5-flash-lite"}},
        ),
        (
            {
                "id": "google:gemini-3.6-flash",
                "label": "Gemini 3.6 Flash",
            },
            {
                "raw": {
                    "modelVersion": "gemini-3.6-flash",
                    "model": "gemini-3.5-flash-lite",
                }
            },
        ),
    ],
)
def test_maintained_provider_label_id_and_model_slug_must_match_exactly(
    tmp_path: Path,
    provider: dict,
    response: dict,
) -> None:
    module = _load_module()
    path = tmp_path / "config-detection-provider-mismatch.json"
    entry = _result_entry()
    entry["provider"] = provider
    entry["response"].update(response)
    path.write_text(json.dumps({"results": {"results": [entry]}}))

    with pytest.raises(ValueError, match="provider (?:label/model|model identity) mismatch"):
        module.extract_from_file(path)


@pytest.mark.parametrize("raw", (None, "not-a-provider-response", {}))
def test_gemini_metrics_require_raw_provider_usage_evidence(
    tmp_path: Path, raw: object
) -> None:
    module = _load_module()
    entry = _result_entry(cost=None)
    if raw is None:
        entry["response"].pop("raw")
    else:
        entry["response"]["raw"] = raw
    path = tmp_path / "config-detection-gemini-missing-raw.json"
    path.write_text(json.dumps({"results": {"results": [entry]}}))

    with pytest.raises(ValueError, match="raw Gemini provider response"):
        module.extract_from_file(path)


@pytest.mark.parametrize("missing", ("responseId", "modelVersion"))
def test_gemini_metrics_require_raw_call_and_model_identity(
    tmp_path: Path,
    missing: str,
) -> None:
    module = _load_module()
    entry = _result_entry(cost=None)
    entry["response"]["raw"].pop(missing)
    path = tmp_path / f"config-detection-gemini-missing-{missing}.json"
    path.write_text(json.dumps({"results": {"results": [entry]}}))

    with pytest.raises(ValueError, match=missing):
        module.extract_from_file(path)


def test_gemini_metrics_reject_raw_prompt_and_visible_only_usage(tmp_path: Path) -> None:
    module = _load_module()
    entry = _result_entry(cost=None)
    entry["response"]["tokenUsage"].pop("total")
    entry["response"]["raw"]["usageMetadata"].pop("totalTokenCount")
    path = tmp_path / "config-detection-gemini-incomplete-usage.json"
    path.write_text(json.dumps({"results": {"results": [entry]}}))

    with pytest.raises(ValueError, match="totalTokenCount or reasoning-token evidence"):
        module.extract_from_file(path)


@pytest.mark.parametrize(
    ("token_usage", "message"),
    [
        ({}, "prompt_tokens must be a nonnegative integer"),
        (
            {"prompt": -1, "completion": 0},
            "prompt_tokens must be a nonnegative integer",
        ),
        (
            {"prompt": True, "completion": 0},
            "prompt_tokens must be a nonnegative integer",
        ),
        (
            {"prompt": 1, "completion": 2.5},
            "visible_completion_tokens must be a nonnegative integer",
        ),
        (
            {"prompt": 100, "completion": 10, "total": 109},
            "total_tokens must be at least",
        ),
        (
            {
                "prompt": 100,
                "completion": 10,
                "total": 1110,
                "billed_completion": 10,
            },
            "billed_completion_tokens does not match",
        ),
    ],
)
def test_gemini_cost_extraction_rejects_malformed_or_inconsistent_usage(
    token_usage: dict[str, object],
    message: str,
) -> None:
    module = _load_module()

    with pytest.raises(ValueError, match=message):
        module.completion_tokens_for_cost(
            "google:gemini-3.6-flash",
            token_usage,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("latencyMs", -1),
        ("latencyMs", True),
        ("latencyMs", float("nan")),
        ("cost", -0.2),
        ("cost", True),
        ("cost", float("inf")),
    ],
)
def test_extract_rejects_malformed_latency_and_cost(
    tmp_path: Path, field: str, value: object
) -> None:
    module = _load_module()
    entry = _result_entry()
    entry[field] = value
    path = tmp_path / "config-detection-malformed-metric.json"
    path.write_text(json.dumps({"results": {"results": [entry]}}))

    with pytest.raises(ValueError, match=f"{field} must be a finite nonnegative number"):
        module.extract_from_file(path)


def test_extract_rejects_impossible_gemini_usage_even_with_reported_cost(
    tmp_path: Path,
) -> None:
    module = _load_module()
    path = tmp_path / "config-detection-impossible-usage.json"
    entry = _result_entry(cost=0.004)
    entry["response"]["tokenUsage"] = {
        "prompt": 100,
        "completion": 10,
        "total": 109,
    }
    path.write_text(json.dumps({"results": {"results": [entry]}}))

    with pytest.raises(ValueError, match="total_tokens must be at least"):
        module.extract_from_file(path)


def test_registry_render_updates_only_the_exact_score_block() -> None:
    module = _load_module()
    registry = """\
evals:
  - id: config-detection
    scores:
      - model: "Gemini 3.6 Flash"
        metrics:
          overall: 0.7
        latency_ms: 999
        cost_usd: 0.9999
        cost_estimated: true
        measured: 2026-01-01
        git_sha: "abc1234"
        result_file: benchmarks/results/config-detection-gemini36.json
      - model: "Existing Model"
        metrics:
          overall: 0.9
        latency_ms: 777
        cost_usd: 0.7777
  - id: scene-extraction
    scores:
      - model: "Gemini 3.6 Flash"
        metrics:
          overall: 0.8
        latency_ms: 555
        cost_usd: 0.5555
"""
    metrics = {
        "config-detection": {
            "Gemini 3.6 Flash": {
                "latency_ms": 1234,
                "cost_usd": 0.0042,
                "cost_estimated": False,
                "sample_count": 1,
                "latency_sample_count": 1,
                "cost_sample_count": 1,
            }
        }
    }

    rendered, updated = module.render_registry_update(
        registry,
        metrics,
        selected_result_file="benchmarks/results/config-detection-gemini36.json",
    )

    assert updated == 1
    assert "latency_ms: 1234" in rendered
    assert "cost_usd: 0.0042" in rendered
    assert "cost_estimated: true" not in rendered
    assert "measured: 2026-01-01" in rendered
    assert 'git_sha: "abc1234"' in rendered
    assert "result_file: benchmarks/results/config-detection-gemini36.json" in rendered
    assert "latency_ms: 777" in rendered
    assert "cost_usd: 0.7777" in rendered
    assert "latency_ms: 555" in rendered
    assert "cost_usd: 0.5555" in rendered


def test_registry_render_fails_closed_on_missing_or_duplicate_score_blocks() -> None:
    module = _load_module()
    metrics = {
        "config-detection": {
            "Gemini 3.6 Flash": {
                "latency_ms": 1234,
                "cost_usd": 0.0042,
                "cost_estimated": False,
                "sample_count": 1,
                "latency_sample_count": 1,
                "cost_sample_count": 1,
            }
        }
    }
    missing = "evals:\n  - id: config-detection\n    scores: []\n"
    duplicate = """\
evals:
  - id: config-detection
    scores:
      - model: "Gemini 3.6 Flash"
        metrics:
          overall: 0.7
        result_file: benchmarks/results/config-detection-gemini36.json
      - model: "Gemini 3.6 Flash"
        metrics:
          overall: 0.8
        result_file: benchmarks/results/config-detection-gemini36.json
"""

    with pytest.raises(ValueError, match="exactly one registry score block"):
        module.render_registry_update(
            missing,
            metrics,
            selected_result_file="benchmarks/results/config-detection-gemini36.json",
        )
    with pytest.raises(ValueError, match="exactly one registry score block"):
        module.render_registry_update(
            duplicate,
            metrics,
            selected_result_file="benchmarks/results/config-detection-gemini36.json",
        )


def test_registry_render_selects_exact_result_file_from_model_history() -> None:
    module = _load_module()
    registry = """\
evals:
  - id: config-detection
    scores:
      - model: "Gemini 3.6 Flash"
        metrics:
          overall: 0.6
        latency_ms: 600
        cost_usd: 0.006
        result_file: benchmarks/results/config-detection-old.json
      - model: "Gemini 3.6 Flash"
        metrics:
          overall: 0.7
        latency_ms: 700
        cost_usd: 0.007
        result_file: benchmarks/results/config-detection-new.json
"""
    metrics = {
        "config-detection": {
            "Gemini 3.6 Flash": {
                "latency_ms": 1234,
                "cost_usd": 0.0042,
                "cost_estimated": False,
                "sample_count": 1,
                "latency_sample_count": 1,
                "cost_sample_count": 1,
            }
        }
    }

    rendered, updated = module.render_registry_update(
        registry,
        metrics,
        selected_result_file="benchmarks/results/config-detection-new.json",
    )

    assert updated == 1
    assert "latency_ms: 600" in rendered
    assert "cost_usd: 0.006" in rendered
    assert "latency_ms: 1234" in rendered
    assert "cost_usd: 0.0042" in rendered
    assert "latency_ms: 700" not in rendered


def test_registry_render_rejects_partial_result_metrics() -> None:
    module = _load_module()
    registry = """\
evals:
  - id: config-detection
    scores:
      - model: "Gemini 3.6 Flash"
        metrics:
          overall: 0.7
        result_file: benchmarks/results/config-detection-gemini36.json
"""
    metrics = {
        "config-detection": {
            "Gemini 3.6 Flash": {
                "latency_ms": None,
                "cost_usd": 0.0042,
                "cost_estimated": False,
                "sample_count": 2,
                "latency_sample_count": 1,
                "cost_sample_count": 2,
            }
        }
    }

    with pytest.raises(ValueError, match="incomplete result metrics"):
        module.render_registry_update(
            registry,
            metrics,
            selected_result_file="benchmarks/results/config-detection-gemini36.json",
        )


@pytest.mark.parametrize(
    ("result_file_line", "error"),
    [
        ("", "exactly one result_file"),
        (
            "        result_file: benchmarks/results/stale-run.json\n",
            "result_file mismatch",
        ),
    ],
)
def test_registry_render_rejects_missing_or_mismatched_result_identity(
    result_file_line: str,
    error: str,
) -> None:
    module = _load_module()
    registry = f"""\
evals:
  - id: config-detection
    scores:
      - model: "Gemini 3.6 Flash"
        metrics:
          overall: 0.7
{result_file_line}"""
    metrics = {
        "config-detection": {
            "Gemini 3.6 Flash": {
                "latency_ms": 1234,
                "cost_usd": 0.0042,
                "cost_estimated": False,
                "sample_count": 1,
                "latency_sample_count": 1,
                "cost_sample_count": 1,
            }
        }
    }

    with pytest.raises(ValueError, match=error):
        module.render_registry_update(
            registry,
            metrics,
            selected_result_file="benchmarks/results/fresh-run.json",
        )


def test_registry_update_dry_run_is_no_write_and_multiple_sources_fail(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    registry_path = tmp_path / "registry.yaml"
    registry_text = """\
evals:
  - id: config-detection
    scores:
      - model: "Gemini 3.6 Flash"
        metrics:
          overall: 0.7
        latency_ms: 999
        cost_usd: 0.9999
        result_file: benchmarks/results/config-detection-run.json
"""
    registry_path.write_text(registry_text)
    result_path = tmp_path / "benchmarks" / "results" / "config-detection-run.json"
    result_path.parent.mkdir(parents=True)
    _, task = _write_contract_task(
        tmp_path,
        "config-detection",
        [_result_entry()["vars"]],
    )
    result_path.write_text(
        json.dumps(_result_payload_with_current_contract([_result_entry()], task))
    )
    monkeypatch.setattr(module, "REGISTRY_PATH", registry_path)
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)

    module.update_registry([result_path], dry_run=True)

    assert registry_path.read_text() == registry_text
    with pytest.raises(ValueError, match="exactly one explicit --result-file"):
        module.update_registry([result_path, result_path], dry_run=True)


def test_registry_update_accepts_filtered_single_model_with_exact_task_matrix(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    first = {
        "scene_text": "file://../fixtures/enrich-scene-elevator.txt",
        "test_key": "good_scene",
    }
    second = {
        "scene_text": "file://../fixtures/enrich-scene-elevator.txt",
        "test_key": "bad_scene",
    }
    _, task = _write_contract_task(tmp_path, "qa-pass", [first, second])
    result_path = tmp_path / "benchmarks" / "results" / "qa-pass-run.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text(
        json.dumps(
            _result_payload_with_current_contract(
                [
                    _result_entry(case_vars=first),
                    _result_entry(case_vars=second),
                ],
                task,
            )
        )
    )
    registry_path = tmp_path / "registry.yaml"
    registry_text = """\
evals:
  - id: qa-pass
    scores:
      - model: "Gemini 3.6 Flash"
        metrics:
          overall: 0.7
        result_file: benchmarks/results/qa-pass-run.json
"""
    registry_path.write_text(registry_text)
    monkeypatch.setattr(module, "REGISTRY_PATH", registry_path)
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)

    module.update_registry([result_path], dry_run=True)

    assert registry_path.read_text() == registry_text


def test_task_contract_accepts_promptfoo_provider_prompt_column_index(
    tmp_path: Path,
) -> None:
    module = _load_module()
    cases = [{"case": "identity"}]
    task_path, task = _write_contract_task(tmp_path, "qa-pass", cases)
    google_row = _result_entry(case_vars=cases[0])
    anthropic_row = _result_entry(
        label="Claude Haiku 4.5",
        provider_id="anthropic:messages:claude-haiku-4-5-20251001",
        case_vars=cases[0],
    )
    anthropic_row["response"]["raw"] = {
        "id": "anthropic-response-123",
        "model": "claude-haiku-4-5-20251001",
        "usage": {"input_tokens": 100, "output_tokens": 20},
    }
    payload = _result_payload_with_current_contract(
        [google_row, anthropic_row],
        task,
    )
    payload["results"]["results"][1]["promptIdx"] = 1

    module.validate_result_task_contract(
        task_path,
        payload["config"],
        payload["results"]["results"],
        payload["results"]["prompts"],
        repo_root=tmp_path,
    )

    payload["results"]["results"][1]["promptIdx"] = 0
    with pytest.raises(ValueError, match="points to a different provider column"):
        module.validate_result_task_contract(
            task_path,
            payload["config"],
            payload["results"]["results"],
            payload["results"]["prompts"],
            repo_root=tmp_path,
        )


@pytest.mark.parametrize(
    ("mutation", "error"),
    [
        ("column_template", "template bytes do not match exactly one current prompt"),
        ("out_of_range", "outside result prompt columns"),
        ("non_integer", "promptIdx must be an integer"),
    ],
)
def test_task_contract_rejects_invalid_result_prompt_column_provenance(
    tmp_path: Path,
    mutation: str,
    error: str,
) -> None:
    module = _load_module()
    cases = [{"case": "identity"}]
    task_path, task = _write_contract_task(tmp_path, "qa-pass", cases)
    payload = _result_payload_with_current_contract(
        [_result_entry(case_vars=cases[0])],
        task,
    )
    if mutation == "column_template":
        payload["results"]["prompts"][0]["raw"] += " stale"
    elif mutation == "out_of_range":
        payload["results"]["results"][0]["promptIdx"] = 1
    else:
        payload["results"]["results"][0]["promptIdx"] = "0"

    with pytest.raises(ValueError, match=error):
        module.validate_result_task_contract(
            task_path,
            payload["config"],
            payload["results"]["results"],
            payload["results"]["prompts"],
            repo_root=tmp_path,
        )


def test_registry_update_rejects_known_stale_qa_promptfoo_config() -> None:
    module = _load_module()
    stale_result = (
        REPO_ROOT
        / "benchmarks"
        / "results"
        / "qa-pass-gemini35flashlite-2026-07-21.json"
    )

    with pytest.raises(
        ValueError,
        match=r"result config\.defaultTest does not match current task",
    ):
        module.update_registry([stale_result], dry_run=True)


@pytest.mark.parametrize(
    ("mutation", "error"),
    [
        ("provider", r"config\.providers do not match current task selection"),
        ("prompt", r"rendered prompt does not match current task"),
        ("rubric", r"config\.tests do not match current task"),
        ("grader", r"config\.defaultTest does not match current task"),
    ],
)
def test_current_task_contract_rejects_semantic_provenance_mutations(
    tmp_path: Path,
    mutation: str,
    error: str,
) -> None:
    module = _load_module()
    cases = [{"case": "first"}, {"case": "second"}]
    task_path, task = _write_contract_task(tmp_path, "qa-pass", cases)
    payload = _result_payload_with_current_contract(
        [_result_entry(case_vars=case) for case in cases],
        task,
    )
    if mutation == "provider":
        payload["config"]["providers"][0]["config"]["maxOutputTokens"] = 4096
    elif mutation == "prompt":
        payload["results"]["results"][0]["prompt"]["raw"] += " stale"
    elif mutation == "rubric":
        payload["config"]["tests"][0]["assert"][0]["value"] = "Old rubric"
    else:
        payload["config"]["defaultTest"]["options"]["provider"] = (
            "openai:gpt-4.1-mini"
        )

    with pytest.raises(ValueError, match=error):
        module.validate_result_task_contract(
            task_path,
            payload["config"],
            payload["results"]["results"],
            payload["results"]["prompts"],
            repo_root=tmp_path,
        )


def test_current_task_contract_rejects_unconfigured_selected_provider(
    tmp_path: Path,
) -> None:
    module = _load_module()
    cases = [{"case": "first"}, {"case": "second"}]
    task_path, task = _write_contract_task(tmp_path, "qa-pass", cases)
    payload = _result_payload_with_current_contract(
        [_result_entry(case_vars=case) for case in cases],
        task,
    )
    payload["config"]["providers"] = json.loads(json.dumps(task["providers"]))
    for row in payload["results"]["results"]:
        row["provider"] = {
            "id": "google:gemini-3.5-flash-lite",
            "label": "Gemini 3.5 Flash-Lite",
        }
        row["response"]["raw"]["modelVersion"] = "gemini-3.5-flash-lite"

    with pytest.raises(
        ValueError,
        match="result rows contain a provider outside the current task",
    ):
        module.validate_result_task_contract(
            task_path,
            payload["config"],
            payload["results"]["results"],
            payload["results"]["prompts"],
            repo_root=tmp_path,
        )


@pytest.mark.parametrize(
    ("provider", "returned_model"),
    [
        (
            {
                "id": "openai:gpt-5.5",
                "label": "GPT-5.5",
                "config": {"max_tokens": 4096},
            },
            "gpt-4o-mini",
        ),
        (
            {
                "id": "file://../providers/openai_responses_provider.py",
                "label": "GPT-5.5 Pro",
                "config": {"model": "gpt-5.5-pro", "max_tokens": 12000},
            },
            "gpt-4o-mini",
        ),
        (
            {
                "id": "anthropic:messages:claude-opus-4-6",
                "label": "Claude Opus 4.6",
                "config": {"max_tokens": 4096},
            },
            "claude-haiku-4-5-20251001",
        ),
        (
            {
                "id": "anthropic:messages:claude-sonnet-4-6",
                "label": "Claude Sonnet 4.6",
                "config": {"max_tokens": 4096},
            },
            "claude-sonnet-4-6-20260701",
        ),
    ],
)
def test_registry_contract_rejects_provider_model_substitution(
    tmp_path: Path,
    provider: dict,
    returned_model: str,
) -> None:
    module = _load_module()
    task_path, payload = _identity_contract_payload(
        tmp_path,
        provider=provider,
        returned_model=returned_model,
    )

    with pytest.raises(ValueError, match="response model does not match requested"):
        module.validate_result_task_contract(
            task_path,
            payload["config"],
            payload["results"]["results"],
            payload["results"]["prompts"],
            repo_root=tmp_path,
        )


@pytest.mark.parametrize("missing", ("id", "model"))
def test_registry_contract_requires_non_gemini_provider_owned_identity(
    tmp_path: Path,
    missing: str,
) -> None:
    module = _load_module()
    provider = {
        "id": "openai:gpt-5.5",
        "label": "GPT-5.5",
        "config": {"max_tokens": 4096},
    }
    task_path, payload = _identity_contract_payload(
        tmp_path,
        provider=provider,
        returned_model="gpt-5.5",
    )
    del payload["results"]["results"][0]["response"]["raw"][missing]

    with pytest.raises(ValueError, match="must be a non-empty string"):
        module.validate_result_task_contract(
            task_path,
            payload["config"],
            payload["results"]["results"],
            payload["results"]["prompts"],
            repo_root=tmp_path,
        )


@pytest.mark.parametrize(
    ("provider", "returned_model"),
    [
        (
            {
                "id": "openai:gpt-5.5",
                "label": "GPT-5.5",
                "config": {"max_tokens": 4096},
            },
            "gpt-5.5-2026-04-23",
        ),
        (
            {
                "id": "anthropic:messages:claude-sonnet-4-5",
                "label": "Claude Sonnet 4.5",
                "config": {"max_tokens": 4096},
            },
            "claude-sonnet-4-5-20250929",
        ),
    ],
)
def test_registry_contract_accepts_exact_same_base_dated_snapshot(
    tmp_path: Path,
    provider: dict,
    returned_model: str,
) -> None:
    module = _load_module()
    task_path, payload = _identity_contract_payload(
        tmp_path,
        provider=provider,
        returned_model=returned_model,
    )

    module.validate_result_task_contract(
        task_path,
        payload["config"],
        payload["results"]["results"],
        payload["results"]["prompts"],
        repo_root=tmp_path,
    )


def test_registry_contract_accepts_visual_requested_model_alias_metadata(
    tmp_path: Path,
) -> None:
    module = _load_module()
    provider = {
        "id": "file://../providers/video_understanding_provider.py",
        "label": "OpenAI Analysis",
        "config": {"provider": "openai", "model": "gpt-5.4"},
    }
    task_path, payload = _identity_contract_payload(
        tmp_path,
        provider=provider,
        returned_model="gpt-5.4-2026-03-05",
    )
    response = payload["results"]["results"][0]["response"]
    response["metadata"] = {
        "provider": "openai",
        "model": "gpt-5.4",
        "requested_model": "gpt-5.4",
        "returned_model": "gpt-5.4-2026-03-05",
        "request_id": "provider-call-123",
    }

    module.validate_result_task_contract(
        task_path,
        payload["config"],
        payload["results"]["results"],
        payload["results"]["prompts"],
        repo_root=tmp_path,
    )

    response["metadata"]["model"] = "gpt-4o-mini"
    with pytest.raises(ValueError, match="metadata.model"):
        module.validate_result_task_contract(
            task_path,
            payload["config"],
            payload["results"]["results"],
            payload["results"]["prompts"],
            repo_root=tmp_path,
        )


def test_registry_update_rejects_duplicate_qa_first_case_in_place_of_second(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_module()
    first = {"test_key": "good_scene", "golden_path": "golden/qa-pass.json"}
    second = {"test_key": "bad_scene", "golden_path": "golden/qa-pass.json"}
    _write_task(tmp_path, "qa-pass", [first, second])
    result_path = tmp_path / "benchmarks" / "results" / "qa-pass-run.json"
    result_path.parent.mkdir(parents=True)
    result_path.write_text(
        json.dumps(
            {
                "results": {
                    "results": [
                        _result_entry(case_vars=first),
                        _result_entry(case_vars=first),
                    ]
                }
            }
        )
    )
    registry_path = tmp_path / "registry.yaml"
    registry_path.write_text("evals: []\n")
    monkeypatch.setattr(module, "REGISTRY_PATH", registry_path)
    monkeypatch.setattr(module, "REPO_ROOT", tmp_path)

    with pytest.raises(
        ValueError,
        match=(
            r"result case matrix mismatch for Gemini 3\.6 Flash: "
            r"missing=1, duplicate=1, extra=0"
        ),
    ):
        module.update_registry([result_path], dry_run=True)


@pytest.mark.parametrize(
    ("observed_cases", "error"),
    [
        ([{"case": "first"}], r"missing=1, duplicate=0, extra=0"),
        (
            [{"case": "first"}, {"case": "second"}, {"case": "extra"}],
            r"missing=0, duplicate=0, extra=1",
        ),
    ],
)
def test_task_matrix_rejects_missing_and_extra_cases(
    tmp_path: Path,
    observed_cases: list[dict],
    error: str,
) -> None:
    module = _load_module()
    task_path = _write_task(
        tmp_path,
        "qa-pass",
        [{"case": "first"}, {"case": "second"}],
    )

    with pytest.raises(ValueError, match=error):
        module.validate_result_task_matrix(
            task_path,
            [_result_entry(case_vars=case) for case in observed_cases],
            repo_root=tmp_path,
        )


def test_task_matrix_rejects_untrusted_task_path_and_row_vars_disagreement(
    tmp_path: Path,
) -> None:
    module = _load_module()
    outside = tmp_path / "outside.yaml"
    outside.write_text(json.dumps({"tests": [{"vars": {"case": "first"}}]}))
    row = _result_entry(case_vars={"case": "first"})

    with pytest.raises(ValueError, match="existing file in benchmarks/tasks"):
        module.validate_result_task_matrix(outside, [row], repo_root=tmp_path)

    task_path = _write_task(tmp_path, "qa-pass", [{"case": "first"}])
    row["testCase"]["vars"] = {"case": "relabeled"}
    with pytest.raises(ValueError, match="vars disagree with testCase.vars"):
        module.validate_result_task_matrix(task_path, [row], repo_root=tmp_path)


def test_task_matrix_rejects_non_json_case_identity_shape(tmp_path: Path) -> None:
    module = _load_module()
    task_path = _write_task(tmp_path, "qa-pass", [{"case": {"name": "first"}}])
    row = _result_entry(case_vars={"case": {1: "first"}})

    with pytest.raises(ValueError, match="keys must be non-empty strings"):
        module.validate_result_task_matrix(task_path, [row], repo_root=tmp_path)


def test_task_matrix_rejects_duplicate_yaml_keys(tmp_path: Path) -> None:
    module = _load_module()
    task_path = tmp_path / "benchmarks" / "tasks" / "qa-pass.yaml"
    task_path.parent.mkdir(parents=True)
    task_path.write_text(
        "tests:\n"
        "  - vars:\n"
        "      case: first\n"
        "      case: silently-replaced\n"
    )

    with pytest.raises(ValueError, match="task YAML contains duplicate key 'case'"):
        module.validate_result_task_matrix(
            task_path,
            [_result_entry(case_vars={"case": "first"})],
            repo_root=tmp_path,
        )


def test_print_only_diagnostic_does_not_require_task_case_matrix(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    module = _load_module()
    row = _result_entry()
    row.pop("vars")
    row.pop("testCase")
    result_path = tmp_path / "config-detection-partial-diagnostic.json"
    result_path.write_text(json.dumps({"results": {"results": [row]}}))

    module.print_report([result_path])

    assert "Gemini 3.6 Flash" in capsys.readouterr().out

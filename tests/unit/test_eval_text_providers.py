"""Mocked transport contracts for text benchmark providers and env wrapper."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def anthropic_provider():
    return _load(
        REPO_ROOT / "benchmarks/providers/anthropic_messages_provider.py",
        "anthropic_messages_provider_contract",
    )


@pytest.fixture
def openai_provider():
    return _load(
        REPO_ROOT / "benchmarks/providers/openai_responses_provider.py",
        "openai_responses_provider_contract",
    )


@pytest.fixture
def script_bible_runtime_provider():
    return _load(
        REPO_ROOT / "benchmarks/providers/script_bible_runtime_provider.py",
        "script_bible_runtime_provider_contract",
    )


def test_anthropic_provider_preserves_request_and_usage_contract(
    anthropic_provider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = {}

    def fake_call(prompt: str, **kwargs):
        seen["prompt"] = prompt
        seen["kwargs"] = kwargs
        return "{\"ok\":true}", {
            "returned_model": "claude-sonnet-4-6",
            "input_tokens": 100,
            "output_tokens": 25,
            "estimated_cost_usd": 0.0012,
            "latency_seconds": 1.25,
            "request_id": "req-1",
            "finish_reason": "end_turn",
        }

    monkeypatch.setattr(anthropic_provider, "call_llm", fake_call)

    result = anthropic_provider.call_api(
        "Inspect source",
        {
            "config": {
                "model": "claude-sonnet-4-6",
                "max_tokens": 8192,
                "temperature": 0.2,
                "max_retries": 2,
                "timeout": 2500,
            }
        },
        {},
    )

    assert seen == {
        "prompt": "Inspect source",
        "kwargs": {
            "model": "claude-sonnet-4-6",
            "max_tokens": 8192,
            "temperature": 0.2,
            "max_retries": 2,
            "request_timeout_seconds": 2.5,
        },
    }
    assert result["output"] == '{"ok":true}'
    assert result["tokenUsage"] == {"total": 125, "prompt": 100, "completion": 25}
    assert result["cost"] == 0.0012
    assert result["latencyMs"] == 1250
    assert result["metadata"]["request_id"] == "req-1"
    assert result["metadata"]["requested_model"] == "claude-sonnet-4-6"
    assert result["metadata"]["returned_model"] == "claude-sonnet-4-6"
    assert result["raw"]["model"] == "claude-sonnet-4-6"
    assert result["raw"]["id"] == "req-1"


def test_script_bible_runtime_provider_uses_exact_prompt_and_schema(
    script_bible_runtime_provider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen = {}

    def fake_call(**kwargs):
        seen.update(kwargs)
        return script_bible_runtime_provider.ScriptBible(
            title="Open Frequency",
            logline="A radio team helps its town.",
            synopsis="The team stays on air and helps reunite a missing dog.",
            act_structure=[
                {
                    "act_number": 1,
                    "title": "Broadcast",
                    "start_scene": "INT. COMMUNITY RADIO STUDIO - NIGHT",
                    "end_scene": "INT. COMMUNITY RADIO STUDIO - MORNING",
                    "summary": "The team keeps broadcasting.",
                    "turning_points": ["Comet returns."],
                }
            ],
            themes=[
                {
                    "theme": "Service",
                    "description": "The station serves its community.",
                    "evidence": ["Maya's plea and Comet's return."],
                }
            ],
            narrative_arc="A worried plea resolves in communal relief.",
            genre="Drama",
            tone="Hopeful",
            protagonist_journey="The ensemble recommits to service.",
            central_conflict="Keeping the community connected.",
            setting_overview="A community radio station.",
            confidence=0.9,
        ), {
            "returned_model": "gemini-3.5-flash-lite",
            "input_tokens": 100,
            "output_tokens": 50,
            "estimated_cost_usd": 0.00175,
            "latency_seconds": 1.5,
            "request_id": "gemini-runtime",
            "finish_reason": "end_turn",
        }

    monkeypatch.setattr(script_bible_runtime_provider, "call_llm", fake_call)
    result = script_bible_runtime_provider.call_api(
        "marker",
        {
            "config": {
                "model": "gemini-3.5-flash-lite",
                "max_tokens": 65536,
                "max_retries": 1,
            }
        },
        {"vars": {"screenplay": "INT. STUDIO - NIGHT\nARIA broadcasts."}},
    )

    assert seen["prompt"] == script_bible_runtime_provider.EXTRACTION_PROMPT.format(
        script_text="INT. STUDIO - NIGHT\nARIA broadcasts."
    )
    assert seen["model"] == "gemini-3.5-flash-lite"
    assert seen["response_schema"] is script_bible_runtime_provider.ScriptBible
    assert seen["fail_on_truncation"] is True
    assert seen["thinking_level"] == "minimal"
    assert result["metadata"]["requested_model"] == "gemini-3.5-flash-lite"
    assert result["metadata"]["returned_model"] == "gemini-3.5-flash-lite"
    assert result["metadata"]["runtime_prompt"] == "script_bible_v1.EXTRACTION_PROMPT"
    assert result["metadata"]["runtime_schema"] == "cine_forge.schemas.ScriptBible"
    assert result["raw"]["id"] == "gemini-runtime"


def test_script_bible_runtime_provider_enforces_opus_5_schema(
    script_bible_runtime_provider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bible = script_bible_runtime_provider.ScriptBible(
        title="Open Frequency",
        logline="A radio team helps its town.",
        synopsis="The team stays on air and helps reunite a missing dog.",
        act_structure=[
            {
                "act_number": 1,
                "title": "Broadcast",
                "start_scene": "INT. COMMUNITY RADIO STUDIO - NIGHT",
                "end_scene": "INT. COMMUNITY RADIO STUDIO - MORNING",
                "summary": "The team keeps broadcasting.",
                "turning_points": ["Comet returns."],
            }
        ],
        themes=[
            {
                "theme": "Service",
                "description": "The station serves its community.",
                "evidence": ["Maya's plea and Comet's return."],
            }
        ],
        narrative_arc="A worried plea resolves in communal relief.",
        genre="Drama",
        tone="Hopeful",
        protagonist_journey="The ensemble recommits to service.",
        central_conflict="Keeping the community connected.",
        setting_overview="A community radio station.",
        confidence=0.9,
    )
    seen = {}

    def fake_request(payload: dict, *, timeout_seconds: float):
        seen.update(payload=payload, timeout_seconds=timeout_seconds)
        return {
            "id": "msg-opus5",
            "model": "claude-opus-5",
            "stop_reason": "end_turn",
            "content": [{"type": "text", "text": bible.model_dump_json()}],
            "usage": {"input_tokens": 100, "output_tokens": 50},
        }

    monkeypatch.setattr(script_bible_runtime_provider, "_request_json", fake_request)
    output, metadata = script_bible_runtime_provider._call_opus_5(
        prompt="SCREENPLAY:\nsource",
        max_tokens=200_000,
        timeout_seconds=12,
    )

    assert output == bible
    assert seen["payload"]["model"] == "claude-opus-5"
    assert seen["payload"]["max_tokens"] == 128_000
    assert "temperature" not in seen["payload"]
    schema = seen["payload"]["output_config"]["format"]["schema"]
    assert "'minimum':" not in str(schema)
    assert "'maximum':" not in str(schema)
    assert "minimum: 0.0" in schema["properties"]["confidence"]["description"]
    assert metadata["requested_model"] == "claude-opus-5"
    assert metadata["returned_model"] == "claude-opus-5"
    assert metadata["estimated_cost_usd"] == 0.00175


def test_anthropic_provider_reports_empty_or_failed_transport_as_error(
    anthropic_provider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        anthropic_provider,
        "call_llm",
        lambda *_args, **_kwargs: (
            "",
            {
                "latency_seconds": 0.1,
                "returned_model": "claude-opus-4-8",
                "request_id": "msg-empty",
            },
        ),
    )
    empty = anthropic_provider.call_api(
        "prompt",
        {"config": {"model": "claude-opus-4-8"}},
        {},
    )
    assert empty["output"] == ""
    assert "no output" in empty["error"].lower()
    assert empty["latencyMs"] >= 0

    def fail(*_args, **_kwargs):
        raise RuntimeError("provider unavailable")

    monkeypatch.setattr(anthropic_provider, "call_llm", fail)
    failed = anthropic_provider.call_api(
        "prompt",
        {"config": {"model": "claude-opus-4-8"}},
        {},
    )
    assert failed["output"] == ""
    assert failed["error"] == "provider unavailable"
    assert failed["latencyMs"] >= 0


@pytest.mark.parametrize(
    ("config", "expected"),
    [
        ({"timeout": 500}, 0.5),
        ({"timeout": 1000}, 1.0),
        ({"timeout": 300000}, 300.0),
        ({"request_timeout_seconds": 12}, 12.0),
        ({"timeout": "bad"}, 600.0),
    ],
)
def test_text_provider_timeout_units_are_explicit(
    anthropic_provider,
    openai_provider,
    config: dict,
    expected: float,
) -> None:
    assert anthropic_provider._timeout_seconds(config) == expected
    assert openai_provider._timeout_seconds(config) == expected


def test_openai_provider_retries_only_without_rejected_temperature(
    openai_provider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payloads = []

    def fake_request(payload: dict, *, timeout_seconds: float):
        payloads.append((payload, timeout_seconds))
        if len(payloads) == 1:
            raise RuntimeError("Unsupported parameter: temperature")
        return {
            "id": "resp-1",
            "model": "gpt-5.5-pro",
            "status": "completed",
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": '{"ok":true}'}],
                }
            ],
            "usage": {
                "input_tokens": 200,
                "output_tokens": 50,
                "total_tokens": 250,
                "output_tokens_details": {"reasoning_tokens": 20},
            },
        }

    monkeypatch.setattr(openai_provider, "_request_json", fake_request)
    monkeypatch.setattr(openai_provider, "estimate_cost_usd", lambda *_args: 0.004)

    result = openai_provider.call_api(
        "Inspect source",
        {
            "config": {
                "model": "gpt-5.5-pro",
                "max_tokens": 4096,
                "temperature": 0,
                "timeout": 300000,
                "response_format": {"type": "json_object"},
            }
        },
        {},
    )

    assert len(payloads) == 2
    assert payloads[0][0]["temperature"] == 0.0
    assert "temperature" not in payloads[1][0]
    assert payloads[1][0]["max_output_tokens"] == 12000
    assert payloads[1][0]["text"] == {"format": {"type": "json_object"}}
    assert payloads[1][1] == 300.0
    assert result["output"] == '{"ok":true}'
    assert result["tokenUsage"]["completionDetails"]["reasoning"] == 20
    assert result["cost"] == 0.004
    assert result["metadata"]["requested_model"] == "gpt-5.5-pro"
    assert result["metadata"]["returned_model"] == "gpt-5.5-pro"
    assert result["raw"]["model"] == "gpt-5.5-pro"
    assert result["raw"]["id"] == "resp-1"


def test_openai_provider_fails_closed_on_completed_response_without_text(
    openai_provider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        openai_provider,
        "_request_json",
        lambda *_args, **_kwargs: {
            "id": "resp-empty",
            "model": "gpt-5.5-pro",
            "status": "completed",
            "output": [],
            "usage": {"input_tokens": 10, "output_tokens": 0},
        },
    )

    result = openai_provider.call_api(
        "prompt",
        {"config": {"model": "gpt-5.5-pro"}},
        {},
    )

    assert result["output"] == ""
    assert "no output_text" in result["error"]
    assert result["metadata"]["request_id"] == "resp-empty"


@pytest.mark.parametrize("missing", ["model", "id"])
def test_openai_provider_rejects_missing_returned_identity(
    openai_provider,
    monkeypatch: pytest.MonkeyPatch,
    missing: str,
) -> None:
    response = {
        "id": "resp-identity",
        "model": "gpt-5.5-pro",
        "status": "completed",
        "output_text": "ok",
        "usage": {"input_tokens": 1, "output_tokens": 1},
    }
    response.pop(missing)
    monkeypatch.setattr(openai_provider, "_request_json", lambda *_a, **_k: response)

    result = openai_provider.call_api(
        "prompt",
        {"config": {"model": "gpt-5.5-pro"}},
        {},
    )

    assert result["output"] == ""
    assert "must be a non-empty string" in result["error"]


def test_text_providers_reject_returned_model_substitution(
    anthropic_provider,
    openai_provider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        openai_provider,
        "_request_json",
        lambda *_a, **_k: {
            "id": "resp-substitute",
            "model": "gpt-4o-mini",
            "status": "completed",
            "output_text": "ok",
            "usage": {"input_tokens": 1, "output_tokens": 1},
        },
    )
    openai = openai_provider.call_api(
        "prompt",
        {"config": {"model": "gpt-5.5-pro"}},
        {},
    )
    assert "does not match requested model" in openai["error"]

    monkeypatch.setattr(
        anthropic_provider,
        "call_llm",
        lambda *_a, **_k: (
            "ok",
            {
                "returned_model": "claude-haiku-4-5-20251001",
                "request_id": "msg-substitute",
            },
        ),
    )
    anthropic = anthropic_provider.call_api(
        "prompt",
        {"config": {"model": "claude-opus-4-8"}},
        {},
    )
    assert "does not match requested model" in anthropic["error"]


@pytest.mark.parametrize("provider_fixture", ["anthropic_provider", "openai_provider"])
def test_text_providers_require_explicit_configured_model(
    provider_fixture: str,
    request: pytest.FixtureRequest,
) -> None:
    provider = request.getfixturevalue(provider_fixture)

    result = provider.call_api("prompt", {"config": {}}, {})

    assert result["output"] == ""
    assert "config.model is required" in result["error"]


def test_all_openai_responses_task_blocks_declare_the_requested_model() -> None:
    matched = 0
    for task_path in sorted((REPO_ROOT / "benchmarks/tasks").glob("*.yaml")):
        task = yaml.safe_load(task_path.read_text(encoding="utf-8"))
        for provider in task.get("providers", []):
            if provider.get("id") != "file://../providers/openai_responses_provider.py":
                continue
            matched += 1
            assert provider.get("label") == "GPT-5.5 Pro"
            assert provider.get("config", {}).get("model") == "gpt-5.5-pro"
    assert matched == 12


def test_provider_env_wrapper_passes_hydrated_environment_to_child(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    wrapper = _load(
        REPO_ROOT / "scripts/with_cine_forge_provider_env.py",
        "with_cine_forge_provider_env_contract",
    )
    seen = {}

    def fake_load(_root: Path):
        monkeypatch.setenv("OPENAI_API_KEY", "hydrated-key")

    def fake_exec(file: str, args: list[str], env: dict[str, str]):
        seen.update(file=file, args=args, key=env.get("OPENAI_API_KEY"))

    monkeypatch.setattr(wrapper, "load_cine_forge_dotenv", fake_load)
    monkeypatch.setattr(wrapper.os, "execvpe", fake_exec)
    monkeypatch.setattr(sys, "argv", ["wrapper", "tool", "--flag"])

    wrapper.main()

    assert seen == {"file": "tool", "args": ["tool", "--flag"], "key": "hydrated-key"}

"""Focused OpenRouter contract tests for the exact-runtime script-bible lane."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[2]


def _load_provider():
    path = REPO_ROOT / "benchmarks/providers/script_bible_runtime_provider.py"
    spec = importlib.util.spec_from_file_location(
        "openrouter_script_bible_provider_contract", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def provider():
    return _load_provider()


def _bible(provider):
    return provider.ScriptBible(
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
                "evidence": ["Maya's plea.", "Comet returns."],
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


def test_qwen38_openrouter_enforces_schema_provider_and_usage(
    provider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bible = _bible(provider)
    seen = {}

    def fake_request(payload: dict, *, timeout_seconds: float):
        seen.update(payload=payload, timeout_seconds=timeout_seconds)
        return {
            "id": "gen-qwen38",
            "model": "qwen/qwen3.8-max",
            "provider": "Alibaba",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": bible.model_dump_json()},
                }
            ],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 60,
                "total_tokens": 160,
                "cost": 0.00056,
                "completion_tokens_details": {"reasoning_tokens": 40},
            },
        }

    monkeypatch.setattr(provider, "_request_openrouter_json", fake_request)
    result = provider.call_api(
        "marker",
        {
            "config": {
                "model": "qwen/qwen3.8-max",
                "provider": "openrouter",
                "max_tokens": 65536,
                "request_timeout_seconds": 12,
                "reasoning_effort": "low",
            }
        },
        {"vars": {"screenplay": "INT. STUDIO - NIGHT\nARIA broadcasts."}},
    )

    payload = seen["payload"]
    assert payload["model"] == "qwen/qwen3.8-max"
    assert payload["reasoning"] == {"effort": "low", "exclude": True}
    assert payload["provider"] == {
        "order": ["Alibaba"],
        "allow_fallbacks": False,
        "require_parameters": True,
        "data_collection": "deny",
    }
    assert payload["response_format"]["type"] == "json_schema"
    assert payload["response_format"]["json_schema"]["strict"] is True
    assert "temperature" not in payload
    assert result["output"] == bible.model_dump_json()
    assert result["tokenUsage"] == {"total": 160, "prompt": 100, "completion": 60}
    assert result["cost"] == 0.00056
    assert result["metadata"]["provider"] == "openrouter"
    assert result["metadata"]["upstream_provider"] == "Alibaba"
    assert result["metadata"]["cost_estimated"] is False
    assert result["metadata"]["allow_fallbacks"] is False
    assert result["raw"]["provider"] == "Alibaba"
    assert result["raw"]["usage"]["completion_tokens_details"] == {
        "reasoning_tokens": 40
    }


def test_qwen38_openrouter_rejects_unpinned_provider(
    provider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bible = _bible(provider)
    monkeypatch.setattr(
        provider,
        "_request_openrouter_json",
        lambda *_args, **_kwargs: {
            "id": "gen-fallback",
            "model": "qwen/qwen3.8-max",
            "provider": "Unexpected Provider",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"content": bible.model_dump_json()},
                }
            ],
            "usage": {
                "prompt_tokens": 1,
                "completion_tokens": 1,
                "total_tokens": 2,
                "cost": 0.00001,
            },
        },
    )

    result = provider.call_api(
        "marker",
        {"config": {"model": "qwen/qwen3.8-max"}},
        {"vars": {"screenplay": "synthetic"}},
    )

    assert result["output"] == ""
    assert "does not match pinned provider" in result["error"]


def test_deepseek_v4_flash_openrouter_enforces_zdr_schema_and_usage(
    provider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bible = _bible(provider)
    seen = {}

    def fake_request(payload: dict, *, timeout_seconds: float):
        seen.update(payload=payload, timeout_seconds=timeout_seconds)
        return {
            "id": "gen-deepseek-v4-flash",
            "model": "deepseek/deepseek-v4-flash-0731",
            "provider": "Phala",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": bible.model_dump_json()},
                }
            ],
            "usage": {
                "prompt_tokens": 120,
                "completion_tokens": 80,
                "total_tokens": 200,
                "cost": 0.000056,
                "completion_tokens_details": {"reasoning_tokens": 30},
            },
        }

    monkeypatch.setattr(provider, "_request_openrouter_json", fake_request)
    result = provider.call_api(
        "marker",
        {
            "config": {
                "model": "deepseek/deepseek-v4-flash-0731",
                "provider": "openrouter",
                "max_tokens": 65536,
                "request_timeout_seconds": 12,
                "reasoning_effort": "low",
            }
        },
        {"vars": {"screenplay": "INT. STUDIO - NIGHT\nARIA broadcasts."}},
    )

    payload = seen["payload"]
    assert payload["model"] == "deepseek/deepseek-v4-flash-0731"
    assert payload["reasoning"] == {"effort": "low", "exclude": True}
    assert payload["provider"] == {
        "order": ["Phala"],
        "allow_fallbacks": False,
        "require_parameters": True,
        "data_collection": "deny",
        "zdr": True,
    }
    assert payload["response_format"]["type"] == "json_schema"
    assert payload["response_format"]["json_schema"]["strict"] is True
    assert result["output"] == bible.model_dump_json()
    assert result["tokenUsage"] == {"total": 200, "prompt": 120, "completion": 80}
    assert result["cost"] == 0.000056
    assert result["metadata"]["provider"] == "openrouter"
    assert result["metadata"]["returned_model"] == (
        "deepseek/deepseek-v4-flash-0731"
    )
    assert result["metadata"]["upstream_provider"] == "Phala"
    assert result["metadata"]["data_collection"] == "deny"
    assert result["metadata"]["zdr"] is True
    assert result["raw"]["provider"] == "Phala"


def test_deepseek_v4_pro_openrouter_enforces_zdr_schema_and_usage(
    provider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bible = _bible(provider)
    seen = {}

    def fake_request(payload: dict, *, timeout_seconds: float):
        seen.update(payload=payload, timeout_seconds=timeout_seconds)
        return {
            "id": "gen-deepseek-v4-pro",
            "model": "deepseek/deepseek-v4-pro",
            "provider": "Baidu",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": bible.model_dump_json()},
                }
            ],
            "usage": {
                "prompt_tokens": 120,
                "completion_tokens": 80,
                "total_tokens": 200,
                "cost": 0.0006,
                "completion_tokens_details": {"reasoning_tokens": 30},
            },
        }

    monkeypatch.setattr(provider, "_request_openrouter_json", fake_request)
    result = provider.call_api(
        "marker",
        {
            "config": {
                "model": "deepseek/deepseek-v4-pro",
                "provider": "openrouter",
                "max_tokens": 65536,
                "request_timeout_seconds": 12,
                "reasoning_effort": "low",
            }
        },
        {"vars": {"screenplay": "INT. STUDIO - NIGHT\nARIA broadcasts."}},
    )

    payload = seen["payload"]
    assert payload["model"] == "deepseek/deepseek-v4-pro"
    assert payload["reasoning"] == {"effort": "low", "exclude": True}
    assert payload["provider"] == {
        "order": ["Baidu"],
        "allow_fallbacks": False,
        "require_parameters": True,
        "data_collection": "deny",
    }
    assert payload["response_format"]["type"] == "json_schema"
    assert payload["response_format"]["json_schema"]["strict"] is True
    assert result["output"] == bible.model_dump_json()
    assert result["metadata"]["returned_model"] == "deepseek/deepseek-v4-pro"
    assert result["metadata"]["upstream_provider"] == "Baidu"
    assert result["metadata"]["data_collection"] == "deny"
    assert result["metadata"]["zdr"] is False
    assert result["raw"]["provider"] == "Baidu"


def test_ox_alpha_openrouter_keeps_schema_without_privacy_or_provider_pin(
    provider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bible = _bible(provider)
    seen = {}

    def fake_request(payload: dict, *, timeout_seconds: float):
        seen.update(payload=payload, timeout_seconds=timeout_seconds)
        return {
            "id": "gen-ox-alpha",
            "model": "stealth/ox-alpha",
            "provider": "Stealth",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": bible.model_dump_json()},
                }
            ],
            "usage": {
                "prompt_tokens": 120,
                "completion_tokens": 80,
                "total_tokens": 200,
                "cost": 0.0,
                "completion_tokens_details": {"reasoning_tokens": 30},
            },
        }

    monkeypatch.setattr(provider, "_request_openrouter_json", fake_request)
    result = provider.call_api(
        "marker",
        {
            "config": {
                "model": "stealth/ox-alpha",
                "provider": "openrouter",
                "max_tokens": 65536,
                "request_timeout_seconds": 12,
                "reasoning_effort": "low",
            }
        },
        {"vars": {"screenplay": "INT. STUDIO - NIGHT\nARIA broadcasts."}},
    )

    payload = seen["payload"]
    assert payload["model"] == "stealth/ox-alpha"
    assert "models" not in payload
    assert payload["reasoning"] == {"effort": "low", "exclude": True}
    assert payload["provider"] == {"require_parameters": True}
    assert payload["response_format"]["type"] == "json_schema"
    assert payload["response_format"]["json_schema"]["strict"] is True
    assert "temperature" not in payload
    assert result["output"] == bible.model_dump_json()
    assert result["cost"] == 0.0
    assert result["metadata"]["returned_model"] == "stealth/ox-alpha"
    assert result["metadata"]["upstream_provider"] == "Stealth"
    assert result["metadata"]["allow_fallbacks"] is None
    assert result["metadata"]["data_collection"] is None
    assert result["metadata"]["zdr"] is False


def test_hy4_preview_openrouter_enforces_schema_without_route_pin(
    provider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bible = _bible(provider)
    seen = {}

    def fake_request(payload: dict, *, timeout_seconds: float):
        seen.update(payload=payload, timeout_seconds=timeout_seconds)
        return {
            "id": "gen-hy4-preview",
            "model": "tencent/hy4-preview",
            "provider": "Tencent",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": bible.model_dump_json()},
                }
            ],
            "usage": {
                "prompt_tokens": 120,
                "completion_tokens": 80,
                "total_tokens": 200,
                "cost": 0.00030016,
                "completion_tokens_details": {"reasoning_tokens": 30},
            },
        }

    monkeypatch.setattr(provider, "_request_openrouter_json", fake_request)
    result = provider.call_api(
        "marker",
        {
            "config": {
                "model": "tencent/hy4-preview",
                "provider": "openrouter",
                "max_tokens": 65536,
                "request_timeout_seconds": 12,
                "reasoning_effort": "low",
            }
        },
        {"vars": {"screenplay": "INT. STUDIO - NIGHT\nARIA broadcasts."}},
    )

    payload = seen["payload"]
    assert payload["model"] == "tencent/hy4-preview"
    assert "models" not in payload
    assert payload["max_tokens"] == 64000
    assert payload["reasoning"] == {"effort": "low", "exclude": True}
    assert payload["provider"] == {"require_parameters": True}
    assert payload["response_format"]["type"] == "json_schema"
    assert payload["response_format"]["json_schema"]["strict"] is True
    assert "temperature" not in payload
    assert result["output"] == bible.model_dump_json()
    assert result["cost"] == 0.00030016
    assert result["metadata"]["returned_model"] == "tencent/hy4-preview"
    assert result["metadata"]["upstream_provider"] == "Tencent"
    assert result["metadata"]["allow_fallbacks"] is None
    assert result["metadata"]["data_collection"] is None
    assert result["metadata"]["zdr"] is False


def test_ox_alpha_diagnostic_can_relax_only_parameter_enforcement(
    provider,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bible = _bible(provider)
    seen = {}

    def fake_request(payload: dict, *, timeout_seconds: float):
        seen.update(payload=payload, timeout_seconds=timeout_seconds)
        return {
            "id": "gen-ox-alpha-diagnostic",
            "model": "stealth/ox-alpha",
            "provider": "Stealth",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": bible.model_dump_json()},
                }
            ],
            "usage": {
                "prompt_tokens": 120,
                "completion_tokens": 80,
                "total_tokens": 200,
                "cost": 0.0,
            },
        }

    monkeypatch.setattr(provider, "_request_openrouter_json", fake_request)
    result = provider.call_api(
        "marker",
        {
            "config": {
                "model": "stealth/ox-alpha",
                "provider": "openrouter",
                "max_tokens": 65536,
                "request_timeout_seconds": 12,
                "reasoning_effort": "low",
                "require_parameters": False,
                "diagnostic_json_only": True,
            }
        },
        {"vars": {"screenplay": "INT. STUDIO - NIGHT\nARIA broadcasts."}},
    )

    assert seen["payload"]["provider"] == {}
    assert seen["payload"]["model"] == "stealth/ox-alpha"
    assert "models" not in seen["payload"]
    assert "response_format" not in seen["payload"]
    assert "DIAGNOSTIC OUTPUT CONTRACT" in seen["payload"]["messages"][0]["content"]
    assert result["metadata"]["require_parameters"] is False
    assert result["metadata"]["schema_enforcement"] == "client-only-diagnostic"
    assert result["metadata"]["returned_model"] == "stealth/ox-alpha"


def test_ox_alpha_diagnostic_strips_only_whole_response_json_fence(provider) -> None:
    payload = '{"title":"Example"}'
    assert provider._diagnostic_json_content(
        f"```json\n{payload}\n```", allow_markdown_fence=True
    ) == (payload, True)
    wrapped = f"before\n```json\n{payload}\n```"
    assert provider._diagnostic_json_content(
        wrapped, allow_markdown_fence=True
    ) == (wrapped, False)

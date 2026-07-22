from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import pytest
from pydantic import BaseModel

from cine_forge.ai.fountain_validate import normalize_fountain_text
from cine_forge.ai.llm import (
    LLMCallError,
    _breaker_state,
    _build_anthropic_payload,
    _build_gemini_payload,
    _is_circuit_breaker_open,
    _normalize_anthropic_response,
    _normalize_gemini_response,
    _parse_provider,
    _record_provider_success,
    _record_provider_transient_failure,
    _reset_circuit_breakers,
    _retry_delay_seconds,
    _to_gemini_schema,
    call_llm,
    estimate_cost_usd,
)
from cine_forge.modules.ingest.scene_breakdown_v1.main import (
    _extract_scene_deterministic,
    _split_into_scene_chunks,
)
from cine_forge.schemas import ScriptBible


class DemoSchema(BaseModel):
    value: str


class _ActionLineEntities(BaseModel):
    characters: list[str]
    props: list[str]


_ACTION_ENTITY_CASES = [
    pytest.param(
        "INT. COMMUNITY RADIO STUDIO",
        ["ARIA", "NOAH", "JUNE"],
        ["TAPE REEL", "CRACKED MIXER"],
        [],
        ["MUGS OF TEA", "STACK OF SCRIPTS", "ON AIR LIGHT", "SKYLIGHT"],
        id="studio-opening",
    ),
    pytest.param(
        "EXT. HILLTOP WATER TOWER - NIGHT",
        ["ARIA", "NOAH"],
        ["PORTABLE ANTENNA"],
        [],
        ["PRAYER FLAGS", "GUARDRAIL", "SERVICE LADDER", "HANDHELD RECEIVER"],
        id="water-tower",
    ),
    pytest.param(
        "INT. STUDIO HALLWAY - NIGHT",
        ["KELL", "JUNE", "PARAMEDIC", "ELDERLY NEIGHBOR"],
        ["HANDWRITTEN EVACUATION ARROWS", "BATTERIES", "TANGLED CABLES"],
        [],
        ["FLUORESCENT LIGHTS", "WALL", "CONTROL-ROOM DOOR"],
        id="studio-hallway",
    ),
    pytest.param(
        "INT. COMMUNITY RADIO STUDIO - CONTINUOUS",
        ["ARIA", "JUNE"],
        ["MIC"],
        ["NOAH"],
        ["MONITORS", "GAIN", "ON AIR LIGHT"],
        id="studio-continuous",
    ),
    pytest.param(
        "EXT. TOWN SQUARE - PRE-DAWN",
        [],
        ["BLANKETS", "KETTLE", "CAMP STOVE"],
        ["KELL", "ELDER WOMAN", "JUNE", "UNKNOWN VOICE"],
        ["BATTERY RADIO", "FOLDING TABLE", "SECOND RECEIVER", "TARPS"],
        id="town-square",
    ),
    pytest.param(
        "INT. COMMUNITY RADIO STUDIO - MORNING",
        ["ARIA", "NOAH", "JUNE", "KELL"],
        ["MAP", "OPEN FREQUENCY SIGN", "CASSETTE DECK"],
        [],
        ["WET COATS", "CHAIRS", "CONSOLES", "FRESH BREAD", "ON AIR LIGHT"],
        id="studio-morning",
    ),
    pytest.param(
        "EXT. NORTH SHELTER GYM - AFTERNOON",
        ["JUNE", "ARIA", "NOAH", "TEENAGER"],
        [
            "PORTABLE RECORDER",
            "WEATHER RADIO",
            "FOLDED MAP",
            "LIST OF MISSING PETS",
        ],
        ["VOLUNTEER"],
        ["COTS", "WHITEBOARD", "BLEACHERS", "RADIO DESK"],
        id="north-shelter",
    ),
    pytest.param(
        "INT. COMMUNITY RADIO STUDIO - NIGHT",
        ["KELL", "ARIA", "NOAH"],
        ["NOTEBOOK", "FINAL CARD"],
        ["JUNE", "UNKNOWN VOICE"],
        ["INDEX CARDS", "CHALKBOARD SCHEDULE", "ON AIR LIGHT"],
        id="studio-night",
    ),
]


def _production_scene_text(source_text: str, heading: str) -> str:
    for chunk in _split_into_scene_chunks(source_text):
        scene = _extract_scene_deterministic(
            chunk=chunk,
            parser_backend="fixture-test",
            parser_confident=True,
        )
        if scene["heading"] == heading:
            return "\n".join(
                element["content"]
                for element in scene["elements"]
                if element["element_type"] in {"action", "dialogue"}
            )
    raise AssertionError(f"missing source scene: {heading}")


@pytest.mark.unit
@pytest.mark.parametrize(
    (
        "heading",
        "expected_characters",
        "expected_props",
        "forbidden_characters",
        "forbidden_props",
    ),
    _ACTION_ENTITY_CASES,
)
def test_fixture_dispatcher_returns_source_grounded_action_entities(
    monkeypatch: pytest.MonkeyPatch,
    heading: str,
    expected_characters: list[str],
    expected_props: list[str],
    forbidden_characters: list[str],
    forbidden_props: list[str],
) -> None:
    fixture_root = Path(__file__).resolve().parents[1] / "fixtures" / "mvp_mock_responses"
    source_text = (fixture_root.parent / "sample_screenplay.fountain").read_text(
        encoding="utf-8"
    )
    monkeypatch.setenv("CINE_FORGE_MOCK_FIXTURE_DIR", str(fixture_root))
    scene_text = _production_scene_text(source_text, heading)

    result, metadata = call_llm(
        prompt=f"Scene heading: {heading}\n\nScene text:\n{scene_text}\n",
        model="fixture",
        response_schema=_ActionLineEntities,
    )

    assert isinstance(result, _ActionLineEntities)
    assert result.characters == expected_characters
    assert result.props == expected_props
    assert set(result.characters).isdisjoint(forbidden_characters)
    assert set(result.props).isdisjoint(forbidden_props)
    assert metadata["estimated_cost_usd"] == 0.0


@pytest.mark.unit
def test_fixture_dispatcher_returns_source_grounded_script_bible(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_root = Path(__file__).resolve().parents[1] / "fixtures" / "mvp_mock_responses"
    source_path = fixture_root.parent / "sample_screenplay.fountain"
    source_text = source_path.read_text(encoding="utf-8")
    canonical_source = normalize_fountain_text(source_text)
    monkeypatch.setenv("CINE_FORGE_MOCK_FIXTURE_DIR", str(fixture_root))

    result, metadata = call_llm(
        prompt=f"SCREENPLAY:\n{canonical_source}\n\n==========",
        model="fixture",
        response_schema=ScriptBible,
    )

    assert isinstance(result, ScriptBible)
    assert result.title == "Signal in the Rain"
    assert "Red Creek" in result.logline
    assert metadata["request_id"] == "fixture-response"
    for act in result.act_structure:
        assert act.start_scene in canonical_source
        assert act.end_scene in canonical_source
        for turning_point in act.turning_points:
            assert turning_point in canonical_source
    for theme in result.themes:
        for evidence in theme.evidence:
            assert evidence in canonical_source


@pytest.mark.unit
def test_fixture_dispatcher_rejects_script_bible_for_an_unlinked_screenplay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_root = Path(__file__).resolve().parents[1] / "fixtures" / "mvp_mock_responses"
    monkeypatch.setenv("CINE_FORGE_MOCK_FIXTURE_DIR", str(fixture_root))

    with pytest.raises(LLMCallError, match="does not match linked source"):
        call_llm(
            prompt="SCREENPLAY:\nINT. DIFFERENT STORY - DAY\nNothing from Red Creek happens.",
            model="fixture",
            response_schema=ScriptBible,
        )


@pytest.mark.unit
def test_fixture_dispatcher_rejects_script_bible_when_anchors_survive_corruption(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_root = Path(__file__).resolve().parents[1] / "fixtures" / "mvp_mock_responses"
    source_text = (fixture_root.parent / "sample_screenplay.fountain").read_text(
        encoding="utf-8"
    )
    corrupted = normalize_fountain_text(
        source_text.replace(
            "A cramped studio hums with old gear.",
            "A marble palace glows with brand-new equipment.",
        )
    )
    monkeypatch.setenv("CINE_FORGE_MOCK_FIXTURE_DIR", str(fixture_root))

    with pytest.raises(LLMCallError, match="exact canonical source content"):
        call_llm(
            prompt=f"SCREENPLAY:\n{corrupted}\n\n==========",
            model="fixture",
            response_schema=ScriptBible,
        )


@pytest.mark.unit
def test_fixture_dispatcher_rejects_script_bible_with_appended_source(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_root = Path(__file__).resolve().parents[1] / "fixtures" / "mvp_mock_responses"
    source_text = (fixture_root.parent / "sample_screenplay.fountain").read_text(
        encoding="utf-8"
    )
    canonical_source = normalize_fountain_text(source_text)
    monkeypatch.setenv("CINE_FORGE_MOCK_FIXTURE_DIR", str(fixture_root))

    with pytest.raises(LLMCallError, match="exact canonical source content"):
        call_llm(
            prompt=(
                f"SCREENPLAY:\n{canonical_source}\n\n"
                "INT. ORBITAL PALACE - NIGHT\nAn unrelated ending is appended."
                "\n\n=========="
            ),
            model="fixture",
            response_schema=ScriptBible,
        )


@pytest.mark.unit
def test_fixture_dispatcher_rejects_unlinked_action_entity_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_root = Path(__file__).resolve().parents[1] / "fixtures" / "mvp_mock_responses"
    monkeypatch.setenv("CINE_FORGE_MOCK_FIXTURE_DIR", str(fixture_root))

    with pytest.raises(LLMCallError, match="matched 0"):
        call_llm(
            prompt="Scene heading: INT. DIFFERENT STORY - DAY\nScene text: Nothing happens.",
            model="fixture",
            response_schema=_ActionLineEntities,
        )


@pytest.mark.unit
def test_fixture_dispatcher_rejects_action_entities_when_anchor_survives_corruption(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture_root = Path(__file__).resolve().parents[1] / "fixtures" / "mvp_mock_responses"
    source_text = (fixture_root.parent / "sample_screenplay.fountain").read_text(
        encoding="utf-8"
    )
    heading = "INT. COMMUNITY RADIO STUDIO"
    scene_text = _production_scene_text(source_text, heading).replace(
        "ARIA threads a tape reel",
        "ARIA destroys a tape reel",
    )
    monkeypatch.setenv("CINE_FORGE_MOCK_FIXTURE_DIR", str(fixture_root))

    with pytest.raises(LLMCallError, match="prompt section hash mismatch"):
        call_llm(
            prompt=f"Scene heading: {heading}\n\nScene text:\n{scene_text}\n",
            model="fixture",
            response_schema=_ActionLineEntities,
        )


@pytest.mark.unit
def test_fixture_dispatcher_rejects_action_entities_when_source_hash_changes(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    original_root = (
        Path(__file__).resolve().parents[1] / "fixtures" / "mvp_mock_responses"
    )
    fixture_root = tmp_path / "fixtures" / "mvp_mock_responses"
    fixture_root.mkdir(parents=True)
    for filename in (
        "scene_action_entities.json",
        "scene_action_entities.provenance.json",
    ):
        shutil.copy2(original_root / filename, fixture_root / filename)
    source_path = fixture_root.parent / "sample_screenplay.fountain"
    shutil.copy2(original_root.parent / source_path.name, source_path)
    source_path.write_text(
        f"{source_path.read_text(encoding='utf-8')}\nTAMPERED\n", encoding="utf-8"
    )
    monkeypatch.setenv("CINE_FORGE_MOCK_FIXTURE_DIR", str(fixture_root))

    with pytest.raises(LLMCallError, match="source hash mismatch"):
        call_llm(
            prompt=(
                "Scene heading: INT. COMMUNITY RADIO STUDIO\n\n"
                "Scene text:\nA cramped studio hums with old gear."
            ),
            model="fixture",
            response_schema=_ActionLineEntities,
        )


@pytest.mark.unit
def test_call_llm_returns_parsed_schema_and_metadata() -> None:
    def fake_transport(_: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": "req_123",
            "choices": [{"message": {"content": '{"value":"ok"}'}}],
            "usage": {"prompt_tokens": 200, "completion_tokens": 40},
        }

    result, metadata = call_llm(
        prompt="hello",
        model="gpt-4o-mini",
        response_schema=DemoSchema,
        transport=fake_transport,
    )

    assert isinstance(result, DemoSchema)
    assert result.value == "ok"
    assert metadata["input_tokens"] == 200
    assert metadata["output_tokens"] == 40
    assert metadata["request_id"] == "req_123"
    assert metadata["estimated_cost_usd"] > 0


@pytest.mark.unit
def test_call_llm_retries_on_transient_error() -> None:
    attempts = {"count": 0}

    def flaky_transport(_: dict[str, Any]) -> dict[str, Any]:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("rate limit exceeded")
        return {
            "id": "req_456",
            "choices": [{"message": {"content": "script text"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        }

    result, metadata = call_llm(
        prompt="normalize",
        model="gpt-4o-mini",
        max_retries=2,
        transport=flaky_transport,
    )

    assert result == "script text"
    assert metadata["request_id"] == "req_456"
    assert attempts["count"] == 2


@pytest.mark.unit
def test_call_llm_retries_on_529_overloaded_error() -> None:
    attempts = {"count": 0}

    def flaky_transport(_: dict[str, Any]) -> dict[str, Any]:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("Anthropic HTTP error 529: overloaded_error")
        return {
            "id": "req_529",
            "choices": [{"message": {"content": "ok"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 10},
        }

    result, metadata = call_llm(
        prompt="normalize",
        model="claude-sonnet-4-6",
        max_retries=2,
        transport=flaky_transport,
    )

    assert result == "ok"
    assert metadata["request_id"] == "req_529"
    assert attempts["count"] == 2


@pytest.mark.unit
def test_call_llm_fails_after_max_retries() -> None:
    def always_fail(_: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("timeout while waiting")

    with pytest.raises(LLMCallError, match="failed after retries"):
        call_llm(
            prompt="x",
            model="gpt-4o",
            max_retries=1,
            transport=always_fail,
        )


@pytest.mark.unit
def test_retry_delay_seconds_uses_exponential_backoff_with_jitter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("cine_forge.ai.llm.random.uniform", lambda _a, b: b)

    assert _retry_delay_seconds(attempt=0, base_delay_seconds=0.5, jitter_ratio=0.25) == 0.625
    assert _retry_delay_seconds(attempt=1, base_delay_seconds=0.5, jitter_ratio=0.25) == 1.25
    assert _retry_delay_seconds(attempt=2, base_delay_seconds=0.5, jitter_ratio=0.25) == 2.5


@pytest.mark.unit
def test_retry_delay_seconds_rejects_negative_inputs() -> None:
    with pytest.raises(ValueError, match="attempt"):
        _retry_delay_seconds(attempt=-1)
    with pytest.raises(ValueError, match="base_delay_seconds"):
        _retry_delay_seconds(attempt=0, base_delay_seconds=-0.1)
    with pytest.raises(ValueError, match="jitter_ratio"):
        _retry_delay_seconds(attempt=0, jitter_ratio=-0.1)


@pytest.mark.unit
def test_circuit_breaker_opens_after_three_transient_failures() -> None:
    _reset_circuit_breakers()
    provider = "anthropic"

    _record_provider_transient_failure(provider, now=100.0)
    _record_provider_transient_failure(provider, now=101.0)
    assert not _is_circuit_breaker_open(provider, now=101.0)

    _record_provider_transient_failure(provider, now=102.0)
    assert _is_circuit_breaker_open(provider, now=102.1)


@pytest.mark.unit
def test_circuit_breaker_closes_after_cooldown_and_resets_on_success() -> None:
    _reset_circuit_breakers()
    provider = "google"

    _record_provider_transient_failure(provider, now=10.0)
    _record_provider_transient_failure(provider, now=11.0)
    _record_provider_transient_failure(provider, now=12.0)
    assert _is_circuit_breaker_open(provider, now=12.1)

    assert not _is_circuit_breaker_open(provider, now=43.0)
    assert _breaker_state(provider).consecutive_failures == 0

    _record_provider_transient_failure(provider, now=50.0)
    _record_provider_success(provider)
    assert _breaker_state(provider).consecutive_failures == 0
    assert not _is_circuit_breaker_open(provider, now=50.1)


@pytest.mark.unit
def test_circuit_breaker_half_open_probe_failure_reopens() -> None:
    _reset_circuit_breakers()
    provider = "anthropic"

    _record_provider_transient_failure(provider, now=10.0)
    _record_provider_transient_failure(provider, now=11.0)
    _record_provider_transient_failure(provider, now=12.0)
    assert _is_circuit_breaker_open(provider, now=12.1)

    # Cooldown expires; next call is half-open probe.
    assert not _is_circuit_breaker_open(provider, now=43.0)
    assert _breaker_state(provider).half_open is True

    # Probe failure should reopen immediately.
    _record_provider_transient_failure(provider, now=43.1)
    assert _is_circuit_breaker_open(provider, now=43.2)


@pytest.mark.unit
def test_estimate_cost_usd_uses_known_model_pricing() -> None:
    cost = estimate_cost_usd(model="gpt-4o-mini", input_tokens=1_000_000, output_tokens=1_000_000)
    assert cost == pytest.approx(0.75)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("model", "expected"),
    [
        ("gpt-5.4", 17.5),
        ("gpt-5.4-mini", 5.25),
        ("gpt-5.4-nano", 1.45),
        ("gemini-3.1-pro-preview", 11.5),
        ("gemini-3.1-flash-lite", 0.5),
        ("grok-4.3", 3.75),
        ("grok-4.5", 8.0),
    ],
)
def test_estimate_cost_usd_supports_newly_added_models(model: str, expected: float) -> None:
    cost = estimate_cost_usd(model=model, input_tokens=1_000_000, output_tokens=1_000_000)
    assert cost == pytest.approx(expected)


@pytest.mark.unit
def test_call_llm_detects_truncation_when_fail_on_truncation() -> None:
    def truncated_transport(_: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": "req_789",
            "choices": [{"message": {"content": "partial"}, "finish_reason": "length"}],
            "usage": {"prompt_tokens": 20, "completion_tokens": 20},
        }

    with pytest.raises(LLMCallError, match="truncated"):
        call_llm(
            prompt="normalize",
            model="gpt-4o-mini",
            fail_on_truncation=True,
            transport=truncated_transport,
        )


@pytest.mark.unit
def test_call_llm_passes_request_timeout_to_provider_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: dict[str, float | None] = {"timeout": None}

    def fake_openai_transport(
        _payload: dict[str, Any],
        *,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        seen["timeout"] = request_timeout_seconds
        return {
            "id": "req_timeout",
            "model": "gpt-4o-mini",
            "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

    monkeypatch.setattr("cine_forge.ai.llm._openai_transport", fake_openai_transport)

    result, _metadata = call_llm(
        prompt="normalize",
        model="gpt-4o-mini",
        request_timeout_seconds=12.5,
    )

    assert result == "ok"
    assert seen["timeout"] == 12.5


@pytest.mark.unit
def test_call_llm_routes_xai_models_to_xai_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, Any] = {"payload": None, "timeout": None}

    def fake_xai_transport(
        payload: dict[str, Any],
        *,
        request_timeout_seconds: float | None = None,
    ) -> dict[str, Any]:
        seen["payload"] = payload
        seen["timeout"] = request_timeout_seconds
        return {
            "id": "xai_req",
            "model": "grok-4.3",
            "choices": [{"message": {"content": "xai ok"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 20},
        }

    monkeypatch.setattr("cine_forge.ai.llm._xai_transport", fake_xai_transport)

    result, metadata = call_llm(
        prompt="test xai",
        model="xai:grok-4.3",
        request_timeout_seconds=22.0,
    )

    assert result == "xai ok"
    assert seen["timeout"] == 22.0
    assert seen["payload"]["model"] == "grok-4.3"
    assert metadata["estimated_cost_usd"] == pytest.approx(0.000175)


# --- Provider Parsing ---


@pytest.mark.unit
def test_parse_provider_prefixed() -> None:
    assert _parse_provider("anthropic:claude-sonnet-4-6") == ("anthropic", "claude-sonnet-4-6")
    assert _parse_provider("google:gemini-2.5-pro") == ("google", "gemini-2.5-pro")
    assert _parse_provider("openai:gpt-4.1") == ("openai", "gpt-4.1")
    assert _parse_provider("xai:grok-4.3") == ("xai", "grok-4.3")


@pytest.mark.unit
def test_parse_provider_autodetect() -> None:
    assert _parse_provider("claude-sonnet-4-6") == ("anthropic", "claude-sonnet-4-6")
    assert _parse_provider("claude-haiku-4-5-20251001") == (
        "anthropic", "claude-haiku-4-5-20251001"
    )
    assert _parse_provider("gemini-2.5-pro") == ("google", "gemini-2.5-pro")
    assert _parse_provider("gemini-2.5-flash") == ("google", "gemini-2.5-flash")
    assert _parse_provider("grok-4.3") == ("xai", "grok-4.3")
    assert _parse_provider("gpt-4.1") == ("openai", "gpt-4.1")
    assert _parse_provider("gpt-4o-mini") == ("openai", "gpt-4o-mini")


@pytest.mark.unit
def test_parse_provider_unknown_prefix_falls_through() -> None:
    # Unknown prefix treated as part of model name, auto-detects to openai
    assert _parse_provider("unknown:some-model") == ("openai", "unknown:some-model")


# --- Gemini Response Normalization ---


@pytest.mark.unit
def test_normalize_gemini_response_basic() -> None:
    raw = {
        "responseId": "gemini-response-basic",
        "modelVersion": "gemini-3.5-flash-lite",
        "candidates": [{
            "content": {"parts": [{"text": "hello world"}]},
            "finishReason": "STOP",
        }],
        "usageMetadata": {
            "promptTokenCount": 100,
            "candidatesTokenCount": 50,
        },
    }
    normalized = _normalize_gemini_response(raw)
    assert normalized["id"] == "gemini-response-basic"
    assert normalized["model"] == "gemini-3.5-flash-lite"
    assert normalized["choices"][0]["message"]["content"] == "hello world"
    assert normalized["choices"][0]["finish_reason"] == "stop"
    assert normalized["usage"]["prompt_tokens"] == 100
    assert normalized["usage"]["completion_tokens"] == 50
    assert normalized["usage"]["completion_tokens_details"] == {
        "visible_tokens": 50,
        "reasoning_tokens": 0,
    }


@pytest.mark.unit
def test_gemini_hidden_thinking_is_billed_and_visible_tokens_are_retained() -> None:
    raw = {
        "responseId": "gemini-response-thinking",
        "modelVersion": "gemini-3.5-flash-lite",
        "candidates": [{
            "content": {"parts": [{"text": "done"}]},
            "finishReason": "STOP",
        }],
        "usageMetadata": {
            "promptTokenCount": 100,
            "candidatesTokenCount": 10,
            "totalTokenCount": 1110,
            "thoughtsTokenCount": 1000,
        },
    }

    result, metadata = call_llm(
        prompt="test",
        model="gemini-3.5-flash-lite",
        transport=lambda _: _normalize_gemini_response(raw),
    )

    assert result == "done"
    assert metadata["input_tokens"] == 100
    assert metadata["output_tokens"] == 1010
    assert metadata["visible_output_tokens"] == 10
    assert metadata["reasoning_output_tokens"] == 1000
    assert metadata["request_id"] == "gemini-response-thinking"
    assert metadata["estimated_cost_usd"] == pytest.approx(0.002555)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("model", "thinking_level"),
    [
        ("gemini-3.5-flash-lite", "minimal"),
        ("gemini-3.6-flash", "medium"),
    ],
)
def test_new_gemini_payload_uses_thinking_level_without_sampling_controls(
    model: str,
    thinking_level: str,
) -> None:
    payload = _build_gemini_payload(
        model=model,
        prompt="Return structured JSON.",
        temperature=0.7,
        max_tokens=65_536,
        response_schema=DemoSchema,
        thinking_level=thinking_level,
    )
    config = payload["generationConfig"]

    assert config["maxOutputTokens"] == 65_536
    assert config["thinkingConfig"] == {"thinkingLevel": thinking_level}
    assert config["responseMimeType"] == "application/json"
    assert "responseSchema" in config
    assert {"temperature", "topP", "topK", "thinkingBudget"}.isdisjoint(config)

    capped = _build_gemini_payload(
        model=model,
        prompt="Return structured JSON.",
        temperature=0.7,
        max_tokens=98_304,
        response_schema=DemoSchema,
        thinking_level=thinking_level,
    )
    assert capped["generationConfig"]["maxOutputTokens"] == 65_536

    legacy = _build_gemini_payload(
        model="gemini-2.5-flash",
        prompt="Return structured JSON.",
        temperature=0.2,
        max_tokens=4096,
        response_schema=DemoSchema,
    )
    assert legacy["generationConfig"]["temperature"] == 0.2
    assert "thinkingConfig" not in legacy["generationConfig"]


@pytest.mark.unit
def test_gemini_payload_rejects_invalid_or_legacy_thinking_level() -> None:
    with pytest.raises(ValueError, match="thinking_level must be one of"):
        _build_gemini_payload(
            model="gemini-3.6-flash",
            prompt="Return structured JSON.",
            temperature=0.0,
            max_tokens=65_536,
            response_schema=DemoSchema,
            thinking_level="ultra",
        )

    with pytest.raises(ValueError, match="not supported"):
        _build_gemini_payload(
            model="gemini-2.5-flash",
            prompt="Return structured JSON.",
            temperature=0.0,
            max_tokens=4096,
            response_schema=DemoSchema,
            thinking_level="minimal",
        )


@pytest.mark.unit
@pytest.mark.parametrize(
    ("usage", "message"),
    [
        ({}, "prompt_tokens must be a nonnegative integer"),
        (
            {"promptTokenCount": -1, "candidatesTokenCount": 2},
            "prompt_tokens must be a nonnegative integer",
        ),
        (
            {"promptTokenCount": True, "candidatesTokenCount": 2},
            "prompt_tokens must be a nonnegative integer",
        ),
        (
            {"promptTokenCount": 1, "candidatesTokenCount": 2.5},
            "visible_completion_tokens must be a nonnegative integer",
        ),
        (
            {
                "promptTokenCount": 100,
                "candidatesTokenCount": 10,
                "totalTokenCount": 109,
            },
            "total_tokens must be at least",
        ),
    ],
)
def test_normalize_gemini_response_rejects_malformed_usage(
    usage: dict[str, object],
    message: str,
) -> None:
    raw = {
        "responseId": "gemini-response-malformed",
        "modelVersion": "gemini-3.6-flash",
        "candidates": [{
            "content": {"parts": [{"text": "done"}]},
            "finishReason": "STOP",
        }],
        "usageMetadata": usage,
    }

    with pytest.raises(ValueError, match=message):
        _normalize_gemini_response(raw)


@pytest.mark.unit
def test_normalize_gemini_response_truncation() -> None:
    raw = {
        "responseId": "gemini-response-truncated",
        "modelVersion": "gemini-3.6-flash",
        "candidates": [{
            "content": {"parts": [{"text": "partial"}]},
            "finishReason": "MAX_TOKENS",
        }],
        "usageMetadata": {"promptTokenCount": 10, "candidatesTokenCount": 10},
    }
    normalized = _normalize_gemini_response(raw)
    assert normalized["choices"][0]["finish_reason"] == "length"


@pytest.mark.unit
def test_gemini_response_rejects_provider_model_substitution() -> None:
    raw = {
        "responseId": "gemini-response-substitution",
        "modelVersion": "gemini-3.6-flash",
        "candidates": [
            {"content": {"parts": [{"text": "done"}]}, "finishReason": "STOP"}
        ],
        "usageMetadata": {"promptTokenCount": 100, "candidatesTokenCount": 10},
    }

    with pytest.raises(LLMCallError, match="modelVersion does not match"):
        _normalize_gemini_response(raw, expected_model="gemini-3.5-flash-lite")


@pytest.mark.unit
def test_gemini_response_rejects_contradictory_thinking_tokens() -> None:
    raw = {
        "responseId": "gemini-response-thinking-contradiction",
        "modelVersion": "gemini-3.5-flash-lite",
        "candidates": [
            {"content": {"parts": [{"text": "done"}]}, "finishReason": "STOP"}
        ],
        "usageMetadata": {
            "promptTokenCount": 100,
            "candidatesTokenCount": 10,
            "totalTokenCount": 1110,
            "thoughtsTokenCount": 999,
        },
    }

    with pytest.raises(ValueError, match="does not reconcile"):
        _normalize_gemini_response(raw, expected_model="gemini-3.5-flash-lite")


@pytest.mark.unit
@pytest.mark.parametrize("missing", ["responseId", "modelVersion"])
def test_gemini_response_requires_call_and_model_identity(missing: str) -> None:
    raw = {
        "responseId": "gemini-response-identity",
        "modelVersion": "gemini-3.5-flash-lite",
        "candidates": [
            {"content": {"parts": [{"text": "done"}]}, "finishReason": "STOP"}
        ],
        "usageMetadata": {"promptTokenCount": 1, "candidatesTokenCount": 1},
    }
    raw.pop(missing)

    with pytest.raises(LLMCallError, match=missing):
        _normalize_gemini_response(raw)


@pytest.mark.unit
def test_normalize_gemini_response_missing_candidates() -> None:
    with pytest.raises(LLMCallError, match="missing candidates"):
        _normalize_gemini_response({"candidates": []})


# --- Gemini Schema Conversion ---


@pytest.mark.unit
def test_to_gemini_schema_simple() -> None:
    schema = DemoSchema.model_json_schema()
    result = _to_gemini_schema(schema)
    assert result["type"] == "OBJECT"
    assert result["properties"]["value"]["type"] == "STRING"
    assert "title" not in result
    assert "additionalProperties" not in result


@pytest.mark.unit
def test_to_gemini_schema_with_optional_field() -> None:
    class WithOptional(BaseModel):
        name: str
        nickname: str | None = None

    schema = WithOptional.model_json_schema()
    result = _to_gemini_schema(schema)
    assert result["properties"]["name"]["type"] == "STRING"
    # Optional resolves to the non-null variant
    assert result["properties"]["nickname"]["type"] == "STRING"


@pytest.mark.unit
def test_to_gemini_schema_nested_model() -> None:
    class Inner(BaseModel):
        score: float

    class Outer(BaseModel):
        name: str
        detail: Inner

    schema = Outer.model_json_schema()
    result = _to_gemini_schema(schema)
    assert result["properties"]["name"]["type"] == "STRING"
    detail = result["properties"]["detail"]
    assert detail["type"] == "OBJECT"
    assert detail["properties"]["score"]["type"] == "NUMBER"


# --- Gemini end-to-end via call_llm with injected transport ---


@pytest.mark.unit
def test_call_llm_with_gemini_model_uses_transport() -> None:
    """Verify gemini-* auto-detects to google and works with injected transport."""

    def fake_gemini_transport(_: dict[str, Any]) -> dict[str, Any]:
        return {
            "choices": [{"message": {"content": '{"value":"gemini_ok"}'}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 50, "completion_tokens": 20},
        }

    result, metadata = call_llm(
        prompt="test",
        model="gemini-2.5-pro",
        response_schema=DemoSchema,
        transport=fake_gemini_transport,
    )
    assert isinstance(result, DemoSchema)
    assert result.value == "gemini_ok"


@pytest.mark.unit
def test_call_llm_with_prefixed_model_string() -> None:
    """Verify provider-prefixed model strings work through call_llm."""

    def fake_transport(_: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": "req_prefix",
            "choices": [{"message": {"content": "prefixed"}}],
            "usage": {"prompt_tokens": 5, "completion_tokens": 5},
        }

    result, metadata = call_llm(
        prompt="test",
        model="anthropic:claude-sonnet-4-6",
        transport=fake_transport,
    )
    assert result == "prefixed"
    # bare_model is used for cost estimation
    assert metadata["model"] == "claude-sonnet-4-6"


# --- Prompt Caching ---


@pytest.mark.unit
def test_caching_adds_cache_control_to_anthropic_payload() -> None:
    """When enable_caching=True, user content is a block with cache_control."""
    payload = _build_anthropic_payload(
        model="claude-sonnet-4-6",
        prompt="Hello world",
        temperature=0.0,
        max_tokens=1024,
        response_schema=None,
        enable_caching=True,
    )
    content = payload["messages"][0]["content"]
    assert isinstance(content, list)
    assert len(content) == 1
    assert content[0]["type"] == "text"
    assert content[0]["text"] == "Hello world"
    assert content[0]["cache_control"] == {"type": "ephemeral"}


@pytest.mark.unit
def test_caching_disabled_leaves_content_as_string() -> None:
    """When enable_caching=False (default), user content stays a plain string."""
    payload = _build_anthropic_payload(
        model="claude-sonnet-4-6",
        prompt="Hello world",
        temperature=0.0,
        max_tokens=1024,
        response_schema=None,
        enable_caching=False,
    )
    content = payload["messages"][0]["content"]
    assert isinstance(content, str)
    assert content == "Hello world"


@pytest.mark.unit
def test_caching_not_applied_for_non_anthropic_transport() -> None:
    """enable_caching=True with a non-Anthropic model calls transport without cache_control."""
    calls = []

    def fake_transport(payload: dict[str, Any]) -> dict[str, Any]:
        calls.append(payload)
        return {
            "id": "req_1",
            "choices": [{"message": {"content": "hello"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }

    call_llm(
        prompt="test",
        model="gpt-4o-mini",
        enable_caching=True,  # Ignored for OpenAI transport
        transport=fake_transport,
    )
    assert len(calls) == 1
    # OpenAI payload uses plain string content
    assert isinstance(calls[0]["messages"][0]["content"], str)


@pytest.mark.unit
def test_normalize_anthropic_response_passes_through_cache_tokens() -> None:
    """Cache token counts from Anthropic usage are preserved in normalized response."""
    raw = {
        "id": "msg_123",
        "model": "claude-sonnet-4-6",
        "content": [{"type": "text", "text": "answer"}],
        "stop_reason": "end_turn",
        "usage": {
            "input_tokens": 1000,
            "output_tokens": 50,
            "cache_read_input_tokens": 900,
            "cache_creation_input_tokens": 100,
        },
    }
    normalized = _normalize_anthropic_response(raw)
    assert normalized["model"] == "claude-sonnet-4-6"
    assert normalized["usage"]["cache_read_input_tokens"] == 900
    assert normalized["usage"]["cache_creation_input_tokens"] == 100

"""Semantic review helpers for runtime media validation."""

from __future__ import annotations

import base64
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator

from cine_forge.ai.llm import estimate_cost_usd
from cine_forge.env import require_env as _require_provider_env
from cine_forge.schemas import (
    CostRecord,
    DeterministicMediaProbe,
    MediaValidationEvidence,
    MediaValidationFinding,
    MediaValidationTarget,
    SemanticMediaReview,
)

OPENAI_CHAT_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
GEMINI_MODELS_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class _SemanticReviewFindingPayload(BaseModel):
    code: str = Field(min_length=1)
    severity: Literal["warning", "error"]
    message: str = Field(min_length=1)
    timestamp_seconds: float | None = Field(default=None, ge=0.0)
    frame_index: int | None = Field(default=None, ge=0)

    @field_validator("severity", mode="before")
    @classmethod
    def _normalize_severity(cls, value: Any) -> Literal["warning", "error"]:
        candidate = str(value).strip().lower()
        if candidate in {"error", "warning"}:
            return candidate
        if candidate in {"blocking", "critical", "high", "severe"}:
            return "error"
        if candidate in {"medium", "minor", "low", "info", "informational"}:
            return "warning"
        raise ValueError("severity must be warning/error or a known synonym")


class _SemanticReviewPayload(BaseModel):
    verdict: Literal["pass", "needs_review", "fail"]
    summary: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    findings: list[_SemanticReviewFindingPayload] = Field(default_factory=list)

    @field_validator("confidence", mode="before")
    @classmethod
    def _normalize_confidence(cls, value: Any) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        candidate = str(value).strip().lower()
        if not candidate:
            raise ValueError("confidence must be provided")
        if candidate.endswith("%"):
            return float(candidate[:-1]) / 100.0
        synonyms = {
            "very_high": 0.98,
            "high": 0.9,
            "medium": 0.65,
            "low": 0.35,
            "very_low": 0.15,
        }
        if candidate in synonyms:
            return synonyms[candidate]
        return float(candidate)


def review_sampled_frames(
    *,
    model: str | None,
    target: MediaValidationTarget,
    prompt_text: str | None,
    context_notes: list[str],
    probe: DeterministicMediaProbe,
    project_dir: Path,
    max_tokens: int,
    temperature: float,
) -> SemanticMediaReview:
    if not model:
        return SemanticMediaReview(
            status="skipped",
            mode="none",
            reason_skipped="No semantic review model was configured.",
        )
    if not probe.sample_frames:
        return SemanticMediaReview(
            status="skipped",
            mode="none",
            model=model,
            reason_skipped="No sampled frames were available for semantic review.",
        )

    try:
        payload, cost = _call_multimodal_reviewer(
            model=model,
            user_text=_semantic_review_prompt(
                target=target,
                prompt_text=prompt_text,
                context_notes=context_notes,
                probe=probe,
            ),
            frames=[
                _frame_packet(project_dir / sample.image.relative_path)
                for sample in probe.sample_frames
            ],
            max_tokens=max_tokens,
            temperature=temperature,
        )
        parsed = _SemanticReviewPayload.model_validate(payload)
    except Exception as exc:
        return SemanticMediaReview(
            status="skipped",
            mode="none",
            model=model,
            reason_skipped=f"Semantic review failed: {exc}",
        )

    return SemanticMediaReview(
        status="pass" if parsed.verdict == "pass" else parsed.verdict,
        mode="sampled_frames",
        model=model,
        summary=parsed.summary,
        confidence=parsed.confidence,
        findings=_parsed_findings(parsed.findings, probe),
        cost=cost,
    )


def _parsed_findings(
    parsed_findings: list[_SemanticReviewFindingPayload],
    probe: DeterministicMediaProbe,
) -> list[MediaValidationFinding]:
    findings: list[MediaValidationFinding] = []
    for finding in parsed_findings:
        findings.append(
            MediaValidationFinding(
                code=finding.code,
                severity=finding.severity,
                message=finding.message,
                evidence=_finding_evidence(finding=finding, probe=probe),
            )
        )
    return findings


def _finding_evidence(
    *,
    finding: _SemanticReviewFindingPayload,
    probe: DeterministicMediaProbe,
) -> list[MediaValidationEvidence]:
    if finding.frame_index is not None and finding.frame_index < len(probe.sample_frames):
        frame = probe.sample_frames[finding.frame_index]
        return [
            MediaValidationEvidence(
                label=f"Frame {finding.frame_index + 1}",
                timestamp_seconds=frame.timestamp_seconds,
                sample_relative_path=frame.image.relative_path,
            )
        ]
    if finding.timestamp_seconds is not None:
        return [MediaValidationEvidence(timestamp_seconds=finding.timestamp_seconds)]
    return []


def _semantic_review_prompt(
    *,
    target: MediaValidationTarget,
    prompt_text: str | None,
    context_notes: list[str],
    probe: DeterministicMediaProbe,
) -> str:
    prompt_excerpt = (prompt_text or "").strip()
    if len(prompt_excerpt) > 700:
        prompt_excerpt = f"{prompt_excerpt[:700]}..."
    included_scene_count = (
        target.included_scene_count
        if target.included_scene_count is not None
        else "unknown"
    )
    omitted_scene_count = (
        target.omitted_scene_count
        if target.omitted_scene_count is not None
        else "unknown"
    )
    lines = [
        (
            "You are reviewing sampled frames from a validated media artifact "
            "for production readiness."
        ),
        "Judge only what is supported by the provided sampled frames and media facts.",
        "Return JSON only.",
        "",
        "Required behavior:",
        '- Use verdict "fail" only for clear blocking problems.',
        (
            '- Use verdict "needs_review" when the sample packet is '
            "inconclusive or has softer concerns."
        ),
        '- Use verdict "pass" only when the sampled evidence looks usable.',
        '- Use finding severity "error" for blocking issues and "warning" for softer concerns.',
        "- Include concrete findings only when you can point to visible evidence.",
        "",
        f"Target label: {target.label}",
        f"Target scope: {target.scope_kind}",
        f"Audio present: {probe.audio_stream_present}",
        f"Sample frames: {len(probe.sample_frames)}",
    ]
    if target.scope_kind == "scene":
        lines.extend(
            [
                f"Scene: {target.scene_heading}",
                f"Scene number: {target.scene_number}",
            ]
        )
    else:
        lines.extend(
            [
                f"Coverage state: {target.coverage_state or 'unknown'}",
                f"Included scenes: {included_scene_count}",
                f"Omitted scenes: {omitted_scene_count}",
                (
                    "Important: for project-level final output, judge only "
                    "the assembled cut that exists here. Omitted scenes are "
                    "not part of the validated media."
                ),
            ]
        )
    lines.extend(
        [
            "",
            "Deterministic notes:",
            f"- decode_succeeded: {probe.decode_succeeded}",
            f"- video_stream_present: {probe.video_stream_present}",
            f"- audio_stream_present: {probe.audio_stream_present}",
        ]
    )
    if context_notes:
        lines.extend(["", "Context notes:"])
        lines.extend(f"- {note}" for note in context_notes)
    lines.extend(
        [
            "",
            "Prompt excerpt:",
            prompt_excerpt or "[unavailable]",
            "",
            "Respond with keys: verdict, summary, confidence, findings[].",
            "Confidence must be a number between 0 and 1, not a word label.",
            (
                "Each finding must include: code, severity, message, and "
                "optionally frame_index or timestamp_seconds."
            ),
        ]
    )
    return "\n".join(lines)


def _call_multimodal_reviewer(
    *,
    model: str,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> tuple[dict[str, Any], CostRecord]:
    provider, bare_model = _parse_provider(model)
    if provider == "openai":
        output, prompt_tokens, completion_tokens = _call_openai_reviewer(
            model=bare_model,
            user_text=user_text,
            frames=frames,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    elif provider == "anthropic":
        output, prompt_tokens, completion_tokens = _call_anthropic_reviewer(
            model=bare_model,
            user_text=user_text,
            frames=frames,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    elif provider == "google":
        output, prompt_tokens, completion_tokens = _call_google_reviewer(
            model=bare_model,
            user_text=user_text,
            frames=frames,
            max_tokens=max_tokens,
            temperature=temperature,
        )
    else:
        raise RuntimeError(f"Unsupported multimodal provider: {provider}")

    cost = CostRecord(
        model=bare_model,
        input_tokens=prompt_tokens,
        output_tokens=completion_tokens,
        estimated_cost_usd=estimate_cost_usd(bare_model, prompt_tokens, completion_tokens),
    )
    return json.loads(_strip_json_fences(output)), cost


def _call_openai_reviewer(
    *,
    model: str,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> tuple[str, int, int]:
    response = _request_json(
        OPENAI_CHAT_URL,
        headers={
            "Authorization": f"Bearer {_require_env('OPENAI_API_KEY')}",
            "Content-Type": "application/json",
        },
        body={
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        *[
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{frame['mime_type']};base64,{frame['base64']}",
                                    "detail": "high",
                                },
                            }
                            for frame in frames
                        ],
                    ],
                }
            ],
            "temperature": temperature,
            "max_completion_tokens": max_tokens,
            "response_format": {"type": "json_object"},
        },
    )
    usage = response.get("usage", {})
    return (
        response["choices"][0]["message"]["content"],
        int(usage.get("prompt_tokens", 0)),
        int(usage.get("completion_tokens", 0)),
    )


def _call_anthropic_reviewer(
    *,
    model: str,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> tuple[str, int, int]:
    response = _request_json(
        ANTHROPIC_MESSAGES_URL,
        headers={
            "x-api-key": _require_env("ANTHROPIC_API_KEY"),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        body={
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "system": (
                "Return JSON only with keys verdict, summary, confidence, findings. "
                "Do not wrap the response in markdown fences."
            ),
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": user_text},
                        *[
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": frame["mime_type"],
                                    "data": frame["base64"],
                                },
                            }
                            for frame in frames
                        ],
                    ],
                }
            ],
        },
    )
    blocks = response.get("content", [])
    usage = response.get("usage", {})
    return (
        "\n".join(block.get("text", "") for block in blocks if block.get("type") == "text"),
        int(usage.get("input_tokens", 0)),
        int(usage.get("output_tokens", 0)),
    )


def _call_google_reviewer(
    *,
    model: str,
    user_text: str,
    frames: list[dict[str, str]],
    max_tokens: int,
    temperature: float,
) -> tuple[str, int, int]:
    response = _request_json(
        _google_generate_content_url(model),
        headers={"Content-Type": "application/json"},
        body={
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {"text": user_text},
                        *[
                            {
                                "inline_data": {
                                    "mime_type": frame["mime_type"],
                                    "data": frame["base64"],
                                }
                            }
                            for frame in frames
                        ],
                    ],
                }
            ],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
                "responseMimeType": "application/json",
            },
        },
    )
    candidates = response.get("candidates", [])
    parts = candidates[0].get("content", {}).get("parts", []) if candidates else []
    usage = response.get("usageMetadata", {})
    return (
        "\n".join(part.get("text", "") for part in parts if "text" in part),
        int(usage.get("promptTokenCount", 0)),
        int(usage.get("candidatesTokenCount", 0)),
    )


def _google_generate_content_url(model: str) -> str:
    encoded_model = urllib.parse.quote(model, safe="")
    return (
        f"{GEMINI_MODELS_URL}/{encoded_model}:generateContent"
        f"?key={_require_env('GEMINI_API_KEY')}"
    )


def _frame_packet(path: Path) -> dict[str, str]:
    return {
        "mime_type": "image/jpeg",
        "base64": base64.b64encode(path.read_bytes()).decode("utf-8"),
    }


def _request_json(url: str, *, headers: dict[str, str], body: dict[str, Any]) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=180) as response:  # noqa: S310
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{url} returned HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{url} request failed: {exc}") from exc


def _require_env(name: str) -> str:
    return _require_provider_env(name)


def _parse_provider(model: str) -> tuple[str, str]:
    if model.startswith("anthropic:messages:"):
        return "anthropic", model.split(":", 2)[2]
    if model.startswith("openai:"):
        return "openai", model.split(":", 1)[1]
    if model.startswith("google:"):
        return "google", model.split(":", 1)[1]
    if model.startswith("claude-"):
        return "anthropic", model
    if model.startswith("gemini-"):
        return "google", model
    return "openai", model


def _strip_json_fences(value: str) -> str:
    stripped = value.strip()
    if stripped.startswith("```"):
        stripped = stripped.split("\n", 1)[1] if "\n" in stripped else stripped
        if stripped.endswith("```"):
            stripped = stripped.rsplit("```", 1)[0]
    return stripped.strip()

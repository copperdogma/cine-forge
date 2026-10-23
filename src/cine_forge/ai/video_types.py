"""Normalized transport contracts and failures for video generation."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from cine_forge.schemas.media_cost import CostReceipt


class VideoGenerationError(RuntimeError):
    """Terminal error raised when a video-generation request fails."""

    def __init__(
        self,
        message: str,
        *,
        retryable: bool = False,
        status_code: int | None = None,
        cost_receipts: list[CostReceipt] | None = None,
        provider_job_id: str | None = None,
        provider_response: dict[str, Any] | None = None,
        submission_uncertain: bool = False,
    ) -> None:
        super().__init__(message)
        self.retryable = retryable
        self.status_code = status_code
        self.cost_receipts = list(cost_receipts or [])
        self.provider_job_id = provider_job_id
        self.provider_response = dict(provider_response or {})
        self.submission_uncertain = submission_uncertain


@dataclass(frozen=True)
class VideoReferenceInput:
    """Local image input passed to the target provider."""

    path: Path
    media_type: str
    usage: Literal["input_reference", "reference_image", "last_frame"]


@dataclass(frozen=True)
class VideoGenerationRequest:
    """Normalized request payload for the provider transport layer."""

    prompt: str
    duration_seconds: int
    resolution: str
    aspect_ratio: str
    first_frame: VideoReferenceInput | None = None
    last_frame: VideoReferenceInput | None = None
    reference_images: list[VideoReferenceInput] = field(default_factory=list)
    provider_params: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class VideoGenerationResult:
    """Normalized response returned by the provider transport layer."""

    video_bytes: bytes
    media_type: str
    model_used: str
    request_id: str | None = None
    provider_job_id: str | None = None
    cost_receipts: list[CostReceipt] = field(default_factory=list)
    provider_response: dict[str, Any] = field(default_factory=dict)

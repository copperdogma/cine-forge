"""Typed source-of-truth for the synthetic ordered-frame dataset."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from typing import Literal

CaseStatus = Literal["active_frame_eval", "quarantined"]
TemporalControl = Literal["dynamic", "static", "change_point"]

OUTPUT_SIZE = (640, 360)
FPS = 8
FRAME_POLICY = "five_evenly_spaced_jpegs_v1"
GENERATOR_VERSION = "frame-truth-v2"


@dataclass(frozen=True)
class FrameTarget:
    """Claims deliberately limited to what five ordered JPEGs can support."""

    summary_reference: str
    required_keywords: tuple[str, ...]
    tone_tags: tuple[str, ...]
    emotion_tags: tuple[str, ...]
    color_tags: tuple[str, ...]
    camera_tags: tuple[str, ...]
    motion_tags: tuple[str, ...]
    continuity_status: str
    continuity_notes: tuple[str, ...]


@dataclass(frozen=True)
class ClipSpec:
    slug: str
    title: str
    scene_kind: str
    duration_seconds: float
    primary_color: tuple[int, int, int]
    secondary_color: tuple[int, int, int]
    accent_color: tuple[int, int, int]
    tags: tuple[str, ...]
    target: FrameTarget
    case_status: CaseStatus
    status_reason: str
    temporal_control: TemporalControl
    expected_unique_sampled_frames: int
    audio_tags: tuple[str, ...] = ()
    transcript: str | None = None
    audio_description: str | None = None
    prop_color_start: tuple[int, int, int] | None = None
    prop_color_end: tuple[int, int, int] | None = None

    @property
    def is_active(self) -> bool:
        return self.case_status == "active_frame_eval"

    def fingerprint(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode()).hexdigest()


def sampled_frame_indexes(total_frames: int) -> list[int]:
    """Return the exact five-frame packet indexes used by generator and scorer."""
    if total_frames < 1:
        raise ValueError("total_frames must be positive")
    return sorted(
        {
            0,
            total_frames // 4,
            total_frames // 2,
            (3 * total_frames) // 4,
            total_frames - 1,
        }
    )

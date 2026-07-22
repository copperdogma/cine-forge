"""Complete ordered synthetic frame-packet case catalog."""

from __future__ import annotations

from video_understanding_dataset_model import ClipSpec
from video_understanding_dataset_specs_a import SPECS_A
from video_understanding_dataset_specs_b import SPECS_B

CLIPS: tuple[ClipSpec, ...] = (*SPECS_A, *SPECS_B)
ACTIVE_CLIPS: tuple[ClipSpec, ...] = tuple(spec for spec in CLIPS if spec.is_active)
QUARANTINED_CLIPS: tuple[ClipSpec, ...] = tuple(spec for spec in CLIPS if not spec.is_active)

if len(CLIPS) != 20:
    raise RuntimeError(f"Expected 20 synthetic frame cases, found {len(CLIPS)}")
if len({spec.slug for spec in CLIPS}) != len(CLIPS):
    raise RuntimeError("Synthetic frame case IDs must be unique")
if len(ACTIVE_CLIPS) != 6:
    raise RuntimeError(f"Expected 6 active frame cases, found {len(ACTIVE_CLIPS)}")

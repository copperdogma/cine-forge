"""Narrative interchange export assembly for OpenTimelineIO."""

from __future__ import annotations

from collections import defaultdict

import opentimelineio as otio

from cine_forge.schemas.export_interchange import NarrativeAnnotation, NarrativeInterchangeExport

_OTIO_RATE = 24.0
_DEFAULT_MARKER_COLOR = otio.schema.MarkerColor.WHITE
_MARKER_COLORS = {
    "blue": otio.schema.MarkerColor.BLUE,
    "green": otio.schema.MarkerColor.GREEN,
    "orange": otio.schema.MarkerColor.ORANGE,
    "purple": otio.schema.MarkerColor.PURPLE,
    "red": otio.schema.MarkerColor.RED,
}


def build_otio_timeline(payload: NarrativeInterchangeExport) -> otio.schema.Timeline:
    """Build an OTIO timeline from the canonical narrative payload."""
    annotations_by_scene: dict[str, list[NarrativeAnnotation]] = defaultdict(list)
    for annotation in payload.annotations:
        annotations_by_scene[annotation.scene_id].append(annotation)

    track = otio.schema.Track(name="Narrative Scenes", kind=otio.schema.TrackKind.Video)
    track.metadata["cine_forge"] = {
        "project_id": payload.project_id,
        "timeline_ref": payload.timeline_ref.model_dump(mode="json"),
        "track_manifest_ref": (
            payload.track_manifest_ref.model_dump(mode="json")
            if payload.track_manifest_ref is not None
            else None
        ),
        "scene_count": len(payload.scenes),
    }

    for scene in payload.scenes:
        clip = otio.schema.Clip(name=scene.heading)
        clip.source_range = _time_range(start_seconds=0.0, duration_seconds=scene.duration_seconds)
        clip.metadata["cine_forge"] = {
            "scene": scene.model_dump(mode="json"),
            "project_id": payload.project_id,
            "timeline_ref": payload.timeline_ref.model_dump(mode="json"),
        }
        for annotation in annotations_by_scene.get(scene.scene_id, []):
            clip.markers.append(
                _build_marker(
                    annotation=annotation,
                    scene_start_seconds=scene.start_seconds,
                )
            )
        track.append(clip)

    timeline = otio.schema.Timeline(name=payload.project_title, tracks=[track])
    timeline.metadata["cine_forge"] = {
        "project_id": payload.project_id,
        "project_title": payload.project_title,
        "timeline_ref": payload.timeline_ref.model_dump(mode="json"),
        "track_manifest_ref": (
            payload.track_manifest_ref.model_dump(mode="json")
            if payload.track_manifest_ref is not None
            else None
        ),
        "total_duration_seconds": payload.total_duration_seconds,
        "scene_count": len(payload.scenes),
        "annotation_count": len(payload.annotations),
    }
    return timeline


def render_otio(payload: NarrativeInterchangeExport) -> str:
    """Render the canonical narrative payload as OTIO JSON."""
    return otio.adapters.write_to_string(build_otio_timeline(payload), adapter_name="otio_json")


def parse_otio(serialized_timeline: str) -> otio.schema.Timeline:
    """Parse OTIO JSON and verify it deserializes to a timeline object."""
    parsed = otio.adapters.read_from_string(serialized_timeline, adapter_name="otio_json")
    if not isinstance(parsed, otio.schema.Timeline):
        raise ValueError("OTIO export did not deserialize to a Timeline")
    return parsed


def _build_marker(
    *,
    annotation: NarrativeAnnotation,
    scene_start_seconds: float,
) -> otio.schema.Marker:
    relative_start = max(annotation.start_seconds - scene_start_seconds, 0.0)
    marker = otio.schema.Marker(
        name=annotation.label,
        marked_range=_time_range(
            start_seconds=relative_start,
            duration_seconds=annotation.duration_seconds,
        ),
        color=_MARKER_COLORS.get(annotation.color_label or "", _DEFAULT_MARKER_COLOR),
    )
    marker.comment = annotation.note or ""
    marker.metadata["cine_forge"] = {
        "annotation": annotation.model_dump(mode="json"),
        "relative_start_seconds": relative_start,
    }
    return marker


def _time_range(*, start_seconds: float, duration_seconds: float) -> otio.opentime.TimeRange:
    return otio.opentime.TimeRange(
        start_time=otio.opentime.RationalTime(start_seconds * _OTIO_RATE, _OTIO_RATE),
        duration=otio.opentime.RationalTime(duration_seconds * _OTIO_RATE, _OTIO_RATE),
    )

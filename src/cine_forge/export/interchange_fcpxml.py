"""Narrative interchange export assembly and FCPXML emission."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import defaultdict
from fractions import Fraction

from cine_forge.artifacts import ArtifactStore
from cine_forge.export.project_loader import (
    load_project_title,
    load_timeline_artifact,
    load_timeline_scenes,
    load_track_manifest_artifact,
)
from cine_forge.schemas import Scene, TimelineEntry
from cine_forge.schemas.export_interchange import (
    NarrativeAnnotation,
    NarrativeInterchangeExport,
    NarrativeSceneSegment,
)

_ANNOTATION_COLORS = {
    "scene_boundary": "blue",
    "beat": "orange",
    "character_entrance": "green",
    "character_exit": "red",
    "emotional_note": "purple",
}


def build_narrative_interchange_export(
    store: ArtifactStore,
    *,
    project_id: str,
    project_title: str | None = None,
) -> NarrativeInterchangeExport:
    """Build a typed narrative export payload from timeline-backed artifacts."""
    timeline_bundle = load_timeline_artifact(store)
    if timeline_bundle is None:
        raise ValueError("Timeline not found for project export")
    timeline_ref, timeline = timeline_bundle

    project_name = project_title or load_project_title(store, project_id)
    manifest_bundle = load_track_manifest_artifact(store, expected_timeline_ref=timeline_ref)
    track_manifest_ref = manifest_bundle[0] if manifest_bundle is not None else None

    timeline_scenes = load_timeline_scenes(store, timeline)
    scenes: list[NarrativeSceneSegment] = []
    annotations: list[NarrativeAnnotation] = []

    cursor_seconds = 0.0
    for index, (entry, scene) in enumerate(timeline_scenes):
        duration_seconds = max(_scene_duration_seconds(entry, scene), 0.0)
        segment = NarrativeSceneSegment(
            scene_id=scene.scene_id,
            scene_number=scene.scene_number,
            scene_ref=entry.scene_ref,
            edit_position=entry.edit_position,
            story_position=entry.story_position,
            heading=scene.heading,
            location=scene.location,
            time_of_day=scene.time_of_day,
            int_ext=scene.int_ext,
            characters_present=list(scene.characters_present),
            start_seconds=cursor_seconds,
            duration_seconds=duration_seconds,
            end_seconds=cursor_seconds + duration_seconds,
        )
        scenes.append(segment)
        annotations.extend(_scene_annotations(segment=segment, scene=scene, index=index))
        cursor_seconds = segment.end_seconds

    for index, segment in enumerate(scenes):
        current_characters = set(segment.characters_present)
        previous_characters = set(scenes[index - 1].characters_present) if index > 0 else set()
        next_characters = (
            set(scenes[index + 1].characters_present)
            if index + 1 < len(scenes)
            else set()
        )

        for character_name in sorted(current_characters - previous_characters):
            annotations.append(
                NarrativeAnnotation(
                    annotation_id=f"{segment.scene_id}-entrance-{_slug(character_name)}",
                    kind="character_entrance",
                    scene_id=segment.scene_id,
                    scene_ref=segment.scene_ref,
                    start_seconds=segment.start_seconds,
                    duration_seconds=0.0,
                    end_seconds=segment.start_seconds,
                    label=f"Entrance: {character_name}",
                    note=f"{character_name} first appears in Scene {segment.scene_number}.",
                    color_label=_ANNOTATION_COLORS["character_entrance"],
                    character_name=character_name,
                )
            )

        for character_name in sorted(current_characters - next_characters):
            annotations.append(
                NarrativeAnnotation(
                    annotation_id=f"{segment.scene_id}-exit-{_slug(character_name)}",
                    kind="character_exit",
                    scene_id=segment.scene_id,
                    scene_ref=segment.scene_ref,
                    start_seconds=segment.end_seconds,
                    duration_seconds=0.0,
                    end_seconds=segment.end_seconds,
                    label=f"Exit: {character_name}",
                    note=(
                        f"{character_name} is no longer present after "
                        f"Scene {segment.scene_number}."
                    ),
                    color_label=_ANNOTATION_COLORS["character_exit"],
                    character_name=character_name,
                )
            )

    annotations.sort(key=_annotation_sort_key)
    return NarrativeInterchangeExport(
        project_id=project_id,
        project_title=project_name,
        timeline_ref=timeline_ref,
        track_manifest_ref=track_manifest_ref,
        total_duration_seconds=cursor_seconds,
        scenes=scenes,
        annotations=annotations,
    )


def render_fcpxml(payload: NarrativeInterchangeExport) -> str:
    """Render the typed narrative export payload as a minimal FCPXML document."""
    root = ET.Element("fcpxml", version="1.11")
    resources = ET.SubElement(root, "resources")
    ET.SubElement(
        resources,
        "format",
        id="fmt1",
        name="FFVideoFormat1080p24",
        frameDuration="100/2400s",
        width="1920",
        height="1080",
        colorSpace="1-1-1 (Rec. 709)",
    )

    library = ET.SubElement(root, "library")
    event = ET.SubElement(library, "event", name=payload.project_title)
    project = ET.SubElement(event, "project", name=payload.project_title)
    sequence = ET.SubElement(
        project,
        "sequence",
        format="fmt1",
        tcStart="0s",
        tcFormat="NDF",
        duration=format_fcpx_time(payload.total_duration_seconds),
    )
    spine = ET.SubElement(sequence, "spine")

    annotations_by_scene: dict[str, list[NarrativeAnnotation]] = defaultdict(list)
    for annotation in payload.annotations:
        annotations_by_scene[annotation.scene_id].append(annotation)

    for scene in payload.scenes:
        gap = ET.SubElement(
            spine,
            "gap",
            name=scene.heading,
            offset=format_fcpx_time(scene.start_seconds),
            start="0s",
            duration=format_fcpx_time(scene.duration_seconds),
        )
        for annotation in annotations_by_scene.get(scene.scene_id, []):
            relative_start = max(annotation.start_seconds - scene.start_seconds, 0.0)
            marker_attrs = {
                "start": format_fcpx_time(relative_start),
                "value": annotation.label,
            }
            note = _annotation_note(annotation)
            if note:
                marker_attrs["note"] = note
            ET.SubElement(gap, "marker", **marker_attrs)

    ET.indent(root, space="  ")
    xml_body = ET.tostring(root, encoding="unicode")
    return f"<?xml version='1.0' encoding='UTF-8'?>\n{xml_body}\n"


def format_fcpx_time(seconds: float) -> str:
    """Encode seconds using FCPXML rational-second syntax."""
    if seconds <= 0:
        return "0s"
    fraction = Fraction(seconds).limit_denominator(1000)
    if fraction.denominator == 1:
        return f"{fraction.numerator}s"
    return f"{fraction.numerator}/{fraction.denominator}s"


def _scene_annotations(
    *,
    segment: NarrativeSceneSegment,
    scene: Scene,
    index: int,
) -> list[NarrativeAnnotation]:
    annotations = [
        NarrativeAnnotation(
            annotation_id=f"{segment.scene_id}-boundary",
            kind="scene_boundary",
            scene_id=segment.scene_id,
            scene_ref=segment.scene_ref,
            start_seconds=segment.start_seconds,
            duration_seconds=segment.duration_seconds,
            end_seconds=segment.end_seconds,
            label=f"Scene {segment.scene_number}",
            note=(
                f"{scene.heading} | Edit {segment.edit_position} | "
                f"Story {segment.story_position}"
            ),
            color_label=_ANNOTATION_COLORS["scene_boundary"],
        )
    ]

    beats = list(scene.narrative_beats)
    for beat_index, beat in enumerate(beats):
        relative_offset = _even_offset(
            duration_seconds=segment.duration_seconds,
            index=beat_index,
            count=len(beats),
        )
        annotations.append(
            NarrativeAnnotation(
                annotation_id=f"{segment.scene_id}-beat-{beat_index + 1}",
                kind="beat",
                scene_id=segment.scene_id,
                scene_ref=segment.scene_ref,
                start_seconds=segment.start_seconds + relative_offset,
                duration_seconds=0.0,
                end_seconds=segment.start_seconds + relative_offset,
                label=f"Beat: {beat.beat_type}",
                note=f"{beat.description} ({beat.approximate_location})",
                color_label=_ANNOTATION_COLORS["beat"],
            )
        )

    emotional_notes: list[str] = []
    if scene.tone_mood:
        emotional_notes.append(f"Mood: {scene.tone_mood}")
    if scene.tone_shifts:
        emotional_notes.append(f"Shifts: {', '.join(scene.tone_shifts)}")
    if emotional_notes:
        emotional_offset = segment.duration_seconds * 0.5 if segment.duration_seconds > 0 else 0.0
        annotations.append(
            NarrativeAnnotation(
                annotation_id=f"{segment.scene_id}-emotion-{index + 1}",
                kind="emotional_note",
                scene_id=segment.scene_id,
                scene_ref=segment.scene_ref,
                start_seconds=segment.start_seconds + emotional_offset,
                duration_seconds=0.0,
                end_seconds=segment.start_seconds + emotional_offset,
                label=f"Emotion: {scene.tone_mood or 'Scene tone'}",
                note=" | ".join(emotional_notes),
                color_label=_ANNOTATION_COLORS["emotional_note"],
            )
        )
    return annotations


def _scene_duration_seconds(entry: TimelineEntry, scene: Scene) -> float:
    if entry.estimated_duration_seconds > 0:
        return entry.estimated_duration_seconds
    line_count = max(scene.source_span.end_line - scene.source_span.start_line + 1, 1)
    return float(max(line_count * 3, 1))


def _even_offset(*, duration_seconds: float, index: int, count: int) -> float:
    if duration_seconds <= 0 or count <= 0:
        return 0.0
    return duration_seconds * ((index + 1) / (count + 1))


def _annotation_sort_key(annotation: NarrativeAnnotation) -> tuple[float, str, str]:
    return (annotation.start_seconds, annotation.kind, annotation.label)


def _annotation_note(annotation: NarrativeAnnotation) -> str | None:
    details: list[str] = []
    if annotation.note:
        details.append(annotation.note)
    if annotation.kind == "scene_boundary":
        details.append(_scene_note_from_annotation(annotation))
    if annotation.color_label:
        details.append(f"Color label: {annotation.color_label}")
    return " | ".join(details) if details else None


def _scene_note(scene: NarrativeSceneSegment) -> str:
    character_summary = ", ".join(scene.characters_present) or "No cast metadata"
    return (
        f"{scene.heading} | {scene.int_ext} {scene.time_of_day} | "
        f"{scene.location} | Cast: {character_summary}"
    )


def _scene_note_from_annotation(annotation: NarrativeAnnotation) -> str:
    return f"Scene ref: {annotation.scene_ref.path}"


def _slug(value: str) -> str:
    return value.lower().replace(" ", "-").replace("/", "-")

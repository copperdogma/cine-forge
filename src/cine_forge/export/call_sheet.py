"""Call-sheet export assembly and PDF rendering."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from fpdf.fonts import FontFace

from cine_forge.export.pdf import PDFExporter, PDFGenerator


@dataclass(slots=True)
class CallSheetLogisticsField:
    label: str
    value: str


@dataclass(slots=True)
class CallSheetSceneRow:
    scene_number: int
    heading: str
    location: str
    time_of_day: str
    summary: str
    cast: str
    script_span: str


@dataclass(slots=True)
class CallSheetLocationRow:
    name: str
    scene_numbers: str
    notes: str


@dataclass(slots=True)
class CallSheetCastRow:
    character_name: str
    scenes: str
    notes: str


@dataclass(slots=True)
class CallSheetDocument:
    project_name: str
    generated_at: datetime
    draft_note: str
    logistics: list[CallSheetLogisticsField]
    locations: list[CallSheetLocationRow]
    schedule: list[CallSheetSceneRow]
    cast: list[CallSheetCastRow]


def build_call_sheet_document(
    *,
    project_name: str,
    scenes: list[dict[str, Any]],
    generated_at: datetime | None = None,
) -> CallSheetDocument:
    """Build a structured call-sheet view from the project data CineForge owns."""
    ordered_scenes = sorted(scenes, key=lambda item: item.get("scene_number") or 0)
    timestamp = generated_at or datetime.now(UTC)

    logistics = [
        CallSheetLogisticsField("General Call", _missing_logistics_value()),
        CallSheetLogisticsField("Shooting Call", _missing_logistics_value()),
        CallSheetLogisticsField("Lunch", _missing_logistics_value()),
        CallSheetLogisticsField("Weather", _missing_logistics_value()),
        CallSheetLogisticsField("Parking", _missing_logistics_value()),
        CallSheetLogisticsField("Nearest Hospital", _missing_logistics_value()),
        CallSheetLogisticsField("Crew Contacts", _missing_logistics_value()),
    ]

    location_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    cast_groups: dict[str, list[int]] = defaultdict(list)
    schedule_rows: list[CallSheetSceneRow] = []

    for scene in ordered_scenes:
        scene_number = int(scene.get("scene_number") or 0)
        location = str(scene.get("location") or "Unknown")
        time_of_day = str(scene.get("time_of_day") or "Unspecified")
        location_groups[location].append(scene)

        for character_name in scene.get("characters_present") or []:
            if scene_number not in cast_groups[character_name]:
                cast_groups[character_name].append(scene_number)

        schedule_rows.append(
            CallSheetSceneRow(
                scene_number=scene_number,
                heading=str(scene.get("heading") or "Unknown"),
                location=location,
                time_of_day=time_of_day,
                summary=_scene_summary(scene),
                cast=", ".join(scene.get("characters_present") or []) or "Not specified",
                script_span=_script_span(scene),
            )
        )

    locations = [
        CallSheetLocationRow(
            name=location,
            scene_numbers=", ".join(
                str(int(scene.get("scene_number") or 0))
                for scene in grouped_scenes
            ),
            notes=", ".join(
                sorted(
                    {
                        f"{scene.get('int_ext') or '?'} {scene.get('time_of_day') or 'UNSPECIFIED'}"
                        for scene in grouped_scenes
                    }
                )
            ),
        )
        for location, grouped_scenes in sorted(location_groups.items())
    ]

    cast_rows = [
        CallSheetCastRow(
            character_name=character_name,
            scenes=", ".join(str(number) for number in sorted(scene_numbers)),
            notes="Actor names, call times, and contact details are not stored in project data.",
        )
        for character_name, scene_numbers in sorted(cast_groups.items())
    ]

    return CallSheetDocument(
        project_name=project_name,
        generated_at=timestamp,
        draft_note=(
            "Planning-only call sheet. Operational logistics are not configured in this "
            "CineForge project yet, so the schedule below only reflects stored narrative data."
        ),
        logistics=logistics,
        locations=locations,
        schedule=schedule_rows,
        cast=cast_rows,
    )


def generate_call_sheet_pdf(
    *,
    project_name: str,
    scenes: list[dict[str, Any]],
    output_path: str,
    generated_at: datetime | None = None,
) -> None:
    """Render a call-sheet PDF that is honest about current substrate limits."""
    document = build_call_sheet_document(
        project_name=project_name,
        scenes=scenes,
        generated_at=generated_at,
    )
    helper = PDFGenerator()
    pdf = PDFExporter(header_title="CineForge Call Sheet")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("helvetica", "B", 24)
    pdf.cell(0, 12, helper.sanitize("CALL SHEET"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 9, helper.sanitize(document.project_name), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 10)
    pdf.cell(
        0,
        6,
        helper.sanitize(
            f"Generated {document.generated_at.astimezone().strftime('%Y-%m-%d %H:%M %Z')}"
        ),
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(3)

    _render_note_box(pdf, helper, title="Draft Status", body=document.draft_note)
    pdf.ln(3)

    _render_two_column_table(
        pdf,
        helper,
        title="Logistics Snapshot",
        headers=("Field", "Current Value"),
        rows=[(field.label, field.value) for field in document.logistics],
        col_widths=(48, 132),
    )
    pdf.ln(3)

    _render_two_column_table(
        pdf,
        helper,
        title="Locations",
        headers=("Location", "Scenes / Notes"),
        rows=[
            (
                row.name,
                f"Scenes {row.scene_numbers} | {row.notes or 'No location notes'}",
            )
            for row in document.locations
        ],
        col_widths=(48, 132),
    )
    pdf.ln(3)

    _render_schedule_table(pdf, helper, document.schedule)
    pdf.ln(3)

    _render_two_column_table(
        pdf,
        helper,
        title="Cast Presence",
        headers=("Character", "Scenes / Limits"),
        rows=[
            (
                row.character_name,
                f"Scenes {row.scenes} | {row.notes}",
            )
            for row in document.cast
        ]
        or [("No cast metadata", "Scene-level cast data is not available.")],
        col_widths=(42, 138),
    )

    pdf.output(output_path)


def _render_note_box(pdf: PDFExporter, helper: PDFGenerator, *, title: str, body: str) -> None:
    pdf.set_fill_color(245, 240, 224)
    pdf.set_draw_color(196, 167, 107)
    pdf.set_line_width(0.2)
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 8, helper.sanitize(title), border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 9)
    pdf.multi_cell(0, 5, helper.sanitize(body), border=1, new_x="LMARGIN", new_y="NEXT")


def _render_two_column_table(
    pdf: PDFExporter,
    helper: PDFGenerator,
    *,
    title: str,
    headers: tuple[str, str],
    rows: list[tuple[str, str]],
    col_widths: tuple[int, int],
) -> None:
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 9, helper.sanitize(title), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 9)
    with pdf.table(col_widths=col_widths, line_height=5) as table:
        table.row(
            [helper.sanitize(headers[0]), helper.sanitize(headers[1])],
            style=FontFace(emphasis="B"),
        )
        for left, right in rows:
            table.row([helper.sanitize(left), helper.sanitize(right)])


def _render_schedule_table(
    pdf: PDFExporter,
    helper: PDFGenerator,
    rows: list[CallSheetSceneRow],
) -> None:
    pdf.set_font("helvetica", "B", 14)
    pdf.cell(0, 9, helper.sanitize("Scene Schedule"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 8)
    with pdf.table(col_widths=(10, 44, 62, 38, 26), line_height=5) as table:
        table.row(
            ["Sc", "Heading", "Summary", "Cast", "Script"],
            style=FontFace(emphasis="B"),
        )
        for row in rows:
            heading = f"{row.heading} | {row.location} | {row.time_of_day}"
            table.row(
                [
                    helper.sanitize(str(row.scene_number)),
                    helper.sanitize(heading),
                    helper.sanitize(row.summary),
                    helper.sanitize(row.cast),
                    helper.sanitize(row.script_span),
                ]
            )


def _scene_summary(scene: dict[str, Any]) -> str:
    beats = scene.get("narrative_beats") or []
    beat_descriptions = [
        str(item.get("description") or "").strip()
        for item in beats
        if isinstance(item, dict) and item.get("description")
    ]
    if beat_descriptions:
        return " / ".join(beat_descriptions[:2])

    action_lines = [
        str(item.get("content") or "").strip()
        for item in scene.get("elements") or []
        if isinstance(item, dict) and item.get("element_type") == "action" and item.get("content")
    ]
    if action_lines:
        return " ".join(action_lines[:2])

    tone_mood = str(scene.get("tone_mood") or "").strip()
    if tone_mood:
        return f"Tone: {tone_mood}"
    return "Narrative summary unavailable."


def _script_span(scene: dict[str, Any]) -> str:
    span = scene.get("source_span") or {}
    start_line = span.get("start_line")
    end_line = span.get("end_line")
    if isinstance(start_line, int) and isinstance(end_line, int):
        return f"Lines {start_line}-{end_line}"
    return "Script span unavailable"


def _missing_logistics_value() -> str:
    return "Not specified in CineForge project data"

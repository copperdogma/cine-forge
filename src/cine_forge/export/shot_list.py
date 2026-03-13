"""Shot-list export helpers."""

from __future__ import annotations

import csv
import io
from typing import Any

from cine_forge.artifacts import ArtifactStore
from cine_forge.export.pdf import PDFExporter, PDFGenerator
from cine_forge.schemas import ArtifactRef, ShotPlan


def load_shot_plans(store: ArtifactStore) -> list[ShotPlan]:
    """Load the latest shot plan for every scene in the project."""
    plans: list[ShotPlan] = []
    for scene_id in sorted(store.list_entities("shot_plan")):
        refs = store.list_versions("shot_plan", scene_id)
        if not refs:
            continue
        artifact = store.load_artifact(refs[-1])
        plans.append(ShotPlan.model_validate(artifact.data))
    plans.sort(key=lambda plan: (plan.scene_number, plan.scene_id))
    return plans


def shot_list_rows(plans: list[ShotPlan]) -> list[dict[str, Any]]:
    """Flatten shot plans into CSV/table-friendly rows."""
    rows: list[dict[str, Any]] = []
    for plan in plans:
        for shot in plan.shots:
            rows.append(
                {
                    "scene_number": plan.scene_number,
                    "scene_heading": plan.scene_heading,
                    "shot_id": shot.shot_id,
                    "coverage_role": shot.coverage_role,
                    "shot_size": shot.shot_size,
                    "camera_angle": shot.camera_angle,
                    "camera_movement": shot.camera_movement,
                    "lens_focal_length": shot.lens_focal_length,
                    "characters_in_frame": ", ".join(shot.characters_in_frame),
                    "point_of_view_character": shot.point_of_view_character or "",
                    "blocking": shot.blocking,
                    "action_description": shot.action_description,
                    "dialogue_lines": " | ".join(shot.dialogue_lines),
                    "duration_estimate_seconds": shot.duration_estimate_seconds,
                    "edit_intent": shot.edit_intent,
                    "adequacy_verdict": plan.coverage_strategy.adequacy_check.verdict,
                }
            )
    return rows


def render_shot_list_csv(plans: list[ShotPlan]) -> str:
    """Render a CSV shot list for all scenes."""
    fieldnames = [
        "scene_number",
        "scene_heading",
        "shot_id",
        "coverage_role",
        "shot_size",
        "camera_angle",
        "camera_movement",
        "lens_focal_length",
        "characters_in_frame",
        "point_of_view_character",
        "blocking",
        "action_description",
        "dialogue_lines",
        "duration_estimate_seconds",
        "edit_intent",
        "adequacy_verdict",
    ]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in shot_list_rows(plans):
        writer.writerow(row)
    return output.getvalue()


def generate_shot_list_pdf(
    *,
    project_name: str,
    plans: list[ShotPlan],
    output_path: str,
) -> None:
    """Render a readable PDF shot list grouped by scene."""
    pdf = PDFExporter()
    helper = PDFGenerator()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("helvetica", "B", 22)
    pdf.cell(0, 14, helper.sanitize(project_name), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "", 12)
    pdf.cell(0, 8, "Shot List", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    for index, plan in enumerate(plans):
        if index > 0:
            pdf.add_page()
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(
            0,
            10,
            helper.sanitize(f"Scene {plan.scene_number} — {plan.scene_heading}"),
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.set_font("helvetica", "", 10)
        pdf.multi_cell(
            0,
            5,
            helper.sanitize(
                f"Coverage approach: {plan.coverage_strategy.coverage_approach}\n"
                f"Adequacy: {plan.coverage_strategy.adequacy_check.verdict} — "
                f"{plan.coverage_strategy.adequacy_check.rationale}"
            ),
            new_x="LMARGIN",
            new_y="NEXT",
        )
        pdf.ln(2)

        rows = [["Shot", "Role", "Size", "Move", "Dur", "In Frame"]]
        for shot in plan.shots:
            rows.append(
                [
                    helper.sanitize(shot.shot_id),
                    helper.sanitize(shot.coverage_role),
                    helper.sanitize(shot.shot_size),
                    helper.sanitize(shot.camera_movement),
                    helper.sanitize(f"{shot.duration_estimate_seconds:.1f}s"),
                    helper.sanitize(", ".join(shot.characters_in_frame) or "-"),
                ]
            )
        with pdf.table(col_widths=(22, 32, 38, 36, 16, 46)) as table:
            for row in rows:
                row_cells = table.row()
                for item in row:
                    row_cells.cell(item)

        pdf.ln(4)
        for shot in plan.shots:
            pdf.set_font("helvetica", "B", 11)
            pdf.cell(
                0,
                7,
                helper.sanitize(
                    f"{shot.shot_id} · {shot.camera_angle} · {shot.lens_focal_length}"
                ),
                new_x="LMARGIN",
                new_y="NEXT",
            )
            pdf.set_font("helvetica", "", 9)
            pdf.multi_cell(
                0,
                4,
                helper.sanitize(
                    f"Blocking: {shot.blocking}\n"
                    f"Action: {shot.action_description}\n"
                    f"Edit intent: {shot.edit_intent}\n"
                    f"Dialogue: {' | '.join(shot.dialogue_lines) or '—'}"
                ),
                new_x="LMARGIN",
                new_y="NEXT",
            )
            pdf.ln(1)

    pdf.output(output_path)


def shot_plan_ref_map(store: ArtifactStore) -> dict[str, ArtifactRef]:
    """Return latest shot-plan refs keyed by scene_id."""
    refs: dict[str, ArtifactRef] = {}
    for scene_id in store.list_entities("shot_plan"):
        versions = store.list_versions("shot_plan", scene_id)
        if versions:
            refs[scene_id] = versions[-1]
    return refs

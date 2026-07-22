from __future__ import annotations

import pytest

from cine_forge.modules.ingest.story_ingest_v1.pdf_layout import (
    normalize_pdf_layout_text,
    normalize_pdf_layout_text_with_diagnostics,
)


@pytest.mark.unit
def test_pdf_layout_reflows_dual_dialogue_in_speaker_order() -> None:
    extracted = """
                           STEEL
               I warned you before.

                           BRICK
               I heard you.

               The men look at each other.

                           STEEL                          BRICK
               Screw retirement.              Screw retirement.

                                                          SMASH CUT TO:
    """

    normalized, diagnostics = normalize_pdf_layout_text_with_diagnostics(extracted)

    assert "STEEL\nScrew retirement.\n\nBRICK ^\nScrew retirement." in normalized
    assert normalized.index("STEEL") < normalized.index("BRICK ^")
    assert "SMASH CUT TO:" in normalized
    assert diagnostics["dual_dialogue_reflow_count"] == 1


@pytest.mark.unit
def test_pdf_layout_does_not_reflow_unbalanced_uppercase_columns() -> None:
    extracted = """
                           LEFT                           RIGHT
               Only the left column has text.

               Ordinary action follows.
    """

    normalized = normalize_pdf_layout_text(extracted)

    assert "LEFT RIGHT" in normalized
    assert "RIGHT ^" not in normalized


@pytest.mark.unit
def test_pdf_layout_does_not_reflow_balanced_non_dialogue_table() -> None:
    extracted = """
                           DATE                           LOCATION
               MONDAY                         STUDIO
               TUESDAY                        WATER TOWER

               Ordinary action follows.
    """

    normalized, diagnostics = normalize_pdf_layout_text_with_diagnostics(extracted)

    assert "DATE LOCATION" in normalized
    assert "MONDAY STUDIO" in normalized
    assert "TUESDAY WATER TOWER" in normalized
    assert "LOCATION ^" not in normalized
    assert diagnostics["dual_dialogue_reflow_count"] == 0


@pytest.mark.unit
@pytest.mark.parametrize(
    ("header", "rows"),
    [
        (
            "                           REQUIREMENT                    STATUS",
            [
                "               Source screenplay retained.   Approved for review.",
                "               Output schema verified.        Ready for use.",
            ],
        ),
        (
            "                           NAME                           ROLE",
            [
                "               Alice Johnson                  Director of photography",
                "               Morgan Lee                     Production designer",
            ],
        ),
    ],
)
def test_pdf_layout_does_not_reflow_sentence_case_tables(
    header: str,
    rows: list[str],
) -> None:
    extracted = "\n".join([header, *rows])

    normalized, diagnostics = normalize_pdf_layout_text_with_diagnostics(extracted)

    assert " ^" not in normalized
    assert diagnostics["dual_dialogue_reflow_count"] == 0


@pytest.mark.unit
def test_pdf_layout_stops_dual_dialogue_before_unspaced_story_boundary() -> None:
    extracted = """
                           STEEL
               I warned you before.
                           BRICK
               I heard you.
               The men look at each other.
                           STEEL                          BRICK
               Screw retirement.              Screw retirement.
                                                          SMASH CUT TO:
               EXT. ROAD - NIGHT
    """

    normalized, diagnostics = normalize_pdf_layout_text_with_diagnostics(extracted)

    assert "STEEL\nScrew retirement.\n\nBRICK ^\nScrew retirement." in normalized
    assert "SMASH CUT TO:\nEXT. ROAD - NIGHT" in normalized
    assert normalized.index("BRICK ^") < normalized.index("SMASH CUT TO:")
    assert diagnostics["dual_dialogue_reflow_count"] == 1


@pytest.mark.unit
def test_pdf_layout_preserves_unknown_uppercase_table_inside_screenplay_context() -> None:
    extracted = """
               INT. OFFICE - DAY

               The coordinator reviews the report.

                           SUBJECT                        NOTES
               Permit status                  Awaiting municipal response.
               Location access                Owner has not replied.
    """

    normalized, diagnostics = normalize_pdf_layout_text_with_diagnostics(extracted)

    assert "SUBJECT NOTES" in normalized
    assert "NOTES ^" not in normalized
    assert diagnostics["dual_dialogue_reflow_count"] == 0

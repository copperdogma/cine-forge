from __future__ import annotations

from types import SimpleNamespace

import pytest

from cine_forge.modules.visualization.storyboard_v1.grid import (
    GRID_PROMPT_MAX_CHARS,
    StoryboardGridLayout,
    build_grid_prompt,
)


@pytest.mark.unit
def test_build_grid_prompt_compacts_long_beat_template_context() -> None:
    layout = StoryboardGridLayout(columns=3, rows=3, size="1536x1024", panel_count=9)
    scene = SimpleNamespace(heading="INT. COMMUNITY RADIO STUDIO - NIGHT")
    repeated_identity = (
        "ARIA has a practical technical silhouette, stable face, work jacket, "
        "headset, rain-darkened sleeves, and focused posture. "
        "NOAH has a lean console-operator silhouette, short hair, neutral layers, "
        "and a calm alert expression. "
        "JUNE has a no-nonsense radio-operator silhouette, functional sweater, "
        "simple watch, and weathered capable expression. "
        "KELL has a field-repair silhouette, portable antenna, canvas tool bag, "
        "lantern, boots, and urgent storm posture. "
    )
    beats = [
        f"Beat {index} of 9 / shot S{index}: advance the scene. {repeated_identity * 3}"
        for index in range(1, 10)
    ]
    panel_briefs = [
        (
            f"Setting: storm-battered radio studio. Characters: Aria, Noah, June, "
            f"Kell. Blocking: panel {index} keeps the emergency broadcast visible. "
            f"{repeated_identity * 4}"
        )
        for index in range(1, 10)
    ]

    prompt = build_grid_prompt(
        scene=scene,
        style="sketch",
        style_instruction="Black-and-white production storyboard drawing.",
        layout=layout,
        panel_briefs=panel_briefs,
        shot_ids=[f"S{index}" for index in range(1, 10)],
        uses_template_reference=True,
        ordered_story_beats=beats,
    )

    assert len(prompt) <= GRID_PROMPT_MAX_CHARS
    assert "Ordered scene beat router:" in prompt
    assert "Beat 9 of 9 / shot S9" in prompt
    assert "Panel 9 / shot S9:" in prompt
    assert "Do not add panel numbers" in prompt


@pytest.mark.unit
def test_build_grid_prompt_includes_reference_anchors_without_drawing_refs() -> None:
    layout = StoryboardGridLayout(columns=2, rows=2, size="1536x1024", panel_count=2)
    scene = SimpleNamespace(heading="INT. LAB - NIGHT")

    prompt = build_grid_prompt(
        scene=scene,
        style="sketch",
        style_instruction="Black-and-white production storyboard drawing.",
        layout=layout,
        panel_briefs=[
            "MARA studies the console in the lab.",
            "OWEN turns toward the monitor bank.",
        ],
        shot_ids=["S1", "S2"],
        uses_template_reference=True,
        reference_anchor_lines=[
            (
                "- MARA: use mara_ref.jpg as the canonical off-canvas character "
                "reference for panels 1-2. Preserve face, hair, build, and wardrobe."
            )
        ],
    )

    assert len(prompt) <= GRID_PROMPT_MAX_CHARS
    assert "Reference-image anchors:" in prompt
    assert "mara_ref.jpg" in prompt
    assert "do not draw the reference cards" in prompt
    assert "Panel briefs:" in prompt

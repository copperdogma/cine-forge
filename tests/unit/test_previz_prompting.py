from __future__ import annotations

import pytest

from cine_forge.modules.generation.render_adapter_v1.previz_prompting import (
    compile_low_fidelity_previz_prompt,
    low_fidelity_previz_profile,
    shot_brief_from_target,
)
from cine_forge.modules.generation.render_adapter_v1.support import load_engine_pack


@pytest.mark.unit
def test_shot_brief_from_target_preserves_core_fields() -> None:
    brief = shot_brief_from_target(
        target={
            "clip_id": "dialogue_confession_push_in",
            "title": "Dialogue confession push-in",
            "summary_reference": "A cool blue two-shot pushes toward a confession.",
            "transcript": "I should have told you before the train left.",
            "audio_description": "Soft piano under the line.",
            "tone_tags": ["intimate", "regretful"],
            "color_tags": ["navy", "teal"],
            "camera_tags": ["locked_two_shot", "slow_push_in"],
            "motion_tags": ["measured"],
            "continuity_notes": ["The envelope stays with Subject B."],
            "clip_tags": ["dialogue"],
        },
        meta={},
        character_labels=["Subject A", "Subject B"],
    )

    assert brief.clip_id == "dialogue_confession_push_in"
    assert brief.character_labels == ["Subject A", "Subject B"]
    assert brief.camera_tags == ["locked_two_shot", "slow_push_in"]


@pytest.mark.unit
def test_compile_low_fidelity_previz_prompt_builds_non_final_house_style() -> None:
    pack = load_engine_pack("openai_sora2")
    brief = shot_brief_from_target(
        target={
            "clip_id": "radio_hold_tracking",
            "title": "Radio hold tracking",
            "summary_reference": (
                "A lateral tracking move follows two officers along a blue corridor."
            ),
            "transcript": "Unit three, hold position until the lights settle.",
            "audio_description": "A dry radio dispatch over light room tone.",
            "tone_tags": ["urgent"],
            "color_tags": ["navy", "teal"],
            "camera_tags": ["lateral_track"],
            "motion_tags": ["measured"],
            "continuity_notes": ["The amber flashlight stays with the lead officer."],
            "clip_tags": ["procedural"],
        },
        meta={},
        character_labels=["Lead Officer", "Support Officer"],
    )

    contract = compile_low_fidelity_previz_prompt(brief=brief, engine_pack=pack)

    assert contract.target_engine_pack_id == "openai_sora2"
    assert contract.consistency_strategy == "prompt_only"
    assert contract.style_profile.profile_id == "cineforge_low_fidelity_previz_v1"
    assert "This is previs, not a final render." in contract.prompt_text
    assert "Lead Officer, Support Officer" in contract.prompt_text
    assert "Track laterally" in contract.prompt_text
    assert "Suppress distracting detail" in contract.prompt_text
    assert "final-render finish" in contract.negative_prompt_terms


@pytest.mark.unit
def test_compile_low_fidelity_previz_prompt_respects_engine_prompt_budget() -> None:
    pack = load_engine_pack("xai_grok_imagine_video")
    brief = shot_brief_from_target(
        target={
            "clip_id": "radio_hold_tracking",
            "title": "Radio hold tracking",
            "summary_reference": (
                "INT. COMMUNITY RADIO STUDIO. Master-driven with character-specific close-ups "
                "on hands and faces. Establish the studio space and three-person dynamic in a "
                "wide shot, then isolate each character's preparation ritual in tight framings "
                "that emphasize focus and vulnerability. "
                + "Quiet competence and weather pressure should remain readable. " * 18
            ),
            "transcript": (
                "JUNE: If this works, half the valley hears us. "
                "NOAH: If this works, we hear them too. "
                "ARIA: Then we stop talking and start listening. "
            )
            * 8,
            "audio_description": (
                "Cramped studio room tone with rain on skylight, old electrical hum, "
                "floorboard creaks, and shrinking interior focus as the ON AIR light becomes "
                "the emotional center. "
            )
            * 12,
            "tone_tags": ["resilient", "intimate", "purposeful", "tender"],
            "color_tags": [
                "Cool-to-warm tension from skylight blue-greys against amber desk lamp glow"
            ]
            * 6,
            "camera_tags": ["wide_master"],
            "motion_tags": ["measured"],
            "continuity_notes": [
                "ARIA at tape machine frame left, NOAH at mixer frame center-right, JUNE entering "
                "with mugs frame right; preserve geography and prop positions."
            ]
            * 4,
            "clip_tags": ["procedural"],
        },
        meta={},
        character_labels=["ARIA", "NOAH", "JUNE"],
    )

    contract = compile_low_fidelity_previz_prompt(brief=brief, engine_pack=pack)

    assert len(contract.prompt_text) <= pack.request_defaults["max_prompt_chars"]
    assert "This is previs, not a final render." in contract.prompt_text
    assert "Characters to keep distinct: ARIA, NOAH, JUNE." in contract.prompt_text
    assert "Engine guidance:" in contract.prompt_text


@pytest.mark.unit
def test_low_fidelity_profile_returns_copy() -> None:
    first = low_fidelity_previz_profile()
    second = low_fidelity_previz_profile()

    assert first == second
    assert first is not second

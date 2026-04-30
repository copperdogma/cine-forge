from __future__ import annotations

import pytest

from cine_forge.modules.generation.render_adapter_v1.previz_prompting import (
    compile_low_fidelity_previz_prompt,
    compile_scene_previz_prompt,
    low_fidelity_previz_profile,
    shot_brief_from_target,
)
from cine_forge.modules.generation.render_adapter_v1.support import load_engine_pack
from cine_forge.schemas import (
    ArtifactRef,
    CoverageAdequacyCheck,
    CoverageStrategy,
    PlanningAudit,
    RenderClip,
    Scene,
    ShotDefinition,
    ShotPlan,
    SourceSpan,
)


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
    assert "Dialogue lock:" in contract.prompt_text
    assert "Unit three, hold position until the lights settle." in contract.prompt_text
    assert "Do not add, paraphrase, repeat" in contract.prompt_text
    assert "Suppress distracting detail" in contract.prompt_text
    assert "final-render finish" in contract.negative_prompt_terms
    assert "improvised dialogue" in contract.negative_prompt_terms


@pytest.mark.unit
def test_compile_low_fidelity_previz_prompt_compact_profile_stays_shorter() -> None:
    pack = load_engine_pack("google_veo31_lite")
    brief = shot_brief_from_target(
        target={
            "clip_id": "dialogue_confession_push_in",
            "title": "Dialogue confession push-in",
            "summary_reference": (
                "A cool blue two-shot pushes toward a confession while the envelope stays "
                "visible between them and the room remains readable."
            ),
            "transcript": "I should have told you before the train left.",
            "audio_description": "Soft piano under the line with minimal room tone.",
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

    standard = compile_low_fidelity_previz_prompt(brief=brief, engine_pack=pack)
    compact = compile_low_fidelity_previz_prompt(
        brief=brief,
        engine_pack=pack,
        prompt_profile="compact",
    )

    assert standard.prompt_profile == "standard"
    assert compact.prompt_profile == "compact"
    assert len(compact.prompt_text) < len(standard.prompt_text)
    assert "This is previs, not a final render." in compact.prompt_text
    assert "Dialogue lock:" in compact.prompt_text
    assert "Characters: Subject A, Subject B." in compact.prompt_text
    assert "Avoid photoreal polish" in compact.prompt_text


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
    assert len(contract.prompt_text.encode("utf-8")) <= pack.request_defaults["max_prompt_chars"]
    assert "This is previs, not a final render." in contract.prompt_text
    assert "Characters to keep distinct: ARIA, NOAH, JUNE." in contract.prompt_text
    assert "Engine guidance:" in contract.prompt_text


@pytest.mark.unit
def test_compile_low_fidelity_previz_prompt_budget_counts_utf8_bytes() -> None:
    pack = load_engine_pack("xai_grok_imagine_video")
    brief = shot_brief_from_target(
        target={
            "clip_id": "final_reversal_single",
            "title": "Final reversal single",
            "summary_reference": (
                "Steel absorbs Brick's line — then smiles — then answers with the matching "
                "retirement reversal. "
                + "The patio stays gorgeous, indifferent, and brutally still — " * 90
            ),
            "transcript": "STEEL: Screw retirement.",
            "audio_description": (
                "Suburban ambience thins — cicadas, sprinkler ticks, lawnmower fading — "
                "until the cut snaps the world off. "
            )
            * 40,
            "tone_tags": ["deadpan", "suspended", "dry", "resigned"],
            "color_tags": ["sunlit green — faded khaki — warm amber"] * 24,
            "camera_tags": ["profile_closeup"],
            "motion_tags": ["stillness"],
            "continuity_notes": [
                "Mirror Brick's prior single — same patio geography, same beer positions."
            ]
            * 24,
            "clip_tags": ["dialogue"],
        },
        meta={},
        character_labels=["BRICK BRADDOCK", "DICK STEEL"],
    )

    contract = compile_low_fidelity_previz_prompt(brief=brief, engine_pack=pack)

    assert len(contract.prompt_text.encode("utf-8")) <= pack.request_defaults["max_prompt_chars"]
    assert "STEEL: Screw retirement." in contract.prompt_text


@pytest.mark.unit
def test_compile_scene_previz_prompt_summarizes_full_shot_sequence() -> None:
    scene_ref = ArtifactRef(
        artifact_type="scene",
        entity_id="scene_001",
        version=1,
        path="artifacts/scene/scene_001/v1.json",
    )
    audit = PlanningAudit(
        intent="test",
        rationale="test",
        confidence=0.9,
        source="ai",
    )
    plan = ShotPlan(
        scene_id="scene_001",
        scene_number=1,
        scene_heading="EXT. PATIO - DAY",
        scene_ref=scene_ref,
        coverage_strategy=CoverageStrategy(
            coverage_approach="Wide master, two-shot, then singles.",
            rhythm_and_flow_intent="Let the silence stretch.",
            look_and_feel_intent="Bright suburban stillness.",
            sound_and_music_intent="Sparse backyard ambience.",
            character_and_performance_notes="Both men are still and resigned.",
            adequacy_check=CoverageAdequacyCheck(rationale="Cuttable."),
            audit=audit,
        ),
        shots=[
            ShotDefinition(
                scene_id="scene_001",
                shot_id="scene_001_shot_01",
                shot_size="Wide / Full Shot",
                camera_angle="Eye level",
                camera_movement="Locked off",
                lens_focal_length="32mm",
                coverage_role="Establishing master",
                characters_in_frame=["BRICK", "STEEL"],
                blocking="Steel enters through the screen door and crosses to Brick.",
                action_description="Beer handoff and opening joke.",
                dialogue_lines=["Beer's ready!", "Are they cold?"],
                duration_estimate_seconds=12,
                edit_intent="Hold the patio geography.",
                audit=audit,
            ),
            ShotDefinition(
                scene_id="scene_001",
                shot_id="scene_001_shot_02",
                shot_size="Medium Two-Shot",
                camera_angle="Eye level",
                camera_movement="Locked off with slight drift",
                lens_focal_length="50mm",
                coverage_role="Primary two-shot",
                characters_in_frame=["BRICK", "STEEL"],
                blocking="Both men toast, then sit in silence.",
                action_description="Long uncomfortable beat after the toast.",
                dialogue_lines=["To retirement.", "Screw retirement."],
                duration_estimate_seconds=18,
                edit_intent="Let the long beat land.",
                audit=audit,
            ),
            ShotDefinition(
                scene_id="scene_001",
                shot_id="scene_001_shot_03",
                shot_size="Medium Close-Up",
                camera_angle="Over the shoulder",
                camera_movement="Locked off",
                lens_focal_length="85mm",
                coverage_role="Brick reaction single",
                characters_in_frame=["BRICK"],
                blocking="Brick absorbs Steel's line before answering.",
                action_description="Brick confirms the emotional turn.",
                dialogue_lines=["Screw retirement."],
                duration_estimate_seconds=8,
                edit_intent="Use as the emotional confirmation.",
                audit=audit,
            ),
        ],
        total_estimated_duration_seconds=38,
    )
    scene = Scene(
        scene_id="scene_001",
        scene_number=1,
        heading="EXT. PATIO - DAY",
        location="PATio",
        time_of_day="DAY",
        int_ext="EXT",
        characters_present=["BRICK", "STEEL"],
        tone_mood="deadpan",
        source_span=SourceSpan(start_line=1, end_line=10),
        confidence=0.9,
    )

    contract, sections, _, _ = compile_scene_previz_prompt(
        scene=scene,
        plan=plan,
        source_maps={},
        resolved_inputs=[],
        engine_pack=load_engine_pack("openai_sora2"),
    )

    assert "Shot 1:" in contract.prompt_text
    assert "Shot 2:" in contract.prompt_text
    assert "Shot 3:" in contract.prompt_text
    assert "Screw retirement." in contract.prompt_text
    assert "Beer handoff and opening joke." in contract.prompt_text
    assert "Long uncomfortable beat after the toast." in contract.prompt_text
    shot_brief = next(section for section in sections if section.section_id == "shot_brief")
    assert "Shot 3:" in shot_brief.body

    silent_clip = RenderClip(
        clip_id="scene_001_clip_001",
        scene_id="scene_001",
        source_shot_ids=["scene_001_shot_01"],
        start_time_seconds=0.0,
        end_time_seconds=8.0,
        target_duration_seconds=8.0,
        dialogue_lines=[],
        action_beats=["Steel enters silently with the beers."],
        derivation="shot_plan",
        rationale="Silent setup beat.",
        confidence=0.8,
    )
    silent_contract, silent_sections, _, _ = compile_scene_previz_prompt(
        scene=scene,
        plan=plan.model_copy(update={"shots": [plan.shots[0]]}),
        render_clip=silent_clip,
        source_maps={},
        resolved_inputs=[],
        engine_pack=load_engine_pack("openai_sora2"),
    )
    assert "Beer's ready!" not in silent_contract.prompt_text
    assert "Dialogue lock: this clip has no scripted spoken dialogue" in silent_contract.prompt_text
    assert "Characters must stay silent" in silent_contract.prompt_text
    assert "no mouth-synced speech" in silent_contract.prompt_text
    assert not any(section.section_id == "dialogue" for section in silent_sections)
    silent_dialogue_lock = next(
        section for section in silent_sections if section.section_id == "dialogue_lock"
    )
    assert "no scripted spoken dialogue" in silent_dialogue_lock.body

    toast_clip = silent_clip.model_copy(
        update={
            "clip_id": "scene_001_clip_002",
            "dialogue_lines": ["STEEL: To retirement."],
            "action_beats": ["Steel raises his beer and says 'To retirement.'"],
            "rationale": "Toast beat.",
        }
    )
    toast_contract, _, _, _ = compile_scene_previz_prompt(
        scene=scene,
        plan=plan.model_copy(update={"shots": [plan.shots[1]]}),
        render_clip=toast_clip,
        source_maps={},
        resolved_inputs=[],
        engine_pack=load_engine_pack("openai_sora2"),
    )
    assert toast_contract.prompt_text.count("To retirement") == 1
    assert "the planned dialogue line" in toast_contract.prompt_text
    assert "only spoken words permitted" in toast_contract.prompt_text
    assert "Do not add, paraphrase, repeat" in toast_contract.prompt_text


@pytest.mark.unit
def test_low_fidelity_profile_returns_copy() -> None:
    first = low_fidelity_previz_profile()
    second = low_fidelity_previz_profile()

    assert first == second
    assert first is not second

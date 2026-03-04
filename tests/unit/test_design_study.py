"""Unit tests for the Design Study schemas and image prompt synthesis."""

import pytest

from cine_forge.ai.image import synthesize_image_prompt
from cine_forge.schemas.design_study import (
    DesignStudyImage,
    DesignStudyRound,
    DesignStudyState,
)

# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_design_study_state_starts_empty():
    state = DesignStudyState(entity_id="character_mariner", entity_type="character")
    assert state.rounds == []
    assert state.selected_final_filename is None
    assert state.thumbnail_filename() is None


@pytest.mark.unit
def test_thumbnail_returns_selected_final():
    state = DesignStudyState(
        entity_id="character_mariner",
        entity_type="character",
        selected_final_filename="design_study_r1_img1.jpg",
    )
    assert state.thumbnail_filename() == "design_study_r1_img1.jpg"


@pytest.mark.unit
def test_thumbnail_falls_back_to_latest_favorite():
    img_fav = DesignStudyImage(
        filename="design_study_r1_img1.jpg",
        decision="favorite",
        prompt_used="test",
        model="imagen-4.0-generate-001",
        round_number=1,
    )
    img_pending = DesignStudyImage(
        filename="design_study_r2_img1.jpg",
        decision="pending",
        prompt_used="test",
        model="imagen-4.0-generate-001",
        round_number=2,
    )
    round1 = DesignStudyRound(
        round_number=1,
        prompt="test",
        model="imagen-4.0-generate-001",
        entity_type="character",
        entity_id="character_mariner",
        images=[img_fav],
    )
    round2 = DesignStudyRound(
        round_number=2,
        prompt="test",
        model="imagen-4.0-generate-001",
        entity_type="character",
        entity_id="character_mariner",
        images=[img_pending],
    )
    state = DesignStudyState(
        entity_id="character_mariner",
        entity_type="character",
        rounds=[round1, round2],
    )
    # latest_favorite traverses all_images (newest first) → img_pending is pending,
    # img_fav is favorite — so favorite wins
    assert state.thumbnail_filename() == "design_study_r1_img1.jpg"


@pytest.mark.unit
def test_selected_final_supersedes_favorite():
    img = DesignStudyImage(
        filename="design_study_r1_img1.jpg",
        decision="favorite",
        prompt_used="test",
        model="imagen-4.0-generate-001",
        round_number=1,
    )
    round1 = DesignStudyRound(
        round_number=1,
        prompt="test",
        model="imagen-4.0-generate-001",
        entity_type="character",
        entity_id="character_mariner",
        images=[img],
    )
    state = DesignStudyState(
        entity_id="character_mariner",
        entity_type="character",
        rounds=[round1],
        selected_final_filename="design_study_r2_img1.jpg",
    )
    assert state.thumbnail_filename() == "design_study_r2_img1.jpg"


@pytest.mark.unit
def test_all_images_newest_first():
    img1 = DesignStudyImage(
        filename="r1.jpg", decision="pending", prompt_used="p", model="m", round_number=1
    )
    img2 = DesignStudyImage(
        filename="r2.jpg", decision="pending", prompt_used="p", model="m", round_number=2
    )
    round1 = DesignStudyRound(
        round_number=1, prompt="p", model="m",
        entity_type="character", entity_id="test", images=[img1],
    )
    round2 = DesignStudyRound(
        round_number=2, prompt="p", model="m",
        entity_type="character", entity_id="test", images=[img2],
    )
    state = DesignStudyState(
        entity_id="test", entity_type="character", rounds=[round1, round2]
    )
    all_imgs = state.all_images()
    assert all_imgs[0].filename == "r2.jpg"
    assert all_imgs[1].filename == "r1.jpg"


# ---------------------------------------------------------------------------
# Prompt synthesis tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
def test_synthesize_character_prompt():
    bible = {
        "name": "The Mariner",
        "description": "A grizzled old sailor.",
        "narrative_role": "protagonist",
        "scene_presence": ["s01", "s02"],
        "inferred_traits": [
            {"trait": "build", "value": "broad-shouldered"},
            {"trait": "age", "value": "late 60s"},
        ],
    }
    prompt = synthesize_image_prompt("character", bible)
    assert "The Mariner" in prompt
    assert "protagonist" in prompt
    assert "broad-shouldered" in prompt
    assert "cinematic" in prompt.lower()
    assert len(prompt) > 50


@pytest.mark.unit
def test_synthesize_location_prompt():
    bible = {
        "name": "The Harbour",
        "description": "A fog-shrouded Victorian harbour.",
        "physical_traits": ["stone pier", "rusting mooring rings"],
        "narrative_significance": "The world he cannot return to",
    }
    prompt = synthesize_image_prompt("location", bible)
    assert "The Harbour" in prompt
    assert "stone pier" in prompt
    assert "establishing shot" in prompt.lower()
    assert len(prompt) > 50


@pytest.mark.unit
def test_synthesize_prop_prompt():
    bible = {
        "name": "The Oar",
        "description": "A heavy oak oar, salt-bleached.",
        "narrative_significance": "Symbol of the sea",
        "associated_characters": ["the_mariner"],
    }
    prompt = synthesize_image_prompt("prop", bible)
    assert "The Oar" in prompt
    assert "Symbol of the sea" in prompt
    assert "prop" in prompt.lower()
    assert len(prompt) > 50


@pytest.mark.unit
def test_synthesize_prompt_handles_missing_fields():
    """synthesize_image_prompt should not crash on sparse bible data."""
    prompt = synthesize_image_prompt("character", {"name": "Bob"})
    assert "Bob" in prompt
    assert len(prompt) > 0

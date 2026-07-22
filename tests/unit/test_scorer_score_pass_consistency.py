from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from tests.unit import test_bible_extraction_scorer as bible
from tests.unit import test_character_extraction_scorer as character
from tests.unit import test_config_detection_scorer as config
from tests.unit import test_continuity_extraction_scorer as continuity
from tests.unit import test_entity_discovery_scorer as entity
from tests.unit import test_normalization_scorer as normalization
from tests.unit import test_qa_pass_scorer as qa
from tests.unit import test_relationship_scorer as relationship
from tests.unit import test_scene_enrichment_scorer as enrichment
from tests.unit import test_scene_extraction_scorer as scene_extraction
from tests.unit import test_script_bible_scorer as script_bible
from tests.unit import test_storyboard_understanding_benchmark as storyboard
from tests.unit import test_video_understanding_scorer_adversarial as video


def _hard_gate_results(tmp_path: Path) -> list[tuple[str, object, dict]]:
    bible_output = bible._location(aliases=["LOWER LAB", "BASEMENT"])

    character_output = character._control()
    character_output["prominence"] = "primary"

    config_output = config._control()
    config_output["invented_field"] = "padding"

    continuity_output = deepcopy(continuity._control())
    continuity_output["entity_states"].append(
        deepcopy(continuity_output["entity_states"][0])
    )

    entity_output = {
        "characters": ["ALICE"],
        "locations": ["LAB"],
        "props": ["KEY"],
        "bonus": ["INVENTED DRAGON"],
    }

    source = normalization.BROKEN_FOUNTAIN_SOURCE.read_text()
    normalized = normalization._mechanically_clean_broken_fountain(source)
    first_action = (
        "A cramped studio hums with old gear. Rain taps the skylight in steady rhythm."
    )
    second_action = (
        "aria threads a tape reel while noah checks a cracked mixer. "
        "june balances two mugs of tea on a stack of scripts."
    )
    normalization_output = normalized.replace(
        f"{first_action}\n{second_action}",
        f"{second_action}\n{first_action}",
    )
    normalization_context = {
        "vars": {
            "golden_path": str(normalization.SIGNAL_GOLDEN),
            "source_text": source,
        }
    }

    qa_output = {
        "passed": True,
        "issues": [],
        "confidence": 0.9,
        "summary": "The extraction is source grounded and complete.",
        "extra": "forbidden",
    }

    relationship_output = {
        "edges": [relationship._edge(), deepcopy(relationship._edge())]
    }

    enrichment_output = enrichment._control()
    enrichment_output["extra"] = "forbidden"

    scene_output = scene_extraction._payload(extra="forbidden")

    script_output = script_bible._control()
    script_output["extra"] = "forbidden"

    storyboard_target = storyboard._write_target(tmp_path, "sbq_case_002")
    storyboard_output = storyboard.good_analysis(case_id="sbq_case_002")
    storyboard_output["packet_reference_count"] = 3

    video_output = video._perfect_prediction()
    video_output["clip_id"] = "another_clip"

    return [
        (
            "bible_extraction_scorer",
            bible.scorer,
            bible.scorer.get_assert(
                json.dumps(bible_output),
                bible._context(
                    tmp_path,
                    bible._location_golden(),
                    location_name="REACTOR LAB",
                ),
            ),
        ),
        (
            "character_extraction_scorer",
            character.scorer,
            character.scorer.get_assert(
                json.dumps(character_output),
                character._context(tmp_path),
            ),
        ),
        (
            "config_detection_scorer",
            config.scorer,
            config.scorer.get_assert(
                json.dumps(config_output),
                config._context(tmp_path),
            ),
        ),
        (
            "continuity_extraction_scorer",
            continuity.scorer,
            continuity.scorer.get_assert(
                json.dumps(continuity_output),
                continuity._context(tmp_path),
            ),
        ),
        (
            "entity_discovery_scorer",
            entity.scorer,
            entity.scorer.get_assert(
                json.dumps(entity_output),
                entity._context(tmp_path),
            ),
        ),
        (
            "normalization_scorer",
            normalization.scorer,
            normalization.scorer.get_assert(
                normalization_output,
                normalization_context,
            ),
        ),
        (
            "qa_pass_scorer",
            qa.scorer,
            qa.scorer.get_assert(
                json.dumps(qa_output),
                qa._context(tmp_path, "good"),
            ),
        ),
        (
            "relationship_scorer",
            relationship.scorer,
            relationship.scorer.get_assert(
                json.dumps(relationship_output),
                relationship._context(tmp_path),
            ),
        ),
        (
            "scene_enrichment_scorer",
            enrichment.scorer,
            enrichment.scorer.get_assert(
                json.dumps(enrichment_output),
                enrichment._context(tmp_path),
            ),
        ),
        (
            "scene_extraction_scorer",
            scene_extraction.scorer,
            scene_extraction.scorer.get_assert(
                json.dumps(scene_output),
                scene_extraction._context(tmp_path),
            ),
        ),
        (
            "script_bible_scorer",
            script_bible.scorer,
            script_bible.scorer.get_assert(
                json.dumps(script_output),
                script_bible._context(tmp_path),
            ),
        ),
        (
            "storyboard_understanding_scorer",
            storyboard.scorer,
            storyboard.scorer.get_assert(
                json.dumps(storyboard_output),
                {"vars": {"target_path": str(storyboard_target)}},
            ),
        ),
        (
            "video_understanding_scorer",
            video.scorer,
            video._assert_result(tmp_path, video_output),
        ),
    ]


@pytest.mark.unit
def test_hard_gate_failures_cannot_report_passing_scores(tmp_path: Path) -> None:
    results = _hard_gate_results(tmp_path)

    assert len(results) == 13
    for name, scorer, result in results:
        assert result["pass"] is False, name
        assert result["score"] < scorer.PASS_THRESHOLD, name
        assert "raw_score=" in result["reason"], name

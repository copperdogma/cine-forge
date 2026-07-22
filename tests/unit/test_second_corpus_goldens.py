from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

from tests.unit.open_frequency_eval_test_support import NORMALIZED_OPEN_FREQUENCY

REPO_ROOT = Path(__file__).resolve().parents[2]
GOLDEN_ROOT = REPO_ROOT / "benchmarks" / "golden"
SCORER_ROOT = REPO_ROOT / "benchmarks" / "scorers"
SOURCE_PATH = REPO_ROOT / "tests" / "fixtures" / "ingest_inputs" / (
    "open_frequency_short.fountain"
)
SECOND_CORPUS_GOLDENS = {
    "open-frequency-maya-character.json",
    "open-frequency-scenes.json",
    "open-frequency-entity-discovery.json",
    "open-frequency-config.json",
    "open-frequency-script-bible.json",
    "normalize-open-frequency-corrupted-golden.json",
}

for module_root in (GOLDEN_ROOT, SCORER_ROOT):
    if str(module_root) not in sys.path:
        sys.path.insert(0, str(module_root))

character_scorer = importlib.import_module("character_extraction_scorer")
config_scorer = importlib.import_module("config_detection_scorer")
entity_scorer = importlib.import_module("entity_discovery_scorer")
normalization_scorer = importlib.import_module("normalization_scorer")
scene_scorer = importlib.import_module("scene_extraction_scorer")
script_bible_scorer = importlib.import_module("script_bible_scorer")
validation_specs = importlib.import_module("golden_validation_specs")

validator_spec = importlib.util.spec_from_file_location(
    "cineforge_golden_validator",
    GOLDEN_ROOT / "validate-golden.py",
)
assert validator_spec and validator_spec.loader
golden_validator = importlib.util.module_from_spec(validator_spec)
validator_spec.loader.exec_module(golden_validator)


def _json(path: Path) -> dict:
    return json.loads(path.read_text())


def _golden_context(filename: str, **extra: object) -> dict:
    return {
        "vars": {
            "golden_path": str(GOLDEN_ROOT / filename),
            **extra,
        }
    }


@pytest.mark.unit
def test_second_corpus_provenance_binds_canonical_source_hash() -> None:
    provenance = _json(GOLDEN_ROOT / "open-frequency-corpus.provenance.json")

    assert provenance["source_path"] == (
        "tests/fixtures/ingest_inputs/open_frequency_short.fountain"
    )
    assert provenance["source_sha256"] == hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest()
    assert provenance["verification_status"] == "CLEAN"
    assert provenance["verification_date"] == "2026-07-22"
    assert "Independent source-first golden-verify" in provenance["verification_method"]
    assert provenance["pending_independent_verification"] == []
    assert {
        Path(path).name for path in provenance["derived_goldens"]
    } == SECOND_CORPUS_GOLDENS - {"normalize-open-frequency-corrupted-golden.json"}
    corrupted_path = REPO_ROOT / provenance["normalization_fixture"]["input_path"]
    assert provenance["normalization_fixture"]["input_sha256"] == hashlib.sha256(
        corrupted_path.read_bytes()
    ).hexdigest()


@pytest.mark.unit
def test_second_corpus_goldens_are_declared_and_structurally_valid() -> None:
    assert SECOND_CORPUS_GOLDENS <= set(validation_specs.GOLDEN_SPECS)
    for filename in SECOND_CORPUS_GOLDENS:
        result, data = golden_validator.validate_file(
            filename,
            validation_specs.GOLDEN_SPECS[filename],
        )
        assert data is not None
        assert result.errors == []


@pytest.mark.unit
def test_second_corpus_task_cases_point_to_canonical_inputs_and_goldens() -> None:
    expected = {
        "character-extraction.yaml": (13, "open-frequency-maya-character.json"),
        "scene-extraction.yaml": (2, "open-frequency-scenes.json"),
        "entity-discovery.yaml": (2, "open-frequency-entity-discovery.json"),
        "config-detection.yaml": (2, "open-frequency-config.json"),
        "script-bible.yaml": (2, "open-frequency-script-bible.json"),
        "normalization.yaml": (3, "normalize-open-frequency-corrupted-golden.json"),
    }
    for task_name, (case_count, golden_name) in expected.items():
        task = yaml.safe_load((REPO_ROOT / "benchmarks" / "tasks" / task_name).read_text())
        assert len(task["tests"]) == case_count
        matching = [
            case for case in task["tests"]
            if case.get("vars", {}).get("golden_path") == f"golden/{golden_name}"
        ]
        assert len(matching) == 1
        source_var = "source_text" if task_name == "normalization.yaml" else "screenplay"
        source_ref = matching[0]["vars"][source_var].lower().replace("_", "-")
        assert "open-frequency" in source_ref


@pytest.mark.unit
def test_open_frequency_scene_golden_is_consumable_by_scorer() -> None:
    golden = _json(GOLDEN_ROOT / "open-frequency-scenes.json")
    result = scene_scorer.get_assert(
        json.dumps(golden),
        _golden_context("open-frequency-scenes.json"),
    )

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
def test_open_frequency_entity_golden_is_consumable_by_scorer() -> None:
    golden = _json(GOLDEN_ROOT / "open-frequency-entity-discovery.json")
    candidate = {
        category: [*config["required"], *config["optional"]]
        for category, config in golden.items()
        if category in {"characters", "locations", "props"}
    }
    result = entity_scorer.get_assert(
        json.dumps(candidate),
        _golden_context("open-frequency-entity-discovery.json"),
    )

    assert result["pass"] is True
    assert result["score"] == 1.0


def _open_frequency_config_candidate() -> dict:
    return {
        "title": {
            "value": "Open Frequency",
            "confidence": 0.99,
            "rationale": "The title page explicitly names Open Frequency.",
        },
        "format": {
            "value": "short film",
            "confidence": 0.9,
            "rationale": (
                "The community radio studio story resolves with a morning broadcast."
            ),
        },
        "genre": {
            "value": ["drama", "disaster"],
            "confidence": 0.9,
            "rationale": (
                "Emergency power and the north shelter insulin request drive the drama."
            ),
        },
        "tone": {
            "value": ["tense", "hopeful"],
            "confidence": 0.9,
            "rationale": "One miracle becomes a steady ON AIR sign by morning.",
        },
        "estimated_duration_minutes": {
            "value": 6,
            "confidence": 0.8,
            "rationale": (
                "The community radio studio, water tower, and high school gym "
                "form four compact scenes."
            ),
        },
        "primary_characters": {
            "value": ["ARIA", "NOAH", "JUNE", "KELL"],
            "confidence": 0.95,
            "rationale": "ARIA, NOAH, JUNE, and KELL operate the broadcast together.",
        },
        "supporting_characters": {
            "value": ["MAYA"],
            "confidence": 0.9,
            "rationale": "MAYA asks the station to help find COMET.",
        },
        "location_count": {
            "value": 3,
            "confidence": 0.95,
            "rationale": (
                "The distinct locations are the community radio studio, water tower, "
                "and high school gym."
            ),
        },
        "locations_summary": {
            "value": (
                "A community radio studio, water tower catwalk, and high school gym "
                "shelter."
            ),
            "confidence": 0.95,
            "rationale": (
                "The community radio studio, water tower, and high school gym are "
                "explicit scene headings."
            ),
        },
        "target_audience": {
            "value": None,
            "confidence": 0.8,
            "rationale": (
                "The storm, insulin request, and missing dog do not establish a "
                "responsible demographic rating."
            ),
        },
    }


def _score_open_frequency_config(candidate: dict) -> dict:
    return config_scorer.get_assert(
        json.dumps(candidate),
        _golden_context(
            "open-frequency-config.json",
            screenplay=SOURCE_PATH.read_text(),
        ),
    )


@pytest.mark.unit
def test_open_frequency_config_golden_is_consumable_by_scorer() -> None:
    candidate = _open_frequency_config_candidate()
    result = _score_open_frequency_config(candidate)

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
def test_open_frequency_config_rejects_maya_as_a_primary_character() -> None:
    candidate = _open_frequency_config_candidate()
    candidate["primary_characters"]["value"].append("MAYA")

    result = _score_open_frequency_config(candidate)

    assert result["pass"] is False
    assert "primary_characters: unsupported values: MAYA" in result["reason"]


@pytest.mark.unit
def test_open_frequency_config_requires_null_target_audience() -> None:
    candidate = _open_frequency_config_candidate()
    candidate["target_audience"]["value"] = "Martian dragon-romance fans"

    result = _score_open_frequency_config(candidate)

    assert result["pass"] is False
    assert "target_audience: value must be null for this source" in result["reason"]
    assert "audience_accuracy=0.00" in result["reason"]


@pytest.mark.unit
def test_open_frequency_config_enforces_each_confidence_floor() -> None:
    candidate = _open_frequency_config_candidate()
    for field in candidate.values():
        field["confidence"] = 0.0

    result = _score_open_frequency_config(candidate)

    assert result["pass"] is False
    assert "title: confidence 0.00 is below minimum 0.90" in result["reason"]
    assert "confidence_quality=0.00" in result["reason"]


@pytest.mark.unit
def test_open_frequency_config_rejects_negated_title_rationale() -> None:
    candidate = _open_frequency_config_candidate()
    candidate["title"]["rationale"] = (
        "Open Frequency is not the title; Dragon Queen is."
    )

    result = _score_open_frequency_config(candidate)

    assert result["pass"] is False
    assert "title: rationale lacks concrete source evidence" in result["reason"]


@pytest.mark.unit
def test_open_frequency_config_rejects_unsupported_location_padding() -> None:
    candidate = _open_frequency_config_candidate()
    candidate["locations_summary"]["value"] += " and a dragon cave."

    result = _score_open_frequency_config(candidate)

    assert result["pass"] is False
    assert (
        "locations_summary: unsupported source-bounded terms: cave, dragon"
        in result["reason"]
    )


@pytest.mark.unit
def test_open_frequency_config_accepts_lightly_humorous_tone() -> None:
    candidate = _open_frequency_config_candidate()
    candidate["tone"] = {
        "value": ["hopeful", "lightly humorous"],
        "confidence": 0.9,
        "rationale": (
            "The one miracle exchange and Kell's cursed-antenna joke make the "
            "emergency lightly humorous."
        ),
    }

    result = _score_open_frequency_config(candidate)

    assert result["pass"] is True
    assert "tone_accuracy=1.00" in result["reason"]


@pytest.mark.unit
@pytest.mark.parametrize(
    ("tones", "rationale"),
    [
        (
            ["hopeful", "witty"],
            "The one miracle exchange keeps the storm emergency hopeful and witty.",
        ),
        (
            ["community-focused", "uplifting"],
            "The north shelter broadcast makes the emergency community-focused and uplifting.",
        ),
        (
            ["urgent", "tense"],
            "The insulin deadline is urgent while the flickering ON AIR sign keeps "
            "the storm tense.",
        ),
        (
            ["urgent", "suspenseful"],
            "The north shelter insulin need is urgent and the uncertain storm signal "
            "is suspenseful.",
        ),
    ],
)
def test_open_frequency_config_scores_source_supported_allowed_tones(
    tones: list[str],
    rationale: str,
) -> None:
    candidate = _open_frequency_config_candidate()
    candidate["tone"] = {
        "value": tones,
        "confidence": 0.9,
        "rationale": rationale,
    }

    result = _score_open_frequency_config(candidate)

    assert result["pass"] is True, result["reason"]
    assert "tone_accuracy=1.00" in result["reason"]


@pytest.mark.unit
@pytest.mark.parametrize(
    "redundant_tones",
    [
        ["hopeful", "uplifting"],
        ["wry", "witty"],
    ],
)
def test_open_frequency_config_rejects_synonym_padded_tones(
    redundant_tones: list[str],
) -> None:
    candidate = _open_frequency_config_candidate()
    candidate["tone"] = {
        "value": redundant_tones,
        "confidence": 0.9,
        "rationale": (
            "The one miracle exchange and north shelter broadcast support the tone."
        ),
    }

    result = _score_open_frequency_config(candidate)

    assert result["pass"] is False
    assert "tone_accuracy=0.25" in result["reason"]


def _act(number: int, title: str, start: str, end: str) -> dict:
    return {
        "act_number": number,
        "title": title,
        "start_scene": start,
        "end_scene": end,
        "summary": f"The Red Creek radio team advances its community broadcast in {title}.",
        "turning_points": [f"The team reaches the {title.lower()} turning point."],
    }


@pytest.mark.unit
def test_open_frequency_script_bible_golden_is_consumable_by_scorer() -> None:
    synopsis = (
        "During a storm in Red Creek, Aria, Noah, June, and Kell struggle to restore the "
        "community radio signal from a studio running on emergency power. Aria and Noah "
        "carry the portable antenna to the water tower, where they hear that the north "
        "shelter needs insulin and dry blankets and reconnect with June. At the high school "
        "gym shelter, June and Kell keep information moving while Maya asks them to broadcast "
        "a plea for her missing dog, Comet. By morning the road is reopening, supplies are "
        "moving, Comet is found, the ON AIR sign is steady, and the radio team returns to work."
    )
    candidate = {
        "title": "Open Frequency",
        "logline": (
            "A community radio team battles a storm and failing signal to broadcast urgent "
            "shelter information across Red Creek."
        ),
        "synopsis": synopsis,
        "act_structure": [
            _act(
                1,
                "Emergency setup",
                "INT. COMMUNITY RADIO STUDIO - NIGHT",
                "INT. COMMUNITY RADIO STUDIO - NIGHT",
            ),
            _act(
                2,
                "Connection and service",
                "EXT. WATER TOWER CATWALK - NIGHT",
                "INT. HIGH SCHOOL GYM SHELTER - PRE-DAWN",
            ),
            _act(
                3,
                "Morning resilience",
                "INT. COMMUNITY RADIO STUDIO - MORNING",
                "INT. COMMUNITY RADIO STUDIO - MORNING",
            ),
        ],
        "themes": [
            {
                "theme": "Community service",
                "description": "The broadcasters turn local information into mutual aid.",
                "evidence": ["north shelter needs insulin", "East road is open one lane"],
            },
            {
                "theme": "Communication and connection",
                "description": "A fragile radio signal reconnects isolated people.",
                "evidence": ["if anyone hears this", "Loud enough to make me useful"],
            },
            {
                "theme": "Resilience and hope",
                "description": "The team keeps working through the storm until morning.",
                "evidence": ["one miracle", "ON AIR sign steadies"],
            },
        ],
        "narrative_arc": (
            "A powerless radio studio becomes a working community lifeline, and the morning "
            "broadcast converts the night's fragile hope into continued service."
        ),
        "genre": "Hopeful disaster drama",
        "tone": "Tense, resilient, warm, and wry",
        "protagonist_journey": (
            "The radio team turns a failing signal into a useful broadcast that reconnects "
            "the community, then settles back to work."
        ),
        "central_conflict": (
            "The team must overcome the storm, emergency power, and a failing signal so the "
            "broadcast can deliver insulin and shelter information."
        ),
        "setting_overview": (
            "Storm-struck Red Creek from night through morning: a community radio studio, "
            "water tower catwalk, and high school gym shelter."
        ),
        "confidence": 0.98,
    }
    result = script_bible_scorer.get_assert(
        json.dumps(candidate),
        _golden_context(
            "open-frequency-script-bible.json",
            screenplay=SOURCE_PATH.read_text(),
        ),
    )

    assert result["pass"] is True
    assert result["score"] == 1.0


@pytest.mark.unit
def test_open_frequency_maya_golden_is_consumable_by_scorer() -> None:
    source = SOURCE_PATH.read_text()
    candidate = {
        "character_id": "maya",
        "name": "MAYA",
        "aliases": [],
        "description": (
            "Maya is a persistent, hopeful teenager in a soaked marching-band jacket who "
            "asks the station to announce her missing dog, Comet, and spells his name for the "
            "broadcast. She later finds him under the vending machine in the band room and "
            "brings the muddy, sleepy dog to the radio studio in the morning."
        ),
        "explicit_evidence": [
            {
                "trait": "teenage evacuee",
                "quote": (
                    "MAYA, a teenager in a soaked marching-band jacket, approaches with a "
                    "flyer for a missing dog named COMET."
                ),
                "source_scene": "INT. HIGH SCHOOL GYM SHELTER - PRE-DAWN",
            },
            {
                "trait": "devoted to Comet",
                "quote": (
                    "He stole my grilled cheese and slept through the evacuation. He's family."
                ),
                "source_scene": "INT. HIGH SCHOOL GYM SHELTER - PRE-DAWN",
            },
            {
                "trait": "successful searcher",
                "quote": "He was under the vending machine in the band room.",
                "source_scene": "INT. COMMUNITY RADIO STUDIO - MORNING",
            },
        ],
        "inferred_traits": [
            {
                "trait": "devoted to Comet",
                "value": "She treats Comet as family.",
                "confidence": 0.99,
                "rationale": "Maya explicitly calls the missing dog family.",
            },
            {
                "trait": "persistent",
                "value": "She keeps searching and recruits the station's help.",
                "confidence": 0.9,
                "rationale": "She brings a flyer, requests a broadcast, and later finds him.",
            },
            {
                "trait": "hopeful",
                "value": "She expects the broadcast can help recover Comet.",
                "confidence": 0.8,
                "rationale": "She asks the station to announce the missing dog.",
            },
        ],
        "scene_presence": [
            "INT. HIGH SCHOOL GYM SHELTER - PRE-DAWN",
            "INT. COMMUNITY RADIO STUDIO - MORNING",
        ],
        "dialogue_summary": (
            "Maya directly asks for help, describes Comet's behavior, spells his name, and "
            "reports where she found him."
        ),
        "narrative_role": "supporting",
        "relationships": [{
            "target_character": "COMET",
            "relationship_type": "family",
            "evidence": "Maya says that Comet is family.",
            "confidence": 0.99,
        }],
        "overall_confidence": 0.98,
    }
    result = character_scorer.get_assert(
        json.dumps(candidate),
        _golden_context(
            "open-frequency-maya-character.json",
            character_name="MAYA",
            screenplay=source,
        ),
    )

    assert result["pass"] is True
    assert result["score"] == 1.0

@pytest.mark.unit
def test_corrupted_open_frequency_normalization_contract_is_consumable() -> None:
    source = (REPO_ROOT / "benchmarks" / "input" / (
        "normalize-open-frequency-corrupted.fountain"
    )).read_text()
    context = _golden_context(
        "normalize-open-frequency-corrupted-golden.json",
        source_text=source,
    )
    normalized = normalization_scorer.get_assert(NORMALIZED_OPEN_FREQUENCY, context)
    still_corrupted = normalization_scorer.get_assert(source, context)

    assert normalized["pass"] is True
    assert normalized["score"] == 1.0
    assert still_corrupted["pass"] is False
    assert "Markdown violations" in still_corrupted["reason"]

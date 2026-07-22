from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

SCORER_ROOT = Path(__file__).resolve().parents[2] / "benchmarks" / "scorers"
if str(SCORER_ROOT) not in sys.path:
    sys.path.insert(0, str(SCORER_ROOT))

from score_semantics import finalize_score  # noqa: E402

SCORER_FILES = (
    "bible_extraction_scorer.py",
    "character_extraction_scorer.py",
    "config_detection_scorer.py",
    "continuity_extraction_scorer.py",
    "entity_discovery_scorer.py",
    "normalization_scorer.py",
    "qa_pass_scorer.py",
    "relationship_scorer.py",
    "scene_enrichment_scorer.py",
    "scene_extraction_scorer.py",
    "script_bible_scorer.py",
    "storyboard_understanding_scorer.py",
    "video_understanding_scorer.py",
)


@pytest.mark.unit
def test_hard_failure_is_capped_strictly_below_threshold_with_raw_diagnostic() -> None:
    result = finalize_score(
        1.0,
        pass_threshold=0.60,
        hard_gates=False,
        reason="schema mismatch",
    )

    assert result == {
        "pass": False,
        "score": 0.5999,
        "reason": "raw_score=1.0000 | schema mismatch",
    }


@pytest.mark.unit
def test_passing_and_low_raw_scores_keep_their_numeric_value() -> None:
    assert finalize_score(
        0.75,
        pass_threshold=0.70,
        hard_gates=True,
        reason="clear",
    ) == {"pass": True, "score": 0.75, "reason": "clear"}
    assert finalize_score(
        0.55,
        pass_threshold=0.70,
        hard_gates=True,
        reason="quality floor",
    ) == {
        "pass": False,
        "score": 0.55,
        "reason": "raw_score=0.5500 | quality floor",
    }


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw_score", "pass_threshold"),
    [(float("nan"), 0.7), (1.1, 0.7), (0.8, 0.0), (0.8, 1.1)],
)
def test_invalid_score_contract_is_rejected(raw_score: float, pass_threshold: float) -> None:
    with pytest.raises(ValueError):
        finalize_score(
            raw_score,
            pass_threshold=pass_threshold,
            hard_gates=True,
            reason="invalid",
        )


@pytest.mark.unit
@pytest.mark.parametrize("scorer_file", SCORER_FILES)
def test_scorer_dynamic_loads_in_fresh_isolated_process(
    tmp_path: Path, scorer_file: str
) -> None:
    script = """
import importlib.util
import sys
from pathlib import Path

path = Path(sys.argv[1]).resolve()
sys.modules.pop("score_semantics", None)
spec = importlib.util.spec_from_file_location("isolated_scorer", path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
assert callable(module.finalize_score)
"""
    completed = subprocess.run(
        [sys.executable, "-I", "-c", script, str(SCORER_ROOT / scorer_file)],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr

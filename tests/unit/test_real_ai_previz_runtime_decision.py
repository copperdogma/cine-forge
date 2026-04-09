from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_SCRIPT_ROOT = REPO_ROOT / "benchmarks" / "scripts"
if str(BENCHMARK_SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCHMARK_SCRIPT_ROOT))

runtime_decision = importlib.import_module("real_ai_previz_runtime_decision")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


@pytest.mark.unit
def test_runtime_decision_main_writes_divergence_summary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    summary_path = tmp_path / "shared-summary.json"
    result_path = tmp_path / "validation-pass.json"
    output_prefix = tmp_path / "decision-summary"

    _write_json(
        summary_path,
        {
            "summary": {"recommended_shipped_case_id": "shipped_lite_4_scene_ready"},
            "cases": [
                {
                    "case_id": "fast_4_scene_ready",
                    "label": "Fast 4 scene-ready",
                    "engine_pack_id": "google_veo31_fast",
                    "duration_seconds": 4,
                    "resolution": "720p",
                    "usefulness_overall": 0.778,
                    "usefulness_note": "Runner-up AI lane.",
                    "all_ai_previz_elapsed_ms": [52_400, 52_000, 52_188],
                    "all_total_elapsed_ms": [165_200, 164_799, 164_398],
                },
                {
                    "case_id": "shipped_lite_4_scene_ready",
                    "label": "Shipped Lite 4 scene-ready",
                    "engine_pack_id": "google_veo31_lite",
                    "duration_seconds": 4,
                    "resolution": "720p",
                    "usefulness_overall": 0.828,
                    "usefulness_note": "Usefulness leader.",
                    "all_ai_previz_elapsed_ms": [55_600, 55_428, 55_320],
                    "all_total_elapsed_ms": [171_500, 171_007, 170_900],
                },
            ],
        },
    )
    _write_json(
        result_path,
        {
            "cases": [
                {
                    "case_id": "fast_4_scene_ready",
                    "ai_previz_elapsed_ms": 52_196,
                    "total_elapsed_ms": 164_799,
                },
                {
                    "case_id": "shipped_lite_4_scene_ready",
                    "ai_previz_elapsed_ms": 55_428,
                    "total_elapsed_ms": 171_007,
                },
            ]
        },
    )

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "real_ai_previz_runtime_decision.py",
            "--summary-file",
            str(summary_path),
            "--result-file",
            str(result_path),
            "--output-prefix",
            str(output_prefix),
        ],
    )

    runtime_decision.main()

    payload = json.loads(output_prefix.with_suffix(".json").read_text(encoding="utf-8"))
    markdown = output_prefix.with_suffix(".md").read_text(encoding="utf-8")

    assert payload["summary"]["current_shipped_case_id"] == "shipped_lite_4_scene_ready"
    assert payload["summary"]["runtime_winner_case_id"] == "fast_4_scene_ready"
    assert payload["summary"]["usefulness_leader_case_id"] == "shipped_lite_4_scene_ready"
    assert payload["summary"]["leaders_diverge"] is True
    assert "No dominant winner is proven" in payload["summary"]["note"]
    assert "Leaders diverge: yes" in markdown
    assert "`fast_4_scene_ready`" in markdown


@pytest.mark.unit
def test_runtime_decision_append_result_file_rejects_unknown_case(tmp_path: Path) -> None:
    result_path = tmp_path / "unknown-case.json"
    _write_json(
        result_path,
        {
            "cases": [
                {
                    "case_id": "missing_case",
                    "ai_previz_elapsed_ms": 50_000,
                    "total_elapsed_ms": 160_000,
                }
            ]
        },
    )

    with pytest.raises(KeyError, match="missing_case"):
        runtime_decision._append_result_file(  # type: ignore[attr-defined]
            cases={},
            result_path=result_path,
        )

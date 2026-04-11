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

throughput_support = importlib.import_module("full_script_throughput_support")


@pytest.mark.unit
def test_manifest_parses_honest_story_lane_boundary() -> None:
    manifest = throughput_support.ThroughputEvalManifest.model_validate_json(
        json.dumps(
            {
                "boundary_id": "story_lane_workspace_ready",
                "boundary_label": "Break Down Script -> Deep Breakdown",
                "honest_scope": "Run mvp_ingest then world_building only.",
                "recipes": [
                    {
                        "recipe_id": "mvp_ingest",
                        "recipe_path": "configs/recipes/recipe-mvp-ingest.yaml",
                        "ui_label": "Break Down Script",
                    },
                    {
                        "recipe_id": "world_building",
                        "recipe_path": "configs/recipes/recipe-world-building.yaml",
                        "ui_label": "Deep Breakdown",
                    },
                ],
                "cases": [
                    {
                        "case_id": "short_control",
                        "label": "Short control screenplay",
                        "input_fixture": (
                            "tests/fixtures/ingest_inputs/open_frequency_short.fountain"
                        ),
                    }
                ],
            }
        )
    )

    assert manifest.boundary_id == "story_lane_workspace_ready"
    assert [recipe.recipe_id for recipe in manifest.recipes] == [
        "mvp_ingest",
        "world_building",
    ]
    assert manifest.cases[0].case_id == "short_control"


@pytest.mark.unit
def test_build_recipe_run_summary_counts_output_volume(tmp_path: Path) -> None:
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir()
    text_artifact = artifacts_dir / "script_bible.json"
    text_artifact.write_text('{"summary": "hello"}\n', encoding="utf-8")
    markdown_artifact = artifacts_dir / "scene_notes.md"
    markdown_artifact.write_text("line one\nline two\n", encoding="utf-8")

    state = {
        "recipe_id": "mvp_ingest",
        "stage_order": ["script_bible", "project_config"],
        "stages": {
            "script_bible": {
                "status": "done",
                "duration_seconds": 1.5,
                "cost_usd": 0.12,
                "input_tokens": 100,
                "output_tokens": 220,
                "artifact_refs": [
                    {"artifact_type": "script_bible", "path": str(text_artifact)},
                ],
            },
            "project_config": {
                "status": "done",
                "duration_seconds": 0.5,
                "cost_usd": 0.01,
                "input_tokens": 50,
                "output_tokens": 25,
                "artifact_refs": [
                    {"artifact_type": "project_config", "path": str(markdown_artifact)},
                ],
            },
        },
        "total_cost_usd": 0.13,
    }

    summary = throughput_support.build_recipe_run_summary(
        state=state,
        recipe_path=REPO_ROOT / "configs" / "recipes" / "recipe-mvp-ingest.yaml",
        ui_label="Break Down Script",
        project_dir=tmp_path,
        repo_root=REPO_ROOT,
        run_id="run-1234",
        elapsed_ms=2400,
        error=None,
    )

    assert summary.success is True
    assert summary.total_duration_ms == 2000
    assert summary.total_output_tokens == 245
    assert summary.output_volume.artifact_count == 2
    assert summary.output_volume.total_bytes == len(text_artifact.read_bytes()) + len(
        markdown_artifact.read_bytes()
    )
    assert summary.output_volume.text_lines == 3


@pytest.mark.unit
def test_budget_summary_uses_normalized_current_and_climb_values() -> None:
    mvp_ingest_a = throughput_support.RecipeRunSummary(
        run_id="run-a-1",
        recipe_id="mvp_ingest",
        recipe_path="configs/recipes/recipe-mvp-ingest.yaml",
        ui_label="Break Down Script",
        elapsed_ms=12_000,
        success=True,
        total_duration_ms=11_500,
        total_cost_usd=0.33,
        total_input_tokens=1_000,
        total_output_tokens=500,
        output_volume=throughput_support.OutputVolumeEvidence(
            artifact_count=3,
            total_bytes=900,
            text_characters=900,
            text_lines=30,
        ),
        stage_summaries=[
            throughput_support.StageThroughputSummary(
                stage_id="normalize",
                status="done",
                duration_ms=6_000,
                cost_usd=0.10,
                input_tokens=400,
                output_tokens=200,
                output_volume=throughput_support.OutputVolumeEvidence(
                    artifact_count=1,
                    total_bytes=300,
                    text_characters=300,
                    text_lines=10,
                ),
            ),
            throughput_support.StageThroughputSummary(
                stage_id="script_bible",
                status="done",
                duration_ms=6_000,
                cost_usd=0.23,
                input_tokens=600,
                output_tokens=300,
                output_volume=throughput_support.OutputVolumeEvidence(
                    artifact_count=2,
                    total_bytes=600,
                    text_characters=600,
                    text_lines=20,
                ),
            ),
        ],
    )
    world_building_a = throughput_support.RecipeRunSummary(
        run_id="run-a-2",
        recipe_id="world_building",
        recipe_path="configs/recipes/recipe-world-building.yaml",
        ui_label="Deep Breakdown",
        elapsed_ms=18_000,
        success=True,
        total_duration_ms=17_500,
        total_cost_usd=0.44,
        total_input_tokens=1_500,
        total_output_tokens=1_200,
        output_volume=throughput_support.OutputVolumeEvidence(
            artifact_count=4,
            total_bytes=2_400,
            text_characters=2_400,
            text_lines=80,
        ),
        stage_summaries=[
            throughput_support.StageThroughputSummary(
                stage_id="analyze_scenes",
                status="done",
                duration_ms=9_000,
                cost_usd=0.22,
                input_tokens=900,
                output_tokens=700,
                output_volume=throughput_support.OutputVolumeEvidence(
                    artifact_count=2,
                    total_bytes=1_600,
                    text_characters=1_600,
                    text_lines=50,
                ),
            ),
            throughput_support.StageThroughputSummary(
                stage_id="entity_graph",
                status="done",
                duration_ms=9_000,
                cost_usd=0.22,
                input_tokens=600,
                output_tokens=500,
                output_volume=throughput_support.OutputVolumeEvidence(
                    artifact_count=2,
                    total_bytes=800,
                    text_characters=800,
                    text_lines=30,
                ),
            ),
        ],
    )
    case_a = throughput_support.CaseBoundaryResult(
        case_id="short",
        label="Short screenplay",
        input_fixture="short.fountain",
        input_word_count=1_000,
        input_line_count=100,
        input_bytes=4_000,
        project_dir="output/short",
        success=True,
        total_elapsed_ms=30_000,
        total_duration_ms=29_000,
        total_cost_usd=0.77,
        total_input_tokens=2_500,
        total_output_tokens=1_700,
        output_volume=throughput_support.OutputVolumeEvidence(
            artifact_count=7,
            total_bytes=3_300,
            text_characters=3_300,
            text_lines=110,
        ),
        recipe_runs=[mvp_ingest_a, world_building_a],
    )

    mvp_ingest_b = mvp_ingest_a.model_copy(
        update={
            "run_id": "run-b-1",
            "elapsed_ms": 15_000,
            "total_duration_ms": 14_500,
            "total_cost_usd": 0.40,
            "total_input_tokens": 1_100,
            "total_output_tokens": 700,
            "output_volume": throughput_support.OutputVolumeEvidence(
                artifact_count=3,
                total_bytes=1_200,
                text_characters=1_200,
                text_lines=40,
            ),
            "stage_summaries": [
                throughput_support.StageThroughputSummary(
                    stage_id="normalize",
                    status="done",
                    duration_ms=8_000,
                    cost_usd=0.14,
                    input_tokens=500,
                    output_tokens=250,
                    output_volume=throughput_support.OutputVolumeEvidence(
                        artifact_count=1,
                        total_bytes=400,
                        text_characters=400,
                        text_lines=12,
                    ),
                ),
                throughput_support.StageThroughputSummary(
                    stage_id="script_bible",
                    status="done",
                    duration_ms=7_000,
                    cost_usd=0.26,
                    input_tokens=600,
                    output_tokens=450,
                    output_volume=throughput_support.OutputVolumeEvidence(
                        artifact_count=2,
                        total_bytes=800,
                        text_characters=800,
                        text_lines=28,
                    ),
                ),
            ],
        }
    )
    world_building_b = world_building_a.model_copy(
        update={
            "run_id": "run-b-2",
            "elapsed_ms": 25_000,
            "total_duration_ms": 24_000,
            "total_cost_usd": 0.60,
            "total_input_tokens": 1_900,
            "total_output_tokens": 1_800,
            "output_volume": throughput_support.OutputVolumeEvidence(
                artifact_count=4,
                total_bytes=3_600,
                text_characters=3_600,
                text_lines=120,
            ),
            "stage_summaries": [
                throughput_support.StageThroughputSummary(
                    stage_id="analyze_scenes",
                    status="done",
                    duration_ms=15_000,
                    cost_usd=0.32,
                    input_tokens=1_100,
                    output_tokens=1_100,
                    output_volume=throughput_support.OutputVolumeEvidence(
                        artifact_count=2,
                        total_bytes=2_500,
                        text_characters=2_500,
                        text_lines=80,
                    ),
                ),
                throughput_support.StageThroughputSummary(
                    stage_id="entity_graph",
                    status="done",
                    duration_ms=10_000,
                    cost_usd=0.28,
                    input_tokens=800,
                    output_tokens=700,
                    output_volume=throughput_support.OutputVolumeEvidence(
                        artifact_count=2,
                        total_bytes=1_100,
                        text_characters=1_100,
                        text_lines=40,
                    ),
                ),
            ],
        }
    )
    case_b = throughput_support.CaseBoundaryResult(
        case_id="long",
        label="Long screenplay",
        input_fixture="long.fountain",
        input_word_count=2_000,
        input_line_count=200,
        input_bytes=8_000,
        project_dir="output/long",
        success=True,
        total_elapsed_ms=40_000,
        total_duration_ms=38_500,
        total_cost_usd=1.00,
        total_input_tokens=3_000,
        total_output_tokens=2_500,
        output_volume=throughput_support.OutputVolumeEvidence(
            artifact_count=7,
            total_bytes=4_800,
            text_characters=4_800,
            text_lines=160,
        ),
        recipe_runs=[mvp_ingest_b, world_building_b],
    )

    budgets = throughput_support.derive_budget_rows([case_a, case_b])
    summary = throughput_support.summarize_results([case_a, case_b], budgets)
    payload = {
        "measured_at": "2026-04-10T00:00:00Z",
        "fixture_manifest": "benchmarks/fixtures/full_script_throughput_cases.json",
        "boundary": {
            "boundary_label": "Break Down Script -> Deep Breakdown",
            "honest_scope": "Story lane only.",
            "recipes": [
                {"recipe_id": "mvp_ingest"},
                {"recipe_id": "world_building"},
            ],
        },
        "summary": summary,
        "budgets": [row.model_dump(mode="json") for row in budgets],
        "cases": [case_a.model_dump(mode="json"), case_b.model_dump(mode="json")],
    }
    markdown = throughput_support.render_throughput_markdown(payload)

    boundary_row = next(row for row in budgets if row.scope_type == "boundary")
    analyze_row = next(row for row in budgets if row.scope_id == "world_building.analyze_scenes")

    assert boundary_row.measurement.current_duration_ms_per_1k_words == 25_000.0
    assert boundary_row.measurement.climb_target_duration_ms_per_1k_words == 20_000.0
    assert analyze_row.measurement.current_output_tokens_per_1k_words == 625.0
    assert summary["top_runtime_hotspot_id"] == "world_building.analyze_scenes"
    assert "current_observed" in markdown
    assert "climb_target" in markdown
    assert "world_building.analyze_scenes" in markdown

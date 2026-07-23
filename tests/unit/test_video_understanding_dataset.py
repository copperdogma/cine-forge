from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "benchmarks" / "scripts"
DATASET_ROOT = REPO_ROOT / "benchmarks" / "video_understanding"
TASK_PATH = REPO_ROOT / "benchmarks" / "tasks" / "video-understanding.yaml"
RELATED_TASK_PATHS = (
    TASK_PATH,
    REPO_ROOT / "benchmarks" / "tasks" / "previz-usefulness.yaml",
    REPO_ROOT / "benchmarks" / "tasks" / "final-render-provider-floor.yaml",
)
PROMPT_PATH = REPO_ROOT / "benchmarks" / "prompts" / "video-understanding.txt"
REGISTRY_PATH = REPO_ROOT / "docs" / "evals" / "registry.yaml"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from video_understanding_dataset_artifacts import (  # noqa: E402
    GENERATOR_FILES,
    generate_dataset,
)
from video_understanding_dataset_model import FrameTarget  # noqa: E402
from video_understanding_dataset_specs import ACTIVE_CLIPS, CLIPS  # noqa: E402
from video_understanding_frame_renderer import render_frame  # noqa: E402

ACTIVE_IDS = [
    "dialogue_confession_push_in",
    "alarm_chase_whip_pan",
    "quiet_bedside_vigil",
    "prop_swap_continuity_break",
    "rooftop_escape_crash_zoom",
    "storm_tunnel_lateral_run",
]
SYNTHESIZED_TONE_TAGS = {
    "alarm",
    "drone",
    "heartbeat",
    "muzak",
    "percussion",
    "radio",
    "soft_music",
}


def _manifest() -> dict:
    return json.loads((DATASET_ROOT / "manifest.json").read_text())


def _task_case_ids() -> list[str]:
    task = yaml.safe_load(TASK_PATH.read_text())
    return [test["vars"]["clip_id"] for test in task["tests"]]


def _tree_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


@pytest.mark.unit
def test_manifest_classifies_every_case_and_task_uses_only_active_cases() -> None:
    manifest = _manifest()
    rows = manifest["clips"]
    active = [row["clip_id"] for row in rows if row["case_status"] == "active_frame_eval"]
    quarantined = [row for row in rows if row["case_status"] == "quarantined"]

    assert len(rows) == 20
    assert active == ACTIVE_IDS == manifest["active_case_ids"] == _task_case_ids()
    assert len(quarantined) == 14
    assert all(row["status_reason"].strip() for row in rows)
    assert set(_task_case_ids()).isdisjoint(row["clip_id"] for row in quarantined)


@pytest.mark.unit
def test_task_cases_keep_subject_identifiers_opaque() -> None:
    task = yaml.safe_load(TASK_PATH.read_text())
    assert len(task["tests"]) == 6
    for test in task["tests"]:
        vars_data = test["vars"]
        assert "clip_title" not in vars_data
        assert vars_data["evaluation_id"].startswith("vfp_active_")
        assert vars_data["clip_id"] not in vars_data["evaluation_id"]


@pytest.mark.unit
def test_all_frame_eval_tasks_keep_titles_out_of_subject_variables() -> None:
    for task_path in RELATED_TASK_PATHS:
        task = yaml.safe_load(task_path.read_text())
        for test in task["tests"]:
            assert "clip_title" not in test["vars"], task_path


@pytest.mark.unit
def test_prompt_binds_evidence_to_submitted_frame_indices() -> None:
    prompt = PROMPT_PATH.read_text()
    assert "exact `frame_index` and `cue` keys" in prompt
    assert "cite one submitted image (0 through 4)" in prompt
    assert "timestamp_seconds" not in prompt


@pytest.mark.unit
def test_prompt_declares_the_exact_nested_output_types() -> None:
    prompt = PROMPT_PATH.read_text()

    assert "`continuity_notes` and `audio_notes` are arrays of strings" in prompt
    assert "`evidence` is an array of 2-4 objects" in prompt
    assert '"frame_index": <integer 0 through 4>' in prompt
    assert '"cue": "<visible cue>"' in prompt
    assert "never strings" in prompt


@pytest.mark.unit
def test_registry_declares_active_policy_and_quarantines_historical_scores() -> None:
    registry = yaml.safe_load(REGISTRY_PATH.read_text())
    entry = next(item for item in registry["evals"] if item["id"] == "video-understanding")
    policy = entry["test_case_policy"]
    assert entry["test_cases"] == 6
    assert policy["mode"] == "explicit_manifest_active_cases"
    assert policy["case_ids"] == ACTIVE_IDS
    assert "filter-first-n" not in entry["command"]
    assert entry["scores"]
    decision_rows = [
        score
        for score in entry["scores"]
        if score["evidence_status"] == "decision-grade"
    ]
    assert {
        (score["model"], score["result_file"])
        for score in decision_rows
    } == {
        (
            "Gemini 3.6 Flash",
            "benchmarks/results/video-understanding-story-208-post-repair-v3-2026-07-22.json",
        ),
        (
            "Gemini 3.5 Flash-Lite",
            "benchmarks/results/video-understanding-story-208-post-repair-v3-2026-07-22.json",
        ),
    }
    assert all(
        score["evidence_status"] == "contaminated-non-decision-grade"
        for score in entry["scores"]
        if score not in decision_rows
    )


@pytest.mark.unit
def test_rendering_has_no_authored_text_path_or_answer_label_fields() -> None:
    source = (SCRIPT_ROOT / "video_understanding_frame_renderer.py").read_text()
    tree = ast.parse(source)
    text_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "text"
    ]
    assert text_calls == []
    clip_fields = set(CLIPS[0].__dataclass_fields__)
    assert "overlay_label" not in clip_fields
    assert "prop_label" not in clip_fields


@pytest.mark.unit
def test_active_packets_have_declared_temporal_diversity_and_provenance() -> None:
    manifest = _manifest()
    rows = {row["clip_id"]: row for row in manifest["clips"]}
    for spec in ACTIVE_CLIPS:
        clip_dir = DATASET_ROOT / spec.slug
        meta = json.loads((clip_dir / "meta.json").read_text())
        actual_hashes = [
            hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted((clip_dir / "frames").glob("*.jpg"))
        ]
        unique_count = len(set(actual_hashes))
        assert len(actual_hashes) == 5
        assert actual_hashes == meta["sampled_frame_sha256"]
        assert actual_hashes == rows[spec.slug]["sampled_frame_sha256"]
        assert unique_count == spec.expected_unique_sampled_frames
        if spec.temporal_control == "static":
            assert unique_count == 1
        elif spec.temporal_control == "change_point":
            assert unique_count == 2
        else:
            assert unique_count >= 4


@pytest.mark.unit
def test_targets_are_constructed_from_frame_observable_fields_only() -> None:
    assert set(FrameTarget.__dataclass_fields__) == {
        "summary_reference",
        "required_keywords",
        "tone_tags",
        "emotion_tags",
        "color_tags",
        "camera_tags",
        "motion_tags",
        "continuity_status",
        "continuity_notes",
    }
    for spec in CLIPS:
        target = json.loads((DATASET_ROOT / spec.slug / "target.json").read_text())
        markdown = (DATASET_ROOT / spec.slug / "target.md").read_text().lower()
        summary = target["summary_reference"].lower()
        assert target["transcript"] is None
        assert target["audio_description"] is None
        assert target["audio_tags"] == []
        assert target["weights"]["audio"] == 0.0
        assert all(keyword.lower() in summary for keyword in target["required_keywords"])
        assert "excluded from scoring" in markdown
        assert spec.transcript is None or spec.transcript.lower() not in markdown
        assert spec.audio_description is None or spec.audio_description.lower() not in markdown


@pytest.mark.unit
def test_asset_audio_metadata_matches_the_single_tone_synthesizer() -> None:
    """The generator mixes speech with at most one real synthetic tone."""
    for spec in CLIPS:
        declared_tones = set(spec.audio_tags) & SYNTHESIZED_TONE_TAGS
        assert len(declared_tones) <= 1, spec.slug
        if spec.audio_description:
            assert "synthetic tones" not in spec.audio_description.lower()


@pytest.mark.unit
def test_generator_provenance_hashes_match_current_sources() -> None:
    provenance = _manifest()["generator_provenance"]["files_sha256"]
    assert set(provenance) == set(GENERATOR_FILES)
    for relative, expected_hash in provenance.items():
        assert hashlib.sha256((REPO_ROOT / relative).read_bytes()).hexdigest() == expected_hash


@pytest.mark.unit
def test_frame_renderer_is_deterministic_for_every_case() -> None:
    for spec in CLIPS:
        total_frames = int(spec.duration_seconds * 8)
        first = render_frame(spec, total_frames // 2, total_frames).tobytes()
        second = render_frame(spec, total_frames // 2, total_frames).tobytes()
        assert first == second


@pytest.mark.unit
def test_generator_outputs_are_deterministic_without_media_encoding(tmp_path: Path) -> None:
    first_root = tmp_path / "first"
    second_root = tmp_path / "second"
    generate_dataset(first_root, repo_root=REPO_ROOT, include_video=False)
    generate_dataset(second_root, repo_root=REPO_ROOT, include_video=False)
    assert _tree_hashes(first_root) == _tree_hashes(second_root)


@pytest.mark.unit
def test_generator_sources_stay_below_architecture_size_limit() -> None:
    for relative in GENERATOR_FILES:
        source_path = REPO_ROOT / relative
        source = source_path.read_text()
        assert len(source.splitlines()) < 400, relative
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end = node.end_lineno or node.lineno
                assert end - node.lineno + 1 <= 100, f"{relative}:{node.name}"

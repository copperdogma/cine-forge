from __future__ import annotations

import ast
import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from tests.unit.final_render_provider_floor_file_inventory import TOUCHED_PYTHON_FILES
from tests.unit.final_render_provider_floor_runtime_test_support import (
    RUNTIME_CONTRACT_MUTATIONS,
    runner_uses_retained_nested_elapsed,
    runtime_contract_accepts,
)
from tests.unit.final_render_provider_floor_test_support import (
    REPORT_EVIDENCE_MUTATIONS,
    apply_evidence_mutation,
    complete_quality_entries,
    complete_runtime_payload,
    prepare_switch,
    write_task_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "benchmarks" / "scripts"
PROVIDER_ROOT = REPO_ROOT / "benchmarks" / "providers"
DATASET_ROOT = REPO_ROOT / "benchmarks" / "final_render_provider_floor"
FIXTURE_PATH = REPO_ROOT / "benchmarks" / "fixtures" / "final_render_provider_floor_cases.json"
RUNTIME_PATH = REPO_ROOT / "benchmarks/results" / (
    "final-render-provider-floor-story-169-runtime-fixed-2026-04-16.json"
)
QUALITY_PATH = REPO_ROOT / "benchmarks/results" / (
    "final-render-provider-floor-story-169-quality-2026-04-16.json"
)
TASK_PATH = REPO_ROOT / "benchmarks" / "tasks" / "final-render-provider-floor.yaml"
REGISTRY_PATH = REPO_ROOT / "docs" / "evals" / "registry.yaml"
for path in (SCRIPT_ROOT, PROVIDER_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from final_render_provider_floor_report import (  # noqa: E402
    _recommend,
    _registry_default,
    _registry_policy,
    build_summary,
)
from generate_final_render_provider_floor_dataset import generate_dataset  # noqa: E402
from video_understanding_transport import (  # noqa: E402
    build_user_text,
    sample_times_seconds,
)

DIMENSION_FIELDS = {
    "summary": ("summary_reference", "required_keywords"),
    "tone": ("tone_tags",),
    "emotion": ("emotion_tags",),
    "continuity": ("continuity_status", "continuity_notes"),
    "evidence": ("evidence",),
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _media_hashes(root: Path) -> dict[str, str]:
    paths = [*root.glob("*/*/clip.mp4"), *root.glob("*/*/frames/*.jpg")]
    return {str(path.relative_to(root)): _sha256(path) for path in sorted(paths)}


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _manifest() -> dict:
    return json.loads((DATASET_ROOT / "manifest.json").read_text(encoding="utf-8"))


@pytest.mark.unit
def test_intended_targets_are_scene_quoted_and_exclude_unverifiable_dimensions() -> None:
    for case in _fixture()["cases"]:
        target = case["analysis_target"]
        provenance = case["target_provenance"]
        source_path = REPO_ROOT / provenance["source_fixture"]
        source = source_path.read_text(encoding="utf-8")
        assert provenance["source_fixture"] == case["input_fixture"]
        assert provenance["source_fixture_sha256"] == _sha256(source_path)
        assert provenance["scene_heading"] in source

        weighted = {
            name for name, weight in target["weights"].items() if float(weight) > 0
        }
        assert weighted == set(provenance["scored_dimensions"])
        assert weighted == set(DIMENSION_FIELDS)
        assert set(provenance["excluded_dimensions"]) == {
            "audio",
            "camera",
            "color",
            "motion",
        }
        assert target["audio_tags"] == target["camera_tags"] == []
        assert target["color_tags"] == target["motion_tags"] == []
        assert target["continuity_status"] == "intact"
        assert "suspicion" not in target["emotion_tags"]
        assert "wonder" not in target["emotion_tags"]
        for criterion, sources in provenance["criteria"].items():
            assert criterion in {
                field for fields in DIMENSION_FIELDS.values() for field in fields
            }
            for source_entry in sources:
                assert source_entry["source_kind"] == "screenplay"
                assert all(quote in source for quote in source_entry["quotes"])


@pytest.mark.unit
def test_generated_targets_are_fixture_intent_not_candidate_frame_truth() -> None:
    fixture_cases = {case["case_id"]: case for case in _fixture()["cases"]}
    manifest = _manifest()
    assert manifest["case_policy"]["target_semantics"] == (
        "intended_source_brief_not_candidate_frame_truth"
    )
    for row in manifest["cases"]:
        target_path = DATASET_ROOT / row["target_path"]
        expected = fixture_cases[row["case_id"]]["analysis_target"]
        assert json.loads(target_path.read_text(encoding="utf-8")) == expected
        assert _sha256(target_path) == row["target_sha256"]
        markdown = (DATASET_ROOT / row["target_markdown"]).read_text(encoding="utf-8")
        assert "Candidate pixels" in markdown
        assert "never redefine the target" in markdown


@pytest.mark.unit
def test_tracked_packets_have_exact_hashes_and_five_frame_case_policy() -> None:
    manifest = _manifest()
    policy = manifest["case_policy"]
    assert policy == {
        "mode": "all_declared_cases_x_all_wired_candidates",
        "case_count": 2,
        "candidate_count": 3,
        "candidate_case_rows": 6,
        "frames_per_candidate_case": 5,
        "target_semantics": "intended_source_brief_not_candidate_frame_truth",
    }
    assert len(list(DATASET_ROOT.glob("*/*/frames/*.jpg"))) == 30
    for case in manifest["cases"]:
        assert len(case["candidate_packets"]) == 3
        for packet in case["candidate_packets"]:
            clip_path = DATASET_ROOT / packet["clip_path"]
            meta_path = DATASET_ROOT / packet["meta_path"]
            frame_paths = sorted(clip_path.parent.glob("frames/*.jpg"))
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            assert packet["frame_count"] == len(frame_paths) == 5
            assert packet["clip_sha256"] == _sha256(clip_path) == meta["clip_sha256"]
            frame_hashes = [_sha256(path) for path in frame_paths]
            assert frame_hashes == packet["sampled_frame_sha256"]
            assert frame_hashes == meta["sampled_frame_sha256"]
            assert packet["sample_times_seconds"] == meta["sample_times_seconds"]
            assert packet["meta_sha256"] == _sha256(meta_path)
            assert meta["generation_cost_usd"] is None
            assert meta["generation_cost_status"] == (
                "unavailable_in_retained_runtime_result"
            )


@pytest.mark.unit
def test_task_uses_opaque_ids_and_intended_source_adherence_rubric() -> None:
    task = yaml.safe_load(TASK_PATH.read_text(encoding="utf-8"))
    assert len(task["providers"]) == 3
    assert len(task["tests"]) == 2
    for provider in task["providers"]:
        config = provider["config"]
        assert config["prompt_version"] == "final-render-provider-floor-v2"
        assert config["frame_policy"] == "five_interior_sixths_jpegs_v2"
        assert config["max_frames"] == 5
    rubric = " ".join(task["tests"][0]["assert"][1]["value"].lower().split())
    assert "intended source brief" in rubric
    assert "candidate pixels never redefine the target" in rubric
    assert "require empty audio fields" in rubric
    assert "excluded color, camera, motion, or audio" in rubric
    assert "pass only at score >= 0.8" in rubric
    for test in task["tests"]:
        vars_data = test["vars"]
        assert "clip_title" not in vars_data
        assert vars_data["evaluation_id"] != vars_data["clip_id"]
        assert vars_data["clip_id"] not in vars_data["evaluation_id"]


@pytest.mark.unit
def test_transport_prefers_declared_times_without_leaking_title_or_target() -> None:
    meta_path = next(DATASET_ROOT.glob("google_veo31/*/meta.json"))
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    times = sample_times_seconds(meta, frame_count=5)
    assert times == [1.333, 2.667, 4.0, 5.333, 6.667]
    text = build_user_text(
        "FRAME PROMPT",
        meta,
        evaluation_id="render_case_opaque",
        prompt_version="final-render-provider-floor-v2",
        frame_count=5,
        sample_times=times,
    )
    assert "render_case_opaque" in text
    assert meta["title"] not in text
    assert meta["clip_id"] not in text
    assert meta["candidate_label"] not in text
    assert meta["source_description"] not in text


@pytest.mark.unit
def test_retained_runtime_rebuild_is_offline_and_byte_reproducible(tmp_path: Path) -> None:
    before = _media_hashes(DATASET_ROOT)
    rebuilt_root = tmp_path / "rebuilt"
    rebuilt = generate_dataset(
        runtime_result_path=RUNTIME_PATH,
        fixture_manifest_path=FIXTURE_PATH,
        output_dir=rebuilt_root,
        retained_clip_root=DATASET_ROOT,
    )
    assert _media_hashes(DATASET_ROOT) == before
    assert _media_hashes(rebuilt_root) == before
    assert rebuilt["case_policy"] == _manifest()["case_policy"]
    assert rebuilt["generator_provenance"] == _manifest()["generator_provenance"]


@pytest.mark.unit
def test_generator_rejects_unquoted_candidate_derived_target(tmp_path: Path) -> None:
    payload = deepcopy(_fixture())
    payload["cases"][0]["target_provenance"]["criteria"]["tone_tags"][0][
        "quotes"
    ].append("A candidate-only visual claim that is absent from the screenplay.")
    bad_fixture = tmp_path / "bad-fixture.json"
    bad_fixture.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="not quoted from its declared scene"):
        generate_dataset(
            runtime_result_path=RUNTIME_PATH,
            fixture_manifest_path=bad_fixture,
            output_dir=tmp_path / "unused",
            retained_clip_root=DATASET_ROOT,
        )


@pytest.mark.unit
def test_historical_v1_quality_report_is_non_decision_grade() -> None:
    summary = build_summary(
        runtime_payload=json.loads(RUNTIME_PATH.read_text(encoding="utf-8")),
        promptfoo_payload=json.loads(QUALITY_PATH.read_text(encoding="utf-8")),
        dataset_root=DATASET_ROOT,
    )
    assert summary["evidence_status"] == "contaminated-non-decision-grade"
    assert summary["recommendation"]["decision"] == (
        "hold_current_default_repaired_rerun_required"
    )


def _report(tmp_path: Path, entries: list[dict], runtime_payload: dict) -> dict:
    return build_summary(
        runtime_payload=runtime_payload,
        promptfoo_payload={"results": {"results": entries}},
        dataset_root=tmp_path,
    )


def _complete_report_inputs(tmp_path: Path) -> tuple[list[dict], dict]:
    runtime_payload = complete_runtime_payload(TASK_PATH)
    write_task_manifest(tmp_path, TASK_PATH, runtime_payload)
    return (
        complete_quality_entries(TASK_PATH, REPO_ROOT / "benchmarks", tmp_path),
        runtime_payload,
    )


@pytest.mark.unit
def test_v2_report_accepts_exact_replayed_task_matrix(tmp_path: Path) -> None:
    entries, runtime_payload = _complete_report_inputs(tmp_path)
    summary = _report(tmp_path, entries, runtime_payload)
    assert summary["evidence_status"] == "decision-grade"
    assert len(summary["candidates"]) == 3
    assert all(row["quality_python"] == 1.0 for row in summary["candidates"])
    assert all(row["quality_rubric"] == 0.9 for row in summary["candidates"])
    assert all(row["quality_overall"] == 0.95 for row in summary["candidates"])
    assert all(row["calls"] == 2 for row in summary["candidates"])


@pytest.mark.unit
@pytest.mark.parametrize("mutation", RUNTIME_CONTRACT_MUTATIONS)
def test_runtime_contract_rejects_adversarial_false_greens(mutation: str) -> None:
    assert runtime_contract_accepts(TASK_PATH)
    assert not runtime_contract_accepts(TASK_PATH, mutation)


@pytest.mark.unit
def test_runtime_runner_reuses_its_retained_nested_elapsed_measurement() -> None:
    assert runner_uses_retained_nested_elapsed(REPO_ROOT)


@pytest.mark.unit
@pytest.mark.parametrize("mutation", REPORT_EVIDENCE_MUTATIONS)
def test_report_rejects_incomplete_or_contradictory_evidence(
    tmp_path: Path, mutation: str
) -> None:
    entries, runtime_payload = _complete_report_inputs(tmp_path)
    apply_evidence_mutation(
        mutation,
        dataset_root=tmp_path,
        entries=entries,
        runtime_payload=runtime_payload,
    )
    summary = _report(tmp_path, entries, runtime_payload)
    assert summary["evidence_status"] == "contaminated-non-decision-grade"
    assert summary["recommendation"]["decision"] == (
        "hold_current_default_repaired_rerun_required"
    )


@pytest.mark.unit
def test_report_ranks_recomputed_scores_and_switches_from_registry_default(
    tmp_path: Path,
) -> None:
    entries, runtime_payload = _complete_report_inputs(tmp_path)
    prepare_switch(entries, runtime_payload, "google_veo31_fast")
    summary = _report(tmp_path, entries, runtime_payload)
    assert summary["previous_default"] == "google_veo31"
    assert summary["candidates"][0]["candidate_variant"] == "google_veo31_fast"
    assert summary["candidates"][0]["quality_overall"] == 1.0
    assert summary["recommendation"]["decision"] == "switch_default_to_google_veo31_fast"


@pytest.mark.unit
@pytest.mark.parametrize(
    ("overrides", "expected_gate"),
    [
        ({"quality_overall": 0.73}, "quality"),
        ({"mean_total_elapsed_ms": 300_001}, "latency"),
        ({"mean_total_cost_usd": 0.021}, "cost"),
    ],
)
def test_switch_requires_every_registry_absolute_gate(
    overrides: dict[str, float], expected_gate: str
) -> None:
    baseline = _decision_row("google_veo31", quality=0.69, direct_inputs=3)
    challenger = _decision_row("google_veo31_fast", quality=0.9, direct_inputs=3)
    challenger.update(overrides)
    result = _recommend([baseline, challenger], policy=_registry_policy())
    assert result["decision"] == "keep_current_default_target_missed"
    assert expected_gate in result["rationale"]
    qualified = _decision_row("qualified", quality=0.85, direct_inputs=3)
    result = _recommend([baseline, challenger, qualified], policy=_registry_policy())
    assert result["decision"] == "switch_default_to_qualified"


def _decision_row(variant: str, *, quality: float, direct_inputs: int) -> dict:
    return {
        "candidate_variant": variant,
        "candidate_label": variant,
        "engine_pack_id": variant,
        "success_ratio": 1.0,
        "quality_overall": quality,
        "mean_total_elapsed_ms": 100_000,
        "mean_total_cost_usd": 0.01,
        "mean_reference_usage_counts": {"input_reference": direct_inputs},
    }


@pytest.mark.unit
def test_registry_quarantines_every_historical_quality_score() -> None:
    registry = yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    entry = next(item for item in registry["evals"] if item["id"] == "final-render-provider-floor")
    assert entry["historical_evidence_status"] == "contaminated-non-decision-grade"
    assert entry["test_case_policy"]["candidate_case_rows"] == 6
    assert entry["test_case_policy"]["frames_per_candidate_case"] == 5
    assert all(
        score["evidence_status"] == "contaminated-non-decision-grade"
        for score in entry["scores"]
    )
    assert entry["manual_frame_inspection"]["coverage"].startswith("30/30")
    assert _registry_default() == entry["default_model"] == "google_veo31"
    assert _registry_policy() == {
        "default_model": "google_veo31",
        "quality_min": 0.74,
        "latency_max": 300_000.0,
        "cost_max": 0.02,
    }


@pytest.mark.unit
def test_touched_final_render_eval_sources_stay_within_size_limits() -> None:
    for relative in TOUCHED_PYTHON_FILES:
        path = REPO_ROOT / relative
        source = path.read_text(encoding="utf-8")
        assert len(source.splitlines()) < 400, relative
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                size = (node.end_lineno or node.lineno) - node.lineno + 1
                assert size <= 100, f"{relative}:{node.name}"

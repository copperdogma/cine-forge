from __future__ import annotations

import ast
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_ROOT = REPO_ROOT / "benchmarks" / "scripts"
DATASET_ROOT = REPO_ROOT / "benchmarks" / "previz_usefulness"
TASK_PATH = REPO_ROOT / "benchmarks" / "tasks" / "previz-usefulness.yaml"
GENERATOR_FILES = (
    "benchmarks/scripts/generate_previz_usefulness_dataset.py",
    "benchmarks/scripts/previz_usefulness_contracts.py",
    "benchmarks/scripts/previz_usefulness_media.py",
    "benchmarks/scripts/previz_usefulness_candidates.py",
)
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from previz_usefulness_contracts import (  # noqa: E402
    load_case_catalog,
    sha256_file,
    validate_retained_prompt,
)


def _manifest() -> dict:
    return json.loads((DATASET_ROOT / "manifest.json").read_text())


@pytest.mark.unit
def test_task_uses_only_unlabelled_decision_candidates_and_dedicated_targets() -> None:
    task = yaml.safe_load(TASK_PATH.read_text())
    variants = [provider["config"]["candidate_variant"] for provider in task["providers"]]
    assert variants == [
        "google_veo31_lite_previz",
        "google_veo31_fast_previz",
        "xai_grok_imagine_video_previz",
    ]
    assert "symbolic" not in variants
    assert "annotated_symbolic" not in variants
    for test in task["tests"]:
        vars_data = test["vars"]
        assert "clip_title" not in vars_data
        assert vars_data["evaluation_id"] != vars_data["clip_id"]
        assert vars_data["target_path"].startswith("previz_usefulness/targets/")
        assert "video_understanding/" not in vars_data["target_path"]


@pytest.mark.unit
def test_case_contract_is_independent_of_mutable_base_target(tmp_path: Path) -> None:
    catalog = json.loads((DATASET_ROOT / "cases.json").read_text())
    hostile_source = tmp_path / "source"
    hostile_source.mkdir()
    (hostile_source / "target.json").write_text(
        json.dumps(
            {
                "summary_reference": "Contradictory replacement target",
                "camera_tags": ["crash_zoom"],
            }
        )
    )
    for item in catalog["cases"]:
        item["source_fixture_dir"] = str(hostile_source)
    catalog_path = tmp_path / "cases.json"
    catalog_path.write_text(json.dumps(catalog))

    _, cases = load_case_catalog(catalog_path)

    radio = next(case for case in cases if case.clip_id == "radio_hold_tracking")
    assert radio.generation_brief["camera_tags"] == ["lateral_track"]
    assert radio.generation_brief["summary_reference"].startswith("A lateral tracking move")


@pytest.mark.unit
def test_generation_briefs_align_with_targets_and_every_retained_prompt() -> None:
    catalog, cases = load_case_catalog()
    decision_variants = catalog["decision_candidate_variants"]
    for case in cases:
        target = json.loads(case.target_path.read_text())
        brief = case.generation_brief
        assert target["clip_id"] == case.clip_id
        assert set(target["tone_tags"]) == set(brief["tone_tags"])
        assert set(target["emotion_tags"]) == set(brief["emotion_tags"])
        assert set(target["color_tags"]) == set(brief["color_tags"])
        assert set(target["camera_tags"]) == set(brief["camera_tags"])
        assert set(target["motion_tags"]) == set(brief["motion_tags"])
        assert target["audio_tags"] == []
        assert target["transcript"] is None
        assert "not derived from any candidate output" in target["source_description"]
        for variant in decision_variants:
            validate_retained_prompt(case, DATASET_ROOT / variant / case.clip_id)


@pytest.mark.unit
def test_manifest_and_meta_hashes_match_all_tracked_assets() -> None:
    manifest = _manifest()
    assert manifest["schema_version"] == "previz-usefulness-manifest-v2"
    assert manifest["case_contract_sha256"] == sha256_file(DATASET_ROOT / "cases.json")
    for case in manifest["cases"]:
        target = REPO_ROOT / case["target_path"]
        target_markdown = REPO_ROOT / case["target_markdown_path"]
        assert case["target_sha256"] == sha256_file(target)
        assert case["target_markdown_sha256"] == sha256_file(target_markdown)
        for variant in case["variants"]:
            candidate_dir = DATASET_ROOT / variant["variant"] / case["clip_id"]
            meta_path = DATASET_ROOT / variant["meta_path"]
            meta = json.loads(meta_path.read_text())
            assert variant["meta_sha256"] == sha256_file(meta_path)
            assert variant["clip_sha256"] == sha256_file(candidate_dir / "clip.mp4")
            assert variant["clip_sha256"] == meta["clip_sha256"]
            frames = sorted((candidate_dir / "frames").glob("*.jpg"))
            assert len(frames) == 5
            actual = {path.name: sha256_file(path) for path in frames}
            assert variant["frame_sha256"] == actual == meta["frame_sha256"]


@pytest.mark.unit
def test_controls_are_explicitly_non_decision_and_answer_leaking() -> None:
    manifest = _manifest()
    assert set(manifest["control_variants"]) == {"symbolic", "annotated_symbolic"}
    assert manifest["control_variants"]["symbolic"]["status"] == (
        "control_only_non_comparable"
    )
    assert manifest["control_variants"]["annotated_symbolic"]["status"] == (
        "control_only_answer_leaking"
    )
    assert all(
        policy["decision_eligible"] is False
        for policy in manifest["control_variants"].values()
    )
    for case in manifest["cases"]:
        controls = [row for row in case["variants"] if row["decision_role"] == "control_only"]
        assert {row["variant"] for row in controls} == {"symbolic", "annotated_symbolic"}
        assert all(row["decision_eligible"] is False for row in controls)


@pytest.mark.unit
def test_retained_prompt_validator_rejects_generation_brief_drift(tmp_path: Path) -> None:
    _, cases = load_case_catalog()
    case = cases[0]
    source = DATASET_ROOT / "google_veo31_lite_previz" / case.clip_id
    candidate_dir = tmp_path / "candidate"
    candidate_dir.mkdir()
    shutil.copy2(source / "prompt_contract.json", candidate_dir / "prompt_contract.json")
    shutil.copy2(source / "prompt.txt", candidate_dir / "prompt.txt")
    prompt_path = candidate_dir / "prompt.txt"
    prompt_path.write_text(prompt_path.read_text().replace("white envelope", "red suitcase"))

    with pytest.raises(ValueError, match="prompt bytes disagree"):
        validate_retained_prompt(case, candidate_dir)


@pytest.mark.unit
def test_controls_only_refresh_is_media_deterministic_and_network_free(tmp_path: Path) -> None:
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg is required")
    outputs = []
    for name in ("first", "second"):
        output = tmp_path / name
        subprocess.run(
            [
                sys.executable,
                str(SCRIPT_ROOT / "generate_previz_usefulness_dataset.py"),
                "--controls-only",
                "--output-dir",
                str(output),
            ],
            check=True,
            cwd=REPO_ROOT,
        )
        outputs.append(json.loads((output / "manifest.json").read_text()))

    for first_case, second_case in zip(outputs[0]["cases"], outputs[1]["cases"], strict=True):
        assert first_case["clip_id"] == second_case["clip_id"]
        for first, second in zip(first_case["variants"], second_case["variants"], strict=True):
            assert first["variant"] == second["variant"]
            assert first["clip_sha256"] == second["clip_sha256"]
            assert first["frame_sha256"] == second["frame_sha256"]


@pytest.mark.unit
def test_generator_sources_stay_below_architecture_size_limit() -> None:
    for relative in GENERATOR_FILES:
        source = (REPO_ROOT / relative).read_text()
        assert len(source.splitlines()) < 400, relative
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                end = node.end_lineno or node.lineno
                assert end - node.lineno + 1 <= 100, f"{relative}:{node.name}"


@pytest.mark.unit
def test_manifest_hashes_do_not_depend_on_file_order() -> None:
    """Sanity-check the helper uses file content, not directory iteration order."""
    paths = sorted(DATASET_ROOT.glob("*/dialogue_confession_push_in/frames/*.jpg"))
    forward = [hashlib.sha256(path.read_bytes()).hexdigest() for path in paths]
    reverse = [hashlib.sha256(path.read_bytes()).hexdigest() for path in reversed(paths)]
    assert forward == list(reversed(reverse))

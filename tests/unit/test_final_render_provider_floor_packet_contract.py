from __future__ import annotations

import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
import yaml
from benchmarks.scripts.real_render_provider_floor_support import runtime_payload_sha256

from tests.unit.final_render_provider_floor_provenance_test_support import (
    refresh_manifest_runtime_fingerprint,
    write_task_manifest,
)
from tests.unit.final_render_provider_floor_runtime_test_support import (
    complete_runtime_payload,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
BENCHMARK_ROOT = REPO_ROOT / "benchmarks"
SCRIPT_ROOT = BENCHMARK_ROOT / "scripts"
TASK_PATH = BENCHMARK_ROOT / "tasks" / "final-render-provider-floor.yaml"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from final_render_provider_floor_generator_provenance import (  # noqa: E402
    REQUIRED_GENERATOR_FILES,
)
from final_render_provider_floor_packet_evidence import (  # noqa: E402
    validated_dataset_packets,
)
from final_render_provider_floor_task_contract import load_task_contract  # noqa: E402


def _inputs(dataset_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    task = yaml.safe_load(TASK_PATH.read_text(encoding="utf-8"))
    variants = {
        row["config"]["candidate_variant"]: row["label"] for row in task["providers"]
    }
    cases = [dict(row["vars"]) for row in task["tests"]]
    payload = complete_runtime_payload(TASK_PATH, variants=variants, cases=cases)
    payload.setdefault("eval_id", "final-render-provider-floor-runtime")
    payload.setdefault("measured_at", "2026-07-22T00:00:00+00:00")
    dataset_root.mkdir()
    write_task_manifest(
        dataset_root,
        TASK_PATH,
        payload,
        variants=variants,
        cases=cases,
    )
    contract = load_task_contract(TASK_PATH)
    assert contract is not None
    return payload, contract


def _validate(
    dataset_root: Path, payload: dict[str, Any], contract: dict[str, Any]
) -> object:
    return validated_dataset_packets(
        dataset_root=dataset_root,
        benchmark_root=BENCHMARK_ROOT,
        repo_root=REPO_ROOT,
        contract=contract,
        runtime_payload=payload,
    )


def _manifest(dataset_root: Path) -> dict[str, Any]:
    return json.loads((dataset_root / "manifest.json").read_text(encoding="utf-8"))


def _write_manifest(dataset_root: Path, manifest: dict[str, Any]) -> None:
    (dataset_root / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rewrite_packet_meta(
    dataset_root: Path, transform: Any
) -> dict[str, Any]:
    manifest = _manifest(dataset_root)
    packet = manifest["cases"][0]["candidate_packets"][0]
    meta_path = dataset_root / packet["meta_path"]
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    transform(meta)
    meta_path.write_text(json.dumps(meta), encoding="utf-8")
    packet["meta_sha256"] = _sha(meta_path)
    _write_manifest(dataset_root, manifest)
    return manifest


@pytest.mark.unit
def test_packet_contract_accepts_only_complete_hash_bound_matrix(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    payload, contract = _inputs(dataset)
    validated = _validate(dataset, payload, contract)
    assert validated is not None
    packets, provenance = validated
    assert set(packets) == contract["pairs"]
    assert set(provenance["files_sha256"]) == REQUIRED_GENERATOR_FILES


@pytest.mark.unit
@pytest.mark.parametrize(
    "mutation",
    ("extra_manifest", "extra_case", "extra_packet", "wrong_status", "wrong_title"),
)
def test_packet_contract_rejects_non_exact_manifest_shapes(
    tmp_path: Path, mutation: str
) -> None:
    dataset = tmp_path / "dataset"
    payload, contract = _inputs(dataset)
    manifest = _manifest(dataset)
    if mutation == "extra_manifest":
        manifest["untracked_policy"] = True
    elif mutation == "extra_case":
        manifest["cases"][0]["untracked_case_fact"] = True
    elif mutation == "extra_packet":
        manifest["cases"][0]["candidate_packets"][0]["untracked_packet_fact"] = True
    elif mutation == "wrong_status":
        manifest["historical_quality_evidence_status"] = "decision-grade"
    else:
        manifest["cases"][0]["title"] = "self-selected title"
    _write_manifest(dataset, manifest)
    assert _validate(dataset, payload, contract) is None


@pytest.mark.unit
@pytest.mark.parametrize(
    "mutation",
    (
        "missing_file",
        "extra_file",
        "stale_file",
        "missing_scope",
        "aliased_fixture",
        "aliased_runtime",
    ),
)
def test_packet_contract_rejects_self_selected_generator_provenance(
    tmp_path: Path, mutation: str
) -> None:
    dataset = tmp_path / "dataset"
    payload, contract = _inputs(dataset)
    manifest = _manifest(dataset)
    provenance = manifest["generator_provenance"]
    files = provenance["files_sha256"]
    if mutation == "missing_file":
        files.pop(next(iter(files)))
    elif mutation == "extra_file":
        files["benchmarks/scripts/untracked_generator.py"] = "0" * 64
    elif mutation == "stale_file":
        files[next(iter(files))] = "0" * 64
    elif mutation == "missing_scope":
        provenance.pop("runtime_result_scope")
    elif mutation == "aliased_fixture":
        provenance["fixture_manifest_path"] = (
            "benchmarks/fixtures/../fixtures/final_render_provider_floor_cases.json"
        )
    else:
        provenance["runtime_result_path"] = "./runtime-result.json"
    _write_manifest(dataset, manifest)
    assert _validate(dataset, payload, contract) is None


@pytest.mark.unit
def test_packet_contract_rejects_malformed_and_stale_raw_runtime(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    payload, contract = _inputs(dataset)
    manifest = _manifest(dataset)
    runtime_path = dataset / manifest["generator_provenance"]["runtime_result_path"]
    runtime_path.write_text("{malformed", encoding="utf-8")
    manifest["generator_provenance"]["runtime_result_sha256"] = _sha(runtime_path)
    _write_manifest(dataset, manifest)
    assert _validate(dataset, payload, contract) is None


@pytest.mark.unit
@pytest.mark.parametrize("artifact", ("manifest", "runtime"))
def test_packet_contract_rejects_duplicate_json_keys(
    tmp_path: Path, artifact: str
) -> None:
    dataset = tmp_path / "dataset"
    payload, contract = _inputs(dataset)
    manifest_path = dataset / "manifest.json"
    manifest = _manifest(dataset)
    if artifact == "manifest":
        original = manifest_path.read_text(encoding="utf-8")
        manifest_path.write_text(
            '{"contract_version":"shadow",' + original[1:], encoding="utf-8"
        )
    else:
        provenance = manifest["generator_provenance"]
        runtime_path = dataset / provenance["runtime_result_path"]
        original = runtime_path.read_text(encoding="utf-8")
        runtime_path.write_text(
            '{"eval_id":"shadow",' + original[1:], encoding="utf-8"
        )
        provenance["runtime_result_sha256"] = _sha(runtime_path)
        _write_manifest(dataset, manifest)
    assert _validate(dataset, payload, contract) is None


@pytest.mark.unit
def test_packet_contract_rejects_self_consistent_but_different_raw_runtime(
    tmp_path: Path,
) -> None:
    dataset = tmp_path / "dataset"
    payload, contract = _inputs(dataset)
    manifest = _manifest(dataset)
    raw = deepcopy(payload)
    raw["measured_at"] = "2026-07-23T00:00:00+00:00"
    runtime_path = dataset / manifest["generator_provenance"]["runtime_result_path"]
    runtime_path.write_text(json.dumps(raw), encoding="utf-8")
    runtime_sha = _sha(runtime_path)
    manifest["generator_provenance"].update(
        runtime_result_sha256=runtime_sha,
        runtime_payload_sha256=runtime_payload_sha256(raw),
    )
    for case in manifest["cases"]:
        for packet in case["candidate_packets"]:
            meta_path = dataset / packet["meta_path"]
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            meta["runtime_provenance"]["runtime_result_sha256"] = runtime_sha
            meta_path.write_text(json.dumps(meta), encoding="utf-8")
            packet["meta_sha256"] = _sha(meta_path)
    _write_manifest(dataset, manifest)
    assert _validate(dataset, payload, contract) is None


@pytest.mark.unit
@pytest.mark.parametrize(
    "mutation", ("wrong_eval", "naive_timestamp", "wrong_fixture_sha", "extra_field")
)
def test_packet_contract_rejects_self_consistent_wrong_runtime_envelope(
    tmp_path: Path, mutation: str
) -> None:
    dataset = tmp_path / "dataset"
    payload, contract = _inputs(dataset)
    if mutation == "wrong_eval":
        payload["eval_id"] = "another-eval"
    elif mutation == "naive_timestamp":
        payload["measured_at"] = "2026-07-22T00:00:00"
    elif mutation == "wrong_fixture_sha":
        payload["fixture_manifest_sha256"] = "0" * 64
    else:
        payload["untracked"] = True
    refresh_manifest_runtime_fingerprint(dataset, payload)
    assert _validate(dataset, payload, contract) is None


@pytest.mark.unit
@pytest.mark.parametrize("artifact", ("target", "provenance", "markdown"))
def test_packet_contract_rejects_self_hashed_staged_target_substitutions(
    tmp_path: Path, artifact: str
) -> None:
    dataset = tmp_path / "dataset"
    payload, contract = _inputs(dataset)
    manifest = _manifest(dataset)
    case = manifest["cases"][0]
    path_key = {
        "target": "target_path",
        "provenance": "target_provenance_path",
        "markdown": "target_markdown",
    }[artifact]
    hash_key = {
        "target": "target_sha256",
        "provenance": "target_provenance_sha256",
        "markdown": "target_markdown_sha256",
    }[artifact]
    artifact_path = dataset / case[path_key]
    if artifact == "markdown":
        artifact_path.write_text("Self-selected target.\n", encoding="utf-8")
    else:
        value = json.loads(artifact_path.read_text(encoding="utf-8"))
        value["self_selected"] = True
        artifact_path.write_text(json.dumps(value), encoding="utf-8")
    case[hash_key] = _sha(artifact_path)
    _write_manifest(dataset, manifest)
    assert _validate(dataset, payload, contract) is None


@pytest.mark.unit
def test_packet_contract_derives_markdown_from_fixture_even_when_task_agrees(
    tmp_path: Path,
) -> None:
    dataset = tmp_path / "dataset"
    payload, contract = _inputs(dataset)
    manifest = _manifest(dataset)
    case = manifest["cases"][0]
    markdown = dataset / case["target_markdown"]
    markdown.write_text("Task-aligned but source-unbacked target.\n", encoding="utf-8")
    case["target_markdown_sha256"] = _sha(markdown)
    _write_manifest(dataset, manifest)
    contract = deepcopy(contract)
    contract["cases"][case["case_id"]]["target_markdown_path"] = markdown
    assert _validate(dataset, payload, contract) is None


@pytest.mark.unit
@pytest.mark.parametrize(
    "mutation", ("stale_sha", "missing_field", "extra_field", "extra_meta_field")
)
def test_packet_contract_rejects_packet_runtime_provenance_drift(
    tmp_path: Path, mutation: str
) -> None:
    dataset = tmp_path / "dataset"
    payload, contract = _inputs(dataset)

    def mutate(meta: dict[str, Any]) -> None:
        runtime = meta["runtime_provenance"]
        if mutation == "extra_meta_field":
            meta["untracked"] = True
        elif mutation == "stale_sha":
            runtime["runtime_result_sha256"] = "0" * 64
        elif mutation == "missing_field":
            runtime.pop("project_dir")
        else:
            runtime["untracked"] = True

    _rewrite_packet_meta(dataset, mutate)
    assert _validate(dataset, payload, contract) is None


@pytest.mark.unit
def test_packet_contract_rejects_aliased_and_symlinked_packet_paths(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    payload, contract = _inputs(dataset)
    manifest = _manifest(dataset)
    packet = manifest["cases"][0]["candidate_packets"][0]
    packet["clip_path"] = str((dataset / packet["clip_path"]).resolve())
    _write_manifest(dataset, manifest)
    assert _validate(dataset, payload, contract) is None

    payload, contract = _inputs(tmp_path / "second-dataset")
    second = tmp_path / "second-dataset"
    manifest = _manifest(second)
    packet = manifest["cases"][0]["candidate_packets"][0]
    meta_path = second / packet["meta_path"]
    outside = tmp_path / "outside-meta.json"
    outside.write_bytes(meta_path.read_bytes())
    meta_path.unlink()
    meta_path.symlink_to(outside)
    assert _validate(second, payload, contract) is None


@pytest.mark.unit
def test_runtime_fingerprint_refresh_rebinds_raw_and_packet_metadata(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    payload, contract = _inputs(dataset)
    payload["measured_at"] = "2026-07-23T00:00:00+00:00"
    refresh_manifest_runtime_fingerprint(dataset, payload)
    manifest = _manifest(dataset)
    provenance = manifest["generator_provenance"]
    runtime_path = dataset / provenance["runtime_result_path"]
    runtime_sha = _sha(runtime_path)
    assert json.loads(runtime_path.read_text(encoding="utf-8")) == payload
    assert provenance["runtime_result_sha256"] == runtime_sha
    assert provenance["runtime_payload_sha256"] == runtime_payload_sha256(payload)
    for case in manifest["cases"]:
        for packet in case["candidate_packets"]:
            meta_path = dataset / packet["meta_path"]
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            assert meta["runtime_provenance"]["runtime_result_sha256"] == runtime_sha
            assert packet["meta_sha256"] == _sha(meta_path)
    assert _validate(dataset, payload, contract) is not None

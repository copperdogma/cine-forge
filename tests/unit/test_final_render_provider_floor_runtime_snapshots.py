from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import pytest
import yaml

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
DATASET_ROOT = BENCHMARK_ROOT / "final_render_provider_floor"
RUNTIME_PATH = BENCHMARK_ROOT / "results" / (
    "final-render-provider-floor-story-169-runtime-fixed-2026-04-16.json"
)
FIXTURE_PATH = BENCHMARK_ROOT / "fixtures" / "final_render_provider_floor_cases.json"
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from final_render_provider_floor_dataset_packets import (  # noqa: E402
    _resolve_source_material,
)
from final_render_provider_floor_packet_evidence import (  # noqa: E402
    validated_dataset_packets,
)
from final_render_provider_floor_runtime_evidence import (  # noqa: E402
    validated_runtime_rows,
)
from final_render_provider_floor_task_contract import load_task_contract  # noqa: E402
from generate_final_render_provider_floor_dataset import generate_dataset  # noqa: E402


def _inputs(dataset_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    task = yaml.safe_load(TASK_PATH.read_text(encoding="utf-8"))
    variants = {
        row["config"]["candidate_variant"]: row["label"] for row in task["providers"]
    }
    cases = [dict(row["vars"]) for row in task["tests"]]
    payload = complete_runtime_payload(TASK_PATH, variants=variants, cases=cases)
    dataset_root.mkdir()
    write_task_manifest(
        dataset_root, TASK_PATH, payload, variants=variants, cases=cases
    )
    contract = load_task_contract(TASK_PATH)
    assert contract is not None
    return payload, contract


def _full_validate(
    dataset_root: Path, payload: dict[str, Any], contract: dict[str, Any]
) -> object:
    packet_result = validated_dataset_packets(
        dataset_root=dataset_root,
        benchmark_root=BENCHMARK_ROOT,
        repo_root=REPO_ROOT,
        contract=contract,
        runtime_payload=payload,
    )
    if packet_result is None:
        return None
    packets, provenance = packet_result
    return validated_runtime_rows(
        payload=payload,
        contract=contract,
        packets=packets,
        provenance=provenance,
    )


def _manifest(dataset_root: Path) -> dict[str, Any]:
    return json.loads((dataset_root / "manifest.json").read_text(encoding="utf-8"))


def _write_manifest(dataset_root: Path, value: dict[str, Any]) -> None:
    (dataset_root / "manifest.json").write_text(json.dumps(value), encoding="utf-8")


def _first_packet(dataset_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = _manifest(dataset_root)
    return manifest, manifest["cases"][0]["candidate_packets"][0]


def _multi_input_packet(dataset_root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    manifest = _manifest(dataset_root)
    packets = manifest["cases"][0]["candidate_packets"]
    packet = next(row for row in packets if len(row["runtime_evidence"]["direct_inputs"]) > 1)
    return manifest, packet


def _rewrite_snapshot_artifact(
    dataset_root: Path, kind: str, transform: Any
) -> None:
    manifest, packet = _first_packet(dataset_root)
    record = packet["runtime_evidence"][kind]
    path = dataset_root / record["path"]
    value = json.loads(path.read_text(encoding="utf-8"))
    transform(value)
    path.write_text(json.dumps(value), encoding="utf-8")
    record["sha256"] = _sha(path)
    _write_manifest(dataset_root, manifest)


def _rewrite_first_meta(dataset_root: Path, transform: Any) -> None:
    manifest, packet = _first_packet(dataset_root)
    path = dataset_root / packet["meta_path"]
    meta = json.loads(path.read_text(encoding="utf-8"))
    transform(meta)
    path.write_text(json.dumps(meta), encoding="utf-8")
    packet["meta_sha256"] = _sha(path)
    _write_manifest(dataset_root, manifest)


@pytest.mark.unit
def test_self_consistent_fabricated_resolved_input_cannot_be_rehashed_green(
    tmp_path: Path,
) -> None:
    dataset = tmp_path / "dataset"
    payload, contract = _inputs(dataset)
    row = payload["runs"][0]["resolved_inputs"][0]
    row.update(
        input_id="fabricated-input",
        relative_path="artifacts/fabricated/reference.png",
        source_ref={
            "artifact_type": "fabricated_manifest",
            "entity_id": "fabricated",
            "path": "artifacts/fabricated_manifest/fabricated/v1.json",
            "version": 1,
        },
    )
    refresh_manifest_runtime_fingerprint(dataset, payload)
    assert _full_validate(dataset, payload, contract) is None


@pytest.mark.unit
@pytest.mark.parametrize("kind", ("render_prompt", "generated_video"))
def test_missing_runtime_artifact_snapshot_is_rejected(
    tmp_path: Path, kind: str
) -> None:
    dataset = tmp_path / "dataset"
    payload, contract = _inputs(dataset)
    _manifest_value, packet = _first_packet(dataset)
    (dataset / packet["runtime_evidence"][kind]["path"]).unlink()
    assert _full_validate(dataset, payload, contract) is None


@pytest.mark.unit
def test_rehashed_artifact_envelope_extra_metadata_is_rejected(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    payload, contract = _inputs(dataset)
    _rewrite_snapshot_artifact(
        dataset,
        "render_prompt",
        lambda value: value["metadata"].__setitem__("untracked", True),
    )
    assert _full_validate(dataset, payload, contract) is None


@pytest.mark.unit
@pytest.mark.parametrize("mutation", ("model", "resolved_input"))
def test_rehashed_compiled_prompt_contradictions_are_rejected(
    tmp_path: Path, mutation: str
) -> None:
    dataset = tmp_path / "dataset"
    payload, contract = _inputs(dataset)

    def mutate(value: dict[str, Any]) -> None:
        if mutation == "model":
            value["data"]["target_model"] = "fabricated-model"
        else:
            value["data"]["resolved_inputs"][0]["input_id"] = "fabricated-input"

    _rewrite_snapshot_artifact(dataset, "render_prompt", mutate)
    assert _full_validate(dataset, payload, contract) is None


@pytest.mark.unit
@pytest.mark.parametrize("mutation", ("no_required_input", "required_prompt_context"))
def test_artifact_snapshots_require_real_direct_conditioning(
    tmp_path: Path, mutation: str
) -> None:
    dataset = tmp_path / "dataset"
    payload, contract = _inputs(dataset)

    def mutate(value: dict[str, Any]) -> None:
        rows = value["data"]["resolved_inputs"]
        if mutation == "no_required_input":
            for row in rows:
                row["required"] = False
        else:
            next(row for row in rows if row["used_as"] == "prompt_context")[
                "required"
            ] = True

    _rewrite_snapshot_artifact(dataset, "render_prompt", mutate)
    _rewrite_snapshot_artifact(dataset, "generated_video", mutate)
    assert _full_validate(dataset, payload, contract) is None


@pytest.mark.unit
@pytest.mark.parametrize(
    "mutation",
    (
        "target_model",
        "request_id",
        "cost",
        "cost_model",
        "duplicate_cost_model",
        "empty_cost_model_segment",
    ),
)
def test_rehashed_generated_artifact_contradictions_are_rejected(
    tmp_path: Path, mutation: str
) -> None:
    dataset = tmp_path / "dataset"
    payload, contract = _inputs(dataset)

    def mutate(value: dict[str, Any]) -> None:
        data = value["data"]
        if mutation == "target_model":
            data["target_model"] = "fabricated-model"
        elif mutation == "request_id":
            data["request_id"] = "fabricated-request"
        elif mutation == "cost":
            data["cost"]["estimated_cost_usd"] = 9.0
        elif mutation == "cost_model":
            data["cost"]["model"] = "fabricated-model"
        elif mutation == "duplicate_cost_model":
            data["cost"]["model"] += f"+{data['target_model']}"
        else:
            data["cost"]["model"] = data["cost"]["model"].replace("+", "++")

    _rewrite_snapshot_artifact(dataset, "generated_video", mutate)
    assert _full_validate(dataset, payload, contract) is None


@pytest.mark.unit
@pytest.mark.parametrize(
    "mutation", ("missing", "extra", "duplicate_row", "hash_drift", "duplicate_bytes")
)
def test_direct_input_snapshot_set_is_exact_and_byte_distinct(
    tmp_path: Path, mutation: str
) -> None:
    dataset = tmp_path / "dataset"
    payload, contract = _inputs(dataset)
    manifest, packet = _multi_input_packet(dataset)
    rows = packet["runtime_evidence"]["direct_inputs"]
    first = dataset / rows[0]["snapshot_path"]
    if mutation == "missing":
        first.unlink()
    elif mutation == "extra":
        (first.parent / "untracked.bin").write_bytes(b"untracked")
    elif mutation == "duplicate_row":
        rows[1] = dict(rows[0])
        _write_manifest(dataset, manifest)
    elif mutation == "hash_drift":
        first.write_bytes(b"mutated")
    else:
        second = dataset / rows[1]["snapshot_path"]
        second.write_bytes(first.read_bytes())
        rows[1]["sha256"] = _sha(second)
        _write_manifest(dataset, manifest)
    assert _full_validate(dataset, payload, contract) is None


@pytest.mark.unit
def test_packet_clip_must_equal_captured_generated_media_sha(tmp_path: Path) -> None:
    dataset = tmp_path / "dataset"
    payload, contract = _inputs(dataset)
    manifest, packet = _first_packet(dataset)
    packet["runtime_evidence"]["generated_media_sha256"] = "0" * 64
    _write_manifest(dataset, manifest)
    assert _full_validate(dataset, payload, contract) is None


@pytest.mark.unit
@pytest.mark.parametrize("field", ("request_notes", "active_project_references"))
def test_runtime_narrative_provenance_must_equal_artifact_snapshot(
    tmp_path: Path, field: str
) -> None:
    dataset = tmp_path / "dataset"
    payload, contract = _inputs(dataset)
    value = ["fabricated note"] if field == "request_notes" else [{"fabricated": True}]
    payload["runs"][0][field] = value
    _rewrite_first_meta(dataset, lambda meta: meta.__setitem__(field, value))
    refresh_manifest_runtime_fingerprint(dataset, payload)
    assert _full_validate(dataset, payload, contract) is None


@pytest.mark.unit
def test_retained_decision_grade_snapshots_survive_offline_reuse(tmp_path: Path) -> None:
    retained = tmp_path / "retained"
    payload, _contract = _inputs(retained)
    run = payload["runs"][0]
    destination = tmp_path / "rebuilt"
    packet_root = destination / run["candidate_variant"] / run["case_id"]
    packet_root.mkdir(parents=True)
    material = _resolve_source_material(
        run=run,
        packet_root=packet_root,
        dataset_root=destination,
        repo_root=tmp_path / "empty-repo",
        retained_root=retained,
    )
    assert material["runtime_evidence"]["status"] == (
        "decision-grade-runtime-snapshots-v1"
    )
    assert material["generated"] is not None
    assert (packet_root / "runtime_evidence/render_prompt.json").is_file()
    assert (packet_root / "runtime_evidence/generated_video.json").is_file()


@pytest.mark.unit
@pytest.mark.parametrize("tamper", ("direct_input_bytes", "prompt_text"))
def test_offline_reuse_rejects_bytes_stale_against_source_manifest(
    tmp_path: Path, tamper: str
) -> None:
    retained = tmp_path / "retained"
    payload, _contract = _inputs(retained)
    run = payload["runs"][0]
    _source_manifest, source_packet = _first_packet(retained)
    evidence = source_packet["runtime_evidence"]
    if tamper == "direct_input_bytes":
        path = retained / evidence["direct_inputs"][0]["snapshot_path"]
        path.write_bytes(b"schema-independent byte tamper")
    else:
        path = retained / evidence["render_prompt"]["path"]
        prompt = json.loads(path.read_text(encoding="utf-8"))
        prompt["data"]["prompt_text"] = "Schema-valid but source-manifest-stale prompt."
        path.write_text(json.dumps(prompt), encoding="utf-8")
    destination = tmp_path / "rebuilt"
    packet_root = destination / run["candidate_variant"] / run["case_id"]
    packet_root.mkdir(parents=True)
    with pytest.raises(ValueError, match="source manifest"):
        _resolve_source_material(
            run=run,
            packet_root=packet_root,
            dataset_root=destination,
            repo_root=tmp_path / "empty-repo",
            retained_root=retained,
        )


@pytest.mark.unit
def test_historical_retained_media_only_dataset_has_no_decision_grade_packets() -> None:
    payload = json.loads(RUNTIME_PATH.read_text(encoding="utf-8"))
    contract = load_task_contract(TASK_PATH)
    assert contract is not None
    assert validated_dataset_packets(
        dataset_root=DATASET_ROOT,
        benchmark_root=BENCHMARK_ROOT,
        repo_root=REPO_ROOT,
        contract=contract,
        runtime_payload=payload,
    ) is None


@pytest.mark.unit
def test_generator_rejects_nested_duplicate_fixture_keys(tmp_path: Path) -> None:
    source = FIXTURE_PATH.read_text(encoding="utf-8")
    duplicated = source.replace(
        '"case_id": "open_frequency_scene_001_studio_night",',
        '"case_id": "open_frequency_scene_001_studio_night",\n'
        '      "case_id": "shadow_case",',
        1,
    )
    assert duplicated != source
    fixture = tmp_path / "duplicate-fixture.json"
    fixture.write_text(duplicated, encoding="utf-8")
    with pytest.raises(ValueError):
        generate_dataset(
            runtime_result_path=RUNTIME_PATH,
            fixture_manifest_path=fixture,
            output_dir=tmp_path / "unused",
            retained_clip_root=DATASET_ROOT,
        )


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

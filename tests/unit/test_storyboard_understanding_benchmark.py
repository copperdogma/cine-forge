from __future__ import annotations

import importlib
import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest
from PIL import Image

from cine_forge.ai.errors import LLMCallError
from cine_forge.evals.retained_media import build_file_inventory, sha256_file
from tests.unit.storyboard_quality_test_support import good_analysis, target_for

REPO_ROOT = Path(__file__).resolve().parents[2]
PROVIDER_ROOT = REPO_ROOT / "benchmarks" / "providers"
SCORER_ROOT = REPO_ROOT / "benchmarks" / "scorers"
for path in (PROVIDER_ROOT, SCORER_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

provider = importlib.import_module("storyboard_understanding_provider")
scorer = importlib.import_module("storyboard_understanding_scorer")


def _write_jpeg(path: Path, color: tuple[int, int, int]) -> None:
    Image.new("RGB", (64, 64), color=color).save(path, format="JPEG", quality=90)


def _write_target(tmp_path: Path, case_id: str) -> Path:
    path = tmp_path / f"{case_id}.json"
    path.write_text(json.dumps(target_for(case_id)), encoding="utf-8")
    return path


def _seal_packet_dataset(sequence: Path) -> tuple[Path, str, str]:
    meta_path = sequence / "meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["assets_sha256_file"] = "assets.sha256.json"
    meta.setdefault("source_grid_count", 0)
    meta.setdefault("storyboard_artifact_count", 0)
    meta_path.write_text(json.dumps(meta, sort_keys=True), encoding="utf-8")

    assets = []
    for kind, directory in (("frame", "frames"), ("reference", "references")):
        for index, path in enumerate(sorted((sequence / directory).glob("*.jpg")), start=1):
            assets.append(
                {
                    "kind": kind,
                    "ordinal_id": f"{kind}_{index:03d}",
                    "relative_path": path.relative_to(sequence).as_posix(),
                    "source_runtime_path": f"fixture/{path.name}",
                    "sha256": sha256_file(path),
                    "bytes": path.stat().st_size,
                }
            )
    asset_manifest = sequence / "assets.sha256.json"
    asset_manifest.write_text(json.dumps({"assets": assets}, sort_keys=True), encoding="utf-8")

    dataset_root = sequence.parents[1]
    manifest_path = dataset_root / "manifest.json"
    manifest = {
        "schema_version": "storyboard-generation-quality-v3",
        "expected_cases": [sequence.name],
        "sequences": [
            {
                "candidate_variant": sequence.parent.name,
                "storyboard_id": sequence.name,
                "asset_manifest": asset_manifest.relative_to(dataset_root).as_posix(),
            }
        ],
        "file_inventory": build_file_inventory(dataset_root),
    }
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    return manifest_path, sha256_file(manifest_path), sha256_file(asset_manifest)


@pytest.mark.unit
def test_provider_subject_text_is_opaque() -> None:
    meta = {
        "storyboard_id": "sbq_case_002",
        "title": "Open Frequency reference-conditioned sequence",
        "scene_ids": ["scene_001", "scene_002"],
        "frame_count": 15,
        "available_reference_image_count": 4,
        "prompt_reference_frame_count": 15,
        "direct_reference_input_count": 35,
        "reference_transport_supported": True,
        "recurring_character_names": ["ARIA", "NOAH"],
        "reference_images": [
            {"label": "Aria character reference"},
            {"label": "Radio studio location reference"},
        ],
    }
    text = provider._build_user_text(
        "Return observations.", meta, prompt_version="storyboard-understanding-v3"
    )
    assert "storyboard_id: sbq_case_002" in text
    assert "frame_count: 15" in text
    assert "reference_count: 2" in text
    for leaked in (
        "Open Frequency",
        "scene_001",
        "ARIA",
        "NOAH",
        "Aria character reference",
        "prompt_reference_frame_count",
        "direct_reference_input_count",
        "reference_transport_supported",
    ):
        assert leaked not in text


@pytest.mark.unit
def test_payload_builders_preserve_neutral_image_order() -> None:
    images = [
        {
            "kind": "storyboard_frame",
            "label": "frame_001",
            "mime_type": "image/jpeg",
            "base64": "a",
        },
        {
            "kind": "storyboard_frame",
            "label": "frame_002",
            "mime_type": "image/jpeg",
            "base64": "b",
        },
        {
            "kind": "reference_image",
            "label": "reference_001",
            "mime_type": "image/jpeg",
            "base64": "c",
        },
    ]
    openai = provider._build_openai_payload(
        model="gpt-5.4", user_text="Inspect.", images=images, max_tokens=2000, temperature=0.0
    )
    anthropic = provider._build_anthropic_payload(
        model="claude-opus-4-6",
        user_text="Inspect.",
        images=images,
        max_tokens=2000,
        temperature=0.0,
    )
    gemini = provider._build_gemini_payload(user_text="Inspect.", images=images, max_tokens=65536)
    expected_labels = [
        "Generated storyboard frame frame_001",
        "Generated storyboard frame frame_002",
        "Supplied reference image reference_001",
    ]
    assert [item["text"] for item in openai["messages"][0]["content"][1::2]] == expected_labels
    assert [item["text"] for item in anthropic["messages"][0]["content"][1::2]] == expected_labels
    assert [item["text"] for item in gemini["contents"][0]["parts"][1::2]] == expected_labels
    assert [
        item["image_url"]["url"].split(",", 1)[1] for item in openai["messages"][0]["content"][2::2]
    ] == ["a", "b", "c"]
    assert [item["source"]["data"] for item in anthropic["messages"][0]["content"][2::2]] == [
        "a",
        "b",
        "c",
    ]
    assert [item["inlineData"]["data"] for item in gemini["contents"][0]["parts"][2::2]] == [
        "a",
        "b",
        "c",
    ]
    assert "temperature" not in gemini["generationConfig"]


@pytest.mark.unit
def test_gemini_cost_includes_hidden_thinking_but_keeps_visible_completion() -> None:
    token_usage = {"prompt": 100, "completion": 10, "total": 1110}

    billed_completion = provider._completion_tokens_for_cost("google", token_usage)

    assert billed_completion == 1010
    assert token_usage["completion"] == 10
    assert provider.estimate_cost_usd(
        "gemini-3.5-flash-lite",
        token_usage["prompt"],
        billed_completion,
    ) == pytest.approx(0.002555)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("token_usage", "message"),
    [
        ({}, "prompt_tokens must be a nonnegative integer"),
        (
            {"prompt": -1, "completion": 0},
            "prompt_tokens must be a nonnegative integer",
        ),
        (
            {"prompt": False, "completion": 0},
            "prompt_tokens must be a nonnegative integer",
        ),
        (
            {"prompt": 1, "completion": "2"},
            "visible_completion_tokens must be a nonnegative integer",
        ),
        (
            {"prompt": 100, "completion": 10, "total": 109},
            "total_tokens must be at least",
        ),
        (
            {
                "prompt": 100,
                "completion": 10,
                "total": 1110,
                "billed_completion": 10,
            },
            "billed_completion_tokens does not match",
        ),
    ],
)
def test_gemini_cost_rejects_malformed_or_inconsistent_usage(
    token_usage: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        provider._completion_tokens_for_cost("google", token_usage)


@pytest.mark.unit
def test_storyboard_gemini_transport_rejects_impossible_usage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self) -> bytes:
            return json.dumps(
                {
                    "candidates": [{"content": {"parts": [{"text": "{}"}]}}],
                    "usageMetadata": {
                        "promptTokenCount": 100,
                        "candidatesTokenCount": 10,
                        "totalTokenCount": 109,
                    },
                }
            ).encode("utf-8")

    monkeypatch.setattr(provider._transport, "require_env", lambda _: "test-key")
    monkeypatch.setattr(
        provider._transport.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: FakeResponse(),
    )

    with pytest.raises(ValueError, match="total_tokens must be at least"):
        provider._call_gemini(
            model="gemini-3.6-flash",
            user_text="Inspect.",
            images=[],
            max_tokens=65_536,
            temperature=0.0,
        )


@pytest.mark.unit
def test_storyboard_gemini_transport_rejects_reasoning_total_disagreement(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self) -> bytes:
            return json.dumps(
                {
                    "candidates": [{"content": {"parts": [{"text": "{}"}]}}],
                    "usageMetadata": {
                        "promptTokenCount": 100,
                        "candidatesTokenCount": 10,
                        "thoughtsTokenCount": 1000,
                        "totalTokenCount": 1111,
                    },
                }
            ).encode("utf-8")

    monkeypatch.setattr(provider._transport, "require_env", lambda _: "test-key")
    monkeypatch.setattr(
        provider._transport.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: FakeResponse(),
    )

    with pytest.raises(ValueError, match="does not reconcile"):
        provider._call_gemini(
            model="gemini-3.6-flash",
            user_text="Inspect.",
            images=[],
            max_tokens=65_536,
            temperature=0.0,
        )


@pytest.mark.unit
def test_storyboard_gemini_transport_retains_raw_usage_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_response = {
        "responseId": "gemini-storyboard-1",
        "candidates": [{"content": {"parts": [{"text": "{}"}]}}],
        "usageMetadata": {
            "promptTokenCount": 100,
            "candidatesTokenCount": 10,
            "thoughtsTokenCount": 1000,
            "totalTokenCount": 1110,
        },
        "modelVersion": "gemini-3.6-flash",
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self) -> bytes:
            return json.dumps(raw_response).encode("utf-8")

    monkeypatch.setattr(provider._transport, "require_env", lambda _: "test-key")
    monkeypatch.setattr(
        provider._transport.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: FakeResponse(),
    )

    result = provider._call_gemini(
        model="gemini-3.6-flash",
        user_text="Inspect.",
        images=[],
        max_tokens=65_536,
        temperature=0.0,
    )

    assert result["raw"] == {
        "responseId": "gemini-storyboard-1",
        "usageMetadata": raw_response["usageMetadata"],
        "modelVersion": "gemini-3.6-flash",
    }
    assert result["token_usage"]["billed_completion"] == 1010


@pytest.mark.unit
def test_storyboard_gemini_transport_requires_response_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw_response = {
        "modelVersion": "gemini-3.6-flash",
        "candidates": [{"content": {"parts": [{"text": "{}"}]}}],
        "usageMetadata": {"promptTokenCount": 1, "candidatesTokenCount": 1},
    }

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self) -> bytes:
            return json.dumps(raw_response).encode("utf-8")

    monkeypatch.setattr(provider._transport, "require_env", lambda _: "test-key")
    monkeypatch.setattr(
        provider._transport.urllib.request,
        "urlopen",
        lambda *_args, **_kwargs: FakeResponse(),
    )

    with pytest.raises(LLMCallError, match="must be a non-empty string"):
        provider._call_gemini(
            model="gemini-3.6-flash",
            user_text="Inspect.",
            images=[],
            max_tokens=65_536,
            temperature=0.0,
        )


@pytest.mark.unit
def test_packet_loader_sends_every_declared_image_without_sampling(tmp_path: Path) -> None:
    sequence = tmp_path / "dataset" / "candidate" / "sbq_case_002"
    frames = sequence / "frames"
    references = sequence / "references"
    frames.mkdir(parents=True)
    references.mkdir()
    for index in range(1, 10):
        _write_jpeg(frames / f"{index:02d}_semantic_shot_name.jpg", (index * 10, 40, 80))
    for index in range(1, 3):
        _write_jpeg(references / f"person_name_{index}.jpg", (40, index * 30, 20))
    (sequence / "meta.json").write_text(
        json.dumps(
            {
                "storyboard_id": "sbq_case_002",
                "frame_count": 9,
                "reference_images": [{"label": "secret one"}, {"label": "secret two"}],
            }
        ),
        encoding="utf-8",
    )
    _manifest_path, dataset_sha256, asset_sha256 = _seal_packet_dataset(sequence)
    packet = provider._load_storyboard_packet(
        sequence_dir=sequence, max_frames=32, max_references=8
    )
    assert [item["label"] for item in packet["frames"]] == [
        f"frame_{index:03d}" for index in range(1, 10)
    ]
    assert [item["label"] for item in packet["references"]] == [
        "reference_001",
        "reference_002",
    ]
    assert packet["dataset_manifest_sha256"] == dataset_sha256
    assert packet["asset_manifest_sha256"] == asset_sha256
    with pytest.raises(RuntimeError, match="silent sampling is forbidden"):
        provider._load_storyboard_packet(sequence_dir=sequence, max_frames=8, max_references=8)


@pytest.mark.unit
def test_packet_loader_rejects_manifest_count_mismatch(tmp_path: Path) -> None:
    sequence = tmp_path / "dataset" / "candidate" / "sbq_case_001"
    frames = sequence / "frames"
    frames.mkdir(parents=True)
    _write_jpeg(frames / "01.jpg", (20, 40, 80))
    (sequence / "meta.json").write_text(
        json.dumps({"storyboard_id": "sbq_case_001", "frame_count": 2, "reference_images": []}),
        encoding="utf-8",
    )
    _seal_packet_dataset(sequence)
    with pytest.raises(RuntimeError, match="frame packet mismatch"):
        provider._load_storyboard_packet(sequence_dir=sequence, max_frames=32, max_references=8)


@pytest.mark.unit
@pytest.mark.parametrize("mutation", ["changed", "extra"])
def test_packet_loader_rejects_changed_or_unlisted_media(
    tmp_path: Path,
    mutation: str,
) -> None:
    sequence = tmp_path / "dataset" / "candidate" / "sbq_case_001"
    frames = sequence / "frames"
    references = sequence / "references"
    frames.mkdir(parents=True)
    references.mkdir()
    frame = frames / "001.jpg"
    _write_jpeg(frame, (20, 40, 80))
    (sequence / "meta.json").write_text(
        json.dumps(
            {"storyboard_id": "sbq_case_001", "frame_count": 1, "reference_images": []}
        ),
        encoding="utf-8",
    )
    _seal_packet_dataset(sequence)
    if mutation == "changed":
        _write_jpeg(frame, (200, 40, 80))
    else:
        _write_jpeg(frames / "002.jpg", (20, 200, 80))

    with pytest.raises(ValueError, match="retained media"):
        provider._load_storyboard_packet(
            sequence_dir=sequence,
            max_frames=32,
            max_references=8,
        )


@pytest.mark.unit
def test_provider_response_binds_exact_retained_packet(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sequence = tmp_path / "dataset" / "candidate" / "sbq_case_001"
    frames = sequence / "frames"
    references = sequence / "references"
    frames.mkdir(parents=True)
    references.mkdir()
    for index in range(1, 9):
        _write_jpeg(frames / f"{index:03d}.jpg", (index * 10, 40, 80))
    (sequence / "meta.json").write_text(
        json.dumps(
            {
                "storyboard_id": "sbq_case_001",
                "candidate_variant": "candidate",
                "frame_count": 8,
                "reference_images": [],
            }
        ),
        encoding="utf-8",
    )
    _manifest_path, dataset_sha256, asset_sha256 = _seal_packet_dataset(sequence)
    model_output = good_analysis(case_id="sbq_case_001")
    model_output.pop("packet_frame_count")
    model_output.pop("packet_reference_count")

    monkeypatch.setattr(
        provider,
        "_dispatch_request",
        lambda **_kwargs: {
            "output": json.dumps(model_output),
            "token_usage": {"prompt": 10, "completion": 10, "total": 20},
            "raw": {
                "id": "storyboard-call-1",
                "model": "gpt-5.4",
                "usage": {"input_tokens": 10, "output_tokens": 10},
            },
        },
    )
    result = provider.call_api(
        "Inspect the packet.",
        {
            "config": {
                "basePath": str(tmp_path),
                "provider": "openai",
                "model": "gpt-5.4",
                "prompt_version": "storyboard-understanding-v3",
                "max_frames": 32,
                "max_references": 8,
            }
        },
        {"vars": {"storyboard_id": "sbq_case_001", "sequence_dir": str(sequence)}},
    )

    assert "error" not in result
    assert result["metadata"]["dataset_manifest_sha256"] == dataset_sha256
    assert result["metadata"]["asset_manifest_sha256"] == asset_sha256


@pytest.mark.unit
def test_provider_injects_trusted_packet_counts() -> None:
    model_output = json.dumps({"storyboard_id": "sbq_case_001", "summary": "visible"})
    output = json.loads(
        provider._attach_packet_contract(
            model_output,
            storyboard_id="sbq_case_001",
            frame_count=15,
            reference_count=0,
        )
    )
    assert output["packet_frame_count"] == 15
    assert output["packet_reference_count"] == 0
    with pytest.raises(ValueError, match="provider-owned"):
        provider._attach_packet_contract(
            json.dumps(
                {
                    "storyboard_id": "sbq_case_001",
                    "packet_frame_count": 999,
                }
            ),
            storyboard_id="sbq_case_001",
            frame_count=15,
            reference_count=0,
        )


@pytest.mark.unit
def test_source_grounded_observations_clear_current_scorer(tmp_path: Path) -> None:
    target_path = _write_target(tmp_path, "sbq_case_002")
    score = scorer.score_output_against_target(
        output=good_analysis(case_id="sbq_case_002"),
        target_path=target_path,
        model_label="fixture",
        prompt_version=scorer.PROMPT_VERSION,
    )
    assert score.hard_constraints_passed is True
    assert score.overall_score >= 0.9


@pytest.mark.unit
def test_old_self_report_and_fenced_json_are_rejected() -> None:
    old_payload = {
        "storyboard_id": "sbq_case_001",
        "summary": "radio storm antenna lantern",
        "keywords": ["radio", "storm", "antenna", "lantern"],
        "style_assessment": {"consistency_status": "consistent", "observed_mediums": ["perfect"]},
        "character_assessments": [],
        "reference_assessments": [],
        "readable_text_present": False,
        "prop_only_non_insert_present": False,
        "evidence": [{"frame_id": "fake", "cue": "trust me"}],
        "overall_confidence": 1.0,
    }
    with pytest.raises(ValueError):
        scorer.parse_prediction(old_payload)
    with pytest.raises(json.JSONDecodeError):
        scorer.parse_prediction(
            f"```json\n{json.dumps(good_analysis(case_id='sbq_case_001'))}\n```"
        )


@pytest.mark.unit
def test_semantic_leak_invalid_ids_and_generic_traits_fail(tmp_path: Path) -> None:
    target_path = _write_target(tmp_path, "sbq_case_001")
    baseline = good_analysis(case_id="sbq_case_001")
    good = scorer.score_output_against_target(
        output=baseline,
        target_path=target_path,
        model_label="fixture",
        prompt_version=scorer.PROMPT_VERSION,
    )

    leaked = deepcopy(baseline)
    leaked["summary"] = "ARIA and NOAH in Open Frequency"
    leaked_score = scorer.score_output_against_target(
        output=leaked,
        target_path=target_path,
        model_label="fixture",
        prompt_version=scorer.PROMPT_VERSION,
    )
    assert leaked_score.hard_constraints_passed is False

    dominated = deepcopy(baseline)
    dominated["evidence"][0] = {
        "frame_id": "frame_999",
        "cue": "No radio studio, no console, and no storm is visible.",
    }
    for assessment in dominated["character_assessments"]:
        assessment["first_half_traits"] = ["person", "human"]
        assessment["second_half_traits"] = ["person", "human"]
    dominated_score = scorer.score_output_against_target(
        output=dominated,
        target_path=target_path,
        model_label="fixture",
        prompt_version=scorer.PROMPT_VERSION,
    )
    assert dominated_score.hard_constraints_passed is False
    assert dominated_score.overall_score < good.overall_score


@pytest.mark.unit
def test_prediction_rejects_extra_schema_keys() -> None:
    payload = good_analysis(case_id="sbq_case_001")
    payload["quality_status"] = "perfect"
    with pytest.raises(ValueError):
        scorer.parse_prediction(payload)

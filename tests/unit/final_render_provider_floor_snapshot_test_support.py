"""Typed synthetic runtime snapshots for final-render provenance tests."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from benchmarks.scripts.real_render_provider_floor_support import CANDIDATE_SPECS

from cine_forge.schemas import (
    Artifact,
    ArtifactMetadata,
    ArtifactRef,
    CompiledRenderPrompt,
    CostRecord,
    GeneratedVideoArtifact,
    MediaFile,
)


def write_runtime_snapshot_fixture(
    *,
    dataset_root: Path,
    packet_root: Path,
    run: dict[str, Any],
    fixture_case: dict[str, Any],
    clip: Path,
) -> dict[str, Any]:
    """Persist a complete synthetic decision-grade runtime evidence subtree."""
    prompt_envelope, prompt, generated_envelope, _generated = snapshot_models(
        run, scene_heading=fixture_case["target_provenance"]["scene_heading"]
    )
    evidence_root = packet_root / "runtime_evidence"
    evidence_root.mkdir()
    prompt_path = evidence_root / "render_prompt.json"
    generated_path = evidence_root / "generated_video.json"
    _write_json(prompt_path, prompt_envelope.model_dump(mode="json"))
    _write_json(generated_path, generated_envelope.model_dump(mode="json"))
    direct_root = evidence_root / "direct_inputs"
    direct_root.mkdir()
    direct_rows = []
    for index, source in enumerate(
        row for row in prompt.resolved_inputs if row.used_as in DIRECT_USES
    ):
        path = direct_root / f"input_{index:02d}.bin"
        path.write_bytes(f"direct:{source.input_id}:{index}".encode())
        direct_rows.append(
            {
                "input_id": source.input_id,
                "used_as": source.used_as,
                "source_relative_path": source.relative_path,
                "snapshot_path": str(path.relative_to(dataset_root)),
                "sha256": _sha256(path),
            }
        )
    return {
        "status": "decision-grade-runtime-snapshots-v1",
        "render_prompt": _record(prompt_path, dataset_root),
        "generated_video": _record(generated_path, dataset_root),
        "generated_media_sha256": _sha256(clip),
        "direct_inputs": direct_rows,
    }


def runtime_snapshot_for_run(run: dict[str, Any]) -> dict[str, Any]:
    """Return internal typed evidence for runtime-contract-only unit tests."""
    prompt_envelope, prompt, generated_envelope, generated = snapshot_models(
        run, scene_heading="INT. SYNTHETIC RUNTIME CONTRACT - NIGHT"
    )
    return {
        "prompt_envelope": prompt_envelope,
        "compiled_prompt": prompt,
        "generated_envelope": generated_envelope,
        "generated_video": generated,
        "generated_media_sha256": "a" * 64,
        "direct_inputs": [
            {
                "input_id": row.input_id,
                "used_as": row.used_as,
                "source_relative_path": row.relative_path,
            }
            for row in prompt.resolved_inputs
            if row.used_as in DIRECT_USES
        ],
    }


def snapshot_models(
    run: dict[str, Any], *, scene_heading: str
) -> tuple[Artifact, CompiledRenderPrompt, Artifact, GeneratedVideoArtifact]:
    """Build mutually linked typed prompt and generated-video envelopes."""
    spec = CANDIDATE_SPECS[run["candidate_variant"]]
    scene_ref = _ref("scene", run["scene_id"], f"artifacts/scene/{run['scene_id']}/v1.json")
    shot_ref = _ref(
        "shot_plan", run["scene_id"], f"artifacts/shot_plan/{run['scene_id']}/v1.json"
    )
    prompt_ref = _ref("render_prompt", run["scene_id"], run["render_prompt_path"])
    generated_ref = _ref(
        "generated_video", run["scene_id"], run["generated_video_artifact_path"]
    )
    prompt = CompiledRenderPrompt(
        scene_id=run["scene_id"],
        scene_number=int(run["scene_id"].removeprefix("scene_")),
        scene_heading=scene_heading,
        scene_ref=scene_ref,
        shot_plan_ref=shot_ref,
        target_provider=spec.provider,
        target_model=run["target_model"],
        engine_pack_id=run["engine_pack_id"],
        compiler_model="gpt-5.4-mini",
        requested_duration_seconds=run["duration_seconds"],
        resolved_duration_seconds=run["duration_seconds"],
        resolution=run["resolution"],
        aspect_ratio=run["aspect_ratio"],
        prompt_text="Generate the exact source-grounded synthetic test scene.",
        sections=[
            {"section_id": "scene", "title": "Scene", "body": scene_heading}
        ],
        completeness={"included_categories": ["scene"]},
        resolved_inputs=run["resolved_inputs"],
        creative_brief_preview={
            "active_project_references": run["active_project_references"]
        },
    )
    generated = GeneratedVideoArtifact(
        scene_id=prompt.scene_id,
        scene_number=prompt.scene_number,
        scene_heading=prompt.scene_heading,
        scene_ref=scene_ref,
        shot_plan_ref=shot_ref,
        prompt_ref=prompt_ref,
        video=MediaFile(
            relative_path=run["generated_media_path"],
            media_type="video/mp4",
            duration_seconds=run["duration_seconds"],
        ),
        duration_seconds=run["duration_seconds"],
        resolution=run["resolution"],
        aspect_ratio=run["aspect_ratio"],
        target_provider=spec.provider,
        target_model=run["target_model"],
        engine_pack_id=run["engine_pack_id"],
        request_id=run["request_id"],
        cost=CostRecord(
            model=f"gpt-5.4-mini+{run['target_model']}",
            input_tokens=1,
            output_tokens=1,
            estimated_cost_usd=run["total_cost_usd"],
            request_id=run["request_id"],
        ),
        resolved_inputs=run["resolved_inputs"],
    )
    return (
        _envelope(prompt_ref, prompt, annotations={}),
        prompt,
        _envelope(
            generated_ref,
            generated,
            annotations={"request_notes": run["request_notes"]},
        ),
        generated,
    )


DIRECT_USES = {"input_reference", "reference_image"}


def _envelope(
    ref: ArtifactRef, model: Any, *, annotations: dict[str, Any]
) -> Artifact:
    return Artifact(
        metadata=ArtifactMetadata(
            ref=ref,
            intent="synthetic final-render provenance contract",
            rationale="exercise exact durable packet evidence",
            confidence=1.0,
            source="code",
            annotations=annotations,
        ),
        data=model.model_dump(mode="json"),
    )


def _ref(artifact_type: str, entity_id: str, path: str) -> ArtifactRef:
    return ArtifactRef(
        artifact_type=artifact_type, entity_id=entity_id, version=1, path=path
    )


def _record(path: Path, root: Path) -> dict[str, str]:
    return {"path": str(path.relative_to(root)), "sha256": _sha256(path)}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

"""Provider-candidate retention and explicitly requested generation for previz usefulness."""

from __future__ import annotations

import json
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

from previz_usefulness_contracts import (
    CASE_CATALOG_PATH,
    CandidateSpec,
    PrevizCase,
    asset_hashes,
    relative_to_repo,
    sha256_file,
    validate_retained_prompt,
)
from previz_usefulness_media import clip_has_audio, ensure_five_frames, extract_sample_frames

from cine_forge.ai.video import VideoGenerationRequest, generate_video
from cine_forge.modules.generation.render_adapter_v1.previz_prompting import (
    compile_low_fidelity_previz_prompt,
)
from cine_forge.modules.generation.render_adapter_v1.support import (
    load_engine_pack,
    normalize_duration_seconds,
)


def preserve_candidate(
    *,
    ffmpeg: str,
    ffprobe: str | None,
    dataset_root: Path,
    case: PrevizCase,
    candidate: CandidateSpec,
) -> dict[str, Any]:
    """Validate and provenance an existing paid candidate without changing media/prompt bytes."""
    destination = dataset_root / candidate.variant / case.clip_id
    for name in ("clip.mp4", "prompt.txt", "prompt_contract.json", "meta.json"):
        if not (destination / name).exists():
            raise ValueError(f"Missing retained AI candidate artifact: {destination / name}")
    meta = json.loads((destination / "meta.json").read_text(encoding="utf-8"))
    ensure_five_frames(
        ffmpeg=ffmpeg,
        candidate_dir=destination,
        duration_seconds=float(meta["duration_seconds"]),
    )
    validate_retained_prompt(case, destination)
    return _write_candidate_meta(
        destination=destination,
        case=case,
        candidate=candidate,
        previous_meta=meta,
        ffprobe=ffprobe,
        retained=True,
    )


def generate_candidate(
    *,
    ffmpeg: str,
    ffprobe: str | None,
    dataset_root: Path,
    case: PrevizCase,
    candidate: CandidateSpec,
) -> dict[str, Any]:
    """Generate one paid candidate only after the caller supplied the explicit CLI opt-in."""
    engine_pack = load_engine_pack(candidate.pack_id)
    duration = _benchmark_duration_seconds(engine_pack=engine_pack, source_duration_seconds=4.0)
    resolution = _benchmark_resolution(engine_pack)
    aspect_ratio = _benchmark_aspect_ratio(engine_pack)
    prompt_contract = compile_low_fidelity_previz_prompt(
        brief=case.shot_brief(),
        engine_pack=engine_pack,
        prompt_profile=candidate.prompt_profile,
    )
    request = VideoGenerationRequest(
        prompt=prompt_contract.prompt_text,
        duration_seconds=duration,
        resolution=resolution,
        aspect_ratio=aspect_ratio,
        provider_params={},
    )
    started = time.perf_counter()
    result = generate_video(request=request, engine_pack=engine_pack)
    latency_ms = round((time.perf_counter() - started) * 1000)

    destination = dataset_root / candidate.variant / case.clip_id
    with tempfile.TemporaryDirectory(
        prefix=f".{candidate.variant}-{case.clip_id}-",
        dir=dataset_root,
    ) as raw:
        staging = Path(raw) / "candidate"
        staging.mkdir()
        (staging / "clip.mp4").write_bytes(result.video_bytes)
        (staging / "prompt_contract.json").write_text(
            prompt_contract.model_dump_json(indent=2) + "\n"
        )
        (staging / "prompt.txt").write_text(prompt_contract.prompt_text + "\n")
        extract_sample_frames(
            ffmpeg=ffmpeg,
            clip_path=staging / "clip.mp4",
            output_dir=staging / "frames",
            duration_seconds=float(duration),
            sample_count=5,
        )
        source_meta = json.loads((case.source_fixture_dir / "meta.json").read_text())
        source_meta.update(
            {
                "duration_seconds": float(duration),
                "resolution": resolution,
                "engine_pack_id": engine_pack.pack_id,
                "target_model": result.model_used,
                "generation_latency_ms": latency_ms,
                "estimated_generation_cost_usd": _estimated_generation_cost_usd(
                    engine_pack=engine_pack,
                    duration_seconds=float(duration),
                ),
                "consistency_strategy": prompt_contract.consistency_strategy,
                "prompt_profile": prompt_contract.prompt_profile,
                "style_profile_id": prompt_contract.style_profile.profile_id,
                "style_profile_title": prompt_contract.style_profile.title,
                "style_profile_summary": prompt_contract.style_profile.summary,
                "negative_prompt_terms": prompt_contract.negative_prompt_terms,
            }
        )
        (staging / "meta.json").write_text(json.dumps(source_meta, indent=2) + "\n")
        meta = _write_candidate_meta(
            destination=staging,
            case=case,
            candidate=candidate,
            previous_meta=source_meta,
            ffprobe=ffprobe,
            retained=False,
        )
        if destination.exists():
            shutil.rmtree(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(staging), str(destination))
    return meta


def _write_candidate_meta(
    *,
    destination: Path,
    case: PrevizCase,
    candidate: CandidateSpec,
    previous_meta: dict[str, Any],
    ffprobe: str | None,
    retained: bool,
) -> dict[str, Any]:
    hashes = asset_hashes(destination)
    meta = dict(previous_meta)
    meta.update(
        {
            "clip_id": case.clip_id,
            "title": case.title,
            "candidate_variant": candidate.variant,
            "candidate_label": candidate.label,
            "analysis_frame_policy": "five_ordered_jpegs_v1",
            "operator_lane": "ai_previz",
            "decision_role": "decision_candidate",
            "decision_eligible": True,
            "artifact_status": (
                "retained_candidate_regrade_ready"
                if retained
                else "fresh_candidate_regrade_ready"
            ),
            "retained_clip_bytes": retained,
            "retained_frame_bytes": retained,
            "retained_prompt_bytes": retained,
            "has_audio": clip_has_audio(
                ffprobe=ffprobe,
                clip_path=destination / "clip.mp4",
            ),
            "case_contract_path": relative_to_repo(CASE_CATALOG_PATH),
            "case_contract_sha256": sha256_file(CASE_CATALOG_PATH),
            "target_path": relative_to_repo(case.target_path),
            "target_sha256": sha256_file(case.target_path),
            "prompt_path": "prompt.txt",
            "prompt_contract_path": "prompt_contract.json",
            **hashes,
        }
    )
    (destination / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta


def _benchmark_duration_seconds(*, engine_pack: Any, source_duration_seconds: float) -> int:
    requested = float(
        engine_pack.request_defaults.get("benchmark_default_duration_seconds")
        or source_duration_seconds
    )
    duration, _ = normalize_duration_seconds(
        requested,
        engine_pack.limits.supported_durations_seconds,
    )
    return int(duration)


def _benchmark_resolution(engine_pack: Any) -> str:
    defaults = engine_pack.request_defaults
    if defaults.get("default_resolution"):
        return str(defaults["default_resolution"])
    if defaults.get("landscape_size"):
        return str(defaults["landscape_size"])
    supported = list(engine_pack.limits.supported_resolutions)
    if not supported:
        raise ValueError(f"{engine_pack.pack_id} has no supported resolutions")
    return str(supported[0])


def _benchmark_aspect_ratio(engine_pack: Any) -> str:
    defaults = engine_pack.request_defaults
    if defaults.get("landscape_aspect_ratio"):
        return str(defaults["landscape_aspect_ratio"])
    supported = list(engine_pack.limits.supported_aspect_ratios)
    if "16:9" in supported:
        return "16:9"
    if not supported:
        raise ValueError(f"{engine_pack.pack_id} has no supported aspect ratios")
    return str(supported[0])


def _estimated_generation_cost_usd(*, engine_pack: Any, duration_seconds: float) -> float | None:
    raw = engine_pack.request_defaults.get("benchmark_cost_per_second_usd")
    return None if raw in (None, "") else round(float(raw) * duration_seconds, 4)

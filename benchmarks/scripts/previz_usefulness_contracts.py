"""Contracts and provenance helpers for the maintained previz-usefulness dataset."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cine_forge.modules.generation.render_adapter_v1.previz_prompting import PrevizShotBrief
from cine_forge.schemas import VideoAnalysisTarget

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_ROOT = REPO_ROOT / "benchmarks" / "previz_usefulness"
CASE_CATALOG_PATH = DATASET_ROOT / "cases.json"
SOURCE_ROOT = REPO_ROOT / "benchmarks" / "video_understanding"
BASELINE_VARIANTS = ("symbolic", "annotated_symbolic")
DEFAULT_CANDIDATE_PACKS = (
    "google_veo31_lite",
    "google_veo31_fast",
    "xai_grok_imagine_video",
)

_AI_VARIANTS_BY_PACK = {
    "openai_sora2": ("openai_sora2", "openai_sora2_previz", "Sora 2 Previz", "standard"),
    "google_veo31_fast": (
        "google_veo31_fast",
        "google_veo31_fast_previz",
        "Veo 3.1 Fast Previz",
        "standard",
    ),
    "google_veo31_lite": (
        "google_veo31_lite",
        "google_veo31_lite_previz",
        "Veo 3.1 Lite Previz",
        "standard",
    ),
    "google_veo31_lite_compact": (
        "google_veo31_lite",
        "google_veo31_lite_compact_previz",
        "Veo 3.1 Lite Compact Previz",
        "compact",
    ),
    "google_veo31": ("google_veo31", "google_veo31_previz", "Veo 3.1 Previz", "standard"),
    "xai_grok_imagine_video": (
        "xai_grok_imagine_video",
        "xai_grok_imagine_video_previz",
        "Grok Imagine Previz",
        "standard",
    ),
}


@dataclass(frozen=True)
class CandidateSpec:
    """One provider-backed candidate lane."""

    pack_id: str
    variant: str
    label: str
    prompt_profile: str = "standard"


@dataclass(frozen=True)
class PrevizCase:
    """Source-authored generation intent plus its frame-observable target projection."""

    evaluation_id: str
    clip_id: str
    title: str
    source_fixture_dir: Path
    target_path: Path
    target_markdown_path: Path
    character_labels: tuple[str, ...]
    generation_brief: dict[str, Any]

    def shot_brief(self) -> PrevizShotBrief:
        """Build the prompt compiler input without consulting the mutable base eval target."""
        return PrevizShotBrief(
            clip_id=self.clip_id,
            title=self.title,
            character_labels=list(self.character_labels),
            **self.generation_brief,
        )


def candidate_specs(*, pack_ids: tuple[str, ...], include_ai: bool) -> list[CandidateSpec]:
    """Resolve selected engine packs to stable dataset variants."""
    if not include_ai:
        return []
    specs: list[CandidateSpec] = []
    for pack_id in pack_ids:
        candidate_info = _AI_VARIANTS_BY_PACK.get(pack_id)
        if candidate_info is None:
            raise ValueError(f"Unsupported previz candidate pack id: {pack_id}")
        engine_pack_id, variant, label, prompt_profile = candidate_info
        specs.append(
            CandidateSpec(
                pack_id=engine_pack_id,
                variant=variant,
                label=label,
                prompt_profile=prompt_profile,
            )
        )
    return specs


def load_case_catalog(path: Path = CASE_CATALOG_PATH) -> tuple[dict[str, Any], list[PrevizCase]]:
    """Load and validate the dedicated previz contract catalog."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "previz-usefulness-case-contract-v1":
        raise ValueError("Unsupported previz-usefulness case contract schema")
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list) or not raw_cases:
        raise ValueError("Previz case catalog must define at least one case")

    cases = [_case_from_payload(item) for item in raw_cases]
    _require_unique([case.clip_id for case in cases], field_name="clip_id")
    _require_unique([case.evaluation_id for case in cases], field_name="evaluation_id")
    return payload, cases


def validate_retained_prompt(case: PrevizCase, candidate_dir: Path) -> None:
    """Prove a retained prompt contract contains the catalog's authored generation brief."""
    prompt_path = candidate_dir / "prompt.txt"
    contract_path = candidate_dir / "prompt_contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    prompt_text = str(contract.get("prompt_text", ""))
    if prompt_path.read_text(encoding="utf-8") != prompt_text + "\n":
        raise ValueError(
            f"Retained prompt bytes disagree with prompt_contract.json: {candidate_dir}"
        )

    brief = case.generation_brief
    required_fragments = [
        f"Characters to keep distinct: {', '.join(case.character_labels)}.",
        f"Shot brief: {brief['summary_reference']}",
        f"Tone cue: {', '.join(brief['tone_tags'])}.",
        f"Color cue: {', '.join(brief['color_tags'])}.",
        f"Continuity anchor: {'; '.join(brief['continuity_notes'])}",
        f"Audio cue: {brief['audio_description']}",
    ]
    dialogue = brief.get("transcript")
    if dialogue:
        required_fragments.append(f"Dialogue cue: {dialogue}")
    missing = [fragment for fragment in required_fragments if fragment not in prompt_text]
    if missing:
        raise ValueError(
            f"Retained prompt does not match source case {case.clip_id}: {missing}"
        )


def asset_hashes(directory: Path) -> dict[str, Any]:
    """Return exact hashes for the clip, ordered frames, and retained prompt artifacts."""
    clip_path = directory / "clip.mp4"
    frames = sorted((directory / "frames").glob("*.jpg"))
    if not clip_path.exists():
        raise ValueError(f"Missing candidate clip: {clip_path}")
    if len(frames) != 5:
        raise ValueError(
            f"Expected exactly five tracked frames in {directory}, found {len(frames)}"
        )
    hashes: dict[str, Any] = {
        "clip_sha256": sha256_file(clip_path),
        "frame_sha256": {path.name: sha256_file(path) for path in frames},
    }
    for name in ("prompt.txt", "prompt_contract.json"):
        path = directory / name
        if path.exists():
            hashes[name.replace(".", "_") + "_sha256"] = sha256_file(path)
    return hashes


def sha256_file(path: Path) -> str:
    """Hash one artifact without loading it all into memory."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_to_repo(path: Path) -> str:
    """Return a stable repository-relative provenance path."""
    return str(path.resolve().relative_to(REPO_ROOT))


def _case_from_payload(payload: Any) -> PrevizCase:
    if not isinstance(payload, dict):
        raise ValueError("Each previz case must be an object")
    target_path = REPO_ROOT / str(payload["target_path"])
    target_markdown_path = REPO_ROOT / str(payload["target_markdown_path"])
    target = VideoAnalysisTarget.model_validate(json.loads(target_path.read_text()))
    if target.clip_id != payload["clip_id"]:
        raise ValueError(f"Target clip_id mismatch for {payload['clip_id']}")
    if not target_markdown_path.exists():
        raise ValueError(f"Missing previz target markdown: {target_markdown_path}")
    brief = payload.get("generation_brief")
    if not isinstance(brief, dict):
        raise ValueError(f"Missing generation_brief for {payload['clip_id']}")
    return PrevizCase(
        evaluation_id=str(payload["evaluation_id"]),
        clip_id=str(payload["clip_id"]),
        title=str(payload["title"]),
        source_fixture_dir=REPO_ROOT / str(payload["source_fixture_dir"]),
        target_path=target_path,
        target_markdown_path=target_markdown_path,
        character_labels=tuple(str(item) for item in payload["character_labels"]),
        generation_brief=dict(brief),
    )


def _require_unique(values: list[str], *, field_name: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"Previz case catalog contains duplicate {field_name} values")

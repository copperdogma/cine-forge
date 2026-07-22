#!/usr/bin/env python3
"""Refresh local controls and provenance for the maintained previz-usefulness dataset."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from previz_usefulness_candidates import generate_candidate, preserve_candidate  # noqa: E402
from previz_usefulness_contracts import (  # noqa: E402
    BASELINE_VARIANTS,
    CASE_CATALOG_PATH,
    DATASET_ROOT,
    DEFAULT_CANDIDATE_PACKS,
    CandidateSpec,
    PrevizCase,
    asset_hashes,
    candidate_specs,
    load_case_catalog,
    relative_to_repo,
    sha256_file,
)
from previz_usefulness_media import build_control_candidate  # noqa: E402

from cine_forge.env import load_cine_forge_dotenv  # noqa: E402


def main() -> None:
    args = _parse_args()
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise SystemExit("ffmpeg is required to refresh the previz usefulness dataset")
    if args.generate_ai:
        load_cine_forge_dotenv(REPO_ROOT)

    dataset_root = args.output_dir.resolve()
    dataset_root.mkdir(parents=True, exist_ok=True)
    catalog, cases = load_case_catalog()
    specs = candidate_specs(
        pack_ids=tuple(args.candidate_packs) if args.candidate_packs else DEFAULT_CANDIDATE_PACKS,
        include_ai=not args.controls_only,
    )
    if dataset_root != DATASET_ROOT and specs and not args.generate_ai:
        raise SystemExit(
            "A non-canonical output directory has no retained AI candidates. "
            "Use --controls-only or explicitly opt into --generate-ai."
        )

    manifest_cases = [
        _refresh_case(
            ffmpeg=ffmpeg,
            ffprobe=shutil.which("ffprobe"),
            dataset_root=dataset_root,
            case=case,
            specs=specs,
            generate_ai=args.generate_ai,
        )
        for case in cases
    ]
    manifest = {
        "schema_version": "previz-usefulness-manifest-v2",
        "generator": relative_to_repo(Path(__file__)),
        "case_contract_path": relative_to_repo(CASE_CATALOG_PATH),
        "case_contract_sha256": sha256_file(CASE_CATALOG_PATH),
        "subject_modality": catalog["subject_modality"],
        "decision_candidate_variants": [spec.variant for spec in specs],
        "control_variants": catalog["control_variants"],
        "cases": manifest_cases,
    }
    (dataset_root / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    _write_readme(dataset_root=dataset_root, specs=specs)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--candidate-pack",
        action="append",
        dest="candidate_packs",
        default=[],
        help="Engine-pack id to validate or explicitly regenerate. Can be repeated.",
    )
    parser.add_argument(
        "--generate-ai",
        action="store_true",
        help="Explicitly opt into paid provider generation. Omitted by default.",
    )
    parser.add_argument(
        "--controls-only",
        action="store_true",
        help="Build only deterministic non-decision controls (safe for temporary directories).",
    )
    parser.add_argument("--output-dir", type=Path, default=DATASET_ROOT)
    return parser.parse_args()


def _refresh_case(
    *,
    ffmpeg: str,
    ffprobe: str | None,
    dataset_root: Path,
    case: PrevizCase,
    specs: list[CandidateSpec],
    generate_ai: bool,
) -> dict[str, Any]:
    variants: list[dict[str, Any]] = []
    for variant in BASELINE_VARIANTS:
        meta = build_control_candidate(
            ffmpeg=ffmpeg,
            dataset_root=dataset_root,
            case=case,
            annotated=variant == "annotated_symbolic",
        )
        variants.append(_variant_manifest(dataset_root, case, variant, meta))
    for spec in specs:
        operation = generate_candidate if generate_ai else preserve_candidate
        meta = operation(
            ffmpeg=ffmpeg,
            ffprobe=ffprobe,
            dataset_root=dataset_root,
            case=case,
            candidate=spec,
        )
        variants.append(_variant_manifest(dataset_root, case, spec.variant, meta))
    return {
        "evaluation_id": case.evaluation_id,
        "clip_id": case.clip_id,
        "title": case.title,
        "target_path": relative_to_repo(case.target_path),
        "target_sha256": sha256_file(case.target_path),
        "target_markdown_path": relative_to_repo(case.target_markdown_path),
        "target_markdown_sha256": sha256_file(case.target_markdown_path),
        "variants": variants,
    }


def _variant_manifest(
    dataset_root: Path,
    case: PrevizCase,
    variant: str,
    meta: dict[str, Any],
) -> dict[str, Any]:
    directory = dataset_root / variant / case.clip_id
    return {
        "variant": variant,
        "candidate_label": meta["candidate_label"],
        "decision_role": meta["decision_role"],
        "decision_eligible": meta["decision_eligible"],
        "artifact_status": meta["artifact_status"],
        "meta_path": str((directory / "meta.json").relative_to(dataset_root)),
        "meta_sha256": sha256_file(directory / "meta.json"),
        **asset_hashes(directory),
    }


def _write_readme(*, dataset_root: Path, specs: list[CandidateSpec]) -> None:
    labels = ", ".join(spec.label for spec in specs) or "none"
    (dataset_root / "README.md").write_text(
        "# Previz Usefulness Dataset\n\n"
        "Generated by `benchmarks/scripts/generate_previz_usefulness_dataset.py`. "
        "The default command performs no provider calls: it rebuilds deterministic controls, "
        "validates retained AI clips/prompts/frames, and refreshes exact provenance hashes.\n\n"
        "Only provider-generated AI candidates without evaluator-authored overlays are "
        "decision-eligible. Symbolic and annotated variants are control-only because they are "
        "deterministic and the annotated frames visibly embed answer-bearing labels and intent.\n\n"
        f"Maintained decision candidates: {labels}.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Materialize storyboard-generation runtime results into a promptfoo image dataset."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = (
    REPO_ROOT / "benchmarks" / "fixtures" / "storyboard_generation_quality_cases.json"
)
DEFAULT_DATASET_ROOT = REPO_ROOT / "benchmarks" / "storyboard_generation_quality"

from storyboard_generation_quality_support import StoryboardQualityManifest  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-result", type=Path, required=True)
    parser.add_argument("--fixture-manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_DATASET_ROOT)
    args = parser.parse_args()

    runtime_payload = json.loads(args.runtime_result.resolve().read_text(encoding="utf-8"))
    manifest = StoryboardQualityManifest.model_validate_json(
        args.fixture_manifest.resolve().read_text(encoding="utf-8")
    )
    cases = {case.case_id: case for case in manifest.cases}

    dataset_root = args.output_dir.resolve()
    if dataset_root.exists():
        shutil.rmtree(dataset_root)
    dataset_root.mkdir(parents=True, exist_ok=True)
    targets_root = dataset_root / "targets"
    targets_root.mkdir(parents=True, exist_ok=True)

    for case in manifest.cases:
        target_dir = targets_root / case.case_id
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "target.json").write_text(
            case.analysis_target.model_dump_json(indent=2) + "\n",
            encoding="utf-8",
        )
        (target_dir / "target.md").write_text(
            _render_target_markdown(case.analysis_target.model_dump(mode="json")),
            encoding="utf-8",
        )

    variants_by_case: dict[str, list[str]] = {}
    for run in runtime_payload.get("runs", []):
        if not run.get("success"):
            continue
        case_id = str(run["case_id"])
        case = cases.get(case_id)
        if case is None:
            continue
        project_dir = (REPO_ROOT / run["project_dir"]).resolve()
        sequence_dir = dataset_root / str(run["candidate_variant"]) / case_id
        frames_dir = sequence_dir / "frames"
        refs_dir = sequence_dir / "references"
        frames_dir.mkdir(parents=True, exist_ok=True)
        refs_dir.mkdir(parents=True, exist_ok=True)

        for index, frame in enumerate(run.get("frames", []), start=1):
            source = project_dir / str(frame["relative_path"])
            target = frames_dir / f"{index:02d}_{source.name}"
            shutil.copyfile(source, target)

        ref_meta: list[dict[str, Any]] = []
        for ref in run.get("reference_images", []):
            source = project_dir / str(ref["relative_path"])
            target = refs_dir / source.name
            shutil.copyfile(source, target)
            ref_meta.append(
                {
                    "label": ref["label"],
                    "entity_name": ref["entity_name"],
                    "relative_path": str(target.relative_to(sequence_dir)),
                }
            )

        meta = {
            "storyboard_id": case_id,
            "title": case.label,
            "scene_ids": list(case.scene_ids),
            "frame_count": len(run.get("frames", [])),
            "candidate_variant": run["candidate_variant"],
            "candidate_label": run["candidate_label"],
            "image_model": run["image_model"],
            "available_reference_image_count": run["available_reference_image_count"],
            "prompt_reference_frame_count": run["prompt_reference_frame_count"],
            "direct_reference_input_count": run["direct_reference_input_count"],
            "reference_transport_supported": run["reference_transport_supported"],
            "recurring_character_names": [
                item.name for item in case.analysis_target.recurring_characters
            ],
            "reference_images": ref_meta,
        }
        (sequence_dir / "meta.json").write_text(
            json.dumps(meta, indent=2) + "\n",
            encoding="utf-8",
        )
        variants_by_case.setdefault(case_id, []).append(str(run["candidate_variant"]))

    manifest_payload = {
        "cases": [
            {
                "storyboard_id": case.case_id,
                "title": case.label,
                "variants": sorted(variants_by_case.get(case.case_id, [])),
                "target_path": f"targets/{case.case_id}/target.json",
                "target_markdown": f"targets/{case.case_id}/target.md",
            }
            for case in manifest.cases
        ]
    }
    (dataset_root / "manifest.json").write_text(
        json.dumps(manifest_payload, indent=2) + "\n",
        encoding="utf-8",
    )


def _render_target_markdown(target: dict[str, Any]) -> str:
    lines = [
        f"# {target['title']}",
        "",
        f"- Summary: {target['summary_reference']}",
        f"- Scene ids: {', '.join(target['scene_ids'])}",
    ]
    if target.get("required_keywords"):
        lines.append(f"- Required keywords: {', '.join(target['required_keywords'])}")
    lines.append(
        "- Style consistency: one coherent storyboard medium; no sudden photoreal "
        "or live-action panel."
    )
    if target.get("recurring_characters"):
        lines.append("- Recurring characters:")
        for item in target["recurring_characters"]:
            descriptors = ", ".join(item.get("descriptor_keywords", [])) or "none"
            lines.append(f"  - {item['name']}: {descriptors}")
    if target.get("reference_expectations"):
        lines.append("- Reference expectations:")
        for item in target["reference_expectations"]:
            descriptors = ", ".join(item.get("descriptor_keywords", [])) or "none"
            lines.append(f"  - {item['label']}: {descriptors}")
    lines.append(
        "- Runtime reference minimums: "
        f"available>={target['expected_available_reference_min']}, "
        f"prompt>={target['expected_prompt_reference_min']}, "
        f"direct>={target['expected_direct_reference_min']}"
    )
    lines.append(
        f"- Avoid readable text: {'yes' if target['should_avoid_readable_text'] else 'no'}"
    )
    lines.append(
        "- Avoid non-insert prop-only collapse: "
        f"{'yes' if target['should_avoid_prop_only_non_insert'] else 'no'}"
    )
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    main()

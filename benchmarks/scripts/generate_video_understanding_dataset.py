#!/usr/bin/env python3
"""Regenerate the complete synthetic ordered-frame benchmark dataset."""

from __future__ import annotations

from pathlib import Path

from video_understanding_dataset_artifacts import generate_dataset

REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_ROOT = REPO_ROOT / "benchmarks" / "video_understanding"


def main() -> None:
    generate_dataset(DATASET_ROOT, repo_root=REPO_ROOT, include_video=True)


if __name__ == "__main__":
    main()

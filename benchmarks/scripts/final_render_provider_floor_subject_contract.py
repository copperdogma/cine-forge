"""Fingerprint the maintained subject-model request contract for final-render evals."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

PROVIDER_ID = "file://../providers/video_understanding_provider.py"
FINAL_RENDER_PROMPT_VERSION = "final-render-provider-floor-v2"
SUBJECT_CONFIG_KEYS = (
    "provider",
    "model",
    "temperature",
    "max_tokens",
    "max_frames",
    "frame_policy",
    "prompt_version",
    "clip_root",
    "candidate_variant",
    "pythonExecutable",
    "timeout",
)
IMPLEMENTATION_FILES = (
    "benchmarks/providers/video_understanding_provider.py",
    "benchmarks/providers/video_understanding_provider_support.py",
    "benchmarks/providers/video_understanding_transport.py",
    "benchmarks/scripts/final_render_provider_floor_subject_contract.py",
    "src/cine_forge/ai/llm.py",
)
REQUEST_SHAPE = {
    "contract_version": "ordered-jpeg-json-subject-request-v1",
    "message_role": "user",
    "frame_mime_type": "image/jpeg",
    "frame_order_markers": True,
    "response_format": "json_object",
    "audio_submitted": False,
}


def subject_contract_fingerprint(
    config: dict[str, Any], *, repo_root: Path
) -> str | None:
    """Hash all settings and implementation bytes that materially shape the call."""
    normalized = normalized_subject_contract(config, repo_root=repo_root)
    if normalized is None:
        return None
    encoded = json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def normalized_subject_contract(
    config: dict[str, Any], *, repo_root: Path
) -> dict[str, Any] | None:
    if not isinstance(config, dict) or any(key not in config for key in SUBJECT_CONFIG_KEYS):
        return None
    selected = {key: config[key] for key in SUBJECT_CONFIG_KEYS}
    if not _valid_selected_config(selected):
        return None
    files: dict[str, str] = {}
    try:
        for relative in IMPLEMENTATION_FILES:
            files[relative] = hashlib.sha256((repo_root / relative).read_bytes()).hexdigest()
    except OSError:
        return None
    return {
        "provider_id": PROVIDER_ID,
        "provider_config": selected,
        "request_shape": REQUEST_SHAPE,
        "implementation_sha256": files,
    }


def runtime_subject_config_is_exact(config: object) -> bool:
    """Allow only the maintained YAML keys plus promptfoo's injected base path."""
    if not isinstance(config, dict):
        return False
    keys = set(config)
    maintained = set(SUBJECT_CONFIG_KEYS)
    if keys not in (maintained, maintained | {"basePath"}):
        return False
    return "basePath" not in config or isinstance(config["basePath"], (str, Path))


def _valid_selected_config(config: dict[str, Any]) -> bool:
    string_keys = (
        "provider",
        "model",
        "frame_policy",
        "prompt_version",
        "clip_root",
        "candidate_variant",
        "pythonExecutable",
    )
    if not all(isinstance(config[key], str) and config[key] for key in string_keys):
        return False
    integer_keys = ("max_tokens", "max_frames", "timeout")
    if not all(
        not isinstance(config[key], bool)
        and isinstance(config[key], int)
        and config[key] > 0
        for key in integer_keys
    ):
        return False
    temperature = config["temperature"]
    return (
        not isinstance(temperature, bool)
        and isinstance(temperature, (int, float))
        and float(temperature) == 0.0
    )

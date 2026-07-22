"""Current task, prompt, provider, target, and rendered-rubric contract loader."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from final_render_provider_floor_subject_contract import (
    FINAL_RENDER_PROMPT_VERSION,
    PROVIDER_ID,
    SUBJECT_CONFIG_KEYS,
    subject_contract_fingerprint,
)

PROMPT_VERSION = FINAL_RENDER_PROMPT_VERSION
MAINTAINED_SHAPE = (3, 2)
TASK_KEYS = {"description", "defaultTest", "prompts", "providers", "tests"}
TEST_VAR_KEYS = {
    "clip_id",
    "evaluation_id",
    "target_path",
    "target_markdown",
}


def load_task_contract(task_path: Path) -> dict[str, Any] | None:
    try:
        payload = yaml.safe_load(task_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return None
    if not isinstance(payload, dict) or set(payload) != TASK_KEYS:
        return None
    providers = payload.get("providers")
    tests = payload.get("tests")
    prompts = payload.get("prompts")
    valid_lists = all(isinstance(value, list) for value in (providers, tests, prompts))
    if not valid_lists or len(prompts) != 1 or (len(providers), len(tests)) != MAINTAINED_SHAPE:
        return None
    prompt_ref = prompts[0]
    if not isinstance(prompt_ref, str) or not prompt_ref.startswith("file://"):
        return None
    benchmark_root = task_path.parent.parent
    prompt_path = _referenced_file(
        task_path.parent,
        prompt_ref.removeprefix("file://"),
        confinement_root=benchmark_root,
    )
    if prompt_path is None:
        return None
    prompt_text = prompt_path.read_text(encoding="utf-8")
    default_test = payload.get("defaultTest")
    default_options = default_test.get("options") if isinstance(default_test, dict) else None
    grader = default_options.get("provider") if isinstance(default_options, dict) else None
    if (
        not isinstance(grader, str)
        or not grader
        or default_test != {"options": {"provider": grader}}
    ):
        return None

    variants = _load_variants(providers, repo_root=task_path.parents[2])
    cases = _load_cases(tests, task_path=task_path, benchmark_root=benchmark_root)
    if variants is None or cases is None:
        return None
    pairs = {(variant, case_id) for variant in variants for case_id in cases}
    return {
        "variants": variants,
        "cases": cases,
        "pairs": pairs,
        "grader": grader,
        "prompt_text": prompt_text,
    }


def _load_variants(
    providers: list[object], *, repo_root: Path
) -> dict[str, dict[str, Any]] | None:
    variants: dict[str, dict[str, Any]] = {}
    shared_analysis_config: dict[str, Any] | None = None
    for provider in providers:
        config = provider.get("config") if isinstance(provider, dict) else None
        variant = config.get("candidate_variant") if isinstance(config, dict) else None
        label = provider.get("label") if isinstance(provider, dict) else None
        provider_id = provider.get("id") if isinstance(provider, dict) else None
        prompt_version = config.get("prompt_version") if isinstance(config, dict) else None
        values = (
            provider_id,
            config.get("frame_policy") if isinstance(config, dict) else None,
            config.get("model") if isinstance(config, dict) else None,
            config.get("provider") if isinstance(config, dict) else None,
        )
        fingerprint = (
            subject_contract_fingerprint(config, repo_root=repo_root)
            if isinstance(config, dict)
            else None
        )
        if (
            not isinstance(provider, dict)
            or set(provider) != {"id", "label", "config"}
            or not isinstance(config, dict)
            or set(config) != set(SUBJECT_CONFIG_KEYS)
            or provider_id != PROVIDER_ID
            or variant in variants
            or prompt_version != PROMPT_VERSION
            or fingerprint is None
            or not all(isinstance(value, str) and value for value in (variant, label))
            or not all(isinstance(value, str) and value for value in values)
        ):
            return None
        max_frames = config.get("max_frames")
        max_tokens = config.get("max_tokens")
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 1
            for value in (max_frames, max_tokens)
        ):
            return None
        analysis_config = {
            key: config[key] for key in SUBJECT_CONFIG_KEYS if key != "candidate_variant"
        }
        if shared_analysis_config is None:
            shared_analysis_config = analysis_config
        elif analysis_config != shared_analysis_config:
            return None
        variants[variant] = {
            "label": label,
            "provider_id": provider_id,
            "prompt_version": prompt_version,
            "frame_policy": values[1],
            "model": values[2],
            "provider": values[3],
            "max_frames": max_frames,
            "max_tokens": max_tokens,
            "subject_contract_sha256": fingerprint,
        }
    return variants


def _load_cases(
    tests: list[object], *, task_path: Path, benchmark_root: Path
) -> dict[str, dict[str, Any]] | None:
    cases: dict[str, dict[str, Any]] = {}
    evaluation_ids: set[str] = set()
    for test in tests:
        vars_data = test.get("vars") if isinstance(test, dict) else None
        assertions = test.get("assert") if isinstance(test, dict) else None
        if (
            not isinstance(test, dict)
            or set(test) != {"vars", "assert"}
            or not isinstance(vars_data, dict)
            or set(vars_data) != TEST_VAR_KEYS
            or not _exact_assertions(assertions)
        ):
            return None
        clip_id = vars_data.get("clip_id")
        evaluation_id = vars_data.get("evaluation_id")
        target_path = vars_data.get("target_path")
        markdown_ref = vars_data.get("target_markdown")
        if (
            clip_id in cases
            or evaluation_id in evaluation_ids
            or not all(
                isinstance(value, str) and value
                for value in (clip_id, evaluation_id, target_path, markdown_ref)
            )
            or not markdown_ref.startswith("file://")
        ):
            return None
        target_json_path = _referenced_file(
            benchmark_root,
            target_path,
            confinement_root=benchmark_root,
        )
        markdown_path = _referenced_file(
            task_path.parent,
            markdown_ref.removeprefix("file://"),
            confinement_root=benchmark_root,
        )
        if target_json_path is None or markdown_path is None:
            return None
        expected_target_root = benchmark_root / "final_render_provider_floor" / "targets"
        if (
            target_json_path != expected_target_root / str(clip_id) / "target.json"
            or markdown_path != expected_target_root / str(clip_id) / "target.md"
        ):
            return None
        markdown_text = markdown_path.read_text(encoding="utf-8")
        rubric_template = assertions[1]["value"]
        if rubric_template.count("{{target_markdown}}") != 1:
            return None
        evaluation_ids.add(evaluation_id)
        cases[clip_id] = {
            "evaluation_id": evaluation_id,
            "target_path": target_path,
            "target_json_path": target_json_path,
            "target_markdown_path": markdown_path,
            "rendered_rubric": rubric_template.replace("{{target_markdown}}", markdown_text),
            "vars": vars_data,
            "assertions": assertions,
        }
    return cases


def _exact_assertions(value: object) -> bool:
    return (
        isinstance(value, list)
        and len(value) == 2
        and all(isinstance(row, dict) for row in value)
        and all(set(row) == {"type", "value"} for row in value)
        and [row.get("type") for row in value] == ["python", "llm-rubric"]
        and all(isinstance(row.get("value"), str) and row["value"] for row in value)
    )


def _referenced_file(
    base: Path,
    relative: object,
    *,
    confinement_root: Path,
) -> Path | None:
    """Resolve one canonical relative file reference inside its declared root."""
    if not isinstance(relative, str) or not relative or "\\" in relative:
        return None
    relative_path = Path(relative)
    parts = relative_path.parts
    parent_prefix = next(
        (index for index, part in enumerate(parts) if part != ".."), len(parts)
    )
    if (
        relative_path.is_absolute()
        or relative_path.as_posix() != relative
        or ".." in parts[parent_prefix:]
    ):
        return None
    root = confinement_root.resolve()
    path = (base.resolve() / relative_path).resolve()
    try:
        path.relative_to(root)
    except ValueError:
        return None
    return path if path.is_file() else None

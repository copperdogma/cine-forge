"""Saved Promptfoo config and prompt provenance checks for registry updates."""

from __future__ import annotations

import re
from pathlib import Path

from cine_forge.ai.errors import LLMCallError
from cine_forge.ai.model_identity import validate_provider_response_identity
from cine_forge.evals.task_matrix import (
    _configured_case_identities,
    _load_task,
    _normalize_test,
    _normalize_tests,
    _observed_case_identity,
    _observed_model_cases,
    _provider_identity,
    _require_exact_coverage,
    _validate_json_value,
    _vars_identity,
)

_SECRET_CONFIG_KEY = re.compile(
    r"(?:api.?key|authorization|password|secret|access.?token)",
    re.IGNORECASE,
)
_TEMPLATE_VARIABLE = re.compile(r"{{\s*([A-Za-z_][A-Za-z0-9_]*)\s*}}")


def validate_result_task_contract(
    task_path: Path,
    result_config: object,
    result_rows: list[object],
    result_prompts: object,
    *,
    repo_root: Path,
) -> None:
    """Bind a registry update to the current task and exact evaluated contract."""
    canonical_task, task = _load_task(task_path, repo_root=repo_root)
    expected = _configured_case_identities(task)
    observed, selected_providers = _observed_model_cases(result_rows)
    for model_name, identities in observed.items():
        _require_exact_coverage(model_name, expected, identities)
    prompts = _load_prompt_templates(task, canonical_task, repo_root=repo_root)
    _validate_saved_config(
        task,
        result_config,
        selected_providers=selected_providers,
        prompts=prompts,
    )
    prompt_columns = _validate_result_prompt_columns(
        result_prompts,
        selected_providers=selected_providers,
        prompts=prompts,
    )
    _validate_rows_against_task(
        task,
        canonical_task,
        result_rows,
        prompt_columns=prompt_columns,
        repo_root=repo_root,
    )


def _validate_saved_config(
    task: dict,
    result_config: object,
    *,
    selected_providers: set[tuple[str, str]],
    prompts: tuple[tuple[str | None, str], ...],
) -> None:
    if not isinstance(result_config, dict):
        raise ValueError("result config must be a mapping")
    current_default = _normalize_test(task.get("defaultTest", {}), "task defaultTest")
    saved_default = _normalize_test(
        result_config.get("defaultTest", {}),
        "result config.defaultTest",
    )
    if saved_default != current_default:
        raise ValueError("result config.defaultTest does not match current task")
    current_tests = _normalize_tests(task.get("tests"), "task tests")
    saved_tests = _normalize_tests(result_config.get("tests"), "result config.tests")
    if saved_tests != current_tests:
        raise ValueError("result config.tests do not match current task")
    _validate_saved_providers(
        task.get("providers"),
        result_config.get("providers"),
        selected_providers=selected_providers,
    )
    _validate_saved_prompt_specs(result_config.get("prompts"), prompts)


def _validate_saved_providers(
    current_value: object,
    saved_value: object,
    *,
    selected_providers: set[tuple[str, str]],
) -> None:
    current = _normalize_providers(current_value, "task providers")
    saved = _normalize_providers(saved_value, "result config.providers")
    current_by_id = {_provider_identity(item, "task provider"): item for item in current}
    saved_by_id = {
        _provider_identity(item, "result config provider"): item for item in saved
    }
    if not selected_providers.issubset(current_by_id) or not selected_providers.issubset(
        saved_by_id
    ):
        raise ValueError("result rows contain a provider outside the current task")
    if (
        set(saved_by_id) in (set(current_by_id), selected_providers)
        and all(saved_by_id[key] == current_by_id.get(key) for key in saved_by_id)
    ):
        return
    raise ValueError("result config.providers do not match current task selection")


def _normalize_providers(value: object, location: str) -> list[dict]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{location} must be a non-empty list")
    normalized: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(value):
        if not isinstance(item, dict) or set(item) != {"id", "label", "config"}:
            raise ValueError(f"{location}[{index}] must contain exactly id, label, config")
        identity = _provider_identity(item, f"{location}[{index}]")
        if identity in seen:
            raise ValueError(f"{location} contains duplicate provider {identity!r}")
        seen.add(identity)
        config = item["config"]
        if not isinstance(config, dict):
            raise ValueError(f"{location}[{index}].config must be a mapping")
        _validate_json_value(config, f"{location}[{index}].config")
        normalized.append({**item, "config": _redact_secret_values(config)})
    return normalized


def _redact_secret_values(value: object, key: str = "") -> object:
    if _SECRET_CONFIG_KEY.search(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {
            child_key: _redact_secret_values(child, child_key)
            for child_key, child in value.items()
        }
    if isinstance(value, list):
        return [_redact_secret_values(child) for child in value]
    return value


def _validate_saved_prompt_specs(
    saved_value: object,
    prompts: tuple[tuple[str | None, str], ...],
) -> None:
    if not isinstance(saved_value, list) or len(saved_value) != len(prompts):
        raise ValueError("result config.prompts do not match current task")
    for saved, (filename, template) in zip(saved_value, prompts, strict=True):
        if not isinstance(saved, str):
            raise ValueError("result config.prompts do not match current task")
        if filename is None and saved.strip() == template:
            continue
        raw_path = saved.removeprefix("file://")
        if filename is None or Path(raw_path).name != filename:
            raise ValueError("result config.prompts do not match current task")
        if Path(raw_path).parent.name != "prompts":
            raise ValueError("result config.prompts do not match current task")


def _validate_result_prompt_columns(
    value: object,
    *,
    selected_providers: set[tuple[str, str]],
    prompts: tuple[tuple[str | None, str], ...],
) -> tuple[tuple[tuple[str, str], str, str], ...]:
    """Bind Promptfoo's provider-prompt table columns to the current task."""
    if not isinstance(value, list) or not value:
        raise ValueError("result prompts must be a non-empty list")

    provider_keys: dict[str, tuple[str, str]] = {}
    for identity in selected_providers:
        provider_id, label = identity
        key = label or provider_id
        if key in provider_keys:
            raise ValueError(f"selected providers share result prompt key {key!r}")
        provider_keys[key] = identity

    observed: set[tuple[tuple[str, str], int]] = set()
    columns: list[tuple[tuple[str, str], str, str]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise ValueError(f"result prompts[{index}] must be a mapping")
        provider_key = item.get("provider")
        if not isinstance(provider_key, str) or provider_key not in provider_keys:
            raise ValueError(
                f"result prompts[{index}].provider is outside the selected task providers"
            )
        label = item.get("label")
        raw = item.get("raw")
        matches = [
            prompt_index
            for prompt_index, (_, template) in enumerate(prompts)
            if raw == template
            and isinstance(label, str)
            and (label == template or label.endswith(f": {template}"))
        ]
        if len(matches) != 1:
            raise ValueError(
                f"result prompts[{index}] template bytes do not match exactly one current prompt"
            )
        identity = provider_keys[provider_key]
        prompt_index = matches[0]
        pair = (identity, prompt_index)
        if pair in observed:
            raise ValueError("result prompts contain a duplicate provider-prompt column")
        observed.add(pair)
        assert isinstance(label, str)
        columns.append((identity, prompts[prompt_index][1], label))
    return tuple(columns)


def _validate_rows_against_task(
    task: dict,
    task_path: Path,
    rows: list[object],
    *,
    prompt_columns: tuple[tuple[tuple[str, str], str, str], ...],
    repo_root: Path,
) -> None:
    default = _normalize_test(task.get("defaultTest", {}), "task defaultTest")
    tests = _normalize_tests(task.get("tests"), "task tests")
    providers = {
        _provider_identity(provider, "task provider"): provider
        for provider in _normalize_providers(task.get("providers"), "task providers")
    }
    tests_by_vars = {
        _vars_identity(test["vars"], "task test.vars"): test for test in tests
    }
    for index, row in enumerate(rows):
        assert isinstance(row, dict)
        identity = _observed_case_identity(row, index=index)
        expected_case = _effective_test(default, tests_by_vars[identity])
        saved_case = _normalize_test(row.get("testCase"), f"result row {index}.testCase")
        if saved_case != expected_case:
            raise ValueError(f"result row {index} testCase does not match current task")
        provider_key = _provider_identity(row["provider"], f"result row {index}")
        current_provider = providers.get(provider_key)
        if current_provider is None:
            raise ValueError(f"result row {index} provider is outside the current task")
        _validate_row_provider_identity(
            current_provider,
            row["response"],
            index=index,
        )
        _validate_row_prompt(
            row,
            index=index,
            expected_case=expected_case,
            prompt_columns=prompt_columns,
            task_path=task_path,
            repo_root=repo_root,
        )


def _validate_row_provider_identity(
    current_provider: dict,
    response: object,
    *,
    index: int,
) -> None:
    """Require provider-owned call/model/usage evidence for registry promotion."""
    if not isinstance(response, dict):
        raise ValueError(f"result row {index}.response must be a mapping")
    provider_family, requested_model = _provider_request_contract(
        current_provider,
        index=index,
    )
    raw = response.get("raw")
    if not isinstance(raw, dict):
        raise ValueError(
            f"result row {index}.response.raw provider evidence is required"
        )
    if provider_family == "google":
        request_id = raw.get("responseId")
        returned_model = raw.get("modelVersion")
        usage = raw.get("usageMetadata")
        usage_name = "usageMetadata"
    else:
        request_id = raw.get("id")
        returned_model = raw.get("model")
        usage = raw.get("usage")
        usage_name = "usage"
    if not isinstance(usage, dict):
        raise ValueError(
            f"result row {index}.response.raw.{usage_name} must be a mapping"
        )
    try:
        identity = validate_provider_response_identity(
            provider=provider_family,
            requested_model=requested_model,
            returned_model=returned_model,
            request_id=request_id,
            require_returned=True,
        )
    except LLMCallError as exc:
        raise ValueError(f"result row {index} provider identity is invalid: {exc}") from exc

    metadata = response.get("metadata")
    if metadata is None:
        return
    if not isinstance(metadata, dict):
        raise ValueError(f"result row {index}.response.metadata must be a mapping")
    expected_metadata = {
        "provider": identity.provider,
        "requested_model": identity.requested_model,
        "returned_model": identity.returned_model,
        "request_id": identity.request_id,
    }
    for key, expected in expected_metadata.items():
        if key in metadata and metadata[key] != expected:
            raise ValueError(
                f"result row {index}.response.metadata.{key} contradicts "
                "provider-owned identity"
            )
    if "model" in metadata and metadata["model"] not in {
        identity.requested_model,
        identity.returned_model,
    }:
        raise ValueError(
            f"result row {index}.response.metadata.model contradicts "
            "provider-owned identity"
        )


def _provider_request_contract(
    current_provider: dict,
    *,
    index: int,
) -> tuple[str, str]:
    provider_id = current_provider["id"]
    config = current_provider["config"]
    if not provider_id.startswith("file://"):
        provider_family = provider_id.split(":", 1)[0]
        if provider_family not in {"openai", "anthropic", "google", "xai"}:
            raise ValueError(
                f"result row {index} has unsupported native provider {provider_family!r}"
            )
        requested_model = provider_id.rsplit(":", 1)[-1]
        return provider_family, requested_model

    model = config.get("model")
    if not isinstance(model, str) or not model.strip():
        raise ValueError(
            f"result row {index} custom provider current config.model is required"
        )
    configured_family = config.get("provider")
    if isinstance(configured_family, str) and configured_family.strip():
        provider_family = configured_family.strip()
    elif provider_id.endswith("/openai_responses_provider.py"):
        provider_family = "openai"
    elif provider_id.endswith("/anthropic_messages_provider.py"):
        provider_family = "anthropic"
    else:
        raise ValueError(
            f"result row {index} custom provider current config.provider is required"
        )
    if provider_family not in {"openai", "anthropic", "google", "xai"}:
        raise ValueError(
            f"result row {index} custom provider family {provider_family!r} is unsupported"
        )
    return provider_family, model.strip()


def _effective_test(default: dict, test: dict) -> dict:
    effective = {**default, **test}
    effective.update(
        {
            "vars": {**default["vars"], **test["vars"]},
            "assert": [*default["assert"], *test["assert"]],
            "options": {**default["options"], **test["options"]},
            "metadata": {**default["metadata"], **test["metadata"]},
        }
    )
    return effective


def _load_prompt_templates(
    task: dict,
    task_path: Path,
    *,
    repo_root: Path,
) -> tuple[tuple[str | None, str], ...]:
    specs = task.get("prompts")
    if not isinstance(specs, list) or not specs:
        raise ValueError("task prompts must be a non-empty list")
    templates: list[tuple[str | None, str]] = []
    for index, spec in enumerate(specs):
        if not isinstance(spec, str) or not spec.strip():
            raise ValueError(f"task prompts[{index}] must be a non-empty string")
        if not spec.startswith("file://"):
            templates.append((None, spec.strip()))
            continue
        prompt_path = _resolve_repo_file(
            task_path.parent / spec.removeprefix("file://"),
            repo_root=repo_root,
            location=f"task prompts[{index}]",
        )
        templates.append((prompt_path.name, prompt_path.read_text().strip()))
    return tuple(templates)


def _validate_row_prompt(
    row: dict,
    *,
    index: int,
    expected_case: dict,
    prompt_columns: tuple[tuple[tuple[str, str], str, str], ...],
    task_path: Path,
    repo_root: Path,
) -> None:
    prompt_index = row.get("promptIdx")
    if isinstance(prompt_index, bool) or not isinstance(prompt_index, int):
        raise ValueError(f"result row {index}.promptIdx must be an integer")
    # Promptfoo indexes provider-prompt result-table columns here, not the
    # task's prompt-template list. With one template and two providers, valid
    # rows therefore carry promptIdx 0 and 1.
    if prompt_index < 0 or prompt_index >= len(prompt_columns):
        raise ValueError(
            f"result row {index}.promptIdx is outside result prompt columns"
        )
    prompt = row.get("prompt")
    if not isinstance(prompt, dict):
        raise ValueError(f"result row {index}.prompt must be a mapping")
    column_provider, template, column_label = prompt_columns[prompt_index]
    row_provider = _provider_identity(row["provider"], f"result row {index}")
    if column_provider != row_provider:
        raise ValueError(
            f"result row {index}.promptIdx points to a different provider column"
        )
    label = prompt.get("label")
    if label != column_label:
        raise ValueError(f"result row {index} prompt label bytes do not match current task")
    expected_raw = _render_prompt(
        template,
        expected_case["vars"],
        task_path=task_path,
        repo_root=repo_root,
    )
    if prompt.get("raw") != expected_raw:
        raise ValueError(f"result row {index} rendered prompt does not match current task")
    if prompt.get("config") != expected_case["options"]:
        raise ValueError(f"result row {index} prompt grader config does not match current task")


def _render_prompt(
    template: str,
    variables: dict,
    *,
    task_path: Path,
    repo_root: Path,
) -> str:
    def replace(match: re.Match) -> str:
        name = match.group(1)
        if name not in variables:
            raise ValueError(f"current prompt references missing variable {name!r}")
        value = variables[name]
        if not isinstance(value, str):
            raise ValueError(f"current prompt variable {name!r} must be a string")
        if not value.startswith("file://"):
            return value
        source = _resolve_repo_file(
            task_path.parent / value.removeprefix("file://"),
            repo_root=repo_root,
            location=f"current prompt variable {name!r}",
        )
        return source.read_text().strip()

    return _TEMPLATE_VARIABLE.sub(replace, template)


def _resolve_repo_file(path: Path, *, repo_root: Path, location: str) -> Path:
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(repo_root.resolve())
    except (FileNotFoundError, ValueError) as exc:
        raise ValueError(f"{location} must resolve to a file inside the repository") from exc
    if not resolved.is_file():
        raise ValueError(f"{location} must resolve to a file inside the repository")
    return resolved

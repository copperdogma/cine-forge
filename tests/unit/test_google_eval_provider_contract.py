"""Repository-wide transport contracts for Gemini promptfoo lanes."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_ROOT = REPO_ROOT / "benchmarks" / "tasks"
SAMPLING_KEYS = {"temperature", "top_p", "top_k", "topP", "topK"}
THINKING_BUDGET_KEYS = {"thinking_budget", "thinkingBudget"}


def _google_providers() -> Iterator[tuple[Path, dict]]:
    for task_path in sorted(TASK_ROOT.glob("*.yaml")):
        task = yaml.safe_load(task_path.read_text(encoding="utf-8"))
        if not isinstance(task, dict):
            continue
        for provider in task.get("providers", []):
            if not isinstance(provider, dict):
                continue
            provider_id = provider.get("id")
            config = provider.get("config", {})
            if not isinstance(config, dict):
                continue
            if (
                isinstance(provider_id, str)
                and provider_id.startswith("google:")
            ) or config.get("provider") == "google":
                yield task_path, provider


def _nested_keys(value: object) -> Iterator[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _nested_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _nested_keys(child)


def _model_id(provider: dict) -> str:
    provider_id = provider.get("id", "")
    config = provider["config"]
    if isinstance(provider_id, str) and provider_id.startswith("google:"):
        return provider_id.removeprefix("google:")
    return str(config.get("model", ""))


@pytest.mark.unit
def test_google_generate_content_lanes_omit_sampling_and_thinking_budgets() -> None:
    """Deprecated controls must not make eval transport silently provider-dependent."""
    providers = list(_google_providers())
    assert providers, "expected maintained Google eval providers"

    errors: list[str] = []
    for task_path, provider in providers:
        keys = set(_nested_keys(provider["config"]))
        forbidden = sorted(keys & (SAMPLING_KEYS | THINKING_BUDGET_KEYS))
        if forbidden:
            errors.append(
                f"{task_path.relative_to(REPO_ROOT)}:{provider.get('label')} "
                f"contains {', '.join(forbidden)}"
            )

    assert not errors, "\n".join(errors)


@pytest.mark.unit
def test_gemini_3_lanes_reserve_full_visible_output_budget() -> None:
    """Hidden reasoning must not consume a small cap before strict JSON completes."""
    errors: list[str] = []
    found = 0
    for task_path, provider in _google_providers():
        model = _model_id(provider)
        if not model.startswith("gemini-3"):
            continue
        found += 1
        config = provider["config"]
        output_limit = config.get("maxOutputTokens", config.get("max_tokens"))
        if not isinstance(output_limit, int) or output_limit < 65_536:
            errors.append(
                f"{task_path.relative_to(REPO_ROOT)}:{model} has "
                f"output limit {output_limit!r}; expected at least 65536"
            )

    assert found, "expected maintained Gemini 3.x eval providers"
    assert not errors, "\n".join(errors)

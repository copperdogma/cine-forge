from __future__ import annotations

import importlib
import sys
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
TASK_PATH = REPO_ROOT / "benchmarks" / "tasks" / "final-render-provider-floor.yaml"
for root in (
    REPO_ROOT / "benchmarks" / "providers",
    REPO_ROOT / "benchmarks" / "scripts",
):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

provider = importlib.import_module("video_understanding_provider")
task_contract = importlib.import_module("final_render_provider_floor_task_contract")
runtime_contract = importlib.import_module("final_render_provider_floor_runtime_evidence")
subject_contract = importlib.import_module("final_render_provider_floor_subject_contract")


def _task() -> dict:
    return yaml.safe_load(TASK_PATH.read_text(encoding="utf-8"))


@pytest.mark.unit
def test_task_binds_each_subject_request_to_exact_config_and_implementation() -> None:
    task = _task()
    contract = task_contract.load_task_contract(TASK_PATH)

    assert contract is not None
    assert set(contract["variants"]) == {
        "openai_sora2",
        "google_veo31",
        "google_veo31_fast",
    }
    for row in task["providers"]:
        variant = row["config"]["candidate_variant"]
        expected = subject_contract.subject_contract_fingerprint(
            row["config"], repo_root=REPO_ROOT
        )
        assert expected is not None and len(expected) == 64
        assert contract["variants"][variant]["subject_contract_sha256"] == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    "mutation", ("extra_config", "missing_config", "wrong_id", "analysis_drift")
)
def test_task_rejects_unbound_subject_provider_changes(mutation: str) -> None:
    rows = deepcopy(_task()["providers"])
    if mutation == "extra_config":
        rows[0]["config"]["clip_dir"] = "unbound-candidate"
    elif mutation == "missing_config":
        rows[0]["config"].pop("max_tokens")
    elif mutation == "wrong_id":
        rows[0]["id"] = "file://../providers/other.py"
    else:
        rows[1]["config"]["model"] = "gpt-5.5-pro"

    assert task_contract._load_variants(rows, repo_root=REPO_ROOT) is None


@pytest.mark.unit
def test_provider_emits_current_subject_fingerprint_before_network_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _task()
    row = task["providers"][0]
    case = task["tests"][0]["vars"]
    seen: dict[str, object] = {}

    def fake_openai(**kwargs: object) -> dict[str, object]:
        seen.update(kwargs)
        return {
            "output": "{}",
            "token_usage": {"prompt": 100, "completion": 20, "total": 120},
            "raw": {
                "id": "analysis-openai-1",
                "model": "gpt-5.4",
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 20,
                    "total_tokens": 120,
                },
            },
        }

    monkeypatch.setattr(provider, "_call_openai", fake_openai)
    config = {**row["config"], "basePath": str(TASK_PATH.parent)}
    response = provider.call_api(
        "Return one strict JSON object.",
        {"config": config},
        {"vars": case},
    )

    expected = subject_contract.subject_contract_fingerprint(config, repo_root=REPO_ROOT)
    assert "error" not in response
    assert response["metadata"]["subject_contract_sha256"] == expected
    assert response["metadata"]["candidate_variant"] == "openai_sora2"
    assert response["metadata"]["clip_id"] == case["clip_id"]
    assert response["tokenUsage"] == {"prompt": 100, "completion": 20, "total": 120}
    assert response["raw"]["model"] == "gpt-5.4"
    assert response["raw"]["id"] == "analysis-openai-1"
    assert response["metadata"]["requested_model"] == "gpt-5.4"
    assert response["metadata"]["returned_model"] == "gpt-5.4"
    assert response["metadata"]["request_id"] == "analysis-openai-1"
    assert response["cost"] == provider.estimate_cost_usd("gpt-5.4", 100, 20)
    assert seen["max_tokens"] == row["config"]["max_tokens"]
    assert len(seen["frames"]) == row["config"]["max_frames"]


@pytest.mark.unit
def test_provider_rejects_unfingerprinted_config_before_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    task = _task()
    config = {
        **task["providers"][0]["config"],
        "basePath": str(TASK_PATH.parent),
        "clip_dir": "unbound-candidate",
    }
    dispatched = False

    def forbidden_dispatch(_: object) -> dict:
        nonlocal dispatched
        dispatched = True
        return {}

    monkeypatch.setattr(provider, "_dispatch_subject_request", forbidden_dispatch)
    response = provider.call_api(
        "Return JSON.", {"config": config}, {"vars": task["tests"][0]["vars"]}
    )

    assert "does not match its exact contract" in response["error"]
    assert dispatched is False


@pytest.mark.unit
def test_runtime_path_contract_rejects_empty_normalized_path() -> None:
    assert runtime_contract._canonical_relative(".", prefix="output") is False

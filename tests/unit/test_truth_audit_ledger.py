from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "check_truth_audit_ledger.py"
SPEC = importlib.util.spec_from_file_location("check_truth_audit_ledger", SCRIPT_PATH)
assert SPEC and SPEC.loader
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)


def _write_ledger(
    tmp_path: Path,
    surfaces: list[dict],
    *,
    expected: int,
    expectations: dict[str, int] | None = None,
) -> Path:
    path = tmp_path / "docs/evals/truth-audit-ledger.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(
            {
                "audit_policy": {
                    "initial_status": "pending",
                    "terminal_statuses": [
                        "clean",
                        "fixed",
                        "quarantined",
                        "documented limitation",
                    ],
                },
                "inventory_expectations": expectations or {"test_suite": expected},
                "surfaces": surfaces,
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return path


def _surface(**overrides: object) -> dict:
    value = {
        "id": "surface-a",
        "kind": "test_suite",
        "owner": "test owner",
        "paths": ["tests/evidence.txt"],
        "decision_impact": {"default_driving": False, "scope": "Fixture scope."},
        "audit_status": "clean",
        "evidence": ["tests/evidence.txt"],
        "notes": "Source-backed review completed.",
        "limitations": "Narrow synthetic fixture only.",
    }
    value.update(overrides)
    return value


def _validate(
    tmp_path: Path,
    surfaces: list[dict],
    *,
    expected: int | None = None,
    expectations: dict[str, int] | None = None,
    require_terminal: bool = False,
) -> list[str]:
    evidence = tmp_path / "tests/evidence.txt"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text("evidence", encoding="utf-8")
    ledger = _write_ledger(
        tmp_path,
        surfaces,
        expected=len(surfaces) if expected is None else expected,
        expectations=expectations,
    )
    return checker.validate_ledger(
        ledger,
        tmp_path,
        require_terminal=require_terminal,
    )


@pytest.mark.unit
def test_ledger_accepts_complete_terminal_inventory(tmp_path: Path) -> None:
    assert _validate(tmp_path, [_surface()], require_terminal=True) == []


@pytest.mark.unit
def test_ledger_rejects_duplicate_surface_ids(tmp_path: Path) -> None:
    errors = _validate(tmp_path, [_surface(), _surface()])
    assert "duplicate surface id: surface-a" in errors


@pytest.mark.unit
def test_ledger_rejects_inventory_count_drift(tmp_path: Path) -> None:
    errors = _validate(tmp_path, [_surface()], expected=2)
    assert "inventory kind test_suite: expected 2, found 1" in errors


@pytest.mark.unit
def test_ledger_rejects_unknown_status(tmp_path: Path) -> None:
    errors = _validate(tmp_path, [_surface(audit_status="looks-good")])
    assert any("unsupported audit_status" in error for error in errors)


@pytest.mark.unit
def test_terminal_surface_requires_resolving_evidence(tmp_path: Path) -> None:
    errors = _validate(
        tmp_path,
        [_surface(evidence=["tests/missing-evidence.txt"])],
    )
    assert any("evidence path does not resolve" in error for error in errors)


@pytest.mark.unit
def test_ledger_rejects_missing_owned_path(tmp_path: Path) -> None:
    errors = _validate(
        tmp_path,
        [_surface(paths=["tests/missing-owned-path.txt"])],
    )

    assert any("owned path does not resolve" in error for error in errors)


@pytest.mark.unit
def test_ledger_accepts_structured_unavailable_owned_path(tmp_path: Path) -> None:
    missing = "tests/deleted-historical-test.py"
    errors = _validate(
        tmp_path,
        [
            _surface(
                paths=[missing],
                unavailable_paths=[
                    {
                        "path": missing,
                        "reason": "Deleted after its assertion-backed replacement landed.",
                    }
                ],
            )
        ],
    )

    assert errors == []


@pytest.mark.unit
@pytest.mark.parametrize(
    "unavailable_paths, expected_error",
    [
        (
            [{"path": "tests/missing.py", "reason": ""}],
            "reason must be non-empty",
        ),
        (
            [{"path": "tests/not-owned.py", "reason": "Historical deletion."}],
            "unavailable path is not listed in paths",
        ),
    ],
)
def test_ledger_rejects_invalid_unavailable_path_declarations(
    tmp_path: Path,
    unavailable_paths: list[dict],
    expected_error: str,
) -> None:
    errors = _validate(
        tmp_path,
        [
            _surface(
                paths=["tests/missing.py"],
                unavailable_paths=unavailable_paths,
            )
        ],
    )

    assert any(expected_error in error for error in errors)


@pytest.mark.unit
def test_ledger_rejects_unavailable_path_that_resolves_again(tmp_path: Path) -> None:
    errors = _validate(
        tmp_path,
        [
            _surface(
                unavailable_paths=[
                    {
                        "path": "tests/evidence.txt",
                        "reason": "Incorrectly declared unavailable.",
                    }
                ]
            )
        ],
    )

    assert any("unavailable path now resolves" in error for error in errors)


@pytest.mark.unit
def test_require_terminal_fails_closed_on_pending_surface(tmp_path: Path) -> None:
    errors = _validate(
        tmp_path,
        [_surface(audit_status="pending")],
        require_terminal=True,
    )
    assert any("1 truth-audit surfaces remain pending" in error for error in errors)


@pytest.mark.unit
def test_ledger_rejects_missing_discovered_semantic_golden(tmp_path: Path) -> None:
    specs = tmp_path / "benchmarks/golden/golden_validation_specs.py"
    specs.parent.mkdir(parents=True)
    specs.write_text("GOLDEN_SPECS = {'demo-golden.json': {}}\n", encoding="utf-8")

    errors = _validate(tmp_path, [_surface()])

    assert any(
        "ledger missing canonical semantic_golden paths: demo-golden.json" in error
        for error in errors
    )


@pytest.mark.unit
def test_ledger_rejects_missing_discovered_promptfoo_task(tmp_path: Path) -> None:
    task = tmp_path / "benchmarks/tasks/demo.yaml"
    task.parent.mkdir(parents=True)
    task.write_text("description: demo\n", encoding="utf-8")

    errors = _validate(tmp_path, [_surface()])

    assert any(
        "ledger missing canonical promptfoo_task paths: benchmarks/tasks/demo.yaml" in error
        for error in errors
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    ("path", "kind", "expected_error"),
    [
        (
            "benchmarks/prompts/demo.txt",
            "prompt",
            "ledger missing canonical prompt paths: benchmarks/prompts/demo.txt",
        ),
        (
            "benchmarks/scorers/demo_scorer.py",
            "python_scorer",
            "ledger missing canonical python_scorer paths: "
            "benchmarks/scorers/demo_scorer.py",
        ),
        (
            "benchmarks/providers/demo_provider.py",
            "eval_transport",
            "ledger missing canonical eval_transport paths: "
            "benchmarks/providers/demo_provider.py",
        ),
        (
            "scripts/with_cine_forge_provider_env.py",
            "eval_transport",
            "ledger missing canonical eval_transport paths: "
            "scripts/with_cine_forge_provider_env.py",
        ),
    ],
)
def test_ledger_rejects_self_declared_omission_from_discovered_path_inventory(
    tmp_path: Path,
    path: str,
    kind: str,
    expected_error: str,
) -> None:
    discovered = tmp_path / path
    discovered.parent.mkdir(parents=True, exist_ok=True)
    discovered.write_text("maintained entrypoint\n", encoding="utf-8")

    errors = _validate(tmp_path, [_surface()])

    assert any(expected_error in error for error in errors), (kind, errors)


@pytest.mark.unit
def test_ledger_requires_one_row_owner_per_discovered_path(tmp_path: Path) -> None:
    prompt = tmp_path / "benchmarks/prompts/demo.txt"
    prompt.parent.mkdir(parents=True)
    prompt.write_text("prompt\n", encoding="utf-8")
    surfaces = [
        _surface(
            id="prompt-a",
            kind="prompt",
            paths=["benchmarks/prompts/demo.txt"],
        ),
        _surface(
            id="prompt-b",
            kind="prompt",
            paths=["benchmarks/prompts/demo.txt"],
        ),
    ]

    errors = _validate(tmp_path, surfaces, expectations={"prompt": 2})

    assert any(
        "ledger duplicates canonical prompt paths: benchmarks/prompts/demo.txt" in error
        for error in errors
    )


@pytest.mark.unit
def test_ledger_rejects_missing_discovered_registry_eval_id(tmp_path: Path) -> None:
    registry = tmp_path / "docs/evals/registry.yaml"
    registry.parent.mkdir(parents=True)
    registry.write_text("evals:\n  - id: demo-eval\n", encoding="utf-8")

    errors = _validate(tmp_path, [_surface()])

    assert any(
        "ledger missing canonical registry_eval ids: demo-eval" in error for error in errors
    )


@pytest.mark.unit
def test_canonical_ledger_has_complete_inventory_and_valid_terminal_evidence() -> None:
    errors = checker.validate_ledger(
        REPO_ROOT / "docs/evals/truth-audit-ledger.yaml",
        REPO_ROOT,
        require_terminal=False,
    )
    assert errors == []

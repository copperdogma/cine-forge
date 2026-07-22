from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.unit
def test_advertised_suite_targets_are_path_scoped() -> None:
    makefile = (REPO_ROOT / "Makefile").read_text()
    expected = {
        "test-unit": ("tests/unit", "unit"),
        "test-integration": ("tests/integration", "integration"),
        "test-smoke": ("tests/smoke", "smoke"),
        "test-acceptance": ("tests/acceptance", "acceptance"),
        "test-round-trip": ("tests/round_trip", "round_trip"),
    }

    for target, (path, marker) in expected.items():
        match = re.search(rf"^{re.escape(target)}:\n\t([^\n]+)$", makefile, re.MULTILINE)
        assert match, f"missing Makefile target {target}"
        command = match.group(1)
        assert path in command
        assert f"-m {marker}" in command


@pytest.mark.unit
def test_ui_suite_has_an_advertised_target() -> None:
    makefile = (REPO_ROOT / "Makefile").read_text()

    assert "test-ui:\n\tnode --test ui/tests/*.test.ts" in makefile


@pytest.mark.unit
def test_python_imports_resolve_to_the_current_checkout() -> None:
    import cine_forge

    package_root = Path(cine_forge.__file__).resolve().parent
    assert package_root.is_relative_to(REPO_ROOT / "src"), (
        f"cine_forge imported from {package_root}, not the current checkout; "
        "run with PYTHONPATH=src or use a Make test target"
    )


@pytest.mark.unit
def test_make_test_gate_rejects_an_inherited_foreign_pythonpath() -> None:
    hostile = "/tmp/cine-forge-foreign-checkout"
    result = subprocess.run(
        ["make", "-n", "test-unit"],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": hostile},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "PYTHONPATH=src " in result.stdout
    assert hostile not in result.stdout


@pytest.mark.unit
def test_direct_test_guide_preserves_worktree_import_safety() -> None:
    guide = (REPO_ROOT / "AGENTS.md").read_text()

    assert "**Unit tests**: `PYTHONPATH=src " in guide
    assert "**Worktree import safety**:" in guide

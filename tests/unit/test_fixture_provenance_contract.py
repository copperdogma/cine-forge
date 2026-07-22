"""Provenance and liveness contracts for non-golden test fixture classes."""

from __future__ import annotations

from pathlib import Path

import pytest

from cine_forge.driver.discovery import discover_modules
from cine_forge.driver.recipe import load_recipe, resolve_execution_order

pytestmark = pytest.mark.unit
REPO_ROOT = Path(__file__).resolve().parents[2]


def test_every_direct_ingest_fixture_is_registered_in_sources() -> None:
    fixture_root = REPO_ROOT / "tests" / "fixtures" / "ingest_inputs"
    sources = (fixture_root / "SOURCES.md").read_text(encoding="utf-8")
    fixture_names = sorted(
        path.name for path in fixture_root.iterdir() if path.is_file() and path.name != "SOURCES.md"
    )

    assert fixture_names
    assert all(f"`{name}`" in sources for name in fixture_names)


def test_lightweight_fixture_scope_and_source_limits_are_documented() -> None:
    readme = (REPO_ROOT / "tests" / "fixtures" / "README.md").read_text(encoding="utf-8")

    for name in ("sample_screenplay.fountain", "sample_prose.txt", "mariner-two-scenes.fountain"):
        assert f"`{name}`" in readme
    assert "decision-grade" in readme
    assert "licensing" in readme
    assert "not recorded" in readme


def test_all_recipe_fixtures_parse_and_reference_discovered_modules() -> None:
    recipe_root = REPO_ROOT / "tests" / "fixtures" / "recipes"
    module_registry = discover_modules(REPO_ROOT / "src" / "cine_forge" / "modules")

    for recipe_path in sorted(recipe_root.glob("*.yaml")):
        recipe = load_recipe(recipe_path)
        assert recipe.recipe_id == recipe_path.stem
        assert resolve_execution_order(recipe)
        assert all(stage.module in module_registry for stage in recipe.stages)


def test_removed_orphan_fixture_directories_stay_empty() -> None:
    for relative in ("normalize_responses", "scene_extract_inputs"):
        fixture_dir = REPO_ROOT / "tests" / "fixtures" / relative
        assert not fixture_dir.exists() or not any(fixture_dir.iterdir())


def test_liberty_church_snapshot_is_explicitly_quarantined() -> None:
    readme = (
        REPO_ROOT
        / "tests"
        / "fixtures"
        / "liberty_church_2"
        / "prod_snapshot_2026-02-19"
        / "README.md"
    ).read_text(encoding="utf-8")

    assert "historical forensic capture" in readme
    assert "not an active test fixture" in readme
    assert "semantic golden" in readme
    assert "quarantined" in readme
    assert "false character identities" in readme

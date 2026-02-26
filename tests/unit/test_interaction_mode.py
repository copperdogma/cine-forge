"""Tests for interaction mode system prompt variation (Story 089)."""

from __future__ import annotations

import pytest

from cine_forge.ai.chat import INTERACTION_MODE_PROMPTS, build_role_system_prompt
from cine_forge.roles.runtime import RoleCatalog


@pytest.fixture()
def catalog() -> RoleCatalog:
    cat = RoleCatalog()
    cat.load_definitions()
    return cat


MINIMAL_SUMMARY: dict = {
    "display_name": "Test Project",
    "input_files": ["test.fountain"],
    "has_inputs": True,
}

MINIMAL_STATE: dict = {
    "state": "fresh_import",
    "next_actions": [],
}


class TestInteractionModePrompts:
    """Verify that system prompt varies by interaction mode."""

    @pytest.mark.unit
    def test_guided_mode_injects_guided_section(self, catalog: RoleCatalog) -> None:
        summary = {**MINIMAL_SUMMARY, "interaction_mode": "guided"}
        prompt = build_role_system_prompt("assistant", summary, MINIMAL_STATE, catalog)
        assert "Guided Mode" in prompt
        assert "step-by-step" in prompt.lower()

    @pytest.mark.unit
    def test_expert_mode_injects_expert_section(self, catalog: RoleCatalog) -> None:
        summary = {**MINIMAL_SUMMARY, "interaction_mode": "expert"}
        prompt = build_role_system_prompt("assistant", summary, MINIMAL_STATE, catalog)
        assert "Expert Mode" in prompt
        assert "terse" in prompt.lower()

    @pytest.mark.unit
    def test_balanced_mode_has_no_extra_section(self, catalog: RoleCatalog) -> None:
        summary = {**MINIMAL_SUMMARY, "interaction_mode": "balanced"}
        prompt = build_role_system_prompt("assistant", summary, MINIMAL_STATE, catalog)
        assert "Guided Mode" not in prompt
        assert "Expert Mode" not in prompt

    @pytest.mark.unit
    def test_default_is_balanced_when_missing(self, catalog: RoleCatalog) -> None:
        # No interaction_mode key at all — should default to balanced (no extra section)
        prompt = build_role_system_prompt("assistant", MINIMAL_SUMMARY, MINIMAL_STATE, catalog)
        assert "Guided Mode" not in prompt
        assert "Expert Mode" not in prompt

    @pytest.mark.unit
    def test_mode_applies_to_non_assistant_roles(self, catalog: RoleCatalog) -> None:
        summary = {**MINIMAL_SUMMARY, "interaction_mode": "guided"}
        prompt = build_role_system_prompt("director", summary, MINIMAL_STATE, catalog)
        assert "Guided Mode" in prompt

    @pytest.mark.unit
    def test_mode_prompts_dict_has_expected_keys(self) -> None:
        assert "guided" in INTERACTION_MODE_PROMPTS
        assert "expert" in INTERACTION_MODE_PROMPTS
        # balanced has no entry (default behavior)
        assert "balanced" not in INTERACTION_MODE_PROMPTS

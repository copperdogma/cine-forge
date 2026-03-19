from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from cine_forge.ai.chat import _execute_propose_artifact_edit


@pytest.mark.unit
def test_propose_artifact_edit_blocks_read_only_render_prompt() -> None:
    service = MagicMock()

    result = _execute_propose_artifact_edit(
        {
            "artifact_type": "render_prompt",
            "entity_id": "scene_001",
            "changes": {"prompt_text": "Manual override"},
            "rationale": "Try to edit compiled prompt",
        },
        service=service,
        project_id="project-123",
    )

    payload = json.loads(result.content)
    assert "review-only" in payload["error"]
    assert result.actions == []
    service.list_artifact_groups.assert_not_called()

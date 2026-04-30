from __future__ import annotations

import pytest

from cine_forge.ai.provider_failures import classify_provider_failure_status


@pytest.mark.unit
def test_provider_failure_classifier_treats_missing_repo_api_key_as_auth_failed() -> None:
    assert (
        classify_provider_failure_status(
            message=(
                "CINE_FORGE_OPENAI_API_KEY (or legacy OPENAI_API_KEY) is not set"
            ),
            error_code=None,
        )
        == "auth_failed"
    )

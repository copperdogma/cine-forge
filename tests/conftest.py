"""Shared pytest config and fixtures."""

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line("markers", "unit: fast tests for isolated units")
    config.addinivalue_line("markers", "integration: tests spanning multiple components")
    config.addinivalue_line("markers", "smoke: lightweight end-to-end checks")

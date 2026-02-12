PYTHON ?= python3

.PHONY: test test-unit test-integration test-smoke lint format

test:
	$(PYTHON) -m pytest

test-unit:
	$(PYTHON) -m pytest -m unit

test-integration:
	$(PYTHON) -m pytest -m integration

test-smoke:
	$(PYTHON) -m pytest -m smoke

lint:
	$(PYTHON) -m ruff check .

format:
	$(PYTHON) -m ruff format .

PYTHON ?= python3
PYTHONPATH ?= src

.PHONY: test test-unit test-integration test-smoke lint format

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest

test-unit:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -m unit

test-integration:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -m integration

test-smoke:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -m smoke

lint:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m ruff check .

format:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m ruff format .

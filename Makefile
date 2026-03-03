PYTHON ?= python3
PYTHONPATH ?= src

.PHONY: test test-unit test-integration test-smoke smoke-test live-test lint format skills-sync skills-check check-size

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest

test-unit:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -m unit

test-integration:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -m integration

test-smoke:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest -m smoke

smoke-test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest tests/integration/test_mvp_recipe_smoke.py -k mocked

live-test:
	PYTHONPATH=$(PYTHONPATH) CINE_FORGE_LIVE_TESTS=1 $(PYTHON) -m pytest tests/integration/test_mvp_recipe_smoke.py -k live

lint:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m ruff check .

format:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m ruff format .

skills-sync:
	./scripts/sync-agent-skills.sh

skills-check:
	./scripts/sync-agent-skills.sh --check

check-size:
	@echo "Python source files over 400 lines:"
	@find src -name "*.py" -exec wc -l {} \; | sort -rn | awk '$$1 > 400 {print "  LARGE: " $$1 " lines — " $$2}'
	@echo ""
	@echo "TypeScript source files over 400 lines:"
	@find ui/src -name "*.ts" -o -name "*.tsx" | xargs wc -l 2>/dev/null | sort -rn | awk '$$1 > 400 && $$2 != "total" {print "  LARGE: " $$1 " lines — " $$2}'

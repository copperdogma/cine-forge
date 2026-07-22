PYTHON ?= python3
override PYTHONPATH := src

.PHONY: test test-unit test-integration test-smoke test-acceptance test-round-trip test-ui smoke-test live-test lint format skills-sync skills-check triage-facts triage-facts-check check-evals check-size

test:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest

test-unit:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest tests/unit -m unit

test-integration:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest tests/integration -m integration

test-smoke:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest tests/smoke -m smoke

test-acceptance:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest tests/acceptance -m acceptance

test-round-trip:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) -m pytest tests/round_trip -m round_trip

test-ui:
	node --test ui/tests/*.test.ts

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

triage-facts:
	$(PYTHON) scripts/triage_facts.py

triage-facts-check:
	$(PYTHON) -m pytest tests/unit/test_triage_facts.py

check-evals:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) scripts/check_eval_registry.py
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) scripts/check_truth_audit_ledger.py
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) scripts/build_eval_contract_manifest.py --check

check-size:
	@echo "Python source files over 400 lines:"
	@find src -name "*.py" -exec wc -l {} \; | sort -rn | awk '$$1 > 400 {print "  LARGE: " $$1 " lines — " $$2}'
	@echo ""
	@echo "TypeScript source files over 400 lines:"
	@find ui/src -name "*.ts" -o -name "*.tsx" | xargs wc -l 2>/dev/null | sort -rn | awk '$$1 > 400 && $$2 != "total" {print "  LARGE: " $$1 " lines — " $$2}'

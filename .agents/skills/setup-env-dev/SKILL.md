---
name: setup-env-dev
description: Set up development environment — project structure, eval infrastructure, and tooling
user-invocable: true
---

# /setup-env-dev

Set up the development environment with emphasis on eval infrastructure. The
ability to test "can AI do this?" is the foundation everything else builds on.

## What This Skill Produces

- Project structure (pyproject.toml, src layout, tests/)
- Virtual environment
- promptfoo configuration (ready to run evals)
- Basic eval scaffold (structural scorer + LLM rubric template)
- Makefile with test/lint/eval commands

## Steps

### 1. Project Structure

If the project doesn't already have a Python package structure, create:

```
src/{project_name}/
    __init__.py
    schemas/          # Pydantic models
tests/
    __init__.py
    fixtures/
        golden/       # Golden reference outputs
    conftest.py
pyproject.toml
Makefile
```

Adapt to the project's language/stack if not Python.

### 2. Core Dependencies

Ensure `pyproject.toml` (or equivalent) includes:

- **pydantic** — Schema definitions
- **instructor** — LLM structured extraction
- **pytest** — Testing
- **ruff** — Linting
- **pyyaml** — Configuration

Dev/eval dependencies:
- **promptfoo** (Node.js, installed globally: `npm install -g promptfoo`)

### 3. Virtual Environment

```bash
python -m venv .venv
.venv/bin/pip install -e ".[dev]"
```

### 4. promptfoo Scaffold

Create `evals/` directory with:

```
evals/
    promptfooconfig.yaml   # Main config
    prompts/               # Prompt templates
    providers/             # Provider configs
    scorers/               # Python scoring scripts
    datasets/              # Test case datasets (reference golden fixtures)
```

The `promptfooconfig.yaml` should be minimal but functional:
- At least one provider (the best available model)
- At least one test case (even a trivial one)
- Dual assertion pattern: Python scorer + LLM rubric
- Judge model: `claude-opus-4-6` (cross-provider judging)
- `max_tokens: 4096` minimum (avoid silent truncation)

### 5. Makefile

```makefile
PYTHON ?= .venv/bin/python

.PHONY: test-unit test lint eval

test-unit:
	$(PYTHON) -m pytest -m unit

test:
	$(PYTHON) -m pytest

lint:
	$(PYTHON) -m ruff check src/ tests/

eval:
	cd evals && promptfoo eval
```

### 6. Verify

- `make test` runs without errors (even if no tests yet)
- `make lint` runs without errors
- `make eval` runs the trivial promptfoo eval successfully

### 7. Update Checklist

Check off Phase 2b items in `docs/setup-checklist.md`.

## Guardrails

- The eval scaffold must be functional on day one. A broken eval setup blocks
  everything downstream.
- Don't over-engineer the project structure. Start minimal. The recursive
  decomposition from `/setup-spec` will reveal what's actually needed.
- promptfoo `max_tokens` must be set explicitly — silent truncation produces
  invalid JSON that wastes hours of debugging.
- Don't use `---` as a separator in promptfoo prompt files — it's interpreted
  as a prompt separator. Use `==========` instead.
- Update the setup checklist when done.

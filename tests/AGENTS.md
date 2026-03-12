# Tests AGENTS

This file scopes instructions for work under `tests/`.

- Prefer deterministic tests; mock networked AI calls by default.
- Keep unit tests isolated and fast.
- Mark tests explicitly with `@pytest.mark.unit`, `integration`, or `smoke`.
- Before changing tests for architectural, workflow, schema, or UX behavior, read the relevant ADRs in `docs/decisions/` and supporting decision docs in `docs/design/` so the tests preserve intended decisions, not accidental current behavior.
- Use live AI tests only behind an explicit environment gate.

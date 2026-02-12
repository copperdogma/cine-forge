# Tests AGENTS

This file scopes instructions for work under `tests/`.

- Prefer deterministic tests; mock networked AI calls by default.
- Keep unit tests isolated and fast.
- Mark tests explicitly with `@pytest.mark.unit`, `integration`, or `smoke`.
- Use live AI tests only behind an explicit environment gate.

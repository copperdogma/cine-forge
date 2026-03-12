# Modules AGENTS

This file scopes instructions for work under `src/cine_forge/modules/`.

- Keep modules stateless and deterministic outside AI calls.
- Every module must declare schema inputs/outputs in `module.yaml`.
- Never bypass schema validation on module outputs.
- Before changing module contracts, stage boundaries, or artifact behavior, read the relevant ADRs in `docs/decisions/` and supporting decision docs in `docs/design/`. If none apply, say so explicitly in the story, work log, or review.
- Prefer narrow module responsibilities and explicit artifact dependencies.
- Add or update module-level tests with every behavior change.

# Triage Orchestration Preservation Map

Use this map when upgrading `/triage` and its leaf lanes. The goal is to add
neutral lane-packet orchestration without losing CineForge's local rules.

## Preserve

- `/triage`
  - CineForge's Ideal has two levels: product Ideal and execution Ideal.
    Preserve both, and distinguish vision-level preferences from
    compromise-level preferences before treating UI, process, or tooling choices
    as durable.
  - The Ideal is the north star: product work should move CineForge toward
    being easy, fun, and engaging rather than merely administrable.
  - Priority comes from Ideal/spec/state/graph reasoning, not from story,
    inbox, eval, architecture, or health queue convenience. Existing artifacts
    are packaging context and candidate continuations after the gap is named.
  - Scoped invocations hand off completely to the matching leaf skill; the
    full-sweep orchestrator must not duplicate or drift from leaf logic.
  - Ideal/spec/state/graph first, plus UI-scout truth when product feel is in
    play.
  - `docs/methodology/state.yaml` is canonical planning state; generated views
    such as `docs/build-map.md` and `docs/stories.md` are evidence, not writable
    sources of truth.
  - Neutral leaf packets remain evidence for cross-domain ranking, not final
    repo-wide recommendations.
  - Completion sanity gate before maintenance-only or no-op answers.
  - A primary gap may remain the biggest Ideal gap while still being the wrong
    recommended action today. The why-now gate must cite last meaningful action,
    evidence date, proof artifact, and what materially changed before repeating
    the same line.
  - If all candidate lines or retry states are `blocked`, `hold`, `wait`,
    `waiting`, `wait-for-trigger`, or `trigger-exhausted`, say there is no
    honest unblocked next action instead of manufacturing maintenance work;
    recommend a truth refresh only when authored state lags later repo evidence.
  - When compiled actionability snippets conflict with authored blocker or
    unblock text, trust the authored story/state source first; treat derived
    actionability cleanup as tooling drift only if it is biasing `/triage`.
  - Eval ladder gate before creating implementation work for AI capability
    gaps.
  - Actionability gate: last meaningful action, date, proof artifact, and what
    materially changed.
  - Anti-fragmentation guidance: avoid tiny story fragments; prefer solid,
    coherent AI-sized stories that meaningfully advance the app. Continue,
    expand, reopen, or consolidate an existing line when subsystem, validation
    boundary, and success surface are materially the same.
  - Phase pressure: actionable `converge`, then `climb`, then `hold`, unless
    recency or blocker evidence says otherwise.
  - `Converge` means try to delete, collapse, or prove residue honestly; lack
    of a fresh external trigger is not enough for no-op when a bounded
    phase-aligned move still exists.
  - Do not recommend work that fights AGENTS-level constraints: relevant ADRs
    and design docs, immutable artifact boundaries, headless operation, the
    best-model baseline rule, live model discovery, no backwards-compatibility
    shims, representative UI evidence, or project-scoped preferences.
  - Preserve AGENTS routing and pushback: `prioritize X` inspects or updates
    `docs/methodology/state.yaml` first; `build/fix X` belongs in a story;
    `measure/benchmark/optimize X` belongs in eval registry plus story work;
    performance work attaches to the owning spec category and phase; push back
    when a proposed action conflicts with ADR/spec/local patterns.
  - One final recommendation with exact `Reply yes to proceed with: ...`
    handoff, after showing the visible top three.

- `/triage-stories`
  - Pending is not proof of buildability.
  - Read actual story files and verify substrate in code when relevant.
  - Keep same subsystem, validation boundary, and success surface in one story
    unless the repo evidence says the runtime seam changed.
  - Treat blocked stories as health flags unless the unblock condition is
    currently met.

- `/triage-inbox`
  - Scan mode is read-only.
  - Processing mode may create artifacts and remove processed inbox items only
    after user confirmation.
  - Link-heavy items get a quick read and recommendation before any full scout.

- `/triage-evals`
  - Read the eval registry and compiled actionability before recommending
    reruns.
  - Do not retry exhausted triggers without materially new evidence.
  - Verify current provider/model claims before treating them as why-now
    triggers.
  - The best-model baseline rule matters: cheap-model failure does not prove
    capability impossibility.

- `/triage-architecture`
  - Architecture audits are bounded by domain.
  - Prefer delete, merge, or re-home over new abstraction.
  - Architecture cadence is real pressure, not an automatic repo-wide winner.

- `/triage-health`
  - Health is read-only and fact-backed.
  - UI-scout freshness, codebase-improvement freshness, eval/model/golden
    freshness, methodology/tooling drift, architecture-audit due domains, and
    dependency/provider health are separate signals.
  - It may recommend follow-up commands, but does not run codebase scouts,
    architecture audits, provider-backed evals, golden builds, dependency
    changes, or implementation work during triage.

- Runbook and fact collection
  - `docs/runbooks/triage.md` is the full-sweep companion and keeps the
    top-three shortlist plus exact `Reply yes to proceed with: ...` handoff.
  - `scripts/triage_facts.py --json` runs directly in the main thread for
    wrappers, stories, evals, UI-scout, architecture-audit cadence,
    codebase-improvement freshness, lane presence, and recent churn.
  - The fact collector is not a delegated lane and not a substitute for leaf
    judgment.
  - `.gemini/commands/*.toml` wrappers are generated by
    `scripts/sync-agent-skills.sh`; refresh wrappers when changed skills alter
    generated descriptions or prompts.

- `/loop-verify`
  - No hard round cap.
  - Material fixes force a fresh full round.
  - Minor-only fixes get narrow verification and do not burn another full round.

## Target Behavior

Full `/triage` should:

1. Read the shared Ideal/spec/state/graph frame.
2. Launch neutral lane packet requests when delegation is allowed.
3. Run `python scripts/triage_facts.py --json` directly in the main thread.
4. Open 2-4 candidate gaps without picking the final winner early.
5. Collect stories, inbox, evals, architecture, and health packets.
6. Build a visible top-three shortlist.
7. Choose one final recommendation aligned to the repo Ideal and current
   actionability evidence.
8. End with `Reply yes to proceed with: ...`.

## Rollout Proof Surfaces

- `.agents/skills/triage/SKILL.md`
- `.agents/skills/triage-stories/SKILL.md`
- `.agents/skills/triage-inbox/SKILL.md`
- `.agents/skills/triage-evals/SKILL.md`
- `.agents/skills/triage-architecture/SKILL.md`
- `.agents/skills/triage-health/SKILL.md`
- `.agents/skills/loop-verify/SKILL.md`
- `.gemini/commands/*.toml`
- `docs/runbooks/triage.md`
- `docs/runbooks/triage-health.md`
- `scripts/triage_facts.py`
- `tests/unit/test_triage_facts.py`
- `scripts/methodology-graph.js`

Do not claim the rollout is done until wrappers are regenerated, the fact
collector works in text and JSON modes, methodology graph checks pass, and
loop-verify has completed a full clean round after any material fixes.

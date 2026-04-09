# Scout 018 — dossier-methodology-hardening-audit

**Sources:** `/Users/cam/Documents/Projects/dossier`, `/Users/cam/Documents/Projects/cine-forge`
**Scouted:** 2026-04-08
**Scope:** Audit CineForge's graph/state methodology migration against the hardening passes Dossier needed after its initial migration. Flag only misses analogous to that work, not repo-specific architectural evolution.
**Previous:** Scout 015 (Storybook & Dossier methodology delta, 2026-03-20) and Story 145 (CineForge methodology graph/state migration)
**Status:** Complete
**Alignment:** No local ADR directly governs these methodology-hardening details. The closest local anchors are `docs/methodology-ideal-spec-compromise.md`, `docs/methodology-artifact-audit-and-migration.md`, `docs/methodology/state.yaml`, `scripts/methodology-graph.js`, and Story 145.

## Findings

1. **The active-surface lint boundary is still materially narrower than CineForge's real live methodology package** — HIGH value
   What: `scripts/methodology-graph.js` hard-lints a fixed `ACTIVE_SURFACE_PATHS` list, but that list excludes multiple files the current repo still treats as live methodology/operator surfaces:
   - `docs/spec.md`
   - `docs/ideal.md`
   - `docs/prompts/ideal-app.md`
   - `docs/evals/README.md`
   - `docs/evals/attempt-template.md`
   - `docs/runbooks/promptfoo.md`
   - `docs/runbooks/golden-build.md`
   - `docs/methodology-artifact-audit-and-migration.md`
   - `.agents/skills/retrofit-ideal/SKILL.md`
   - `.agents/skills/setup-methodology/references/modes.md`
   Us: These are not archival docs. AGENTS, setup-methodology, create-eval, golden/eval workflows, retrofit-ideal, and setup-checklist all still point at them as current workflow or contract surfaces.
   Why this counts: This is the same class of migration miss Dossier only caught on later sweeps. It is not "CineForge chose a different architecture"; it is an under-scoped lint boundary around files the repo itself still treats as live.
   Recommendation: Expand `ACTIVE_SURFACE_PATHS` to match the actual live methodology package and add regressions for each added surface family.

2. **The audit artifact promises lint guarantees the compiler does not currently implement** — HIGH value
   What: `docs/methodology-artifact-audit-and-migration.md` says blocking/warning lints cover ownerless state keys and freshness drift, and it seeds `last_reviewed` fields throughout `docs/methodology/state.yaml`.
   Us: `scripts/methodology-graph.js` contains no ownerless-key lint, no `last_reviewed` parsing, and no freshness checks for category or compromise state. The current implementation only validates ID/link integrity plus a narrow stale-instruction scan. The same artifact also shows a now-invalid example state shape: it still demonstrates `stories_index.sections` with `id: "current-execution-map"`, but the compiler now rejects that form and requires `stories_index.current_execution_map` instead. It also misstates lint severity: the artifact lists legacy-header-only stories and missing `category_refs` as warnings, while the current compiler hard-fails both as errors.
   Why this counts: This is live contract drift inside the migration package itself. The doc says the migration hardened these checks; the compiler does not enforce them.
   Recommendation: Either implement the promised lints or narrow the audit artifact so it stops overstating the hard contract.

3. **Eval lineage is still heuristic rather than explicit** — HIGH value
   What: `parseEvalRegistry()` in `scripts/methodology-graph.js` infers eval links by scraping free text for `spec:N`, story IDs, and compromise IDs. `docs/evals/registry.yaml` entries do not currently carry explicit `story_refs`, `spec_refs`, `category_refs`, or `compromise_refs`.
   Us: `/create-eval` and `docs/runbooks/create-eval.md` still tell the operator to add "linkage notes" or "methodology anchors", not a concrete explicit-lineage field contract.
   Why this counts: This is the same migration hardening Dossier had to add later. CineForge has a graph, but eval lineage is still partly reconstructed from prose instead of being canonical in the registry.
   Recommendation: Move eval lineage to explicit registry keys, teach those fields in `/create-eval`, and make the compiler consume those fields directly instead of scraping prose.

4. **`docs/stories.md` authority hardening is still weaker than the `docs/build-map.md` hardening** — MEDIUM value
   What: The compiler blocks manual `docs/stories.md` edit instructions and authored `docs/build-map.md` authority phrasing, but it does not have the parallel generated-view warning for ambiguous `docs/stories.md` authority wording.
   Us: A live surface could describe `docs/stories.md` as an authority surface without explicitly saying it is generated and still pass validation, as long as it does not literally instruct hand edits.
   Why this counts: Dossier only caught this after later sweeps. This is not a repo-shape difference; it is a missing symmetry in the stale-instruction lint.
   Recommendation: Add a `docs/stories.md` generated-index authority lint parallel to the build-map authority lint.

5. **Story category-ownership hardening is still partial** — MEDIUM value
   What: The compiler requires non-empty `category_refs`, but it does not enforce that story `category_refs` include every category implied by the story's own `spec_refs` and `compromise_refs`.
   Us: `/create-story` also does not teach that stricter completeness rule; it tells the agent to fill `category_refs` but does not say they must include all parent `spec:N` categories implied by the linked refs.
   Why this counts: This is the same metadata-hardening class Dossier had to add later. It is a guardrail gap, not a broad architecture difference.
   Recommendation: Enforce implied-category completeness in the compiler and teach it in `/create-story`.
   Current-state note: I checked the current generated graph and did not find an existing story violating this rule today.

6. **Methodology regression coverage did not keep up with the hardening frontier** — MEDIUM value
   What: `tests/unit/test_methodology_graph.py` currently has five tests, all focused on blocked-story metadata, current execution-map rendering, health-flag behavior, and stale campaign/execution-map references.
   Us: There is no regression coverage for the missing items above: active-surface boundary breadth, audit-artifact contract drift, explicit eval lineage, `docs/stories.md` generated-view authority framing, or implied-category completeness.
   Why this counts: This matches Dossier's pattern: the early migration had core compiler tests, but the long-tail misses only stopped recurring once each one got a regression test.
   Recommendation: Add narrow regression tests for each hardening rule as it lands instead of relying on manual sweeps.

7. **An excluded live skill already contains exactly the kind of stale generated-view workflow Dossier had to remove later** — HIGH value
   What: `.agents/skills/retrofit-ideal/SKILL.md` still tells the operator to:
   - `Record baseline results in evals/baseline-results.md`
   - `Update stories.md with Ideal-alignment notes`
   Us: `evals/baseline-results.md` does not exist in CineForge, and `docs/stories.md` is now a generated view rather than a hand-maintained planning surface.
   Why this counts: This is not hypothetical boundary risk anymore. A real excluded live surface is already teaching the old model, exactly because the active-surface lint never looks at it.
   Recommendation: Rewrite `/retrofit-ideal` to target canonical metadata/state surfaces and bring it under the compiler's stale-instruction boundary.

8. **The live setup checklist still preserves retired eval-baseline instructions inside its historical archive** — MEDIUM value
   What: `docs/setup-checklist.md` still carries historical carry-forward tasks to create and populate `evals/baseline-results.md`, even though that file does not exist and the current eval workflow is centered on `docs/evals/registry.yaml`, `docs/evals/README.md`, and attempt records.
   Us: The section is marked historical, but `docs/setup-checklist.md` is still a live operator surface and the setup runbook explicitly tells agents to preserve historical notes there.
   Why this counts: This is the same "historical residue inside a live surface" class Dossier kept finding on later sweeps. It is easy for stale obligations to persist indefinitely unless the live checklist is periodically normalized.
   Recommendation: Rewrite those historical lines into generic legacy-baseline wording or remove them from the live checklist surface entirely.

9. **The repo-local audit artifact is still partly written as a pre-migration plan, not a post-migration record** — HIGH value
   What: `docs/methodology-artifact-audit-and-migration.md` still says, in present tense:
   - the repo currently relies on hand-authored planning surfaces
   - there is no compiled methodology graph or structured state substrate yet
   - there is no dedicated architecture-audit lane yet
   - the new methodology package should add that lane
   Us: Those statements are now false on the current tree. The file is included in the repo's live methodology package and is referenced as migration authority, so its tense matters.
   Why this counts: This is the same class of issue Dossier only caught after later sweeps: the migration record itself becomes a stale source of operator guidance unless it is rewritten into a post-migration contract.
   Recommendation: Rewrite the audit artifact as a completed migration record with an explicit historical-baseline section, current contract, and current certification status.

10. **Story 145's proof log now overstates how clean the migration ended up being** — MEDIUM value
   What: `docs/stories/story-145-methodology-graph-state-migration.md` still records closure evidence such as "all structural checks now pass" and that remaining warnings were only legacy metadata debt.
   Us: Later sweeps found additional real issues outside that original closeout: excluded live surfaces, stale retrofit/setup guidance, audit-artifact contract drift, and missing compiler lints. The story is the designated proof log for the migration, so its closeout evidence is no longer complete.
   Why this counts: This is not a complaint about historical work logs existing. It matters because the audit artifact explicitly tells readers to use Story 145 as the proof log, so stale closure claims can mislead future agents into believing the hardening sweep already covered more than it did.
   Recommendation: Add a follow-up evidence note to Story 145 summarizing the later hardening gaps found post-closeout, or explicitly narrow what that story certifies.

11. **Decision records are outside the stale-instruction guardrail, and at least one live ADR still teaches manual generated-index upkeep** — MEDIUM value
   What: `AGENTS.md` explicitly tells agents to read `docs/decisions/` and `docs/design/` before making architectural, workflow, schema, or UX decisions, but `scripts/methodology-graph.js` does not include those decision surfaces in `ACTIVE_SURFACE_PATHS`. A concrete stale hit already exists: `docs/decisions/adr-003-film-elements/adr.md` still includes the action item `Update docs/stories.md to reflect all cancellations, reshapes, and new stories`.
   Us: After the graph/state migration, `docs/stories.md` is a generated view, not a hand-maintained planning surface. This is the same class of stale generated-index instruction Dossier only caught on later sweeps, just sitting in CineForge's decision layer instead of a skill/runbook.
   Why this counts: This is not merely another example of Finding 1's methodology-package boundary list. CineForge's own agent contract says decision records are live inputs to future choices. If they remain outside the stale-instruction lint, old manual generated-view steps can persist in architecture guidance indefinitely.
   Recommendation: Either widen the stale-instruction lint to cover relevant decision docs or add a dedicated decision-record sweep for methodology drift, then normalize ADR-003 so it no longer tells readers to update a generated artifact manually.

12. **The live eval-attempt contract still splits `retry_status` vs `retry_state` across workflow surfaces** — MEDIUM value
   What: `docs/evals/README.md`, `docs/evals/registry.yaml`, `triage-evals`, and `docs/runbooks/triage-evals.md` all teach and consume `retry_status`, but `docs/evals/attempt-template.md` still uses the older `Retry state` / `retry_state` wording in both the template body and the Definition of Done checklist. One real attempt artifact (`docs/evals/attempts/002-video-understanding-google-max-output-budget.md`) also still uses the old heading.
   Us: This is a live contract drift inside the eval workflow package. The registry protocol and triage logic now speak one vocabulary, while the attempt template still teaches another. Because agents and humans use the attempt files as the narrative record for retries, the mismatch can keep reintroducing the stale field name even if the registry itself is correct.
   Why this counts: This is the same class of post-migration hardening miss Dossier kept finding: the compiler/workflow contract evolved, but a live template and its downstream artifacts were left behind. It is not a repo-shape difference or a newer architectural choice.
   Recommendation: Normalize the attempt template and existing attempt-story headings to `retry_status` terminology, or explicitly document the mapping so agents do not keep minting mixed vocabulary.

13. **The top-level README still presents `docs/stories.md` without generated-index framing, and it sits outside the guardrail** — LOW value
   What: `README.md` still lists `docs/stories.md: story index` in the repository layout, but it does not say that the file is generated from the graph/state compiler. `README.md` is also outside `ACTIVE_SURFACE_PATHS`, so this wording is not checked by the stale-instruction lint.
   Us: After the migration, `docs/stories.md` is no longer an authored planning input. Dossier only caught this class of issue late, when unqualified `docs/stories.md` mentions were still teaching the wrong mental model even without explicitly telling people to edit the file.
   Why this counts: This is not just a stylistic nit in a generic README. It is the repo's first orientation surface, and it currently describes a generated methodology artifact as if it were an ordinary maintained index. That is exactly the kind of low-grade contract drift that later re-seeds stronger workflow mistakes.
   Recommendation: Update the README entry to call `docs/stories.md` a generated story index/dashboard view, and either widen the guardrail to cover the README or add it to a periodic live-surface sweep.

14. **The top-level README still points agents at a non-existent `skills/` root instead of the canonical `.agents/skills` surface** — LOW value
   What: `README.md` still says the repo layout includes `skills/` and tells the reader to "Use skills under `skills/` for common tasks," but the actual canonical skills root is `.agents/skills`, as reinforced in `AGENTS.md`. There is no `skills/` directory at the repo root.
   Us: This is live operator-surface drift in the same category as the README story-index wording. It is not a newer architecture that supersedes Dossier's work; it is stale orientation text left behind after CineForge's cross-CLI skill unification moved the source of truth to `.agents/skills`.
   Why this counts: Dossier's later sweeps kept finding exactly this kind of first-touch orientation drift: the repo's canonical workflow surface moved, but a top-level document still taught the old location or ownership model. Because README is outside the guardrail, that stale path can persist and misdirect future agents.
   Recommendation: Update the README to point at `.agents/skills` (or explain the wrapper layout accurately), and consider bringing README into the same periodic live-surface audit as other operator docs.

15. **The archived retrofit-gap memo still points at generated planning views as if they carry current authoritative values** — LOW value
   What: `docs/retrofit-gaps.md` is explicitly archived, but its carry-forward guidance still tells readers to use `docs/build-map.md` for "current substrate status" and says "The authoritative values now live in `docs/spec.md` and `docs/build-map.md`." It also points to `docs/stories.md` for backlog ownership without generated-index framing.
   Us: Under the graph/state methodology, `docs/build-map.md` and `docs/stories.md` are generated views, not canonical planning inputs. This is the same late-sweep residue Dossier kept finding in archived-but-still-live docs: the file admits it is historical, but the surviving redirect language still teaches the wrong authority model.
   Why this counts: This is not a complaint that archived files exist. The problem is that a live repo doc now redirects readers toward generated outputs with authoritative phrasing. Because the file remains outside the stale-instruction guardrail, the wording can persist indefinitely.
   Recommendation: Rewrite the archive note so it points to `docs/methodology/state.yaml` / the graph-backed methodology stack explicitly, and describe `docs/build-map.md` / `docs/stories.md` as generated views rather than authority surfaces.

16. **A live operational runbook still points at the obsolete `skills/` root instead of `.agents/skills`** — LOW value
   What: `docs/runbooks/browser-automation-and-mcp.md` still lists the deployment skill as `skills/deploy/SKILL.md`, but CineForge's canonical skills root is `.agents/skills`, and the real file is `.agents/skills/deploy/SKILL.md`.
   Us: This is the same stale-skill-root class as the README drift, but it matters independently because this runbook is a live operator troubleshooting surface. A reader following the reference lands on a nonexistent path even though the correct skill exists in the repo.
   Why this counts: Dossier's later sweeps kept finding exactly this kind of first-touch tooling drift: a real workflow surface moved to the canonical skills root, but a supporting runbook still taught the pre-unification location. Because this runbook is outside the stale-instruction guardrail, the bad path can survive indefinitely.
   Recommendation: Update the runbook reference to `.agents/skills/deploy/SKILL.md` and include this runbook in the same periodic live-surface sweep as the README and methodology package docs.

## Non-Findings

- I did not find evidence that CineForge's current repo has already drifted into bad story category ownership; the current generated graph showed no story missing an implied parent category.
- Beyond `/retrofit-ideal`, the historical setup-checklist archive, `docs/decisions/adr-003-film-elements/adr.md`, the top-level `README.md`, the archived `docs/retrofit-gaps.md` memo, and the browser automation runbook's stale deploy-skill path, I did not find another sampled excluded live surface already teaching obviously stale `docs/stories.md` or `docs/build-map.md` authority wording. The remaining non-methodology drift I found is confined to stale skill-root references in first-touch operator docs.
- In the decision-record layer, I found one concrete stale generated-index instruction in `docs/decisions/adr-003-film-elements/adr.md`; I did not find a second comparable hit in the sampled `docs/design/` / `docs/decisions/` surfaces beyond that ADR.
- In the eval-attempt workflow, I found one concrete existing artifact still using the old `Retry state` wording (`docs/evals/attempts/002-video-understanding-google-max-output-budget.md`). I did not find evidence that registry or triage surfaces were still using the old field name.
- `node scripts/methodology-graph.js build`, `node scripts/methodology-graph.js check`, and `.venv/bin/python -m pytest tests/unit/test_methodology_graph.py -q` all pass on the current tree after refreshing generated outputs.
- I did not find another currently false present-tense migration summary as strong as the audit artifact's opening section. Story 145 is looser and more historical, but its proof log still needs qualification now that later audits found more issues.

## Verification

- Read `AGENTS.md`, `scripts/methodology-graph.js`, `tests/unit/test_methodology_graph.py`, `docs/methodology-artifact-audit-and-migration.md`, `docs/methodology/state.yaml`, `docs/evals/registry.yaml`, and Story 145
- Read `docs/decisions/adr-003-film-elements/adr.md` after confirming `AGENTS.md` still treats `docs/decisions/` / `docs/design/` as live decision inputs
- Compared the live eval retry vocabulary across `docs/evals/README.md`, `docs/evals/attempt-template.md`, `docs/evals/registry.yaml`, `.agents/skills/triage-evals/SKILL.md`, and `docs/runbooks/triage-evals.md`
- Re-read `README.md` as a live orientation surface and compared its `docs/stories.md` wording against the post-migration generated-view contract
- Compared `README.md`'s skill-path guidance against the actual repo layout and `AGENTS.md`'s canonical `.agents/skills` instruction
- Re-read `docs/retrofit-gaps.md` as an archived-but-live surface and checked whether its redirect language still described generated planning views as authoritative
- Checked non-historical `skills/...` path references outside `.agents/skills/` and confirmed the remaining live hit in `docs/runbooks/browser-automation-and-mcp.md`
- Read live workflow surfaces that currently reference the excluded files:
  - `docs/spec.md`
  - `.agents/skills/setup-methodology/SKILL.md`
  - `.agents/skills/setup-methodology/references/modes.md`
  - `.agents/skills/retrofit-ideal/SKILL.md`
  - `.agents/skills/create-eval/SKILL.md`
  - `.agents/skills/create-story/SKILL.md`
  - `.agents/skills/create-story/templates/story.md`
  - `docs/runbooks/promptfoo.md`
  - `docs/runbooks/golden-build.md`
  - `docs/runbooks/create-eval.md`
  - `docs/setup-checklist.md`
  - `docs/prompts/ideal-app.md`
  - `docs/evals/README.md`
  - `docs/evals/attempt-template.md`
- Ran `node scripts/methodology-graph.js check` before refresh; it reported stale generated outputs
- Ran `node scripts/methodology-graph.js build`
- Re-ran `node scripts/methodology-graph.js check`; result: clean
- Ran `.venv/bin/python -m pytest tests/unit/test_methodology_graph.py -q`; result: `5 passed`
- Ran repo-wide searches for stale generated-view/manual-surface phrasing and for `baseline-results.md`; result: real stale hits in `/retrofit-ideal` and the historical archive of `docs/setup-checklist.md`, and no current `evals/baseline-results.md` file in the repo
- Re-read the opening and certification/proof sections of the audit artifact and Story 145 against the current repo state; result: the audit artifact is still partly pre-migration in present tense, and Story 145 now needs qualification as an incomplete hardening proof log

## Evidence

- Compiler boundary:
  - `scripts/methodology-graph.js`
- Migration contract claims:
  - `docs/methodology-artifact-audit-and-migration.md`
  - `docs/stories/story-145-methodology-graph-state-migration.md`
- Live excluded surfaces:
  - `docs/spec.md`
  - `docs/ideal.md`
  - `docs/prompts/ideal-app.md`
  - `docs/evals/README.md`
  - `docs/evals/attempt-template.md`
  - `docs/runbooks/promptfoo.md`
  - `docs/runbooks/golden-build.md`
  - `docs/methodology-artifact-audit-and-migration.md`
  - `.agents/skills/retrofit-ideal/SKILL.md`
  - `.agents/skills/setup-methodology/references/modes.md`
- Explicit-lineage gap:
  - `docs/evals/registry.yaml`
  - `.agents/skills/create-eval/SKILL.md`
  - `docs/runbooks/create-eval.md`
- Eval retry-contract drift:
  - `docs/evals/README.md`
  - `docs/evals/attempt-template.md`
  - `docs/evals/attempts/002-video-understanding-google-max-output-budget.md`
  - `.agents/skills/triage-evals/SKILL.md`
  - `docs/runbooks/triage-evals.md`
- Concrete stale-surface evidence:
  - `.agents/skills/retrofit-ideal/SKILL.md`
  - `docs/setup-checklist.md`
  - `docs/decisions/adr-003-film-elements/adr.md`
  - `README.md`
  - `docs/retrofit-gaps.md`
  - `docs/runbooks/browser-automation-and-mcp.md`
- Post-migration record drift:
  - `docs/methodology-artifact-audit-and-migration.md`
  - `docs/stories/story-145-methodology-graph-state-migration.md`

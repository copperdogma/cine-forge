# Story 208 — UI test inventory ownership

## Triage decision

2026-10-23, main working tree based on `714802a`. The previous goal turn made
concrete progress: Story185 completed screenplay-first Home and associated
truth fixes with representative browser evidence. This pass ran the direct
`scripts/triage_facts.py --json` collector in the main thread and refreshed all
five neutral lane packets. The 11 spec categories remain partially covered;
no ready story does not mean the product is complete.

The final cross-domain shortlist was:

1. **Make UI-test inventory omission fail automatically (Story208).** Fresh,
   locally reproduced evidence shows a current false green. Existing audit
   ownership and checker patterns support a bounded repair without providers,
   new architecture, or model/default changes. Stop when omitted maintained
   modules/fixtures fail and the correctly declared real inventory passes.
2. **Fresh full-pipeline walkthrough (Draft229).** Widest immediate product-truth
   coverage, now that185/201 are complete. FP1 is194 days old against14-day
   cadence. First establish fresh normal intake and the provider/execution
   envelope; stop at one honest dated report rather than rerunning to green.
3. **Representative reference-pack fidelity (Draft197).** Strong active
   spec:6/7 value, but the next paid comparison still needs a representative
   source-backed reference strategy and an actual retry trigger. Existing
   untracked visual evidence must retain its provenance/ownership.

The confirmed Export focus-return defect remains a separate small UI candidate.
No new eval actionability or convergence-ready compromise appeared. Exhausted
model retries, old untriaged links and cadence-only architecture flags do not
justify unrelated provider runs or speculative refactors.

## Vs Ideal

The direction is improving: the surfaced Home is calmer, generated cut coverage
and review status are inspectable, and normal headless assembly is available.
The gap to the north star remains substantial: coherent iterative filmmaking
still needs fresh full-path proof and representative visual continuity evidence.
This execution-ideal repair removes a manually maintained blind spot in the
evidence system; it is not a capability or feature-completeness claim.

## Reproduction and chosen contract

`baseline.json` records an in-memory mutation of the real ledger: remove
`ui/tests/media-validation-health.test.ts` and its captured needs_review fixture.
The current checker returned no inventory error and the current manifest omitted
both, even though `make test-ui` selects the test. No source/evidence file was
deleted or edited for the reproduction.

Use Makefile's existing `ui/tests/*.test.ts` boundary and regular fixture data
under `ui/tests/fixtures/` as canonical inventory, reusing the checker's current
source-versus-declaration design. Every maintained input needs exactly one
explicit test-suite claim. A suite can own multiple files; prompt/scorer/etc.
one-path-per-row rules must remain intact. Discovery must not turn pending
review into terminal certification. Exclusions follow manifest cache/OS policy;
unsupported symlink inputs must fail explicitly rather than disappear from the
hash inventory.

Ownership stays in the existing checker (507 lines before, no classes), with
focused helpers and tests. Historical archives/manifests are immutable. This
touches neither application behavior nor AI decision logic, so browser tests,
model tournaments, and scored provider calls do not validate the change.

## Verification

The focused worker's first five new inventory cases failed3/passed2 before the
repair and passed afterward. Two symlink probes then failed before explicit
rejection was added; the final ledger suite has31 passing tests, plus5 passing
suite-boundary tests. Parent replayed three actual omission mutations through
full validate_ledger: missing test, missing fixture, and both together. Each
now reports the exact missing canonical paths; the actual complete terminal
ledger passes. `repair-proof.json` records those results and exact unchanged
historical manifest/index hashes.

Independent strong review repeated the real omission and manifest-selection
checks and found no material issue. The existing one-canonical-path-per-row
contracts were untouched; pending UI ownership still fails require-terminal.
No model or scored evaluation ran and no score changed.

The final14 manifest tests, targeted Ruff, real terminal-ledger check, current
manifest check, methodology compile/check and diff hygiene pass. Proportional
validation reuses earlier unaffected application/UI/backend evidence rather
than rerunning product suites for a checker-only change. Story208 is reclosed.
Current broad-registry rejection of44 unrelated retained-media extras remains a
separate ownership issue. Those files and the strict gate stay intact.

The new immutable current snapshot isv25, with995 declared files and bundle SHA256 `752d449977abf54102e57c9331f86e46cf33dc6842e7ecd191bff5cb93e4f2ae`. Earlier snapshots remain unchanged.

Optional verification: `PYTHONPATH=src .venv/bin/python scripts/check_truth_audit_ledger.py --require-terminal` and inspect `repair-proof.json`.

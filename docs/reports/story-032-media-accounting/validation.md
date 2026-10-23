# Story032 media-accounting validation — 2026-10-23

Disposition: **Close now** for the reopened accounting regression. Final focused
review has no actionable findings. Grade: **B** with explicit live-provider and
credential-incident limits below. Main is dirty; no staging, commit or push.

## Impact

Saved video estimates now include compiler and media work. Later failures retain
known incurred estimates and successful clips. Unknown job outcomes remain
visible through the driver, reports and UI; they do not become zero, budget
allowance or a blind retry. Unsupported retired targets fail before paid media
or prerequisite work through the normal API start path. Figures are estimates,
not provider invoices.

## Findings and disposition

| Finding | Decision and evidence |
|---|---|
| Video cost omitted; later failed units lost known work | Accepted; real red render-v3/driver-v2 fixtures, typed receipts and168 affected tests. Earlier render-v1/v2 and driver-v1 are setup failures, not behavioral proof. |
| Bearer credential forwarded to returned media URLs | Accepted; submission/poll auth retained, download/redirect auth absent; mocked boundary tests, no live CDN claim. |
| Complete run B showed project budget remaining despite unresolved A | Accepted P2 from Codex; `history-budget-red-v2.txt` has2fail/1pass, `history-budget-green-v1.txt` has23pass. Only project-scope status is omitted; B keeps its complete run allowance. |
| Historical raw states bypassed replay guard | Accepted parent finding; canonical stage summarizer reused. Both red historical API cases now pass;82 API/preflight tests and actual API409 proof. |
| Real singular `/run/:id` consumer and separate AI-previz viewer missed by initial UI changes | Accepted browser finding; shared metrics/cost component now reused. Mobile long badge also fixed and bounds inspected. |
| Follow-up review | No actionable findings; bounded static review of actual fixes. It did not independently execute tests or verify provider billing. |

Review signals: `output/story-032-codex-review.txt` and
`output/story-032-codex-review-followup.txt`. Their scope is the uncommitted
accounting work, not unrelated earlier fixes in this checkout.

## Acceptance evidence

| Current-slice acceptance | Result |
|---|---|
| Baseline failing fixtures before implementation | Met: baseline, render-red-v3 and driver-red-v2 provenance records. |
| Exact current provider/model/resolution/duration/price provenance | Met: xAI pricing/identity/duration tests; current rates are480p USD.05/s and720p USD.07/s. Known retired or unqualified targets reject; no replacement adopted. |
| Artifacts, driver and summaries retain success/partial costs once | Met: receipt dedupe/conflict, aggregate-ordering and partial-driver fixtures; summary/export tests. |
| Media download credentials separated | Met: mock HTTP and redirect assertions use synthetic loader values. |
| Unknown jobs survive without blind resubmission | Met: transport indeterminate-submit/poll cases; terminal cost-bearing driver failures; typed evidence and API replay guard. |
| Automatic still backfill accounted or rejected before paid work | Met: pure dry-inspection, existing-reference/no-work cases, and fail-before-dispatch tests. New paid still generation remains unavailable/unqualified. |
| Honest cost UI and API replay | Met: normal completed and historical media projects, both run routes, project history/trend and saved video; actual422/409 responses create no run dirs. |
| Proportional tests, schema and manual artifacts | Met: checks below and typed output inspection. No quality score or adoption is claimed. |

## Checks and evidence reuse

- Integrated affected backend:168passed (`integrated-backend-tests-v2.txt`).
- Credential-free broad unit run (`broad-unit-v2.txt`):2287passed and one API
  coercion fixture failed because it implicitly depended on a developer key.
  The fixture now declares a synthetic prefixed xAI key; the affected44 tests
  pass (`api-coercion-readiness-green-v1.txt`). Production readiness was not
  bypassed. This is composite final coverage, not a claim that the original
  broad command itself passed.
- Later affected service/export/budget tests23passed, API/preflight82passed.
  Those checks cover the changed dependencies after the broad run. Unchanged
  broad-unit evidence is reused; no third full-unit run was needed.
- Seven fake dotenv environment tests passed in a separate credential-cleared
  process with temporary fixture loading enabled (`env-fixture-tests.txt`).
- Immutable manifestv27:1050files, bundle
  `867cf1cc3da0d3c511135af89c5e648e8895f3e0d0982683ceb3ad9d39086538`.
  Current manifest and terminal ledger checks pass;45 manifest/ledger tests pass.
  Earlier versions are unchanged. Selected runtime dependencies were added to
  their existing throughput/previz ledger owners.
- Final full src/tests and affected scripts Ruff passes (`final-ruff.txt`).
  UI lint and `tsc -b` pass after final layout edits;25 maintained UI tests pass.
  Final production build passes (`ui-final-build.txt`); existing chunk-size
  advisory remains. No CI workflow is declared in `.github/workflows/` here.
- Methodology compile/check refreshed after closure. Early compile attempts
  failed because new work-log lines lacked the parser's compact timestamp;
  formatting was corrected without weakening cadence validation.

Tested environment: this checkout with `PYTHONPATH=src`, project virtualenv,
provider API-key variables cleared and `PYTHON_DOTENV_DISABLED=1`; explicit fake
keys in isolated tests. No provider calls from accounting verification. Final
source hashes are in `final-source-identities.json`; exact dependency snapshot
is manifestv27. Planning/story/report-only close-out edits do not invalidate
code tests.

## Manual and browser proof

`normal-driver-partial-video-v1.json` and `normal-driver-partial-state-v1.json`
were inspected: saved video .41 =compiler.01 +synthetic media.40; failed render
stage1.24 =four compilers.01 +three videos.40,7unique receipts,3clips preserved.
This normal driver/module/store execution uses seeded upstream fixtures and fake
media; it is **mechanical accounting evidence**, not product-quality proof or
support for the retired fixture provider.

Representative browser states instead come from normal actual runtime projects:
`open-frequency` fresh intake run-fae39865 and existing
`brick-steel-full-retired` media runs/artifacts. Desktop1600x1100 and
mobile390x844 show qualified totals, known subtotals, unresolved historical
media, unknown averages/trends and no replay controls. Both surfaced singular
and dedicated run routes were inspected. The saved historical AI-previz video
shows its unverified recorded estimate separately from current recipe adoption
status. Final mobile label/warning bounds are60..318 within390, no document
horizontal overflow. Saved screenshot and DOM files are alongside this report;
`browser-console.json` is empty. Native viewport override did not affect the
existing hidden tab, so documented CDP viewport/screenshot controls produced the
verified mobile dimensions; temporary overrides were reset.

`live-api-proof-v1.json`: health200; Render current/all preflight soft-block;
start422; historical resume/retry409 `unresolved_media_cost`; no new run dirs.
API restarted cleanly after final backend changes. No media submission occurred.

## Architecture, limits and follow-up

ADR002 (preflight) and003 (demand-driven Film lane), spec1.6/spec8.1 and R12 fit.
No accounting-specific ADR applies. Prices, permissions, identity, arithmetic
and provenance are deterministic; no semantic decision-model change is needed.
Render, video, stage execution and cost responsibilities were extracted; no
retired-transport shim or second ledger remains. ProjectRun remains oversized
(~840 lines after metrics extraction); untouched flow responsibility is a
watchpoint, not a claim of complete UI decomposition. Domain counts/notes advance
without resetting full-audit dates.

No fresh generation, provider billing/access/quality qualification, historical
rate backcast, strict within-stage spend cap, crash recovery, or general failed
LLM-response billing guarantee. Current compiler calls direct `call_llm`, not
RoleRuntime; a generic dual-ingestion producer is not claimed. Historical media
with absent receipts stays incomplete. Existing current-recipe adoption gating
still uses its maintained evaluation evidence; this repair does not promote a
provider or rewrite that benchmark result. Story138 remains Draft for coherent
prepare/inspect/planning work;229 remains Blocked pending qualified current
media and an inspectable envelope. The full FP1 walkthrough is still unfinished.
No scored AI eval ran, so no registry score was changed.

## Credential incident and learning review

A mocked test failure printed a configured xAI key in diagnostic tool output.
No request was sent. The saved log was sanitized, loader stubs fixed and offline
process isolation applied. `credential-scan-final.json` found no exact configured
key values in scanned saved task artifacts. Sanitizing a file cannot erase
already-emitted tool history: the xAI key should be rotated by the operator.
No credential/account change was performed. This follow-up is not represented
as resolved by the code tests.

`/learning-review`: **candidate-warranted**, one high-risk miss and a small
pre-import isolation guard. Draft:
`docs/learning-candidates/candidate-20261023-offline-test-credential-isolation.md`.
No live skill/instruction/test-bootstrap policy or memory was changed; promotion
requires explicit approval.

Optional verification: open `/open-frequency/runs/run-fae39865` for a complete
estimate, `/brick-steel-full-retired/runs` for incomplete historical subtotals,
and scene001 Render on the fresh project for the current provider blocker.
The continuous triage goal remains active. No commit or push is authorized.

Close-out: `/mark-story-done` applied to the reopened slice. Existing Story032
Changelog entry retained under that skill’s duplicate-entry guard. The story
and generated dashboards record completion;138/229 and credential rotation
remain explicitly separate follow-ups.

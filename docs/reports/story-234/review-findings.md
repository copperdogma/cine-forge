# Story 234 review findings

Independent `codex review --uncommitted`, requested Astra high, completed against the active uncommitted implementation. Served identity was not separately verified. This first review is advisory evidence with four accepted defects, not a clean validation gate.

| Finding | Disposition | Required proof |
|---|---|---|
| P1 preparation retry/resume drops end_at and may run video without review | Fixed, targeted recovery tests pass | Both recovery paths retain selected stop boundary; no video stage |
| P1 filesystem entity ordering differs between normal driver and inspection snapshot | Fixed, shared collector canonicalized | Deliberately reversed enumeration yields identical consumed inputs |
| P2 one-clip previz has neither clip viewer nor standalone viewer | Fixed, one-clip consumers tested | One current clip has playback/action; missing and historical scopes remain honest |
| P2 approval validation occurs before initial run state | Fixed, pollable initializing/rejected context | Pollers see state while guard runs, rejection stays API-readable |

Parent review also accepted two direct findings: confirmed runs must retain normal server readiness (not merely UI gating), and distinct approved plans can anticipate identical output versions/media paths. The latter is proven by a deterministic helper probe. A narrow per-project nonblocking OS file lock must cover all driver runs whose selected stages include the renderer, from source check through output persistence. It must not serialize preparation or consume an approval on contention. This is bounded output safety, not a general job/reservation platform.

## Browser failure evidence

Two normal surfaced preparation runs completed backend work but crashed the React UI at completion with `Maximum update depth exceeded` and composed-ref/state-setter frames. The second ran under frozen UI code, ruling out an HMR-only explanation. Retained console: `browser-failures.json`. Cold reload and explicit inspection work, but that does not satisfy the transition acceptance criterion.

The focused UI investigator found installed Radix Slot1.2.3 and old related primitives with the unstable ref pattern described in [upstream issue3963](https://github.com/radix-ui/primitives/issues/3963) and [fix3967](https://github.com/radix-ui/primitives/pull/3967). [React documents ref detach/reattach behavior](https://react.dev/reference/react-dom/components/common#ref-callback). This is a plausible mechanism, not yet locally proven causality or a license to hide the error with retries. Keep the failure until a bounded repair passes the same real completion transition.

## Accepted fixes and local proof

All four first-review findings are fixed. Recovery tests retain `end_at` for retry and resume; reversed entity enumeration produces identical shared inputs; the UI current-clip predicate includes one-clip plans; initializing state is published before approval validation and rejection remains readable. Parent readiness and concurrency findings are also fixed: confirmation retains server preflight, and the per-project POSIX renderer lock spans input validation through persistence for both approved and ordinary driver paths. Contention does not consume the worker claim. Focused regression files name these contracts explicitly.

The UI dependency repair is narrowly `@radix-ui/react-slot: 1.2.5`, with its expected compose-refs1.1.3 dependency. Primary dependencies were not changed. Fresh scene3 normal preparation completed with chat open and automatic inspection; desktop/mobile controls remained usable and there were no new console warnings/errors after the patch. The standalone fixture did not reproduce the old fault, so the observed successful normal transition is the bounded repair evidence. No claim of general React failure elimination is made.

Second independent review completed with the findings below; this record is not yet the final closure verdict.

## Second review — three accepted same-scope defects

The second independent Astra-high `codex review --uncommitted` identified:

1. **P2 confirmed runs omitted downstream media validation.** Accepted: existing recipes include `validate_media`, but confirmation ended at the video stage. Retain downstream validation restricted to the generated selection; prove validation outputs and costs without live provider calls.
2. **P2 approved-run Resume acknowledges guaranteed failure.** Accepted: recovery rewrites runtime and run ID while one-use approval remains bound to the prior run. Reject recovery synchronously with a fresh-inspection handoff before queuing; do not widen replay authority or add generalized recovery.
3. **P2 budget-paused preparation appears successful.** Accepted: terminal `finished_at` alone does not mean selected preparation stages succeeded. Require successful preparation and retain the normal paused/resume affordance.

These are still implementation gaps, not close-out bookkeeping. Focused fixes and confirmation are in progress; story remains In Progress. The later manifest roll is intentionally delayed until this executable scope is stable.

The precise Slot-specific upstream source is [PR3899](https://github.com/radix-ui/primitives/pull/3899) with [issue3799](https://github.com/radix-ui/primitives/issues/3799); earlier3963/3967 links described the general unstable-ref failure class. Installed Slot1.2.5 uses useComposedRefs. Its own compose-refs resolves to1.1.3 while unrelated primitives retain1.1.2; no broad dependency upgrade is implied.

## Final disposition — 2026-10-25

All three second-review findings are fixed and confirmed. Approved API/CLI execution includes validate_media; only the current run's exact selected outputs are admitted. Recovery rejects before queue/bootstrap, retaining unresolved-cost priority. Paused preparation has an actionable run link and cannot emit success; existing plans avoid empty preparation jobs. A final bounded independent read-only review found no material issue. Normal scene4 budget-pause proof has0calls/0attempts/0newcost, with original budget restored; final browser console is empty. Validation and closure authority: validation.md.

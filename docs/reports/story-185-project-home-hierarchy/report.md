# Story 185 — screenplay-first Project Home

Verified locally on 2026-10-23 against the working tree based on `714802a`.
No commit, push, provider call, or model/default change.

Home now keeps the screenplay, title, logline, and compact metadata primary.
Scenes is explicit even with chat closed. Script Bible and Project Cut use
labeled dialogs; only actionable artifact health appears as a compact Inbox
alert. The cut card distinguishes generated clips from scenes. A persistent
controller retains pending assembly state when its dialog closes.

| Real pipeline project / viewport | Script top before | Script top after |
|---|---:|---:|
| Degraded Brick & Steel / 1600×1100 | 717.5px | 330px |
| Degraded Brick & Steel / 390×844 | 1105.75px | 462px |
| Healthy Brick & Steel 3 / 1600×1100 | not measured | 280.8px |
| Healthy Brick & Steel 3 / 390×844 | not measured | 376px |

The four JSON packets contain 60 passing acceptance checks with zero console
errors: screenplay in the initial viewport, no horizontal page overflow, visible
Scenes, no persistent health/cut cards, health alert matching the actual data,
Bible contents, clip/scene labels, dialog bounds, and Bible/Cut keyboard focus
restoration. Export still opens with screenplay/project-data options and closes.
Desktop and mobile Scenes navigation, screenplay scene-divider navigation,
and the cut's Close button were additionally checked. Screenshots were manually
inspected; mobile retains readable script and dialog content.

The retained `browser-acceptance.mjs` function ran through CUA's documented
tab/viewport/filesystem APIs. Resizing an already-open desktop chat opens its
existing mobile modal; that modal was explicitly dismissed before mobile Home
acceptance. Some cold navigation probes exceeded the browser host's short
selector deadline; subsequent observations confirmed normal data loading.

## Real cut and validation

The unchanged final-output recipe ran via `DriverEngine` against existing Brick
inputs and pipeline artifacts. It produced new immutable `final_output:project:v1`
and `media_validation:project:v1`; `representative-cut-driver.json` records both
successful stages, original runtime parameters, and $0 cost. No semantic model
was configured. Both artifact schemas validate. The 14.043-second partial cut
contains the latest track manifest's two clips for scene 2 and explicitly omits
five other scenes. Decode/probe passed, five frames were extracted, and semantic
review remains skipped / needs_review. A sample frame was manually inspected;
this check does not establish creative/media fidelity.

Desktop/mobile Project Cut displays partial coverage, generated clip/scene
counts, review-needed status, validation samples, and working artifact and
validation links. Native video controls played the actual cut to its end
(`cut-playback.json`). The final-output card's initial misleading “Validation
Failed” label for backend needs_review was captured as a real regression fixture
before repair. It now says “Needs Review” in amber; failures remain failures.

`assembly-pending-regression.json` records a separate mechanical probe: intercept
the actual assembly POST before backend execution, close/reopen the dialog,
assert assembly remains disabled, then return a synthetic failure and assert it
re-enables. Exactly one request was intercepted. No run/provider call occurred in
that probe. All artifact-group inventories were unchanged during the preceding
read-only UI checks (`ui-inspection-preserved-artifacts.json`). The later real
driver run intentionally adds the two new versions above.

## Validation and limits

- UI ESLint, build-mode TypeScript, production build, and all 25 node UI tests
  pass. The pre-existing large-bundle build advisory remains.
- The new health fixture and Previz consumer regressions failed before repair and passed afterward;
  it also protects failure/success/missing/stale-report distinctions and review
  attention. Previz playback-summary logic was extracted into its existing support module before adding explicit review-needed wording, shrinking its oversized panel from952 to948 lines. The real existing eight-player Previz route also renders on desktop/mobile with clean consoles; its stale state does not exercise the new review-needed branch. No scored AI evaluation ran, so no score was changed.
- Independent strong review cleared the extracted navigation/controller logic;
  the parent inspected generated outputs and screenshots.
- The former 612-line Home is now 216 lines; focused header/Bible components and
  the 352-line cut component keep new/extracted functions below 100 lines. The existing oversized PrevizPanel is acknowledged and shrank during its focused summary extraction.
- The old Story 194 fixture has seeded canonical content and no uploaded input;
  it was excluded from acceptance. No artifact was seeded or copied into a
  project for product proof.
- The existing controlled ExportModal returns focus to the document body. Its
  reachability/closure is preserved; the new Bible/Cut panels restore focus.
- This targeted pass does not reset the stale full FP1 walkthrough or unrelated
  architecture-audit dates. Broad registry validation still detects previously
  recorded unrelated retained-media extras; this change does not weaken it.

Where to verify: open `/brick-steel-full-retired`, use Scenes, Script Bible, and
Project Cut. In Project Cut, open Artifact Detail to play the partial cut or
Validation Detail to inspect local-only validation and omitted coverage.

Final close-out: current immutable contract v24 includes995 declared files, including the new UI test and real fixture (bundle416e806c9cb50e08212198d52a73cf1d4ef63b499151113b05202cd871b439af). Ledger/current-manifest checks pass;34 focused ledger/manifest tests and the final14-test manifest rerun pass. The generated methodology view was refreshed after the final work-log entry; remaining warnings are the existing due architecture domains and stale FP1 coverage. Story229 owns the next bounded walkthrough readiness check.

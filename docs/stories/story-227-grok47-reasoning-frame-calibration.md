---
id: "227"
title: "Grok 4.7 Reasoning Frame Calibration"
status: "Done"
priority: "High"
ideal_refs:
  - "R12"
  - "R18"
spec_refs:
  - "spec:7"
  - "spec:8"
  - "spec:9"
adr_refs:
  - "ADR-003"
depends_on:
  - "226"
category_refs:
  - "spec:7"
  - "spec:8"
  - "spec:9"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "methodology_tooling"
roadmap_tags:
  - "evals"
  - "model-refresh"
legacy_system: "Cross-Cutting"
---

# Story 227 — Grok 4.7 reasoning on source-reviewed ordered frames

Status: Done

## Decision contract

Owner: `video-understanding`, spec:7/spec:8/spec:9, headless reference analysis only. User authorized Grok4.7 reasoning followup; coordinator resolved current owner v4 truth overlay (same v3 JPEGs/prompt) and current quality comparator exact GPT6.1Sol low4096. Current remote base b66b42ad989c1187ff539ec1b4ddc398d3900da2; isolated branch codex/grok47-frames-effort-20261002. Primary checkout dirty and read-only.

Fresh native xAI Responses strict schema, `grok-4.7`, low/medium/high, equal8192 reasoning-inclusive output cap, storefalse, no sampling or output cache, serial independent conversations. Calibration: storm_tunnel_lateral_run, dialogue_confession_push_in, quiet_bedside_vigil. Same maintained deterministic scorer and cross-provider Opus4.6 frozen rubric; source-backed clarifications from Attempts043/045/046 fixed before calls. No semantic prompt/golden/scorer/default changes. Private media/scripts, audio/video and ScriptBible excluded.

USD5 total all-provider hard cap. Conservative xAI per-dispatch USD2.098304 uses500K context at long-contextUSD4/M +8192 output atUSD12/M. Official image understanding lacks dimension-token formula, so empirical prior4360 input is not a hard bound. Calls serial; reserve before dispatch and release only on settled valid charge. Unknown liabilities remain charged at reserve. Matrix completion contingent on settledcost; do not promise all worstcasecalls fit. Atmost2operational recoveries; reuse subjects for judge repair. Judge reserve actual serializedUTF8bytes+4096 role/schema padding atUSD5/M +1024output atUSD25/M. No secret transfers: ownerwrapper provides existing xAI/Anthropic/OpenAI credentials.

Selection only after source review: calibration mean>=.70 and2/3rubric>=.80, meaningful>=.15 improvementoverfreshlow unless lowitself>=.80. Prefer source-acceptable/economic arm, not highest arithmetic score alone. Selectedarm other3cases reuses calibrationoutputs; full6overall>=.80 plus per-call<=15s and<=USD.02 needed for freshSolcontrol6. Same-slice arm selection stays exploratory; remaining3 are heldout confirmation. No autonomous QA/default/runtime adoption.

## Work log

2026-10-02 — Read ownerprotocol/skill/AGENTS, current attempts043/045/046, task/scorer/v4sourcecorrections. Sourceoverlay13file checkpassed. Ownercatalogdiscovery started; existingcredentials present bynameonly. Wrote zero-cost sourcehashfreeze and progressive runner. Exactsynthetic fullrawreceipts persisted before adapter parsing; native/harness same dispatch qualifies firstcalibrationcall, no extra paid duplicateprobe. Next: coordinatorpreflight review, then boundedcalibration.

2026-10-02 coordinator clarification before arm selection — The inherited initial plan described current owner per-call value gates, but this approved reasoning campaign preserves Attempt038's mean latency<=15s and mean subject cost<=USD.02. Individual exceedances remain reported, not automatic exclusions. No subject, rubric, scorer or target changes; calibration is exploratory and heldout3 required for broadening. Original call-time freeze remains immutable; this additive policy supersedes only economics selection wording.

2026-10-02 result — All9subjects and9Opusjudges completed, no paidrecovery. Currentv4 calibration low.50987/5.402s/USD.009032; medium.54853/17.000s/USD.015300; high.49648/19.980s/USD.015206. Allarms0/3rubricpasses; increasedeffortdoesnotrepair dialoguegrowth or tunnelstreak misses. Accuratebedsidegeometry separatedfromsubjective tagpenalties. Noexpansion/controlrun because noarmqualifies. ActualxAIUSD.118614 +estimatedOpusUSD.105910 =USD.224524/5, unknown0. Attempt047/source-review/fullraw/hashmanifest preserved; ownerkeysmanaged/noinjectioncleanup. Storyremains In Progress pending normal validation/closure; no commit/push authorized.

Post-run limitation — Each ofthese9subjects observed278–2002billedoutputtokens, within8192, but separateownerobservedprovider exceeding8192. Do not infer universal capenforcement fromthisrun. Currentreceiptssettled/no furtherpaidcalls. Original/repairedexecutedrunnerarchives distinctfromcleanactivecode. Offlineverifier checksall9bodies/usage/scorer/hashes; 80focusedvideo tests initiallypassed; finalcontractmanifest/registry/methodologychecks recordedbelow.

Validation — 85focused video/contract tests passed; Ruff passed allchanged Python. V4 builder checked13sourcefiles. Offline verifier rechecked63frozeninputs and allretainedrequest/raw/output/judge hashes,9uniqueexactsubjectIDs,5imagebodyparityacrossefforts,providerusagecharges and unchangedscorerreplay withoutprovider calls. Registry/truthaudit/newimmutablev20manifest checks passed; methodology compile/check current with preexistingUIscout/architecturefreshnesswarnings; diffwhitespaceclean. Activepaidrunner failcloses onceimmutable result exists. No default, production, credentialaccount, commit/push changes.

## Workflow Gates

- [x] Build complete
- [x] Validation complete or explicitly skipped by user
- [x] Story marked done via /mark-story-done
- [x] Tenet verification complete
- [x] Documentation updates complete

## Close-out — 2026-10-02

Cam authorized finish-and-push for linked evidence. Closed via the owner mark-story-done convention after reusing the unchanged 85 focused-test inputs and passing offline evidence verification, lint, registry/truth ledger/immutable manifest and methodology checks. All source mismatches are classified; temporal capability failures are non-runtime-blocking because no product frame analyzer exists. The requested three-effort calibration is complete; the predeclared failed progressive gate makes additional subjects/comparator unnecessary. No in-scope inbox changes exist in this worktree or the primary checkout. No GitHub workflow or mandatory repository CI/review gate is configured. Changelog and generated planning views refreshed. Full safe synthetic receipts and source bytes are repository-resolvable; secrets and private fixtures were excluded. The containing close-out commit adds custody without changing call-time base/hash identities or promoting calibration into an autonomous-QA/default verdict. Landing waits for coordinator all-repository preflight.

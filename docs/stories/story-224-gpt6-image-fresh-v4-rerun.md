---
id: "224"
title: "GPT-6 Image Fresh V4 Rerun"
status: "Done"
priority: "High"
ideal_refs:
  - "R12 (transparency & control)"
  - "R18 (model improvements collapse scaffolding)"
spec_refs:
  - "spec:7"
  - "spec:8"
  - "spec:9"
adr_refs:
  - "ADR-003"
depends_on:
  - "222"
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
  - "openai"
legacy_system: "Cross-Cutting"
---

# Story 224 — GPT-6 Image Fresh V4 Rerun

Cam's fresh request authorizes a new USD1.50 total provider ceiling, separate from Story 222's receipts. Fresh direct `gpt-6-sol` and `gpt-6-luna` low reasoning, five JPEGs at `detail:high`, strict Responses schema, Standard tier, `store:false`, 1,400 output tokens; same maintained prompt and all six current v4 source-corrected targets/scorer. Fresh `gemini-3.5-flash-lite` uses its unchanged maintained schema and 65,536 output cap. The independent maintained `claude-opus-4-6` rubric judges all 18 frozen outputs with 1,024 output cap. Serial dispatch, no SDK/automatic retries, fresh run identity, synthetic/public owner fixtures only. No ScriptBible or product inference integration, default change, commit, push or deployment.

Owner credentials are loaded only through `scripts/with_cine_forge_provider_env.py`, verified by presence. Native subject requests are made by the maintained adapter; offline replay through its exact `call_api` verifies entrypoint parity without spending on duplicate subjects. The direct runner explicitly reserves every request before dispatch and stores raw bytes before parsing. Unknown usage/error billing keeps the maximum reservation. Conservative subject input allowance is 20,000 tokens including all five images/schema/prompt; judge input allowance is 10,000. Reservations: Sol USD0.064, Luna USD0.0032, Gemini USD0.16984, Opus USD0.0756, including worst cache-write pricing. Estimated total approximately USD0.70, but the next request is admitted only if settled plus still-reserved plus its maximum remains <=USD1.50. Complete 6x3 is preferred; no semantic tuning or new subject calls for judge/scorer faults.

Official OpenAI [changelog](https://developers.openai.com/api/docs/changelog), checked by Conductor 2026-09-27, records a September 25 image-encoding fix affecting Sol/Luna and recommends reruns. Yesterday's September 26 evidence already postdates that notice; this is a fresh replication, not a causal before/after measurement of the fix. Official model pages: [Sol](https://developers.openai.com/api/docs/models/gpt-6-sol), [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna). Standard per-million input/cache-read/cache-write/output rates are Sol 2/.2/2.5/10 and Luna .1/.01/.125/.5. Gemini .30/2.50 and Opus 5/25 retain the owner contract. Actual billed provider dollars are unavailable; token-derived upper/estimated charges are reported.

The inspected headless reference analysis lane may gain a preferred model. No product ordered-frame inference call exists; the 0.80 quality gate, <=15s subject latency and <=USD0.02 subject cost remain required for autonomous QA/default promotion. Current Luna v4 derived evidence .5986 versus Gemini .4313, all six paired wins, is retained. The new matrix does not erase those prior results.

Preflight: isolated `codex/gpt6-image-rerun-20260927` from `origin/main` f4a0dec; v4 builder checked all 13 target/source files. Owner live catalog discovery completed. With socket/network access disabled, focused GPT6 transport, benchmark and adversarial scorer checks passed 44 tests. An initial test command named a nonexistent scorer test file; it made no inference and was corrected to the actual maintained test filenames. The call-time freeze pins task, prompt, providers, scorer, v4 references, all submitted JPEGs, judge topology and bounded runner. No runtime architectural choice is being changed; ADR-003 remains lineage context.

Completed: [Attempt 044](../evals/attempts/044-gpt6-image-fresh-v4-rerun.md) preserves all18 subjects/18 judges and source review. Sol .6080, Luna .5902, Gemini .3861; no combined case meets .80. Luna remains inspected headless value choice; Sol size-change example is useful but no automatic routing subset is proven. Total USD0.50574295, no unknown reservations/retries. Product/default promotion remains held. Archived exact call-time runner before formatting/import cleanup and immutable-artifact guards; original freeze/result unchanged. Registry records attempt history without replacing committed current-score evidence. No extra provider calls or broad tests.

Closeout validation: registry consistency passed; methodology graph build and current-output check passed after converting Story 224's frontmatter to the owner's supported indented list format. Initial inline-list and PyYAML indentation representations were local documentation faults, corrected without inference. Existing architecture/UI-scout warnings remain unrelated to this run. `git diff --check` passed. Focused 44-test evidence was reused because unchanged provider/scorer inputs stayed frozen; postrun runner lint and offline archive/cap admission checks passed. No broader suites, replayed paid calls, product changes, commits or pushes.

Authorized scoped commit preparation: retained the 36 synthetic native receipts and ledger under `docs/evals/receipts/gpt6-image-rerun-20260927/`, pinned by immutable retention manifest v2. The completed-run lock blocks accidental subjects/judges redispatch from a fresh clone. Original run artifacts are unchanged. Inbox reviewed; no live capture difference. Current origin/main remains the producing base; no integration required. Reused 44 applicable offline tests; only new guard, retained hashes and records were verified. Coordinator owns final multi-repo push clearance.

Commit-preflight verification passed with sockets disabled: subjects and judges both reject redispatch when their output directory and ledger are absent, before creating that directory or making any request. All 36 tracked native receipts match producing hashes; the original result/freeze/archive and postrun runner/v2 retention manifest hashes reconcile. Sensitive credential/header field scan passed. Ruff, registry consistency, methodology current-output check and diff check passed. No repository CI workflows or configured Git hooks were found locally. Existing architecture/UI-scout methodology warnings are unrelated. No provider access or paid inference occurred during closeout.

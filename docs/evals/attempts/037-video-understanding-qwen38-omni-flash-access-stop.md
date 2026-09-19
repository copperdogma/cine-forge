# Eval Attempt 037 — Qwen3.8-Omni-Flash ordered-frame access stop

**Date:** 2026-09-19  
**Status:** Deferred by user — direct-provider access unavailable  
**Eval:** `video-understanding`  
**Subject:** Alibaba Model Studio `qwen3.8-omni-flash` (not ordinary Qwen3.8 Flash)  
**Lineage:** Story 208 repaired ordered-frame v3 surface; spec:7, spec:8, spec:9

## Approved decision contract

Conductor Scout 071 revised item 1 authorized US$0.75 total for direct Alibaba
qualification, `dialogue_confession_push_in`, and the six maintained cases only
if every earlier gate passes. Use low reasoning, five ordered JPEGs per case,
`video-understanding-frame-packet-v3`, current deterministic scorer and Opus 4.6
rubric. Require exact served identity, terminal response, reconciled usage,
strict contract and native/harness parity, all hard assertions, overall >=0.80,
latency <=15 seconds and subject cost <=US$0.02/case. Fresh Gemini 3.5 Flash-Lite
control follows only if the candidate advances and the all-inclusive cap fits.
Existing repaired references are Gemini 3.6 Flash 0.4397 and Gemini 3.5 Flash-Lite
0.4071; they support HOLD, not a fine ranking. No production-default change is
part of this campaign. This task is a capability detector, not evidence that
native audio/video or role-modality compromise C5 can be removed.

The README identifies project-owned synthetic controls. No private screenplay,
media, audio, transcript, semantic title or MP4 would be sent. Disclosed Alibaba
posture allows storage, claims no training, and has no established ZDR guarantee.
Strict-contract failure would allow at most one labeled JSON-object anchor
diagnostic; such a diagnostic cannot unlock the full adoption comparison.
Concurrency would begin at one, no subject cache, and multi-case work would
require a zero-cost resolved-matrix and conservative spend preflight.

## Current access evidence and stop

Isolated worktree: `/Users/cam/.codex/worktrees/qwen38-omni-flash-cineforge-20260919`.
Branch: `codex/qwen38-omni-flash-20260919`.
Fetched remote base: `b5140648653c16194ba025a80d0b9542ddaeb775` (`origin/main`).
The primary checkout had unrelated edits and was left untouched.

The owner's normal `scripts/with_cine_forge_provider_env.py` loader resolved the
isolated checkout and shared owner `.env` / `.env.local` without copying them.
Presence-only checks returned false for `DASHSCOPE_API_KEY`, `ALIBABA_API_KEY`,
`ALIBABA_CLOUD_API_KEY`, `QWEN_API_KEY` and their `CINE_FORGE_` forms. No other
DASHSCOPE/ALIBABA/ALIYUN/QWEN variable names were present in the hydrated process.
No values, hashes or secret files were printed, transferred or stored.
The coordinator reported no supported centrally custodied direct Alibaba access;
the central helper has no Alibaba provider mapping. This does not assert that
an arbitrary unregistered variable is absent from the vault, which was not read.

Therefore execution stopped before an authenticated catalog request, inference,
contract qualification, adapter construction, matrix resolution, subject,
incumbent, judge or diagnostic call. Broad other-provider model discovery was
not run: it cannot establish the selected direct Alibaba access and would widen
this bounded access check. No model/route substitution or account provisioning
occurred. No provider response, served identity, error or usage exists.

Public identity evidence is the dated Conductor source review of Alibaba's
[exact model page](https://www.alibabacloud.com/help/en/model-studio/qwen3-8-omni-flash),
[structured output guide](https://www.alibabacloud.com/help/en/model-studio/qwen-structured-output)
and [privacy notice](https://www.alibabacloud.com/help/en/model-studio/privacy-notice).
API listing is not callability. No inference claim is made from these documents.

## Spend and layered verdict

| Layer | Outcome |
| --- | --- |
| Access | Local execution blocked by missing configured direct credentials; model callability unverified |
| Transport | Not measured, including strict schema and five-image parity |
| Reliability | Not measured; no remote service request was made |
| Capability | Not measured; no semantic misses or model-wrong classification |
| Economics | US$0.00 actual provider spend / US$0.75 cap; latency and per-response cost unmeasured |
| Adoption | Defer the ordered-frame decision; current defaults unchanged |

Every stage had zero provider calls and zero spend. No temporary credential was
injected, so cleanup is not applicable. No raw model artifact exists to hash.
The user explicitly deferred this evaluation on 2026-09-19 because access is
unavailable; a key may be provisioned someday. No automatic retry is scheduled
or authorized. Reopen only on an explicit future user request after authorized
direct Alibaba credentials and regional workspace endpoint are configured;
resume at access and production-contract qualification, not at full scoring. A router evaluation would require a newly verified exact
model route and explicit scope selection.

## Reproduction and validation

From the isolated worktree, the safe access check used the owner Python and env
wrapper followed by an inline Python presence check; the body below prints only
booleans and variable names:

```bash
/Users/cam/Documents/Projects/cine-forge/.venv/bin/python scripts/with_cine_forge_provider_env.py python - <<'PY'
import os, json
names = ['DASHSCOPE_API_KEY', 'ALIBABA_API_KEY', 'ALIBABA_CLOUD_API_KEY', 'QWEN_API_KEY']
names += ['CINE_FORGE_' + name for name in names.copy()]
print(json.dumps({name: bool(os.environ.get(name)) for name in names}, indent=2))
print(sorted(name for name in os.environ if any(term in name.upper() for term in ('DASHSCOPE', 'ALIBABA', 'ALIYUN', 'QWEN')) and name not in names))
PY
```

Documentation-only stop: inspect provenance and links, validate registry and
refresh/check generated methodology records; no product suite is warranted.

Validation results: `scripts/check_eval_registry.py` PASS;
`scripts/check_truth_audit_ledger.py` PASS;
`node scripts/methodology-graph.js build` and `check` PASS (existing architecture
and UI freshness warnings); `git diff --check` PASS. `make check-evals` stops on
the contract manifest's pre-existing drift in `AGENTS.md` and
`scripts/methodology-graph.js`: both current hashes equal their fetched base
bytes. The new registry attempt is excluded from the contract projection.
No manifest, runtime, benchmark or scorer repair was performed for this access
stop. The user authorized committing and pushing this deferral record on 2026-09-19.

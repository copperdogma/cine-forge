---
id: "220"
title: "Grok 4.7 Bounded Video and Script-Bible Evaluations"
status: "Done"
priority: "High"
ideal_refs:
  - "R1 (story understanding)"
  - "R12 (transparency & control)"
  - "R18 (model improvements collapse scaffolding)"
spec_refs:
  - "spec:2"
  - "spec:7"
  - "spec:8"
  - "spec:9"
adr_refs:
  - "ADR-001"
  - "ADR-003"
depends_on:
  - "208"
  - "212"
  - "218"
category_refs:
  - "spec:2"
  - "spec:7"
  - "spec:8"
  - "spec:9"
compromise_refs: []
input_coverage_refs: []
architecture_domains:
  - "ingest_and_world_building"
  - "methodology_tooling"
roadmap_tags:
  - "evals"
  - "model-refresh"
  - "xai"
  - "grok-4-7"
legacy_system: "Cross-Cutting"
---

# Story 220 — Grok 4.7 Bounded Video and Script-Bible Evaluations

## Goal

Independently qualify direct xAI `grok-4.7` on CineForge's maintained
ordered-JPEG video-understanding and exact-runtime ScriptBible boundaries. Keep
the provisional `gemini-3.5-flash-lite` defaults unchanged unless fresh,
decision-grade evidence clears every lane gate.

## Decision Contract

- **Candidate and route:** direct xAI Responses `grok-4.7`, low reasoning,
  `store=false`, exact returned identity, terminal output, reconciled raw usage,
  and provider-enforced strict JSON Schema. xAI's current 30-day default
  retention and non-ZDR posture limit both lanes to the explicitly synthetic
  public/owned controls below.
- **Video lane:** six maintained active source-backed synthetic controls, each
  with exactly five ordered JPEGs and neutral timing metadata. No audio, MP4,
  transcript, semantic title, or quarantined case may enter the request. The
  strict `VideoAnalysisPrediction` schema and v3 prompt are frozen. Gate:
  overall `>=0.80`, each hard assertion passes, average latency `<=15,000 ms`,
  and average subject cost `<=US$0.02`; fresh Gemini 3.5 Flash-Lite is gated on
  candidate success.
- **Script-Bible lane:** one repo-authored synthetic Open Frequency exact-runtime
  `ScriptBible` case with maintained deterministic scorer and frozen
  cross-provider Opus 4.6 rubric. Gate: overall `>=0.90`, each assertion
  passes, latency `<=30,000 ms`, and subject cost `<=US$0.01`; fresh Gemini 3.5
  Flash-Lite and the second corpus are gated on candidate success.
- **Independence:** each lane has its own probes, ledger, and stop decision;
  a result in one cannot advance or block the other.
- **Budget:** aggregate US$1.10, including probes, subject calls, incumbent
  calls, and judges; video maximum US$0.75 and Script-Bible maximum US$0.35.
  Serial concurrency one, no subject cache, no semantic retry, and at most one
  changed-evidence diagnostic only for a source-backed transport defect.
- **Out of scope:** private fixtures, The Mariner unless later explicitly
  eligible and every Script-Bible entry gate passes, audio/video-native claims,
  default changes, deployment, commit, or push.

## Plan

1. Freeze the existing v3 frame and exact-runtime ScriptBible contracts, then
   validate the benchmark-only Grok 4.7 Responses adapters offline.
2. Run a minimal native strict-schema access/identity/usage probe per lane and
   confirm exact image and schema parity before the six-case visual subject run.
3. Resolve the zero-cost one-provider, one-case topologies and run each lane
   independently at no-cache concurrency one.
4. Inspect raw output, scorer, rubric, latency, usage, and cost after every
   stage; apply each lane's progressive stop immediately on a hard miss.
5. Record safe manifests, the attempt, registry, truth ledger, work log, and
   proportionate validation without changing runtime behavior.

## Work Log

20260922-0000 — created isolated worktree `codex/grok47-eval-20260922` from
`origin/main` at `bdcea8d5b9fafe9f358274ee57ccf3987a07f49f`. The primary
checkout was left untouched because it is dirty and behind origin. Read the
maintained v3 video contract and Attempts 019/023. Added benchmark-only direct
xAI Responses strict-schema adapters for Grok 4.7.

20260922-0015 — Focused adapter and regression coverage passed (46 tests).
Native and harness five-JPEG probes proved direct Responses transport, exact
identity, terminal strict JSON, raw-usage reconciliation, and ordered-image
parity before the visual subject run.

20260922-0025 — The six maintained synthetic video controls completed with
exact `grok-4.7` identity and schema-valid output. Aggregate quality was
0.4816, below the 0.80 gate; average latency was 8,608 ms and actual average
subject cost was $0.008501. This is a semantic model rejection, so no Gemini
control was run. Video spend was $0.069502 actual xAI plus $0.432825 accounted
maintained-judge estimate, $0.502327 total.

20260922-0045 — The independent synthetic Open Frequency exact-runtime case
completed with exact identity and provider-strict `ScriptBible` JSON. It scored
0.80995 aggregate (0.8967 raw deterministic; 0.92 maintained rubric), took
25,533 ms, and cost $0.015042 actual. The recorded hard score is below the
quality gate, but source inspection found the theme/journey deductions to be a
keyword-grounding ambiguity rather than a clean semantic model loss; the raw
deterministic-plus-rubric average would clear 0.90. The actual subject-cost
miss independently rejects the lane, so no comparator or second corpus was run.
Script-Bible spend was $0.035928 actual xAI plus $0.132765 accounted
maintained-judge estimate, $0.168693 total. All calls were terminal; no
unresolved exposure remains.

20260922-0050 — Recorded the video quality rejection and Script-Bible decisive
cost rejection in Attempt 038, the registry, and
the safe contract manifest. No production/default configuration changed and no
commit or push was made.

20260922-0115 — User-approved offline source adjudication replayed the saved
Grok 4.7 Script-Bible response with the unchanged scorer: `0.6999` hard and
`0.8967` raw. Four evidence deductions expose lexical sensitivity to faithful
paraphrase, while one citation and the journey wording require semantic
judgment. A generalized relaxation would admit invented relations, so no
model-specific exception, scorer/golden change, or score rewrite was made.
The versioned adjudication records source lines and hashes. The actual $0.015042
cost miss remains the independent adoption rejection; no paid call occurred.

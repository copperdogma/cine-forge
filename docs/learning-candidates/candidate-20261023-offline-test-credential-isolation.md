---
title: "Isolate provider credentials before offline tests import application code"
status: "Draft"
created: "2026-10-23"
target_surface: "tests/conftest.py and docs/runbooks/close-out.md"
trigger_class: "single high-risk credential exposure"
review_cadence: "review before promotion; no scheduled loop"
confidence: "high"
source_runs: ["Story032 media-accounting validation, dirty main714802a, 2026-10-23"]
user_corrections: ["none recorded"]
evidence_summary: "A mocked header assertion printed a real prefixed xAI credential because a generic test override did not win after application dotenv loading. No request was sent. Stubbing the loader and removing provider environment variables before imports prevented recurrence in the affected tests."
evidence:
  - "docs/research/story-032-media-accounting-2026-10-23.md"
  - "docs/reports/story-032-media-accounting/integrated-backend-verification-v1.json"
  - "docs/reports/story-032-media-accounting/credential-scan.json"
proposed_change: "Run offline tests in a provider-credential-free subprocess with dotenv disabled before application imports; require explicit synthetic loader stubs for credential assertions. Keep dotenv helper fixture tests in a separate cleared process that loads only temporary fake files."
promotion_gate: "Cam explicitly accepts this candidate and a narrow implementation proves live opt-in tests and temporary dotenv fixtures retain their intended behavior."
---

# Candidate — Offline test credential isolation

## Summary

An offline test accidentally read the configured CineForge xAI credential and a
failure exposed it in diagnostic output. A tiny process-level boundary would
protect credentials even when an individual test stub is incomplete.

## Evidence and provenance

Story032's saved verification note identifies the affected intermediate test
run. The saved log was sanitized and the key loader replaced with a synthetic
stub. The task-local `output/story-032-offline-pytest.py` clears provider API-key
variables and disables python-dotenv before pytest imports the app. Environment
helper tests ran separately with temporary synthetic files. The subsequent
artifact scan found no configured key values in the scanned saved reports; that
does not remove already-emitted tool history. No provider request occurred.
User corrections: none recorded. No secret value is stored in this candidate.

## Required evidence gate

Concrete story, research and sanitized verification records are linked above.
This is a Draft based on one high-risk miss, not an asserted repeated pattern.

## Observed pattern and smallest proposed change

Generic environment overrides are not sufficient when a repo-scoped prefixed
key has precedence or a previous import loaded dotenv. Isolate offline pytest
before collection, rather than relying solely on each test's monkeypatch.
Preserve an explicit live-test opt-in path and a separate fake dotenv fixture
path. Do not print credential values, fingerprints, request headers or env files.

## Rejection checks

This is not a novelty, taste or clean-success lesson. The general security
mandate already prohibits secret exposure; it does not currently establish a
collection-time offline credential boundary. The proposed mechanical guard
remains useful with stronger models because import order and env precedence
are runtime properties. Exact implementation and the live-test escape hatch
still need review; the temporary task launcher is evidence, not a shipped policy.

## Trigger, cadence and lifecycle

Trigger: one credential exposure during mocked validation. Cadence: one review
before promotion. Current status: Draft; next allowed transition: Proposed.
No live skill, instruction, test bootstrap or memory change is made here.
Acceptance/promotion require Cam's explicit approval. Dismissed candidates need
fresh evidence to reopen; Promoted is terminal.

## Promotion action and validation plan

If accepted, implement the smallest bootstrap boundary in the maintained test
entry point and document its offline/live separation in the close-out runbook.
Use a fake canary credential to prove it cannot reach offline transport/header
assertions, run fake dotenv fixtures independently, and demonstrate an explicitly
opted-in live-test process still receives its intended environment without
printing it. Never use a real key as the canary.

## Decision history

- 2026-10-23 — Drafted after `/learning-review`: candidate-warranted, high-risk
  miss with a small runtime guard; no promotion requested or applied.

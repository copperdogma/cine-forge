# Agent Staffing and Event Waits — Alignment 055 Receipt

Date: 2026-10-06 (America/Edmonton)
Status: policy landed on owner remote main; final receipt landing is recorded
by the rollout coordinator in Conductor Alignment 055.

Source: Conductor Alignment 055,
`/Users/cam/Documents/Projects/conductor-align-055/docs/alignments/align-055-agent-staffing-and-event-waits.md`.
Source candidate: `codex/align-055-conductor`; frozen strategic-dispatch skill
SHA-256: `6158049fc9fe13e25c79e401cfe87f85fea115a095d9ee9cf9160534bc6c0b0c`.

Owner: `cine-forge`.
Owner base: `4fce5f32e30eb48b1a5d90e5abeb346fd9daa17f`.
Owner branch: `codex/align-055-cine-forge`.
Owner worktree: `/Users/cam/.codex/worktrees/align-055/cine-forge`.

## Applied Scope

Added a short [AGENTS staffing policy](../AGENTS.md). Strategic loop review
resolves the strongest available eligible model and highest supported effort
from runtime capabilities, records requested configuration separately from
verified served identity, and uses one bounded read-only reviewer only when
needed. Full-history fork inheritance and supported override rules are explicit.
Ordinary workers remain economical and risk-sized. Completion events and
message-aware waits replace unchanged status polling; timeouts, late results,
chat authorization and continuation limits remain explicit.

Adapted only installed leaves: `loop-review`, `loop-verify`, `build-story`,
`validate`, `finish-and-push`, `triage`, `ideation`, `create-adr` and
`setup-methodology`, plus `evaluate-model` where already installed. Updated
[the setup runbook](runbooks/setup-methodology.md) to preserve these focused
boundary decisions on refresh, including sparse/no-code exceptions.

Ten installed leaves adapted. Replaced only the operational Haiku/Sonnet/Opus
staffing table and Opus coordinator mandate with current-runtime, task-risk
selection. Retained benchmark subjects, pinned judges, historical model evidence,
structural/semantic scoring, source-backed golden judgments, mismatch taxonomy,
privacy, paid-run limits and immutable artifact contracts. The owner evaluation
skill gets economical staffing/event collection and actual aggregate spend gates;
strategic-review staffing cannot change any frozen evaluation configuration.

Scope and authority remain with the main agent; plan gates, one Git owner,
proportional validation, aggregate budgets, deadlines, no-recursion and clean
verification stops remain intact. Existing delegation authorization covers the
same bounded ideation/ADR worker; user opt-outs and tool restrictions prevail.

## Validation

- `make skills-check` — passed, 40 canonical skills; compatibility links valid and command aliases optional.
- `git diff --check` — passed, including final receipt/changelog inspection.
- Affected local links and added whitespace — passed. Reviewed scope contains
  only installed policy leaves, AGENTS, setup runbook, receipt and required
  changelog. Compatibility checks pass; generated planning records unchanged.
- No product suite or provider call: this patch changes policy prose only.
- No compiler generation: authored story/state/ADR/eval metadata is unchanged.
- No changes to product/model configuration, fixtures, goldens, scores or data.
- No staging, commit, push or primary-checkout edit by this adaptation worker.

Policy scenario inspection preserves unavailable-configuration disclosure,
already-configured main-agent review, failed/late-result handling, timeout versus
completion distinctions, clean-verifier termination, frozen eval subjects/judges,
existing delegation authorization and explicit triage lane coverage. Reused the
source Alignment 055 mailbox-wake evidence; no live message/provider test or
cost-saving measurement was needed or claimed for these prose changes.

## Verified policy landing

Cam's 2026-10-06 approval covered this scoped commit and push. After the global
Conductor/11-owner preflight cleared, policy commit
`1005e514e68552793f026f6d8faa1b35311b2258` was pushed to
`origin/codex/align-055-cine-forge` and fast-forwarded onto `origin/main`.
`git ls-remote origin refs/heads/main` verified that exact policy SHA after
landing. The primary checkout and its unrelated work were preserved.

This section records the observed policy landing. Its subsequent receipt-only
commit is recorded with final remote-main proof in Conductor Alignment 055's
consolidated owner ledger. Policy validation is reused because the checked leaf,
AGENTS and workflow inputs are unchanged; the receipt update receives scoped
content review and `git diff --check`. No product rerun is required.

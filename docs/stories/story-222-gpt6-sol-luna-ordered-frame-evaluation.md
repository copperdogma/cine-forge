---
id: "222"
title: "GPT-6 Sol and Luna Ordered-Frame Evaluation"
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
  - "208"
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

# Story 222 — GPT-6 Sol and Luna Ordered-Frame Evaluation

## Decision contract

Conductor Scout 076 item 3 and Cam's `yes` authorize direct OpenAI Responses `gpt-6-sol` and `gpt-6-luna`, each at low reasoning, on only the six active `video-understanding` v3 source-backed synthetic cases. Each case supplies five ordered JPEGs, neutral timing and opaque ID. No native video, audio, private material, ScriptBible, QA, or runtime default change is in scope. Fresh direct `gemini-3.5-flash-lite` is the same-input reference if a subject clears progressive gates; it is not an adopted passing incumbent. The maintained `claude-opus-4-6` rubric judge is explicit and frozen.

The subject contract is direct foreground Responses Standard, `store:false`, exact model identity, terminal complete output, provider strict JSON Schema, five image parts, 1,400 maximum output tokens, no cache reuse and concurrency one. First case precedes six. One subject's stop does not cancel the other. Target overall is at least 0.80, subject latency at most 15 seconds and subject cost at most USD0.02 per call. The all-provider ceiling is USD1.50. No automatic retry, reasoning/output sweep, or cap transfer. Incomplete output is transport evidence.

Only repository-owned synthetic pixels, target text, prompt and rubric may leave the machine. Current direct Standard data posture was disclosed by Scout 076; `store:false` does not prove ZDR. The owner wrapper loads existing owner OpenAI, Google and Anthropic variables by presence only; no central key injection is needed.

Before each paid request reserve the complete next-request maximum conservatively, including image input and output, and account uncertain billing at its reservation. Current USD/M standard rates: Sol input/cache read/cache write/output 2/0.2/2.5/10; Luna 0.1/0.01/0.125/0.5; Gemini 3.5 Flash-Lite input/output 0.30/2.50; Opus 4.6 judge 5/25. Reserve 20,000 subject input tokens (five images plus prompt, over four times the prior direct Anthropic case) and 1,400 output tokens: Sol USD0.064 with cache-write upper rate, Luna USD0.0032. Judge reserve 10,000 input and 1,024 output = USD0.0756. Google reference retains owner output setting of 65,536, so its full-request reserve is USD0.16984 at 20,000 input tokens. Release unused reservation only after terminal usage establishes cost. Stop if the next full reserve does not fit the remaining ceiling.

## Plan and work log

1. Validate active v3 source hashes, prompt, target/scorer and exact six-case matrix at zero cost. Resolve explicit provider and judge selection, case sessions, prompt bytes, cache policy, concurrency and output paths.
2. Check exact direct model access. Qualify one native five-image strict response per candidate. Preserve full safe raw envelopes before parsing. Run owner harness parity on the same first case only if the native gate admits it.
3. Score first cases with frozen structural and Opus 4.6 rubric. Advance each subject to six only when its first case clears contract, quality and value gates. Run fresh Gemini controls only when admitted and fundable. Keep every stop and unmeasured layer explicit.
4. Write a numbered attempt, registry history, hashes, spend ledger, validation and no-default-change verdict.

20260926-preflight — Isolated worktree `codex/gpt6-sol-luna-eval-20260926` from `origin/main` `163bcb1ecd36de97b76e5ad83298048c9211a4d7`; primary checkout remains untouched. Owner wrapper presence checks found OpenAI, Anthropic and Gemini variables. The dataset, scorer and benchmark unit checks passed. The repaired registry declares exactly six active frame cases; older quarantined rows do not enter this run.

20260926-first-case — [Attempt 041](../evals/attempts/041-gpt6-sol-luna-video-understanding-first-case-stop.md) and its [evidence manifest](../evals/story-222-gpt6-sol-luna-video-evidence.json) record both exact direct native five-image strict responses, raw usage and safe raw pointers. Sol's one owner Promptfoo parity plus frozen Opus 4.6 judge scored 0.39415 combined and stopped before six; Luna's native structural 0.5983 makes 0.80 impossible even with a perfect rubric, so it stopped before a duplicate subject call. Sol's parity scale/motion miss is source-grounded model-wrong; subjective tone and lexical `closer` deductions are ambiguous. Total accounted all-provider spend was USD0.035800575 of USD1.50, including an estimated USD0.023165 judge charge. No Gemini reference, default change, commit or push.

20260926-validation — Focused dataset, benchmark, scorer, adapter, report and contract-manifest tests passed 68/68; touched Python files passed Ruff and `git diff --check` passed. `make check-evals` passed registry, truth-ledger and new immutable v12 contract-manifest checks. `pnpm methodology:compile` regenerated the story, graph and build-map views. The attempt remains a bounded first-case stop with full-six capability and contemporary comparative advantage unmeasured. A source-verified target/scorer clarification is the next useful work before another paid comparison.

20260926-continuation — The updated Conductor evaluate-model route and Cam's continued approval called for recovering the soft first-case scorer artifact and completing the remaining decision-bearing owner comparison within the same USD1.50 cap. [Attempt 042](../evals/attempts/042-gpt6-luna-repaired-six-case-comparison.md) and its [v2 evidence manifest](../evals/story-222-gpt6-sol-luna-video-evidence-v2.json) preserve the original Attempt 041 scores, independently regrade saved output for source-backed temporal enlargement, add Luna first owner parity and matched fresh Gemini first control, then run both on all six active source-backed five-JPEG cases with the frozen Opus 4.6 rubric. The historical maintained full-six result is Luna 0.5299 versus fresh Gemini 0.4188 overall; Luna wins five of six and costs about 5.7 times less per subject, but both pass zero of six at the 0.80 gate. The rooftop target wrongly demands growth for a same-size figure; a saved-output, no-provider-call sensitivity excluding that case is Luna 0.52432 versus Gemini 0.42334, four of five Luna wins, and zero of five passing. Luna has a clear prop-continuity classification error, while bedside and rooftop target/judge deductions need targeted truth review. Sol remains stopped on its first owner case's grounded scale miss. Campaign accounted spend is USD0.390639095 / 1.50, including estimated judge charges. No default change, commit or push. Recommendation: retain the runtime route, use Luna as the preferred research/reference challenger, and repair source/target/rubric ambiguity before any promotion decision.

20260926-truth-v4 — [Attempt 043](../evals/attempts/043-video-understanding-source-truth-v4-headless-qualification.md) freezes source-reviewed references before scoring. The same twelve saved full-six subject outputs and original JPEG hashes were reused; no subject was called again. The maintained task now points to a v4 target overlay: rooftop removes a false growth/acceleration claim, bedside describes observable geometry without requiring one object identity, and dialogue scores visible body enlargement while excluding ambiguous camera mechanism from the deterministic aggregate. Three untouched references are byte-identical to v3. The symmetric derived regrade applies the v4 deterministic scorer to all six cases per arm, uses six bounded Opus 4.6 judge-only calls for the three changed references, and retains original judgments for three unchanged references. Luna leads fresh matched Gemini 0.5986 to 0.4313 and wins all six paired cases, but both pass 0/6 at the 0.80 autonomous-QA gate. The revised judge still penalizes some plausible bedside readings and interpretive tone; neither score is fully truth-clean. Campaign accounted spend is USD0.531629095 / 1.50, with USD0.140990 estimated incremental judge cost. Source review found no ordered-frame product inference call to swap: Story 030's maintained path is the headless Promptfoo task. Luna is the preferred model for inspected headless ordered-frame reference runs; no autonomous QA/default adoption or production integration is claimed. No commit or push.

20260926-postrun-cleanup — The exact paid-call builder and judge scripts were copied into hash-checked snapshots before mechanical Ruff cleanup of the active scripts. [Post-run provenance](../evals/story-222-truth-v4-postrun-provenance.json) preserves separate call-time and active hashes; the original freeze/evidence and all receipts remain untouched. Archive-aware verification and offline regrade reproduce the same derived result. The current contract manifest advances to v15. No provider call, default change, commit or push.

20260926-landing-selection — Cam separately authorized scoped commit and remote-main landing of this completed benchmark and model-selection record. The candidate includes Attempts 041–043, original and repaired results, v4 source references, focused transport/scoring code and tests, exact call-time snapshots, contract/evidence manifests, registry/policy updates, this Done story, one CalVer changelog entry and generated planning views. The primary checkout's unrelated dirty work and ignored raw receipts remain outside the commit. The previously recorded 73 focused tests, Ruff, overlay/freeze checks, byte-identical offline regrade and owner `check-evals` still apply to the unchanged code and evidence inputs; landing will verify remote commit ancestry. This note records selection for landing, not a claim that remote main has already advanced.

# Runbook: Evaluate Model

> Run a fair, production-relevant CineForge model evaluation from an informal
> request through a scoped adoption recommendation.

## Context

Use `/evaluate-model <natural-language brief>` when one or more new or existing
models need fresh model-slot evidence. The command is self-contained: the user
does not need to separately invoke discovery, story creation, Promptfoo,
eval-improvement, or registry bookkeeping.

Use `/create-eval` instead when the missing thing is a new capability measure,
not a new subject model. Use `/improve-eval` directly when the explicit goal is
to repair a prompt, scorer, rubric, or golden rather than compare models.

## Prerequisites

- a current CineForge checkout with `AGENTS.md`, methodology state, and registry
- the selected benchmark task, prompt, scorer, rubric, and golden
- an explicitly resolved benchmark workspace; it may be this checkout or a
  separate CineForge sidequest worktree
- a usable CineForge Python environment and Node.js 24
- provider credentials loadable through
  `scripts/with_cine_forge_provider_env.py`
- public, synthetic, or otherwise approved fixtures
- an owning story and predeclared decision contract for execution

## Steps

1. `[judgment]` Interpret the whole brief.
   - Resolve candidates, target slots/tasks, explicit settings, budget, privacy,
     audit versus execution intent, and force-fresh intent.
   - Honor the latest clear correction in a long brief.
   - If the user omitted scope, choose the smallest maintained surface set that
     can change a real runtime/default decision.
   - A normal execute/test/compare request authorizes the bounded workflow under
     `/evaluate-model`; ask only when the skill's authority boundary is crossed.

2. `[judgment]` Read repo truth before planning.
   - Read the Ideal, methodology state/graph, current spec phase, relevant ADRs,
     registry rows, prior attempts, and recent model-refresh stories.
   - Resolve the actual runtime default from module manifests/code.
   - Resolve the best eligible maintained evidence after freshness, fixture,
     transport, and target checks. Do not equate the runtime default, highest raw
     score, and best eligible evidence unless the repo proves they are the same.
   - Read each selected eval's dynamic target; do not reuse old thresholds from
     a prior story.

3. `[script]` Resolve the benchmark workspace.

```bash
git worktree list
```

   - Prefer the current checkout when it contains the selected
     `benchmarks/tasks/` file.
   - Otherwise locate the documented CineForge sidequest worktree and verify
     that config, prompt, scorer, golden, and result paths resolve within the
     intended code state.
   - Do not use a remembered absolute path without verifying it.

4. `[judgment]` Create or reuse one coherent owning story.
   - Write exact candidates, slots, comparators, dynamic gates, fixture scope,
     configuration arms, cache/concurrency, retry limits, stop rules, privacy,
     and total spend cap.
   - Default the all-provider ledger to US$5 when the user and repo supply no
     tighter limit.
   - For several candidates, use the same maintained references per slot and a
     progressive screen rather than a pairwise/full-matrix tournament.

5. `[judgment]` Refresh current external truth.
   - Check current first-party model, API, structured-output, reasoning,
     pricing, rate-limit, retention/training, and ZDR documentation.
   - Run CineForge discovery as catalog evidence, not callability proof.
   - Map launch names to exact slugs and record expected served identities.

6. `[script]` Qualify access and transport through the CineForge env wrapper.
   - Load provider variables only through the wrapper belonging to the selected
     checkout.
   - Run access, native, production-contract, and harness-parity probes in that
     order for every materially distinct surface.
   - Require terminal success, expected served identity, complete output, sane
     usage/cost, and the production schema/modality before scoring.
   - Capture sanitized status, finish reason, identity, usage, latency, and
     errors. Never record credential values.

7. `[script]` Run the bounded Promptfoo arm from the resolved `benchmarks/`
   directory.

```bash
source ~/.nvm/nvm.sh
nvm use 24 > /dev/null 2>&1
CINEFORGE_ROOT=/absolute/path/to/the/selected/cine-forge-checkout
CINEFORGE_PYTHON=/absolute/path/to/a/cine-forge-python
PROMPTFOO_PYTHON="$CINEFORGE_PYTHON" \
  "$CINEFORGE_PYTHON" "$CINEFORGE_ROOT/scripts/with_cine_forge_provider_env.py" \
  promptfoo eval -c tasks/<eval>.yaml \
  --filter-providers '<candidate-filter>' \
  --no-cache --filter-first-n 1 -j 1 \
  --output results/<fresh-run-name>.json
```

   - Replace placeholders only after resolving real paths and exact provider
     labels.
   - Progress from smoke to differentiating slice to bounded maintained task.
   - Select on a predeclared calibration slice and freeze the arm before the
     decision run. If selection touched the decision fixtures, keep those
     scores exploratory and confirm on a predeclared held-out slice or with
     predeclared repeats.
   - Raise concurrency only after provider limits are verified; keep the repo
     maximum unless the task is an explicit throughput experiment.
   - Promptfoo exit code `100` means assertion failures. Inspect the result
     rather than calling it a harness crash.

8. `[judgment]` Protect scoring integrity.
   - Inspect the raw output and original source before classifying a mismatch.
   - Use both the maintained deterministic structural scorer and semantic
     rubric; report them separately.
   - Record judge-provider and capability bias. A same-provider judge must not
     be the sole basis for a marginal decision-changing conclusion; use a
     predeclared capable cross-provider or symmetric second judge on frozen
     outputs when necessary.
   - Do not judge-shop after seeing scores.
   - `qa-pass` and `video-understanding` are quarantined while Story 208/registry
     contamination notes remain current. Repair and revalidate their truth
     surfaces or report the relevant slot as not measured.

9. `[judgment]` Classify and debug failures.
   - Locate the producing stage: provider/router, subject request, adapter,
     parser, cleanup, structural scorer, rubric judge, or golden.
   - Report `model-wrong`, `golden-wrong`, or `ambiguous`, plus
     runtime-blocking/non-runtime-blocking when applicable.
   - Treat capacity, auth, quota, rate-limit, API-shape, missing schema flags,
     truncation, and native-versus-harness divergence as operational evidence
     until fixed or proven otherwise.
   - Change one causal variable at a time and stay inside the declared retry and
     spend caps.

10. `[script]` Extract and record metrics.

```bash
"$CINEFORGE_PYTHON" "$CINEFORGE_ROOT/scripts/extract-eval-metrics.py" \
  --result-file <absolute-resolved-result-path>
```

   - Record quality, latency, cost, retries, cache, concurrency, exact requested
     and served IDs, source/document dates, commands, tool versions, and ledger.
   - For dirty runs, preserve base SHA plus hashes/patches for every changed
     eval/provider file and ignored raw artifact. A base SHA alone is not exact
     provenance.
   - Update registry, attempt/story evidence, and methodology surfaces even for
     failed or inconclusive authorized evals.

11. `[judgment]` Decide independently per slot.
   - Compare candidate evidence with both the actual runtime default and best
     eligible maintained result under current gates.
   - Report unrun or quarantined slots as not measured; a progressive stop is
     not a semantic failure.
   - End with adopt, conditional adopt, do not adopt, or defer for each exact
     slot. Never change a default without explicit authorization.

## Boundaries

### Always do

- use current first-party docs plus live exact-identity evidence for execution
- use the CineForge provider-env wrapper and resolve the benchmark workspace
- predeclare spend, arms, retries, cache, concurrency, and comparators
- use strict provider-enforced output schemas when the production contract
  requires them and the provider supports them
- inspect raw artifacts and source-backed goldens
- keep each model slot's progression and verdict independent
- preserve exact provenance and update the registry after any real eval

### Ask first

- private fixtures on a provider path not already approved
- total provider spend above the declared/default cap
- new dependencies, architecture, or a second benchmark system
- changing production defaults, goldens, scorer meaning, or product behavior
- workspace or credential ownership cannot be resolved safely

### Never do

- print, copy, or commit provider keys
- treat catalog visibility or HTTP 200 as proof of a valid evaluated response
- score prompt-only JSON when strict schema is a production requirement
- blame model quality for provider, adapter, parser, scorer, judge, or golden
  failure
- use quarantined QA/video raw scores for adoption or compromise decisions
- overwrite prior evidence during force-fresh work
- commit, push, deploy, or change defaults implicitly

## Troubleshooting

- **Model is listed but the call fails:** classify auth/tier/region/quota before
  capability; catalog evidence is not access evidence.
- **Native call works, Promptfoo fails:** inspect API family, adapter shape,
  env-wrapper ownership, cache key, and served identity before changing prompts.
- **JSON is malformed:** verify strict-schema flags, finish reason, visible plus
  reasoning token budget, and raw output before blaming compliance.
- **A model looks unusually weak:** verify prompt parity, exact served model,
  fixture health, structural/rubric components, and judge bias.
- **A candidate beats the default:** check the best eligible maintained result,
  repeats, all current gates, and whether the evidence covers that exact slot.
- **A later slot did not run:** report not measured and the stop condition; do
  not infer failure.

## Lessons Learned

- 2026-07-22 — The doc-web pilot showed that production-enforced structured
  output, served identity, force-fresh semantics, bounded retries/spend, and
  source inspection must be first-class workflow gates rather than afterthoughts.
- 2026-07-22 — CineForge's own recent refreshes showed that contaminated QA and
  symbolic-video truth surfaces can invert conclusions. Quarantine them until
  repaired instead of accumulating more misleading model rows.

---
name: evaluate-model
description: Evaluate one or more AI models end to end for CineForge. Use for natural-language requests ranging from a broad new-model evaluation to a narrow task or model-slot comparison, including long or self-correcting briefs, multiple candidates, audit-only review, or a force-fresh rerun. Resolve current access and model identity, choose maintained decision-bearing surfaces, qualify provider and structured-output transport, run a fair bounded comparison, debug invalid attempts, preserve exact evidence, and give scoped adoption recommendations without changing defaults from launch claims or bad harness output.
user-invocable: true
---

# /evaluate-model [natural-language evaluation brief]

> Alignment check: Read `docs/ideal.md`,
> `docs/methodology-ideal-spec-compromise.md`, `docs/methodology/state.yaml`,
> `docs/methodology/graph.json`, generated dashboards, and relevant records in
> `docs/decisions/` / `docs/design/` before choosing a lane. Respect the current
> phase and detector for any `docs/spec.md` compromise. If none apply, state
> that explicitly.

Evaluate the requested candidates through production-relevant call shapes. Do
not merely replace a model name, run Promptfoo once, and treat every red cell as
model-quality evidence.

## Invocation and Authority

Treat everything after `/evaluate-model` as an evaluation brief, not positional
arguments. A model name alone is enough. The brief may be informal, rambling,
narrow, contain multiple models, or provide exact settings. Extract and retain:

- candidate names, families, exact slugs, providers, and access paths
- task, runtime stage, model slot, eval ID, fixture slice, or adoption question
- incumbent or requested head-to-head comparison
- reasoning/thinking, schema, tool, sampling, modality, and output constraints
- cost, latency, privacy, safety, repeats, concurrency, or deadline limits
- execute/test/compare intent versus plan/design/read-only intent
- reuse, audit, force-fresh, reproduce, or variance intent
- exclusions and later corrections; the latest clear instruction wins

Resolve routine omissions from current official documentation, authenticated
access evidence, runtime configuration, and repo truth. Do not require a second
command for discovery, story creation, eval triage, mismatch investigation, or
recording. State consequential interpretations before spending.

Unless explicitly limited to planning or audit, an evaluate/run/test/compare
request authorizes the smallest bounded execution under this skill's limits,
using configured CineForge credentials and eligible fixtures. It also
authorizes the normal story, provider-lane, result, attempt, registry, and
methodology updates needed to make that evaluation valid and durable. The
request itself satisfies the plan gate for this standard bounded workflow once
the plan is written in the owning story. Ask again only for a material scope
expansion, new dependency or architecture, private payload not already
approved, a higher spend cap, or a product/default decision reserved for the
user. Evaluation never implicitly authorizes a default change, commit, push,
deployment, credential copying, or rollout.

A plan/design/read-only request makes no provider calls, runs no harness,
creates no artifacts, and mutates no repo surface. Use the execution sections
as an audit checklist and report gaps.

Treat requests to rerun from scratch, reproduce, measure variance, or exercise
the workflow fresh as **force-fresh** even without that label. Force-fresh only
bypasses duplicate avoidance: preserve prior evidence, use new result/attempt
identities, bypass subject caches, and retain all privacy, spend, fairness,
retry, truth, and default-change controls. A fresh adoption comparison reruns
the relevant candidate and incumbent on frozen inputs. Candidate-only
transport or variance reproduction cannot support a contemporaneous
superiority claim.

When force-fresh leaves the comparison shape unstated, infer it from the
verification objective. A workflow-acceptance or fresh adoption request reruns
the candidate and relevant incumbent on the same frozen inputs. A candidate
variance or transport-reproduction request may remain candidate-only, with no
current superiority claim.

If neither the brief nor a stricter repo contract supplies a total provider
budget, cap all paid calls for the invocation at **US$5**. This includes access
and contract probes, subjects, incumbents, retries, and judges. Start a ledger
before the first paid call and update it after every stage. Stop and ask before
spending if the smallest valid decision-bearing run may exceed the cap or
pricing cannot be bounded conservatively.

When the brief is broad, select the smallest portfolio of materially distinct
maintained model slots that can change a current CineForge decision. When it is
narrow, honor that surface and verify that it is decision-bearing. For several
candidates, qualify each independently and compare each with the same
maintained references per slot; do not create pairwise tournaments. Screen
progressively so candidate count does not multiply the full matrix.

## Non-Negotiable Rule

Do not call a model bad when access, capacity, provider transport, adapter,
prompt contract, output schema, parser, cleanup, scorer, judge, or golden failed
before valid subject evidence existed. Preserve operational failures and keep
them separate from semantic capability.

## 1. Resolve the Decision and Evidence Owner

1. Resolve colloquial launch names to exact API identities only when the mapping
   is unambiguous. Never silently substitute another model, tier, or snapshot.
2. Inspect `docs/evals/registry.yaml`, prior attempts and model-refresh stories,
   current methodology state, runtime manifests/code, and live model-slot
   configuration.
3. Check whether current source-backed evidence already answers the same
   candidate/configuration/slot question. Reuse it unless force-fresh applies
   or a model, provider, prompt, scorer, golden, runtime, or decision fact
   materially changed.
4. Rank maintained lanes by decision leverage, relevant capability coverage,
   evidence gap, and cost. Do not run every historical eval by default.
5. For execution, create or reuse the minimum coherent owning story and write
   its decision contract before provider spend or eval mutation. Candidates on
   one decision surface share ownership; do not create a story per model.

Read before changing or spending:

- `AGENTS.md`, the alignment sources named above, and relevant spec/ADRs
- `docs/evals/README.md`, registry entries, attempts, and recent refresh stories
- the selected task, prompt, structural scorer, rubric, golden, provider path,
  raw results, and `docs/runbooks/promptfoo.md`
- repo-local discovery, create-story, create-eval, and improve-eval skills

The decision contract must record:

- exact candidates/providers and requested configuration arms
- named runtime stage/model slot and eval IDs for each selected surface
- current runtime default from executable config, not memory
- best **eligible** maintained evidence after freshness, contract, fixture, and
  target checks; this may differ from the runtime default or highest raw score
- maintained prompt, fixtures, structural scorer, rubric/judge, golden, SHA,
  and dynamic target from the current registry
- quality, latency, cost, reliability, privacy, and safety gates
- freshness objective, reusable evidence, stop conditions, and later gates

Judge each slot independently. Failure on one slot must not block an unrelated
slot; success on one slot must not generalize to another. A candidate that
beats the runtime default but not the best eligible evidence is a maintenance
signal, not automatically an adoption win. If no maintained lane can change a
decision, return an evidence-backed no-eval/defer result.

## 2. Refresh External and Local Truth

For execution, consult current first-party provider documentation and produce
live owner-run evidence. Announcement copy, router catalogs, aliases, and model
memory do not prove reproducible access.

Build a dated call-contract sheet per candidate and selected surface:

- exact model slug, tier/snapshot mapping, region, and access path
- native endpoint/API family and current SDK/Promptfoo/custom-provider support
- served-model/provider metadata and router fallback policy
- required text/image/video/file/tool input shape and supported roles
- strict JSON Schema or structured-output support and required flags
- reasoning/thinking controls, allowed values, and output-token interaction
- rejected sampling, stop, seed, penalty, and tool parameters
- current pricing, rate/concurrency limits, and availability guidance
- retention, training, ZDR, and payload eligibility

Run `<cineforge-python> <repo-root>/scripts/discover-models.py --check-new` with
the checkout and interpreter resolved in Section 3. Treat it as catalog
evidence, never as callability proof. Verify exact access with the owning
provider or approved router. A marketing name and served API ID may differ;
record the mapping and do not claim the requested model was tested without
served-identity evidence.

## 3. Resolve the Benchmark Workspace and Credentials

Never assume one absolute benchmark path. First use the current checkout if it
contains the selected `benchmarks/tasks/` files. Otherwise inspect current git
worktrees and resolve the documented CineForge sidequest workspace. Verify the
selected config, prompt, scorer, golden, and result directory all belong to the
same intended code state. Stop if the workspace cannot be resolved safely.

Load credentials only through that checkout's
`scripts/with_cine_forge_provider_env.py`; do not source, print, copy, or commit
keys. Resolve an available CineForge Python environment explicitly. Start with
public, synthetic, or approved fixtures. `store: false` is not privacy or ZDR
proof. Keep private raw data in protected/ignored storage; track only safe
hashes, summaries, or pointers.

## 4. Qualify Transport Before Scoring

Advance per candidate and materially distinct surface, preserving sanitized
request/response, status, latency, usage, finish reason, served identity, and
errors:

1. **Access probe** — exact model authorized and callable.
2. **Native probe** — smallest direct provider call outside Promptfoo when
   practical; confirm actual served identity.
3. **Contract probe** — exercise the production modality, tool, long-context,
   or strict structured-output requirement.
4. **Harness-parity probe** — send the same small case through the selected
   CineForge provider/task and compare with native behavior.

Qualify each distinct output schema independently. HTTP 200 is insufficient:
require terminal success, no provider error/incomplete state, expected served
model, complete output, and sane usage/cost. Fail closed on unknown response
shapes, missing identity, malformed usage, truncated content, wrong schema, or
undocumented fallback. Promptfoo omissions remain `unverified`, not invented.

When structured output is required, use provider-enforced strict schema when
supported. Prompt-only JSON is not equivalent. If only a weaker documented
mode exists, label it; if strict output is mandatory, classify incompatibility
rather than a semantic miss. Ensure output budget covers reasoning plus the
visible schema. Inspect the actual native request and raw response—a passing
unit parser or fenced JSON cleanup does not prove contract parity.

Repair a narrow provider/harness defect only after native evidence isolates it.
Test the repair and rerun parity before scoring. A semantic prompt change,
reasoning change, or output-budget change is a declared configuration arm, not
invisible transport repair.

## 5. Predeclare a Fair Matrix

Before viewing scores, record:

- candidate arms and provider-valid recommended settings
- the current runtime default and best eligible comparator per slot
- whether fresh comparators are required for the claim
- at most two justified diagnostic/configuration arms beyond recommended
  candidate settings across the evaluation, unless the user approves more
- aggregate spend cap, stop rules, fixture slice, repeats, and retry cap
- frozen semantic prompt, fixtures, structural scorer, rubric, golden, and
  downstream cleanup
- cache and concurrency policy; use no-cache for changed/force-fresh subjects

Give candidates comparable opportunity using valid provider controls; do not
force identical invalid parameters or tune only the loser. Use a predeclared
calibration slice, then freeze one configuration before decision evidence. If
configuration selection used the decision fixtures, every observed score on
those fixtures remains exploratory: confirm the frozen arm on a predeclared
held-out slice or with predeclared repeated evidence before making a promotion
claim. Start at `-j 1`; raise concurrency only after limits are verified and
never above the repo norm without a separate throughput experiment.

## 6. Protect Scoring and Golden Truth

Use the selected eval's maintained **structural scorer and semantic rubric**.
Neither alone is sufficient. Keep them fixed during model comparison and
attribute their scores separately before computing or quoting an aggregate.

The maintained rubric judge may share a provider with a subject or be weaker
than a frontier subject. Record that bias risk. A same-provider judge must not
be the sole evidence for a marginal decision-changing win or loss. For such a
case, use a predeclared capable cross-provider judge or symmetric second judge
on the frozen outputs, disclose disagreement, and leave ambiguous cases out of
promotion evidence. Do not judge-shop after seeing a score.

Treat source-backed goldens as truth surfaces, not knobs. Inspect original
screenplay/media before changing one. Use `/improve-eval` internally for
model-wrong, golden-wrong, scorer-wrong, or ambiguous diagnosis, while retaining
CineForge's canonical reported taxonomy: **model-wrong**, **golden-wrong**, or
**ambiguous**. Record runtime-blocking versus non-runtime-blocking when relevant.

The registry and Story 208 currently record material contamination in
`qa-pass` and `video-understanding`. Until a source-backed repair and clean
verification supersede those notes, quarantine their raw scores: do not use
them to adopt/reject a model, change a default, or advance C2/C3/C5. Repair them
through the eval-improvement workflow, or report those slots as not measured.
Do not silently replace them with an improvised fixture.

## 7. Run Progressively and Inspect Artifacts

Use the smallest stage that answers the next question:

1. public/synthetic native and parity smoke
2. one representative Promptfoo case
3. known differentiating or failing slice
4. bounded maintained task with frozen configuration
5. independent next slot/repeats only after its own entry condition passes

Run Promptfoo from the resolved `benchmarks/` directory, through the CineForge
env wrapper, with explicit filtered providers, output path, `--no-cache` where
required, and initially `-j 1`. Exit code `100` means assertion failures, not a
harness crash; inspect raw results before classifying it.

After every stage, inspect subject output, structural details, rubric evidence,
usage, cost, and source artifacts. Stop weak or incompatible arms before an
expensive later gate, but retain every attempt. If an entry condition prevents
a distinct slot from running, report that slot as **not measured** and adoption
as **not advanced/deferred under the declared ladder**. Do not convert a valid
progressive stop into a semantic failure on an unrun capability.

## 8. Classify and Debug Failures

Identify the producing stage first: provider/router, subject request, adapter,
parser, cleanup, structural scorer, rubric judge, or golden.

| Failure | Required response |
| --- | --- |
| capacity, timeout, `5xx`, or capacity-coded `429` | Follow provider guidance and retry within the cap. Keep reliability/latency/cost separate from conditional semantic quality. |
| auth, quota, plan, region, tier, or policy | Correct only within existing authority; otherwise mark access constrained/blocked and capability not measured. |
| client rate/concurrency `429` | Inspect body/headers and reduce concurrency; do not blame model quality. |
| wrong endpoint, modality shape, or unsupported parameter | Recheck current docs, change one contract variable, rerun native then parity. |
| schema not enforced | Enable documented strict output and verify the native request before scoring. |
| truncation or thinking-token exhaustion | Inspect finish/usage, declare the corrected arm, and rerun only the affected slice. |
| native succeeds but harness fails | Treat as adapter/cache/harness incompatibility until disproved. |
| scorer, rubric, judge, cleanup, or golden mismatch | Isolate it on frozen output and run eval-improvement classification. |
| valid output contradicts source-backed expectation | Count as model-quality evidence after contract validity is proven. |
| refusal/filter | Report separately as policy/safety compatibility. |

Change one causal variable at a time. Report both conditional semantic quality
on valid responses and end-to-end production reliability including failures,
retries, latency, and cost. Never erase initial failures by quoting only a
successful retry.

## 9. Record Exact Evidence and Decide

Before recommending adoption:

- compare against both the actual runtime default and best eligible evidence
- apply the current registry's per-slot quality, latency, cost, reliability,
  privacy, and safety gates rather than hard-coded historical thresholds
- reject empty, partial, stale, wrongly attributed, or quarantined bundles
- record sanitized commands, docs/date, requested and served model IDs,
  parameters, fixtures, repeats, cache, concurrency, versions, and cost ledger
- for a clean run, record exact SHA; for a dirty run, record base SHA plus
  hashes/patches of every relevant changed file and ignored raw artifact
- when raw results are ignored, track a compact manifest with hashes, safe
  aggregates, and regeneration commands
- update `docs/evals/registry.yaml` for every authorized eval, including failed
  or inconclusive runs, with explicit story/category/compromise lineage
- add a numbered attempt when the non-trivial result warrants one, update the
  owning story, and regenerate methodology surfaces

Do not change a default because a model is new, faster, cheaper, or highest on
one raw aggregate. Adoption requires decision-grade evidence for the exact
slot. A default change remains a separate explicit user decision unless the
brief specifically authorized it after defining the gate.

## Required Output

Return a compact record with one row per `(slot/surface, candidate, frozen
configuration)` where useful:

1. interpreted brief and material assumptions
2. owner/story, selected slots/evals, runtime defaults, best eligible evidence,
   and why these lanes outranked alternatives
3. current official evidence, exact identities/access paths, and freshness mode
4. configuration/fairness matrix, cache/concurrency, and spend ledger
5. access per candidate: available, constrained, blocked, or unverified
6. transport per candidate/surface: qualified, blocked, or inconclusive
7. reliability: acceptable, degraded, failed, or not measured
8. capability: better, equivalent, worse, or not measured, with conditional
   semantic quality separated from end-to-end production results
9. structural score, rubric score, judge/bias treatment, latency, and cost
10. mismatch classification and source evidence
11. adoption per slot: adopt, conditional adopt, do not adopt, or defer
12. exact artifacts/registry/story/provenance and unmeasured limits

An access or transport block normally yields `capability: not measured` and
`adoption: defer`. Missing a mandatory production feature can make a candidate
ineligible. A valid source-backed semantic loss can support `do not adopt`.
State which happened.

## Guardrails

- Never score pre-response infrastructure failure as a semantic miss.
- Never weaken a required prompt, modality, schema, tool, or safety contract to
  make a candidate pass.
- Never tune a golden, scorer, or judge to rescue a model.
- Never send private fixtures through an unapproved provider path.
- Never borrow another repo's credentials or expose credential values.
- Never use quarantined QA/video evidence for adoption until repaired.
- Never overwrite prior force-fresh artifacts.
- Never commit, push, deploy, change defaults, or broaden rollout implicitly.

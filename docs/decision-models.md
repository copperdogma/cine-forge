# Decision models in CineForge

Decision models make bounded semantic judgments over context that code supplies.
They return typed answers from developer-defined choices or rubrics; code can
then combine those answers with deterministic rules. This can help where exact
string heuristics are brittle and a full language-model response is unnecessary.
It does not establish that a judgment is true, preserve source evidence, or
replace CineForge's creative roles and generation models.

## Choose the right boundary

When changing a semantic decision, compare three approaches and record why the
selected one fits:

- **Deterministic code** for exact rules, arithmetic, identity, permissions,
  provenance, state changes, and execution.
- **Decision model** for a small, defined semantic judgment over supplied
  context, where an answer can be selected from known outcomes.
- **Language model** for open-ended interpretation, explanation, proposals,
  creative reasoning, or generated artifacts.

The three can work together: a decision model can suggest a candidate verdict;
code preserves evidence and gates; a language model can explain or develop the
result. Do not make model output authoritative by changing its JSON shape.

## Typed questions

- **Choice** selects one item from a finite set. Include `unknown` or `other`
  when the candidates may not cover the input.
- **Noul** answers one clearly defined yes/no question as a probability of yes.
  It has no separate confidence field; 0.5 means yes and no are equally likely,
  not a middle value on a scale.
- **Score** places a judgment on ordered, named rubric levels. Its result is a
  probability-weighted mean of the level positions and can be fractional. Code
  owns normalization and weights when combining separate scores.
- Split multi-part judgments into narrow questions. Combine score values,
  thresholds, and weights in code where their effect can be inspected.

## Evidence and uncertainty

Supply only the context needed for each judgment, with source identifiers and
timestamps where available. Keep source excerpts, hashes, and provenance in the
owning artifact; a verdict is an interpretation of evidence, not a replacement
for it. Record which candidates were considered, how they were selected, and
whether the candidate set may be incomplete.

Provide an explicit no-match or unknown outcome. Check that candidate selection
has not silently omitted the correct entity. Reject or re-evaluate stale context
when its source artifact, script version, or upstream evidence has changed.
When the model fails, times out, returns an invalid answer, or falls below an
appropriate threshold, use an explicit review, retry, or established fallback
path. Never convert missing evidence or service failure into a confident
negative verdict.

Choice and Score distributions describe how probability is spread over the
configured answers. Concentration is not correctness. Calibration is a
population-level property that must be measured on representative judgments;
thresholds should reflect the consequences of an error. Noul gives a yes
probability without a separate confidence value.

## Evaluation and operation

Compare the complete candidate workflow with CineForge's real current baseline
on representative screenplay and project data. Include candidate generation,
the decision call, evidence retention, review, and fallback. Measure judgment
quality and candidate coverage, plus end-to-end cost and latency; include
fallback work in those totals. Preserve the owning eval's acceptance criteria
and verdict. Do not substitute a small synthetic test or a model's confidence
for maintained project evidence.

Apply existing privacy and enablement gates before sending scripts, user assets,
or project artifacts to an external service. Minimize supplied data and verify
the provider's current retention, access, and modality terms for the intended
account before integration. This guide authorizes no runtime integration.

## CineForge fit

Candidate entity verdicts (for example, whether two discovered entities may
refer to the same character) are a possible bounded judgment. Keep quoted script
evidence, artifact lineage, human overrides, and final canon decisions in their
existing owner-controlled flow. Decision models do not replace entity evidence,
role reasoning, suggestion artifacts, or image/video/text generation. There is
no decision-model integration proposed by this guidance.

## Dated capability notes

Checked 2026-10-01. TypeSafe documents Jev as text-only and describes Choice,
Noul, Score, and confidence semantics in its [System One overview](https://docs.typesafe.ai/concepts/system-one),
[primitives reference](https://docs.typesafe.ai/primitives), [Score reference](https://docs.typesafe.ai/primitives/score), and
[confidence guide](https://docs.typesafe.ai/confidence). OpenAI's [DevDay 2026
recap](https://openai.com/index/devday-2026-recap/) dated 2026-09-29 announced
Decisions API using Luna with text or image context and limited-preview access,
with a broad release planned in the coming days. These announcements do not
verify account eligibility, API contracts, privacy terms, or pricing. Recheck
official provider documentation before any integration decision.

---
type: synthesis-prompt
topic: "ai-model-benchmarking-tools"
created: "2026-02-15T21:22:42.944338+00:00"
auto-generated: true
---

# Synthesis Prompt

You are acting as lead research editor. Your task is to read multiple independent research reports on the same topic, reconcile them, and produce one final, implementation-ready synthesis.

## Research Context

## Context

We have a production AI pipeline (CineForge) that uses LLM models for ~10 different tasks: script normalization, scene extraction, character/location/prop bible generation, entity graph extraction, continuity tracking, and more. Each task has different quality requirements — some need SOTA models regardless of cost, others can use cheap models. Today we guess which model to use. We want to replace guessing with data.

We need a tool that can:
1. Define benchmark tasks with specific prompts, inputs, and expected outputs
2. Run the same task across multiple models from multiple providers (OpenAI, Anthropic, Google, etc.)
3. Evaluate outputs using both code-based scoring (deterministic metrics) and AI-judge scoring (a strong model rates the output)
4. Track cost (tokens, latency, dollars) per model per task
5. Produce leaderboards and cost/quality comparison reports
6. Manage "golden datasets" — curated sets of inputs with known-good reference outputs

This is NOT about running standard LLM benchmarks (MMLU, HumanEval, etc.). We need **custom task evaluation** — our own prompts, our own inputs, our own scoring criteria.

## Research Questions

### 1. Existing Open-Source Tools
Find and evaluate ALL existing open-source tools, frameworks, and libraries for custom AI model benchmarking and evaluation. For each tool found, assess:

- **Name, repo URL, stars, last commit date, maintenance status**
- **Core capabilities**: What can it do? Multi-model? Multi-provider? Custom tasks?
- **Evaluation support**: Does it support custom scoring functions? AI-as-judge? Both code-based and AI-judge evaluation?
- **Cost tracking**: Does it track token usage, latency, and dollar cost?
- **Golden dataset management**: Can it store and version reference outputs?
- **Task definition format**: How are benchmark tasks defined? YAML? Python? JSON?
- **Provider support**: Which model providers are supported? Is it extensible to new providers?
- **CLI vs UI**: Does it have a CLI? A web dashboard? Both?
- **Reporting**: What does output look like? Leaderboards? Charts? JSON? Markdown?
- **Extensibility**: Can you add custom scoring functions, custom providers, plugins?
- **Python-friendly**: Is it Python-based or Python-friendly? Easy to integrate?
- **Community health**: Active development? Good docs? Responsive maintainers?

Key tools to investigate (but don't limit to these):
- **promptfoo** — prompt testing and evaluation framework
- **OpenAI Evals** — OpenAI's evaluation framework
- **Braintrust** — AI evaluation platform (has open source components?)
- **LangSmith / LangChain Evaluation** — evaluation features in LangChain ecosystem
- **Humanloop** — prompt management and evaluation
- **Ragas** — RAG evaluation framework
- **DeepEval** — LLM evaluation framework
- **Phoenix (Arize)** — observability and evaluation
- **Inspect AI** — UK AISI evaluation framework
- **Any others you find**

### 2. Gap Analysis
For the top 3–5 most promising tools, do a detailed gap analysis against our requirements:

| Requirement | Weight | Tool A | Tool B | Tool C |
|-------------|--------|--------|--------|--------|
| Multi-provider (OpenAI + Anthropic + Google minimum) | Must-have | ? | ? | ? |
| Custom task definitions (our prompts, our inputs) | Must-have | ? | ? | ? |
| Code-based scoring (custom Python functions) | Must-have | ? | ? | ? |
| AI-judge scoring (configurable judge model + rubric) | Must-have | ? | ? | ? |
| Cost tracking (tokens + dollars per model per task) | Must-have | ? | ? | ? |
| Golden dataset management | Should-have | ? | ? | ? |
| CLI interface | Should-have | ? | ? | ? |
| Cross-run comparison / leaderboards | Should-have | ? | ? | ? |
| Python-based or Python-friendly | Should-have | ? | ? | ? |
| Statistical rigor (multiple runs, confidence intervals) | Nice-to-have | ? | ? | ? |
| Extensible (plugins, custom providers) | Nice-to-have | ? | ? | ? |
| Lightweight / standalone (not a full platform) | Nice-to-have | ? | ? | ? |

### 3. Recommendation
Based on your analysis:
- **If a tool meets ≥80% of must-haves and ≥60% of should-haves**: Recommend adoption. Explain what gaps remain and how to work around them.
- **If no tool meets the bar**: Recommend building our own. Explain what the best tools got right that we should learn from, and what they got wrong that we should avoid.

### 4. Architecture Patterns (if building)
If recommending we build our own, briefly outline:
- What the architecture should look like
- Key design decisions to get right
- Pitfalls to avoid (learned from existing tools' limitations)
- Estimated complexity (is this a weekend project or a month-long effort?)

## Reports to Synthesize

You will receive 2 research reports, each produced by a different AI model. Each report covers the same research question from the instructions above.

## Your Synthesis Goals

1. Grade each source report on quality: evidence density, practical applicability, specificity, and internal consistency (0–5 scale for each, with a one-paragraph critique).
2. Extract key claims by topic area.
3. Identify where reports agree (high confidence) vs. disagree (needs adjudication).
4. Resolve contradictions with explicit reasoning — evaluate the strength of each report's evidence, not majority vote.
5. Separate "proven / high confidence" from "promising but uncertain."
6. Produce one concrete recommendation, not a menu of options.
7. If one report is clearly higher quality, weight it accordingly and say why.

## Required Output Format

Begin your response with:

---
canonical-model-name: "{the product name you are — e.g., chatgpt, claude, gemini, grok — lowercase, no version numbers}"
report-date: "{today's date in ISO 8601}"
research-topic: "ai-model-benchmarking-tools"
report-type: "synthesis"
---

Then produce the following sections:

1. **Executive Summary** (8–12 bullets)
2. **Source Quality Review** (table with scores + short commentary per report)
3. **Consolidated Findings by Topic**
4. **Conflict Resolution Ledger** (claim, conflicting views, final adjudication, confidence level)
5. **Decision Matrix** (if applicable — weighted, with scoring rationale)
6. **Final Recommendation** (concrete, with rationale)
7. **Implementation Plan / Next Steps** (if applicable)
8. **Open Questions & Confidence Statement**

## Quality Instructions

- Be concrete and specific, not generic.
- Clearly label assumptions and uncertainty.
- Prefer practical reliability over novelty.
- If evidence is weak across all reports, say so — do not manufacture false confidence.
- Do not simply merge or average — adjudicate.
- Note which report(s) contributed each key finding.

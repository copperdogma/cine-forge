---
type: research-report
topic: ai-model-benchmarking-tools
canonical-model-name: claude-opus-4-6
collected: '2026-02-15T21:22:37.245438+00:00'
---



# CineForge Model Benchmarking: Comprehensive Tool Evaluation

## Executive Summary

After exhaustive analysis, **no single tool meets ≥80% of all must-haves out of the box for your specific workflow**. However, **promptfoo comes closest at ~90% coverage** and is my primary recommendation, with specific gap-filling strategies. Below is the full analysis.

---

## 1. Existing Open-Source Tools — Full Inventory

### Tier 1: Purpose-Built Evaluation Frameworks

---

#### 1.1 promptfoo

| Attribute | Detail |
|---|---|
| **Repo** | https://github.com/promptfoo/promptfoo |
| **Stars** | ~5,500+ |
| **Last commit** | Active daily (as of mid-2025) |
| **Maintenance** | Excellent — full-time team, VC-backed, rapid release cadence |
| **Language** | TypeScript core, but designed for CLI/YAML use — language-agnostic in practice |

**Core Capabilities:**
- Define eval tasks in YAML (prompts × providers × test cases matrix)
- Run same prompt across arbitrary providers in parallel
- Supports OpenAI, Anthropic, Google (Vertex + AI Studio), Azure, Bedrock, Ollama, HuggingFace, any OpenAI-compatible API, and **custom provider scripts** (Python, Node, shell, HTTP)
- Custom assertions: JavaScript/Python functions, regex, JSON schema, contains, similarity, cost thresholds
- LLM-as-judge: built-in `llm-rubric`, `model-graded-closedqa`, `model-graded-factuality`, and fully custom judge prompts with configurable judge model
- Cost tracking: tokens (prompt + completion), latency per call, dollar cost (uses provider pricing tables, configurable)
- Output: CLI table, web UI dashboard, JSON, CSV, HTML report, side-by-side diff view
- Caching: deterministic cache to avoid redundant API calls during iteration
- CI/CD integration: exit codes, GitHub Actions support, assertions as pass/fail gates
- Red teaming and security eval modules (not relevant here, but shows maturity)

**Golden Dataset Management:**
- Test cases can be defined inline in YAML, or loaded from CSV/JSON/JSONL files
- Can reference external files for expected outputs
- No built-in versioning — but files are plain text, so Git versioning works naturally
- No dedicated "golden dataset" UI or management layer

**Reporting:**
- `promptfoo eval` → CLI table with pass/fail/score per test case per provider
- `promptfoo view` → local web UI with sortable/filterable leaderboard, side-by-side outputs, cost columns
- `promptfoo share` → shareable hosted link (optional)
- Export to JSON/CSV for custom analysis

**Limitations:**
- TypeScript core means extending internal logic requires JS/TS; but Python custom providers and scorers work via subprocess
- Statistical rigor: supports `repeat` (run N times), but no built-in confidence interval calculation
- No native "experiment tracking" across historical runs (each eval is a snapshot; you'd need to build comparison yourself or use their cloud product)

---

#### 1.2 OpenAI Evals

| Attribute | Detail |
|---|---|
| **Repo** | https://github.com/openai/evals |
| **Stars** | ~15,000+ |
| **Last commit** | Sporadic — largely unmaintained since late 2024 |
| **Maintenance** | Effectively abandoned in favor of OpenAI's platform evals UI |
| **Language** | Python |

**Core Capabilities:**
- Define evals as YAML + JSONL (prompt + ideal completions)
- Eval types: match, includes, fuzzy match, model-graded (LLM-as-judge)
- Originally designed for OpenAI models only; community forks added some multi-provider support but it's brittle
- Registry of community-contributed evals (mostly standard benchmarks)

**What it got right:**
- Clean JSONL format for golden datasets (prompt + ideal pairs)
- Model-graded eval concept was ahead of its time
- Python-native

**What it got wrong:**
- Tightly coupled to OpenAI API — adding Anthropic/Google requires forking
- No cost tracking
- No web UI, no leaderboard, minimal reporting
- No custom scoring functions beyond their predefined types without modifying source
- Effectively dead project

**Verdict:** Historical interest only. Don't use this.

---

#### 1.3 DeepEval

| Attribute | Detail |
|---|---|
| **Repo** | https://github.com/confident-ai/deepeval |
| **Stars** | ~4,500+ |
| **Last commit** | Active (weekly) |
| **Maintenance** | Good — maintained by Confident AI |
| **Language** | Python |

**Core Capabilities:**
- Python-native, pytest-style test runner (`deepeval test run`)
- Define test cases as Python objects: `LLMTestCase(input=..., actual_output=..., expected_output=...)`
- Rich built-in metrics: answer relevancy, faithfulness, hallucination, bias, toxicity, GEval (LLM-as-judge with custom criteria), summarization
- **GEval metric**: define custom rubric in natural language, pick judge model, get scored 0–1 — this is exactly AI-judge scoring
- **Custom metrics**: subclass `BaseMetric`, implement `measure()` and `is_successful()` in Python — full code-based scoring
- Multi-provider: uses LiteLLM under the hood, so supports OpenAI, Anthropic, Google, Azure, Bedrock, Ollama, 100+ providers
- Cost tracking: tracks token count and latency per test case; dollar cost via LiteLLM's cost mapping
- Dataset management: `EvaluationDataset` class, load from JSON/CSV, push to Confident AI cloud for versioning
- Reporting: CLI output (pytest-style), Confident AI cloud dashboard (free tier), JSON export
- Confident AI platform (optional): run history, regression tracking, leaderboard-like comparisons

**Golden Dataset Management:**
- `EvaluationDataset` with `add_test_case()`, save/load from JSON
- Cloud-hosted dataset versioning via Confident AI (optional, freemium)
- Git-friendly JSON files for local use

**Limitations:**
- The "run same prompt across multiple models" workflow is less natural — you'd write a loop in Python that swaps models and collects results; it's not declarative like promptfoo's YAML matrix
- Reporting is basic unless you use the Confident AI cloud
- Cross-model comparison/leaderboard is a cloud feature, not local
- Pytest integration is great for CI, but less great for exploratory benchmarking sessions

---

#### 1.4 Inspect AI (UK AI Safety Institute)

| Attribute | Detail |
|---|---|
| **Repo** | https://github.com/UKGovernmentBEIS/inspect_ai |
| **Stars** | ~2,500+ |
| **Last commit** | Active (maintained by UK AISI) |
| **Maintenance** | Excellent — government-funded, professional team |
| **Language** | Python |

**Core Capabilities:**
- Python-native task definition with decorators: `@task` defines a benchmark
- Dataset loading from CSV/JSON/HuggingFace with `Sample(input=..., target=...)`
- Solvers: composable pipeline of prompt transformations (system message, chain-of-thought, etc.)
- Scorers: built-in (exact match, includes, pattern, model-graded) + fully custom Python scorer functions
- Model-graded scoring: built-in, configurable judge model and rubric template
- Multi-provider: OpenAI, Anthropic, Google, Azure, Bedrock, Together, Mistral, Ollama, HuggingFace, vLLM, custom
- **Evaluation log viewer**: `inspect view` launches a polished local web UI showing results, scores, token usage, per-sample details
- Cost tracking: token counts (input/output/total), latency, model metadata per sample — dollar cost calculable but not displayed natively
- Statistical: supports `epochs` (multiple runs), but no built-in CI calculation
- CLI: `inspect eval`, `inspect view`, `inspect log`

**What it does exceptionally well:**
- Task definition is pure Python with clean abstractions — very natural for Python devs
- Solver/scorer composability is elegant
- The web log viewer is surprisingly polished for a government project
- Excellent documentation

**Limitations:**
- No native "leaderboard" or cross-run comparison — each eval produces a log; comparing requires manual effort or custom scripts
- Dollar cost not computed (just tokens)
- No dataset versioning beyond files on disk
- Designed more for safety evals than for production model selection — the mental model is "evaluate a model on a task" not "compare 5 models on the same task side-by-side"
- Multi-model comparison requires running separate evals and comparing logs

---

#### 1.5 Ragas

| Attribute | Detail |
|---|---|
| **Repo** | https://github.com/explodinggradients/ragas |
| **Stars** | ~7,500+ |
| **Last commit** | Active |
| **Maintenance** | Good |
| **Language** | Python |

**Assessment:** Ragas is specifically designed for RAG pipeline evaluation (context recall, context precision, answer faithfulness, answer relevancy). While it supports custom metrics and LLM-as-judge, its entire conceptual model revolves around retrieval-augmented generation with context chunks. For CineForge's tasks (script normalization, entity extraction, continuity tracking), the RAG-centric abstractions are a poor fit. You'd be fighting the framework. **Not recommended for this use case.**

---

#### 1.6 Phoenix (Arize AI)

| Attribute | Detail |
|---|---|
| **Repo** | https://github.com/Arize-AI/phoenix |
| **Stars** | ~8,000+ |
| **Last commit** | Active daily |
| **Maintenance** | Excellent — VC-funded company |
| **Language** | Python |

**Assessment:** Phoenix is primarily an **observability** tool — tracing, logging, debugging LLM applications in production. It has eval capabilities (LLM-as-judge, custom eval functions) but they're secondary to its tracing focus. It can evaluate logged traces, but doesn't have the "define tasks, run across models, compare" workflow. You'd use Phoenix alongside a benchmarking tool, not instead of one. **Better suited as a production monitoring layer than a benchmarking tool.**

---

#### 1.7 LangSmith / LangChain Evaluation

| Attribute | Detail |
|---|---|
| **Repo** | LangSmith is proprietary SaaS; LangChain evaluation modules are in `langchain` |
| **Stars** | LangChain: 100k+, but the eval module is a small subset |
| **Maintenance** | Active but evaluation is not the focus |

**Assessment:**
- LangSmith has dataset management, evaluation runs, custom evaluators, LLM-as-judge, and comparison views — but it's a **proprietary hosted platform**, not open source
- LangChain's `evaluation` module is open source but thin — basic criteria evaluators, string distance, embedding distance, custom Python evaluators
- Requires buying into the LangChain ecosystem heavily
- Cost tracking through LangSmith traces
- If you're already using LangChain: consider it. If not: the overhead of adopting LangChain's abstractions for everything is not justified for benchmarking alone

**Verdict:** Not recommended unless already deep in LangChain ecosystem.

---

#### 1.8 Braintrust

| Attribute | Detail |
|---|---|
| **Repo** | https://github.com/braintrustdata/braintrust-sdk |
| **Stars** | ~300+ |
| **Maintenance** | Active (VC-funded company) |

**Assessment:**
- Braintrust is primarily a **commercial platform** with open-source SDKs
- The SDK provides logging, scoring, dataset management
- Evaluation runs, comparisons, and the dashboard are cloud features
- Custom scorers in Python, LLM-as-judge, multi-model comparison — all available through the platform
- Open-source `autoevals` library (https://github.com/braintrustdata/autoevals) is useful standalone: provides battle, closedqa, factuality, humor, possible, security, sql, summary, translation LLM-graded scorers
- The `autoevals` library can be used with ANY framework — it's just scoring functions

**Verdict:** `autoevals` is a useful library to borrow scoring functions from. The full Braintrust platform is commercial. Not recommended as the core framework.

---

#### 1.9 Humanloop

**Assessment:** Fully proprietary SaaS. No meaningful open-source component. Skip.

---

#### 1.10 Additional Tools Discovered

**MLflow LLM Evaluate** (https://github.com/mlflow/mlflow)
- MLflow added `mlflow.evaluate()` for LLMs — supports custom metrics, built-in toxicity/relevance/etc.
- Integrates with MLflow tracking for experiment management
- Heavyweight dependency (full MLflow)
- Multi-model comparison through MLflow's experiment comparison UI
- Python-native, mature, well-maintained
- **Interesting option if you already use MLflow**

**LiteLLM** (https://github.com/BerriAI/litellm)
- Not an eval framework, but a universal model gateway: unified API across 100+ providers
- Tracks token usage, cost, latency
- Several eval frameworks use it internally (DeepEval does)
- **Essential building block** regardless of which framework you choose

**Evidently AI** (https://github.com/evidentlyai/evidently)
- Data/ML monitoring with recent LLM eval additions
- Custom descriptors, LLM-as-judge
- Strong on statistical analysis and drift detection
- Not primarily designed for model comparison benchmarking

**Weights & Biases Weave** (https://github.com/wandb/weave)
- W&B's LLM eval and tracing tool
- Custom scorers, dataset management, comparison views
- Open source but designed to funnel into W&B platform
- Python-native, good abstractions

---

## 2. Gap Analysis — Top 5 Tools

Based on the above, the top 5 most promising tools for CineForge's requirements are:

1. **promptfoo** — best multi-model comparison workflow
2. **DeepEval** — best Python-native experience
3. **Inspect AI** — cleanest architecture and scoring extensibility
4. **MLflow LLM Evaluate** — best experiment tracking
5. **promptfoo + DeepEval hybrid** (considered as a strategy)

### Detailed Gap Matrix

| Requirement | Weight | promptfoo | DeepEval | Inspect AI | MLflow LLM Eval |
|---|---|---|---|---|---|
| **Multi-provider** (OpenAI + Anthropic + Google min) | Must-have | ✅ Full — native support for all three + dozens more, custom provider scripts | ✅ Full — via LiteLLM, 100+ providers | ✅ Full — native support for all three + many more | ⚠️ Partial — requires custom wrapper per provider; no unified provider abstraction |
| **Custom task definitions** (our prompts, our inputs) | Must-have | ✅ Full — YAML prompts × vars × providers matrix; load inputs from CSV/JSON | ✅ Full — Python test cases, load from JSON/CSV | ✅ Full — Python `@task` with `Dataset` of `Sample` objects | ✅ Full — Python, pass any data to `mlflow.evaluate()` |
| **Code-based scoring** (custom Python functions) | Must-have | ✅ — via Python script assertions (`type: python`, reference external .py files) | ✅ Full — subclass `BaseMetric`, implement `measure()` in pure Python | ✅ Full — `@scorer` decorator, pure Python, composable | ✅ Full — custom metric functions in Python |
| **AI-judge scoring** (configurable judge model + rubric) | Must-have | ✅ Full — `llm-rubric` assertion, custom judge prompt, configurable model, score extraction | ✅ Full — `GEval` metric with custom criteria, configurable judge model, 0–1 scoring | ✅ Full — `model_graded_qa`, `model_graded_fact`, custom judge templates, configurable model | ⚠️ Partial — built-in relevance/toxicity judges; custom judge requires manual implementation |
| **Cost tracking** (tokens + dollars per model per task) | Must-have | ✅ Full — tokens, latency, dollar cost displayed in UI and JSON output; configurable pricing | ✅ — tokens + latency tracked; dollar cost via LiteLLM cost tables; displayed in CLI output | ⚠️ Partial — tokens and latency in eval logs; no dollar cost computation | ⚠️ Partial — token counts in traces; dollar cost not native |
| **Golden dataset management** | Should-have | ⚠️ Partial — CSV/JSON files with expected outputs; no versioning beyond Git | ⚠️ Partial — `EvaluationDataset` JSON; optional cloud versioning via Confident AI | ⚠️ Partial — Dataset from CSV/JSON/HF; no versioning | ✅ — MLflow Datasets with versioning, lineage tracking |
| **CLI interface** | Should-have | ✅ Full — `promptfoo eval`, `promptfoo view`, `promptfoo share`, `promptfoo cache` | ✅ — `deepeval test run` (pytest-based), `deepeval login` | ✅ Full — `inspect eval`, `inspect view`, `inspect log` | ⚠️ Partial — Python API primary; `mlflow` CLI exists but eval isn't CLI-first |
| **Cross-run comparison / leaderboards** | Should-have | ✅ Full — web UI shows all providers side-by-side with scores and costs per test case; comparison is the core UX | ⚠️ Partial — requires Confident AI cloud for comparison; local is per-run only | ⚠️ Partial — `inspect view` shows per-run; no built-in cross-run comparison | ✅ — MLflow experiment comparison UI, charts, tables |
| **Python-based or Python-friendly** | Should-have | ⚠️ Partial — TypeScript core; Python custom providers/scorers via subprocess; YAML config is language-agnostic | ✅ Full — pure Python, pytest integration | ✅ Full — pure Python | ✅ Full — pure Python |
| **Statistical rigor** (multiple runs, CIs) | Nice-to-have | ⚠️ Partial — `repeat` field for N runs; no CI computation | ⚠️ Partial — can loop runs; no CI computation | ⚠️ Partial — `epochs` for N runs; no CI computation | ⚠️ Partial — can log multiple runs; no automatic CI |
| **Extensible** (plugins, custom providers) | Nice-to-have | ✅ Full — custom providers (Python/JS/HTTP), custom assertions, transform functions, plugins | ✅ — custom metrics, custom models via LiteLLM | ✅ Full — custom solvers, scorers, models; composable architecture | ✅ — custom metrics, plugins |
| **Lightweight / standalone** | Nice-to-have | ✅ — `npx promptfoo@latest eval` works standalone; no infra needed | ✅ — `pip install deepeval`; no infra needed | ✅ — `pip install inspect-ai`; no infra needed | ❌ — MLflow server, artifact store, database; heavyweight |

### Scoring Summary

| Tool | Must-haves (5) | Should-haves (4) | Nice-to-haves (3) | Notes |
|---|---|---|---|---|
| **promptfoo** | 5/5 (100%) | 3.5/4 (88%) | 2.5/3 (83%) | Python-friendliness is the only real gap |
| **DeepEval** | 5/5 (100%) | 2/4 (50%) | 2/3 (67%) | Weak on comparison UX without cloud |
| **Inspect AI** | 4.5/5 (90%) | 2.5/4 (63%) | 2.5/3 (83%) | Dollar cost gap; comparison gap |
| **MLflow** | 3.5/5 (70%) | 3/4 (75%) | 1.5/3 (50%) | Provider and judge gaps; heavyweight |

---

## 3. Recommendation

### Primary Recommendation: **Adopt promptfoo**

promptfoo meets **100% of must-haves** and **~88% of should-haves**, clearing both bars. Here's the specific argument:

#### Why promptfoo wins for CineForge:

**1. The comparison workflow is native.** CineForge's core need is "run the same task across 5 models and compare." promptfoo's YAML matrix design makes this trivially declarative:

```yaml
# cineforge-benchmarks/scene-extraction.yaml
description: "Scene extraction benchmark"

prompts:
  - file://prompts/scene-extraction-v2.txt

providers:
  - openai:gpt-4o
  - openai:gpt-4o-mini
  - anthropic:messages:claude-sonnet-4-20250514
  - anthropic:messages:claude-3-5-haiku-20241022
  - vertex:gemini-2.0-flash
  - vertex:gemini-2.5-pro

tests:
  - vars:
      script: file://golden/inception-act1.txt
    assert:
      - type: python
        value: file://scorers/scene_extraction_scorer.py
      - type: llm-rubric
        value: |
          Evaluate the scene extraction output against the reference.
          Score on: completeness (all scenes found), boundary accuracy
          (correct start/end), metadata quality (descriptions, characters).
          Reference output: {{expected}}
        provider: openai:gpt-4o
    metadata:
      expected: file://golden/inception-act1-scenes.json
      category: scene-extraction

  - vars:
      script: file://golden/parasite-opening.txt
    assert:
      - type: python
        value: file://scorers/scene_extraction_scorer.py
      - type: llm-rubric
        value: |
          Evaluate scene extraction completeness and accuracy.
          Reference: {{expected}}
        provider: openai:gpt-4o
    metadata:
      expected: file://golden/parasite-opening-scenes.json
      category: scene-extraction
```

**2. Custom Python scorers work well despite TypeScript core:**

```python
# scorers/scene_extraction_scorer.py
import json

def get_assert(output, context):
    """Custom scorer for scene extraction quality."""
    try:
        extracted = json.loads(output)
        expected = json.loads(context["vars"].get("expected_scenes", "[]"))
    except json.JSONDecodeError:
        return {"pass": False, "score": 0, "reason": "Output is not valid JSON"}

    # Deterministic metrics
    expected_count = len(expected)
    extracted_count = len(extracted)
    count_accuracy = min(extracted_count, expected_count) / max(expected_count, 1)

    # Character overlap scoring
    expected_chars = {s.get("characters", []) for s in expected}
    # ... detailed matching logic ...

    score = (count_accuracy * 0.4) + (boundary_score * 0.3) + (metadata_score * 0.3)

    return {
        "pass": score >= 0.7,
        "score": score,
        "reason": f"Count accuracy: {count_accuracy:.2f}, "
                  f"Boundary: {boundary_score:.2f}, "
                  f"Metadata: {metadata_score:.2f}"
    }
```

**3. Cost tracking is built in.** The web UI and JSON output show tokens (prompt/completion), latency (ms), and estimated dollar cost per cell in the comparison matrix. You can immediately see "GPT-4o scores 0.92 on scene extraction at $0.034/call, while Claude Haiku scores 0.85 at $0.003/call."

**4. The web UI is exactly the leaderboard you want.** `promptfoo view` shows a matrix of [test cases] × [providers] with scores, pass/fail, cost, and you can sort by any column. This is your model leaderboard.

#### Gaps and Workarounds:

**Gap 1: Not Python-native (TypeScript core)**
- **Impact:** Medium. You interact via YAML + Python scorer scripts, not Python APIs.
- **Workaround:** Your scorers and data processing are all Python. promptfoo calls them via subprocess. In practice, your Python scorer files are clean standalone modules. If you need to orchestrate from Python (e.g., trigger evals programmatically), you can call `subprocess.run(["promptfoo", "eval", "-c", config_path])` or use the recently-added Python SDK wrapper.
- **Alternative:** Use DeepEval for tasks where you want tighter Python integration, and promptfoo for the comparison workflow.

**Gap 2: Golden dataset versioning**
- **Impact:** Low. Your golden datasets are JSON/CSV files.
- **Workaround:** Store golden datasets in Git alongside your eval configs. Use a directory structure:
```
cineforge-benchmarks/
├── tasks/
│   ├── scene-extraction.yaml
│   ├── character-bible.yaml
│   └── continuity-check.yaml
├── prompts/
│   ├── scene-extraction-v2.txt
│   └── character-bible-v3.txt
├── golden/
│   ├── inception-act1.txt
│   ├── inception-act1-scenes.json  # reference output
│   └── ...
├── scorers/
│   ├── scene_extraction_scorer.py
│   ├── character_bible_scorer.py
│   └── json_structure_scorer.py
└── results/  # gitignored, or selectively committed
```
Git gives you versioning, diffs, and blame on golden datasets. This is actually better than a database for your use case.

**Gap 3: Statistical rigor**
- **Impact:** Low-medium.
- **Workaround:** Set `repeat: 5` in config for stochastic tasks. Post-process the JSON output with a simple Python script to compute mean, stddev, and confidence intervals:

```python
# scripts/compute_stats.py
import json, numpy as np
from scipy import stats

with open("promptfoo_output.json") as f:
    results = json.load(f)

# Group by provider × test case, compute CI
for provider_results in grouped:
    scores = [r["score"] for r in provider_results]
    mean = np.mean(scores)
    ci = stats.t.interval(0.95, len(scores)-1, loc=mean, scale=stats.sem(scores))
    print(f"{provider}: {mean:.3f} [{ci[0]:.3f}, {ci[1]:.3f}]")
```

**Gap 4: Cross-run historical tracking**
- **Impact:** Low-medium.
- **Workaround:** promptfoo stores eval results in a local SQLite database (~/.promptfoo/). You can query it, or commit JSON outputs to Git with timestamps. For richer tracking, the promptfoo cloud product (free tier) provides run history — or you could push results to a simple dashboard.

---

### Secondary Recommendation: Use DeepEval as a complement

For tasks where you want **tight Python integration** — especially for CI/CD gates, integration with existing Python pipelines, or complex scoring logic that benefits from importing your own modules directly:

```python
# tests/test_character_bible.py
import pytest
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import GEval, BaseMetric
from deepeval.test_case import LLMTestCaseParams

class CharacterConsistencyMetric(BaseMetric):
    """Custom code-based metric for character bible completeness."""

    def __init__(self):
        self.threshold = 0.7
        self.score = 0

    def measure(self, test_case: LLMTestCase):
        # Your deterministic scoring logic
        output = json.loads(test_case.actual_output)
        expected = json.loads(test_case.expected_output)

        fields_present = sum(1 for f in REQUIRED_FIELDS if f in output) / len(REQUIRED_FIELDS)
        name_match = fuzz.ratio(output.get("name", ""), expected["name"]) / 100
        # ... more deterministic checks ...

        self.score = (fields_present * 0.5) + (name_match * 0.3) + (trait_overlap * 0.2)
        self.reason = f"Fields: {fields_present:.2f}, Name: {name_match:.2f}"
        self.success = self.score >= self.threshold
        return self.score

    def is_successful(self):
        return self.success

    @property
    def __name__(self):
        return "Character Consistency"

# AI judge for subjective quality
character_quality_judge = GEval(
    name="Character Bible Quality",
    criteria="""Evaluate the character bible entry for:
    1. Completeness: Does it cover physical description, personality, motivations, relationships?
    2. Accuracy: Does it match what's described in the source script?
    3. Specificity: Are descriptions specific enough to maintain continuity?
    4. Formatting: Is it well-structured and consistent?""",
    evaluation_params=[LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.EXPECTED_OUTPUT],
    model="gpt-4o",
    threshold=0.7,
)

@pytest.mark.parametrize("golden", load_golden_dataset("character_bible"))
def test_character_bible(golden):
    test_case = LLMTestCase(
        input=golden["input"],
        actual_output=run_model(golden["input"], model="claude-sonnet-4-20250514"),
        expected_output=golden["expected"],
    )
    assert_test(test_case, [CharacterConsistencyMetric(), character_quality_judge])
```

**Use promptfoo for:** "Which model is best for task X?" (comparison workflow)
**Use DeepEval for:** "Does our pipeline pass quality gates in CI?" (test workflow)

---

## 4. Architecture Pattern (If Building — Not Primary Recommendation, But Included)

Even though I recommend adopting promptfoo, here's the architecture if you needed to build something custom (e.g., if requirements evolve significantly):

### Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    CLI / Web UI                       │
│  cineforge-bench run scene-extraction --models all   │
│  cineforge-bench compare --task scene-extraction     │
│  cineforge-bench report --format markdown            │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│              Task Registry                            │
│  YAML task definitions: prompt, inputs, scorers,     │
│  judge config, model constraints                     │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │scene-extract│  │char-bible    │  │continuity  │ │
│  │.yaml        │  │.yaml         │  │.yaml       │ │
│  └─────────────┘  └──────────────┘  └────────────┘ │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│              Execution Engine                         │
│  For each (task × model × input):                    │
│    1. Render prompt with input vars                  │
│    2. Call model via LiteLLM                         │
│    3. Capture output, tokens, latency, cost          │
│    4. Run scorers (code + judge)                     │
│    5. Store result                                   │
│  Async with concurrency limits, retry, caching       │
└────────────┬──────────────┬─────────────────────────┘
             │              │
┌────────────▼──────┐  ┌───▼──────────────────────────┐
│  Model Gateway    │  │  Scorer Registry              │
│  (LiteLLM)       │  │  ┌──────────────────────────┐ │
│  - OpenAI        │  │  │ Code Scorers (Python)    │ │
│  - Anthropic     │  │  │ - json_valid             │ │
│  - Google        │  │  │ - scene_count_accuracy   │ │
│  - Azure         │  │  │ - entity_overlap         │ │
│  - Ollama        │  │  │ - custom functions       │ │
│  - Any provider  │  │  └──────────────────────────┘ │
│                   │  │  ┌──────────────────────────┐ │
│  Unified API:     │  │  │ Judge Scorers (LLM)     │ │
│  completion()     │  │  │ - configurable model     │ │
│  → output,        │  │  │ - configurable rubric    │ │
│    tokens,        │  │  │ - score extraction       │ │
│    cost,          │  │  │ - reasoning capture      │ │
│    latency        │  │  └──────────────────────────┘ │
└───────────────────┘  └──────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│              Results Store                            │
│  SQLite / JSON files                                 │
│  Schema: run_id, task, model, input_id, output,      │
│          scores{}, tokens{}, cost, latency, timestamp │
│                                                       │
│  Golden Datasets: JSON files in Git                  │
│  Results: SQLite for querying, JSON for portability  │
└────────────────┬────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────┐
│              Reporting Engine                         │
│  - Leaderboard: task × model matrix with scores+cost │
│  - Cost/quality Pareto chart                         │
│  - Per-task winner recommendation                    │
│  - Markdown / HTML / JSON output                     │
│  - Optional: Streamlit dashboard                     │
└─────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Use LiteLLM as the model gateway.** Don't build provider adapters. LiteLLM handles 100+ providers with a unified `completion()` API and built-in cost tracking. This is a solved problem.

2. **YAML task definitions, Python scorers.** Tasks should be declarative (YAML) so non-engineers can define benchmarks. Scorers should be Python so you get full power for domain-specific logic.

3. **Separate code scoring from judge scoring.** They serve different purposes and should be composable. A task should be able to have zero or many of each.

4. **Cache aggressively.** Hash (model + prompt + input + params) → cache response. Model API calls are expensive. Invalidate cache when prompt changes, not when scorer changes.

5. **Store raw outputs alongside scores.** You will always want to re-examine outputs and re-score with improved scorers without re-running models.

6. **Results are append-only.** Never overwrite a run. Every eval is a timestamped snapshot. Compare across snapshots.

### Pitfalls to Avoid (Learned from Existing Tools)

- **Don't couple to one provider** (OpenAI Evals' fatal flaw)
- **Don't require a cloud service for basic functionality** (Braintrust, LangSmith trap)
- **Don't over-engineer the UI** — start with CLI + JSON output, add UI later
- **Don't build your own LLM client** — use LiteLLM
- **Don't store golden data in a database** — files in Git are simpler and more durable
- **Don't make scoring synchronous with model calls** — cache model outputs, allow re-scoring separately

### Estimated Complexity

If building from scratch:
- **MVP (CLI, 3 tasks, comparison table):** 1–2 weeks for a senior engineer
- **Production-quality (all tasks, web UI, caching, CI):** 4–6 weeks
- **Ongoing maintenance:** 2–4 hours/week for provider updates, new tasks

**This is why I recommend promptfoo** — it's already 80% of what you'd build, and the remaining 20% (Python scorer integration, golden data management) is straightforward to layer on top.

---

## 5. Concrete Getting-Started Plan with promptfoo

### Week 1: Foundation

```bash
# Install
npm install -g promptfoo
# Or use npx (no install needed)
npx promptfoo@latest init cineforge-benchmarks
```

```yaml
# cineforge-benchmarks/promptfooconfig.yaml
# Start with one task, two models
description: "CineForge Scene Extraction Benchmark"

prompts:
  - id: scene-extraction-v1
    raw: |
      You are a professional script analyst. Extract all scenes from the
      following screenplay excerpt. For each scene, provide:
      - scene_number
      - heading (slug line)
      - start_line and end_line
      - brief description
      - characters present
      - location

      Output valid JSON array.

      SCREENPLAY:
      {{script}}

providers:
  - id: openai:gpt-4o
    config:
      temperature: 0.1
  - id: anthropic:messages:claude-sonnet-4-20250514
    config:
      temperature: 0.1
  - id: openai:gpt-4o-mini
    config:
      temperature: 0.1

defaultTest:
  options:
    provider: openai:gpt-4o  # judge model

tests:
  - vars:
      script: file://golden/inception-act1.txt
    assert:
      - type: is-json
      - type: python
        value: file://scorers/scene_count.py
      - type: llm-rubric
        value: |
          Compare this scene extraction to the reference. Score 1-10 on:
          - Completeness (all scenes identified)
          - Accuracy (correct boundaries and descriptions)
          - Character identification (all speaking/present characters)
          Reference: file://golden/inception-act1-expected.json
    metadata:
      task: scene-extraction
      difficulty: medium

  - vars:
      script: file://golden/parasite-opening.txt
    assert:
      - type: is-json
      - type: python
        value: file://scorers/scene_count.py
      - type: llm-rubric
        value: |
          Compare this scene extraction to the reference.
          Reference: file://golden/parasite-opening-expected.json
    metadata:
      task: scene-extraction
      difficulty: hard
```

```bash
# Run
promptfoo eval -c promptfooconfig.yaml

# View results
promptfoo view
```

### Week 2: Expand to all CineForge tasks

Create one YAML config per task:
- `tasks/scene-extraction.yaml`
- `tasks/character-bible.yaml`
- `tasks/location-bible.yaml`
- `tasks/prop-bible.yaml`
- `tasks/entity-graph.yaml`
- `tasks/continuity-check.yaml`
- `tasks/script-normalization.yaml`

Create a master runner:

```bash
#!/bin/bash
# run_all_benchmarks.sh
for config in tasks/*.yaml; do
    echo "=== Running $(basename $config) ==="
    promptfoo eval -c "$config" --output "results/$(basename $config .yaml).json"
done

# Generate combined report
python scripts/combine_results.py results/ > reports/leaderboard.md
```

### Week 3: Polish and CI

```yaml
# .github/workflows/model-benchmark.yml
name: CineForge Model Benchmark
on:
  schedule:
    - cron: '0 6 * * 1'  # Weekly Monday 6am
  workflow_dispatch:

jobs:
  benchmark:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
      - run: npm install -g promptfoo
      - run: bash run_all_benchmarks.sh
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
      - uses: actions/upload-artifact@v4
        with:
          name: benchmark-results
          path: results/
```

---

## Final Verdict

| Decision | Recommendation |
|---|---|
| **Primary tool** | **promptfoo** — adopt immediately |
| **Complement for CI/Python** | **DeepEval** — use for pytest-style quality gates |
| **Model gateway** | **LiteLLM** — use if building any custom tooling around the edges |
| **Scoring library** | **Braintrust autoevals** — borrow their LLM-graded scorers as needed |
| **Build our own?** | **No** — promptfoo covers 90%+ of requirements; build the remaining 10% as lightweight scripts around it |

The 10% you'll build: a `combine_results.py` script for cross-task leaderboards, a `compute_stats.py` for confidence intervals, and your domain-specific Python scorers. That's 2–3 days of work, not 2–3 months.
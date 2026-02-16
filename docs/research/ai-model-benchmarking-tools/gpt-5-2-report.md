---
type: research-report
topic: ai-model-benchmarking-tools
canonical-model-name: gpt-5.2
collected: '2026-02-15T21:22:37.242063+00:00'
---

I can’t reliably “find and evaluate ALL existing open‑source tools” with accurate **stars / last commit dates / maintenance status** without live web access. What I *can* do is:

1) enumerate the major open-source options that are commonly used for **custom LLM task evaluation** (not academic benchmarks),  
2) describe their capabilities against your requirements (based on known designs/docs up to my cutoff),  
3) give a **gap analysis** for the most promising 3–5, and  
4) recommend adopt vs build, plus an architecture if building.

If you want the “repo URL + stars + last commit” table to be exact, paste a shortlist of repos you’re considering (or allow me browsing in your environment) and I’ll fill it in precisely.

---

## 1) Existing open-source tools for custom LLM benchmarking/evaluation

### A. Promptfoo
- **What it is**: Prompt test runner + eval harness focused on “run prompts across models and compare.”
- **Core capabilities**
  - Multi-model, multi-provider runs; good for A/B testing prompts and models.
  - Strong at “matrix” evaluation: many prompts × many test cases × many models.
- **Evaluation support**
  - **Code-based scoring**: yes (custom JS/TS/Python via scripts; supports assertions, regex, JSON schema checks, etc.).
  - **AI-as-judge**: yes (LLM graders/rubrics).
- **Cost tracking**
  - Tracks token usage/latency; cost support exists but may require provider pricing config; varies by provider.
- **Golden dataset management**
  - Has test cases in YAML/JSON; can store expected outputs; versioning is “whatever your git does.”
- **Task definition format**
  - YAML-centric (prompts, providers, tests, assertions).
- **Provider support**
  - Broad: OpenAI, Anthropic, Google, Azure OpenAI, local (Ollama), etc. Extensible.
- **CLI vs UI**
  - CLI first; also has a local web viewer/report.
- **Reporting**
  - HTML reports, console tables, JSON exports; comparisons across runs are possible.
- **Extensibility**
  - Good: custom assertions, custom providers, custom graders.
- **Python-friendly**
  - Usable from Python pipelines but not “Python-native”; it’s more CLI/Node oriented.
- **Community health**
  - Generally active and widely used in prompt engineering workflows.

**Fit for CineForge**: Very close to what you want for “custom tasks + multi-provider + judge + reports,” especially if you’re okay with YAML/CLI and some glue for dataset/versioning and deeper analytics.

---

### B. OpenAI Evals (open-source)
- **What it is**: A framework OpenAI released for writing evals; originally oriented around OpenAI models but can be adapted.
- **Core capabilities**
  - Define evals (datasets + eval logic) and run them.
- **Evaluation support**
  - **Code-based scoring**: yes (Python).
  - **AI-as-judge**: yes (model-graded evals are a core pattern).
- **Cost tracking**
  - Tracks tokens for OpenAI; dollars/cost and non-OpenAI providers are not first-class.
- **Golden dataset management**
  - Supports datasets (JSONL) and expected outputs; versioning via git.
- **Task definition format**
  - YAML + Python classes + JSONL datasets.
- **Provider support**
  - Primarily OpenAI; can be extended but not as plug-and-play as newer tools.
- **CLI vs UI**
  - CLI; no rich dashboard by default.
- **Reporting**
  - JSON logs; basic summaries.
- **Extensibility**
  - High in Python, but you’ll write code.
- **Python-friendly**
  - Yes (Python-native).
- **Community health**
  - Unclear long-term momentum vs newer ecosystems; many teams moved to other frameworks.

**Fit**: Great conceptual foundation (datasets + eval classes + model-graded), but you’ll likely spend time modernizing provider support, reporting, and cost accounting.

---

### C. DeepEval
- **What it is**: Python LLM evaluation framework with built-in metrics and the ability to write custom ones.
- **Core capabilities**
  - Evaluate LLM outputs for tasks like QA, summarization, RAG, etc.
  - Integrates with common LLM stacks.
- **Evaluation support**
  - **Code-based scoring**: yes (custom metrics).
  - **AI-as-judge**: yes (LLM-based metrics/judges).
- **Cost tracking**
  - Some token/cost tracking depending on integrations; not always comprehensive across providers.
- **Golden dataset management**
  - Supports datasets/test cases; “golden set” is typically your own files + git.
- **Task definition format**
  - Python-first (define test cases/metrics in code).
- **Provider support**
  - Often via wrappers (OpenAI/Anthropic/etc.); depends on version.
- **CLI vs UI**
  - Primarily Python; some CLI support exists in some versions; not a full dashboard.
- **Reporting**
  - Python outputs; can export results; not always “leaderboard” out of the box.
- **Extensibility**
  - Good for custom metrics; provider extensibility depends on adapters.
- **Python-friendly**
  - Yes.
- **Community health**
  - Active in the LLM tooling space (verify current status in your environment).

**Fit**: Strong if you want Python-native eval + custom metrics + judge, but you may need to build the “benchmark runner across many providers + cost/latency + leaderboards” layer.

---

### D. LangChain / LangSmith (partially open-source)
- **What it is**
  - LangChain is open-source; LangSmith is primarily a hosted product (with some SDKs open).
- **Core capabilities**
  - Experiment tracking, dataset-based evaluation, prompt/version management (mostly via LangSmith).
- **Evaluation support**
  - **Code-based scoring**: yes (custom evaluators).
  - **AI-as-judge**: yes (LLM evaluators).
- **Cost tracking**
  - LangSmith tracks tokens/latency well when instrumented; dollars may require config.
- **Golden dataset management**
  - LangSmith has strong dataset management (but it’s a platform).
- **Task definition format**
  - Python; datasets stored in LangSmith.
- **Provider support**
  - Broad via LangChain integrations.
- **CLI vs UI**
  - UI is a big part (LangSmith web app).
- **Reporting**
  - UI dashboards, comparisons, experiment runs.
- **Extensibility**
  - High.
- **Python-friendly**
  - Yes.
- **Community health**
  - Very active.

**Fit**: If you’re okay adopting a platform (and potentially paid/hosted), it’s one of the most complete. If you need “lightweight standalone open-source,” it may not match.

---

### E. Ragas (RAG evaluation)
- **What it is**: Focused on evaluating RAG pipelines (faithfulness, context precision/recall, etc.).
- **Core capabilities**
  - Great for RAG-specific metrics; less for arbitrary CineForge tasks.
- **Evaluation support**
  - Code-based + LLM-judge style metrics (many metrics use an LLM).
- **Cost tracking**
  - Not the main focus.
- **Golden dataset management**
  - You provide datasets; not a full dataset/versioning system.
- **Task definition format**
  - Python.
- **Provider support**
  - Via LLM wrappers.
- **Fit**: Likely only useful for the subset of CineForge tasks that are retrieval/grounding related.

---

### F. Arize Phoenix (open-source)
- **What it is**: Observability + evaluation for LLM apps; has tracing, datasets, evals.
- **Core capabilities**
  - Collect traces, run evals, analyze failure modes.
- **Evaluation support**
  - Supports evaluators; can do LLM-based evals; also supports deterministic checks.
- **Cost tracking**
  - Strong on latency; token/cost depends on instrumentation.
- **Golden dataset management**
  - Has dataset concepts; more “observability platform” than “benchmark runner.”
- **CLI vs UI**
  - Has a UI (local/hosted) for analysis.
- **Fit**: Great if you also want production observability; may be heavier than a pure benchmarking harness.

---

### G. UK AISI Inspect (Inspect AI)
- **What it is**: A framework for writing and running LLM evaluations; oriented toward structured evals and safety/testing.
- **Core capabilities**
  - Task specs, datasets, model runners, scoring.
- **Evaluation support**
  - Code-based scoring; supports model-graded patterns.
- **Cost tracking**
  - Some run metadata; cost accounting may not be first-class.
- **Golden dataset management**
  - Dataset-driven; versioning via files/git.
- **Task definition format**
  - Python + config.
- **Provider support**
  - Supports multiple providers; extensible.
- **CLI vs UI**
  - CLI; reporting artifacts.
- **Fit**: Promising for “serious eval harness,” but you may still need to build cost/leaderboards and CineForge-specific task templates.

---

### H. Braintrust (partially open; platform-first)
- **What it is**: Experiment tracking + evals; often used as a hosted platform. Some components/SDKs are open.
- **Fit**: Similar tradeoff to LangSmith—very complete if you accept a platform; less so if you need fully OSS + self-contained.

---

### I. Humanloop (platform-first; not OSS in the way you want)
- **Fit**: Likely not aligned with “open-source tool” requirement.

---

### J. Other notable OSS adjacent pieces (useful but not complete solutions)
- **LiteLLM**: Great as a **multi-provider abstraction** + usage tracking hooks; not an eval framework by itself.
- **Helicone**: OSS LLM observability/proxy; good for cost/latency logging; not a benchmark runner.
- **TruLens**: OSS eval/observability; similar space to Phoenix; can do feedback functions (including LLM judges).

---

## 2) Gap analysis (top 5 most promising for your requirements)

I’ll score as: **Yes / Partial / No** (and brief notes). Weights per your table.

### Tools compared
- **Promptfoo**
- **DeepEval**
- **Inspect AI**
- **OpenAI Evals**
- **Phoenix (Arize)**

| Requirement | Weight | Promptfoo | DeepEval | Inspect AI | OpenAI Evals | Phoenix |
|---|---|---|---|---|---|---|
| Multi-provider (OpenAI+Anthropic+Google) | Must | **Yes** | **Partial** (depends on adapters) | **Partial/Yes** (provider support exists; verify) | **No/Partial** (OpenAI-first) | **Partial** (via instrumentation) |
| Custom task definitions (your prompts/inputs) | Must | **Yes** (YAML tests) | **Yes** (Python test cases) | **Yes** | **Yes** | **Partial** (more “eval on traces/datasets”) |
| Code-based scoring (custom Python) | Must | **Partial** (custom assertions; not Python-native) | **Yes** | **Yes** | **Yes** | **Yes** |
| AI-judge scoring (judge model + rubric) | Must | **Yes** | **Yes** | **Yes/Partial** | **Yes** | **Yes/Partial** |
| Cost tracking (tokens + dollars per model per task) | Must | **Partial** (tokens/latency good; dollars varies) | **Partial** | **Partial** | **Partial** (OpenAI tokens; dollars not robust) | **Partial** (latency strong; tokens/cost depends) |
| Golden dataset management | Should | **Partial** (files + git) | **Partial** | **Partial** | **Partial** | **Partial/Yes** (datasets exist, but platformy) |
| CLI interface | Should | **Yes** | **Partial** | **Yes** | **Yes** | **Partial** |
| Cross-run comparison / leaderboards | Should | **Yes/Partial** (reports; can compare) | **Partial** | **Partial** | **Partial** | **Yes** (UI comparisons) |
| Python-based or Python-friendly | Should | **Partial** | **Yes** | **Yes** | **Yes** | **Yes** |
| Statistical rigor (multi-runs, CIs) | Nice | **No/Partial** | **Partial** | **Partial/Yes** (depending on harness) | **No/Partial** | **Partial** |
| Extensible (plugins/providers) | Nice | **Yes** | **Partial/Yes** | **Yes** | **Yes** | **Yes** |
| Lightweight / standalone | Nice | **Yes** | **Yes** | **Yes** | **Yes** | **No/Partial** (heavier) |

### What this table implies
- **No single tool cleanly hits all must-haves**, mainly because **true cost accounting (tokens + $) across providers** and **golden dataset lifecycle** are not consistently first-class in OSS eval harnesses.
- The closest “benchmark runner” experience is **Promptfoo** (but it’s not Python-native).
- The closest “Python-native eval framework” is **DeepEval / Inspect / OpenAI Evals**, but you’ll build more of the runner/reporting/cost layer.

---

## 3) Recommendation

### Recommendation: adopt + extend (not build from scratch), with a thin internal layer
A pure “adopt as-is” likely won’t meet your ≥80% must-haves threshold because of **cost tracking** and **golden dataset management** depth. But you also don’t need to build everything: the market already solved the hard parts of:
- running prompts across models,
- structuring eval cases,
- LLM-as-judge patterns,
- basic reporting.

**Best path**:  
- Use **Promptfoo** as the *execution + multi-provider matrix runner + judge harness* **or** use **Inspect AI** as the *Python-native harness*,  
- and build a **CineForge Eval Orchestrator** layer that standardizes:
  - provider invocation (possibly via **LiteLLM**),
  - cost accounting,
  - dataset/golden set versioning,
  - leaderboard storage and reporting.

If you strongly prefer Python-first integration with your pipeline, I’d bias toward **Inspect AI or DeepEval** + LiteLLM, rather than Promptfoo.

#### Why not “build our own end-to-end”?
You’ll end up re-implementing:
- concurrency, retries, rate limits, provider quirks,
- prompt templating,
- judge patterns and rubric calibration,
- result storage formats,
- report generation.

That’s a lot of surface area. Better to stand on an eval harness and build only the missing pieces.

---

## 4) Architecture patterns (for the “thin internal layer” or if you decide to build more)

### A. Reference architecture
**1) Task Spec Layer (declarative)**
- `task.yaml` (or Python) defines:
  - prompt template(s)
  - input schema
  - output schema (JSON schema / pydantic)
  - evaluation plan: deterministic metrics + judge rubric(s)
  - required model capabilities (JSON mode, tool use, max context, etc.)

**2) Dataset Layer (“golden sets”)**
- Store as versioned artifacts:
  - `datasets/<task>/<version>/cases.jsonl`
  - `reference_outputs.jsonl` (optional; sometimes you only have rubric-based judging)
  - metadata: source script IDs, scene IDs, difficulty tags
- Use git + DVC (or lakeFS) if datasets are large.

**3) Runner Layer**
- Expands matrix: (task × dataset × model × run_seed)
- Handles:
  - concurrency
  - retries/backoff
  - caching (don’t re-run identical calls)
  - structured logging of raw requests/responses

**4) Provider Abstraction**
- Use **LiteLLM** (or your own adapter) to normalize:
  - OpenAI / Anthropic / Google / Azure / etc.
  - token usage fields
  - latency
  - request/response formats

**5) Evaluation Layer**
- Deterministic scorers (Python):
  - JSON schema validity
  - exact match / fuzzy match
  - graph similarity (for entity graphs)
  - continuity constraint checks
- Judge scorers:
  - configurable judge model(s)
  - rubric templates per task
  - pairwise ranking option (often more stable than absolute 1–10)
  - judge calibration set (to detect drift)

**6) Results Store**
- Write every run to a normalized table:
  - `runs` (run_id, git_sha, task_version, dataset_version, model, provider, params)
  - `cases` (case_id, input_hash, tags)
  - `outputs` (raw_output, parsed_output, errors)
  - `metrics` (metric_name, value, details_json)
  - `cost` (prompt_tokens, completion_tokens, total_tokens, latency_ms, usd)
- SQLite/Postgres is enough.

**7) Reporting**
- Leaderboards:
  - quality score (weighted)
  - cost per case
  - quality/$ frontier (Pareto)
  - latency distributions
- Export:
  - JSON/CSV for internal dashboards
  - Markdown summaries for PRs
  - HTML report for humans

### B. Key design decisions to get right
- **Canonical output schemas** per task (Pydantic/JSON schema). This makes deterministic scoring and diffing possible.
- **Judge design**: prefer **pairwise comparisons** or rubric with anchored examples; store judge prompts and judge outputs for auditability.
- **Cost accounting**: centralize pricing tables and normalize token fields; providers differ a lot.
- **Reproducibility**: pin model versions where possible; store full request parameters; record prompt templates after rendering.
- **Caching**: hash (model + prompt + input + params) to avoid re-spend.

### C. Pitfalls to avoid (common in existing tools)
- Treating “golden outputs” as static truth when tasks are inherently subjective—use **hybrid**: schema + invariants + judge.
- Not storing raw outputs and parse errors—debugging becomes impossible.
- Letting judge model drift silently—add periodic re-judging and calibration.
- Only reporting averages—also report variance, failure rates, and constraint violations.

### D. Complexity estimate
- **Thin layer on top of an existing harness (Promptfoo/Inspect + LiteLLM + Postgres + reports)**: ~2–4 weeks for a solid v1 with leaderboards and cost/latency.
- **Full custom system from scratch**: ~6–10+ weeks to reach comparable maturity (provider quirks + reporting + caching + judge tooling).

---

## What I need from you to finalize with high confidence
1) Do you require **100% open-source + self-hosted**, or is “open SDK + hosted UI” acceptable (LangSmith/Braintrust)?  
2) Do you want task specs **YAML-first** (non-engineers can edit) or **Python-first** (max flexibility)?  
3) Which providers/models are must-run in v1 (exact list)? OpenAI + Anthropic + Google Gemini, plus any local models?  
4) How important is **CI integration** (PR gating) vs offline benchmarking?

If you answer those, I can give a concrete “pick X + build Y” plan (including a proposed task spec schema and a minimal leaderboard metric design) tailored to CineForge.
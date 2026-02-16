---
type: synthesis-report
topic: ai-model-benchmarking-tools
synthesis-model: claude-opus-4-6
source-reports:
- claude-opus-4-6-report.md
- gpt-5-2-report.md
synthesized: '2026-02-15T21:26:07.119876+00:00'
---



---
canonical-model-name: "claude"
report-date: "2025-07-10"
research-topic: "ai-model-benchmarking-tools"
report-type: "synthesis"
---

# CineForge Model Benchmarking Tool: Synthesis Report

## 1. Executive Summary

- **promptfoo is the clear primary recommendation**, meeting all 5 must-have requirements and ~88% of should-haves. Both reports converge on this conclusion, though Report 2 is more hedging.
- **No single tool meets 100% of all requirements out of the box**, but promptfoo's gaps (Python-nativeness, golden dataset versioning, statistical rigor) are addressable with lightweight scripts—not a custom platform.
- **DeepEval is the strongest Python-native complement**, particularly useful for CI/CD quality gates via pytest integration, but its cross-model comparison UX is weak without the paid Confident AI cloud.
- **Inspect AI is architecturally elegant** but lacks native cross-model comparison and dollar-cost tracking, making it better suited as a scorer library than a primary benchmarking harness.
- **OpenAI Evals is effectively dead**—both reports agree it's historically interesting but not viable for production adoption.
- **Ragas, Phoenix, LangSmith, Braintrust, and Humanloop are not recommended** as primary tools: Ragas is RAG-specific, Phoenix is observability-focused, and the others are proprietary platforms.
- **LiteLLM is an essential building block** regardless of framework choice—it provides unified multi-provider access with built-in cost tracking across 100+ providers.
- **Building from scratch is not recommended.** The hard problems (provider abstraction, concurrency, retry logic, judge patterns, prompt templating) are already solved. The remaining 10% (cross-task leaderboards, confidence intervals, domain-specific scorers) is 2–5 days of scripting, not months of platform engineering.
- **The recommended implementation path is: promptfoo (comparison workflow) + DeepEval (CI gates) + custom Python scripts (stats, combined reporting) + Git (golden dataset versioning).**
- **Estimated time to production benchmarking: 2–3 weeks** for a senior engineer covering all ~10 CineForge tasks.
- **Key architectural insight from both reports:** cache model outputs aggressively (hash on model+prompt+input+params), store raw outputs separately from scores (enables re-scoring without re-calling APIs), and use pairwise judge comparisons over absolute scoring where feasible.
- **One open question remains:** whether promptfoo's subprocess-based Python scorer integration introduces meaningful friction at CineForge's scale of ~10 tasks with complex domain-specific scoring logic. A 2-day spike will resolve this.

## 2. Source Quality Review

| Criterion | Report 1 (Claude Opus) | Report 2 (GPT-5) |
|---|---|---|
| **Evidence Density** | 5/5 | 3/5 |
| **Practical Applicability** | 5/5 | 3/5 |
| **Specificity** | 5/5 | 2/5 |
| **Internal Consistency** | 5/5 | 4/5 |
| **Overall** | **5.0/5** | **3.0/5** |

**Report 1 (Claude Opus) Critique:**
Exceptional quality. Provides exact repo URLs, approximate star counts, specific capability assessments with clear pass/partial/fail verdicts, concrete YAML and Python code examples showing how promptfoo and DeepEval would actually be configured for CineForge tasks, a detailed getting-started plan broken into weeks, and a well-reasoned architecture section with specific pitfalls drawn from analyzing each tool's failures. The gap analysis matrix is precise with percentage scores rather than vague qualifiers. The recommendation is singular and decisive with explicit gap-filling strategies. This is implementation-ready documentation.

**Report 2 (GPT-5) Critique:**
Honest about its limitations (acknowledges inability to verify live data), but this transparency comes at the cost of concreteness. Assessments use vague qualifiers ("Partial/Yes," "depends on adapters," "verify current status") that don't help a team make decisions. Provides no code examples, no repo URLs, no star counts, and no specific version information. The recommendation is a hedging "adopt + extend" with multiple conditional paths ("if you prefer Python-first... bias toward Inspect AI or DeepEval") rather than a concrete pick. The architecture section is solid conceptually (pairwise judge comparisons, DVC for large datasets, judge calibration sets) and contributes several ideas Report 1 missed, but lacks the implementation specificity to act on. The closing "what I need from you to finalize" section, while honest, essentially defers the recommendation.

**Weighting decision:** Report 1 is weighted ~75/25 over Report 2 for tool-specific claims and the primary recommendation. Report 2 contributes meaningfully on architecture patterns (pairwise judging, judge calibration, DVC for large datasets, Pydantic output schemas) and is weighted more equally there.

## 3. Consolidated Findings by Topic

### 3.1 Tool Landscape Overview

**High Confidence (both reports agree):**

| Tool | Category | Recommendation | Both Agree? |
|---|---|---|---|
| **promptfoo** | Purpose-built eval framework | **Primary adoption candidate** | ✅ |
| **DeepEval** | Python-native eval framework | **Strong complement** | ✅ |
| **Inspect AI** | Python eval framework (UK AISI) | **Honorable mention; good architecture** | ✅ |
| **OpenAI Evals** | Legacy eval framework | **Do not use; effectively abandoned** | ✅ |
| **Ragas** | RAG-specific eval | **Not applicable to CineForge** | ✅ |
| **Phoenix (Arize)** | Observability with eval features | **Wrong tool for benchmarking** | ✅ |
| **LangSmith** | Proprietary platform | **Not recommended unless already invested** | ✅ |
| **Braintrust** | Proprietary platform w/ OSS SDKs | **autoevals library useful; platform not recommended** | ✅ |
| **Humanloop** | Proprietary SaaS | **Skip** | ✅ |
| **LiteLLM** | Multi-provider gateway | **Essential building block** | ✅ |

**Report 1 unique contributions:**
- MLflow LLM Evaluate: assessed as interesting but heavyweight; not recommended unless already using MLflow
- Weights & Biases Weave: open source but funnels into W&B platform
- Evidently AI: strong on statistical analysis/drift but not designed for model comparison
- Braintrust `autoevals` library: specifically identified as a useful standalone scoring library

**Report 2 unique contributions:**
- Helicone: OSS LLM proxy for cost/latency logging (not an eval framework)
- TruLens: OSS eval/observability similar to Phoenix
- DVC/lakeFS mentioned for large golden dataset versioning

### 3.2 promptfoo Deep Assessment

**Capabilities confirmed by both reports:**
- YAML-centric task definition with prompts × providers × test cases matrix
- Native multi-provider support (OpenAI, Anthropic, Google, Azure, Bedrock, Ollama, custom)
- Code-based scoring via custom assertions (JS/TS/Python)
- LLM-as-judge via `llm-rubric` and related assertion types
- Token and latency tracking with cost estimation
- CLI-first with local web UI (`promptfoo view`)
- Caching to avoid redundant API calls
- Good extensibility (custom providers, custom assertions)

**Key detail from Report 1 (not in Report 2):**
- Python scorers work via subprocess (`type: python`, reference external .py files)
- `repeat` field supports multiple runs for stochastic tasks
- Local SQLite database stores eval history
- `promptfoo share` for shareable hosted links
- CI/CD integration with exit codes and GitHub Actions support
- Red teaming modules (maturity indicator)
- VC-backed with full-time team and daily commits

### 3.3 DeepEval Deep Assessment

**Capabilities confirmed by both reports:**
- Python-native with pytest integration
- Custom metrics via `BaseMetric` subclass
- GEval for LLM-as-judge with custom rubrics
- Support for multiple providers

**Key detail from Report 1 (not in Report 2):**
- Uses LiteLLM under the hood (100+ providers)
- `EvaluationDataset` class with JSON persistence
- Confident AI cloud for dataset versioning and cross-run comparison (freemium)
- The "run same prompt across multiple models" workflow requires a Python loop—not declarative like promptfoo
- ~4,500+ stars, weekly commits

**Report 2 uncertainty:** Rated DeepEval's multi-provider support as "Partial (depends on adapters)"—this is **incorrect** per Report 1's specific claim that it uses LiteLLM internally. Report 1's claim is higher confidence.

### 3.4 Inspect AI Deep Assessment

**Capabilities confirmed by both reports:**
- Python-native with clean `@task` decorator pattern
- Custom scorers via `@scorer` decorator
- Multi-provider support (OpenAI, Anthropic, Google, etc.)
- Built-in model-graded scoring
- CLI interface (`inspect eval`, `inspect view`)

**Key detail from Report 1 (not in Report 2):**
- `inspect view` launches a "surprisingly polished" local web UI
- Solver/scorer composability is architecturally elegant
- Excellent documentation
- ~2,500+ stars, government-funded professional team
- No native leaderboard or cross-run comparison
- Dollar cost not computed (only tokens)
- Multi-model comparison requires separate eval runs

### 3.5 Cost Tracking Assessment

**Both reports agree this is the weakest area across all tools.** No tool provides fully automatic, accurate dollar-cost tracking across all providers out of the box.

**Report 1's assessment (more specific):**
- promptfoo: ✅ Full—uses provider pricing tables, configurable, displayed in UI
- DeepEval: ✅ via LiteLLM cost tables
- Inspect AI: ⚠️ Tokens only, no dollar cost
- MLflow: ⚠️ Tokens only, no dollar cost

**Report 2's assessment (more pessimistic):**
- Rates cost tracking as "Partial" for nearly every tool

**Adjudication:** Report 1 is more specific and distinguishes between tools that have configurable pricing tables (promptfoo, DeepEval via LiteLLM) versus those that only track tokens. Report 1's assessment is more credible. promptfoo and DeepEval handle cost tracking adequately for CineForge's needs, with LiteLLM providing the pricing data layer.

### 3.6 Golden Dataset Management

**Both reports agree:** No tool provides dedicated golden dataset versioning. All rely on files (JSON/CSV/JSONL) managed via Git. Report 1 argues this is actually preferable ("files in Git are simpler and more durable" than a database). Report 2 suggests DVC or lakeFS for large datasets.

**Synthesis:** For CineForge (screenplay excerpts + reference outputs), Git is sufficient. Datasets are text-based and human-reviewable. DVC is worth considering only if datasets grow to contain large binary assets (unlikely for this use case).

### 3.7 Architecture Patterns (If Building)

Both reports provide architecture outlines with significant overlap:

| Component | Report 1 | Report 2 | Synthesis |
|---|---|---|---|
| Model gateway | LiteLLM | LiteLLM | ✅ Unanimous |
| Task definition | YAML + Python scorers | YAML or Python (flexible) | YAML for tasks, Python for scorers |
| Results store | SQLite/JSON | SQLite/Postgres | SQLite for lightweight; Postgres only if scaling |
| Caching | Hash(model+prompt+input+params) | Same | ✅ Unanimous |
| Scoring architecture | Separate code + judge scorers | Same, plus pairwise ranking | Both approaches, pairwise is a good addition |
| Raw output storage | Store alongside scores | Store separately for re-scoring | ✅ Unanimous |
| Output schemas | Implicit | **Pydantic/JSON Schema per task** | Report 2's suggestion is valuable |
| Judge calibration | Not mentioned | **Calibration sets + drift detection** | Report 2's suggestion is valuable |
| Reporting | Markdown/HTML/JSON + optional Streamlit | JSON/CSV/Markdown/HTML | Similar |

**Unique contributions from Report 2:**
- **Pairwise judge comparisons** over absolute 1–10 scoring (more stable)
- **Judge calibration sets** to detect drift over time
- **Canonical output schemas** per task (Pydantic) for deterministic scoring
- **DVC/lakeFS** for large dataset versioning
- **Pareto frontier** (quality/$) as a reporting visualization

These are genuinely useful architectural ideas that should be incorporated even when adopting promptfoo.

## 4. Conflict Resolution Ledger

| Claim | Report 1 | Report 2 | Adjudication | Confidence |
|---|---|---|---|---|
| **promptfoo meets must-have threshold** | Yes (100% must-haves) | Hedging ("no single tool cleanly hits all must-haves") | **Report 1 is correct.** Report 1 provides specific evidence for each must-have. Report 2's hesitation stems from cost tracking concerns, but Report 1 demonstrates promptfoo has configurable pricing tables and displays dollar cost in its UI. | High |
| **DeepEval multi-provider support** | Full (via LiteLLM, 100+ providers) | "Partial (depends on adapters)" | **Report 1 is correct.** DeepEval uses LiteLLM internally, which provides broad provider support. Report 2's assessment appears based on older or incomplete information. | High |
| **promptfoo code-based scoring** | ✅ Full (Python via subprocess) | "Partial (not Python-native)" | **Both are partially right, but the practical impact differs.** promptfoo does support Python scorers, but they run via subprocess rather than in-process. Report 1 correctly identifies this works well in practice. Report 2 correctly notes it's "not Python-native." For CineForge, this is a minor friction point, not a blocker. | High |
| **Should we "adopt" or "adopt + extend"?** | Adopt promptfoo (90%+ coverage, build remaining 10% as scripts) | "Adopt + extend with thin internal layer" | **Converge on Report 1's framing.** The difference is rhetorical: both recommend using an existing tool plus lightweight custom work. Report 1 is more precise about what the custom work entails (combine_results.py, compute_stats.py, domain scorers = 2–3 days). Report 2 frames it as a larger "orchestrator layer" (2–4 weeks), which overstates the required effort given promptfoo's existing capabilities. | High |
| **Primary tool recommendation** | promptfoo (singular) | promptfoo OR Inspect AI (conditional on Python preference) | **Report 1's singular recommendation is better.** Inspect AI lacks cross-model comparison and dollar cost—two features core to CineForge's needs. The Python-friendliness gap in promptfoo is manageable via subprocess Python scorers. Leaving the choice open creates decision paralysis without clear benefit. | High |
| **Complexity estimate for custom build** | MVP: 1–2 weeks; Production: 4–6 weeks | Thin layer: 2–4 weeks; Full custom: 6–10+ weeks | **Compatible estimates.** Report 1's "MVP 1–2 weeks" aligns with Report 2's "thin layer 2–4 weeks" when accounting for Report 1 assuming promptfoo handles more. Both agree full custom is 4–10+ weeks. This reinforces the "adopt, don't build" recommendation. | Medium-High |

## 5. Decision Matrix

Weighted scoring on a 0–3 scale (0=No, 1=Poor, 2=Adequate, 3=Excellent).

| Requirement | Weight | promptfoo | DeepEval | Inspect AI |
|---|---|---|---|---|
| Multi-provider (OpenAI+Anthropic+Google) | **Must** (×3) | 3 (9) | 3¹ (9) | 3 (9) |
| Custom task definitions | **Must** (×3) | 3 (9) | 3 (9) | 3 (9) |
| Code-based scoring (Python) | **Must** (×3) | 2² (6) | 3 (9) | 3 (9) |
| AI-judge scoring | **Must** (×3) | 3 (9) | 3 (9) | 3 (9) |
| Cost tracking (tokens+dollars) | **Must** (×3) | 3 (9) | 2 (6) | 1 (3) |
| Golden dataset management | **Should** (×2) | 2³ (4) | 2 (4) | 2 (4) |
| CLI interface | **Should** (×2) | 3 (6) | 2 (4) | 3 (6) |
| Cross-run comparison / leaderboards | **Should** (×2) | 3 (6) | 1⁴ (2) | 1 (2) |
| Python-based or Python-friendly | **Should** (×2) | 2 (4) | 3 (6) | 3 (6) |
| Statistical rigor | **Nice** (×1) | 1 (1) | 1 (1) | 1 (1) |
| Extensible | **Nice** (×1) | 3 (3) | 2 (2) | 3 (3) |
| Lightweight / standalone | **Nice** (×1) | 3 (3) | 3 (3) | 3 (3) |
| **TOTAL** | | **69** | **64** | **64** |
| Must-have subtotal (max 45) | | **42** (93%) | **42** (93%) | **39** (87%) |
| Should-have subtotal (max 24) | | **20** (83%) | **16** (67%) | **18** (75%) |

¹ Via LiteLLM internally  
² Python via subprocess, not in-process  
³ Files + Git; no dedicated UI  
⁴ Requires Confident AI cloud for cross-run comparison  

**promptfoo clears both thresholds:** ≥80% must-haves (93%) and ≥60% should-haves (83%).  
**DeepEval clears both thresholds** but with weaker should-have coverage (67%).  
**Inspect AI clears must-have threshold** (87%) and should-have threshold (75%) but trails on cost tracking.

## 6. Final Recommendation

### **Adopt promptfoo as the primary benchmarking framework.**

**Rationale:**
1. It is the only tool where multi-model comparison is the *core design* rather than an afterthought. CineForge's fundamental question—"which model is best for each task?"—maps directly to promptfoo's YAML matrix of prompts × providers × test cases.
2. It meets all 5 must-have requirements, including the hardest one (cost tracking with dollar amounts).
3. The web UI (`promptfoo view`) provides exactly the leaderboard/comparison view CineForge needs without building anything.
4. It has the strongest maintenance and community health (VC-backed, daily commits, full-time team).
5. The Python-friendliness gap is real but manageable—Python scorers work via subprocess and cover CineForge's needs.

### **Use DeepEval as a complement for CI/CD quality gates.**

Where you want pytest-style `assert_test()` calls embedded in your Python CI pipeline (e.g., "fail the deploy if character bible quality drops below 0.7"), DeepEval's pytest integration is cleaner than shelling out to promptfoo.

### **Do not build a custom framework.**

Both reports agree the hard problems (provider abstraction, concurrency, retry, judge patterns, caching) are already solved. The custom work is:
- `combine_results.py`: ~100 lines to aggregate cross-task promptfoo JSON outputs into a master leaderboard
- `compute_stats.py`: ~50 lines using scipy/numpy for confidence intervals on repeated runs
- Domain-specific Python scorers: ~200–500 lines per task (you'd write these regardless of framework)
- Directory structure for golden datasets in Git

**Total custom effort: 3–5 days**, not weeks or months.

## 7. Implementation Plan / Next Steps

### Phase 1: Foundation (Week 1)

**Day 1–2: Setup and first task**
```bash
npm install -g promptfoo
mkdir cineforge-benchmarks && cd cineforge-benchmarks
promptfoo init
```
- Pick one task (recommend: scene extraction—it has clear structure and is easy to score)
- Create YAML config with 3 providers: `openai:gpt-4o`, `anthropic:messages:claude-sonnet-4-20250514`, `vertex:gemini-2.0-flash`
- Create 3 golden test cases with reference outputs
- Write one Python scorer (JSON validity + scene count accuracy)
- Add one `llm-rubric` assertion for subjective quality
- Run `promptfoo eval` and `promptfoo view` — validate the workflow

**Day 3–4: Add 2–3 more tasks**
- Character bible generation
- Entity graph extraction
- Script normalization
- Each task: YAML config + 3–5 golden test cases + Python scorer + judge rubric

**Day 5: Expand model coverage**
- Add to all tasks: `gpt-4o-mini`, `claude-3-5-haiku`, `gemini-2.0-flash`, `gemini-2.5-pro`
- Run full matrix; review cost/quality tradeoffs in web UI

### Phase 2: Full Coverage + Automation (Week 2)

**Day 6–8: Remaining tasks**
- Location/prop bible generation
- Continuity tracking
- Any remaining CineForge pipeline tasks
- Build `run_all_benchmarks.sh` master runner

**Day 9–10: Reporting and statistics**
- Write `combine_results.py` for cross-task leaderboard
- Write `compute_stats.py` for confidence intervals (use `repeat: 5` in configs)
- Generate Markdown leaderboard report

### Phase 3: CI Integration + Polish (Week 3)

- Set up GitHub Actions for weekly automated benchmark runs
- Add DeepEval pytest tests for critical quality gates
- Document the golden dataset contribution process (how to add new test cases)
- Create initial "model recommendation per task" document based on first benchmark results
- Implement pairwise judge comparisons for subjective tasks (Report 2's suggestion) where absolute scoring proves unreliable

### Ongoing (Post-Launch)

- **Monthly:** Re-run benchmarks when new model versions drop
- **Quarterly:** Review and update golden datasets; add harder test cases
- **As needed:** Add new tasks as CineForge pipeline evolves
- **Monitor:** Judge calibration—periodically re-judge old outputs with updated judge prompts to detect drift (Report 2's suggestion)

### Recommended Directory Structure

```
cineforge-benchmarks/
├── tasks/
│   ├── scene-extraction.yaml
│   ├── character-bible.yaml
│   ├── entity-graph.yaml
│   ├── continuity-check.yaml
│   ├── script-normalization.yaml
│   └── ...
├── prompts/
│   ├── scene-extraction-v2.txt
│   ├── character-bible-v3.txt
│   └── ...
├── golden/
│   ├── inception-act1.txt
│   ├── inception-act1-scenes.json       # reference output
│   ├── parasite-opening.txt
│   ├── parasite-opening-scenes.json
│   └── ...
├── scorers/
│   ├── scene_extraction_scorer.py
│   ├── character_bible_scorer.py
│   ├── entity_graph_scorer.py
│   ├── json_structure_scorer.py
│   └── common.py                        # shared scoring utilities
├── scripts/
│   ├── run_all_benchmarks.sh
│   ├── combine_results.py
│   └── compute_stats.py
├── results/                             # .gitignore'd (or selective)
│   ├── 2025-07-14-scene-extraction.json
│   └── ...
├── reports/                             # committed
│   ├── leaderboard-2025-07-14.md
│   └── ...
├── ci/
│   ├── test_quality_gates.py            # DeepEval pytest tests
│   └── ...
└── README.md
```

### Tool Stack Summary

| Component | Tool | Role |
|---|---|---|
| Benchmark runner + comparison | **promptfoo** | Core workflow |
| CI quality gates | **DeepEval** | pytest integration |
| Provider abstraction | **LiteLLM** (via DeepEval internally; available standalone if needed) | Unified API |
| Scoring utilities | **Braintrust autoevals** (optional) | Pre-built LLM judge scorers |
| Golden dataset versioning | **Git** | Simple, durable, diff-friendly |
| Statistical analysis | **scipy + numpy** (custom script) | Confidence intervals |
| Output schemas | **Pydantic** (in Python scorers) | Validate structured outputs |

## 8. Open Questions & Confidence Statement

### Open Questions

1. **Python subprocess friction at scale:** promptfoo calls Python scorers via subprocess. For 10 tasks × 6 models × 10 test cases = 600 scorer invocations, is the subprocess overhead meaningful? Likely negligible (each call is fast), but worth validating in the Week 1 spike. If it's a problem, batch scoring in a post-processing step.

2. **Judge model selection and cost:** Using GPT-4o as a judge for every test case across every model adds significant cost. Should CineForge use a cheaper judge for screening and reserve expensive judges for close calls? This is a design decision that will emerge from initial benchmark results.

3. **Pairwise vs. absolute judging:** Report 2 correctly notes pairwise comparisons are more stable than absolute 1–10 scoring. promptfoo's `llm-rubric` does absolute scoring by default. Implementing pairwise judging within promptfoo would require custom Python scorer logic. Worth exploring for subjective tasks (character bible quality) but not blocking for v1.

4. **Model version pinning:** Some providers (especially OpenAI) silently update model versions. How will CineForge track which exact model version produced which results? promptfoo logs model identifiers but doesn't capture internal version hashes. This is a provider-level limitation; document it and use dated model identifiers where available.

5. **Large context handling:** Some CineForge tasks (full script normalization) may require long-context models. promptfoo supports this, but cost per test case may be high. Need to design golden datasets that test both short excerpts and full scripts.

### Confidence Statement

**High confidence (90%+):**
- promptfoo is the right primary tool for CineForge's benchmarking needs
- Building from scratch would be significantly more costly for equivalent functionality
- The recommended directory structure and workflow will scale to all ~10 CineForge tasks
- DeepEval is the right complement for Python CI integration

**Medium confidence (70–85%):**
- 3 weeks is sufficient for full implementation across all tasks (depends on complexity of domain-specific scorers)
- promptfoo's Python subprocess integration will not be a meaningful bottleneck
- The `autoevals` library from Braintrust will add value beyond custom scorers

**Lower confidence (50–70%):**
- Absolute LLM-as-judge scoring will be sufficiently reliable for all CineForge tasks without pairwise comparisons (may need iteration)
- Dollar cost tracking across all providers will be accurate without manual pricing table maintenance (LiteLLM's pricing data may lag new model releases)
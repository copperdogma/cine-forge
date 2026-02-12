# Long Document AI Editing Research - COMBINED

20260212: Created.

This document is a combined report of the following research reports:
- [Codex Research Report](codex-research-report.md)
- [ChatGPT 5.2 Research Report](gpt5-2-research-report.md)
- [Grok 4.1 Research Report](grok4-1-research-report.md)
- [Opus 4.6 Research Report](opus4-6-research-report.md)
- [Gemini 3 Research Report](gemini3-research-report.md)

They were all given to Opus 4.6 to be synthesized into this report, using this prompt: [Opus 4.6 Synthesis Prompt](opus4-6-synthesis-prompt.md)


# CineForge Story 004 — Long-Document Screenplay Normalization
## Consolidated Research Synthesis & Architecture Recommendation
**Date:** 2026-02-12  
**Status:** Implementation-ready  
**Sources:** 5 independent research reports (Codex, GPT-5.2, Grok 4.1, Opus 4.6, Gemini 3)

---

## 1. Executive Summary

- **The binding constraint for full-script normalization in Feb 2026 is max output tokens (32K–128K), not context windows (200K–1M+).** Only GPT-5/5.2 and possibly Opus 4.6 can regenerate a full 45K-token screenplay in one pass; all other models require chunking or edit-list strategies for long scripts.
- **All five reports converge on a hybrid architecture** that routes screenplay-like input through edit-list/patch cleanup and prose/notes through scene-boundary chunked conversion. No report recommends monolithic single-pass as the primary strategy for production.
- **Edit-list/patch is 31–86% cheaper and ~79% faster than full regeneration** for screenplay cleanup, with mechanical failure rates of 6–50% that drop below 5% with fuzzy matching + retry loops. These numbers are grounded in Aider benchmarks, the JSON Whisperer paper, and the oh-my-pi project.
- **Fountain is the unanimous canonical format choice**, with `fountain-tools` (wildwinter) as the recommended parser and `screenplain` for FDX/PDF export. No dissenting view across any report.
- **Scene-boundary chunking with 300–500 token overlap and a compressed running metadata document (~800–1000 tokens)** is the proven coherence strategy. Temperature must be 0.0–0.2 for normalization consistency.
- **Structured outputs (JSON Schema) are GA across all major providers** and should be used for QA violation lists, edit-list schemas, and metadata extraction — not for raw screenplay text output.
- **Prompt caching is a major cost lever** (50–90% savings on repeated prefixes): design prompts with stable style-guide + schema prefix and variable chunk text appended last.
- **Provider-native edit tools exist** — OpenAI `apply_patch` and Anthropic text editor tool — and formalize the patch-first pattern with built-in failure detection. Use where available; fall back to a custom `str_replace` + fuzzy-match harness.
- **Cost per screenplay: $0.03–$0.83** depending on model and approach, with Gemini 2.5 Flash and GPT-5 Mini offering the best cost-quality tradeoff for volume. Claude Sonnet 4.5 is the premium low-variance option.
- **v1 should ship this sprint.** The existing CineForge baseline (single-pass short / edit-list long screenplay / chunked prose / QA pass) is architecturally correct; the upgrade path is better tooling, scene-native chunking, deterministic Fountain validation, and structured retry/repair loops.
- **v2 targets a screenplay IR (AST/JSON)** with JSON Patch (RFC 6902) editing and deterministic Fountain rendering, plus DSPy prompt optimization and optional two-model architect/applier splits.

---

## 2. Source Quality Review

| Report | Evidence Density (0–5) | Practical Applicability (0–5) | Specificity (0–5) | Internal Consistency (0–5) | **Composite** |
|---|---|---|---|---|---|
| **Codex** | 2 | 4 | 3 | 5 | **3.5** |
| **GPT-5.2** | 5 | 5 | 5 | 5 | **5.0** |
| **Grok 4.1** | 3 | 3 | 3 | 4 | **3.3** |
| **Opus 4.6** | 5 | 5 | 5 | 5 | **5.0** |
| **Gemini 3** | 3 | 2 | 3 | 3 | **2.8** |

### Commentary

**Codex (3.5/5).** Short, internally consistent, and practical. Functions as a clean summary of the hybrid strategy already implemented in CineForge's baseline. Low evidence density — no citations, no benchmarks, no cost numbers. Useful as a sanity check but contributes no new data. No quality issues; used in full.

**GPT-5.2 (5.0/5).** The strongest report. Every claim is grounded in specific API documentation with inline citations. Uniquely contributes: (a) provider-native patch tools (`apply_patch`, text editor tool) as first-class primitives, (b) the distinction between patch-first (screenplay cleanup) vs. scene-generation (prose conversion) as fundamentally different operations, (c) concrete prompt caching guidance per provider, (d) detailed cost tables with derivation, (e) the v2 screenplay IR concept with JSON Patch. Internals are fully consistent. Used as the primary architectural source.

**Grok 4.1 (3.3/5).** Covers all required topics with a decision matrix and source list. Weaknesses: some claims are vague ("0% on internal benchmarks" for targeted edits — unverifiable), model names are slightly off (GPT-5.3-Codex, which other reports don't corroborate as a single model name), and the cost ranges are wide without derivation. The "80–90% coherence in production" claim for LangChain/LlamaIndex is unsourced. Useful for its breadth and risk section. Claims used only where corroborated by other reports.

**Opus 4.6 (5.0/5).** Exceptionally detailed and quantitative. Uniquely contributes: (a) the Aider/oh-my-pi/EDIT-Bench benchmark data on edit-list failure rates (6–50%), (b) the two-model Cursor architecture as a v2 pattern, (c) detailed fuzzy-matching pipeline spec (exact → whitespace-normalized → SequenceMatcher > 0.85), (d) concrete chunk-level prompt window arithmetic (5,700 tokens per chunk), (e) the Instructor library as the production validation layer, (f) specific model throughput numbers (Gemini Flash ~250 t/s, GPT-4.1 ~80–100 t/s, Claude Sonnet ~77 t/s). One caveat: Opus 4.6's own 128K output claim is flagged as "third-party only." Used as the primary implementation source.

**Gemini 3 (2.8/5).** The longest report but lowest signal-to-noise ratio. Significant quality issues:
- **Buzzword inflation:** Terms like "AI Shepherd," "Composable Intelligence," "Universal Semantic Layer," "Economic Page" are either jargon for simple concepts or sourced from marketing/blog content rather than technical documentation.
- **Unverifiable claims:** "GPT-5.3 Garlic" with "Perfect Recall" and "EPTE" — sourced from a single speculative blog post (wavespeed.ai), not OpenAI documentation. The pricing table for Claude 4.6 ($10/$37.50) contradicts the Opus 4.6 report ($5/$25) and the GPT-5.2 report ($3/$15 for Sonnet).
- **Overreach:** Recommending LangGraph, STED metrics, "Character Bibles," MCP integration, and mobile-first formatting validators in a v1 checklist exceeds what's realistic for a normalization pipeline MVP.
- **Useful portions retained:** The JSON Whisperer / EASE citation (corroborated by Opus 4.6 and GPT-5.2), Fountain tooling section, and the general scene-parallel architecture concept. The "7-day checklist" and STED/regulatory sections are discarded as non-actionable for Story 004.

---

## 3. Consolidated Findings by Topic

### 3.1 API & Model Capabilities

**Verified model landscape (Feb 2026):**

| Model | Context | Max Output | Structured Output | Best Use in Pipeline |
|---|---|---|---|---|
| GPT-5 / 5.2 | 400K | 128K | GA | Full regen (short-to-medium scripts), edit-list gen |
| GPT-5 Mini | 400K | 128K | GA | Budget full-regen, QA pass |
| GPT-4.1 | 1M | 32K | GA | Large-context read → compact edits/diagnostics |
| GPT-4.1 Mini | 1M | 32K | GA | Edit-list generation (output stays compact) |
| Claude Sonnet 4.5 | 200K (1M beta) | 64K | GA | Premium low-variance normalization |
| Claude Opus 4.6 | 200K (1M beta) | 128K* | GA | *Output cap unverified from primary docs* |
| Gemini 2.5 Pro | 1M | 65K | GA | Context caching; tight-fit regen |
| Gemini 2.5 Flash | 1M | 65K | GA | Best $/quality ratio for volume |

**Key operational facts:**
- Structured outputs (JSON Schema, strict mode) are GA across all three providers but have documented failure modes: repetition under certain schema designs (Gemini), subset JSON Schema support (OpenAI), and strict unique-match requirements (Anthropic text editor).
- Streaming (SSE) is universal and essential for long outputs — both for UX and for early detection of malformed output or runaway repetition.
- Prompt caching: OpenAI automatic (prefix-match, ≥1024 tokens), Anthropic explicit (`cache_control` breakpoints), Gemini implicit + explicit (TTL). All three reward prompt designs where stable content (style guide, schema, tools) comes first.
- Silent truncation is a hazard: OpenAI defaults to `truncation: disabled` (fail-loud, preferred). Always monitor `finish_reason` / `stop_reason` for `max_tokens`.
- "Lost in the middle" attention degradation is empirically confirmed (Stanford/Berkeley) and directly relevant — place formatting rules at both start and end of system prompt.

### 3.2 Frameworks & Libraries

**Recommended minimal stack (all reports agree):**

| Library | Role | Why |
|---|---|---|
| `fountain-tools` (wildwinter) | Fountain parse/serialize + FDX read | Best Python parser, incremental, multi-format |
| `screenplain` | FDX/PDF export | Mature, CLI + library |
| `instructor` | Pydantic schema validation + auto-retry | Provider-agnostic, 3M+ monthly downloads, explicit retry |
| `langchain-text-splitters` | Scene-aware chunking | `RecursiveCharacterTextSplitter` with custom separators |
| `difflib` (stdlib) | Fuzzy matching for edit-list application | `SequenceMatcher` with 0.85 threshold |
| `xml.etree.ElementTree` (stdlib) | FDX XML parsing | Direct, no extra dependency |

**Evaluated and deferred:**
- **LangGraph / LangChain orchestration:** Three reports mention it; one (Gemini 3) over-indexes on it. For a pipeline that is fundamentally sequential (parse → normalize → validate → repair), full graph orchestration adds complexity without proportional benefit. Defer to v2 if pipeline branching becomes genuinely complex.
- **DSPy:** Opus 4.6 and Gemini 3 both flag its prompt optimization (MIPROv2, 25–65% improvement). High potential but requires a gold-standard eval set of 20–50 normalized screenplays. Defer to v2.
- **Microsoft Guidance / constrained decoding:** Only useful for self-hosted models. CineForge uses cloud APIs → skip.
- **LlamaIndex:** RAG-oriented, not document transformation. Skip for Story 004.
- **Diff Match Patch (Google):** Repo is archived (read-only). Maintenance risk. Use `difflib` instead.

### 3.3 Chunking & Coherence Strategies

**Consensus across all five reports:**

1. **Scene-native segmentation beats token-native chunking.** Split at `INT.`/`EXT.` scene headings, not at fixed token counts. Fountain's explicit syntax makes this deterministic even on messy input. Group 2–3 short scenes per chunk; split very long scenes at beat transitions. Target: 2,000–4,000 tokens per chunk.

2. **Overlap of 300–500 tokens** (tail of previous scene) provides boundary context. Mark as read-only (`[PREVIOUS CONTEXT — DO NOT MODIFY]`). Beyond 20% overlap: diminishing returns with increased cost.

3. **Compressed running metadata document** (~800–1,000 tokens) carries across all chunks:
   ```json
   {
     "characters": ["SARAH", "DAVID (V.O.)"],
     "locations": ["INT. APARTMENT - NIGHT", "EXT. ROOFTOP - DAY"],
     "style_notes": "CUT TO: transitions, no FADE TO:",
     "narrative_summary": "Sarah discovered the letter; David called from overseas..."
   }
   ```
   Update after each chunk via LLM compression. This prevents unbounded context growth that kills pure Refine chains.

4. **Prompt window per chunk:** System prompt (~1,500 tokens) + running metadata (~800 tokens) + previous chunk tail (~400 tokens) + current chunk (~3,000 tokens) = ~5,700 tokens input. Well within any model's capacity.

5. **Temperature 0.0** for all normalization calls. No creative variation desired.

6. **Deterministic seam checks after reassembly:** duplicate headings, dropped transitions, character name casing drift, orphaned dialogue blocks.

### 3.4 Edit-List vs. Full Regeneration

**When to use which (consensus):**

| Input Type | Edit Density | Recommended Approach |
|---|---|---|
| Screenplay, minor cleanup | <20% lines changed | Edit-list (patch) |
| Screenplay, major reformatting | 20–40% lines changed | Edit-list, with fallback to chunked regen for failed sections |
| Screenplay, heavy rewrite | >40% lines changed | Chunked regeneration |
| Prose/notes → screenplay | 100% (new content) | Chunked scene-generation |
| Short doc (<5K tokens), any type | Any | Single-pass regeneration |

**Edit-list failure modes and mitigations (from Opus 4.6 / GPT-5.2):**
- **Search-block mismatch:** LLM can't perfectly reproduce the text to find. Mitigation: layered fuzzy matching (exact → whitespace-normalized → `SequenceMatcher` ratio > 0.85).
- **Non-unique anchors:** Repeated text like `CUT TO:` matches multiple locations. Mitigation: include scene ID or surrounding context in search block; Anthropic explicitly warns about this.
- **Patch ordering:** If batching patches, ordering matters (serial application with rolling context). Mitigation: enforce sequential application; rebase on failure.
- **Line number hallucination:** Models fabricate line numbers. Mitigation: use search/replace blocks (not line numbers). Use `<<<<<<< SEARCH` / `>>>>>>> REPLACE` delimiters (Aider format, proven).

**Edit format recommendation (Opus 4.6):** Search/replace blocks, not unified diff, not line numbers, not JSON Patch (that's v2). The Aider format has the broadest model compatibility and the most benchmark data.

### 3.5 Screenplay-Specific Tooling

**Unanimous across reports:**
- **Fountain** is the canonical format target. Plain text, parseable, git-friendly, developer-friendly.
- **Limitation:** Fountain omits production features (revision marks, locked pages). CineForge should target *writer-stage* canonicalization for v1 and defer production-stage features.
- **No standalone screenplay format validator exists.** Validation is implicit: if `fountain-tools` parses it successfully with >80% element coverage, it's valid. Build a custom lint layer on top for: orphaned dialogue, malformed scene headings, inconsistent character name casing, missing title page.
- **FDX interop:** `xml.etree.ElementTree` for parsing + `screenplain` for FDX export. Map `<Paragraph Type="...">` to Fountain elements directly.

### 3.6 Token Economics

**Baseline sizing:** ~100-page screenplay ≈ 25K–30K words ≈ 33K–45K tokens.

**Cost per screenplay (representative, Feb 2026):**

| Approach | Gemini 2.5 Flash | GPT-5 Mini | Claude Sonnet 4.5 |
|---|---|---|---|
| Single-pass (35K in / 35K out) | ~$0.03 | ~$0.08 | ~$0.64 |
| Chunked conversion + QA (80K in / 50K out) | ~$0.07 | ~$0.13 | ~$1.02 |
| Edit-list + QA + 1 repair (80K in / 8K out) | ~$0.04 | ~$0.04 | ~$0.32 |

**Cost levers:**
- Prompt caching: 50–90% reduction on repeated prefixes (system prompt, Fountain rules, schema).
- Batch API: 50% discount for async (24-hour) processing.
- Combined (batch + caching): processing 100 screenplays via Gemini Flash costs ~$1–$7 total.

**Avoid reasoning models** (o1/o3/o4-mini) for normalization — they bill hidden "thinking" tokens as output, inflating costs 3–10× for a formatting task that doesn't need chain-of-thought.

---

## 4. Conflict Resolution Ledger

| Claim | Conflicting Views | Final Adjudication | Confidence |
|---|---|---|---|
| **Claude Opus 4.6 max output** | Opus 4.6 report: "128K, third-party claim only." GPT-5.2 report: "128K." Gemini 3 report: "128K." | Treat as **128K unverified**. Code should check `finish_reason` and fall back to chunking if truncated. Do not depend on 128K for architecture decisions. | Medium |
| **Gemini 3 Pro/Flash availability** | Grok 4.1 cites "Gemini 3 Pro Preview, 200K+." GPT-5.2 cites "Gemini 3 Pro Preview, 1M/65K." Opus 4.6 focuses on Gemini 2.5 Flash/Pro. | Use **Gemini 2.5 Flash/Pro** as the verified production models. Gemini 3 Pro Preview may exist but is not the cost-optimal choice. Opus 4.6's pricing and throughput data for 2.5 Flash is most concrete. | High |
| **"GPT-5.3 Garlic" / "GPT-5.3-Codex"** | Gemini 3 report cites "GPT-5.3 Garlic" with "Perfect Recall" from a speculative blog. Grok 4.1 cites "GPT-5.3-Codex." GPT-5.2 report references GPT-5.2 with specific API docs. | **Discard "GPT-5.3 Garlic" claims** — sourced from a single unverifiable blog, not OpenAI documentation. Use GPT-5.2 / GPT-5 Mini / GPT-4.1 as the verified OpenAI lineup. | High |
| **Claude 4.6 pricing** | Gemini 3: $10/$37.50 per MTok. GPT-5.2: $3/$15 (Sonnet 4.5), $5/$25 (Opus 4.6 implied by third-party). Opus 4.6: $5/$25 (Opus 4.6). | Gemini 3's pricing is an outlier, likely confusing premium long-context beta rates with standard. Use **Sonnet 4.5: $3/$15** and **Opus 4.6: $5/$25** as working estimates, but verify at runtime. | Medium |
| **Coherence ceiling** | Gemini 3: "~10,000 tokens" (citing LongGenBench). Opus 4.6: "superlinear degradation above ~30K." GPT-5.2: "lost in the middle" is non-uniform but not quantified as a hard ceiling. | Not a hard ceiling — it's a gradient. Practical guidance: **don't trust single-pass regeneration above ~30K output tokens** for format-sensitive tasks. Below that, single-pass is viable with QA. Above, chunk. | High |
| **Edit-list mechanical failure rates** | Opus 4.6: "6–50% depending on model and format." Grok 4.1: "0–9% on internal benchmarks." GPT-5.2: implicit (documents failure modes but no aggregate rate). | The 6–50% range (Opus 4.6, sourced from Aider/oh-my-pi/EDIT-Bench) is the most credible because it comes from named external benchmarks. Grok's "0%" is likely cherry-picked. With fuzzy matching + retry: **<5% residual failure rate** is achievable. | High |
| **LangGraph as essential framework** | Gemini 3: "the premier choice for production-grade agentic workflows." GPT-5.2: mentions LangChain text-splitters only. Opus 4.6: recommends minimal stack, no orchestration framework. | **Skip LangGraph for v1.** The normalization pipeline is sequential, not a DAG with branching. Use Python functions and simple orchestration. Reconsider if pipeline complexity genuinely requires graph-based state management. | High |
| **Overlap percentage** | Grok 4.1: "10–30%." GPT-5.2: "last 1–2 blocks." Opus 4.6: "300–500 tokens, 15–20% sweet spot." Gemini 3: "10–15%." | **300–500 tokens** (Opus 4.6) is the most concrete and actionable. This typically corresponds to 10–20% depending on chunk size. Use absolute tokens, not percentages, to avoid chunk-size dependency. | High |
| **Instructor vs. other validation** | Opus 4.6: Instructor is "highest-value integration." GPT-5.2: uses provider-native structured outputs. Gemini 3: STED framework. | **Use Instructor for v1** — it's provider-agnostic, handles retries, and integrates Pydantic validation. Provider-native structured outputs are complementary (use both). STED is an evaluation metric, not a validation tool — discard Gemini 3's framing. | High |

---

## 5. Decision Matrix

Scoring 1–5 (5 = best). Weights reflect CineForge's production pipeline priorities: correctness and repairability dominate over cost and speed.

| Criterion | Weight | A: Mostly Single-Pass | B: Hybrid (Patch + Chunked + Single) | C: Fully Chunked Multi-Pass |
|---|---|---|---|---|
| **Format fidelity / drift resistance** | 0.30 | 2 — content loss >30K tokens; "laziness" documented | 5 — edit-list preserves unchanged text; chunked conversion at scene boundaries | 4 — good but more seam artifacts than B |
| **Repairability / observable failures** | 0.20 | 2 — monolithic output; failures are global | 5 — patch failures are detectable and retryable per-edit; QA → structured fix list | 4 — chunk-level retry possible but heavier |
| **Cross-chunk coherence** | 0.15 | 4 — no chunks, no seams (when it works) | 4 — running metadata + overlap; deterministic seam checks | 3 — more chunks = more seam risk |
| **Cost efficiency** | 0.15 | 3 — full output even for minor cleanup | 5 — edit-list is 70–86% cheaper for cleanup; single-pass for short docs | 2 — redundant context across many chunks |
| **Latency** | 0.10 | 3 — 3–13 min for full regen | 4 — edit-list: ~1 min; chunked: parallelizable | 3 — sequential chunking is slow without parallelism |
| **Implementation complexity** | 0.10 | 5 — simplest, one call | 3 — classifier + two paths + patch harness + validator | 3 — chunking + overlap + metadata carry-forward |
| **Weighted total** | **1.00** | **2.80** | **4.65** | **3.35** |

**Approach B (Hybrid) wins decisively.** This aligns with the recommendations of all five reports and with CineForge's existing baseline architecture.

---

## 6. Final Architecture Recommendation

### v1: Ship This Sprint

**Pipeline stages (concrete, mapped to CineForge codebase):**

```
INPUT
  │
  ├─ [1] Input Classifier (deterministic + cheap LLM fallback)
  │     Detect: screenplay-like vs prose/notes vs FDX
  │     If Fountain-parseable with >80% element coverage → screenplay path
  │     If valid FDX XML → convert to Fountain → screenplay path
  │     Otherwise → prose/notes path
  │
  ├─ [2a] SCREENPLAY PATH: Patch-First Normalization
  │     Short (<5K tokens) → single-pass normalize
  │     Long (≥5K tokens) → edit-list generation (SEARCH/REPLACE blocks)
  │       → fuzzy apply (exact → whitespace-norm → SequenceMatcher >0.85)
  │       → fail-loud on ambiguity; retry with error context (max 3)
  │       → fallback: chunked regen for failed sections
  │
  ├─ [2b] PROSE/NOTES PATH: Scene-Chunked Conversion
  │     Scene-boundary detection (regex + LLM fallback for proto-scenes)
  │     Chunk at scenes (2–4K tokens each)
  │     Per-chunk: convert to Fountain with:
  │       - system prompt (Fountain rules + 2 few-shot examples, cached)
  │       - running metadata (~800 tokens, updated after each chunk)
  │       - previous chunk tail (~400 tokens, read-only)
  │     Reassemble
  │
  ├─ [3] Deterministic Fountain Normalizer (post-LLM, no AI)
  │     Force scene headings uppercase
  │     Force character names uppercase
  │     Ensure blank lines before scene headings and character cues
  │     Strip trailing whitespace, normalize line endings to \n
  │     Validate: fountain-tools parse succeeds
  │
  ├─ [4] QA Pass (LLM)
  │     Send normalized output + original input
  │     Model returns structured JSON: list of issues + suggested fix ops
  │     Using Instructor + Pydantic schema for validation
  │     If critical issues: targeted repair pass (patch ops, not full regen)
  │     Cap retries at 3; if unresolved → needs_review flag
  │
  └─ [5] Output
        Canonical .fountain text
        Per-call cost/token metadata attached
        QA results attached to artifact audit metadata
```

**v1 model choices:**
- **Default:** Gemini 2.5 Flash — best $/quality ratio ($0.15/$0.60 per MTok, ~250 t/s)
- **Edit-list generation:** GPT-4.1 Mini — large context (1M), compact output fits 32K cap
- **QA pass:** GPT-5 Mini — cheapest per-token for short structured output
- **Premium fallback:** Claude Sonnet 4.5 — lowest variance, highest instruction-following

**v1 library stack:**
- `fountain-tools` — parse/serialize Fountain + FDX read
- `screenplain` — FDX/PDF export
- `instructor` — Pydantic validation + auto-retry across providers
- `langchain-text-splitters` — `RecursiveCharacterTextSplitter` with `["\nINT.", "\nEXT.", "\nINT./EXT.", "\nI/E", "\n\n\n"]`
- `difflib` — fuzzy matching for edit application
- `xml.etree.ElementTree` — FDX XML parsing

**v1 key parameters:**
- Edit format: `<<<<<<< SEARCH` / `>>>>>>> REPLACE` (Aider-proven)
- Fuzzy match threshold: `SequenceMatcher` ratio > 0.85
- Chunk target: 2,000–4,000 tokens
- Overlap: 400 tokens (read-only previous context)
- Running metadata cap: 1,000 tokens (LLM-compressed after each chunk)
- Temperature: 0.0
- Max retries per edit: 3
- Max QA repair passes: 3
- `finish_reason` monitoring: auto-reroute to chunked on `max_tokens`

### v2: Next 1–2 Milestones

1. **Screenplay IR (AST/JSON).** Represent screenplay as structured JSON: `scenes[]`, each with heading, action blocks, dialogue blocks, transitions. Edit via JSON Patch (RFC 6902). Render to Fountain deterministically. This makes validation structural (not whitespace-dependent) and patch operations unambiguous.

2. **DSPy prompt optimization.** Compile normalization prompts against a gold-standard eval set of 20–50 correctly normalized screenplays. MIPROv2 for automated few-shot example selection.

3. **Two-model architect/applier.** Frontier model generates semantic diffs (what should change and why); fine-tuned fast model applies them at high throughput. Modeled after Cursor's architecture.

4. **Hashline edit format.** Tag every line with 2-character content hashes for unambiguous edit targeting. The oh-my-pi benchmark shows up to 10× improvement for weaker models.

5. **Parallel chunk processing.** Run scene chunks concurrently (Map phase), reconcile (Reduce phase) with a coherence pass. Cuts wall-clock time 5–8× for chunked conversion.

6. **Batch API integration.** For non-real-time bulk processing (back-catalog normalization), use provider batch APIs for 50% cost reduction.

### Non-Goals (What NOT to Build Yet)

- **LangGraph orchestration.** The pipeline is sequential. Simple Python functions suffice.
- **"Character Bible" / "Universal Semantic Layer."** The running metadata document handles continuity for v1. A persistent character database is a product feature, not a normalization dependency.
- **STED evaluation metrics.** Useful for benchmarking, not for production validation. Fountain parse success + custom lint rules are sufficient for v1.
- **Mobile-first "Economic Page" formatting.** Normalization targets writer-stage Fountain, not reader-experience optimization.
- **Self-hosted models / constrained decoding.** CineForge uses cloud APIs; skip Guidance/vLLM integration.
- **Regulatory compliance metadata.** AI content transparency tags are a product/legal decision, not a normalization pipeline concern.
- **PDF/OCR input.** Defer to a separate ingest story. Story 004 scope is text input normalization.

---

## 7. Implementation Plan for CineForge

### 7.1 File-Level Changes (Priority Order)

| Priority | File | Change |
|---|---|---|
| **P0** | `src/cine_forge/ai/long_doc.py` | Add scene-boundary chunker using `RecursiveCharacterTextSplitter` with screenplay separators. Add running metadata document (init, update, compress). Add overlap handling (400 tokens read-only). |
| **P0** | `src/cine_forge/ai/llm.py` | Add edit-list generation prompt (SEARCH/REPLACE format). Add fuzzy patch application (exact → whitespace-norm → SequenceMatcher). Add `finish_reason` monitoring with auto-reroute to chunked. Add prompt caching layout (stable prefix first). |
| **P0** | `src/cine_forge/ai/qa.py` | Switch QA output to structured JSON via Instructor + Pydantic schema. Add targeted repair loop (QA violations → patch ops → apply → revalidate). Cap retries at 3; `needs_review` on exhaustion. |
| **P1** | `src/cine_forge/modules/ingest/script_normalize_v1/main.py` | Add input classifier (Fountain parse test, FDX detection, fallback to prose). Route to appropriate pipeline path. Add FDX-to-Fountain converter. |
| **P1** | New: `src/cine_forge/ai/fountain_validate.py` | Deterministic post-LLM normalizer: uppercase scene headings + character names, blank line enforcement, whitespace cleanup, line ending normalization. Fountain parse check via `fountain-tools`. Custom lint: orphaned dialogue, malformed headings, inconsistent character names. |
| **P2** | `docs/research/long-doc-editing.md` | Replace with this synthesis document as the canonical research reference. |
| **P2** | New: `src/cine_forge/ai/schemas.py` | Pydantic schemas for QA violation list, edit-list operations, running metadata document, normalization result envelope. |

### 7.2 Testing Strategy

**Test corpus (10 inputs, as specified in Opus 4.6 report):**
1. 2 clean Fountain files (short + long)
2. 2 FDX files (simple + complex formatting)
3. 2 prose narratives (treatment-style + rough draft)
4. 2 rough notes/outlines (bullet points + stream-of-consciousness)
5. 1 mixed-format document
6. 1 edge case: very long (120+ pages, >50K tokens)

**Acceptance criteria per test:**
- [ ] Output parses successfully via `fountain-tools` (hard gate)
- [ ] Custom lint: zero orphaned dialogue, zero malformed headings
- [ ] Content preservation: manual diff against input shows no unintended omissions or additions
- [ ] Character name consistency: all instances of each character use the same casing
- [ ] Cost within 2× of estimated per-approach costs above
- [ ] Latency < 5 min for edit-list path, < 15 min for chunked conversion path
- [ ] `needs_review` flag raised correctly when QA issues persist past 3 retries

**Regression suite:** After v1 ships, convert test corpus results into automated regression tests. Store gold-standard outputs for diff-based regression.

### 7.3 Cost Control & Safety Guardrails

- **Token caps per call:** Set `max_tokens` explicitly on every API call. Never rely on model defaults.
- **Per-screenplay cost ceiling:** Abort and flag for manual review if total cost exceeds $2.00 (5× worst-case estimate). Prevents runaway retry loops.
- **Retry budget:** Max 3 retries per edit application. Max 3 QA repair passes. Max 2 re-routes from edit-list to chunked regen. After exhaustion: `needs_review`, not infinite loops.
- **`finish_reason` / `stop_reason` monitoring:** If `max_tokens`, auto-reroute to chunked. If `content_filter`, log and flag. Never silently accept truncated output.
- **Per-stage cost telemetry:** Log input tokens, output tokens, cached tokens, model used, latency, and cost for every API call. Aggregate per-screenplay. This data drives all future optimization.
- **Provider-agnostic interface:** Abstract LLM calls behind a provider config that can be swapped without code changes. Pin to specific model version strings, not aliases.
- **Temperature 0.0:** Enforced at the infrastructure level for all normalization calls.

---

## 8. Open Questions & Validation Experiments

| # | Question | Experiment | Blocking? |
|---|---|---|---|
| 1 | What is Opus 4.6's actual max output in production? | Run a 50K-token regen test with Opus 4.6; check `stop_reason`. | No — architecture doesn't depend on it |
| 2 | Does `fountain-tools` handle all CineForge edge cases? | Parse 10 real-world messy screenplays; document failures. | Yes — determines if we need parser patches |
| 3 | What's the actual failure rate of SEARCH/REPLACE on screenplay text? | Run edit-list normalization on 10 test scripts; log match confidence per edit. | No — fuzzy matching + fallback covers this |
| 4 | Is `instructor` stable with Gemini 2.5 Flash? | Run 50 structured output calls; measure schema compliance rate. | Yes — determines default provider choice |
| 5 | How much does prompt caching actually save in practice? | Run same script 5× with and without caching; compare billed tokens. | No — savings are gravy, not blocking |
| 6 | What's the optimal running metadata compression ratio? | Test 500, 800, and 1200-token metadata caps across 5 long scripts; measure coherence drift. | No — 800 is a reasonable starting point |

---

## 9. Final Confidence Statement

**Architecture confidence: High.** All five reports independently converge on the same hybrid strategy. The existing CineForge baseline is architecturally correct and needs tooling upgrades, not a redesign.

**Implementation confidence: Medium-High.** The library stack (`fountain-tools`, `instructor`, `langchain-text-splitters`) is well-documented and actively maintained. The edit-list fuzzy matching pipeline is battle-tested in the Aider ecosystem. The main implementation risk is screenplay-specific edge cases in parsing and edit application, which will surface during testing.

**Cost estimates: Medium.** Provider pricing is volatile and model naming is chaotic. The cost ranges above are order-of-magnitude correct but should be validated against actual API billing after the first 10 test runs.

**What could invalidate this recommendation:**
- A provider ships a model with verified 200K+ output and zero "laziness" degradation, making single-pass viable for all inputs. (Unlikely in next 3 months.)
- `fountain-tools` proves inadequate for messy real-world screenplays, requiring a custom parser. (Mitigated by the validation experiment in §8.)
- Edit-list failure rates on screenplay text are significantly higher than on code (the domain where most benchmarks exist). (Mitigated by fallback to chunked regen for failed sections.)

**Bottom line:** Build the hybrid. Ship it this sprint. Instrument everything. Let production data drive v2 priorities.

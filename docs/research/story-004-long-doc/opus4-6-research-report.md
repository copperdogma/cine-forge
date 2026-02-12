# Long Document AI Editing Research (Opus 4.6 Deep Research Report, Feb 2026)
20260212: Created.

# AI screenplay normalization for CineForge: architecture decision

**The binding constraint isn't context windows—it's max output tokens.** Most frontier models in early 2026 accept 200K–1M input tokens but cap output at 32K–65K, which is barely enough (or insufficient) for regenerating a full 45K-token screenplay in a single pass. The viable strategy for v1 is a hybrid: classify input type, route screenplays through scene-aware edit-list patching, route prose/notes through chunked conversion at scene boundaries, and run a lightweight QA pass. Cost per screenplay: **$0.03–$0.50** depending on model and approach, with latency of 1–13 minutes. Gemini 2.5 Flash and GPT-4.1 Mini offer the best cost-quality tradeoff for production pipelines today.

---

## A) Executive summary

- **Output token limits, not context windows, are the bottleneck.** GPT-4.1 caps at 32K output; Claude Sonnet 4.5 and Gemini 2.5 Pro cap at 64–65K. Only GPT-5 (128K output) and possibly Claude Opus 4.6 (128K, unverified) comfortably fit full screenplay regeneration.
- **Edit-list/patch is 70–86% cheaper and 79% faster than full regeneration**, but has a mechanical failure rate of 6–50% depending on model and edit format. Fuzzy matching + retry loops bring reliability above 95%.
- **Full regeneration above ~30K tokens causes content loss ("laziness")** in all current models. Chunked regeneration at scene boundaries with 300–500 token overlap and running metadata carry-forward is the proven mitigation.
- **Fountain plain-text format is the ideal canonical representation** — well-specified, git-friendly, parser-supported in Python. Use `fountain-tools` (wildwinter) for parsing/serialization, `screenplain` for FDX/PDF export.
- **Research shows superlinear performance degradation with input length.** A weaker model with chunk-based processing can outperform a stronger model in single-shot on documents above ~30K tokens.
- **Prompt caching + Batch API together reduce costs 70–95%** when processing screenplay volumes. System prompts and formatting rules stay cached across runs.
- **Instructor library (Pydantic validation)** is the most production-ready tool for enforcing structured screenplay output schemas with automatic retry on validation failure.
- **v1 architecture should ship this week**: input classifier → format-specific route → scene-boundary chunked processing → Instructor-validated output → deterministic Fountain reassembly → QA pass.

---

## B) Findings by section

### 1. API-level support reveals output ceilings that dictate architecture

The landscape of usable models for screenplay normalization narrows dramatically once you filter by max output tokens. A typical feature screenplay runs **35K–55K tokens**; any model with less than ~40K max output cannot regenerate one in a single pass.

| Model | Context | Max output | Output sufficient? | Structured output | Input/Output $/M | Notes |
|---|---|---|---|---|---|---|
| **GPT-5 / 5.2** | 400K | **128K** | ✅ Excellent | ✅ GA | $1.25–1.75 / $10–14 | Best OpenAI for full regen |
| **GPT-5 Mini** | 400K | **128K** | ✅ Excellent | ✅ GA | $0.25 / $2 | Budget full-regen option |
| **GPT-4.1** | 1M | **32K** | ⚠️ Only short scripts | ✅ GA | $2 / $8 | Huge context, limited output |
| **GPT-4.1 Mini** | 1M | **32K** | ⚠️ Only short scripts | ✅ GA | $0.40 / $1.60 | Best for edit-list approach |
| **Claude Sonnet 4.5** | 200K (1M beta) | **64K** | ✅ Tight fit | ✅ GA | $3 / $15 | Strong instruction following |
| **Claude Opus 4.6** | 200K (1M beta) | **128K*** | ✅ If verified | ✅ GA | $5 / $25 | *Third-party claim only* |
| **Gemini 2.5 Pro** | 1M | **65K** | ✅ Tight fit | ✅ GA | $1.25 / $10 | Context caching available |
| **Gemini 2.5 Flash** | 1M | **65K** | ✅ Tight fit | ✅ GA | $0.15 / $0.60 | Best $/quality ratio |
| **o3 / o4-mini** | 200K | **100K** | ✅ | ✅ GA | $1.10–2 / $4.40–8 | Reasoning overhead 3–10× |

**Structured output** is now GA across all major providers. OpenAI and Anthropic use constrained decoding to guarantee valid JSON schema compliance. Research by Tam et al. (2024) shows **10–15% reasoning degradation** under strict JSON constraints, but this primarily affects complex reasoning tasks—mechanical formatting normalization is less affected.

**Streaming** is universal via SSE and works with structured output modes. For 45K-token outputs at ~80 tokens/sec, generation takes **~9–10 minutes** without streaming feedback—streaming is essential for UX.

**Practical reliability concern**: The "lost in the middle" problem (Stanford/Berkeley) means models under-attend to information in the middle of long contexts. For screenplay normalization, **place formatting rules at both the start and end of the system prompt**.

### 2. Libraries worth integrating form a lean but effective stack

After evaluating six major frameworks, the recommended stack is deliberately minimal. Every additional dependency adds failure modes in production.

**Instructor** (11K GitHub stars, 3M+ monthly PyPI downloads) is the highest-value integration. It wraps any LLM provider with Pydantic model validation, automatic retry on schema violation, and streaming with partial validation. Define `SceneHeading`, `ActionBlock`, `DialogueLine` as Pydantic models, and Instructor enforces the schema with retries. It supports OpenAI, Anthropic, Google, and 12+ other providers through a single `from_provider()` interface.

**LangChain text-splitters** (`langchain-text-splitters` v1.1.0, Dec 2025) provide `RecursiveCharacterTextSplitter` that can be customized with screenplay-specific separators (`\nINT.`, `\nEXT.`, scene heading patterns). The `add_start_index=True` parameter tracks chunk positions for reassembly. The Refine chain pattern—where each chunk's processing carries forward the previous chunk's output—directly maps to sequential screenplay processing. Known limitation: older segments get over-emphasized, and the carry-forward context can exceed limits if not compressed.

**DSPy** (31.9K stars, Stanford NLP) offers a unique capability: **automatic prompt optimization**. Define normalization signatures like `normalize_scene(raw_scene, style_guide, previous_context) → normalized_scene` and DSPy's MIPROv2 optimizer bootstraps few-shot examples from gold-standard screenplays, achieving **25–65% improvement over manual prompts**. Worth investing in for v2 but not essential for v1.

**fountain-tools** (wildwinter, `screenplay-tools` on GitHub) is the best Python Fountain parser. It provides incremental line-by-line parsing, a `CallbackParser` for event-driven processing, a `Writer` for canonical Fountain serialization, and new FDX support. Multi-language (Python, JS, C#, C++). **screenplain** complements it for FDX and PDF export.

**Microsoft Guidance** (19K stars) provides grammar-based constrained decoding at ~50μs overhead per token. Its `llguidance` engine has been merged into vLLM, SGLang, and llama.cpp. Valuable if you self-host models; less useful with cloud APIs since providers already offer constrained decoding.

**LlamaIndex** has an interesting new product, LlamaReport, with intelligent edit proposals for document sections. However, it's a cloud product requiring paid plans, and its core framework is oriented toward RAG rather than document transformation. Low priority for v1.

### 3. Scene-boundary chunking with compressed carry-forward is the proven pattern

A 2025 arXiv paper ("Divide and Conquer for Long Context LLMs") provides the strongest empirical evidence: **LLM performance degrades superlinearly with input length**, and a weaker model with chunk-based processing can surpass GPT-4o applied in single-shot on large inputs. Three distinct failure modes compound: cross-chunk dependence (task noise), confusion from context size (model noise), and imperfect result integration (aggregator noise).

**Optimal chunk strategy for screenplays**: split at scene boundaries, targeting **2,000–4,000 tokens per chunk**. A 45K-token screenplay yields ~12–18 chunks. Screenplays have natural structural boundaries (scene headings starting with INT/EXT) that make this straightforward. Grouping 2–3 short scenes into one chunk and splitting very long scenes at beat transitions keeps chunks within the target range.

**Overlap of 300–500 tokens** (the tail of the previous scene) provides boundary context. Mark this overlap as read-only: `[PREVIOUS CONTEXT — DO NOT MODIFY]`. A/B testing by practitioners shows **15–20% overlap is the sweet spot** — beyond 20%, diminishing returns with increased cost.

**The critical coherence mechanism is a compressed running metadata document** (~500–1,000 tokens) that carries across all chunks. This document contains: character names encountered so far, established formatting conventions (how character extensions like V.O./O.S. are styled), narrative summary of prior scenes, and any style notes. Update it after each chunk. This prevents the unbounded context growth that kills pure Refine chains while maintaining coherence.

Each chunk's prompt window looks like: `[System: Fountain formatting rules + few-shot example (~1,500 tokens)] + [Running metadata (~800 tokens)] + [Previous chunk tail (~400 tokens)] + [Current chunk to normalize (~3,000 tokens)]` = ~5,700 input tokens per chunk, well within any model's capacity.

**Temperature must be 0.0–0.2** for normalization consistency. Higher temperatures cause style drift between chunks.

### 4. Edit-list wins on efficiency but needs robust application infrastructure

The edit-list vs. full-regeneration debate is the most extensively studied area, thanks to AI coding tools. Key findings:

**Edit-list approach produces 31–86% fewer output tokens** (confirmed by both the JSON Whisperer paper from Lightricks and Waleed Kadous's Edit Trick experiments), is **~79% faster**, and **~70% cheaper**. Quality is within 5% of full regeneration for mechanical edits. The JSON Whisperer paper from Lightricks is directly relevant—it tested RFC 6902 JSON patch generation on scene data from a film production platform.

**But mechanical failure rates range from 6% to 50%** depending on model and edit format. The top failure modes are: (1) search-block mismatch where the LLM can't perfectly reproduce the text it's trying to find; (2) line number hallucination—OpenAI explicitly recommends avoiding line numbers in edit formats; (3) missed related updates where the model patches one occurrence but misses others; (4) format non-compliance where models not trained on a specific edit format fail to use it correctly.

**The mitigations are well-established.** Layered fuzzy matching (exact → whitespace-insensitive → Levenshtein) brings match rates above 95%. Aider, Cursor, and Codex CLI all use this pattern. The hashline approach (February 2026, oh-my-pi project) tags every line with a 2–3 character content hash, achieving up to **10× improvement for weaker models** and ~20% reduction in output tokens. For structured screenplay data, the JSON Whisperer's EASE encoding (converting arrays to dictionaries with stable keys) eliminates index arithmetic errors.

**Full regeneration is the default for prose-to-screenplay conversion** (the input has no existing structure to patch). For screenplay-to-screenplay cleanup, the decision depends on edit density: if >40% of lines need changes, regeneration is simpler and nearly as efficient as edit-list. If <20% need changes, edit-list is clearly superior.

**Cursor's two-model architecture is the most sophisticated hybrid**: a frontier model generates a "semantic diff" (intended changes with comment markers), then a fine-tuned 70B "fast-apply" model rewrites the file at ~1,000 tokens/sec. Aider's Architect/Editor mode similarly splits planning from execution, hitting **85% on coding benchmarks** with o1-preview + DeepSeek as editor. This two-step pattern applies directly to screenplay normalization.

### 5. Fountain format and a thin tooling layer cover the screenplay domain

**Fountain is the canonical format.** It's well-specified, human-readable, git-friendly, and supported by parsers in every major language. The specification defines 14 element types (scene heading, action, character, dialogue, parenthetical, transition, dual dialogue, lyrics, centered text, title page, page breaks, sections, synopses, notes/boneyard). Key formatting rules the normalizer must enforce: scene headings start with INT/EXT (uppercase), character names always uppercase, no blank line between character and dialogue, parentheticals wrapped in `()`, transitions uppercase ending in `TO:`.

**No standalone screenplay format validator exists as a library.** Validation is implicitly handled by parsers—if a parser tokenizes input successfully, the Fountain syntax is valid. For production, build a custom validator checking: orphaned dialogue (no preceding character), malformed scene headings, inconsistent character name casing, and missing title page metadata.

**FDX (Final Draft XML) parsing is straightforward.** The format maps cleanly: `<Paragraph Type="Scene Heading">` → Fountain scene heading, `Type="Character"` → uppercase character name, etc. Python's `xml.etree.ElementTree` handles this directly. The `screenplay-tools` library now supports FDX reading.

**No open-source AI screenplay normalizer exists.** Commercial SaaS tools (LivingWriter, Squibler, HyperWrite) offer AI formatting but are closed-source and not embeddable. The HoLLMwood research framework (arXiv 2406.11683) and DSR framework (arXiv 2510.23163) confirm that **decoupling narrative generation from format conversion improves quality by 2.4 points** over end-to-end generation. This validates CineForge's approach of treating normalization as a separate pipeline stage.

### 6. Token economics favor edit-list for cleanup and Gemini Flash for volume

Cost per screenplay across three approaches, using representative models:

| Approach | Gemini 2.5 Flash | GPT-4.1 Mini | Claude Sonnet 4.5 | Latency (Flash) |
|---|---|---|---|---|
| **A: Single-pass** (50K in / 45K out) | **$0.13** | $0.09 | $0.83 | ~3.5 min |
| **B: Chunked** (131K in / 59K out) | **$0.19** | $0.15 | $1.28 | ~4 min |
| **C: Edit-list + QA** (100K in / 15K out) | **$0.07** | $0.06 | $0.53 | ~1 min |

**Approach C is cheapest** because output drops to 15K tokens (edit instructions + QA). But it only works for screenplay→screenplay cleanup—prose conversion requires Approach A or B.

**Batch API discounts (50%)** are available from all three major providers with 24-hour async delivery. **Prompt caching** saves an additional 50–90% on repeated system prompts. Combined, processing 100 screenplays via Gemini 2.5 Flash batch costs **$1.20–$6.40** total depending on approach.

**Latency profile**: Gemini 2.5 Flash leads at **~250 tokens/sec output** (3.5 min for full screenplay). GPT-4.1 runs ~80–100 t/s (~8 min). Claude Sonnet 4.5 runs ~77 t/s (~10 min). Chunked approaches (Approach B) can parallelize: running 9 chunks concurrently cuts wall-clock time by ~5×, making even slower models practical.

**Reasoning models (o1/o3/o4-mini) are a trap for this use case.** They bill invisible "thinking" tokens as output—a 45K visible output could cost 3–10× listed rates. Screenplay normalization is a formatting task, not a reasoning task. Avoid.

**Hidden cost: retry overhead.** Plan for 5–15% additional spend. Cheaper models produce more formatting errors requiring correction passes. A $0.10 model needing 3 retries costs more than a $0.50 model that succeeds first try. Claude Sonnet models show notably lower variance in production.

---

## C) Decision matrix

Scoring 1–5 (5 = best) across weighted criteria for three candidate architectures processing a typical 45K-token screenplay:

| Criterion (weight) | A: Single-pass large context | B: Scene-chunked conversion | C: Edit-list + QA | C+A Hybrid |
|---|---|---|---|---|
| **Reliability** (25%) | 3 — content loss risk above 40K tokens; "laziness" documented | 4 — scene-boundary chunks avoid mid-scene splits; carry-forward proven | 3 — 6–50% mechanical failure rate mitigated by fuzzy matching + retry | **4** — routes to strongest approach per input |
| **Output quality** (20%) | 4 — coherent when it works; no seam artifacts | 3 — seam artifacts at chunk boundaries; drift risk | 4 — preserves unchanged content perfectly; edit quality within 5% | **4** — best quality per path |
| **Cost efficiency** (20%) | 3 — full output required even for minor cleanup | 2 — 55–60% more expensive than single-pass due to redundant context | 5 — 70% cheaper than single-pass for cleanup | **4** — cheapest path per input type |
| **Latency** (10%) | 3 — 3–13 min depending on model | 3 — parallelizable chunks ~4 min; sequential ~13 min | 5 — ~1 min for edit-list generation | **4** — fast for cleanup, adequate for conversion |
| **Input flexibility** (10%) | 4 — handles prose/notes/screenplay | 5 — handles any input via LLM chunked conversion | 1 — only works for existing screenplay input | **5** — routes prose to B, screenplay to C |
| **Implementation complexity** (10%) | 5 — simplest; one API call | 2 — chunking, overlap, carry-forward, reassembly | 3 — edit format, fuzzy matching, application logic | **2** — most complex; classifier + two paths |
| **Scalability** (5%) | 2 — cannot handle screenplays exceeding output limit | 5 — works for any length document | 4 — edit list stays compact regardless of doc size | **5** — no length ceiling |
| **Weighted score** | **3.35** | **3.30** | **3.55** | **3.90** |

**The hybrid approach (C+A) wins.** Route screenplay inputs through edit-list patching (C), route prose/notes through chunked conversion (B variant), and use single-pass (A) only for short documents under 15K tokens. This maximizes cost efficiency and quality while handling all input types.

---

## D) Recommended architecture

### v1: Ship this sprint

```
                    ┌─────────────────────┐
                    │  INPUT CLASSIFIER   │
                    │  (deterministic +   │
                    │   cheap LLM call)   │
                    └─────┬───────┬───────┘
                          │       │
              ┌───────────┘       └───────────┐
              ▼                               ▼
   ┌─────────────────────┐       ┌─────────────────────────┐
   │  SCREENPLAY INPUT   │       │  PROSE / NOTES INPUT    │
   │                     │       │                         │
   │  1. Parse (FDX →    │       │  1. Scene-boundary      │
   │     Fountain, or    │       │     detection (regex    │
   │     detect existing │       │     + LLM fallback)     │
   │     Fountain)       │       │  2. Chunk at scenes     │
   │  2. Validate        │       │     (2-4K tokens each)  │
   │  3. Short? → single │       │  3. Per-chunk: convert  │
   │     pass normalize  │       │     to Fountain with    │
   │  4. Long? → edit-   │       │     running metadata    │
   │     list generation │       │     carry-forward       │
   │     + fuzzy apply   │       │  4. Reassemble          │
   │  5. QA pass         │       │  5. QA pass             │
   └─────────────────────┘       └─────────────────────────┘
              │                               │
              └───────────┐       ┌───────────┘
                          ▼       ▼
                    ┌─────────────────────┐
                    │  FOUNTAIN VALIDATOR  │
                    │  + NORMALIZER       │
                    │  (deterministic)    │
                    └─────────┬───────────┘
                              ▼
                    ┌─────────────────────┐
                    │  CANONICAL OUTPUT   │
                    │  (.fountain + .fdx) │
                    └─────────────────────┘
```

**v1 model choices:**
- **Primary**: Gemini 2.5 Flash ($0.13/screenplay, ~250 t/s, 65K output) for chunked conversion and QA
- **Fallback**: GPT-4.1 Mini ($0.09/screenplay, 32K output) for edit-list generation (output stays compact)
- **Premium path**: Claude Sonnet 4.5 ($0.83/screenplay) for scripts requiring highest fidelity, or when retry rate on Flash exceeds threshold

**v1 library stack:**
- `fountain-tools` (wildwinter) — Fountain parse/serialize + FDX read
- `screenplain` — FDX/PDF export
- `instructor` — Pydantic schema validation with auto-retry
- `langchain-text-splitters` — Scene-aware chunking with custom separators
- `xml.etree.ElementTree` — Direct FDX XML parsing
- `difflib` — Fuzzy matching for edit-list application

**v1 key implementation details:**
- Edit-list format: search/replace blocks (not line numbers, not unified diff). Use `<<<<<<< SEARCH` / `>>>>>>> REPLACE` delimiters, matching Aider's proven format.
- Fuzzy matching pipeline: exact match → whitespace-normalized → `difflib.SequenceMatcher` (ratio > 0.85) → fail and retry with error context.
- Running metadata document: `{characters: [...], locations: [...], style_notes: str, narrative_summary: str}` — updated after each chunk, capped at 1,000 tokens via LLM compression.
- Prompt caching: cache the system prompt (Fountain rules + few-shot examples, ~1,500 tokens) across all chunks and all screenplays. Saves 90% on repeated input with Anthropic, 75% with OpenAI.
- Temperature: 0.0 for all normalization calls. No creative variation desired.

### v2: Next 1–2 milestones

- **DSPy prompt optimization**: Compile normalization prompts against a gold-standard set of 20–50 correctly normalized screenplays. MIPROv2 should yield 25–65% quality improvement over hand-tuned prompts.
- **Hashline edit format**: Tag every line of input with 2-character content hashes. The oh-my-pi benchmark (Feb 2026) shows up to 10× improvement in edit application accuracy for weaker models.
- **Two-model architecture** (Cursor-style): Use Claude Sonnet 4.5 as "architect" to generate semantic diffs, then GPT-4.1 Nano as fast "applier." Architect identifies what needs to change; applier executes at ~150 t/s for pennies.
- **Self-hosted fast-apply model**: Fine-tune a small model (Llama 3 8B or similar) on screenplay edit application. Cursor's approach achieves ~1,000 t/s with speculative decoding. Eliminates API dependency for the mechanical apply step.
- **Parallel chunk processing**: Run chunks concurrently (Map phase) then reconcile (Reduce phase) with a coherence pass. Cuts wall-clock time 5–8× for chunked conversion.
- **Context caching at Google's tier**: Gemini's context caching stores the system prompt + Fountain spec in Google's cache at $1/M tokens/hour. For batch processing 100+ screenplays in a session, this beats per-request prompt overhead.
- **PDF input via OCR**: Integrate Tesseract + ML-based screenplay element classification (the ACL 2014 approach for scene boundary detection achieves significantly higher accuracy than regex alone).

---

## E) Risks and mitigations

**Risk 1: Output truncation on long screenplays.** Models silently truncate when hitting output limits. A 55K-token screenplay in single-pass on Gemini 2.5 Pro (65K limit) leaves only 10K tokens of headroom—less with JSON overhead. *Mitigation*: Always monitor `finish_reason` / `stop_reason`. If `max_tokens`, automatically re-route to chunked processing. Never rely on single-pass for screenplays above 40K tokens.

**Risk 2: Content loss in full regeneration.** The "laziness" problem—models omitting sections with `...continues as before...`—is documented across all frontier models for outputs above ~20K tokens. *Mitigation*: Use edit-list for screenplay cleanup (unchanged content is never regenerated). For prose conversion, validate output token count is within ±15% of expected length; if shorter, flag for chunk-level re-processing.

**Risk 3: Edit-list mechanical failures.** Search blocks that don't match the source document. Aider reports this degrades notably above 25K tokens of context. *Mitigation*: Layered fuzzy matching with a 0.85 similarity threshold. On failure, retry with the exact error message and the correct target text in the prompt. Limit to 3 retries, then fall back to chunked regeneration for the affected section.

**Risk 4: Semantic drift across chunks.** Style and formatting conventions shift between chunks, creating visible "seams." *Mitigation*: Fixed system prompt + running metadata document + few-shot examples in every chunk. Post-processing deterministic normalizer (character name casing, scene heading format) catches mechanical inconsistencies. Temperature 0.0.

**Risk 5: Provider pricing volatility and model deprecation.** LLM prices dropped ~80% through 2025 and model naming is chaotic. *Mitigation*: Abstract the LLM call behind a provider-agnostic interface (Instructor already does this via `from_provider()`). Maintain a model config that can be swapped without code changes. Pin to specific model versions, not aliases.

**Risk 6: Fountain spec ambiguity at edges.** Dual dialogue, forced elements, and boneyard have parser-dependent behavior. *Mitigation*: Define a CineForge-canonical subset of Fountain that the normalizer targets. Document deviations from the spec. Use `fountain-tools` as the reference parser—if it parses correctly, the output is valid.

---

## F) What I would implement this week

1. **Define Pydantic schemas** for all Fountain element types (`SceneHeading`, `Action`, `Character`, `Dialogue`, `Parenthetical`, `Transition`, `TitlePage`). Each element has type, raw text, and optional metadata (scene number, character extensions, dual dialogue flag). This is the contract between LLM output and deterministic processing.

2. **Build the input classifier.** Deterministic rules: if input parses as valid FDX XML → FDX path; if `fountain-tools` Parser succeeds with >80% element coverage → Fountain path; otherwise → prose/notes path. No LLM call needed for classification in most cases.

3. **Implement FDX-to-Fountain converter** using `xml.etree.ElementTree`. Map `<Paragraph Type="...">` to Fountain elements. Handle `<Text Style="...">` for bold/italic/underline. Test against 5 real FDX files.

4. **Build the scene-boundary chunker.** Custom `RecursiveCharacterTextSplitter` separators: `["\nINT.", "\nEXT.", "\nINT./EXT.", "\nI/E", "\n\n\n"]`. Target 3,000 tokens per chunk. Include 400 tokens of read-only previous context. Wire up running metadata document (character list + summary, compressed to 800 tokens after each chunk).

5. **Wire up Instructor** with Gemini 2.5 Flash as default provider. Define the normalization prompt with Fountain syntax rules and 2 few-shot examples of correct normalization. Set `max_retries=3`. Validate that output parses cleanly through `fountain-tools` Parser.

6. **Implement edit-list path** for screenplay→screenplay cleanup. Prompt generates `<<<<<<< SEARCH` / `>>>>>>> REPLACE` blocks. Build the application layer with `difflib.SequenceMatcher` fuzzy matching. Log match confidence for every applied edit. Route to chunked regeneration on 3 consecutive match failures.

7. **Build the deterministic Fountain normalizer** (post-LLM). Regex-based: force scene headings to uppercase, force character names to uppercase, ensure blank lines before scene headings and character cues, strip trailing whitespace, normalize line endings to `\n`. This catches the mechanical errors that LLMs introduce inconsistently.

8. **Wire up the QA pass.** Send full normalized output + original input to a cheap model (GPT-4.1 Nano, $0.02/screenplay). Prompt: "Compare these two documents. List any content that was present in the original but missing from the normalized version, any content added that wasn't in the original, and any formatting errors." Parse response as a list of issues. If critical issues found, re-process affected scenes.

9. **Add instrumentation.** Log: input type, chunk count, model used, tokens consumed (input/output), retry count per chunk, edit match confidence scores, QA issue count, total latency, total cost. This data drives every optimization decision from here.

10. **Test against 10 diverse inputs**: 2 clean Fountain files, 2 FDX files, 2 prose narratives, 2 rough notes/outlines, 1 mixed-format document, 1 edge case (very long, 120+ pages). Measure: format validity rate, content preservation rate (diff against manual gold standard), cost, latency.

---

## G) Sources

- **OpenAI API pricing and model docs** (platform.openai.com/docs/models, pricepertoken.com) — Model specs, context windows, output limits, structured output support
- **Anthropic Claude pricing and docs** (platform.claude.com/docs/en/about-claude/pricing) — Claude Sonnet 4.5, Opus 4.6 specs, structured output GA, batch API
- **Google Gemini API pricing** (ai.google.dev/gemini-api/docs/pricing) — Gemini 2.5 Pro/Flash, 3 Pro/Flash pricing, context caching, batch discounts
- **Aider documentation and benchmarks** (aider.chat/docs/benchmarks.html) — Edit format comparison, search/replace reliability, architect/editor mode, laziness benchmarks
- **"The Harness Problem"** (blog.can.ac, Feb 12 2026) — Hashline edit format, oh-my-pi benchmark across 16 models, patch failure rates by format
- **JSON Whisperer** (arXiv 2510.04717, Lightricks/Hebrew Univ.) — RFC 6902 JSON patch generation for film production scene data, EASE encoding, 31% token reduction
- **"Divide and Conquer for Long Context LLMs"** (arXiv 2506.16411) — Empirical evidence of superlinear performance degradation with input length
- **Cursor Instant Apply** (cursor.sh/blog, blog.getbind.co, blog.sshh.io) — Two-model sketch+apply architecture, speculative decoding, fast-apply model details
- **EDIT-Bench** (arXiv 2511.04486) — 540 real-world editing problems across 40 LLMs, pass@1 rates
- **Diff-XYZ** (JetBrains, arXiv 2510.12487) — Cross-format benchmark confirming no single edit format dominates
- **Tam et al. "Let Me Speak Freely?"** (2024) — 10–15% reasoning degradation under strict JSON constraints
- **Fountain syntax specification** (fountain.io/syntax) — Full element type reference and formatting rules
- **fountain-tools / screenplay-tools** (github.com/wildwinter/fountain-tools) — Python Fountain parser, incremental parsing, FDX support
- **screenplain** (github.com/vilcans/screenplain, PyPI) — Fountain parser + FDX/PDF export in Python
- **Instructor library** (python.useinstructor.com, github.com/567-labs/instructor) — Pydantic LLM validation, auto-retry, multi-provider support
- **DSPy** (dspy.ai, github.com/stanfordnlp/dspy) — Declarative LLM pipeline optimization, MIPROv2
- **LangChain text-splitters** (pypi.org/project/langchain-text-splitters) — RecursiveCharacterTextSplitter, custom separators, Refine chain
- **Hamel Husain chunk sizing guide** (hamel.dev/blog) — Fixed vs. expansive output task chunking strategies
- **"Parsing Screenplays for Extracting Social Networks"** (ACL 2014, aclanthology.org/W14-0907) — ML-based screenplay element classification
- **DSR Framework** (arXiv 2510.23163) — Two-stage narrative-then-format conversion, 2.4 point improvement over end-to-end
- **HoLLMwood** (arXiv 2406.11683) — LLM screenplay generation framework, failure mode analysis
- **Waleed Kadous "The Edit Trick"** (Medium) — 86% token reduction, 79% speed improvement with edit-list vs regeneration
- **Fabian Hertwig "Code Surgery"** (fabianhertwig.com, Apr 2025) — Comprehensive analysis of AI coding tool edit formats
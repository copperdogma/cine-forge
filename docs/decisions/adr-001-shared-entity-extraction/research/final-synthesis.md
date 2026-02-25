---
type: synthesis-report
topic: shared-entity-extraction
synthesis-model: claude-opus-4-6
source-reports:
- ai-openai-deep-research.md
- claude-opus-4-6-report.md
- gemini-3-1-pro-preview-report.md
- gpt-5-2-pro-report.md
- grok-4-1-report.md
synthesized: '2026-02-25T00:06:21.314280+00:00'
---



---
canonical-model-name: "claude"
report-date: "2025-07-01"
research-topic: "shared-entity-extraction"
report-type: "synthesis"
---

# Synthesis: Shared Entity Extraction with Provenance

## 1. Executive Summary

- **No single off-the-shelf tool delivers the full pipeline** (chunked extraction → provenance-rich evidence quotes → identity resolution → relationship extraction → confidence scoring). All five reports agree on this fundamental finding. A custom pipeline built on existing components is required.
- **The two-pass extraction pattern** (extract entities first, then extract relationships given the entity roster; or extract → verify) is the single highest-impact architectural decision, yielding 18–45% improvements across multiple independent benchmarks (KGGen, LINK-KG, CORE-KG, ODKE+). This is the strongest empirical finding across all reports.
- **LangExtract (Google)** is the only tool purpose-built for provenance-rich extraction with character-level source grounding, but it lacks identity resolution and relationship extraction — it is a component, not a complete solution.
- **Microsoft GraphRAG** is the most mature pipeline (~31K stars, active development) with entity extraction, relationship extraction, community detection, and text-unit provenance, but its entity disambiguation is weak and its summarization pipeline loses exact-quote provenance.
- **Neo4j GraphRAG Python** is the only tool with production-grade entity resolution (fuzzy + semantic matchers) but is newer and less battle-tested.
- **Instructor** (jxnl, ~12.4K stars, 6M+ monthly PyPI downloads) is the best low-level building block for enforcing provenance-rich Pydantic schemas on LLM outputs and should be a core dependency regardless of higher-level framework choice.
- **Chunking strategy has more impact than model choice**: SLIDE (2025) showed overlapping sliding-window chunking improves entity extraction by 24% and relationship extraction by 39% over baseline — a larger gain than upgrading the LLM.
- **A three-tier model cascade** (cheap for NER, mid-tier for relationships/coref, premium for hardest disambiguation) reduces costs 60–90% versus premium-only, making the 300-page genealogy book tractable at $3–10 total.
- **The recommended architecture** is: Python library with CLI wrapper → pre-chunked JSONL input → per-chunk extraction with Instructor → coreference resolution → embedding-based blocking + LLM entity resolution → relationship aggregation → JSON property graph output with a separate evidence store.
- **Identity resolution at genealogy scale** (500 entities) requires blocking strategies (token blocking, embedding ANN) to avoid O(n²) comparisons; combined with genealogy-specific heuristics (surname + generation + geography), this is tractable.
- **Confidence scoring must use external validation**, not LLM self-assessment. The extract → verify → corroborate pattern (Apple ODKE+) achieves 98.8% precision; cost-conscious alternatives include temperature-varied self-consistency (CISC, 53% cost reduction).

## 2. Source Quality Review

| Report | Evidence Density (0–5) | Practical Applicability (0–5) | Specificity (0–5) | Internal Consistency (0–5) | Overall (0–5) | Commentary |
|---|---|---|---|---|---|---|
| **Report 1 (OpenAI Deep Research)** | 4 | 4 | 4 | 4 | **4.0** | Strong on LangExtract (unique find), good architecture section, well-sourced. Slightly over-relies on LangExtract as a silver bullet. The star count claim (~1.7K) needs verification. Pipeline stages are practical but generic. Coreference and relationship sections lack depth compared to Report 2. |
| **Report 2 (Claude Opus)** | 5 | 5 | 5 | 5 | **5.0** | The highest-quality report by a significant margin. Uniquely cites specific benchmarks (KGGen 18% improvement, SLIDE 24%/39%, ODKE+ 98.8% precision, LINK-KG 45.21% dedup reduction, IncRML 315x storage reduction). Provides concrete cost estimates ($3–10 for 300pp). The three-tier cascade, blocking math, and event-sourcing recommendations are implementation-ready. Only report to cite Maverick, CISC, Tem-DocRED, and BYU hierarchical extraction. |
| **Report 3 (Gemini Pro)** | 3 | 4 | 4 | 4 | **3.8** | Practical and well-structured with clear Recommended/Runner-up/Avoid format. The LangGraph + Instructor recommendation is sound and actionable. Weaker on evidence — most claims lack specific citations or benchmarks. The Map-Reduce framing is useful. Bipartite output (Entities + Mentions) is a clean conceptual contribution. Slightly overconfident in some assertions (e.g., "20-40% higher retrieval" for structural chunking cited to "Unstructured.io benchmarks" without links). |
| **Report 4 (GPT 5.2 Pro)** | 0 | 0 | 0 | 0 | **0.0** | API error — no content produced. Excluded from synthesis. |
| **Report 5 (Grok)** | 3 | 4 | 3 | 4 | **3.5** | Solid survey with reasonable recommendations. Agrees with the consensus on Microsoft GraphRAG and LlamaIndex. Less specific than Reports 1–2 on provenance implementation details. The provenance table example is a useful contribution. Weaker on academic citations (mentions ProvSEEK, CRAC 2025 but provides less analysis). Some recommendations overlap with others without adding new evidence. |

**Weighting decision**: Report 2 (Claude Opus) is weighted most heavily due to its substantially higher evidence density, concrete benchmarks, cost modeling, and implementation specificity. Report 1 (OpenAI) is weighted second for its unique LangExtract discovery and solid architecture. Report 3 (Gemini) provides useful framing. Report 5 (Grok) provides corroboration. Report 4 is excluded.

## 3. Consolidated Findings by Topic

### 3.1 Tool Landscape

**Consensus findings (high confidence):**
- No tool delivers the complete pipeline out of the box (all 4 reports agree)
- Microsoft GraphRAG is the most mature/adopted LLM-driven KG construction pipeline (~31K stars) (Reports 2, 3, 5)
- Instructor is the best building block for structured LLM extraction with custom schemas (Reports 1, 2, 3, 5)
- OpenIE/ReVerb/OLLIE are outdated and should be avoided (Reports 1, 2, 5)
- Commercial services (Comprehend, Document AI, Diffbot) lack the provenance richness needed (Reports 1, 2, 3, 5)
- spaCy is useful as a preprocessing component (coref, fast NER) but insufficient alone (Reports 1, 2, 3, 5)

**Key tool discoveries by report:**
- **LangExtract** (Google): Only Report 1 extensively covers this. Character-level source grounding is a unique capability. However, it lacks identity resolution and relationship extraction. Best understood as a *component* for the extraction stage, not a complete solution.
- **Neo4j GraphRAG Python**: Only Report 2 covers this in depth. The built-in entity resolution (FuzzyMatchResolver, SpaCySemanticMatchResolver) is a unique differentiator. Still labeled "experimental."
- **Graphiti** (Zep): Only Report 2 covers this. Bi-temporal provenance model is the most sophisticated of any tool. Designed for conversational memory, not batch document processing.
- **KGGen**: Only Report 2 cites this (NeurIPS 2025). Two-pass pattern demonstrated 18% improvement over GraphRAG on MINE benchmark.
- **LightRAG**: Only Report 3 mentions this as an alternative to GraphRAG.
- **Relik** (Sapienza): Reports 1 and 2 cover this. Fast entity linking + relation extraction on BERT-era models. Useful as a cost-effective first pass.
- **GLiNER**: Only Report 2 mentions this. Zero-shot NER on single GPUs — useful for the cheap first tier.

### 3.2 Architecture

**Consensus on pipeline ordering:**
All reports agree on a multi-stage pipeline. The specific ordering has a critical divergence:

| Stage | Report 1 | Report 2 | Report 3 | Report 5 |
|---|---|---|---|---|
| 1 | Chunk + Clean | Coreference | Local Extraction (Map) | Chunk with metadata |
| 2 | Mention extraction | Entity + Rel extraction | Identity Resolution (Shuffle) | Per-chunk extraction |
| 3 | Coreference | Cross-chunk entity resolution | Attribute Aggregation (Reduce) | Global identity resolution |
| 4 | Entity linking | Entity summarization | — | Relationship extraction |
| 5 | Attribute extraction | Verification pass | — | Fact aggregation |
| 6 | Relationship extraction | — | — | — |
| 7 | Merge + dedup | — | — | — |

**Adjudication**: Report 2's coreference-first ordering is best supported by evidence (LINK-KG 45.21% node dedup reduction, CORE-KG 38.37% noise reduction). Resolving "he/she/the eldest boy" to canonical names *before* extraction ensures the LLM works with unambiguous text, producing cleaner entities and relationships downstream.

**Consensus on input contract:**
- Pre-chunked JSONL with metadata (chunk_id, text, document_id, source location) — all reports agree
- Tool should optionally handle chunking itself — Reports 1, 2, 5 agree; Report 3 argues chunking should stay out of the library. Adjudication: accept both, with built-in chunking as convenience.

**Consensus on output contract:**
- Property graph beats RDF (Reports 2, 3, 5 agree; Report 1 doesn't address RDF directly)
- Must include both raw mentions and resolved entities (Reports 2, 3 agree explicitly)
- Evidence should be hybrid: inline IDs on entities/edges → separate evidence store (Report 2's strongest articulation; Report 3's bipartite model is equivalent)

**Consensus on distribution:**
- Python library first, CLI wrapper second, service later (all reports agree)

### 3.3 Chunking

**Consensus (high confidence):**
- Structure-aware chunking (scenes, chapters) dramatically outperforms fixed-token chunking (all reports agree)
- Overlap at boundaries (10–20%) is essential to capture cross-boundary relationships (Reports 1, 2, 5)
- SLIDE-style overlapping windows improve extraction by 24% (entities) and 39% (relationships) (Report 2, specific benchmark)
- Entity registry/roster should be propagated across chunks (Reports 1, 2, 3, 5)

### 3.4 Identity Resolution

**Consensus (high confidence):**
- This is the hardest unsolved problem and the weakest link in all existing tools (all reports)
- Blocking strategies (token, embedding ANN) are essential to avoid O(n²) at scale (Reports 2, 3, 5)
- Hybrid approach: cheap embedding similarity for candidate generation → LLM for final disambiguation (Reports 2, 3, 5)
- Graph structure assists resolution: if two "Sarah" mentions share a spouse "David," they're likely the same person (Report 3's unique contribution)
- Genealogy-specific blocking keys: surname + generation + geography (Report 2)

### 3.5 Confidence Scoring

**Consensus (high confidence):**
- LLM self-assessed confidence is unreliable (Reports 2, 3 explicitly state this)
- External verification (separate model validates extracted facts against source) is the gold standard (Reports 2, 3)
- ODKE+ pattern achieves 98.8% precision via extract → ground → corroborate (Report 2)
- Multi-sample self-consistency with confidence weighting (CISC) reduces costs 53% (Report 2)
- Frequency across chunks is a useful heuristic signal (Report 1)

### 3.6 Scalability (300-page Genealogy)

**Consensus:**
- Tractable with chunking + parallel processing + tiered models (all reports)
- Estimated cost: $3–10 for 300 pages (Report 2; no other report provides a cost estimate)
- Estimated time: 5–15 minutes (Report 2; no other report estimates time)
- Genealogy-specific patterns (Ahnentafel numbering, generational naming) require domain-specific extraction templates (Reports 1, 2, 5)
- Temporal validation (parents born before children, marriage within lifetimes) provides cheap deterministic quality checks (Reports 2, 5)

## 4. Conflict Resolution Ledger

| Claim | Conflicting Views | Adjudication | Confidence |
|---|---|---|---|
| **Best overall tool recommendation** | R1: LangExtract (5/5). R2: Neo4j GraphRAG Python (4.5/5). R3: Instructor + LangGraph (4.8/5). R5: Microsoft GraphRAG (4.5/5). | **No single tool; build a custom pipeline using Instructor for extraction, with Microsoft GraphRAG or Neo4j GraphRAG Python as the graph construction framework.** LangExtract is valuable for its provenance grounding but is not a complete solution (no identity resolution, no relationship extraction). Neo4j GraphRAG Python's entity resolution is compelling but experimental. Microsoft GraphRAG is most proven at scale. Instructor is the universally agreed building block. The recommendation is a composed system, not a single tool. | High |
| **Should chunking be in or out of the library?** | R3: Keep chunking out; let consumers pre-chunk. R1, R2, R5: Tool should handle chunking with built-in support. | **Accept both pre-chunked input AND provide built-in structural chunking.** The three consuming projects (screenplay, memoir, gamebook) have different structural conventions. Built-in chunking with configurable strategies (scene-aware, chapter-aware, sliding-window) reduces integration burden while JSONL input preserves flexibility. | High |
| **Pipeline ordering: coreference first or after extraction?** | R1, R5: Extract mentions first, then coreference, then linking. R2: Coreference first, then extraction. R3: Extract per-chunk (implicitly includes coref within chunk), then global resolution. | **Coreference first (within-chunk), then extraction on resolved text.** R2 cites LINK-KG (45.21% dedup reduction) and CORE-KG (38.37% noise reduction) as direct evidence. The logic is sound: resolving "he" → "John Smith" before extraction means the LLM extracts facts about "John Smith" consistently, not about "he." This is consistent with the Relik/Coreferee pipeline documented in R1. | High |
| **GraphRAG entity resolution quality** | R2: "notably weak — 'Jon' and 'Jon Márquez' remain separate nodes." R5: "Partial (community clustering)." R1: "Yes (Graph context linking)." | **GraphRAG's entity resolution IS weak for fine-grained disambiguation.** R2 provides specific failure examples. Community clustering helps group related entities but does not merge co-referent mentions. R1's assessment is too generous. This is a known limitation documented in GraphRAG issues. | High |
| **LangExtract star count and maturity** | R1: "~1.7K stars, Active (2024)." R2: "Released December 2025." | **R2's timeline is more recent and likely more accurate.** LangExtract is a relatively new Google project. The star count is plausible but should be verified. The key point is that it exists and provides character-level source grounding — both reports agree on this capability. | Medium |
| **Cost estimate for 300-page processing** | R2: "$3–10, 5–15 minutes." No other report provides estimates. | **Accepting R2's estimate as the best available, with the caveat it assumes the three-tier cascade and prompt caching.** Without tiering (all premium), costs could be 5–10x higher. The estimate is well-reasoned (160–200K input tokens × 3–5x processing overhead × tiered pricing). | Medium |
| **RDF vs property graph** | R2: "Property graphs beat RDF" — RDF requires cumbersome reification for provenance. R1: Suggests JSON graph but doesn't address RDF. Others: no strong opinion. | **Property graph is correct for this use case.** RDF reification or named graphs for provenance is genuinely awkward and adds complexity without benefit when the consumers are application developers, not semantic web users. | High |
| **Event sourcing for incremental processing** | R2: Advocates event sourcing (entity_discovered, relationship_found events). R3: Advocates append-only mentions. R1, R5: Describe incremental merge without specifying the pattern. | **Event sourcing is the right pattern but pragmatically, start with append-only mentions + periodic re-resolution.** Full event sourcing adds significant implementation complexity. The append-only mention store (R3) achieves 80% of the benefit. Upgrade to full event sourcing when versioning/replay requirements materialize. | Medium |

## 5. Decision Matrix

Weighted scoring for the framework/foundation choice (not the complete pipeline — every option requires custom work):

| Criterion (Weight) | Microsoft GraphRAG | Neo4j GraphRAG Python | Instructor + Custom Pipeline | LangExtract + Custom |
|---|---|---|---|---|
| **Entity extraction quality (15%)** | 4 | 4 | 5 (schema-controlled) | 5 |
| **Relationship extraction (15%)** | 5 (typed + claims) | 4 | 4 (custom) | 2 (not built-in) |
| **Provenance/evidence fidelity (20%)** | 3 (text-unit IDs, loses quotes in summaries) | 3 (FROM_CHUNK edges, no quotes) | 5 (fully custom with quote fields) | 5 (character-level grounding) |
| **Identity resolution (20%)** | 2 (weak) | 4 (fuzzy + semantic, experimental) | 3 (must build) | 1 (not built-in) |
| **Scalability to 300pp (10%)** | 5 (designed for corpora) | 4 (async pipeline) | 4 (must orchestrate) | 4 (multi-pass) |
| **Maturity/community (10%)** | 5 (31K stars, Microsoft) | 3 (newer, ~1K stars) | 5 (12.4K stars, 6M PyPI/mo) | 2 (newer, single-purpose) |
| **Flexibility for 3 domains (10%)** | 3 (rigid pipeline) | 4 (configurable) | 5 (fully custom) | 3 (extraction only) |
| **Weighted Total** | **3.45** | **3.55** | **4.40** | **3.25** |

**Scoring rationale**: Provenance fidelity and identity resolution are weighted highest (20% each) because they are the two capabilities that distinguish this project from standard NER. Instructor + Custom Pipeline scores highest because it provides maximum control over both — the evidence schema is whatever you define in Pydantic, and identity resolution can be implemented exactly as needed. The trade-off is more engineering effort upfront.

## 6. Final Recommendation

### Build a custom multi-stage pipeline using Instructor as the extraction core, with optional integration of Microsoft GraphRAG or Neo4j GraphRAG Python components.

**Concrete architecture:**

```
┌─────────────────────────────────────────────────────┐
│                    INPUT LAYER                        │
│  Raw text OR pre-chunked JSONL                       │
│  Built-in chunkers: scene-aware, chapter-aware,      │
│  SLIDE-style overlapping (configurable via YAML)     │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│            STAGE 1: COREFERENCE (per-chunk)          │
│  spaCy + Coreferee (or Maverick for quality)         │
│  Rewrite pronouns/aliases → canonical surface forms  │
│  Output: resolved text + coref chain metadata        │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│         STAGE 2: EXTRACTION (per-chunk, parallel)    │
│  Instructor + Pydantic schemas                       │
│  Tier 1 model (GPT-4o-mini / Haiku) for:            │
│    - Person mentions with evidence quotes            │
│    - Biographical attributes with evidence quotes    │
│    - Relationships with evidence quotes              │
│    - Each fact carries: quote, chunk_id, char_offset │
│  Entity roster injected into prompt for consistency  │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│       STAGE 3: IDENTITY RESOLUTION (global)          │
│  a) Token blocking (group by shared name tokens)     │
│  b) Embedding similarity within blocks (HNSW ANN)   │
│  c) LLM judge (Tier 2 model) for ambiguous pairs    │
│  d) Graph-assisted: shared relations boost merging   │
│  Output: canonical entity IDs, alias mappings        │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│       STAGE 4: VERIFICATION (selective)              │
│  Tier 2 model validates extracted facts vs source    │
│  Assigns confidence scores (0.0–1.0)                │
│  Flags contradictions for human review               │
│  Only runs on low-confidence or high-stakes facts    │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│              OUTPUT LAYER                             │
│  JSON property graph:                                │
│    - entities[] (canonical, with all attributes)     │
│    - mentions[] (raw, with source locations)         │
│    - relationships[] (between resolved entities)     │
│    - evidence_store[] (quotes, offsets, confidence)  │
│  Optional: Neo4j import, NetworkX, or graph DB       │
└─────────────────────────────────────────────────────┘
```

**Why this over alternatives:**

1. **vs. "just use GraphRAG"**: GraphRAG loses exact quotes in its summarization pipeline and has weak entity resolution. You'd spend more time fighting its pipeline than building your own.
2. **vs. "just use LangExtract"**: LangExtract handles extraction + provenance beautifully but has zero identity resolution or relationship extraction. You'd need to build everything else anyway.
3. **vs. "just use Neo4j GraphRAG Python"**: The entity resolution is compelling but experimental, and you're locked into Neo4j as the graph store. The pipeline is less flexible for three diverse consuming projects.
4. **vs. "build everything from scratch"**: Instructor, spaCy/Coreferee, and embedding libraries (sentence-transformers) provide battle-tested components. The custom work is in orchestration, schema design, and the resolution logic — not in the extraction mechanics.

**Key dependencies:**
- `instructor` — structured LLM extraction with Pydantic
- `spacy` + `coreferee` (or `maverick` for higher quality) — within-chunk coreference
- `sentence-transformers` — entity embeddings for blocking
- `hnswlib` or `faiss` — approximate nearest neighbor for entity resolution blocking
- `pydantic` — schema definitions for input, output, and evidence
- `click` — CLI wrapper
- LLM provider: Anthropic Claude (Haiku for Tier 1, Sonnet for Tier 2, Opus for Tier 3) or OpenAI (4o-mini, 4o, o1/o3)

## 7. Implementation Plan / Next Steps

### Phase 1: Core Pipeline (Weeks 1–3)
1. **Define Pydantic schemas**: `Mention`, `Entity`, `Relationship`, `Evidence`, `ExtractionResult`
2. **Implement JSONL input contract** with built-in scene-aware and chapter-aware chunkers
3. **Build per-chunk extraction** using Instructor with evidence-quote enforcement
4. **Implement entity roster** that grows across chunks and injects into prompts
5. **Wire up spaCy + Coreferee** for within-chunk coreference as a preprocessing step
6. **Output JSON property graph** with the three-layer structure (mentions, entities, relationships + evidence store)

### Phase 2: Identity Resolution (Weeks 3–5)
7. **Implement token blocking** (group mentions by shared name tokens)
8. **Add embedding-based similarity** within blocks using sentence-transformers + HNSW
9. **Build LLM judge** for ambiguous pairs (Tier 2 model)
10. **Add graph-assisted merging** (shared relations boost merge confidence)
11. **Test on 10-page screenplay** (CineForge scenario) — target: 15 characters correctly resolved

### Phase 3: Verification & Confidence (Weeks 5–6)
12. **Implement verification pass** (separate LLM validates facts against source quotes)
13. **Add confidence scoring** (verification result + frequency + evidence count)
14. **Add contradiction detection** and human-review flagging
15. **Test on 100-page document** (Storybook scenario) — target: 100 entities, <5% error rate

### Phase 4: Scale & Domain Adaptation (Weeks 6–8)
16. **Implement three-tier model cascade** with configurable tier assignment
17. **Add YAML profile system** (base + screenplay + genealogy + fiction overlays)
18. **Add incremental processing** (append new mentions, re-resolve against existing roster)
19. **Genealogy stress test** (300-page book) — target: $10 budget, <15 minutes, >90% entity resolution accuracy
20. **Add CLI wrapper** with `extract`, `resolve`, `verify`, and `export` commands

### Phase 5: Polish (Weeks 8–10)
21. **Add domain-specific extractors** (screenplay dialogue cues, genealogy numbering systems, gamebook stats)
22. **Performance optimization** (prompt caching, batch API calls, parallel chunk processing)
23. **Documentation and examples** for each consuming project
24. **Publish as Python package** (`pip install entity-provenance`)

## 8. Open Questions & Confidence Statement

### High Confidence (supported by multiple reports + benchmarks)
- Two-pass extraction (extract → verify) outperforms single-pass
- Coreference before extraction improves downstream quality
- Structure-aware chunking with overlap outperforms fixed-token chunking
- Property graph output with separate evidence store is the right format
- Blocking strategies make entity resolution tractable at genealogy scale
- LLM self-reported confidence is unreliable; external validation is needed

### Medium Confidence (supported by 1–2 reports with evidence)
- Cost estimate of $3–10 for 300 pages (depends on model pricing, which changes frequently)
- Neo4j GraphRAG Python's entity resolution will mature into production quality
- LangExtract's character-level grounding is reliable at scale (newer tool, less community testing)
- Event sourcing is the optimal incremental processing pattern (vs. simpler append-only)

### Open Questions (insufficient evidence across all reports)
- **Cross-document identity resolution across different document types** (e.g., merging a person mentioned in a transcript with the same person in a memoir) — no tool or paper demonstrates this reliably at scale. Our pipeline handles it in theory (global roster), but quality is unproven.
- **Optimal overlap percentage** for chunking — 10–20% is cited by multiple reports but no benchmark directly compares percentages. SLIDE provides the closest evidence but doesn't isolate overlap percentage as a variable.
- **Calibration of confidence scores** — even with verification passes, producing well-calibrated probabilities (where "0.8 confidence" means the fact is true 80% of the time) is not demonstrated in any cited system. Scores should be treated as ordinal rankings, not calibrated probabilities.
- **Hallucination rate at 300-page scale** — Report 2 cites 5–15% single-pass hallucination, but this is from general LLM benchmarks, not entity extraction specifically on long narratives. Actual rates with enforced evidence quotes may be lower.
- **How well does the entity roster injection scale?** — At 500 entities, the roster itself consumes significant prompt tokens. No report addresses the point at which the roster exceeds practical prompt budgets. Likely need to inject only the most relevant entities (by embedding similarity to the current chunk) rather than the full roster.

### Confidence Statement
The core architectural recommendations (multi-stage pipeline, Instructor for extraction, coreference-first, blocking-based entity resolution, property graph output with evidence store) are well-supported by converging evidence across 4 independent reports and multiple academic benchmarks. The specific tool and cost recommendations carry moderate uncertainty due to rapid field evolution (GraphRAG, KGGen, LangExtract, and Neo4j GraphRAG Python all shipped major changes in 2024–2025). The genealogy stress test is theoretically tractable but unvalidated end-to-end at the specified scale by any cited system. **Plan for a proof-of-concept on the screenplay use case first** (smallest scale, most structural signals) before committing to the genealogy architecture.
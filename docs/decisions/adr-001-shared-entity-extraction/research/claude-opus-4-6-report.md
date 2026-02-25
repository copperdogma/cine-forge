---
type: research-report
topic: shared-entity-extraction
canonical-model-name: claude-opus-4-6
research-mode: standard
collected: '2026-02-24T16:20:12.312922+00:00'
---

# Provenance-rich entity extraction from unstructured text

**No single existing tool fully implements LLM-driven entity extraction with evidence chains, confidence scores, and cross-chunk identity resolution — but a viable system can be assembled today.** The closest production-ready foundation is Neo4j's GraphRAG Python package, which uniquely offers built-in entity resolution alongside schema-guided extraction. The recommended architecture is a multi-stage pipeline using tiered LLM models: cheap models for initial NER, mid-tier for relationship classification, and premium models reserved for the hardest 5–10% of disambiguation decisions. A 300-page genealogy book can be processed for **$3–10 in approximately 5–15 minutes** using this approach. The critical insight from academic research is that two-pass patterns (extract → verify/resolve) consistently outperform single-pass extraction across every dimension — entity quality, relationship accuracy, and provenance fidelity.

---

## Area 1: The open-source landscape is rich but fragmented

Twenty-plus tools were evaluated across five tiers: full KG construction pipelines, building-block libraries, traditional NLP tools, commercial APIs, and emerging frameworks. The field has exploded since 2024, driven by LLM structured output capabilities, but **no tool delivers the complete pipeline** of chunked extraction with evidence quotes, identity resolution, relationship extraction, and confidence scoring out of the box.

### The top five candidates ranked by fit

| Criteria | Neo4j GraphRAG Python | Microsoft GraphRAG | Graphiti (Zep) | LlamaIndex PropertyGraph | KGGen |
|---|---|---|---|---|---|
| **Fit score** | **4.5/5** | 4.0/5 | 4.0/5 | 3.5/5 | 3.5/5 |
| Entity extraction | ✅ Schema-guided, typed | ✅ LLM-based, configurable | ✅ Custom types, episodic | ✅ Multiple extractors | ✅ Two-pass |
| Relationship extraction | ✅ Typed with properties | ✅ With descriptions | ✅ Semantic edges | ✅ Typed relations | ✅ Entity-aware |
| Provenance | ✅ FROM_CHUNK edges | ✅ text_unit_ids | ✅✅ **Bi-temporal + episodes** | ⚠️ Metadata only | ⚠️ Implicit |
| Identity resolution | ✅✅ **Fuzzy + semantic** | ⚠️ Name matching only | ✅ Built-in dedup | ⚠️ None built-in | ✅ LLM clustering |
| Scalability (300pp) | ✅ Async pipeline | ✅ Designed for corpora | ✅ Parallel LLM calls | ✅ num_workers | ✅ Proven at scale |
| GitHub stars / backing | ~1K (Neo4j official) | **~30.9K** | ~5K (Zep AI) | ~40K (LlamaIndex) | NeurIPS 2025 |

**Neo4j GraphRAG Python** earns the top spot because it is the only tool with production-grade entity resolution (both `FuzzyMatchResolver` using RapidFuzz and `SpaCySemanticMatchResolver` for semantic similarity). It covers the full pipeline from PDF parsing through graph storage and retrieval, supports any major LLM provider, and is backed by Neo4j's long-term commitment. The key weakness: entity resolution is still labeled "experimental," and provenance requires custom enrichment to include evidence quotes.

**Microsoft GraphRAG** (~30.9K stars) is the most mature and widely adopted. Its community detection via the Leiden algorithm and hierarchical summarization are unique strengths. However, its entity disambiguation is notably weak — "Jon" and "Jon Márquez" remain separate nodes. It's designed primarily for RAG retrieval, not standalone KG construction, and LLM indexing costs are high.

**Graphiti** from Zep AI has the **best provenance model** of any tool surveyed: bi-temporal tracking (`valid_at`/`invalid_at` for when facts were true, `created_at`/`expired_at` for when they were recorded) with episodic linkage back to source data. It also handles incremental updates natively. The limitation: it's designed for conversational agent memory rather than batch document processing, requiring adaptation for the 300-page book scenario.

### Notable building blocks worth integrating

**Instructor** (jxnl, ~12.4K stars, 6M+ monthly PyPI downloads) is not an extraction pipeline but the best low-level building block for defining provenance-rich Pydantic schemas with `evidence_quote`, `confidence_score`, and `source_location` fields, then extracting structured data from any LLM. **LangExtract** from Google (released December 2025) provides character-level source grounding — every extraction maps to exact character positions in source text — and handles 100–300+ page documents with smart chunking. **KGGen** (NeurIPS 2025) demonstrated an **18% absolute improvement over GraphRAG** on the MINE benchmark by using a two-pass pattern: extract entities first, then extract relations given the entity list, then cluster/merge.

For cost-effective preprocessing, **GLiNER** (zero-shot NER, ~3.5K stars) and **ReLiK** (Sapienza NLP, joint entity linking + relation extraction) run on single GPUs with BERT-era models, offering entity detection at a fraction of LLM costs. These can serve as the fast first pass before expensive LLM reasoning.

### What to avoid

**OpenIE/ReVerb/OLLIE** — academic tools from the pre-LLM era that are mostly unmaintained and superseded in quality. **Amazon Comprehend** and **Google Document AI** — designed for form/invoice extraction, not narrative KG construction. **REBEL** alone — efficient joint NER+RE but provides no evidence spans, confidence scores, or identity resolution. **Diffbot** — excellent provenance and entity disambiguation against their 10B+ entity KG, but commercial and closed-source.

---

## Area 2: Academic research converges on multi-stage hybrid pipelines

### Evidence-grounded entity extraction has matured rapidly

The field has shifted decisively from flat NER to structured entity extraction with source attribution. **MuSEE** (EMNLP 2024) reformulated extraction as entity-centric rather than triplet-centric, introducing the AESOP metric family for evaluating multi-property entity extraction — exactly what biographical extraction needs. The key finding: extracting entities with their attributes in a single entity-focused pass outperforms traditional triplet extraction.

For long documents, the **"lost in the middle"** problem (Liu et al., 2024) is the critical constraint: LLMs systematically miss information buried in the middle of long contexts. This makes chunking mandatory rather than optional, even with 128K+ context windows. **LangExtract** addresses this with sentence-aware overlapping chunks and multi-pass extraction with stochastic sampling to improve recall — processing 10K documents in half a day for ~$300.

The practical comparison between LLM and traditional NER is nuanced. For standard entity types (person names, organizations, locations), traditional models like spaCy remain highly competitive and orders of magnitude cheaper. **LLMs are dramatically superior for structured entity extraction** — extracting entities with multiple typed attributes (birth dates, occupations, family roles) where traditional models fail entirely. The recommended hybrid: use GLiNER or spaCy for entity detection, then LLMs for attribute enrichment.

### Relationship extraction requires filtering before classification

A critical finding from **LMRC** (Li et al., 2024): on document-level relation extraction benchmarks, **LLM-based methods still lag behind BERT-based approaches** because the massive number of no-relation entity pairs disperses the model's attention. The solution — a two-stage hybrid where a lightweight RoBERTa classifier first filters entity pairs likely to have relations, then an LLM classifies the filtered set — significantly narrows the gap with SOTA.

For narrative text specifically, **Yan et al. (2025)** constructed the NCRE dataset with 100 characters and 3,591 relationship instances across three dimensions (polarity, age/generation, social role), demonstrating that LLM-based approaches significantly outperform traditional baselines on literary relationship extraction. For temporal relationships (critical for genealogy), **Tem-DocRED** (Nature Scientific Data, 2025) introduced the first systematic approach to extracting relation quadruples — (subject, relation, object, temporal_info) — from documents.

The recommended approach for provenance-rich relationship extraction is a three-step pipeline: (1) entity detection via GLiNER or fine-tuned NER, (2) candidate pair filtering via lightweight classifier, (3) LLM-based relation classification with simultaneous evidence quote extraction. This balances cost, quality, and provenance requirements.

### Cross-document identity resolution is the critical bottleneck

Every major tool and framework identifies entity resolution as its weakest link. **Maverick** (ACL 2024, Sapienza NLP) achieves SOTA coreference on CoNLL-2012 with a 500M parameter encoder — **170x faster** and using 0.006x the memory of 13B+ generative models. For long documents, **hierarchical entity merging** (Gupta et al., LaTeCH-CLfL 2024) recursively merges entity clusters across chunks, enabling coreference for arbitrarily long documents including full novels.

The emerging consensus is a **hybrid supervised + LLM approach** (ImCoref-CeS, 2025): use efficient encoder models for initial coreference resolution, then deploy LLM reasoning only for ambiguous cases. This achieves higher accuracy than either approach alone while managing costs. For alias detection, the **STANCE** system uses optimal transport-based string similarity, improving cross-document coreference by +2.8 B³ F1.

Scaling to hundreds of entities requires blocking strategies to avoid O(n²) comparisons. With **500 entities**, naive pairwise comparison means 124,750 pairs; with token blocking (average block size 10), this drops to ~2,500 comparisons. Embedding-based approaches using HNSW approximate nearest neighbor search reduce this further to ~500–1,000 comparisons with negligible accuracy loss.

### Chunking strategy matters more than model choice

**SLIDE** (2025) demonstrated that overlapping sliding window chunking improves entity extraction by **24%** and relationship extraction by **39%** compared to baseline GraphRAG chunking — a larger improvement than upgrading the LLM model. The mechanism: each chunk receives additional context from surrounding windows, preventing information loss at boundaries.

The recommended hierarchy of chunking strategies for this use case:

- **Best for structured documents** (screenplays, chapter-based books): Scene/chapter-aware chunking respecting narrative boundaries, with 15–20% overlap
- **Best for unstructured narrative**: SLIDE-style overlapping windows at paragraph boundaries, 800–2,048 tokens per chunk
- **Best for very long documents** (300+ pages): Hierarchical chunking — chapter-level first, then sub-chapter chunks within each chapter, with a running entity registry propagated across chunks

The **entity registry pattern** is critical: maintain a growing list of known entities and inject the top entities into each chunk's extraction prompt, so the LLM can recognize returning characters. KGGen, LINK-KG, and NVIDIA all recommend this approach independently.

### Confidence scoring demands external validation

LLM self-reported confidence is consistently unreliable — research shows systematic overconfidence. The gold standard is Apple's **ODKE+** pipeline, which achieves **98.8% precision** on 19 million extracted facts using a two-LLM pattern: one LLM extracts, a second LLM validates each fact against source evidence, then a corroborator ranks and normalizes. This "extract → ground → corroborate" pattern is the highest-precision approach documented.

For cost-conscious implementations, **confidence-weighted self-consistency** (CISC, ACL Findings 2025) extends the self-consistency method by extracting confidence from each sample and using it to weight votes. This achieves statistically significant improvements over standard self-consistency while reducing computational cost by **up to 53%**. The practical implementation: generate 2–3 extraction samples at temperature 0.3–0.7, ask the LLM for confidence on each, use temperature-scaled softmax for normalization, and accept facts that exceed a threshold — flagging the rest for human review.

---

## Area 3: Architecture should follow the two-pass pattern

### Input contract: accept both raw and pre-chunked

The ideal input format is structured JSON objects per chunk carrying embedded metadata — `chunk_id`, `text`, `document_id`, and a `metadata` dict with `page_number`, `chapter`, `scene`, `speaker`, and character position offsets. Both GraphRAG and LlamaIndex internally convert plain text to similar structured objects. The tool should **accept both pre-chunked and raw text**, with built-in chunking as default. This accommodates screenplay scene-based splitting (where consumers know the natural boundaries) while handling unstructured memoir text automatically.

For the three consuming projects, metadata needs differ: screenplays require `act`, `scene`, `speaker`, and `stage_direction` fields; memoir/transcripts need `chapter`, `page_number`, `speaker`, and `timestamp_range`; interactive fiction needs `chapter`, `narrator`, `point_of_view`, and `location_context`. A YAML profile system with inheritance cleanly handles these variations.

### The optimal pipeline is coreference-first, then extraction

Research from **LINK-KG** (2025) and **CORE-KG** (2025) decisively favors resolving coreferences before extracting entities and relationships. LINK-KG's three-phase pipeline (NER-LLM → Mapping-LLM with prompt cache → Resolve-LLM) achieved a **45.21% reduction in node duplication** versus baselines. CORE-KG's type-aware coreference resolution reduced noise by **38.37%** compared to GraphRAG's default joint extraction.

The recommended pipeline ordering:

1. **Coreference resolution** — resolve pronouns, aliases, and descriptive references to canonical forms, producing "resolved text"
2. **Entity + relationship extraction** (combined, per chunk) — extract from resolved text using schema-guided LLM prompts
3. **Cross-chunk entity resolution** — merge duplicate entities across chunks using fuzzy matching + semantic similarity
4. **Entity summarization** — LLM consolidates multiple descriptions of each entity into a canonical profile
5. **Verification pass** — second LLM validates extracted facts against source text, assigning confidence scores

For the "entity roster" problem, the **discover-then-detail** two-pass approach with an incrementally built roster is optimal. As each chunk is processed, discovered entities are added to a prompt cache, and subsequent chunks reference this cache for consistency. This avoids both the fragmentation of single-pass extraction and the double cost of two full passes.

### Output should be a JSON property graph with a separate evidence store

**Property graphs beat RDF** for this use case. RDF inherently lacks mechanisms to attach provenance data to statements (requiring cumbersome workarounds like reification or named graphs), while property graphs natively support properties on both nodes and edges. The output schema should have three layers: **mentions** (raw extractions with source locations and character offsets), **entities** (resolved/canonical, linking to their mentions), and **relationships** (between resolved entities, linking to evidence).

The provenance structure should be hybrid: inline evidence IDs on entities and relationships pointing to a separate evidence store containing surface forms, context snippets, character offsets, extraction confidence, model version, and extraction timestamp. This keeps the entity graph clean while preserving full audit trails. Both raw mentions and resolved entities must be preserved — for error correction, auditability, and consumer flexibility (film analysis needs character aliases; genealogy needs birth names vs. married names).

### Incremental processing via event sourcing

The extraction pipeline is a natural fit for event sourcing. Each extraction produces immutable events (`entity_discovered`, `relationship_found`, `attribute_updated`), and the current entity graph is a materialized view computed from all events. This enables adding new documents without full reprocessing, reconstructing any past version by replaying events to a timestamp, and re-running with a better model by replaying from the same source events. **IncRML** demonstrated that incremental KG construction using change data capture achieves **up to 315x less storage and 4.4x less CPU time** versus full regeneration.

Conflict resolution follows an additive model: never delete old evidence, add new evidence with source and timestamp, weight by source reliability and recency, and flag contradictions for human review.

### Start as a library with a thin CLI wrapper

The recommended interface is **library-first with a CLI wrapper** — not a service. A service-first architecture is premature for an early-stage tool and adds infrastructure overhead without benefit. The library should be fully usable programmatically (composable, testable, type-safe), with a thin Click-based CLI enabling scriptable batch processing. A REST/gRPC service can be added later when scale demands it. Configuration should use YAML profiles with inheritance — a base profile plus domain-specific overlays for screenplay, genealogy, and fiction extraction.

---

## Area 4: The 300-page genealogy book is tractable with tiered models

### Token budget management with a three-tier cascade

A 300-page book contains roughly **160,000–200,000 tokens** of input text. With chunking overhead (15% overlap) and multiple extraction passes, expect 3–5x the base tokens processed. The breakthrough cost optimization is a **three-tier model cascade**:

- **Tier 1 (cheap, $0.15–0.80/M tokens)**: GPT-4o Mini or Claude Haiku 3.5 for initial NER — extracting all person mentions, dates, and locations. Budget models handle straightforward extraction identically to premium models for 70–80% of workloads.
- **Tier 2 (mid-range, $3–5/M tokens)**: Claude Sonnet or GPT-4o for coreference resolution, relationship classification, and initial entity disambiguation.
- **Tier 3 (premium, $15/M tokens)**: Claude Opus or equivalent for only the hardest 5–10% of decisions — distinguishing three different "John Smith" entities or resolving contradictory evidence.

This cascade achieves **60–90% cost reduction** versus using premium models for everything. Additional optimizations include Anthropic's prompt caching (cache reads at 0.1x base rate, yielding 90% savings on repeated context), batch processing APIs (50% discount for non-real-time jobs), and enforcing structured JSON output to minimize expensive output tokens (which cost 3–8x more than input).

**Estimated total: $3–10 for a 300-page book, processed in 5–15 minutes.**

### Identity resolution at scale requires blocking

For a genealogy book with **500 unique entities**, naive pairwise comparison generates 124,750 pairs — at ~100ms per LLM comparison, that's 3.5 hours. Blocking strategies reduce this dramatically:

- **Token blocking** (group by shared name tokens): ~2,500 comparisons, ~4 minutes
- **Embedding-based ANN** (HNSW approximate nearest neighbor): ~500–1,000 comparisons, ~1–2 minutes
- **Hierarchical resolution**: Resolve within chapters first (O(k²) per chapter where k ≪ n), then cross-chapter with surname + generation as blocking keys, then global merge with LLM verification for conflicts

For genealogy specifically, the blocking key should combine **surname + approximate generation + geographic context**. A name variant gazetteer handles diminutives (Elizabeth/Betty/Liz/Beth), anglicization (Giovanni/John), and patronymic systems. String similarity measures (Jaro-Winkler distance) serve as features alongside temporal and relational context for final disambiguation.

### Genealogy-specific patterns demand hierarchical extraction

Genealogy books have unique structural properties that extraction must exploit. Standard numbering systems (Ahnentafel, Register System, Henry System) encode generation depth and parent-child relationships directly in the text. George Nagy (Springer 2021) demonstrated that for semi-structured genealogy documents with consistent formatting, template-matching achieves **>99% NER precision** — far exceeding LLM-based approaches for these specific patterns.

The recommended extraction hierarchy is: (1) detect family units from narrative structure, (2) extract individuals with canonical names and vital dates, (3) extract attributes and relationships. BYU's hierarchical joint extraction improved fine-grained NER F1 from **0.4753 to 0.8563** by using relationship information to disambiguate entity types — proving that hierarchical context dramatically improves extraction quality in family history records.

Temporal disambiguation is the primary tool for resolving the "John Smith" problem in genealogy. When the same common name refers to 5–10+ different individuals across a book, birth/death dates, spousal relationships, and geographic context form a composite disambiguation signature. The one-sense-per-discourse assumption — standard in NLP — explicitly does not hold in genealogy texts. Diachronic named entity disambiguation models integrating temporal features outperform standard approaches "by large margins" on historical datasets.

### Validation closes the accuracy gap

Biological plausibility checks provide a cheap, deterministic validation layer: parents must be born before children (with reasonable generation gaps of 20–35 years), marriage dates must fall within lifetimes, and death dates must follow birth dates. These catch LLM hallucinations that violate temporal logic. The Cal Poly pipeline achieved **F1 = 0.871** for relationship classification alone, dropping to **F1 = 0.676** end-to-end — the gap being primarily entity resolution errors that propagate downstream.

---

## Putting it all together: the recommended build

### Primary recommendation: custom pipeline on Neo4j GraphRAG Python foundation

Build on **Neo4j GraphRAG Python** as the framework (for its entity resolution, graph storage, and pipeline infrastructure), enriched with **Instructor** for custom provenance-rich Pydantic extraction schemas, using **SLIDE-style overlapping chunking** and a **three-tier model cascade**. Add a verification pass using the ODKE+ extract-then-verify pattern. Output as a JSON property graph with a separate evidence store. Interface as a Python library with Click CLI and YAML configuration profiles.

### Runner-up: Microsoft GraphRAG + custom entity resolution layer

When community detection and hierarchical summarization are important (e.g., for the film analysis use case where understanding character communities matters), build on Microsoft GraphRAG and add a custom entity resolution post-processing step using Maverick + embedding-based clustering. This trades identity resolution quality for GraphRAG's superior community analysis and massive ecosystem. Choose this when the consuming application benefits more from global document understanding than precise entity disambiguation.

### What to avoid

**Building entirely from scratch** — the extraction prompting, chunking, and graph construction code in existing tools represents person-years of engineering. **Using a single tool unmodified** — no tool handles provenance with evidence quotes, confidence scoring, and identity resolution together. **Choosing RDF** — unnecessarily complex for application-focused extraction without semantic web interoperability requirements. **Skipping the verification pass** — single-pass LLM extraction has 5–15% hallucination rates that compound across hundreds of entities. **Service-first architecture** — premature optimization that adds infrastructure complexity before the pipeline is proven.

The field is moving fast. GraphRAG, KGGen, Graphiti, and LangExtract all shipped major capabilities in 2024–2025, and the convergence toward two-pass extraction with tiered model cascades suggests these patterns will become standard infrastructure within a year. Building now on these foundations, with clean provenance contracts and incremental processing from the start, positions the tool to absorb improvements as they emerge.
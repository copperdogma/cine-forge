---
type: research-prompt
topic: "shared-entity-extraction"
created: "2026-02-24"
---

# Research Prompt: Shared Entity Extraction with Provenance

## Context

We need a tool or library that extracts **people, biographical attributes, and relationships** from arbitrary text, with **full provenance** (source references, evidence quotes, confidence scores) for every extracted fact.

### The Core Loop

The fundamental pipeline we need:
1. **Chunk text** into meaningful units (chapters, pages, scenes, sections)
2. **Extract entity mentions** from each chunk with evidence (quotes, locations)
3. **Resolve identities** across chunks (same person mentioned differently in different places)
4. **Extract relationships** between entities with evidence
5. **Build a provenance-rich entity graph** where every node attribute and every edge carries source references

### Scale Requirements

- **Minimum**: 10-page screenplay (~30 scenes, ~15 characters)
- **Target**: 100-page document (~50 chapters, ~100 entities)
- **Stretch**: 300-page genealogy book (thousands of person mentions, hundreds of individuals, complex family trees spanning generations)

### What Makes This Different from Standard NER

Standard Named Entity Recognition identifies "John Smith" as a PERSON at character offset 47. We need:
- **John Smith is brave** — evidenced by passages on pages 12, 45, and 89 (with direct quotes)
- **John Smith is the son of Mary Smith** — evidenced by the passage on page 3 (with direct quote)
- **John Smith on page 12 and "the eldest boy" on page 45 are the same person** — resolved with confidence 0.92
- **John Smith's full biography**: occupation, personality traits, key life events — each fact with its own evidence chain

This is closer to **knowledge graph construction from unstructured text** than traditional NER.

### Three Consuming Projects

This tool must serve three different domains:

1. **Film/Screenplay Analysis** (CineForge): Characters from screenplays. Structural signals available (dialogue cues, scene headings). Output: character bibles with prominence, narrative roles, trait evidence, relationship stubs.

2. **Personal Story Chronicle** (Storybook): People from conversation transcripts and potentially long-form books (genealogy, memoirs). Identity resolution is critical ("my mom" = "Sarah" = "your mother"). Temporal scoping on facts ("lived in Chicago 1985-1992"). Incremental extraction across multiple documents.

3. **Interactive Fiction** (Codex Forge): NPCs and enemies from gamebook text. Structured stats (combat attributes). Section-based navigation graph. Code-first with AI escalation.

## What I Need

### 1. Existing Open Source Tools Survey

Search exhaustively for existing tools, libraries, and frameworks that perform LLM-driven entity extraction with provenance. For each candidate, evaluate:

- **Does it extract entities AND relationships?** (not just NER)
- **Does it provide provenance/evidence?** (source locations, quotes, not just labels)
- **Does it handle identity resolution?** (coreference, alias merging)
- **Does it use LLMs?** (not just spaCy/BERT-era models — we need reasoning)
- **Does it scale to 300+ pages?**
- **Is it actively maintained?** (last commit, community size, funding)
- **What's the output format?** (structured JSON/graph, or just annotations?)

Specific tools to investigate (and any others you find):
- **LangChain extraction chains** — structured output from LLMs
- **LlamaIndex knowledge graph** — builds KGs from documents
- **instructor** (jxnl) — structured extraction with Pydantic
- **Unstructured.io** — document preprocessing
- **spaCy + custom NER** — traditional NLP approach
- **OpenIE / ReVerb / OLLIE** — open information extraction
- **Neo4j NaLLM / GraphRAG** — graph construction from text
- **Microsoft GraphRAG** — entity extraction + community summarization
- **Diffbot Natural Language API** — commercial entity extraction
- **Google Document AI** — entity extraction service
- **Amazon Comprehend** — entity/relationship extraction
- **Any recent (2024-2026) open source projects** specifically for LLM-driven knowledge graph construction from text

For the top 3-5 candidates, provide a detailed comparison matrix.

### 2. Academic Research & Proven Approaches

Survey the state of the art in:

**a) Evidence-Grounded Entity Extraction**
- What research exists on extracting entities with source attribution (not just labels)?
- How do modern approaches handle extracting biographical attributes (traits, facts, events) vs. just entity names?
- What's the state of the art for extraction quality on long documents?

**b) Relationship Extraction with Provenance**
- Best approaches for extracting typed relationships (family, professional, adversarial) from narrative text
- How to ground relationships in specific textual evidence
- Handling implicit/inferred relationships vs. explicitly stated ones

**c) Cross-Document Identity Resolution (Entity Linking / Coreference)**
- State of the art for resolving entity mentions across document chunks
- Handling aliases, pronouns, descriptive references ("the tall man", "my mother")
- Scaling identity resolution to hundreds of entities across long documents
- LLM-based approaches vs. traditional clustering/embedding approaches

**d) Chunked Processing for Long Documents**
- Best practices for splitting documents while preserving entity context
- Sliding window vs. hierarchical chunking vs. scene/chapter-aware chunking
- How to maintain entity state across chunks without context window overflow
- Approaches for 300+ page documents that exceed any single context window

**e) Confidence Scoring and Quality Assessment**
- How to assign meaningful confidence to extracted facts
- Multi-pass verification approaches (extract → verify → escalate)
- Human-in-the-loop patterns for extraction quality

### 3. Architecture Best Practices

If we build this ourselves, what should the architecture look like?

**a) Input Contract**
- What's the ideal input format for chunked text? (JSONL? Directory of files? Streaming?)
- How should chunk metadata be structured (IDs, types, source locations)?
- Should the tool handle chunking itself, or require pre-chunked input?

**b) Pipeline Stages**
- What's the optimal stage ordering? (mention extraction → coreference → attribute extraction → relationship extraction? Or a different order?)
- Should stages be independent (each processes full text) or sequential (each builds on prior output)?
- How to handle the "entity roster" problem — do you discover all entities first, then extract details? Or extract details as you discover?

**c) Output Contract**
- What output format maximizes downstream flexibility? (JSON entity graph? RDF triples? Property graph?)
- How should provenance be structured? (inline vs. separate provenance store)
- Should the output include raw mentions/evidence or just resolved entities?

**d) Incremental Processing**
- How to add new documents to an existing entity graph without full reprocessing
- Conflict resolution when new evidence contradicts existing facts
- Versioning and lineage tracking across extraction runs

**e) CLI Tool vs. Library vs. Service**
- Trade-offs for each distribution model
- What interface makes the most sense for multi-project consumption?

### 4. Scalability Deep Dive

The genealogy book use case is the stress test:
- 300+ pages
- Thousands of person mentions
- Hundreds of unique individuals
- Complex multi-generational family trees
- Temporal relationships ("married in 1952", "died before his brother")
- Ambiguous references ("John Jr." vs "John Sr." vs "young John")

What specific techniques exist for handling this scale?
- Token budget management across chunks
- Efficient identity resolution at scale (not O(n²) comparisons)
- Hierarchical extraction (family units → individuals → attributes)
- Handling genealogy-specific patterns (family trees, generational naming)

## Output Format

For each category, provide:
1. **Recommended choice** with reasoning
2. **Runner-up** and when you'd pick it instead
3. **Avoid** — What looks tempting but has known issues
4. **Evidence** — Links, benchmarks, community sentiment, adoption data

For the existing tools survey, provide a comparison matrix with columns:
- Tool name, last updated, GitHub stars/activity
- Entity extraction (Y/N/Partial), Relationship extraction (Y/N/Partial)
- Provenance/evidence support, Identity resolution
- LLM-powered, Scalability (pages), Output format
- Overall fit score (1-5) for our use case

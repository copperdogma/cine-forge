# ADR-001: Shared Entity Extraction Library

**Status:** DECIDED — Build standalone library ("Dossier")

## Context

We maintain three projects that all need to extract people, biographies, and relationships from text with full provenance:

1. **CineForge** — Extracts characters, relationships, and entity graphs from screenplays. Already has a sophisticated battle-tested pipeline (3-pass LLM extraction with QA, adjudication gate, hybrid co-occurrence + AI relationship graph, evidence grounding with quotes and scene refs).

2. **Storybook** — Will extract people, claims (atomic facts), and relationships from conversation transcripts and potentially from long-form text like genealogy books (300+ pages). Needs identity resolution across documents, temporal scoping, and categorical confidence.

3. **Codex Forge** — Extracts combat enemies and navigation relationships from gamebook text. Currently code-first with AI escalation, but could benefit from a shared entity extraction layer for NPC/character identification.

All three share the same fundamental loop:
- **Chunk text** → **Extract entity mentions with evidence** → **Resolve identities across chunks** → **Extract relationships with evidence** → **Build a graph**

The key differentiator from existing NER tools is **provenance**: every extracted fact must point back to specific source locations (chapter/page/line, direct quotes, confidence scores) — not just "this string is a person name."

The question: should we build a shared, standalone tool/library for this, or does something adequate already exist in open source?

## The Ideal (No Technology Constraints)

A standalone CLI tool (like `deep-research`) that:
- Accepts chunked text with chunk metadata (IDs, types, source locations)
- Uses configurable LLM backends to extract entities, attributes, and relationships
- Returns a rich entity graph where every node attribute and every edge carries:
  - Source chunk references
  - Direct quote evidence
  - Confidence scores
  - Extraction provenance (model, prompt version, timestamp)
- Handles identity resolution across chunks (same person mentioned differently)
- Scales from a 10-page screenplay to a 300-page genealogy book
- Is domain-agnostic: consuming projects provide chunking strategy and output mapping
- Supports incremental extraction (process new chunks against existing graph)

## Options

### Option A: Adopt an Existing Open Source Tool
If something exists that handles LLM-driven entity extraction with provenance, relationship discovery, and identity resolution at the quality level we need — just use it.

### Option B: Build a Standalone CLI Tool
Extract and generalize CineForge's world-building pipeline into a new project. Domain-agnostic input (chunked text + config), structured output (entity graph with provenance). Projects call it as a subprocess.

### Option C: Build a Python Library (pip-installable)
Same as B but as an importable library rather than a CLI tool. Tighter integration, more flexible, but more coupling.

### Option D: Share Patterns, Not Code
Each project implements its own extraction using the same architectural blueprint but tuned to its domain. Document the pattern, don't abstract the code.

## Research Needed

- [x] Comprehensive survey of existing open-source tools for LLM-driven entity extraction with provenance
- [x] Academic research on state-of-the-art approaches to evidence-grounded entity and relationship extraction
- [x] Best practices for identity resolution across document chunks at scale
- [x] Architectural patterns for chunked text processing pipelines that scale to 300+ page documents
- [x] Evaluation of existing extraction frameworks (LangChain, LlamaIndex, instructor, etc.) for this use case

All research complete — see `research/final-synthesis.md` for the multi-model synthesis.

## Decision

**Option C: Build a Python Library** — named **Dossier** (`pip install dossier`).

Standalone Python library with CLI wrapper. No existing open-source tool delivers the full pipeline (entity extraction + provenance + identity resolution + relationship extraction + confidence scoring) — all 5 research reports agreed. Instructor + Pydantic is the recommended extraction core.

Key decisions:
- **Standalone library**, not built inside Codex Forge. Codex Forge wraps it in pipeline modules; CineForge imports it directly.
- **Three-layer Level of Detail model**: Mentions (raw spans) → Structured Facts (deduplicated, evidence-backed) → Summaries (bios, identity cards).
- **AI-first**: every pipeline stage must justify itself against "just ask the LLM." Eval first, pipeline second.
- **Forward-only pipeline**: data flows upward only. No write-back from Layer 2 to Layer 1.

Full specification: `spec.md` in this directory.

**Repository:** https://github.com/copperdogma/dossier — bootstrapped from this ADR and spec.

## Legacy Context

CineForge's world-building pipeline is the most mature implementation. Key patterns to preserve or improve upon:
- Scene-aware chunking with per-chunk LLM extraction
- 3-pass extraction with QA verification and model escalation
- LLM adjudication gate before expensive extraction passes
- Hybrid entity graph (deterministic co-occurrence + AI narrative relationships)
- Evidence grounding with direct quotes and scene/line references

Storybook's ADR-006 (SCOPEEL entity model) and ADR-007 (extraction pipeline) contain extensive multi-model research on entity models and extraction architectures — these should be referenced.

## Dependencies

- Storybook ADR-006 (Entity Model) — informs output schema requirements
- Storybook ADR-007 (Knowledge Extraction) — informs pipeline architecture
- CineForge world-building pipeline — primary implementation reference

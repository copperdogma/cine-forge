# Dossier — Specification

**Status:** Draft (reviewed)
**ADR:** 001-shared-dossierion
**Last updated:** 2026-02-24

## 1. Vision

A standalone Python library (with CLI wrapper) that extracts **people, biographical profiles, and relationships** from arbitrary text, with **full provenance** — every extracted fact traces back to specific source passages with direct quotes.

The library is a **pure computation layer**: text in, entity graph out. It has no opinions about how the text was obtained (OCR, PDF parsing, clipboard paste) or how the output is consumed (UI, database, game engine). Consuming projects handle their own intake and output.

### 1.1 Architectural Boundary

```
┌─────────────────────────────────────────────────┐
│  dossier (pip install)                            │
│  Pure Python library. No pipeline dependencies.  │
│  Takes text → returns entity graph.              │
└───────────┬──────────────────┬──────────────────┘
            │                  │
   ┌────────▼────────┐  ┌─────▼──────────────┐
   │  CineForge       │  │  Codex Forge        │
   │  imports library  │  │  wraps library in   │
   │  directly in its  │  │  pipeline modules,  │
   │  world-building   │  │  chains with intake │
   │  pipeline         │  │  (OCR → text →      │
   │                   │  │  entity graph →     │
   │                   │  │  export)            │
   └───────────────────┘  └─────────────────────┘
            │                       │
            └───────┐   ┌───────────┘
                    ▼   ▼
              ┌──────────────┐
              │  Storybook    │
              │  calls CLI or │
              │  wraps in its │
              │  own pipeline │
              └──────────────┘
```

- **CineForge** imports the library directly (Python) in its world-building pipeline
- **Codex Forge** wraps the library in pipeline modules, chaining it with intake (OCR, image extraction, table rescue → clean text → entity extraction → export)
- **Storybook** calls the CLI or imports if it adds a Python backend
- The library does NOT depend on any consuming project. Consuming projects depend on it.

### 1.2 Consuming Projects

| Project | Domain | Input Text | Entity Scale | Key Requirement |
|---|---|---|---|---|
| **CineForge** | Film/screenplays | 90–120 pages, structured (Fountain) | 5–50 characters | Rich character bibles with trait evidence |
| **Storybook** | Personal history | Transcripts, genealogy books, diaries (10–300pp) | 10–500 people | Identity resolution, temporal facts, eras |
| **Codex Forge** | Media processing | Any text extracted by its intake pipeline | Varies | Modular integration, section-level provenance |

### 1.3 Design Principles

- **Provenance is the product.** An extracted fact without a source reference is noise.
- **Level of Detail is configurable.** The same engine handles a 90-page screenplay and a 300-page genealogy book by adjusting extraction depth, not by being a different system.
- **Domain logic stays in consuming projects.** The library extracts people, attributes, relationships, and references. It does not know what a "screenplay" or "gamebook" is.
- **Cost scales with the text, not with the entity count.** Processing is per-chunk. A book with 5 characters and a book with 500 characters cost roughly the same to extract if they're the same page count.
- **AI-first: design for the ideal, backfill for limitations.** Imagine a perfect model that reads the full text and outputs a complete entity graph in one shot. That's the north star. Every pipeline stage (chunking, coreference, tiered models, verification) exists only to compensate for current model limitations. Each stage must justify itself against "just ask the LLM." As models improve, stages should become removable. Keep evals that test beyond current SOTA so we know when to simplify.
- **Eval first, pipeline second.** Build golden references and scoring before building the pipeline. Test the dumbest possible approach (single-shot, full-text, one prompt) first. Measure the gap. Build only enough pipeline to close the gap.
- **Entity type is a parameter, not hardcoded.** V1 extracts people/characters. The architecture (LoD layers, fact categories, mention types, identity resolution) works for any entity type. Future versions add locations, organizations, etc. by changing extraction prompts and schemas, not by changing the pipeline.

---

## 2. Core Concepts

### 2.1 The Three Layers of Entity Knowledge

Every entity accumulates knowledge at three distinct layers. This is the **Level of Detail (LoD)** model:

```
┌─────────────────────────────────────────────┐
│            LAYER 3: SUMMARY                  │
│  "Harry Potter is a wizard, the Boy Who      │
│   Lived, protagonist of the series"          │
│   → Synthesized from Layer 2                 │
│   → References point DOWN to Layer 2 items   │
│   → Stable: changes only when evidence does  │
└──────────────────────┬──────────────────────┘
                       │ derived from
┌──────────────────────▼──────────────────────┐
│          LAYER 2: STRUCTURED FACTS           │
│  Identity:  name="Harry Potter",             │
│             aliases=["The Boy Who Lived"]     │
│  Traits:    brave (era: Hogwarts years,      │
│             refs: ch1p3, ch4p12, ch7p45)     │
│  Events:    "defeats Quirrell" (ref: ch17p2) │
│  Relations: son_of(James), friend(Ron)       │
│   → Each fact has evidence references         │
│   → References point DOWN to Layer 1 spans   │
│   → Grows with text, but deduplicated        │
└──────────────────────┬──────────────────────┘
                       │ extracted from
┌──────────────────────▼──────────────────────┐
│          LAYER 1: MENTIONS                   │
│  "Harry grabbed his wand and stepped         │
│   forward" — chunk_id=ch1_p3, offset=1247    │
│  "the boy who lived" — chunk_id=ch2_p1,      │
│   offset=89                                  │
│   → Raw text spans with source locations     │
│   → Every appearance, reference, discussion  │
│   → This is the ground truth                 │
└─────────────────────────────────────────────┘
```

**Layer 1 (Mentions)** is the complete, unprocessed record — every time a person appears, is referenced, is discussed. This grows linearly with text length. It's stored but not necessarily all surfaced to the consumer.

**Layer 2 (Structured Facts)** is the organized, deduplicated knowledge — traits, events, relationships, each with pointers to the Layer 1 mentions that support them. This grows sublinearly because facts are deduplicated ("Harry is brave" appears once with N evidence references, not N times). Cross-chunk implications that no single chunk could reveal (e.g., a promise in chapter 1 fulfilled in chapter 10) are discovered at this layer during synthesis across all Layer 1 mentions for an entity.

**Layer 3 (Summary)** is the synthesized profile — a natural-language bio plus structured identity card. This is approximately fixed-size per entity regardless of text length. It references Layer 2 facts, not raw text.

**Key architectural property:** Data flows upward only. Layer 1 is complete after the extraction pass. Layer 2 synthesizes from Layer 1 — it may discover cross-chunk implications, but it does NOT write back to Layer 1. Layer 1 is raw ground truth; Layer 2 is interpretation.

### 2.2 Mention Types

Not all mentions of a person carry the same weight or serve the same purpose. The engine classifies each mention:

| Type | Description | Example | Extraction Priority |
|---|---|---|---|
| **self_action** | The person does something | "Harry grabbed his wand" | High — reveals character |
| **self_speech** | The person speaks | "I'm not going to let you do this" | High — reveals voice/intent |
| **described** | Narrator/text describes the person | "He was thin, with a lightning scar" | High — reveals identity |
| **discussed** | Another person talks about them | Hermione to Ron: "Harry would never do that" | Medium — reveals reputation |
| **witnessed** | Person is present but passive | "Harry watched from the doorway" | Low — establishes presence |
| **referenced** | Indirect/contextual reference | "the Chosen One's wand lay on the table" | Low — establishes relevance |

The **extraction depth** setting controls which mention types are collected. Named presets cover the 80% case; the underlying mention type list is directly configurable for power users:

| Depth | Mention Types Collected | Use Case |
|---|---|---|
| `shallow` | self_action, self_speech, described | Quick character identification. Screenplays. |
| `standard` | Above + discussed, witnessed | Character bibles. Most use cases. |
| `exhaustive` | All types including referenced | Genealogy, academic analysis, completionism. |

Depth levels are additive: a `standard` run builds on a prior `shallow` run without re-extracting what's already captured.

### 2.3 Fact Categories

Layer 2 facts are organized into categories. This addresses the "who vs. what" distinction:

**Identity** ("Who are they?")
- Name, aliases, titles
- Physical description
- Occupation/role
- Key relationships (parent, spouse, friend, enemy)
- Core personality traits
- One-line summary

Identity facts are relatively **stable** — they don't grow much with text length. However, identity facts may be **era-scoped** (see 2.4) to handle character evolution. "Harry is timid" (era: pre-Hogwarts) and "Harry is brave" (era: Hogwarts years) are not contradictions — they're a progression.

**Chronicle** ("What have they done?")
- Events participated in, with temporal ordering where available
- Decisions made
- Interactions with other entities
- State changes (moved, married, died, changed allegiance)

Chronicle facts **grow with text length** but can be summarized hierarchically. For a 300-page genealogy book, the chronicle for each person might be 5-50 events. For all 7 HP books, Harry's chronicle might be hundreds of events — but summarizable into a structured timeline.

**Context** ("How are they situated?")
- What others say about them (reputation)
- Where they appear (presence mapping)
- Indirect references and allusions

Context facts grow **fastest** and are the lowest signal-to-noise. Most consumers only want these at `exhaustive` depth.

### 2.4 Eras (Temporal Scoping)

People change over time. A genealogy subject may have been "a farmer in the 1920s" and "a shopkeeper in the 1950s." A fictional character may evolve from timid to brave across a story arc. Without temporal scoping, these would appear as conflicting facts.

**Eras** are optional temporal labels on identity and chronicle facts:

```json
{
  "key": "trait",
  "value": "timid and bullied",
  "era": { "label": "pre-Hogwarts", "evidence_ids": ["ev_002", "ev_008"] },
  "confidence": 0.88
}
```

Era labels are extracted from the text, not imposed by the pipeline. They represent the **character's timeline**, not the narrative timeline. A flashback in chapter 20 showing Harry's childhood produces an era-tagged fact for "early childhood" even though the source chunk is chapter 20.

Era types:
- **Named periods**: "childhood", "college years", "pre-Hogwarts", "married life"
- **Date ranges**: "1920-1940", "before 1980"
- **Relative**: "before marriage", "after the war"
- **Unscoped**: When a fact applies across the entire known timeline (e.g., "born in Surrey")

Eras are first-class extracted facts with their own evidence — the era label itself requires provenance.

### 2.5 Entity Resolution

The same person may be mentioned differently across chunks:
- "Harry", "Harry Potter", "Potter", "the boy", "the Chosen One", "my son"
- "Grandma Rose", "Rose Elizabeth Carter", "Mrs. Carter", "my mother"

The engine resolves these into canonical entities through:

1. **Within-chunk coreference** — Rewrites pronouns and short references to the most specific name in that chunk, before extraction. Research shows 38-45% noise reduction (LINK-KG, CORE-KG benchmarks).
2. **Cross-chunk resolution** — After extraction, mentions are grouped into canonical entities using:
   - Token blocking (shared name tokens → same candidate group)
   - Embedding similarity within blocks
   - LLM judge for ambiguous pairs
   - Graph-assisted merging (two mentions that share a relationship target are likely the same person)

---

## 3. Architecture

### 3.1 Pipeline Overview

```
INPUT                    PIPELINE                              OUTPUT
─────                    ────────                              ──────

Raw text      ┌─────────────────────────────────────┐
  or          │  1. CHUNK (optional)                 │
Pre-chunked   │     Structure-aware splitting        │
JSONL         │     + overlap at boundaries          │     JSON property graph:
              ├─────────────────────────────────────┤       • entities[]
              │  2. RESOLVE REFERENCES (per-chunk)   │       • mentions[]
              │     Coreference resolution            │       • relationships[]
              │     Pronoun → canonical name          │       • evidence[]
              ├─────────────────────────────────────┤       • metadata
              │  3. EXTRACT (per-chunk, parallel)    │
              │     Entity mentions + evidence        │     Configurable depth:
              │     Attributes + evidence             │       shallow / standard
              │     Relationships + evidence          │       / exhaustive
              ├─────────────────────────────────────┤
              │  4. IDENTIFY (global)                │     Configurable summary:
              │     Cross-chunk entity resolution     │       on / off
              │     Alias mapping                    │
              │     Canonical ID assignment           │
              ├─────────────────────────────────────┤
              │  5. VERIFY (selective)               │
              │     Fact validation against source    │
              │     Confidence scoring                │
              │     Contradiction detection           │
              ├─────────────────────────────────────┤
              │  6. SUMMARIZE (optional)             │
              │     Layer 3 synthesis                 │
              │     Bio generation                   │
              └─────────────────────────────────────┘
```

**Every stage is designed to be removable.** If a SOTA model can handle the full text in one pass and produce 98%+ accuracy, stages 1-2 become unnecessary and stages 3-6 collapse into a single call. The eval harness measures which stages actually earn their keep.

### 3.2 Stage Details

#### Stage 1: Chunk

**Input:** Raw text (or pre-chunked JSONL — if pre-chunked, this stage is skipped).

**Built-in chunking strategies:**
- `chapter` — Split on chapter/section headings (configurable regex)
- `scene` — Split on scene headings (Fountain-aware, configurable)
- `sliding` — Fixed-size overlapping windows (SLIDE-style, configurable overlap %)
- `page` — Split on page boundaries (for paginated sources like PDFs)
- `custom` — User-provided chunk boundaries via JSONL

**Output:** JSONL with chunk metadata:
```json
{
  "chunk_id": "ch3_p2",
  "text": "Harry grabbed his wand and stepped forward...",
  "document_id": "philosopher_stone",
  "source": {
    "type": "chapter",
    "chapter": 3,
    "page": 42,
    "line_start": 15,
    "line_end": 47
  }
}
```

**Overlap:** Configurable 0-20%. Overlapping text is tagged so downstream stages can deduplicate mentions that appear in the overlap zone.

**Note on necessity:** Current 1M+ token context windows can hold a 300-page book. Chunking remains valuable for extraction quality (LLMs attend better to focused text) and cost management (tiered models on smaller inputs), but the eval harness will determine whether chunking actually improves results for a given input size and model.

#### Stage 2: Resolve References (Per-Chunk)

**Purpose:** Rewrite within-chunk coreference so the extraction stage sees unambiguous text.

**Method:** spaCy + Coreferee (fast, sufficient for most cases) or Maverick (higher quality, slower). This is a **removable stage** — modern LLMs handle pronouns well. The eval harness will determine if this stage earns its cost.

**Example:**
- Input: `"He grabbed his wand. The boy stepped forward."`
- Output: `"Harry grabbed Harry's wand. Harry stepped forward."`
- Metadata: coreference chains preserved for provenance

**Why before extraction (when used):** LINK-KG benchmark shows 45% node deduplication improvement; CORE-KG shows 38% noise reduction. The LLM extracts facts about "Harry" consistently rather than about "he" and "the boy" separately.

#### Stage 3: Extract (Per-Chunk, Parallel)

**Purpose:** Extract entity mentions, attributes, and relationships from each chunk.

**Method:** Instructor + Pydantic schemas, with configurable model tiering:
- **Tier 1** (cheap/fast: Haiku, GPT-4o-mini): Initial extraction pass
- **Tier 2** (mid: Sonnet, GPT-4o): Verification and complex disambiguation
- **Tier 3** (premium: Opus, o3): Escalation for low-confidence or contradictory results

Specific model assignments are determined by promptfoo evals against golden references, not assumed. The tier system is a cost optimization — if a Tier 1 model scores 95%+ on the eval, no cascade is needed.

**Entity roster injection (optional optimization):** After the first N chunks, the engine can inject a growing entity roster into the extraction prompt to encourage consistent naming. This is purely an optimization for the merge step — extraction works without it. When the roster exceeds a size threshold, only the most relevant entities (by embedding similarity to the current chunk) are injected.

**Per-chunk extraction output:**
```json
{
  "chunk_id": "ch3_p2",
  "mentions": [
    {
      "mention_id": "m_001",
      "surface_form": "Harry",
      "resolved_form": "Harry Potter",
      "mention_type": "self_action",
      "span": { "start": 0, "end": 5 },
      "quote": "Harry grabbed his wand and stepped forward",
      "attributes_observed": [
        {
          "category": "identity",
          "key": "trait",
          "value": "brave",
          "era": null,
          "confidence": 0.85,
          "quote": "grabbed his wand and stepped forward into the darkness alone"
        }
      ],
      "relationships_observed": []
    }
  ]
}
```

#### Stage 4: Identify (Global)

**Purpose:** Resolve mentions across all chunks into canonical entities.

**Method (multi-step to avoid O(n²)):**
1. **Token blocking:** Group mentions by shared name tokens. "Harry Potter", "Harry", "Potter" → same block. "Ron Weasley" → different block.
2. **Embedding similarity:** Within each block, compute pairwise similarity using sentence-transformers embeddings. Pairs above threshold → auto-merge. Pairs in fuzzy zone → LLM judge.
3. **LLM judge:** For ambiguous pairs, a Tier 2 model decides if two mentions are the same person given their attributes and context.
4. **Graph-assisted merge:** If two candidate entities share a relationship target (both are "friend of Ron"), boost merge confidence.

The pipeline naturally handles late discovery: extract everything per-chunk without worrying about consistency, then merge globally. This is forward-only — no back-and-forth passes needed.

**Output:** Canonical entity list with alias mappings:
```json
{
  "entity_id": "e_harry_potter",
  "canonical_name": "Harry Potter",
  "aliases": ["Harry", "Potter", "the boy who lived", "the Chosen One"],
  "mention_ids": ["m_001", "m_007", "m_023", "m_089"]
}
```

#### Stage 5: Verify (Selective)

**Purpose:** Validate extracted facts against source text. Assign confidence scores.

**Method:**
- A separate LLM (Tier 2) receives the extracted fact + the source quote + surrounding context
- Judges: Does the quote actually support this fact? (yes/partial/no)
- Flags contradictions (e.g., two mentions claim different parents for the same person)
- Considers era-scoped facts: "timid" (pre-Hogwarts) and "brave" (Hogwarts) are NOT contradictions
- Only runs on: low-confidence extractions, high-stakes facts (relationships, death events), and a random sample for quality monitoring

**Confidence scoring formula:**
```
confidence = (
  verification_score * 0.4 +        # Did the verifier agree?
  evidence_count_signal * 0.3 +      # How many independent mentions support this?
  cross_chunk_consistency * 0.2 +    # Is this consistent across chunks?
  source_directness * 0.1            # self_action > discussed > referenced
)
```

This is externally derived, not LLM self-reported. LLM self-confidence is unreliable (research consensus). This stage is **removable** — if extraction precision is 98%+ on the eval, verification is waste.

#### Stage 6: Summarize (Optional)

**Purpose:** Generate Layer 3 summaries — natural-language bios and identity cards.

**Method:** A Tier 2 model receives the Layer 2 structured facts for an entity and generates:
- One-line identity summary
- Short bio (2-5 sentences), era-aware (covers character evolution if eras are present)
- Structured identity card (name, aliases, key relationships, key traits)

**This stage is optional** because some consumers (Codex Forge) don't need bios, and some (CineForge) may want to generate their own domain-specific summaries from the structured facts.

### 3.3 Model Tiering

| Tier | Models | Used For | Cost Character |
|---|---|---|---|
| Tier 1 | Haiku 4.5, GPT-4o-mini, Gemini Flash | Per-chunk extraction, mention classification | Cheap, fast |
| Tier 2 | Sonnet 4.6, GPT-4o, Gemini Pro | Verification, identity resolution judge, summarization | Moderate |
| Tier 3 | Opus 4.6, o3, Gemini Ultra | Escalation for low-confidence, contradiction resolution | Expensive, rare |

The cascade: Tier 1 handles ~80% of work. Tier 2 handles verification and hard disambiguation (~15%). Tier 3 is escalation-only (~5%). Estimated cost for 300 pages: $3-10.

**Actual model assignments are determined by promptfoo evals**, not assumed. The eval harness tests all available models at each tier and picks the best quality/cost ratio. This table is a starting hypothesis.

### 3.4 Prompt Caching

The system prompt + Pydantic schema definition is identical across all chunks within a run. This makes Anthropic's prompt caching (and OpenAI's equivalent) directly applicable — cache the static prefix, only pay for the per-chunk text. This could cut Tier 1 extraction costs by 50-80%. The extraction prompt structure should be designed cache-friendly: static system prompt + schema first, variable chunk text last.

---

## 4. Input/Output Contracts

### 4.1 Input

**Option A: Pre-chunked JSONL** (recommended for integrations)
```jsonl
{"chunk_id": "scene_1", "text": "INT. OFFICE - DAY\n\nHarry sits at his desk...", "document_id": "script_v2", "source": {"type": "scene", "number": 1, "page": 1}}
{"chunk_id": "scene_2", "text": "EXT. PARK - NIGHT\n\nRon waits under a streetlight...", "document_id": "script_v2", "source": {"type": "scene", "number": 2, "page": 3}}
```

**Option B: Raw text file** (the engine chunks it)
```bash
dossier run --input book.txt --chunker chapter --depth standard
```

**Configuration (YAML profile):**
```yaml
extraction:
  depth: standard              # shallow | standard | exhaustive
  mention_types:               # override preset (power users)
    - self_action
    - self_speech
    - described
    - discussed

chunking:
  strategy: chapter            # chapter | scene | sliding | page
  overlap_pct: 10              # 0-20
  heading_pattern: "^Chapter\\s+\\d+"

models:
  tier1: anthropic/haiku-4.5
  tier2: anthropic/sonnet-4.6
  tier3: anthropic/opus-4.6

identity_resolution:
  embedding_model: all-MiniLM-L6-v2
  similarity_threshold: 0.82
  use_llm_judge: true
  graph_assisted: true

summarize: true                # Generate Layer 3 bios
verify: true                   # Run verification pass
verify_sample_rate: 0.1        # Verify 10% of standard-confidence facts

temporal:
  extract_eras: true           # Extract era labels for identity facts
```

### 4.2 Output

**JSON property graph with evidence store:**

```json
{
  "metadata": {
    "engine_version": "0.1.0",
    "extraction_depth": "standard",
    "documents": ["script_v2"],
    "chunk_count": 45,
    "entity_count": 12,
    "relationship_count": 23,
    "models_used": {
      "tier1": "haiku-4.5",
      "tier2": "sonnet-4.6"
    },
    "cost_usd": 0.42,
    "duration_seconds": 34
  },

  "entities": [
    {
      "id": "e_harry_potter",
      "canonical_name": "Harry Potter",
      "aliases": ["Harry", "the boy who lived"],
      "summary": {
        "one_line": "A brave young wizard, orphaned as an infant, who discovers his magical heritage at age eleven.",
        "bio": "Harry Potter grew up as a timid, bullied child in the Dursley household, unaware of his magical heritage. Upon entering Hogwarts, he found confidence, loyal friendships, and a destiny he never sought...",
        "identity_card": {
          "occupation": "Student / Wizard",
          "key_traits": ["brave", "loyal", "impulsive"],
          "key_relationships": ["son of James Potter", "friend of Ron Weasley"]
        }
      },
      "facts": {
        "identity": [
          {
            "key": "full_name",
            "value": "Harry James Potter",
            "era": null,
            "confidence": 0.97,
            "evidence_ids": ["ev_001", "ev_034"]
          },
          {
            "key": "trait",
            "value": "timid, bullied by family",
            "era": { "label": "pre-Hogwarts", "evidence_ids": ["ev_002"] },
            "confidence": 0.91,
            "evidence_ids": ["ev_002", "ev_008"]
          },
          {
            "key": "trait",
            "value": "brave, confident",
            "era": { "label": "Hogwarts years", "evidence_ids": ["ev_015"] },
            "confidence": 0.94,
            "evidence_ids": ["ev_015", "ev_089", "ev_134"]
          }
        ],
        "chronicle": [
          {
            "key": "event",
            "value": "Receives Hogwarts acceptance letter",
            "temporal": { "relative_order": 3 },
            "confidence": 0.98,
            "evidence_ids": ["ev_005"]
          }
        ],
        "context": [
          {
            "key": "reputation",
            "value": "Known as 'the boy who lived' by the wizarding world",
            "confidence": 0.99,
            "evidence_ids": ["ev_003", "ev_022"]
          }
        ]
      },
      "mention_count": 847,
      "first_appearance": { "chunk_id": "ch1_p1", "evidence_id": "ev_001" },
      "mention_type_distribution": {
        "self_action": 312,
        "self_speech": 201,
        "described": 89,
        "discussed": 156,
        "witnessed": 67,
        "referenced": 22
      }
    }
  ],

  "relationships": [
    {
      "id": "r_001",
      "source_entity": "e_harry_potter",
      "target_entity": "e_ron_weasley",
      "type": "friend",
      "confidence": 0.96,
      "evidence_ids": ["ev_010", "ev_028", "ev_055"],
      "temporal": { "established_in": "ch6_p1" }
    },
    {
      "id": "r_002",
      "source_entity": "e_harry_potter",
      "target_entity": "e_james_potter",
      "type": "child_of",
      "confidence": 0.99,
      "evidence_ids": ["ev_003", "ev_044"]
    }
  ],

  "evidence": [
    {
      "id": "ev_001",
      "chunk_id": "ch1_p1",
      "document_id": "philosopher_stone",
      "quote": "The boy who lived — Harry Potter — had come to Hogwarts at last.",
      "span": { "start": 1247, "end": 1312 },
      "source": {
        "chapter": 1,
        "page": 1,
        "line": 15
      },
      "mention_type": "described"
    }
  ]
}
```

**Note on mention storage:** At `exhaustive` depth on long works, the `evidence` array could be very large (thousands of entries). The output format supports streaming JSONL as an alternative for large extractions, where entities and evidence are emitted as separate line-delimited records.

---

## 5. Scale Considerations

### 5.1 The Complexity Spectrum

| Input | Pages | ~Entities | ~Mentions | Est. Cost | Est. Time |
|---|---|---|---|---|---|
| Movie screenplay | 90-120 | 5-50 | 200-2,000 | $0.30-1.00 | 30-90s |
| Short memoir/diary | 50-100 | 10-80 | 500-5,000 | $0.50-3.00 | 1-5min |
| Genealogy book | 200-300 | 100-500 | 2,000-20,000 | $3-10 | 5-15min |
| Novel (single) | 250-400 | 20-100 | 5,000-30,000 | $3-8 | 5-15min |
| Novel series (e.g., HP 1-7) | ~3,400 | 200-800 | 50,000-200,000 | $30-80 | 1-3hr |

### 5.2 What Grows and What Doesn't

- **Layer 1 (mentions):** Grows linearly with text. All of HP = ~200K mentions. Stored but not all surfaced.
- **Layer 2 (facts):** Grows sublinearly. Harry's identity facts are ~the same whether extracted from book 1 or all 7. His chronicle grows, but events are deduplicated. All of HP = maybe 3,000-5,000 unique facts across all characters.
- **Layer 3 (summaries):** Fixed per entity. ~200 characters × 1 paragraph each = bounded.
- **Entity resolution cost:** Scales with entity count, not text length. Blocking keeps it O(n log n) not O(n²).
- **Relationships:** Grows modestly. Even HP has maybe 500-800 meaningful relationships.

### 5.3 Depth as the Cost Lever

The `depth` setting is the primary control for managing scale vs. cost:

- `shallow`: Only collect self_action, self_speech, described. Skip verification. Skip summarization. Fast, cheap, good for "who's in this text?"
- `standard`: Add discussed and witnessed. Verify low-confidence facts. Generate summaries. Good for character bibles and genealogy.
- `exhaustive`: Collect everything including indirect references. Full verification. Good for academic analysis or completionist extraction.

Depth levels are **additive**: running `standard` after a prior `shallow` run only extracts the additional mention types, not everything from scratch.

A 300-page genealogy at `standard` depth: $3-10, 5-15 minutes.
All 7 HP books at `exhaustive` depth: $30-80, 1-3 hours. This is a deliberate choice the user makes.

### 5.4 Entity Roster Scaling

When the entity roster exceeds ~100 entities, injecting all of them into every chunk's extraction prompt becomes impractical (token budget). The entity roster is an **optional optimization**, not a requirement. Without it, the pipeline extracts mentions per-chunk with whatever names appear, then Stage 4 (Identify) merges them globally.

When roster injection is enabled, the selection strategy:

1. **Top-N by prominence:** Always inject the top 20 entities (by mention count so far)
2. **Chunk-relevant entities:** Embed the current chunk and inject entities whose prior mentions are semantically similar (top 30 by cosine similarity)
3. **Recency bias:** Entities mentioned in the last 5 chunks get priority
4. **Maximum roster size in prompt:** ~50 entities, configurable

---

## 6. Configuration Profiles

Consuming projects provide YAML profiles that tune extraction for their domain:

### 6.1 Screenplay Profile (CineForge)
```yaml
name: screenplay
chunking:
  strategy: scene
  overlap_pct: 0          # Scenes are self-contained
extraction:
  depth: standard
  mention_types: [self_action, self_speech, described, discussed]
  fact_categories: [identity, chronicle]
temporal:
  extract_eras: false     # Screenplays are typically single-timeline
identity_resolution:
  similarity_threshold: 0.90
  use_llm_judge: false    # Characters have consistent names in screenplays
summarize: true
verify: true
verify_sample_rate: 0.05  # Low — screenplays are explicit
```

### 6.2 Genealogy Profile (Storybook)
```yaml
name: genealogy
chunking:
  strategy: chapter
  overlap_pct: 15         # Cross-chapter family references
extraction:
  depth: standard
  mention_types: [self_action, self_speech, described, discussed, witnessed]
  fact_categories: [identity, chronicle, context]
  relationship_priority: high
temporal:
  extract_eras: true      # Life stages, date ranges, generational periods
identity_resolution:
  similarity_threshold: 0.78  # Lower — more aliases in genealogy
  use_llm_judge: true
  graph_assisted: true        # Critical for "which John Smith?"
  blocking_keys: [surname, generation, geography]
summarize: true
verify: true
verify_sample_rate: 0.15      # Higher — genealogy has more ambiguity
```

### 6.3 Gamebook Profile (Codex Forge)
```yaml
name: gamebook
chunking:
  strategy: custom            # Pre-chunked by section number
extraction:
  depth: shallow
  mention_types: [self_action, described]
  fact_categories: [identity]
  custom_attributes:
    - key: skill
      type: integer
    - key: stamina
      type: integer
temporal:
  extract_eras: false
identity_resolution:
  similarity_threshold: 0.95  # Enemies have explicit names
  use_llm_judge: false
summarize: false
verify: false                 # Code-first extraction handles QA
```

---

## 7. Distribution

### 7.1 Python Library

```python
from dossier import Engine, Profile

engine = Engine(profile=Profile.from_yaml("screenplay.yaml"))

# From pre-chunked data
result = engine.extract(chunks=[
    {"chunk_id": "s1", "text": "INT. OFFICE - DAY\n\nHarry sits...", ...},
    {"chunk_id": "s2", "text": "EXT. PARK - NIGHT\n\nRon waits...", ...},
])

# From raw text
result = engine.extract_file("book.txt")

# Incremental (add deeper extraction to existing results)
existing = engine.load_graph("shallow_run.json")
result = engine.extract(chunks=chunks, existing_graph=existing)

# Access results
for entity in result.entities:
    print(entity.canonical_name, entity.summary.one_line)
    for fact in entity.facts.identity:
        era = f" ({fact.era.label})" if fact.era else ""
        print(f"  {fact.key}: {fact.value}{era} (confidence={fact.confidence})")
```

### 7.2 CLI

```bash
# Basic extraction
dossier run --input chunks.jsonl --profile screenplay.yaml --output graph.json

# From raw text with built-in chunking
dossier run --input book.txt --chunker chapter --depth standard --output graph.json

# Incremental (deeper extraction on existing results)
dossier run --input chunks.jsonl --existing graph.json --output graph_updated.json

# Just identify (skip extraction, resolve existing mentions)
dossier resolve --input mentions.jsonl --output entities.json

# Just summarize (generate Layer 3 from existing Layer 2)
dossier summarize --input graph.json --output graph_with_summaries.json

# Inspect
dossier inspect graph.json                    # Overview stats
dossier inspect graph.json --entity "Harry"   # Single entity detail
dossier inspect graph.json --evidence ev_001  # Single evidence entry
```

---

## 8. Open Questions

### 8.1 Resolved

1. **Should this be built inside Codex Forge?** No. Standalone library. Codex Forge wraps it in pipeline modules. CineForge imports it directly. The library has no pipeline dependencies. (Resolved: architecture discussion, 2026-02-24)

2. **Should extraction be per-sentence?** No. Chunk-level (scene/chapter) gives the LLM enough context to connect implicit relationships within a chunk. Cross-chunk implications are discovered at Layer 2 synthesis. Sentence-level extraction would lose context and produce worse results. (Resolved: design review, 2026-02-24)

3. **Does data need to flow back from Layer 2 to Layer 1?** No. Layer 1 is raw ground truth (mentions). Layer 2 synthesizes from Layer 1 and may discover cross-chunk implications, but these are Layer 2 facts with evidence pointers to Layer 1 mentions. No write-back needed. (Resolved: design review, 2026-02-24)

4. **Should we research LLM citation formats?** No. Our provenance is structural data (chunk IDs, character offsets, direct quotes) consumed by code. Different problem from rendering footnotes in markdown. (Resolved: design review, 2026-02-24)

5. **Back-and-forth passes for late entity discovery?** Not needed. The pipeline is forward-only: per-chunk extraction discovers mentions independently, then Stage 4 (Identify) merges them globally. If chunk 1 finds "Harry" and chunk 50 finds "The Boy Who Lived," they merge at Stage 4. (Resolved: design review, 2026-02-24)

6. **Multi-document scope?** V1 supports multi-volume single narrative (e.g., all HP books as one extraction run with multiple input files). Cross-document entity merging (diary + genealogy book + census record about the same family) is v2. This may become the core of Storybook's people/relationship storage. (Resolved: design review, 2026-02-24)

### 8.2 Active Questions

1. ~~**Project name.**~~ Resolved: **Dossier** / `dossier`. (2026-02-24)

2. **Should Layer 1 mentions be stored in the main output or a separate file?** For a screenplay (200 mentions), inline is fine. For HP-scale (200K mentions), a separate `mentions.jsonl` sidecar makes more sense. Probably: inline up to a threshold, sidecar above it.

3. **Temporal representation details.** Eras are conceptually defined (section 2.4) but the exact representation of fuzzy dates, relative ordering, and temporal validation (parents born before children) needs detailed schema design. How to handle novels with non-linear narratives and unreliable narrators.

4. **Incremental processing conflict resolution.** When new text contradicts existing facts (book 2 reveals something that reframes book 1), what happens? Options: flag for review, keep both with provenance, auto-resolve by recency.

5. **Prompt caching implementation.** Anthropic and OpenAI both support prompt caching. The system prompt + schema should be designed cache-friendly (static prefix, variable chunk text last). Exact implementation depends on provider SDK features at build time.

6. **Testing strategy.** Golden references needed for: screenplay extraction (CineForge has existing fixtures), short story (need to create), genealogy chapter (need to create). Dual scoring: Python scorer for structural quality + LLM rubric for semantic quality. Identity resolution quality measured by precision/recall against hand-labeled entity clusters.

---

## 9. Non-Goals (v1)

- **Non-person entities.** V1 extracts people/characters only. Locations, objects, organizations are future work. The architecture supports them — entity type is a parameter, not hardcoded — but v1 scope is people.
- **Cross-document entity merging.** V1 handles multi-volume single narratives (one extraction run, multiple input files). Merging entities across independently-processed documents (a diary AND a genealogy book) is v2.
- **Media intake.** V1 takes text as input. Converting PDFs, images, or audio to text is the consuming project's responsibility (e.g., Codex Forge's OCR pipeline).
- **Real-time / streaming extraction.** V1 is batch-oriented.
- **Multi-language support.** V1 is English-only.
- **Embedding/vector store integration.** V1 outputs JSON. Consumers handle their own vector indexing.
- **UI.** V1 is library + CLI only. Visualization is the consumer's responsibility.

---

## 10. Implementation Sequence

Following the "eval first, pipeline second" principle:

### Phase 0: Golden References & Eval Harness
1. Create golden references: short screenplay, short story, genealogy chapter (hand-curated, expert-validated)
2. Set up promptfoo eval harness with dual scoring (Python structural + LLM semantic)
3. **Baseline test**: single-shot full-text extraction with SOTA model. No pipeline. Measure the gap against golden references.
4. This baseline determines how much pipeline we actually need.

### Phase 1: Core Extraction
5. Implement the extraction schemas (Pydantic: Mention, Entity, Relationship, Evidence, Era)
6. Implement per-chunk extraction with Instructor
7. Implement Stage 4 (Identify) — entity resolution with token blocking + embedding similarity
8. Output JSON property graph
9. Eval against golden references. Compare to baseline.

### Phase 2: Quality & Scale
10. Add coreference preprocessing (Stage 2) — eval whether it improves results
11. Add verification pass (Stage 5) — eval whether it improves results
12. Add model tiering/cascade — eval whether cheaper models maintain quality
13. Add summarization (Stage 6)
14. Add era extraction
15. Test at genealogy scale (300 pages)

### Phase 3: Polish & Distribution
16. CLI wrapper
17. Prompt caching optimization
18. Incremental extraction support
19. Configuration profiles for each consuming project
20. Package and publish (`pip install dossier`)

---

## Appendix A: Research Summary

See `research/final-synthesis.md` for the full multi-model research synthesis. Key findings that shaped this spec:

- No existing tool delivers the full pipeline (all 5 research reports agree)
- Coreference before extraction improves quality 38-45% (LINK-KG, CORE-KG benchmarks)
- Two-pass extract→verify achieves 98.8% precision (ODKE+ benchmark)
- Overlapping chunk windows improve extraction 24% entities, 39% relationships (SLIDE benchmark)
- Three-tier model cascade reduces cost 60-90% vs. premium-only
- Property graph with separate evidence store is the optimal output format
- Token blocking + embedding ANN makes identity resolution tractable at 500+ entities
- Instructor is the universally recommended extraction building block

## Appendix B: Design Discussion Log

This spec was developed through an iterative design discussion (2026-02-24). Key debates and resolutions:

- **Codex Forge as foundation vs. standalone library:** Investigated Codex Forge architecture in depth. Found that while its recipe/DAG system is sound, its driver hard-codes per-module CLI wiring (550-line `build_command()`), modules lack a standardized Python interface, and the artifact store is run-scoped without cross-run resolution. Decision: standalone library that Codex Forge can wrap in pipeline modules.
- **Sentence-level vs. chunk-level extraction:** Sentence-level loses within-chunk context and doesn't help with cross-chunk implications. Chunk-level is strictly better.
- **AI-first design principle:** Every pipeline stage must justify itself against "just ask the LLM." Build the eval harness first, test the dumbest approach, build only enough complexity to close the gap. Stages are designed to be removable as models improve.
- **Eras for temporal identity:** Identity facts can be era-scoped to handle character evolution and life-stage changes without creating false contradictions.

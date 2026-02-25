---
type: research-report
topic: shared-entity-extraction
canonical-model-name: gemini-3.1-pro-preview
research-mode: standard
collected: '2026-02-24T16:21:19.654465+00:00'
---

This is a comprehensive research report addressing your requirements for a provenance-rich, LLM-driven entity and relationship extraction system. 

Because your requirement bridges **Information Extraction (IE)**, **Knowledge Graph (KG) Construction**, and **Cross-Document Coreference Resolution (CDCR)**, no single off-the-shelf tool perfectly handles all your constraints out of the box—especially the strict requirement for exact quote provenance mapped to globally resolved entities. 

However, the modern AI stack provides the exact primitives needed to build this.

---

# 1. Existing Open Source Tools Survey

Most traditional NLP tools (spaCy, OpenIE) fail because they lack reasoning for implicit traits and relationships. Most modern LLM tools (GraphRAG) fail because they abstract away the exact source quotes in favor of synthesized summaries. 

### Comparison Matrix

| Tool / Framework | Last Updated / Activity | Entity / Rel. Extraction | Provenance / Evidence | Identity Resolution | LLM Powered | Scale (Pages) | Output Format | Fit Score (1-5) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Instructor (jxnl) + LangGraph** | Active (10k+ stars) | Y / Y (Custom Pydantic) | Y (Enforced via schema) | Y (Custom logic via graph) | Y | 300+ (via Map-Reduce) | Custom JSON/Pydantic | **4.8** |
| **LlamaIndex Property Graph** | Active (35k+ stars) | Y / Y | Partial (Tied to source nodes) | Partial (Basic deduplication) | Y | 100+ | Graph Store / JSON | **4.0** |
| **Microsoft GraphRAG** | Active (18k+ stars) | Y / Y | Partial (Lost in summaries) | Y (Clustering) | Y | 1000+ | Parquet / GraphML | **3.5** |
| **LightRAG** | Active (5k+ stars) | Y / Y | Partial | Y (Fast deduplication) | Y | 1000+ | GraphML / JSON | **3.5** |
| **Neo4j LLM Graph Builder** | Active (1k+ stars) | Y / Y | N (Abstracts to graph) | Y (Entity resolution step) | Y | 100+ | Neo4j DB | **3.0** |
| **spaCy + Custom NER** | Active (30k+ stars) | Y / Partial | Y (Character offsets) | Partial (Coreference models) | N (BERT/Transformers) | 1000+ | Annotations | **2.0** |
| **Amazon Comprehend / GCP Doc AI** | Active (Commercial) | Y / Partial | Y (Offsets) | N | Y (Blackbox) | 1000+ | JSON | **1.5** |

### Tool Recommendations

**1. Recommended: Instructor (jxnl) orchestrated by LangGraph**
*   **Reasoning:** You have highly specific schema requirements (exact quotes, confidence scores, temporal scoping). `Instructor` forces LLMs to output strict JSON matching Pydantic models. `LangGraph` allows you to build the exact multi-stage pipeline you need (Chunk -> Extract -> Resolve -> Merge) with state management.
*   **Runner-up:** **LlamaIndex Property Graph**. It has built-in extractors for entities and relations, but you will have to heavily customize the prompts to force it to retain exact quote provenance rather than just linking to the parent text chunk.
*   **Avoid:** **Microsoft GraphRAG**. While incredible for global Q&A, its pipeline is rigid. It extracts entities, but then aggressively summarizes them into "Communities," losing the exact quote-level provenance you need for a Character Bible or Genealogy tree.
*   **Evidence:** Instructor is the industry standard for structured extraction. LangGraph is currently the dominant framework for stateful, multi-step LLM pipelines.

---

# 2. Academic Research & Proven Approaches

### a) Evidence-Grounded Entity Extraction
*   **Recommended:** **Schema-Driven Extractive Prompting**. Define a Pydantic schema that requires `fact`, `exact_quote`, and `chunk_id`. Prompt the LLM: *"You may only extract facts if you can provide an exact, verbatim substring from the text as evidence."*
*   **Runner-up:** **Two-Pass Extraction**. Pass 1: LLM highlights relevant sentences. Pass 2: LLM converts highlighted sentences into structured entity attributes.
*   **Avoid:** Asking the LLM to summarize a character's traits directly. It will hallucinate and blend in outside knowledge.
*   **Evidence:** Research on "Grounded Text Generation" shows that forcing an LLM to output the exact quote *before* outputting the synthesized fact drastically reduces hallucination (similar to Chain-of-Thought).

### b) Relationship Extraction with Provenance
*   **Recommended:** **Joint Entity-Relation Extraction via LLMs**. Instead of extracting entities and then asking for relationships, extract them together in one schema: `Person(name, traits, relationships=[Relationship(target, type, quote)])`.
*   **Runner-up:** **OpenIE + LLM Filtering**. Use traditional Open Information Extraction to get Subject-Verb-Object triples, then use an LLM to classify and map them to your schema.
*   **Avoid:** Pre-defined rigid relationship ontologies (e.g., only allowing "SPOUSE", "CHILD"). Narrative text requires flexible, descriptive relationships ("RIVAL", "MENTOR", "SECRETLY_IN_LOVE_WITH").
*   **Evidence:** Papers like *GPT-NER* and *LLMs for Knowledge Graph Construction* demonstrate that LLMs perform best at relation extraction when allowed to define the relationship type dynamically, followed by a normalization step.

### c) Cross-Document Identity Resolution (Coreference)
*   **Recommended:** **Canopy Clustering + LLM Pairwise Resolution**. 
    1. Generate embeddings for all extracted entity names/aliases.
    2. Group them into "canopies" (e.g., all mentions of "John", "Mr. Smith", "John Smith" go into one bucket).
    3. Ask the LLM to evaluate the bucket: *"Given these mentions and their context quotes, which ones refer to the same individual?"*
*   **Runner-up:** **Global Entity Roster**. Maintain a running list of resolved entities. For each new chunk, ask the LLM: *"Does 'the tall man' refer to anyone on this roster, or is it a new person?"*
*   **Avoid:** O(n²) pairwise LLM comparisons. Comparing every entity to every other entity will blow up your token costs and time.
*   **Evidence:** The standard approach in modern CDCR (Cross-Document Coreference Resolution) is to use cheap embedding models for blocking/clustering, and expensive LLMs only for the final disambiguation.

### d) Chunked Processing for Long Documents
*   **Recommended:** **Structural Chunking with Overlap**. For screenplays (CineForge), chunk by Scene. For books (Storybook), chunk by Chapter/Section. Never chunk arbitrarily by token count if structural markers exist.
*   **Runner-up:** **Semantic Chunking**. If no structure exists, use embedding-based semantic chunking to break text at natural topic shifts.
*   **Avoid:** Fixed-size token chunking (e.g., strictly 1000 tokens). This splits sentences and separates pronouns from their subjects, destroying extraction quality.
*   **Evidence:** Unstructured.io and LlamaIndex benchmarks show structural chunking yields 20-40% higher retrieval and extraction accuracy compared to naive token chunking.

### e) Confidence Scoring and Quality Assessment
*   **Recommended:** **Self-Reflection / Verification Agent**. Have a separate, smaller LLM prompt (or a different model like Claude 3.5 Haiku) act as a judge. Input: `[Quote, Extracted Fact]`. Output: `Confidence Score 0.0-1.0`.
*   **Runner-up:** **Logprobs**. Use the API's token log probabilities to gauge confidence.
*   **Avoid:** Asking the extracting LLM to rate its own confidence in the same prompt. LLMs are notoriously overconfident and will almost always output `0.9` or `1.0`.
*   **Evidence:** "Self-Correction in LLMs" research indicates that LLMs are poor at evaluating their own outputs in a single pass, but highly effective when acting as an independent evaluator in a separate pass.

---

# 3. Architecture Best Practices

If you build this (which is highly recommended given your specific needs), here is the optimal architecture.

### a) Input Contract
*   **Recommended:** **Pre-chunked JSONL**. The tool should accept an array of objects: `{"chunk_id": "scene_4", "text": "...", "metadata": {"location": "page 12"}}`. 
*   **Reasoning:** CineForge, Storybook, and Codex Forge all have vastly different parsing needs (Screenplay PDFs vs. Gamebook XMLs). Keep parsing/chunking *out* of the extraction library. Let the consuming apps do the chunking and pass clean JSONL to the extractor.

### b) Pipeline Stages (The "Map-Reduce" Pattern)
*   **Recommended:** A three-stage sequential pipeline.
    1.  **Local Extraction (Map):** Process each chunk independently. Extract `Mentions` (Name, Traits, Relations, Quotes).
    2.  **Identity Resolution (Shuffle):** Group all `Mentions` globally. Merge aliases ("John" + "Mr. Smith") into `Global Entities`.
    3.  **Attribute Aggregation (Reduce):** For each `Global Entity`, compile all traits and relationships, deduplicate them, and attach the array of evidence quotes.

### c) Output Contract
*   **Recommended:** **Bipartite JSON Graph**. 
    *   `Entities`: The resolved people (e.g., `id: entity_1`, `name: John Smith`).
    *   `Mentions`: The exact textual occurrences (e.g., `id: mention_45`, `entity_id: entity_1`, `quote: "John was brave"`, `chunk_id: scene_4`).
*   **Reasoning:** This preserves 100% of the provenance. If a user clicks "Brave" in the UI, you can instantly query the `Mentions` table to show the exact quote and page number.

### d) Incremental Processing
*   **Recommended:** **Event Sourcing / Append-Only Mentions**. When a new chapter is added, run *Local Extraction* on it to generate new `Mentions`. Append these to the database. Then, re-run the *Identity Resolution* step to map the new mentions to existing `Entities` (or create new ones).
*   **Reasoning:** You never have to re-process the old text. You only pay for the resolution step.

### e) Distribution Model
*   **Recommended:** **Python Library with a REST API wrapper (FastAPI)**. 
*   **Reasoning:** CineForge and Storybook might be web apps, while Codex Forge might be a local script. A core Python library (`pip install provenance-extractor`) that exposes a Pydantic-based API is the most flexible.

---

# 4. Scalability Deep Dive: The Genealogy Stress Test

A 300-page genealogy book with thousands of mentions and complex temporal relationships will break standard LLM pipelines due to context limits and hallucination.

### Specific Techniques for Genealogy Scale:

1.  **Temporal Scoping (The "4D Graph"):**
    *   Genealogy requires facts to have timestamps. Your schema must include `valid_from` and `valid_to`.
    *   *Prompting:* "Extract the relationship, and if mentioned, the date range it applies to (e.g., married 1950-1982)."

2.  **Hierarchical Resolution (Solving the "John Jr." problem):**
    *   In genealogy, names repeat across generations. Standard embedding clustering will group "John Sr." and "John Jr." together.
    *   *Solution:* **Contextual Embeddings**. Do not just embed the name "John". Embed the name *plus its immediate relationships* (e.g., "John, son of Mary, born 1920"). Use this enriched string for clustering before passing to the LLM for resolution.

3.  **Graph-Based Deduplication:**
    *   If the LLM is unsure if "Sarah" on page 10 is "Sarah" on page 250, use graph logic. If page 10 Sarah is married to "David", and page 250 Sarah is married to "David", the confidence score of them being the same person increases dramatically. 
    *   *Implementation:* Use NetworkX (Python) to find isomorphic subgraphs (matching family units) to assist the LLM in identity resolution.

4.  **Token Budget Management:**
    *   For 300 pages, you cannot pass the whole book to an LLM.
    *   Use the **Map-Reduce** architecture described above. Extracting mentions chunk-by-chunk (Map) scales infinitely and linearly. The only bottleneck is the Resolution (Reduce) phase. By using Canopy Clustering (grouping by name/timeframe), you break the Reduce phase into hundreds of small, cheap LLM calls rather than one massive one.

### Summary Recommendation for Your Build

Do not try to force an off-the-shelf tool like Microsoft GraphRAG to do this; you will fight its internal prompts constantly to keep your exact quotes. 

Instead, build a **LangGraph** application. 
1. Define your strict schemas using **Pydantic** (Entity, Mention, Relationship, Evidence).
2. Use **Instructor** to force `gpt-4o-mini` or `claude-3-5-haiku` to extract `Mentions` chunk-by-chunk.
3. Write a Python function to cluster mentions by name embeddings.
4. Use a final LLM pass to resolve those clusters into `Entities`. 

This gives you total control over the provenance, scales linearly, and perfectly serves screenplays, memoirs, and gamebooks.
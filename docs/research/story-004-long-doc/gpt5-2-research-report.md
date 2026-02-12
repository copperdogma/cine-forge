# Long Document AI Editing Research (ChatGPT 5.2 Deep Research Report, Feb 2026)
20260212: Created.

# Long-Document AI Screenplay Normalization for CineForge

## Executive summary

- The main 2026 shift is that “long document” screenplay normalization is no longer primarily blocked by context length for ~100-page scripts; it’s blocked by **format fidelity, edit determinism, and repairability**. Models from OpenAI / Anthropic / Google now support **~400K–1M+ input** and **~64K–128K output**, which makes single-pass regeneration feasible in *token limits* for typical feature scripts. citeturn20search5turn14view1turn10search0  
- For **screenplay cleanup (already screenplay-like input)**, the most reliable “pipeline-grade” pattern today is **edit-list / patch-first**, backed by deterministic patch application + validation. OpenAI’s `apply_patch` tool and Anthropic’s text editor tool are explicit provider-side primitives that formalize this pattern and surface failure modes (“patch failed”, “multiple matches”) that you can catch and recover from. citeturn8view0turn18view0  
- For **prose/notes → screenplay conversion**, a pure patch approach is usually the wrong primitive (you’re not “editing”; you’re “compiling”). The most robust approach is **structure-first conversion**: segment into scene units (or “proto-scenes”), then generate scenes with a shared continuity state and a strict formatting/validation loop; only then do global QA and targeted repairs. (This is still chunking—but chunk boundaries are screenplay-native.) citeturn3search0turn2search28turn16search0  
- **Structured outputs are now table stakes** across the big three: OpenAI Structured Outputs (JSON Schema subset + `strict`), Anthropic structured outputs + strict tool use, and Gemini structured output. This enables robust “QA → actionable fix list” loops, not just “regenerate and hope”. citeturn19view1turn17search2turn0search2  
- **Caching is a major cost/latency lever** for multi-call normalization pipelines: OpenAI prompt caching is automatic (prefix match) and can reduce latency/cost materially; Anthropic uses explicit `cache_control` breakpoints; Gemini supports implicit + explicit context caching with TTL. Design prompts so the style guide + schema sit in the cached prefix. citeturn15view2turn14view4turn15view3  
- Practical recommendation for the next 1–2 iterations: implement a **hybrid engine**: (a) parse/segment, (b) patch-first normalization for screenplay inputs, (c) scene-based generation for prose/notes, (d) validator-driven QA producing structured fix lists, (e) targeted repair passes that apply more patches, not full rewrites. This minimizes drift and makes failures observable and recoverable. citeturn8view0turn18view0turn15view4  
- Plan for next milestones: move from “text in/text out” to an internal **screenplay IR (AST-like)**, so the model produces/repairs structure and text separately; then render Fountain (or your canonical text) deterministically and validate it continuously. Fountain’s ecosystem is strong for portability, but it omits some production-only concepts (e.g., revision marks), so decide whether canonicalization targets *writer-stage* or *production-stage* workflows. citeturn3search4turn3search1  

_Assigned lens: Frameworks & Architectures._  

## Provider API capabilities for long-document editing

### OpenAI

**Context/output practicality.** Current OpenAI API models span two relevant “long-doc axes”:

- **Very large output**: `gpt-5.2` supports **400,000 context** and **128,000 max output tokens**, so generating an entire ~100-page screenplay in one call is feasible from a token-budget perspective. citeturn20search5turn5view3  
- **Very large context**: `gpt-4.1` class models support ~**1,047,576 context** but smaller output caps (~**32,768**), which is often insufficient for full-script regeneration but useful for “read-everything then emit edits / diagnostics”. citeturn4search1turn5view3  

**Structured output constraints.** OpenAI Structured Outputs lets you enforce response conformance to a JSON Schema (`response_format: { type: "json_schema", …, strict: true }`), which is especially useful for:
- returning an edit list / patch plan as machine-checkable JSON, and
- returning a QA violation list with exact anchors and fix operations instead of free-form notes. citeturn19view0turn19view1  

OpenAI also explicitly notes schema-support is a subset of JSON Schema and unsupported features will error in strict mode—this matters when you design patch schemas (keep them simple). citeturn19view3  

**Edit/diff patterns.** OpenAI now ships a first-class **`apply_patch` tool**: the model emits structured patch operations (create/update/delete) containing unified-diff-style hunks; your harness applies them and reports success/failure back to the model for recovery loops. This is directly aligned with your baseline “edit-list/patch style” strategy for long screenplay cleanup, but standardized at the tool layer. citeturn8view0  

**Tool/function calling reliability + retries.** OpenAI’s model comparison indicates streaming + function calling + structured outputs are supported across the modern endpoints (`v1/responses`, etc.). citeturn5view3turn21view0  
OpenAI also positions tool calling reliability and long-context reasoning as key improvements in GPT‑5.2 (note: this is vendor-provided evaluation; treat as directional, not a guarantee). citeturn5view4  

**Streaming behavior.** OpenAI Responses streaming uses **server-sent events (SSE)** (`stream: true`) and defines event types (`response.created`, etc.). For long-output screenplay generation, streaming is mostly a UX and timeout/latency-management tool; for pipelines, it’s also useful for early detection of malformed structured outputs or runaway repetition. citeturn15view0turn15view1  

**Operational knobs that matter for long docs.**
- `truncation: disabled` (default) forces explicit failure if you exceed context; `auto` silently drops earlier conversation items. For normalization pipelines, silent truncation is usually worse than failure, because it creates hard-to-detect drift. citeturn21view0  
- Prompt caching is automatic for prompts ≥1024 tokens and is prefix-sensitive; this strongly favors a design where your screenplay style guide + schema live at the start of the prompt, with per-document text appended. citeturn15view2  

### Anthropic

**Context/output practicality.** Anthropic’s current model line (e.g., Opus 4.6 / Sonnet 4.5) supports:
- **200K standard context**, with a **1M context window** available under a beta header for eligible org tiers, and
- **large output caps** (Opus 4.6: up to **128K** output; Sonnet 4.5: up to **64K** output). citeturn14view1turn14view2turn9search4  

This means one-pass full screenplay regeneration is typically feasible with output caps (especially with Opus), but the more important question remains determinism and drift.

**Structured output + strict tool use.** Anthropic distinguishes:
- JSON outputs for controlling response format, and
- strict tool use for validating tool parameters—both can be combined. citeturn17search2  

This is valuable for “QA produces structured mistakes + structured fix ops” pipelines, where the model must call a “patch tool” with schema-valid parameters.

**Edit/diff patterns.** Anthropic’s **text editor tool** is a built-in tool for viewing and modifying files with commands like `view`, `str_replace`, `insert`, and `create`. It has explicit guidance that is directly relevant to patch-style screenplay cleanup:
- `str_replace` requires exact matching (including whitespace), and
- you must ensure replacements match **exactly one location** to avoid unintended edits (and the tool can error on multiple matches). citeturn18view0  

This is a strong signal of “pipeline-grade” thinking: failures are detectable and recoverable, but only if your patch design avoids ambiguous anchors.

**Streaming behavior.** Anthropic streaming uses **SSE** with clearly defined event sequences (`message_start`, `content_block_delta`, `message_stop`) and explicit overloaded errors (e.g., stream error events). Pipelines should treat overloads as retryable and implement exponential backoff + idempotent job control. citeturn14view3  

**Token economics + thresholds.** Anthropic pricing is model-specific and includes a notable operational cliff: if you enable 1M context and exceed **200K input tokens**, the whole request is charged at premium long-context rates. For screenplay normalization at ~100 pages, you’re usually below 200K input tokens, but batch processing large corpora may cross this. citeturn14view0turn14view2  

**Prompt caching.** Anthropic supports explicit prompt caching using `cache_control` blocks, enabling partial prompt reuse for repetitive prefixes. This is especially effective if you reuse large schemas/instructions/tool definitions across many chunk calls. citeturn14view4  

### Google Gemini (Gemini API + Vertex AI)

**Context/output practicality.** Gemini 3 developer documentation lists **1M input and 64K output** for Gemini 3 Pro Preview and Gemini 3 Flash Preview. citeturn10search0turn10search4  
Vertex AI model docs similarly describe token limits for Gemini 3 Pro Preview (1,048,576 input; 65,536 output) and explicitly list capabilities incl. structured output + function calling + context caching. citeturn10search4  

**Structured output constraints + failure modes surfaced in docs.** Gemini supports structured output, but Google’s troubleshooting documentation calls out specific production failure patterns relevant to long-document structured pipelines:
- repeated text when output field order differs from the defined schema,
- repetition issues in structured output when prompts include certain escape sequences, and
- repetitive tool calling when the model loses state. citeturn15view4  

These are not theoretical—they’re operational hazards you must design around (schema design, prompt hygiene, and “tool loop” state tracking).

**Streaming behavior.** Google’s Gemini ecosystem offers both standard REST and real-time APIs. The Live API uses **WebSockets** for bidirectional streaming, and the public API reference describes receiving messages via WebSocket events. citeturn10search2turn10search25  

For screenplay normalization, WebSockets are usually optional unless you need interactive editing; batch/offline normalization mainly needs robust retry/cancellation semantics.

**Context caching.** Gemini supports:
- implicit caching (automatic; no guaranteed savings),
- explicit caching (manual; TTL-based; savings-guaranteed), and it provides practical tips like keeping shared prefix content at the beginning of the prompt. citeturn15view3  

### Other serious providers (what matters for CineForge)

If you support “bring your own model/provider,” two issues dominate for long-document screenplay normalization: **max output tokens** and **editing primitives**.

- **entity["company","Cohere","ai models provider"]**: Command R / R+ are 128K context but have **~4,000 max output tokens**, meaning they are not suitable for full screenplay generation in one pass (but may be usable as a smaller “QA classifier/extractor” if you only output a compact JSON report). citeturn11search0turn11search8  
- **entity["company","AI21 Labs","jamba models provider"]**: Jamba models emphasize long context (e.g., 256K). They can be interesting for ingest-heavy steps (outline extraction, beat sheet synthesis), but you must verify output limits and structured output reliability per endpoint before using them for full-script emission. citeturn11search7turn11search3  
- **entity["company","xAI","grok models provider"]**: Grok 4.1 Fast is advertised with a **2M context window** and tool calling + structured outputs, but (based on third-party platform docs) response-length caps can be much smaller than the full context window. Treat it as a “read a lot / emit compact artifacts” candidate unless you confirm large output caps in the exact endpoint you will deploy. citeturn11search22turn11search10  
- **entity["company","Mistral AI","ai models provider"]** and other open(-ish) model providers can be cost-effective but often have smaller context/output budgets and less mature structured output/tooling semantics than the big three; they are typically better as “cheap drafting” workers in a multi-stage pipeline than as the final normalizer. citeturn11search1turn11search25  

## Libraries and frameworks for chunked editing and reassembly

This section is biased toward **minimal primitives that fail loudly** over “agent frameworks that hide complexity,” because screenplay normalization is a deterministic pipeline problem disguised as an LLM prompt problem.

### Chunking/splitting frameworks

- **entity["organization","LangChain","llm framework"]**: the RecursiveCharacterTextSplitter is explicitly designed to preserve semantic units by splitting on a hierarchy of separators and supports chunk overlap; overlap is described as a mitigation for information loss at boundaries. citeturn16search0turn16search29  
- **entity["organization","LlamaIndex","llm framework"]**: sentence- and window-based node parsers are designed to keep sentence boundaries intact and optionally preserve surrounding context in metadata (“window”), which maps well to “avoid seam artifacts” patterns if you implement screenplay-aware splitting. citeturn16search1turn16search8  

**Production reliability pattern:** these frameworks help with splitting and orchestration, but they do not guarantee that chunk outputs will stitch cleanly. Their real value in CineForge is (a) standardized splitters and (b) composable pipelines—not correctness by default. citeturn16search0turn16search8  

### Edit/diff application libraries (provider-agnostic)

- **Unified diffs / patching**: If you rely on unified-diff patches, your patch-application must handle imperfect hunks. OpenAI’s `apply_patch` tool standardizes the *generation* of diffs and makes patch success/failure explicit in a loop, but you still own the harness and recovery semantics. citeturn8view0  
- **Diff Match Patch**: Google’s diff-match-patch notes that its patch format assumes serial application, with rolling context that depends on previous patches being applied. This matters if you batch LLM-generated patches: ordering becomes part of correctness. Also note the repo is archived (read-only), which matters for long-term maintenance risk. citeturn16search2turn16search31  
- **JSON Patch / Merge Patch**: These are standardized formats (RFC 6902 and RFC 7386). They’re perfect for editing structured IR (AST/JSON), not raw screenplay text—unless you first map screenplay into a structured representation. citeturn16search28turn16search3  

**Practical guidance:** for v1, use *text-level* patching (unified diff or `str_replace`) because it’s easiest to implement. For v2, move toward **IR-level patching** (JSON Patch) after you represent the screenplay as structured nodes. citeturn16search28turn16search3  

### Screenplay-specific tooling worth integrating

Canonical screenplay text implies you need a parseable spec. The main practical options for your use case are:

- **Fountain**: Fountain is designed to be human-readable plain text “that looks like a screenplay,” with defined rules for scene headings, character names, dialogue, and transitions; it is explicitly positioned as portable and developer-friendly. citeturn3search4turn3search0  
  - Constraint: Fountain explicitly notes it does not include some production features (e.g., revision marks, locked pages). So if your canonicalization target is production-grade Final Draft workflows, you may eventually need a richer canonical format or extension strategy. citeturn3search4  
- **entity["organization","Screenplain","fountain cli and library"]**: supports Fountain-to-outputs like Final Draft FDX / HTML / PDF and can be used as CLI or library—useful for “render + validate” loops and compatibility with studio workflows. citeturn3search1turn3search9  
- **entity["company","Final Draft","screenwriting software vendor"]** interoperability via **FDX (XML)** is widely used; multiple open-source tools exist for reading/writing FDX-like files. Screenplain can output FDX; other libraries (e.g., Go) can parse FDX XML. citeturn3search1turn3search7  
- Multi-language Fountain/FDX tooling: **entity["organization","wildwinter/fountain-tools","screenplay-tools libraries"]** provides format-agnostic screenplay representation with import/export to Fountain and Final Draft FDX across multiple languages. citeturn3search31  
- Alternative interchange: ScreenJSON documentation explicitly discusses FDX as XML; useful if you want a JSON-native interchange layer, but adoption in studio tooling is lower than Fountain/FDX. citeturn3search11  

## Chunking and cross-chunk coherence strategies

Even with 1M-token contexts, long-context usage is not uniformly reliable: the “lost in the middle” phenomenon shows that models can under-attend to information in the middle of long contexts, which is directly relevant when you stuff an entire screenplay + rules + notes into a single prompt and expect perfect adherence everywhere. citeturn2search28turn5view4  

### Proven chunking strategies that reduce drift and seam artifacts

**Scene-native segmentation beats token-native chunking.** For screenplay work, the best chunk boundaries are **structural boundaries**:
- scene headings / sluglines (INT./EXT. etc.),
- dialogue blocks,
- transitions.

Fountain’s explicit syntax makes it easy to segment by these markers deterministically, even when the original input is messy but “screenplay-like.” citeturn3search0turn3search4  

**Overlap is a mitigation, not a solution.** Overlap reduces boundary loss but introduces duplication risk. LangChain’s documentation frames overlap as a mitigation for information loss when context is divided. For screenplay chunks, overlap should be used as “boundary guardrails” (e.g., last 1–2 blocks) and then deterministically de-duplicated during reassembly. citeturn16search0  

**Continuity memory across chunks should be explicit and structured.** A robust pattern in 2026 is: maintain a small, structured “continuity state” object and feed it to each chunk operation. Do not rely on the model to infer continuity from prior chunk text alone. This is aligned with modern structured-output/tooling capabilities across providers (OpenAI Structured Outputs; Anthropic structured outputs; Gemini structured output). citeturn19view1turn17search2turn0search2  

Concrete continuity state fields that matter for screenplay normalization:
- Canonical character names (including aliases).
- Canonical slugline location names.
- Formatting decisions (e.g., whether to enforce `CUT TO:` style transitions).
- A rolling “last scene summary” and “open threads” list.

### Continuity memory patterns that work in pipelines

**Pattern: “global style guide + local window + validator feedback.”**
1. Keep a stable global style guide (cached prefix).
2. For each scene chunk, include:
   - the chunk text,
   - the immediate prior/next scene boundary blocks (small overlap),
   - the continuity state,
   - and a contract: output must parse + pass validators.
3. After generation, run validators; on failure, do a small repair call that sees only failed regions + validator errors.

This directly exploits caching primitives (OpenAI automatic prompt caching; Anthropic `cache_control`; Gemini implicit/explicit caching options). citeturn15view2turn14view4turn15view3  

**Assumption (explicit):** there is limited published benchmark data on “screenplay seam artifact rates” specifically; the recommendation is extrapolated from long-context failure research and production experience patterns described in current API/tooling docs. citeturn2search28turn15view4  

## Edit-list vs full regeneration at scale

### Where full regeneration is reliable vs unreliable

**Reliable scenarios (relative):**
- Small/medium documents where you can tolerate some rewriting.
- Inputs that are primarily prose, where you’re effectively authoring anew.

**Unreliable in pipeline terms:**
- “Cleanup/normalization” where you must preserve line-level meaning but adjust formatting: full regeneration invites drift, paraphrase, and subtle deletions/duplications, especially across long contexts. The “lost in the middle” problem makes this worse as the model’s attention can be non-uniform across long inputs. citeturn2search28  

The fact that OpenAI and Anthropic built explicit patch/edit tools (OpenAI `apply_patch`; Anthropic text editor tool) is a strong ecosystem signal that deterministic editing primitives are more production-friendly than “rewrite the whole file.” citeturn8view0turn18view0  

### Where edit-lists (patches) are reliable vs unreliable

**Reliable scenarios:**
- Mechanical formatting fixes (spacing, indentation, consistent scene headings).
- Deterministic substitutions (character name casing, standardizing `INT./EXT.`).
- Local edits where you can uniquely anchor exactly what should change (key requirement for Anthropic `str_replace`). citeturn18view0  

**Unreliable scenarios (failure modes you must mitigate):**
- Non-unique anchors (“multiple matches”) when text repeats (common in screenplays: `CUT TO:`, repeated character cues). Anthropic explicitly warns to ensure replacements match exactly one location. citeturn18view0  
- Patch/hunk mismatch when the model generates diffs against a slightly different file version; any patch-oriented system needs strong versioning/idempotency. OpenAI’s `apply_patch` loop is explicitly designed to report failures back so the model can recover, but you still need robust harness logic. citeturn8view0  
- Patch ordering complexity: diff-match-patch notes its patch format assumes serial application with rolling context. If you generate multiple patches out of order (e.g., parallel chunk patches), you can create subtle misapplies unless you enforce ordering and/or rebase patches. citeturn16search2  

### Typical error cases and mitigations (implementation-oriented)

**Error case: model emits schema-valid JSON but semantically wrong patch.**  
Mitigation: require the model to include:
- a small “before” excerpt hash (or exact `old_str`) and
- a post-apply verifier step that re-reads the updated region and confirms invariants.
This maps naturally onto both OpenAI and Anthropic edit tools (they both support iterative “apply then report back” loops). citeturn8view0turn18view0  

**Error case: repetition/runaway output under structured schema.**  
Gemini’s troubleshooting guide explicitly documents repetition issues tied to schema field ordering and escape sequences; treat this as a real production hazard.  
Mitigation: schema design rules for structured responses:
- avoid encouraging field order in prompts,
- make all fields required,
- avoid problematic escape patterns in examples,
- and implement automatic “repeat detector” that aborts + retries with adjusted sampling if repetition is detected. citeturn15view4  

**Error case: tool calling loops / repeated tool calls.**  
Gemini’s docs describe repetitive tool calling when the model loses context; OpenAI and Anthropic both expose strong multi-turn features with explicit state passing and tool results.  
Mitigation:
- keep tool loops bounded (max tool calls),
- record tool-call history in a machine-parseable state object,
- and force a “done vs continue” decision in the model output schema. citeturn15view4turn21view0turn14view3  

## Token economics and latency profile for 100-page workflows

### Baseline sizing assumptions (explicit)

- Rule-of-thumb: **1 token ≈ 0.75 words ≈ 4 characters** in English. citeturn13search0  
- Assume a ~100-page screenplay in plain text is on the order of **~25k words** (varies widely). Using the rule-of-thumb, that’s **~33k tokens**.  
- For normalization, output token count is often similar to input (~30k–40k tokens) unless you add/remove lots of content.

These are sizing assumptions; use provider token-counting endpoints in production for accurate metering (OpenAI and Anthropic both document token management/counting support; Gemini also provides token counting guidance). citeturn21view0turn13search8turn10search5  

### Provider price anchors (Feb 2026, cited)

- OpenAI `gpt-5-mini` (Batch API price shown in model docs): **$0.25 / 1M input tokens**, **$2.00 / 1M output tokens**. citeturn20search0  
- Anthropic Sonnet 4.5 standard: **$3 / input MTok**, **$15 / output MTok**. citeturn14view1  
- Gemini 3 Flash Preview: **$0.50 / $3** (input/output per 1M tokens). Gemini 3 Pro Preview: **$2 / $12** for <200k tokens. citeturn10search0  

### Cost comparison by approach (order-of-magnitude, per screenplay)

Assume input = 35k tokens and output = 35k tokens for the “single pass” case. For chunking/patching, assume:
- chunked conversion: 10 chunks, total input ~80k tokens, total output ~50k tokens, plus one QA call (35k in, 2k out)
- patch-first cleanup: patch pass (35k in, 5k out) + QA (35k in, 2k out) + one targeted repair pass (10k in, 1k out)

These are representative; actual pipelines should log per-stage token usage and cost. citeturn13search0turn21view0  

**Estimated cost (USD) using the price anchors above:**

| Approach | OpenAI `gpt-5-mini` (batch pricing) | Anthropic Sonnet 4.5 (standard) | Gemini 3 Flash Preview |
|---|---:|---:|---:|
| Single-pass regeneration (+ optional QA folded into same call) | ~$0.08 | ~$0.64 | ~$0.12 |
| Chunked conversion + QA | ~$0.13 | ~$1.02 | ~$0.20 |
| Patch-first cleanup + QA + 1 repair pass | ~$0.04 | ~$0.32 | ~$0.06 |

How these numbers were derived:
- Multiply input tokens (in millions) × input $/M + output tokens (in millions) × output $/M using the cited pricing. citeturn20search0turn14view1turn10search0turn13search0  

### Latency profile (practical)

- Long outputs are latency-dominant; streaming improves perceived latency and lets you fail fast on format errors. OpenAI and Anthropic explicitly support SSE streaming; Gemini supports WebSocket streaming in Live API contexts. citeturn15view1turn14view3turn10search2  
- Chunked approaches can reduce wall-clock latency via parallelism, but only if your stitching/validation is robust and you manage ordering and overlap deterministically. citeturn16search0turn16search2  
- Patch-first approaches reduce output tokens (and thus generation time) substantially, but may require iterative retries when patches fail to apply (which is still generally cheaper/faster than regenerating a 35k-token script). citeturn8view0turn18view0  

### Caching impact (large in multi-call pipelines)

If you make many calls per script (chunked conversion, iterative repairs), caching can materially reduce cost:
- OpenAI prompt caching is automatic and depends on exact prefix match; it is designed to reduce latency and input token costs for repeated prefixes. citeturn15view2  
- Anthropic prompt caching reuses prefixes via explicit `cache_control` blocks. citeturn14view4  
- Gemini supports implicit caching and explicit caching with TTL. citeturn15view3  

For CineForge, this strongly favors a prompt structure with:
1) style guide + schema + tool definitions first,
2) variable chunk text last. citeturn15view2turn15view3  

## Recommendation for CineForge architecture and rollout plan

### Candidate approaches evaluated

- **Approach A: One-shot full regeneration**
  - Feed entire document + rules; generate canonical screenplay text in one call; then do a QA call if needed.
  - Uses large output token support (64K–128K) now available. citeturn20search5turn14view1turn10search0  

- **Approach B: Scene-native chunked regeneration + continuity state**
  - Parse/segment into scenes; generate scene outputs; reassemble; run global QA; targeted repairs.
  - Uses overlap and continuity memory patterns explicitly. citeturn3search0turn16search0turn2search28  

- **Approach C: Patch-first hybrid (recommended)**
  - If screenplay-like input: generate **patch ops** (edit list) + apply deterministically + validate.
  - If prose/notes input: scene-native chunked generation (Approach B) but still use patch-based repairs and validator-driven QA.
  - Leverages provider-native patch/edit tools where available (`apply_patch`, text editor tool). citeturn8view0turn18view0turn15view4  

### Decision matrix (weighted)

Scoring: 1 (worst) to 5 (best). Weights reflect film-pipeline needs: correctness + repairability dominate.

| Criterion | Weight | A: One-shot regen | B: Scene-chunk regen | C: Patch-first hybrid |
|---|---:|---:|---:|---:|
| Format fidelity + drift resistance | 0.30 | 2 | 4 | 5 |
| Repairability / observable failures | 0.20 | 2 | 4 | 5 |
| Cross-chunk coherence | 0.15 | 3 | 4 | 4 |
| Cost efficiency | 0.15 | 4 | 3 | 5 |
| Wall-clock latency | 0.10 | 3 | 4 | 4 |
| Implementation complexity (lower is better) | 0.10 | 4 | 3 | 3 |
| **Weighted total** | **1.00** | **2.75** | **3.75** | **4.65** |

Why C wins:
- It matches the tooling direction of major providers: OpenAI explicitly supports structured diffs via `apply_patch`; Anthropic explicitly supports file edits via the text editor tool and calls out unique-match/validation requirements. citeturn8view0turn18view0  
- It treats known failure modes as first-class: schema repetition/tool loops (Gemini troubleshooting) and patch mismatch are detectable and recoverable. citeturn15view4turn8view0  
- It minimizes catastrophic drift by shrinking the amount of text the model must regenerate at once (especially for cleanup). citeturn2search28turn16search2  

### Recommended architecture

#### v1 (next 1–2 iterations): deterministic core + LLM as constrained transformer

**Canonical format target:** “Strict Fountain-like screenplay text” as the canonical text output, because it is plain text, parseable, and has mature conversion tooling (e.g., Screenplain to PDF/FDX). citeturn3search4turn3search1  

**Pipeline stages (concrete):**

1. **Ingress + coarse typing**
   - Detect input class: screenplay-like vs prose/notes.
   - If you can parse as Fountain with minor repair: treat as screenplay-like.

2. **Parsing + scene segmentation**
   - If screenplay-like: parse into blocks (scene headings, dialogue blocks, transitions).
   - If prose/notes: segment into “proto-scenes” (LLM-generated scene list) *then* treat each proto-scene as a unit of generation.

3. **Normalization engine**
   - Screenplay-like input: run a **patch proposal** step:
     - Model outputs a structured list of patch operations (provider-native patch tool where available, otherwise your own JSON schema), not the full document.
     - Apply patches deterministically; fail loudly on ambiguity (multiple matches, patch failures). citeturn8view0turn18view0  
   - Prose/notes input: run **scene-generation** per segment with:
     - continuity state object,
     - small overlap at boundaries,
     - strict formatting rules.

4. **Validator-driven QA**
   - Validate:
     - parseability (Fountain parser),
     - structural invariants (every dialogue has a character cue, scene headings in correct form, etc.),
     - forbidden constructs (duplicate scenes, repeated blocks, etc.).
   - QA model call returns a **structured fix list** (JSON schema). Use provider structured-output features to make this reliable. citeturn19view1turn17search2turn0search2  

5. **Targeted repair loop**
   - Convert fix list → patch ops → apply → revalidate.
   - Stop on convergence or escalation threshold.

**Provider mapping for v1 (practical):**
- OpenAI: use Responses API + Structured Outputs + `apply_patch` tool + SSE streaming. citeturn8view0turn19view1turn15view1  
- Anthropic: Messages API + structured outputs/strict tool use + text editor tool; treat “multiple matches” as a first-class retry signal and adjust chunk anchors. citeturn17search2turn18view0  
- Gemini: use structured output but apply Google’s troubleshooting guidance (schema order, escape hygiene, tool-loop safeguards). citeturn15view4turn0search2  

#### v2 (next milestones): internal screenplay IR + IR-aware editing

**Goal:** shift from “LLM edits text directly” to “LLM edits structured screenplay IR, then renderer emits canonical text.”

- Represent the screenplay as a JSON IR:
  - scenes[], each with heading, action blocks, dialogue blocks, transitions.
- Use JSON Patch (RFC 6902) against this IR for edits; then render to Fountain deterministically. citeturn16search28turn3search4  
- This makes:
  - validation stronger (structural invariants aren’t inferred from whitespace),
  - diff/patch operations less ambiguous,
  - and seam artifacts rarer (because blocks are explicit nodes).

**Why not do v2 immediately?** It’s extra engineering, and v1 already significantly improves determinism by using patch tools and validators; v2 is the longer-term correctness move once you’ve observed real production failure modes.

### Risks and mitigations

**Risk: Patch ambiguity (repeated strings) → “multiple matches” or wrong edits.**  
Mitigation:
- Patch at higher-level anchors (scene IDs), not raw repeated text.
- Include unique sentinels per chunk/scene (stable IDs in comments or metadata lines) during intermediate processing, then strip them in final render.
Anthropic explicitly warns to ensure unique matching for replacements. citeturn18view0  

**Risk: Silent truncation / drift in long context.**  
Mitigation:
- Treat context overflow as failure, not silent truncation; OpenAI’s Responses API defaults to `truncation: disabled` and documents the behavior explicitly. citeturn21view0  
- Prefer chunking/patching over monolithic prompts even when context allows, because long-context attention can be non-uniform. citeturn2search28  

**Risk: Structured output repetition / schema weirdness.**  
Mitigation:
- Follow Gemini’s documented guidance: don’t specify field order, make fields required, avoid problematic escapes, and implement repeat detection + retries. citeturn15view4  
- Keep schemas small and avoid unsupported JSON Schema features (OpenAI structured outputs subset). citeturn19view3  

**Risk: Provider tool drift / versioned tool behavior changes.**  
Mitigation:
- Pin model snapshots where possible and run regression evals on a test suite of scripts; Anthropic explicitly notes snapshot stability and that older tool versions aren’t guaranteed compatible with newer models. citeturn14view1turn18view0  

**Risk: Cost blowups in multi-call pipelines.**  
Mitigation:
- Design for caching: keep stable prefix content and reuse it. OpenAI prompt caching is automatic; Anthropic and Gemini provide explicit mechanisms. citeturn15view2turn14view4turn15view3  

### What I would implement this week

- Implement a **canonical screenplay format decision**: normalize to Fountain-like text (writer-stage) and add a renderer pipeline to FDX/PDF using **entity["organization","Screenplain","fountain cli and library"]** for validation/interop. citeturn3search1turn3search9turn3search4  
- Build a **screenplay parser + segmenter**:
  - Fountain parse if possible; otherwise heuristic blocks (sluglines, character cues).
  - Segment by scenes; emit `scene_id` (hash of heading + ordinal) for stable addresses. citeturn3search0turn3search4  
- Implement a **patch schema** (provider-agnostic) and a deterministic **patch harness**:
  - For OpenAI path: integrate `apply_patch` tool loop.
  - For Anthropic path: integrate text editor tool (`str_replace`, `insert`) loop.
  - Treat “patch failed” / “multiple matches” as structured retry triggers with auto-escalation. citeturn8view0turn18view0  
- Implement a **validator suite**:
  - Fountain parse check (hard fail).
  - Custom lint rules (missing character cues, malformed sluglines, etc.).
  - Output a structured error list suitable for LLM repair calls. citeturn3search0turn19view1turn17search2  
- Implement a **QA → repair loop**:
  - QA model returns JSON: list of violations + suggested fix ops.
  - Apply fixes via patch harness; revalidate; cap retries; log everything. citeturn19view1turn8view0turn15view4  
- Add **token + cost telemetry per stage** and enable caching-friendly prompt layouts:
  - OpenAI: prefix-stable prompts to maximize automatic cache hits.
  - Anthropic: explicit cache breakpoints for shared instructions.
  - Gemini: explicit caching for shared style guide when chunking. citeturn15view2turn14view4turn15view3  

### Source list (URLs + one-line relevance each)

- `https://developers.openai.com/api/docs/guides/tools-apply-patch` — OpenAI’s `apply_patch` tool (structured diffs + harness loop), directly relevant to patch-first screenplay cleanup.  
- `https://developers.openai.com/api/docs/guides/structured-outputs/` — OpenAI Structured Outputs JSON Schema constraints (`strict`) for QA/fix-list schemas.  
- `https://platform.openai.com/docs/api-reference/responses` — Responses API parameters (streaming, truncation semantics) that affect long-doc reliability.  
- `https://platform.openai.com/docs/models/gpt-5.2` and `https://platform.openai.com/docs/models/gpt-5-mini` — Current OpenAI context/output token limits and pricing anchors for token economics.  
- `https://platform.openai.com/docs/guides/prompt-caching` — OpenAI automatic prompt caching behavior and prompt-structuring guidance.  
- `https://platform.claude.com/docs/en/about-claude/models/overview` — Anthropic model lineup (context windows, max output) and pricing anchor.  
- `https://platform.claude.com/docs/en/about-claude/pricing` — Anthropic long-context pricing thresholds (200K input token cliff with 1M context enabled).  
- `https://platform.claude.com/docs/en/agents-and-tools/tool-use/text-editor-tool` — Anthropic text editor tool commands + unique-match/validation guidance for patch workflows.  
- `https://platform.claude.com/docs/en/build-with-claude/streaming` — Anthropic SSE streaming structure + overload signaling (retry design).  
- `https://ai.google.dev/gemini-api/docs/gemini-3` — Gemini 3 model table with in/out context and pricing anchors.  
- `https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-pro` — Vertex AI Gemini 3 Pro token limits and supported capabilities (structured output, caching, function calling).  
- `https://ai.google.dev/gemini-api/docs/caching` — Gemini implicit + explicit caching mechanisms and TTL model.  
- `https://ai.google.dev/gemini-api/docs/troubleshooting` — Documented Gemini structured-output/tool-loop failure modes that must be mitigated in production.  
- `https://fountain.io/syntax/` and `https://fountain.io/` — Fountain screenplay markup rules, used as canonical screenplay text target.  
- `https://github.com/vilcans/screenplain` — Screenplain library/CLI for Fountain → FDX/PDF rendering (validation + interop).  
- `https://github.com/wildwinter/fountain-tools` — Multi-language Fountain/FDX tooling for integrating screenplay parsing and conversion across stacks.  
- `https://huggingface.co/papers/2307.03172` — “Lost in the Middle” paper: evidence that long-context attention is non-uniform, motivating chunk/patch strategies even when context windows are huge.
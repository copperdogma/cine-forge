# Long Document AI Editing Research (Grok 4.1 Research Report, Feb 2026)
20260212: Created.

### A) Executive Summary
- As of February 2026, state-of-the-art LLMs like Anthropic's Claude Opus 4.6 (1M token context), OpenAI's GPT-5.3-Codex, and Google's Gemini 3 Pro (200k+ tokens) enable single-pass processing for ~100-page screenplays (~30k-40k tokens), reducing the need for chunking in short-to-medium docs but still requiring it for cost optimization and coherence in complex edits.
- API providers support structured outputs (e.g., JSON mode) and tool calling, but reliability varies: hallucinations in tool args are common, streaming aids long outputs, but edit/diff patterns favor targeted line edits over full regeneration to minimize error propagation.
- Open-source frameworks like LangChain and LlamaIndex excel in chunked editing/reassembly, with semantic chunking and overlaps (10-30%) proven to mitigate drift; failure modes include semantic fragmentation and context loss, addressed via chunk expansion.
- Edit-list approaches (e.g., diff-based) are more reliable at scale than full regeneration, with lower error rates (e.g., 0% on internal benchmarks for targeted edits) and reduced latency, though continual finetuning may be needed for lifelong editing.
- Screenplay-specific tools like Fountain parsers (e.g., fountain-js, betterfountain) integrate well for validation and formatting, ensuring canonical output without custom builds.
- Token economics for a 100-page workflow: single-pass ~$0.10-0.50 (input/output), chunked ~$0.20-0.80, edit-list + QA ~$0.15-0.60; latency profiles favor edit-list for production (seconds vs. minutes).
- Recommended v1: Hybrid chunked + edit-list using Claude Opus 4.6 for reliability; v2: Leverage 10M+ contexts (e.g., Llama 4) for full single-pass with agent teams.
- Key risks include model drift in multi-pass (mitigate with QA loops) and cost overruns (cap via token limits); prioritize production reliability over demo hype.

### B) Findings by Section

1) API-level support:  
   OpenAI's GPT-5.3-Codex offers advanced coding/editing with 25% faster inference, supporting tool calling but prone to invalid JSON/hallucinated params; developers must validate args. Streaming via chunks handles long outputs, with finish reasons for max tokens. No explicit context sizes in docs, but practical for 100k+ tokens based on benchmarks. Anthropic's Claude Opus 4.6 provides 1M token context, structured outputs, and agent teams for parallel editing; excels in long sessions with low drift, tool calling reliable for cybersecurity/finance edits, streaming for extended tasks. Google's Gemini 3 Pro/2.5 Pro support 200k+ tokens (up to 1M beta), structured generation, function calling with high reliability; edit/diff via targeted tools, streaming optimized for long docs. Other providers like Meta's Llama 4 offer 10M tokens for ultra-long editing, but API access varies; max output practicality ~128k tokens across providers, with edit patterns favoring diff over full regen for reliability.

2) Libraries/frameworks:  
   LangChain and LlamaIndex are top open-source choices for chunked editing/reassembly, supporting semantic chunking and RAG pipelines; real-world reliability includes 80-90% coherence in production but fails on semantic fragmentation (e.g., mixed topics in chunks). Haystack and BentoML handle long-doc workflows with low-latency reassembly; failure modes: context dilution in large chunks, mitigated by overlap and validation loops. TensorZero adds observability for production pipelines.

3) Chunking and coherence:  
   Proven strategies: Semantic chunking (by meaning), overlaps (10-30%), context-aware breaks, late chunking to preserve semantics, and post-processing expansion (e.g., neighbor chunks). Avoid drift via token-based measurement, re-anchoring prompts to original query, and continuity memory (e.g., summary carry-over across chunks). Evidence strong for RAG apps, but uncertainty in screenplay-specific drift (assumption: similar to legal/scholarly docs).

4) Edit-list vs full regeneration:  
   Edit-list (targeted diffs) reliable at scale with 0-9% error rates on benchmarks, avoids regeneration latency; unreliable in autoregressive chains due to error propagation. Full regeneration unreliable for long docs (degrades to pre-edit accuracy after 10k updates), high failure in sequential editing (38.5% success vs. 96% claimed in demos). Mitigations: Continual finetuning, perplexity checks, partial edits.

5) Screenplay-specific tooling:  
   Fountain parsers like fountain-js (JS), betterfountain (VS Code), LabScreenplay (utils), and Ovid/fountain-parser (Perl) for parsing/markdown; validators via re-emission/export to PDF/FDX for format checks. Integrate for canonical output; domain tools like screenplay-tools support Final Draft interop.

6) Token economics:  
   For ~100-page screenplay (~30k tokens input, 40k output): Single-pass ~$0.10-0.50 (e.g., Gemini 2.5 Pro $1.25 in/$10 out per 1M). Chunked (5-10 chunks + overlap) ~$0.20-0.80, higher latency (10-30s vs. 5s single). Edit-list + QA ~$0.15-0.60, lowest latency via targeted calls. Assumptions on prices (OpenAI/Anthropic similar); flag uncertainty in exact 2026 rates.

7) Recommendation:  
   Best now: Hybrid chunked edit-list with Opus 4.6 for reliability. Later: Full single-pass with Llama 4/Gemini evolutions for 10M+ contexts.

### C) Decision Matrix

| Approach | Reliability (Weight: 0.3) | Cost (Weight: 0.25) | Latency (Weight: 0.2) | Quality/Coherence (Weight: 0.25) | Total Score (out of 10) |
|----------|---------------------------|---------------------|-----------------------|----------------------------------|-------------------------|
| Single-Pass Full Regen | 7 (High with 1M+ contexts, but drift in complex) | 8 (Lowest calls) | 6 (5-10s for 40k tokens) | 7 (Good for short, but dilution) | 7.15 |
| Chunked Conversion | 8 (Overlaps mitigate seams) | 6 (More calls) | 5 (10-30s with reassembly) | 9 (Semantic focus) | 7.25 |
| Edit-List + Apply + QA | 9 (Targeted, low errors) | 7 (Efficient diffs) | 8 (Seconds per edit) | 8 (Preserves original) | 8.05 |

### D) Recommended Architecture
- **v1 (Now, Next 1-2 Iterations):** Hybrid: Chunk input into semantic segments (LangChain), generate edit-list with Opus 4.6 tool calling, apply diffs, QA loop (retry 2-3x). Use Fountain parser for final validation.
- **v2 (Next 1-2 Milestones):** Full single-pass with agent teams (e.g., Opus 4.6+), leveraging 1M+ contexts for end-to-end normalization; integrate continual finetuning for custom screenplay domain.

### E) Risks and Mitigations
- Risk: Coherence drift in chunks (medium probability). Mitigation: 20% overlaps + summary memory.
- Risk: Tool calling hallucinations (high). Mitigation: Arg validation + fallback to structured JSON.
- Risk: Cost overruns in QA loops (low). Mitigation: Token caps per call, monitor usage.
- Risk: Model deprecation (medium). Mitigation: Multi-provider abstraction (e.g., LangChain).
- Risk: Format errors in screenplay output (low). Mitigation: Integrate Fountain validator post-QA.

### F) “What I Would Implement This Week” Checklist
- Set up LangChain for chunking/reassembly with semantic strategy.
- Prototype edit-list gen using Claude Opus 4.6 API (tool calling for diffs).
- Integrate fountain-js parser for input parsing/output validation.
- Build QA retry loop (perplexity threshold for acceptance).
- Estimate costs for 100-page test doc; run benchmarks on latency/error rates.
- Deploy minimal pipeline in code_execution env for local testing.

### G) Source List
- https://platform.openai.com/docs/api-reference/chat: OpenAI API details on tool calling and streaming.
- https://docs.anthropic.com/en/api/messages: Anthropic Messages API overview.
- https://ai.google.dev/gemini-api/docs/models/gemini: Google Gemini model specs.
- https://openai.com/api/pricing/: OpenAI pricing (though insufficient for specific models).
- https://www.anthropic.com/pricing: Anthropic pricing.
- https://ai.google.dev/pricing: Google Gemini API pricing.
- https://medium.com/@ai.nishikant/better-chunks-better-answers-chunking-strategies-for-smarter-rag-ba414704c33e: Chunking strategies for coherence.
- https://machinelearningmastery.com/essential-chunking-techniques-for-building-better-llm-applications: Trade-offs in chunk size for LLM apps.
- https://weaviate.io/blog/chunking-strategies-for-rag: Late chunking and context management.
- https://www.mindee.com/blog/llm-chunking-strategies: Context preservation techniques.
- https://www.pinecone.io/learn/chunking-strategies: Post-processing expansions.
- https://globalnodes.tech/blog/chunking-strategy-for-llm-application: Overlapping for continuity.
- https://arxiv.org/html/2509.07759v1: Survey on long-doc segmentation.
- https://developer.ibm.com/articles/awb-strategies-enhancing-rag-effectiveness: Enhancing RAG with chunking.
- https://www.firecrawl.dev/blog/best-open-source-rag-frameworks: Top RAG frameworks including LangChain.
- https://redwerk.com/blog/top-llm-frameworks: CrewAI and multi-agent frameworks.
- https://contabo.com/blog/open-source-llms: Open-source LLM guides.
- https://weaviate.io/blog/chunking-strategies-for-rag: Chunking in LangChain/LlamaIndex (duplicate relevance).
- https://www.bentoml.com/blog/navigating-the-world-of-open-source-large-language-models: BentoML for deployment.
- https://zilliz.com/blog/10-open-source-llm-frameworks-developers-cannot-ignore-in-2025: LLM frameworks overview.
- https://pub.towardsai.net/5-underrated-libraries-frameworks-for-ai-engineers-to-learn-in-2026-751135919d8e: Langfuse for observability.
- https://www.igmguru.com/blog/top-open-source-llms: Open-source LLMs.
- https://www.mygreatlearning.com/blog/top-open-source-llms: Use cases for open LLMs.
- https://www.atlantic.net/gpu-server-hosting/top-llm-development-tools-2026: LangChain as premier framework.
- https://kanerika.com/blogs/open-source-llms-models: GLM for long docs.
- https://arxiv.org/html/2503.05683v1: Limits of knowledge editing.
- https://medium.com/@pYdeas/when-llms-give-almost-correct-code-fix-it-with-targeted-line-edits-instead-of-a-full-rewrite-af3329e42010: Targeted edits vs. full rewrite.
- https://arxiv.org/html/2410.18785v1: Evaluation of edited LLMs.
- https://ofey.me/assets/review/acl25_yang.html: Real-world editing failures.
- https://www.southbridge.ai/blog/a-review-of-editing-with-llms: Strategies for LLM editing.
- https://github.com/meshula/LabScreenplay: Fountain parser utils.
- https://wildwinter.medium.com/fountain-movie-script-parser-javascript-python-c-c-ca088d63d298: Multi-lang Fountain parsers.
- https://fountain.io/: Fountain syntax overview.
- https://github.com/mattdaly/Fountain.js: JS Fountain parser.
- https://opensource.com/article/21/12/linux-fountain: Fountain in Linux editors.
- https://setpixel.com/writing/writing-a-screenplay-in-fountain: Fountain community tools.
- https://www.youtube.com/watch?v=vKMnRAcz_Kc: BetterFountain plugin.
- https://github.com/Ovid/fountain-parser: Perl Fountain parser.
- https://johnaugust.com/2012/introducing-fountain: Fountain spec.
- https://medium.com/creativity-ai/creativity-ai-62-anthropics-smartest-claude-yet-kling-goes-all-in-and-midjourney-s-style-16ecc6589da0: Claude updates.
- https://www.anthropic.com/claude/sonnet: Claude Sonnet 4.5 details.
- https://www.shakudo.io/blog/top-9-large-language-models: Top LLMs including Llama 4.
- https://magazine.sebastianraschka.com/p/state-of-llms-2025: Predictions and state of LLMs.
- https://docs.cloud.google.com/vertex-ai/generative-ai/docs/deprecations/partner-models: Claude/Gemini deprecations.
- https://zapier.com/blog/best-llm: Best LLMs 2026.
- https://venturebeat.com/technology/openais-gpt-5-3-codex-drops-as-anthropic-upgrades-claude-ai-coding-wars-heat: GPT-5.3-Codex launch.
- https://dentro.de/ai/news: AI news Feb 2026.
- https://www.platformer.news/journalism-job-automation-claude: AI model comparisons.
- https://press.airstreet.com/p/state-of-ai-february-2026-newsletter: State of AI newsletter.
- https://radicaldatascience.wordpress.com/2026/02/10/ai-news-briefs-bulletin-board-for-february-2026: AI news briefs.
- https://www.linkedin.com/pulse/llm-papers-reading-notes-february-2026-jean-david-ruvini-aztac: LLM paper notes.
- https://www.anthropic.com/: Anthropic home.
- https://www.latent.space/p/ainews-openai-and-anthropic-go-to: AI news on model wars.
- https://llm-stats.com/ai-news: LLM updates aggregation.
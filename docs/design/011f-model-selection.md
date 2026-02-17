# 011f Chat AI — Model Selection Analysis

**Date**: 2026-02-16
**Story**: 011f (Conversational AI Chat)
**Status**: Approved

---

## Requirements

The chat AI is the conversational layer on top of a deterministic state machine. It must:

1. **Large context** — system prompt + project state + artifact contents + chat history + page context. Budget: 100-200K tokens for a mature project.
2. **Good tool use** — call discrete tools mid-conversation (read artifacts, query state, start runs). These are simple, scoped tool calls — not complex multi-step agentic chains.
3. **Streaming** — token-by-token SSE for responsive UX. Tool call indicators interleaved.
4. **Good personality** — creative collaborator for filmmakers. Enthusiastic about the story, knowledgeable about film, not robotic.
5. **Cost-efficient** — called on every user message. Must be affordable for frequent interactive use.

### What the AI Does NOT Need

- **Deep agentic reasoning**: The state machine handles project progression. The AI reads state, it doesn't compute it.
- **Long-running orchestration**: No multi-hour chains of tool calls. Turns are conversational — quick reads, short responses.
- **Opus-class judgment**: The tools are well-defined and scoped. The AI picks which tool to call and synthesizes results into a conversational response. Sonnet-tier models handle this reliably.

---

## Context Window Landscape (Feb 2026)

Context is no longer a differentiator — everything is 1M.

| Model | Context | Input $/M | Output $/M | **$/turn*** | Integrated? |
|-------|---------|-----------|------------|-------------|-------------|
| Claude Opus 4.6 | 200K (1M beta) | $5.00 | $25.00 | **$0.275** | Yes |
| **Claude Sonnet 4.5** | 200K (1M beta) | $3.00 | $15.00 | **$0.165** | Yes |
| Claude Haiku 4.5 | 200K | $1.00 | $5.00 | **$0.055** | Yes |
| GPT-4.1 | 1M | — | — | — | Yes |
| GPT-4.1 Mini | 1M | $2.00 | $8.00 | **$0.108** | Yes |
| Gemini 2.5 Pro | 1M | $1.25 | $10.00 | **$0.073** | No (038) |
| **Gemini 2.5 Flash** | 1M | $0.15 | $0.60 | **$0.008** | No (038) |

*50K input + 1K output, standard pricing, no caching.

---

## Recommendation

### Primary: Claude Sonnet 4.5

- **$0.165/turn** standard, **~$0.03/turn** with prompt caching
- 200K context standard (1M beta) — more than sufficient
- Excellent tool use — reliable for discrete, scoped tool calls
- Good creative personality — warm, professional, knowledgeable about narrative
- Already integrated in `src/cine_forge/ai/llm.py` — zero blockers
- Fast TTFT (~150ms), great streaming support
- Monthly cost: ~$60 with caching (2K turns/mo)

### Why not Opus 4.6?

Opus is the best model, but it's overkill for this use case. The chat AI doesn't do deep agentic reasoning — the state machine handles project progression, and tool calls are simple and scoped. Opus costs 7x more than Sonnet with caching, and the extra reasoning depth doesn't materially improve conversational Q&A, creative discussion, or artifact lookups. Save Opus for pipeline modules where judgment matters.

### Why not Haiku 4.5?

Cheaper ($0.055/turn) but personality is too thin for a creative collaborator. Haiku is concise and direct — good for background tasks, not for engaging filmmakers in creative discussion about their characters.

### Future cost optimization: Gemini 2.5 Flash

At $0.008/turn, Gemini Flash is 20x cheaper than Sonnet — essentially free. It has 1M native context (no beta needed), good tool use, and adequate personality. Blocked on Story 038 (multi-provider transport). Once 038 lands, evaluate Flash as the default with Sonnet as the quality escalation tier.

### Alternative: GPT-4.1 Mini

$0.108/turn, 1M native context, already integrated. Viable fallback if Anthropic has availability issues. Personality needs testing — may be too generic for the creative collaborator role.

---

## Cost Projection

| Strategy | $/Turn | Monthly (2K turns) |
|----------|--------|-------------------|
| Sonnet 4.5 (standard) | $0.165 | $330 |
| Sonnet 4.5 (cached) | ~$0.03 | ~$60 |
| Gemini Flash (future) | $0.008 | $16 |
| Tiered Flash + Sonnet (future) | ~$0.02 | ~$40 |

Prompt caching strategy: cache the system prompt + project snapshot (static per conversation). These are the bulk of input tokens (~40K of the 50K). With 90% cache hit rate, input cost drops from $0.15 to $0.015.

---

## Implementation Notes

- **Pricing update needed**: `llm.py` MODEL_PRICING_PER_M_TOKEN shows outdated Opus 4.6 pricing ($15/$75 → $5/$25).
- **Streaming**: `llm.py` currently does batch calls only. Need to add `client.messages.stream()` for the chat endpoint.
- **Prompt caching**: Anthropic supports cache control headers. Cache system prompt + project snapshot.
- **max_tokens**: Set 4096 for chat responses (sufficient for conversational turns).
- **Model config**: Chat model should be configurable per-project (default: `claude-sonnet-4-5-20250929`). Allows upgrading to Opus for specific projects or downgrading to Flash once available.

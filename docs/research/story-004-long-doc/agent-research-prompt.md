# Story 004 External Agent Prompt

Use this as the base prompt for each external model/agent. Change only the `Assigned Lens` line so each report is complementary.

```text
You are conducting deep technical research for CineForge (an AI-first film pipeline).
Your job is to produce an evidence-backed recommendation for long-document AI screenplay normalization.

Assigned Lens: [replace with one of: "API/Model Capabilities", "Frameworks & Architectures", "Screenplay/Editorial Workflow + Cost Ops"]

Context:
- We are implementing Story 004: Script Normalization.
- Input can be screenplay/prose/notes, output must be canonical screenplay text.
- We already have a baseline strategy:
  - short docs: single pass
  - long screenplay cleanup: edit-list/patch style
  - long prose/notes conversion: chunked conversion + overlap
  - second-pass QA model call with retry loop
- We need a stronger decision based on current (Feb 2026) state of the art.

Research Questions (must answer all):
1) API-level support:
   - What do OpenAI, Anthropic, Google, and other serious providers currently offer for long document editing?
   - Structured output constraints, max context/output practicality, tool/function calling reliability, edit/diff patterns, streaming behavior.
2) Libraries/frameworks:
   - Best open-source choices for chunked editing/reassembly.
   - Real-world reliability patterns and failure modes.
3) Chunking and coherence:
   - Proven strategies to avoid drift and seam artifacts.
   - Continuity memory patterns across chunks.
4) Edit-list vs full regeneration:
   - Where each is reliable/unreliable at scale.
   - Typical error rates/failure cases and mitigations.
5) Screenplay-specific tooling:
   - Fountain parsers, screenplay format validators, domain-specific tools worth integrating.
6) Token economics:
   - Practical cost/latency profile for ~100-page screenplay workflows.
   - Compare likely cost for: single-pass, chunked conversion, edit-list + apply + QA.
7) Recommendation:
   - Best architecture for CineForge in next 1-2 iterations (now) and next 1-2 milestones (later).

Output Requirements:
- Keep it concrete and implementation-oriented.
- Include:
  A) Executive summary (5-8 bullets)
  B) Findings by section (1-7 above)
  C) Decision matrix table with weighted scores across at least 3 candidate approaches
  D) Recommended architecture (v1 now, v2 later)
  E) Risks and mitigations
  F) “What I would implement this week” checklist
  G) Source list (URLs + one-line relevance each)

Evaluation Constraints:
- Prefer practical production guidance over hype.
- Distinguish “works in demos” vs “works reliably in pipelines”.
- Flag uncertainty explicitly where evidence is weak.
- If claims are speculative, label them as assumptions.

Tone:
- Senior engineer + applied researcher.
- Critical, specific, and cost-aware.
```

# Scout 007 — Storybook & Dossier delta

**Sources:** `/Users/cam/Documents/Projects/Storybook/storybook`, `/Users/cam/Documents/Projects/dossier`
**Scouted:** 2026-03-02
**Scope:** Changes since Scout 006 (2026-03-01)
**Previous:** Scout 006 (2026-03-01)
**Status:** Partial (items 1–3 done; 4–6 pending)

## Findings

### From Storybook

1. **`golden-verify` — Tooling check before subagent launch** — LOW value
   What: Before launching subagents, identify the project's execution pattern (e.g., `npx tsx`, `.venv/bin/python`) and pass it in the instructions. Prevents subagents failing silently because they used the wrong interpreter.
   Us: Our `golden-verify` step 3 launches subagents but doesn't include a tooling check. The instruction hardcodes `.venv/bin/python benchmarks/golden/validate-golden.py` (correct for us), but the principle of explicitly passing the interpreter to subagents is sound.
   Recommendation: Adopt inline — add a one-sentence tooling check before step 3.

2. **`golden-create` — Explicit inbox cleanup step** — LOW value
   What: Explicit step 6: "Move the inbox item to the new fixture directory after processing is complete. Prevents other agents from re-processing it. If the fixture directory already has a matching source file, delete the inbox copy instead."
   Us: Our `golden-create` step 5 says "Validate and track" but has no explicit inbox move. The move is implied but not stated.
   Recommendation: Adopt inline — insert explicit inbox-move step between validate and report.

3. **`setup-golden` — Coverage matrix JSON template inline** — LOW value
   What: Full JSON template for `_coverage-matrix.json` embedded in the skill with standard `verification_status` values: `"pending"`, `"needs-review"`, `"verified"`. Agents don't need to look it up elsewhere.
   Us: Our `setup-golden` at line 78 says "**Tracking files** — Empty checklist table and coverage matrix." — no template.
   Recommendation: Adopt inline — add template block to the generate-everything section.

4. **`create-story` — Accessibility audit checklist** — MEDIUM value
   What: Added an accessibility checklist for any story touching UI:
   - Touch targets ≥ 44×44px
   - Color contrast ≥ 4.5:1 (WCAG AA)
   - Keyboard navigation (tab order, focus rings)
   - Semantic HTML + ARIA labels
   - Screen reader tested (axe/Lighthouse)
   - No information conveyed by color alone
   Both the SKILL.md convention and the story template were updated.
   Us: CineForge story template has tenet verification but no accessibility checklist. Our Ideal doesn't have an elderly-user focus (Storybook's rationale), but accessibility is still good practice for a professional filmmaking tool.
   Recommendation: Adopt inline — add accessibility checklist to our story template and create-story SKILL.md.

5. **Context window management pattern** — MEDIUM value (reference for Story 011f)
   What: Storybook Story 006 implemented context summarization: when conversation history exceeds 150k chars (~37k tokens), summarize the oldest 50% via a single `generateText()` call and replace them with a single assistant message `[Earlier conversation summary: ...]`. User doesn't see the summary; AI continuity is preserved. Char threshold (not token count — avoids tokenizer dependency). Uses Haiku for the summary call (cheap, fast).
   Us: Story 011f (Conversational AI Chat) is Draft — not yet in progress. This is the exact problem it will need to solve.
   Recommendation: Note as reference for Story 011f, not inline adoption. No code to add now.

### From Dossier

6. **Per-provider LLM circuit breaker** — MEDIUM value
   What: Thread-safe `CLOSED → OPEN → HALF_OPEN` circuit breaker in `src/dossier/circuit_breaker.py`. Detects consecutive transient failures (rate limit, 429, 500, 503, timeout) and stops sending requests to that provider until cooldown expires. Then allows one probe request. Resets on success. Module-level registry (`get_breaker(provider)`) so caller doesn't manage lifetime. 244 lines, zero external dependencies beyond stdlib.
   Us: `src/cine_forge/ai/llm.py` has retry logic (increment `max_tokens`, escalate to stronger model on malformed JSON) but no circuit breaker for API-level transient failures. If Anthropic or OpenAI has a transient outage, we hammer the API until timeout.
   Recommendation: Adopt as story — not a trivial inline change. Needs integration into `llm.py` call sites, tests, and decision on which errors should trip it.

7. **Dossier production golden T1 verification** — context only
   What: Dossier completed adversarial verification of their full T1 fixture set (15 fixtures, VERIFICATION_REPORT.md per fixture). Key pattern: each verification report documents what was fixed, validator result, and final verdict. Automated via `/golden-verify`.
   Us: We have 13 golden files in `benchmarks/golden/` and some in `tests/fixtures/golden/` — none have VERIFICATION_REPORT.md files or a _verification-checklist.md. The `/setup-golden`, `/golden-create`, `/golden-verify` skills are ready; we just haven't run them.
   Recommendation: Skip for now. Already tracked as Story 109 (golden-build runbook). When we run `/setup-golden`, the reports will be generated.

## Approved

- [x] 1. `golden-verify` tooling check — added tooling check note before subagent launch instructions
- [x] 2. `golden-create` inbox cleanup step — added step 6 (inbox move), old step 6 renumbered to 7
- [x] 3. `setup-golden` coverage matrix template — added JSON template + verification_status values inline
- [ ] 4. Accessibility checklist — `.agents/skills/create-story/SKILL.md` + templates/story.md
- [ ] 5. Context window mgmt — reference for Story 011f (no code change)
- [ ] 6. LLM circuit breaker — create story
- [ ] 7. Dossier golden reports — skip

All skills synced (34 total).

## Skipped / Rejected

- 7. Dossier golden T1 verification reports — tracked in Story 109, will be generated when `/setup-golden` runs

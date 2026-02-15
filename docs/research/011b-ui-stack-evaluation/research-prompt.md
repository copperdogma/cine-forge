---
type: research-prompt
topic: "011b-ui-stack-evaluation"
created: "2026-02-15T01:12:51.559710+00:00"
---

# Research Prompt

You are conducting technical research for CineForge, an AI-first film production pipeline tool. We are building a production-quality Operator Console UI and need to select the optimal technology stack.

**Critical constraint: AI agents (Claude Code, Cursor, Codex) write 100% of the UI code.** The stack must be optimized for AI-generated code quality — not developer ergonomics, not community size, not hiring market. The question is: "Which stack produces the most polished, correct, accessible UI when an AI writes all the code?"

## Current Stack (stopgap, may be replaced)
- React 18 + TypeScript
- Vite (build tooling)
- Tailwind CSS (utility classes)
- No component library — all components hand-written
- Single-file App.tsx (~1800 lines)

This produces functional but visually "developer dashboard" output. We need "creative tool" quality.

## Research Areas (answer ALL)

### 1. Component Library Selection (Primary Decision)

Evaluate these component libraries specifically for AI code generation quality (Feb 2026 state of the art):

- **shadcn/ui**: Copy-paste components, Radix primitives, Tailwind styling. Very popular in AI-generated code. Evaluate ceiling — can it look like more than a "shadcn site"?
- **Radix UI (direct)**: Unstyled primitives. Maximum flexibility but more work per component. How well do AI agents style Radix from scratch?
- **Mantine**: Full-featured, opinionated, good defaults. Large API surface — does AI handle it well or get confused?
- **Park UI**: Ark UI primitives + design tokens. Newer, less training data. How does AI quality compare?
- **Chakra UI v3**: Major rewrite on Ark UI. Post-2025 — is there enough AI training data?
- **Ant Design**: Enterprise-grade, very complete. Highly opinionated — does that help or hurt AI code gen?
- **Material UI (MUI)**: Largest ecosystem. Heavy abstractions. AI-generated MUI code quality?
- **Others** worth considering in Feb 2026 that may not be on this list.

For each, evaluate:
1. **AI code quality**: When Claude/GPT/Codex generates code using this library, how correct/polished is the output?
2. **Visual ceiling**: Can it produce genuinely beautiful UIs, or does it plateau at "clean but generic"?
3. **Composability**: Can AI mix, customize, and extend components without fighting the library?
4. **Accessibility defaults**: WCAG 2.1 AA out of the box?
5. **Bundle size / performance**: Matters for artifact-heavy UIs with many data views.
6. **Dark mode / theming**: CineForge will likely use a dark theme. How easy is theme customization?

### 2. AI-Assisted UI Development Workflow

- What is the state of the art for AI-generated UI in Feb 2026?
- Evaluate these tools specifically: **v0** (Vercel), **Bolt** (StackBlitz), **Lovable**, **Google Stitch** (stitch.withgoogle.com — Gemini-powered, exports to Figma/HTML), **Antigravity**, **Claude Artifacts**, **Cursor Composer**.
- Can any of these be used as a design-to-code pipeline for CineForge? (Design screens in tool X → export → integrate into codebase?)
- What's the best workflow for iterating on UI with Claude Code specifically? Screenshot-driven? Component-first? Design tokens?
- What patterns lead to AI generating BAD UI code? (Over-abstraction, unclear design systems, too many competing patterns?)

### 3. Framework Evaluation

- Should we stay on React 18, or is there a compelling reason to switch?
- Evaluate: **React 19** (if stable), **Solid.js**, **Svelte 5**, **Vue 3** — specifically for AI code generation quality.
- Does any framework produce materially better AI-generated code than React?
- SSR/SSG considerations: CineForge is a local dev tool (localhost), not a deployed web app. Does Next.js/Remix/etc. add value, or just complexity?

### 4. Specialized Viewer Libraries

CineForge needs type-specific artifact viewers. Recommend specific libraries for:

- **Screenplay/script text**: Rendering Fountain-formatted text with proper screenplay formatting (sluglines, action, dialogue, parentheticals). Any React-compatible Fountain renderers?
- **Structured data browser**: Collapsible JSON/YAML viewer with syntax highlighting, search, copy. Think Postman-style but embeddable.
- **Graph visualization**: For entity relationship graphs (characters ↔ locations ↔ props) and artifact dependency/lineage graphs. Evaluate: react-flow, d3, vis.js, cytoscape.js, sigma.js.
- **Diff/comparison views**: Side-by-side or inline diffs for artifact version comparison. Monaco diff? react-diff-viewer?
- **Timeline/track visualization**: For future phases (shot timeline, audio tracks). What libraries support track-based editing UIs? Is there a React equivalent of a DAW-style timeline?

### 5. Recommendation

Based on all research, provide:
1. **Recommended component library** with clear rationale.
2. **Recommended framework** (stay React or switch, with reasoning).
3. **Recommended development workflow** for AI-assisted UI coding.
4. **Viewer library picks** per artifact type.
5. **Stack migration plan**: What changes from the current stopgap, and what stays?
6. **What NOT to do**: Anti-patterns for AI-generated UI development.

## Output Format
Structure your response with clear headings matching the research areas above. Be specific — name libraries, version numbers, and cite real capabilities (not vague assessments). If you're unsure about Feb 2026 availability of something, say so explicitly. End with a concrete, actionable recommendation section.

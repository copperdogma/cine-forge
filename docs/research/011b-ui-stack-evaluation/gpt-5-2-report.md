---
type: research-report
topic: 011b-ui-stack-evaluation
canonical-model-name: gpt-5.2
collected: '2026-02-15T01:24:49.906143+00:00'
---

## 1) Component Library Selection (Primary Decision) — optimized for AI-written code (Feb 2026)

### What “AI-optimized” means in practice
When AI agents write 100% of UI code, the best library is the one that:
- **Has a narrow, consistent API** (reduces hallucinated props/variants).
- **Encodes accessibility and interaction correctness** (keyboard, focus, ARIA, portals, layering).
- **Has strong “default beauty”** (so the AI doesn’t need to invent a design system every time).
- **Still allows a high visual ceiling** via tokens + composition (so you don’t plateau at “generic dashboard”).

Below is a library-by-library evaluation against your criteria.

---

### A. shadcn/ui (Radix + Tailwind, copy/paste)
**1) AI code quality**
- **Very high** for Claude/Cursor/Codex because the patterns are extremely common in training data and the components are “just React code.”
- AI is good at producing *working* dialogs/menus/tabs because Radix handles the hard parts.
- Failure mode: AI often **forks components inconsistently** (slightly different button variants, spacing scales, duplicated cn() helpers) unless you enforce a strict component registry.

**2) Visual ceiling**
- **Higher than people think**, but only if you treat it as a *starting kit*, not a “theme.”
- Out of the box it tends to converge to the recognizable “shadcn look” (neutral grays, rounded-md, subtle borders).
- You can absolutely reach “creative tool” quality, but you must add:
  - **Design tokens** (color ramps, elevation, blur, noise, accent system)
  - **Motion** (micro-interactions)
  - **Layout primitives** (panels, splitters, inspector patterns)
  - **Iconography + typography system**
- Without those, it plateaus at “clean dev dashboard.”

**3) Composability**
- **Excellent**. Because it’s your code, AI can refactor and extend freely.
- Radix primitives compose well (Popover + Command + ScrollArea, etc.).

**4) Accessibility defaults**
- **Strong** (Radix is generally excellent for keyboard/focus/ARIA).
- Caveat: once you heavily customize, AI can accidentally break semantics (e.g., div buttons, missing labels). You need linting + review gates.

**5) Bundle size / performance**
- Generally **good**. You only ship what you copy.
- Tailwind can be very small with proper content scanning.
- Radix adds some weight but is reasonable for a console app.

**6) Dark mode / theming**
- **Good** if you adopt CSS variables + tokens (shadcn supports this pattern).
- AI can manage theme variables reliably if you keep them centralized.

**Net:** Best “AI reliability + flexibility” option, but you must invest in tokens and a component registry to avoid “shadcn sameness.”

---

### B. Radix UI (direct, unstyled primitives)
**1) AI code quality**
- Mixed. AI can wire primitives correctly, but **styling from scratch is where quality drops**.
- You’ll get more “almost right” spacing, focus rings, layering bugs, and inconsistent states unless you provide a strong design spec.

**2) Visual ceiling**
- **Very high** (it’s unstyled).
- But the ceiling is irrelevant if AI can’t consistently reach it without human design direction.

**3) Composability**
- Excellent.

**4) Accessibility defaults**
- Excellent (Radix strength).

**5) Bundle size / performance**
- Good.

**6) Dark mode / theming**
- Up to you; AI often creates fragmented theming approaches unless constrained.

**Net:** Great primitives, but **not optimal** if AI must invent the entire styling system repeatedly.

---

### C. Mantine (full-featured, opinionated)
**1) AI code quality**
- Usually **correct**, but the API surface is large and AI sometimes:
  - mixes v6/v7 patterns,
  - guesses prop names,
  - misuses theming hooks.
- When it’s right, it’s productive; when it’s wrong, debugging is non-trivial.

**2) Visual ceiling**
- **Moderate to high**. Mantine can look polished, but it has a recognizable “Mantine app” feel unless you deeply theme it.

**3) Composability**
- Good, but you’re working within Mantine’s system. Extending beyond it can get awkward.

**4) Accessibility defaults**
- Generally good, but varies by component. (You still need audits.)

**5) Bundle size / performance**
- Can be heavier than Radix+handpicked components because you tend to import more.

**6) Dark mode / theming**
- Strong theming story; dark mode is straightforward.

**Net:** Good if you want a cohesive system quickly, but **AI confusion risk** is higher due to breadth/version drift.

---

### D. Park UI (Ark UI + tokens)
**1) AI code quality**
- Risk: **less training data** than shadcn/Radix/MUI/Ant.
- AI may hallucinate APIs or produce outdated examples.

**2) Visual ceiling**
- Potentially high because tokens-first can look very “designed.”

**3) Composability**
- Good in principle (Ark primitives), but depends on how stable your chosen patterns are.

**4) Accessibility defaults**
- Ark UI aims for accessible primitives, but you must verify component-by-component.

**5) Bundle size / performance**
- Likely fine, but depends on implementation.

**6) Dark mode / theming**
- Tokens-first is good for dark themes.

**Net:** Promising, but **not the safest** for “AI writes everything” unless you lock down internal docs/examples and treat it as an internal design system.

---

### E. Chakra UI v3 (Ark UI-based rewrite)
**1) AI code quality**
- Transitional risk: AI may output Chakra v2 patterns (very common) that don’t match v3.
- If v3 is fully stable and widely adopted by Feb 2026, this improves—but I can’t guarantee the training mix is clean.

**2) Visual ceiling**
- Historically “clean app UI,” not “creative tool,” unless heavily customized.

**3) Composability**
- Good, but Chakra abstractions can fight bespoke layouts.

**4) Accessibility defaults**
- Generally good.

**5) Bundle size / performance**
- Historically not the lightest; v3 may improve, but unknown.

**6) Dark mode / theming**
- Strong.

**Net:** Could be viable, but **version mismatch risk** is real for AI-generated code.

---

### F. Ant Design
**1) AI code quality**
- High correctness because Ant is very prescriptive and well-documented.
- AI tends to generate working forms/tables quickly.

**2) Visual ceiling**
- **Low for “creative tool.”** Ant looks like enterprise software. You can theme it, but it fights you.

**3) Composability**
- Moderate. You often adapt your UI to Ant’s patterns.

**4) Accessibility defaults**
- Mixed historically; improving, but you must test. (Ant has had a11y gaps in some components over time.)

**5) Bundle size / performance**
- Can be heavy, especially if you pull in many components.

**6) Dark mode / theming**
- Possible, but deep theming is non-trivial and can be brittle.

**Net:** Great for admin/enterprise; **wrong vibe** for CineForge’s “creative tool” target.

---

### G. Material UI (MUI)
**1) AI code quality**
- High. MUI is extremely common in training data; AI generates correct component usage often.
- Failure mode: AI mixes v4/v5/v6 patterns or uses deprecated props.

**2) Visual ceiling**
- Medium. You can make beautiful UIs, but it tends to look “Material” unless you fight it.

**3) Composability**
- Good, but the styling system and overrides can get complex for AI.

**4) Accessibility defaults**
- Generally strong.

**5) Bundle size / performance**
- Can be heavy; tree-shaking helps but real apps often import a lot.

**6) Dark mode / theming**
- Strong theming, but deep customization is verbose.

**Net:** Reliable, but tends to produce “Google-ish app UI,” not bespoke creative tooling.

---

### H. “Others” worth considering (Feb 2026)
- **Base UI (by MUI team)**: unstyled primitives approach. If mature by 2026, it’s similar to Radix in concept; AI reliability depends on adoption.
- **React Aria / React Spectrum**: extremely strong a11y primitives and patterns. Historically more complex APIs; AI can struggle unless you provide strict examples. Visual ceiling depends on your styling layer.
- **Fluent UI (Microsoft)**: polished, but “enterprise Microsoft” aesthetic; not ideal for creative tool vibe.

---

### Component library conclusion (AI-first)
If the goal is **maximum correctness + polish with AI writing everything**, the best practical choice is:

**shadcn/ui + Radix primitives + a CineForge token system + a strict component registry**  
This gives you:
- Radix-level interaction correctness
- AI-friendly copy/paste code patterns
- Full control to escape the “shadcn look” via tokens and curated components

The key is to treat shadcn as **source code you own**, not a “library you use.”

---

## 2) AI-Assisted UI Development Workflow (Feb 2026)

### State of the art (Feb 2026)
The best results come from **constraining the AI**:
- A **single design system** (tokens, spacing scale, typography, radii, elevation, motion)
- A **component registry** (Button, IconButton, Panel, InspectorRow, SplitView, DataTable, EmptyState, Toast, etc.)
- A **screen-by-screen spec** (layout + states + keyboard behavior)
- **Screenshot-driven iteration** (AI is much better at “match this” than “invent something tasteful”)

AI is now strong at:
- Generating correct React component code
- Wiring state machines and keyboard interactions (if you specify)
- Producing consistent styling **if tokens are enforced**

AI is still weak at:
- Inventing a coherent visual language without references
- Avoiding subtle a11y regressions without tooling
- Avoiding over-engineering unless you explicitly forbid it

---

### Tooling evaluation (design-to-code potential)

#### v0 (Vercel)
- Strength: fast generation of React/Tailwind/shadcn-style UIs; good for “starter screens.”
- Weakness: tends to converge to the v0/shadcn aesthetic; exports often need refactoring into your component registry.
- Best use: **rapid mock screens** → then “port” into CineForge components.

#### Bolt (StackBlitz)
- Strength: full-stack sandboxing; quick runnable prototypes.
- Weakness: code quality varies; tends to generate more scaffolding than you want.
- Best use: **throwaway prototypes** for complex interactions.

#### Lovable
- Strength: productized “app generation” workflows.
- Weakness: often optimizes for shipping a generic app, not integrating into an existing design system.
- Best use: ideation, not production UI.

#### Google Stitch (stitch.withgoogle.com)
- Strength: design-to-code / Figma-ish export workflows; can help with layout exploration.
- Weakness: exports often become “static HTML/CSS” that must be re-componentized; risk of non-idiomatic React.
- Best use: **layout reference** + token extraction, not direct production code.

#### Antigravity
- I don’t have reliable, up-to-date technical details on its Feb 2026 capabilities/exports. Treat as experimental unless you validate output quality.

#### Claude Artifacts
- Strength: excellent for iterating on a single component/screen with immediate visual feedback.
- Weakness: integration step still required; artifacts can drift from your repo conventions.
- Best use: **component sketchpad** with strict prompts (“use CineForge tokens, use our Panel component”).

#### Cursor Composer (and similar agentic IDE flows)
- Strength: best-in-class for repo-aware edits, refactors, and multi-file changes; can follow your patterns if they exist.
- Weakness: if your repo has inconsistent patterns, it will amplify inconsistency.
- Best use: **primary implementation environment** once your design system is established.

---

### Best workflow for Claude Code specifically (production-quality)
1. **Lock a design system contract**
   - `tokens.css` (CSS variables): colors, typography, radii, elevation, spacing, motion durations
   - Tailwind config maps to tokens (or use CSS vars directly)
2. **Create a CineForge UI package**
   - `/ui` folder with curated primitives: `Button`, `IconButton`, `Panel`, `SplitView`, `Tabs`, `Toolbar`, `Inspector`, `DataGridShell`, `EmptyState`, `Skeleton`, `Toast`
   - Wrap Radix where needed (Dialog, Popover, DropdownMenu, Tooltip)
3. **Component-first generation**
   - Ask Claude to implement/modify **one component at a time**, with explicit acceptance criteria (keyboard nav, focus trap, aria-labels, loading/empty/error states)
4. **Screenshot-driven iteration loop**
   - Provide: screenshot + “match this spacing/typography” + “do not introduce new tokens”
   - Require: before/after diffs and a short checklist (a11y, states)
5. **Automated gates**
   - ESLint + TypeScript strict
   - Storybook (or Ladle) for visual regression targets
   - Playwright component tests for keyboard/focus
   - axe-core checks in CI for key screens

---

### Patterns that lead to bad AI UI code
- **No tokens** → AI invents new colors/spacing every file.
- **Multiple styling paradigms** (Tailwind + CSS modules + inline styles + styled-components) → inconsistency explodes.
- **Over-abstraction early** (generic “RendererFactory”, “UniversalPanel”) → unreadable and brittle.
- **Single giant file** (your current App.tsx) → AI loses local reasoning and repeats patterns incorrectly.
- **Unclear interaction specs** (“make it like Figma”) → AI guesses wrong keyboard behavior and focus management.
- **Competing component sources** (some shadcn, some Mantine, some custom) → mismatched props and styling.

---

## 3) Framework Evaluation (AI code generation quality)

### Stay React or switch?
For an operator console / creative tool UI, **React remains the safest choice for AI-generated correctness** because:
- Most training data and best-practice examples
- Best ecosystem for complex UI widgets (editors, graphs, diff, virtualization)
- AI agents are consistently better at React than alternatives in edge cases

#### React 18 vs React 19
- If **React 19 is stable in your environment**, it’s generally worth adopting for:
  - improved concurrent features and ecosystem alignment
  - better long-term compatibility with modern libraries
- But React 18 is fine if stability is paramount. The bigger win is **architecture + component system**, not the React version.

#### Solid.js / Svelte 5 / Vue 3 (AI perspective)
- **Svelte 5**: AI can generate Svelte components, but complex state + large app architecture tends to drift. Ecosystem for specialized viewers is thinner than React.
- **Vue 3**: AI does okay, but again fewer “drop-in” specialized console widgets than React.
- **Solid.js**: excellent performance, but AI often makes reactivity mistakes (signals vs memos) unless tightly guided.

**Net:** None of these produce *materially better AI-generated UI* than React for your use case. React’s ecosystem advantage dominates.

### SSR/SSG frameworks (Next.js/Remix/etc.)
CineForge is a **localhost tool**, not a content site:
- SSR/SSG adds complexity (routing conventions, server/client boundaries, bundling constraints) with little benefit.
- Unless you need auth, server rendering, or deployment, prefer a **client-only app**.

**Recommendation:** React + Vite remains ideal. Consider **TanStack Router** only if you need robust routing; otherwise keep it simple.

---

## 4) Specialized Viewer Libraries (artifact-specific)

### A) Screenplay/script text (Fountain)
Goal: render Fountain into properly formatted screenplay layout (Courier-like, margins, dialogue blocks).

Options (React-compatible):
- **fountain-js** (parser) + custom renderer  
  - Use fountain-js to parse into tokens/AST, then render with your own layout rules.
  - This is often the most reliable path for “final draft-like” formatting.
- **fountain** npm packages vary; many are parsers, not renderers.  
  - Practical approach: **parser + your renderer** is usually necessary for production formatting.

Recommendation:
- **Use `fountain-js` for parsing** and build a **CineForge ScreenplayRenderer** component:
  - supports pagination (optional), scene list, character list extraction
  - selectable text, copy, search, and “jump to scene”
  - print-like CSS for accurate indentation

### B) Structured data browser (JSON/YAML)
- **react-json-view** (popular, but check maintenance status) or **@uiw/react-json-view** (a maintained fork in many stacks)
- **monaco-editor** for raw JSON/YAML with search, folding, schema validation
- For YAML parsing: **yaml** package

Recommendation:
- For “Postman-style inspector”:  
  - **Monaco Editor** for raw + schema + search  
  - plus a tree viewer like **@uiw/react-json-view** for collapsible browsing  
  - Add copy-path, copy-value, and filter/search.

### C) Graph visualization (relationships + lineage)
Evaluate:
- **react-flow**: best for node-edge editors, interactive graphs, minimap, pan/zoom, custom nodes. Great for “dependency graph” UIs.
- **cytoscape.js**: very capable for large graphs and layouts; more “graph science,” less “React-native feel.”
- **d3**: maximum control, maximum custom work; AI can generate d3 but correctness/maintainability suffers.
- **sigma.js**: great for large network visualization (WebGL), but more specialized.
- **vis.js**: older; many projects moved away due to maintenance fragmentation.

Recommendation:
- **react-flow** for artifact lineage and editable relationship graphs (best UX for operator console).
- If you anticipate **very large graphs (10k+ nodes)**, consider **sigma.js** for performance, but it’s a different UX paradigm.

### D) Diff/comparison views
- **Monaco Editor Diff**: best-in-class for text diffs, especially for JSON, scripts, logs.
- **react-diff-view** / **react-diff-viewer**: fine for simpler diffs, but Monaco is more “tool-grade.”

Recommendation:
- **Monaco diff editor** for artifact versions (inline + side-by-side).
- Add semantic diff for JSON (optional): compute JSON patch and render a structured diff view.

### E) Timeline/track visualization (DAW-style)
This is the hardest category; most “DAW-like” UIs are custom.

Options:
- **react-konva** (canvas-based) for performant custom timeline rendering.
- **pixi.js** (via React bindings) for high-performance 2D rendering.
- **d3** for scales + custom rendering (but you’ll still need a rendering layer).
- Some niche “react timeline” libraries exist, but most are not DAW-grade (no snapping, trimming, multi-track editing, waveforms).

Recommendation:
- Plan for a **custom timeline** built on:
  - **react-konva** (or Pixi) for rendering
  - your own interaction model (drag, trim, snap, zoom)
- If you need waveforms later: integrate a waveform renderer (often custom canvas) rather than expecting a turnkey React library.

---

## 5) Recommendation (concrete, actionable)

### 5.1 Recommended component library
**Primary pick: shadcn/ui (as source) + Radix UI primitives + CineForge design tokens**

Rationale (AI-first):
- Highest probability that AI generates **correct, working components** with minimal prop hallucination.
- Radix gives you **accessible interaction primitives** (menus, dialogs, popovers, focus management).
- Owning the code lets you push beyond the “shadcn look” by enforcing:
  - a token system
  - a curated component registry
  - consistent motion/typography

What to add to escape “developer dashboard”:
- A **tokenized theme** (CSS variables) with:
  - richer neutrals, accent ramps, semantic colors
  - elevation/blur/noise layers (creative tool feel)
  - typography scale (including mono for code/artifacts)
- A **layout system**: Split panes, dockable panels (even if not fully dockable yet), inspector patterns, command palette, toolbars.

### 5.2 Recommended framework
**Stay on React + Vite. Move to React 19 if stable for you; otherwise keep React 18.**
- Do **not** add Next.js/Remix unless you have a clear need (auth/SSR/deployment).
- Add:
  - **TanStack Query** (artifact fetching/caching) if you have async data
  - **TanStack Virtual** for large lists/tables
  - A router only if multi-screen navigation becomes real (TanStack Router or React Router)

### 5.3 Recommended AI-assisted development workflow
1. **Refactor into a real component architecture**
   - Break the 1800-line `App.tsx` into screens + components.
2. **Create a “CineForge UI Contract” doc for AI**
   - Tokens, spacing scale, component usage rules, do/don’t examples.
3. **Use Cursor/Claude Code as the primary repo-aware agent**
   - Enforce: “Only use components from `/ui` unless adding a new one.”
4. **Add Storybook (or Ladle) + visual regression**
   - Every new component gets a story with states.
5. **Add a11y + keyboard tests**
   - Playwright + axe-core checks for key screens (dialogs, menus, forms).

### 5.4 Viewer library picks (by artifact type)
- **Screenplay (Fountain):** `fountain-js` parser + custom React renderer (CineForge-owned)
- **Structured data:** Monaco Editor + `@uiw/react-json-view` (tree) + `yaml`
- **Graphs:** `react-flow` (primary); consider sigma.js only for very large graphs
- **Diff:** Monaco diff editor
- **Timeline:** custom on `react-konva` (or Pixi) + your interaction model

### 5.5 Stack migration plan (from current stopgap)
Keep:
- React + TypeScript
- Vite
- Tailwind (but move to token-driven Tailwind)

Change:
1. **Introduce tokens**
   - `tokens.css` with CSS variables
   - Tailwind config maps `colors`, `borderRadius`, `boxShadow`, etc. to variables
2. **Adopt shadcn/ui properly**
   - Generate/copy components into `/ui`
   - Standardize `cn`, variants, and file structure
3. **Create CineForge-specific components**
   - `Panel`, `SplitView`, `Inspector`, `Toolbar`, `CommandPalette`, `ArtifactHeader`, `StatusPill`
4. **Decompose App.tsx**
   - `/screens/*`, `/features/*`, `/ui/*`, `/viewers/*`
5. **Add quality gates**
   - ESLint rules for a11y basics
   - Storybook + Playwright + axe

### 5.6 What NOT to do (AI UI anti-patterns)
- Don’t mix multiple component libraries (e.g., Mantine + shadcn + MUI) in one app.
- Don’t let AI invent new colors/spacing per component—**tokens only**.
- Don’t build a “universal renderer framework” early; build concrete viewers first.
- Don’t keep large monolithic files; AI will duplicate logic and styling.
- Don’t rely on AI to “make it beautiful” without references—use screenshots, mood boards, and explicit token constraints.
- Don’t skip a11y automation; AI will regress focus/labels over time.

---

# Final, actionable recommendation (CineForge Operator Console)

**Choose:** React (18/19) + Vite + TypeScript + Tailwind (tokenized) + **shadcn/ui (owned source) + Radix**  
**Build:** a CineForge design token system + curated `/ui` registry + Storybook + a11y/keyboard CI gates  
**Use AI effectively:** screenshot-driven iteration + strict component usage rules + avoid over-abstraction  
**Viewers:** fountain-js+custom renderer, Monaco (+ JSON tree), react-flow, Monaco diff, custom Konva timeline

If you want, I can propose a concrete `/ui` component inventory (20–30 components) and a `tokens.css` starter palette specifically tuned for “creative tool dark UI” (elevation, translucency, accent behavior, focus treatment) so AI agents have a stable target to generate against.
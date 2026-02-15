# UI Stack Evaluation

**Status**: Researched and reviewed
**Method**: Deep research (3 providers: GPT-5.2, Claude Opus 4.6, Gemini 3)
**Research**: `docs/research/011b-ui-stack-evaluation/final-synthesis.md`
**Decisions**: Captured in `docs/design/decisions.md`

---

## Summary

Research complete. Three AI providers evaluated component libraries, frameworks, state management, and viewer libraries optimized for AI-assisted development. Final synthesis reviewed with Cam on 2026-02-15. All key decisions captured in `docs/design/decisions.md`.

### Chosen Stack
- **shadcn/ui** + custom design tokens (component library)
- **React 19** + Vite + TypeScript (framework)
- **Tailwind CSS** (styling)
- **Zustand** (client state management)
- **TanStack Query** (server state / API caching)
- **CodeMirror** (screenplay viewer), **ReactFlow** (graphs, post-MVP), **Recharts** (stats)

### Build approach
Fresh build from scratch. The existing Operator Console Lite is a throwaway prototype — preserved as reference only. Primary build tool is Claude Code + Chrome MCP for visual feedback loop. v0.dev for design exploration when component shape is uncertain.

See `docs/design/decisions.md` for the full set of decisions including AI development workflow and anti-patterns.

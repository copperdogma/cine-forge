# Story 102 — Promptfoo Multi-Turn Conversational Evals

**Priority**: Medium
**Status**: Draft
**Spec Refs**: —
**Depends On**: —

## Goal

Add multi-turn conversational eval test cases to the promptfoo benchmark suite. CineForge's AI roles (Director, Character, Sound Designer) operate in conversation chains where context from earlier turns affects later responses. Single-turn evals miss regression in conversational continuity, persona consistency across turns, and constraint adherence under sustained interaction. Use promptfoo's `_conversation` + `conversationId` pattern to test multi-turn scenarios.

## Notes

- Sourced from Scout 003 (Storybook's `luna-persona.eval.yaml` pattern)
- promptfoo supports multi-turn via `_conversation` flag and `conversationId` on test cases
- Each turn can have its own LLM-rubric assertion
- Focus areas: role persona consistency, creative direction coherence across turns, constraint adherence under pressure
- These evals cost real API money — separate from unit test suite
- Benchmark workspace is in the `cine-forge-sidequests` worktree

## Work Log

20260228 — Created as Draft from Scout 003 finding #6.

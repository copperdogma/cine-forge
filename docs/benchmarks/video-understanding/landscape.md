# Video Understanding Landscape

## Comparison Matrix

| Benchmark | What It Measures | Modalities | Director-Level Fit | Licensing / Internal-Use Feasibility | CineForge Gap |
|---|---|---|---|---|---|
| Video-MME | Broad video QA, subtitle-aware understanding, temporal recall | Visual, optional subtitles, temporal | Medium-low. Strong for generic comprehension, weak on cinematography and continuity nuance. | Research benchmark, useful as a reference task family, but not a clean project-owned internal regression corpus. Re-check terms before shipping any bundled clips. | Does not score director-facing reads like shot language, color intent, or generated-output continuity drift. |
| MVBench | Multi-task video reasoning across movement, counting, action, and event understanding | Visual, temporal | Low. Good motion/task coverage, but not built around cinematic interpretation. | Research release; suitable for ideas and challenge categories, not a drop-in owned eval set. | Little coverage for tone, emotional read, or previz-style artistic intent. |
| TempCompass | Temporal ordering, before/after reasoning, event sequencing | Visual, temporal | Low. Helpful for motion and temporal coherence thinking, but not for scene craft. | Research benchmark rather than an internal regression asset. | No meaningful camera-language or color-grade evaluation. |
| MLVU | Long-video understanding, summarization, retrieval, reasoning over extended clips | Visual, temporal, long-context | Medium-low. Useful for memory/recall patterns, but not for short-form director QA. | Research-focused; heavier operational footprint than CineForge needs for short generated scenes. | Solves the wrong runtime problem: long-context recall rather than per-scene generated-output judgment. |
| LongVideoBench | Long-horizon video reasoning and retrieval | Visual, temporal, long-context | Low for Story 030. Strong on duration stress, weak on generated-scene craft. | Research corpus; clip ownership and redistribution are the wrong fit for repo-native regression assets. | Long-form retrieval is not the current blocker for generated scene QA. |
| CineTechBench | Cinematic understanding, film-language and critic-style reads | Visual, dialogue-aware, film-specific | Medium-high conceptually. Best public signal for director-facing language. | Better thematic alignment, but still not a clean, repo-owned regression substrate for internal reruns. | Closer to the target, but still does not give CineForge a stable, project-owned benchmark corpus tied to generated outputs. |

## Conclusion

**Existing public benchmarks are insufficient as the primary Story 030 benchmark. CineForge needs its own benchmark.**

Public suites are still useful inputs. They tell us which dimensions matter, what temporal traps good models fail on, and how to structure judge prompts. They do **not** solve the repo-fit problem:

- CineForge needs a **project-owned** benchmark corpus that can rerun safely in-repo without rights ambiguity.
- Story 030 is about **generated output QA**, not generic video question answering.
- Director-facing cues like tone, shot language, color intent, continuity drift, and audio contrast are underrepresented or only indirectly measured in the public sets.
- Several public suites are effectively **research assets**, not stable operational substrates for CineForge's day-to-day regression loop.

## Reuse Strategy

Use the public landscape as design input, not as the final benchmark substrate:

- Borrow the **task families**: temporal coherence, motion reasoning, dialogue-aware analysis, and long-context caution.
- Borrow the **failure patterns**: missed continuity changes, shallow summarization, and overreliance on subtitles or literal object naming.
- Keep the **dataset local and synthetic** for v1 so rights are clean and the eval remains reproducible.
- Reserve **true lip-sync validation** for a later benchmark slice built on licensed human-footage clips. Synthetic previz clips cannot honestly validate that dimension.

## Story 030 Decision

Build a CineForge-specific promptfoo benchmark around:

- 20 synthetic previz-style clips
- normalized target/prediction/score schemas
- deterministic scorer plus Opus-judged semantic rubric
- pilot-first execution on an anchor subset before scaling to the full matrix

# Lightweight Test Fixture Contract

These small fixtures are repo-maintained test inputs, not benchmark goldens.

- `sample_screenplay.fountain` and `sample_prose.txt` are paired, repo-authored
  *Signal in the Rain* fixtures created for Story 007. They exercise screenplay
  passthrough and prose-to-screenplay paths using the same narrative material.
- `mariner-two-scenes.fountain` is a local two-scene excerpt fixture added with
  the value/default evaluation work. Its upstream publication or licensing
  provenance is not recorded, so it is restricted to local structural and
  integration checks and must not be presented as a public or decision-grade
  benchmark corpus.

Assertions using these files should pin source facts (title, ordered headings,
named characters, or exact dialogue), not merely non-empty output.

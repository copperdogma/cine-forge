# Ordered-frame truth overlay v4

The six target JSON/Markdown pairs here are the maintained scoring references for `tasks/video-understanding.yaml`. The five JPEGs, neutral metadata, and subject prompt still come from `benchmarks/video_understanding/`. No video or audio is submitted. The original v3 targets and prior results remain unchanged for audit.

`benchmarks/scripts/build_video_understanding_truth_v4.py --check` verifies every target and the overlay manifest against the current v3 source media. Use `--write` only when making another source-verified truth correction; preserve the current v4 artifact and use a new version for future semantic changes.

Corrections relative to v3:

- Dialogue: bodies enlarge at fixed centers but the prop/background do not scale, so a camera mechanism is not established. Camera is excluded from the deterministic aggregate; the semantic reference asks for the visible size change without requiring a push-in label.
- Bedside: the left round-topped form and horizontal block permit more than one object reading. The summary target uses visible geometry and stillness rather than requiring the hidden lamp/bed interpretation.
- Rooftop: the runner keeps the same pixel size while crossing the gap, and its lateral speed is constant. The larger/escalating requirements were removed.

The alarm, prop-swap, and storm references are byte-identical copies of v3. All six JPEG packets are byte-identical to v3. The full source and corrected-target SHA-256 hashes are in `manifest.json`.

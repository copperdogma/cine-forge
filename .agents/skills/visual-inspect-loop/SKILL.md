---
name: visual-inspect-loop
description: Manually inspect visual or rendered artifacts against their source, record concrete quality gaps, convert them into generic failure classes, patch the pipeline, rerun, and reinspect. Use when correctness depends on screenshots, page images, crops, generated HTML/PDF/slides, OCR output, UI renders, or other artifacts where tests/logs are not enough.
user-invocable: true
---

# /visual-inspect-loop [artifact or page]

> Alignment check: Before choosing an approach, verify it aligns with `docs/ideal.md`
> and relevant decision records in `docs/decisions/`. If this work touches a known
> compromise in `docs/spec.md`, respect its limitation type and evolution path.
> If none apply, say so explicitly.

Use this when artifact quality is visual, spatial, semantic, or source-faithfulness dependent.

## Core Rule

You are not only an orchestrator. You are the inspection instrument.

Do not write code to guess what the user asked you to personally inspect before you have actually inspected it. Render the source and result, look at them yourself, reason about what is wrong, then use code to make that judgment reproducible.

Automation preserves and scales your judgment. It does not replace the first judgment.

## When To Use

Use this skill for:

- source PDF/page/image versus generated HTML, Markdown, text, crop, or bundle output
- OCR/layout/crop/figure-placement quality checks
- UI screenshots, rendered pages, slide decks, document renders, charts, or visual reports
- any task where "it ran" does not prove "it is correct"
- any user request for manual inspection, visual comparison, iterative QA, or "look at the output"

Do not use this as a generic code-review loop. Use `validate` or `loop-verify` for non-visual review.

## Loop

1. Pick a small target.
   - Prefer one page, screen, slide, chart, crop group, or chapter.
   - Choose a high-signal target with multiple decision types when possible.

2. Build a QA packet.
   - Source artifact: original page/image/render.
   - Result artifact: output screenshot/render/HTML/PDF/crop result.
   - Intermediate evidence: manifests, crop sheets, OCR text, provenance, conformance report, logs.
   - Put the packet in an inspectable path and cite it in notes.

3. Personally inspect.
   - Open the source and result visually.
   - Compare content, order, hierarchy, layout-dependent meaning, missing items, extra items, over/under-crops, duplicated content, and semantic prominence.
   - Decide what should be text, what should be a source-pixel figure, what is decorative, and what is uncertain.
   - Do this before patching code.

4. Write notes before fixing.
   - Record what is right.
   - Record what is wrong.
   - Record the expected behavior.
   - Name the generic failure class.
   - Avoid page-specific or title-specific fixes unless the story explicitly owns a one-off output.

5. Patch the generic system.
   - Change code, prompt, recipe knobs, schema, or validator behavior for the failure class.
   - Keep source-pixel provenance intact for visual content.
   - Never manually edit final generated output as the solution.

6. Rerun cheaply and honestly.
   - Reuse expensive upstream artifacts when valid.
   - Start from the narrowest safe pipeline stage.
   - Regenerate the inspected result, not a side copy.

7. Reinspect the same target.
   - Open the new result and compare it to the source again.
   - Confirm the original issue is fixed.
   - Check for obvious regressions on nearby or representative previously-fixed targets.

8. Preserve the learning.
   - Add a regression test or validator only after the manual failure is understood.
   - Save the QA packet and notes in the repo/story artifact location.
   - Update story/work-log evidence with artifact paths and sample observations.

## Inspection Note Template

```markdown
## Target
- Source:
- Output:
- Intermediates:

## What Looks Right
- ...

## Problems Found
- ...

## Expected Behavior
- ...

## Generic Failure Class
- ...

## Fix Attempt
- ...

## Rerun Evidence
- ...

## Reinspection Result
- ...

## Remaining Caveats
- ...
```

## Guardrails

- Do not rely on a passing test, validator, or model response as visual proof.
- Do not replace personal inspection with a detector, OCR heuristic, or model call unless the user explicitly asks for a fully automated pass.
- Do not overfit the fix to a page number, source title, fixture name, or exact phrase when the issue is a category behavior.
- Do not claim an output is good unless you opened the rendered artifact or source/result images in the current pass.
- Do not broaden canonical format coverage from one local inspected artifact unless the repo has a maintained fixture/eval proving the category.
- If the result is still mixed, say so and name the remaining failure mode.

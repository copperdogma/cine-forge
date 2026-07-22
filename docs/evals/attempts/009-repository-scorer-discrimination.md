# Eval Attempt 009 - Repository Scorer Discrimination

**Status:** Succeeded with documented limitations
**Eval:** repository-scorer-discrimination (13 maintained scorer families)
**Date:** 2026-07-21
**Worker Model:** GPT-5.6
**Subject Model(s):** Cached historical outputs only during repair; bounded current-default and ceiling confirmations after the harness gate

## Mission

Make every maintained deterministic scorer discriminate a valid answer from
contract-specific adversarial mutations without weakening legitimate semantic
flexibility. The immediate target is not a higher model score: it is to prevent
empty, generic, fabricated, overpredicted, wrong-scene, wrong-relationship,
ungrounded-evidence, or prohibited-format outputs from clearing an adoption
threshold. Only after scorer and golden truth are independently green will
cached subject outputs be rescored and latency/cost-neutral decision deltas be
recorded.

## Prior Attempts

Read Attempts 001 through 006 before repair. Their durable constraints are:

- Config Attempt 001 proved scorer/golden/rubric defects can invert rankings;
  no historical config score is accepted without source-backed re-verification.
- Video Attempt 002 exhausted sampled-frame reruns until a genuinely different
  native-video path exists; output-budget truncation must not be confused with
  semantic failure.
- Scene-enrichment Attempt 003 retired its prompt fix; this campaign changes
  scorer behavior only where an adversarial mutation proves a gap.
- Storyboard Attempts 004-006 split dimensions and rejected prompt-only
  reference anchors. Do not retry them without a stronger visual substrate.

## Baseline Reproduction

The read-only Story 208 audit already demonstrated four adoption-grade false
positives:

- Entity discovery awarded `1.0` when empty strings were supplied as entities.
- Relationship discovery awarded `1.0` with invented relationship types and
  invented evidence.
- Scene extraction awarded `1.0` when every per-scene fact was fabricated but
  aggregate shape remained plausible.
- Video understanding awarded `1.0` for every allowed tag plus hallucinated
  evidence.

Additional source inspection identified untested risks in QA constraints,
normalization fences/speaker attribution, config synonym denominators,
continuity key matching, script-bible keyword-only gates, character/bible
evidence grounding, scene enrichment, and storyboard evidence/reference
discipline. Each risk remains a hypothesis until a checked-in mutation test
reproduces it.

## Classification and Runtime Impact

- **Classification:** scorer-wrong/golden-wrong hypotheses map to CineForge's
  required taxonomy as `golden-wrong` when the evaluation contract rewards a
  materially wrong subject output. Individual subject mismatches remain
  model-wrong, golden-wrong, or ambiguous after cached rescoring.
- **Runtime impact:** default-decision-blocking but generally
  non-runtime-blocking. A scorer defect invalidates model/default evidence; it
  does not by itself prove the shipped runtime output is wrong.
- **Exception:** any scorer test that exposes the same unchecked condition at a
  production boundary receives a separate runtime classification and repair.

## Plan

1. Preserve baseline mutations as direct unit tests before changing each scorer.
2. Group non-overlapping scorer families among focused owners; no owner edits a
   golden under semantic verification or a task prompt/rubric in the same pass.
3. Require, per scorer: a valid/perfect control, contract-specific wrong
   mutations, and monotonicity (a dominated mutation cannot outscore its
   parent). Assert threshold behavior, not brittle internal weights alone.
4. Extract focused helpers before editing the 586-line video scorer or any
   method exceeding the repository size rule.
5. Classify every demonstrated gap before repair. Preserve reasonable aliases,
   paraphrases, and ambiguous judgments rather than forcing exact text.
6. Run direct scorer tests and rescore immutable cached outputs. Record output,
   config, prompt, scorer, and golden hashes; do not make paid model calls while
   only the evaluation contract changes.
7. Audit the matching task prompt and Opus rubric with generic, contradictory,
   answer-copied, and schema-only probes. Change wording only when a probe
   demonstrates a false pass or contradiction.
8. Update registry history and run a bounded current-default plus one ceiling
   confirmation only where repaired evidence could change a default or
   compromise detector.

## Work Log

- 2026-07-21: Created this attempt before scorer mutation. Read all six prior
  attempt files and recorded their retry constraints. Paid calls remain gated.
- 2026-07-21: Preserved the entity-discovery false-perfect as a direct unit
  probe. Before repair, three empty-string entities scored `1.0`; after repair
  they score `0.125` and fail. A grounded control remains `1.0`, removing one
  required prop is strictly worse, and seven invented names trigger the new
  conservative gross-overprediction hard gate. Classification: `golden-wrong`
  evaluation evidence caused by a scorer defect; non-runtime-blocking but
  default-decision-blocking. No subject call, latency, or provider cost.
- 2026-07-21: Preserved relationship discovery's IDs-only false-perfect with
  synthetic source-grounding controls. Before repair, correct endpoint IDs plus
  an invented type and invented long evidence scored `1.0`; after repair the
  wrong-type mutation scores `0.45` and fails, while a correct type with
  fabricated evidence scores `0.80` but fails the grounding gate. The exact
  grounded control remains `1.0`, and removing grounding is strictly worse.
  Classification: `golden-wrong` evaluation evidence caused by a scorer defect;
  non-runtime-blocking but default-decision-blocking. No subject call, latency,
  or provider cost.
- 2026-07-21: Preserved scene extraction's aggregate-only false-perfect. Before
  repair, keeping the headings and global character set while swapping all
  per-scene characters and fabricating scene numbers, locations, interior/
  exterior values, times, and summaries scored `1.0`. The repaired scorer
  aligns each heading once and grades those facts locally; the same mutation
  now scores `0.5777` and fails while the exact control remains `1.0`. A
  one-scene dominated mutation also scores strictly lower. Classification:
  `golden-wrong` evaluation evidence caused by a scorer defect;
  non-runtime-blocking but default-decision-blocking. No subject call, latency,
  or provider cost.
- 2026-07-21: Normalization probes reproduced two independent false-perfect
  paths: a prohibited Markdown-fenced Fountain response and a response with all
  required dialogue assigned to the wrong speakers each scored `1.0`. The
  repaired scorer inspects raw formatting before unwrapping and binds each
  fragment to its preceding Fountain cue. The mutations now fail at `0.85` and
  `0.90` respectively, the exact control remains `1.0`, and content deletion is
  strictly worse. Classification: `golden-wrong` evaluation evidence caused by
  a scorer defect; non-runtime-blocking but default-decision-blocking. No
  subject call, latency, or provider cost.
- 2026-07-21: A fifth independent relationship-golden pass exposed a second
  scorer defect: substring type matching accepted malformed labels such as a
  longer word containing an otherwise valid relationship keyword. Type matching
  now compares normalized declared alternatives exactly; a `mentor` control
  still scores `1.0`, while `tormentor` fails. This is the same
  default-decision-blocking, non-runtime-blocking `golden-wrong` evidence class
  as the earlier relationship false-positive. No subject call or provider cost.
- 2026-07-21: QA-pass probes reproduced four composite-score bypasses: the
  wrong `passed` boolean, a generic issue sharing only the expected field, a
  good-case warning beyond the declared maximum, and a summary missing all
  required conclusions. The repaired scorer hard-gates each declared contract;
  exact good/bad controls remain `1.0`, seven direct tests pass, and dominated
  issue evidence scores lower. Classification: `golden-wrong` evaluation
  evidence caused by scorer defects; non-runtime-blocking but
  default-decision-blocking. No subject call or provider cost.
- 2026-07-21: Config-detection controls reproduced ranking distortion and hard
  contract bypasses. One valid genre and tone alternative was divided by every
  synonym in each list; `not a short film` satisfied the critical format; a
  missing declared field still cleared the composite threshold; and boolean
  confidences counted as numbers. The repaired scorer gives a valid alternative
  group full credit, rejects negated phrases and missing fields, excludes bools,
  and hard-gates declared critical fields. Six exact/adversarial/monotonicity
  tests pass. Classification: `golden-wrong` evaluation evidence caused by
  scorer defects; non-runtime-blocking but default-decision-blocking. No subject
  call or provider cost.
- 2026-07-21: The third independent script-bible pass supplied a hollow payload
  that the old scorer awarded `1.0`: substring title, pure-comedy genre,
  cheerful tone, out-of-range confidence, padding-only synopsis, one-word
  themes, and a malformed later act all escaped its shallow gates. The repaired
  scorer checks every act/theme member, exact title, genre/tone, grounded
  synopsis and conflicts, and confidence; the same class of synthetic hollow
  control now scores `0.605` and fails while an evidence-bearing control stays
  `1.0`. Five perfect/adversarial/monotonicity tests pass. Classification:
  `golden-wrong` evaluation evidence caused by scorer defects;
  non-runtime-blocking but default-decision-blocking. No subject call or cost.
- 2026-07-21: Normalization source-aware probes extended the earlier repair.
  Exact-substring scene matching let one later continuous heading stand in for
  a missing earlier scene; blank-line rules were not hard gates; `NOAH (V.O.)`
  was misclassified as a malformed parenthetical; and action deletion or novel
  action was invisible. The scorer now matches headings uniquely and exactly,
  treats cue extensions correctly, enforces cue spacing, and uses the supplied
  source text for lexical recall, novel-token, V.O., and transition guards.
  Eight direct controls pass. This remains default-decision-blocking,
  non-runtime-blocking `golden-wrong` evaluation evidence. No subject call or
  provider cost.
- 2026-07-21: Scene-enrichment source-first review reproduced four scorer
  failures: a completely wrong heading retained `0.95`; invented `NIGHT` tied
  correct `UNSPECIFIED`; omitting all three thugs still passed at `0.83`; and
  one generic `THUG` satisfied three numbered characters. The repaired scorer
  hard-gates exact heading, source-declared time, and full canonical character
  recall, while evidence details use token coverage instead of a single common
  word. Five direct controls pass and a faithful synthetic answer remains
  `1.0`. Classification: `golden-wrong` evaluation evidence caused by scorer
  defects; non-runtime-blocking but default-decision-blocking. No provider call
  or cost.
- 2026-07-21: Character-extraction probes exposed six contract bypasses: an
  alias could replace the canonical dialogue-cue name, fabricated aliases and
  scenes were not hard failures, only half the required evidence concepts were
  needed, evidence scene labels only had to be arbitrary substrings of the
  screenplay, key traits/facts were not gates, and nested evidence/relationship
  schemas and confidences were not validated. The repaired scorer requires the
  exact canonical identity, exact source-declared alias/scene sets, complete
  required evidence/trait/fact coverage, quotes grounded to a declared source
  scene, and typed nested contracts while preserving a legitimate empty-alias
  array. Nine perfect/adversarial/monotonicity controls pass. Classification:
  `golden-wrong` evaluation evidence caused by scorer defects;
  non-runtime-blocking but default-decision-blocking. No provider call or cost.
- 2026-07-21: The shared location/prop bible scorer accepted identity fragments,
  aliases copied into prose instead of the alias field, a single shared word as
  a complete physical trait, scene words scattered anywhere in the payload,
  partial fact/theme keywords, empty typed fields, and boolean confidence. It
  also used substring golden lookup, allowing one entity name to select another.
  The replacement uses exact normalized entity selection, exact IDs/names,
  typed and substantive schema gates, exact verified alias/scene sets, and
  complete concept coverage for physical facts, key facts, and narrative
  requirements. It preserves the distinct location and prop output contracts;
  nine direct controls for both kinds pass. Classification: `golden-wrong`
  evaluation evidence caused by scorer defects; non-runtime-blocking but
  default-decision-blocking. No provider call or cost.
- 2026-07-21: Continuity probes reproduced the key-reuse and composite bypass
  class: the old scorer ignored `scene_id`, fuzzy-matched entity suffixes across
  types, allowed duplicate/extra entities, properties, and changes, graded
  change evidence globally rather than against the expected entity/property,
  averaged entity confidence so one bad value could hide behind another, and
  did not validate nested types or confidences. Golden mutations also remained
  above the global `0.60` threshold because no critical fact was a hard gate.
  The replacement enforces exact scene/entity identity, one typed state per
  expected entity, exact canonical property sets, complete expected property
  and change criteria, no unmatched changes, source-grounded evidence tied to
  each matching change, all declared evidence coverage, and per-entity/nested
  confidence. Nine perfect/adversarial/monotonicity controls pass.
  Classification: `golden-wrong` evaluation evidence caused by scorer defects;
  non-runtime-blocking but default-decision-blocking. No provider call or cost.
- 2026-07-21: A clean normalization-golden pass then isolated four residual
  source-fidelity bypasses: title deletion (`0.9918`), parenthetical deletion
  (`0.9959`), terminal-punctuation mutation (`1.0000`), and a phantom heading
  (`0.9984`) all passed. Direct source contracts now reject them at `0.9625`,
  `0.9646`, `0.9667`, and `0.9542`, respectively, while directly checking every
  declared structural flag; the cached clean broken-Fountain control remains
  `1.0000`. Seventeen focused tests pass. Classification and runtime impact are
  unchanged; no provider call or cost.
- 2026-07-21: A clean QA-golden pass isolated four remaining composite exploits.
  One-token reasons fell from `1.000 pass` to `0.600 fail`; required defects
  mislabeled as notes plus unrelated error fillers fell from `1.000` to `0.750`
  and fail; all-required warnings plus one unrelated error fell from `1.000` to
  `0.825` and fail; low confidence with an empty summary remains numerically
  `0.800` but fails explicit hard gates. The scorer now binds two-anchor reason
  concepts, per-required actionable/error severity, relevant error counts,
  finite confidence, root issue schema, and substantive failing summaries.
  Twenty-three focused tests pass. No provider call or cost.
- 2026-07-21: Group A prompt/rubric probes demonstrated that source-blind
  judges accepted quotes assigned to the wrong scenes, generic location prose,
  a purse answer missing its amount and gang ownership, and relationship graphs
  with incorrect canonical IDs or relocated evidence. Character, location,
  prop, and relationship subject prompts now expose exact typed schemas and
  source-only contracts; all ten matching Opus rubrics receive the screenplay,
  distinguish facts from interpretations, reject answer copying into the wrong
  field, and hard-fail fabricated evidence or wrong scenes. Twelve contract
  regressions and the combined 35-test Group A contract/scorer slice pass. No
  provider call or cost.
- 2026-07-21: Group B probes demonstrated four independent contract defects.
  Entity discovery explicitly excused false positives and leaked fixture
  answers; cached noun-dump output received `0.85`. Script bible prohibited a
  source-supported comedy component and demanded a completed arc beyond the
  unresolved ending. Scene extraction's judge scored a faithful 15-scene
  output `0.55` because it conventionalized unusual source headings. Scene
  enrichment invited unsupported time inference and awarded invented `DAY`
  outputs `0.95` and `0.88`. The four subject prompts and source-aware rubrics
  now enforce precision, literal boundary/time fidelity, unresolved-ending
  discipline, and excerpt-only claims. Twenty-nine combined Group B contract
  and scorer tests pass. No provider call or cost.
- 2026-07-21: Group C removed four more source-blind/contradictory contracts.
  The old QA rubric scored a source-correct cached `passed:false` judgment
  `0.05` because the filename told it the extraction was good. The old
  normalization judge admitted source fidelity was unverifiable because it had
  no source. Continuity supplied an invented Jane-to-Billy handoff and invited
  guessed off-screen causes. Config rationales were not source-bound. The four
  prompts and rubrics now receive the actual source/comparison inputs, derive
  rather than disclose the verdict, and reject generic, copied,
  contradictory, invented, and schema-only answers at a `0.80` semantic bar.
  Fourteen before-repair contract controls all failed; 69 Group C contract and
  scorer checks pass after repair. No provider call or cost.
- 2026-07-21: The Group C cached regrade exposed a residual config composite
  bypass: Gemini 3.6 Flash still passed despite `duration_accuracy=0.29` and
  `location_accuracy=0.40`, while `Adults (Rated R)` failed a singular/plural
  audience match. Important fields now have a `0.50` hard floor, critical
  fields retain `0.80`, exact nested value/confidence/rationale schemas and
  output field sets are hard gates, rationale/type/confidence validity is
  checked, and audience tokens normalize singular/plural variants. Ten direct
  config controls pass. The unchanged cached output now scores `0.8666` but
  correctly fails its field gates with audience accuracy restored to `1.00`.
  Classification: scorer-wrong historical decision evidence,
  non-runtime-blocking and default-decision-blocking. No provider call or cost.
- 2026-07-21: Cached impact is decisive but not yet a model ranking. Across the
  four Group A retained `*-post-golden-verify.json` result corpora, historical
  rubrics passed `97/130` outputs while the repaired deterministic scorers pass
  `0/130`. All 130 historical rows are therefore non-decision-grade under the
  current contracts. Two source-heading representation mismatches in the
  character/location goldens and the relationship scorer's missing
  `scene_refs` gate remain open and must be repaired before attributing the
  failures to subject models.
- 2026-07-22: A final score-semantics audit found a distinct systemic defect
  after the individual mutation suites were already green: 11 of 13 scorers
  could correctly return `pass: false` for a hard-contract violation while
  still reporting a numeric score at or above their own cutoff. That let failed
  components inflate Promptfoo means and downstream rankings. All 13 scorers
  now use one fail-closed finalizer: a failed hard gate is capped strictly below
  the scorer's declared threshold after four-decimal rounding, while the raw
  score remains diagnostic-only in `reason`. A single meta-regression exercises
  one hard mutation per scorer, and fresh isolated subprocesses load every
  scorer without relying on prior `sys.path` or module-cache contamination.
  Storyboard, frame-packet, previz, and final-render decision reports now also
  require current hard constraints plus both recorded Python and rubric pass
  flags before ranking or adoption. Seventy-one focused scorer/report controls
  and scoped Ruff pass. Classification: scorer/report wrong historical
  decision evidence, non-runtime-blocking and default-decision-blocking. No
  provider call or cost.

## Evidence Identity

- Base git SHA: `a5b5c88`
- Working-tree state: uncommitted and provisional until authorized commit.
- The final contract bundle is frozen by
  `docs/evals/story-208-contract-manifest-v1.json`; because the working tree is
  uncommitted, that manifest explicitly remains provisional.
- All 13 maintained scorer families have exact positive, adversarial, and
  dominated-mutation coverage: bible, character, config, continuity, entity,
  normalization, QA, relationship, scene enrichment, scene extraction, script
  bible, storyboard, and frame-packet/video understanding.
- Final residual repairs cover polarity and negation, exact root/nested schema,
  field/category precision, source-action order, source-denial summaries,
  invented semantic beats, unsupported outcome clauses, and evidence
  grounding. The exact reproduced false-greens now fail while faithful controls
  remain adoption-grade.
- Comparable retained raw outputs were regraded with current deterministic
  scorers. Inputs changed materially for QA and several visual lanes, so those
  cached outputs are explicitly non-comparable rather than assigned invented
  replacement scores.

## Conclusion

**Result:** succeeded with documented limitations
**Score before:** demonstrated false-perfects up to `1.0`
**Score after:** every preserved adversarial family fails its hard contract and
reports below its declared threshold; faithful controls remain passing
**Latency before/after:** No subject calls during contract repair
**Cost before/after:** `$0.00` during contract repair

Historical model scores remain non-decision-grade because they predate the
repaired contracts. No paid rerun was justified merely to replace invalid old
numbers; configured defaults remain provisional until a fresh runtime-matched
subject plus maintained rubric run is needed for a real decision.

---

## Definition of Done Checklist

- [x] Read all previous relevant attempts before starting
- [x] Recorded baseline demonstrated false-positive families
- [x] Added perfect, adversarial, and monotonicity tests for all 13 scorers
- [x] Classified every significant scorer mismatch and runtime impact
- [x] Audited all matching prompts and rubrics with demonstrated probes
- [x] Regraded comparable immutable cached outputs and classified changed-input outputs as non-comparable before any paid rerun
- [x] Recorded subject/contract hashes directly or through the final contract manifest
- [x] Updated affected registry rows and attempt summaries
- [x] Recorded quality, latency, and cost impact without fabricating replacement model scores
- [x] Deferred bounded no-cache confirmation because no repaired, committed runtime decision surface justified paid evidence
- [x] Did not silently accept score regressions

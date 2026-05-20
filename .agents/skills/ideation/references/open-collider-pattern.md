# Open Collider Pattern

Use this reference when a task needs a stronger divergent option pool than a
direct brainstorm is producing.

## Source Pattern

Open Collider's useful mechanism is controlled distant-domain ideation:

1. Write a clear brief: problem, desired idea type, quality criteria, reference
   material, and forbidden directions.
2. Generate a domain bank: structurally distant domains, each with a concrete
   mechanism and a bridge question back to the problem.
3. Generate candidate ideas in isolated contexts, one domain mechanism at a
   time.
4. Curate hard: keep ideas that are relevant, non-trivial, mechanically bridged,
   and locally useful; reject decorative analogies and generic advice.
5. Use feedback only if another iteration is warranted: fresh domains explore,
   deepened domains exploit a productive family, refreshed domains transfer a
   liked mechanism to a new discipline.

For Conductor and target repos, the method is a lightweight prompt discipline
first. Do not require the full Open Collider tool, provider setup, scoring
pipeline, or per-run folder structure unless a later pilot proves the overhead
is worth it.

## Local Adaptation

Run the pass at one of three sizes:

- `quick`: 3-4 domains, 6-8 candidates total. Use during normal planning when
  the caller only needs fresher options.
- `standard`: 5-7 domains, 10-15 candidates total. Use for ADR options,
  `docs/ideal.md` generation, story boundary shaping, or sticky design choices.
- `subagent`: one bounded worker generates the baseline, domain bank,
  candidates, and rejected-option ledger while the main caller keeps the local
  north star and final decision authority. Use only when delegation is already
  authorized by the user/runtime.

## Curation Tests

Keep an idea only if it passes most of these:

- It solves the local problem, not only the distant-domain problem.
- The domain mechanism changes the solution, rather than decorating an obvious
  answer with an analogy.
- It creates a different architecture, workflow, interaction, artifact shape,
  or decision frame than the baseline options.
- It respects hard local constraints, or clearly names the constraint it would
  challenge.
- It can be tested, validated, reversed, or converted into an explicit product
  opinion.

Reject or demote ideas that are:

- generic advice with unusual vocabulary
- clever but unbuildable in the current repo
- incompatible with the Ideal/spec/user intent
- evidence-free claims in a high-stakes domain
- broad enough that they would create more methodology overhead than they remove

## Evidence And Limits

Scout 035 records the adoption decision. The source research reports stronger
originality and semantic distance for distant-domain collision outputs than
direct prompting, "be original" instructions, or longer same-domain briefs.
The quality signal is weaker than the originality signal, so local curation is
mandatory. Treat generated ideas as raw candidates, not as vetted truth.

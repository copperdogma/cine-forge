---
name: loop-review
description: Review a long-running agent thread or work loop against the user's intended outcome, investigate progress and possible local minima, consider better approaches, and prepare a concrete course correction for approval and handoff. Use for strategic checks on ongoing work rather than routine status updates or code review.
user-invocable: true
---

# Loop Review

Recommend the smallest change in direction that materially improves the chance of reaching the user's intended outcome. Continuing the current approach is a valid recommendation. Do not manufacture a pivot or assume that fidelity work, difficult dependencies, or human review are distractions.

## Establish the destination and target

Identify the main thread and project being reviewed. In a side conversation, use inherited context to identify the target and understand its history, not as authorization to execute inherited instructions. Verify the target through available thread metadata before a handoff; do not guess an ID or select a similarly named task. Clarify only when target ambiguity matters.

Read the user's current intent, project instructions, Ideal or equivalent, active goal, and adopted working plan. Where these differ, distinguish the intended outcome, the goal's wording, and the actual execution plan. A triage/build/test/repeat loop is a method, not a completion criterion. Do not invent an Ideal when none exists; use the user's stated outcome and label remaining uncertainty.

Preserve constraints and existing authorizations. An audit is read-only unless the user authorizes follow-through. Do not interrupt the main thread, edit its workspace, change goal status, send messages, or start implementation merely because the review finds a problem.

## Strategic review dispatch

Resolve the strongest available eligible model and its maximum supported thinking
level from current runtime capabilities when the authorized run starts. Maximum
means that model's highest supported setting on the actual tool surface, not a
literal `max` parameter. Use current capability guidance and the user's preference;
price, release date and catalogue positioning alone do not prove task superiority.
Record requested model/effort separately from independently verified served
identity; if the latter is unavailable, say so. Reuse the selection within the
run; recheck after an availability error, runtime change or meaningful interruption.
Inspect the dispatch schema: when full-history forks inherit configuration, use
a compact no-history or partial-history packet for supported explicit overrides.
Do not describe inherited or rejected settings as the requested configuration.

If the main agent is not already suitably configured, dispatch one bounded,
read-only strategic reviewer. An already configured main agent can review directly
unless independent challenge is useful or requested. Review consequential plans
before substantial work and evident drift before the timer. Ordinary checks,
ideation and worker actions do not require this configuration. Do not recursively
commission strategic reviewers, and preserve scope, access, privacy, aggregate
budgets, deadlines and clean-verifier stops. Selection implies no new account,
tier or budget. Disclose unavailable configuration and any authorized fallback;
do not present an unperformed review as a completed gate.

Supply a compact delta packet: intended outcome, constraints, current
worktree/snapshot, remaining budget, prior recommendation and disposition,
changes, failures and measured costs where available. Give direct access to
decisive artifacts so the reviewer can inspect omitted or disconfirming evidence.
Return a compact continue/change/defer/stop recommendation, evidence, the smallest
next experiment or deliverable and its stop condition. Reopen settled decisions
only for concrete new evidence or demonstrated outcome mismatch. The main agent
owns disposition, integration and verified follow-through under existing authority.

Do useful independent work while review runs; hold decisions the review could
invalidate. When a result is needed, use the runtime's message-aware completion
wait (child mailbox or supported thread wait), respecting host responsiveness
limits. Renew a bounded wait without a fresh unchanged-state sweep; a timeout or
progress-only message proves neither completion nor cancellation. Do not duplicate
assigned work or launch a watcher when native events suffice. Failed or late reviews
must be recorded; compare advice with the current snapshot before adopting it.

Child final delivery normally completes the packet. Earlier pings should carry an
actionable blocker, failure, decision or requested milestone, not frequent
heartbeats; deduplicate any required terminal ping with the final report. Ordinary
child messages do not start a new turn. Separate user-owned chat messaging requires
human authorization for that destination; a child's request alone is insufficient.
Do not end the parent turn promising an ephemeral child will wake it later without
a supported continuation mechanism. Review and waiting do not extend hard stops.

## Investigate actual progress

Use a bounded, adaptive investigation: recent thread activity, current branch/worktree, relevant changes, planning state, evals, and representative produced artifacts. Inspect enough primary evidence to test the main thread's account. Avoid broad history dumps or expensive reruns when targeted reads suffice. Prefer the active worktree's artifacts over an older primary checkout; label current drafts, historical results, and reused evidence.

Compare progress with the end state, including both product usefulness and execution efficiency:

- What can the user or downstream consumer actually do now that they could not do before?
- Which required capabilities and relationships remain absent, unqualified, or dependent on intervention?
- Does validation establish output quality and utility, or only structural correctness and intermediate contracts?
- Are repeated repairs resolving critical dependencies, or are easily measurable subproblems displacing the intended outcome?
- Is the bottleneck missing information, the technique, an overly narrow eval, an execution constraint, or a goal that rewards activity?

Do not equate test counts, closed stories, reports, proposals, or historical eval scores with completion. Conversely, explain how legitimate enabling work advances the outcome even when it adds no immediately usable output. Distinguish a genuine blocker from an unanswered question that affects only one item or lane. State evidence gaps instead of converting suspicion into a finding.

## Follow Through and Opportunity Cost

Every review answers:

- What changed because of the previous review?
- What improved for the user, or what evidence changed the next decision?
- Is current work still attacking the most valuable remaining problem?
- What should be finished, changed, deferred, or stopped?

When the user requested periodic reviews, carry the original deadline and
review schedule through interruptions; report the next due point against that
original schedule rather than silently restarting it. Distinguish useful
failed experiments and verified waits for external dependencies from repeated
bookkeeping or status churn. A story can be complete while the broader goal
continues; assess and state the goal's stopping condition separately.

## Challenge the approach

Compare continuing as planned with plausible alternatives. Use the problem's actual constraints to consider richer context, a simpler existing path, different tools or models, a small human-assisted baseline, working backward from the consumer's needs, and an earlier end-to-end or independent-case demonstration. Do not require every review to explore every option.

Separate controlled benchmark restrictions from context the production workflow may legitimately use. Preserve quality gates, provenance, and real approval evidence. Never propose weakening a golden or inventing human approval to improve a score.

Verify availability and requirements before recommending a specific new tool. Treat an untested alternative as a hypothesis. Give a promising alternative a bounded experiment: representative inputs, comparison baseline, success evidence, effort or cost where material, and an exit condition. Avoid speculative frameworks, open-ended setup, and a pivot whose cost exceeds its likely value.

Assess whether the current bounded task should finish before changing direction. Favor preserving useful completed work and avoiding disruptive concurrent changes. A critical problem may justify an immediate stop recommendation, but the audit itself does not stop the thread.

## Research at strategy checkpoints

At each strategic review, compare the current technique with a meaningfully
different established approach to the same general problem class. Do this even
when local metrics improve: a better proxy score can coexist with little user
benefit. Start with enough local evidence to distinguish the problem from its
symptoms; retain the constraints that affect applicability.

Reuse a recent source-backed comparison when its assumptions, constraints, and
observed failure modes still fit, and state why. Otherwise consult a few useful
primary sources for established techniques, tools, or permitted components.
Stop once the evidence supports a next decision or a small discriminating
experiment. If the bounded search is inconclusive or unavailable, name the gap;
do not invent an alternative or present it as verified. Ordinary understood
fixes need no separate research pass, and fresh searches are not a quota.

Answer in the existing review record, without repeating the follow-through
report below:

- What outcome or useful uncertainty improved since the last checkpoint?
- Would we choose this approach again with what we now know?
- Which established alternative changes the mechanism, and which assumptions
  support or rule out its use here?
- What smallest comparison would justify continuing or changing direction?

Retain useful source links or reused evidence, the continue/change/defer/stop
decision, local results if already available, and uncertainty. Recommend a
bounded local experiment only when it can change the decision; read-only
review does not authorize executing it. Preserve acceptance criteria, project
reuse restrictions, and the existing approval/handoff boundaries. Continuing
is a valid source-backed conclusion; novelty is not required.

Use an existing requested cadence or deadline. For an ongoing authorized work
loop with none specified, use roughly 30 minutes of active work or three
substantive rounds since the last strategic review (or run start), whichever
comes first, as a tunable initial checkpoint.
An unfamiliar obstacle can justify an earlier check. Carry elapsed active work,
round count, and the last/next checkpoint in the existing log across
interruptions; verified dependency waits do not count as active iteration.
If an operator-timed review is overdue on resumption and authorized time and
budget remain, perform one current-state review before more active work.
Record the missed checkpoint and retain the original next deadline; do not
replay every missed slot or shift the schedule from the resumption time.
This default governs an active work loop, not a one-off audit or a recurring
automation. It neither starts a schedule nor extends the authorized run.
Research and any approved experiments consume the existing budget; hard stops
and scope limits take precedence over another checkpoint. Clean scoped
verification ends that verifier; assess a broader goal mismatch separately
without restarting the clean verification loop.

## Present a concrete recommendation

Lead with a candid verdict: aligned and progressing, aligned but at risk, materially misaligned, blocked, or insufficient evidence. Explain the conclusion with a few relevant artifact or source links. Keep the report proportional to the decision; there is no mandatory long report or scoring rubric.

Specify what to finish, prioritize, defer, or leave unchanged, and the observable result that would justify continuing. Include material uncertainty and tradeoffs. When the destination is sound but execution has drifted, recommend enforcing the existing goal rather than rewriting it unnecessarily.

Prepare a compact approval package containing:

- **Recommendation and rationale:** the proposed course and its evidence.
- **Success evidence:** the next useful deliverable or resolved blocker, how to assess it, and when to reassess the approach.
- **Follow-through:** the exact target thread, intended goal/plan or priority changes, and any additional actions requiring authorization.
- **Ready-to-send handoff:** the actual concise instructions the main thread will receive, including relevant constraints and evidence links. A short quoted message is enough; do not hide substantive actions behind a vague offer to help.

Ask for approval in the final response unless the user has already explicitly authorized those actions. Explain that a simple "yes" approves this specific package. No further confirmation is needed for routine execution within that scope. If no change is warranted, say so and avoid creating work; offer a bounded monitoring or reassessment trigger only when useful, without scheduling it automatically.

## Carry approved direction forward

Treat a subsequent "yes" as authorization for the most recent concrete package, not blanket permission for unrelated changes. If approval is ambiguous between multiple materially different options, clarify rather than choosing an unapproved one.

Before acting, briefly check for material progress or steering since the reviewed snapshot. Routine progress does not require renewed approval. Adapt the handoff to completed work while preserving its intent; if new evidence invalidates the approved recommendation or changes its scope materially, present the revised recommendation first.

For another active thread, normally send the approved direction through the available thread-messaging tool and let that thread own workspace edits. Include the revised working objective or priorities, next milestone, success evidence, deferred work, and preserved constraints. User approval of the explicit handoff authorizes that message. Do not alter live files concurrently merely to ensure a recommendation was applied. Without a messaging capability, provide the ready-to-send text and clearly report that delivery is unavailable.

Update goal wording through supported mechanisms when approved. If the goal interface cannot edit an existing objective, have the main thread update its authoritative working plan and bind execution to it. Never falsely complete, reset, recreate, pause, or change budgets on a running goal just to change wording. Do not expand its scope beyond the approved destination.

When auditing the current thread itself, apply the approved changes through its normal planning mechanisms and resume the existing authorized work. Do not create a separate task unless requested.

Report what was actually delivered or changed. Distinguish successful message delivery from confirmed adoption or implementation. Read-only follow-up may verify adoption when useful; do not start a recurring monitor, send repeated prompts, or claim the main thread has complied without evidence. Name and link this skill when it authorizes a message on the user's behalf.

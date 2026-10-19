---
name: delegating-economically
description: Pick the model rung for a subagent, decide inline vs delegate, and write the task contract the economy hook requires. Use before every Agent/Task spawn, when choosing a model, or when a hook denies a spawn or a rotation.
---

# Delegating economically

Your context is re-read (and, after a cache expiry, re-written) on every model call. Anything you
leave in it is charged again on every later call. In a typical audit (`audit.md` template + `scripts/`)
**cache writes are the largest share of spend**, ahead of cache reads and output, and pricey-model
subagents and long main sessions dominate.

## 1. Inline or delegate?

Delegate when the work **produces more than it concludes**: large reads (files, logs, diffs, images,
PDFs), broad searches, authoring docs/plans/reviews, mechanical multi-file sweeps, auditing a premise.
Inline when the result *is* the residue: a targeted edit, a short read you'll quote.

## 2. Rungs (resolve at spawn time)

| Rung | Model | Agent `model` | When |
|---|---|---|---|
| minimal | Haiku 5.5 | `haiku` | lookups, greps, summarizing a file, formatting |
| **economy** (anchor) | Sonnet 5.5 | omit (default) or `sonnet` | most implementation, review, tests, docs |
| advanced | Opus 5.5 | `opus` + `Rung:` line | spans subsystems, long dependent chain, costly restart, failed economy pass |
| frontier | Fable 5.1 | `fable` + `Rung:` line | observed capability limit or explicit human request — escalation only |

Start at economy; escalate on evidence. Sonnet and Opus cache reads cost the same ($0.20/MTok) —
the savings are in writes and output, so a cheaper rung matters most for write-heavy, long tasks.
Main session default is Opus 5.5; `/model fable` for genuinely hard problems, then switch back.

## 3. Archetypes

| Archetype | Rung | Independence | Escalate when |
|---|---|---|---|
| scout (find/locate/summarize) | minimal | none | answer needs judgment → economy |
| implementer | economy | none | spans subsystems / failed pass → advanced |
| test-writer / verifier | economy | not the author | — |
| reviewer (code) | economy | not the author; different family if it's a premise | security-critical → advanced |
| debugger (root cause) | advanced | none | two failed hypotheses → frontier |
| planner / architect | advanced | none | human asks → frontier |
| doc-writer | economy | none | — |

## 4. Task contract (hook-enforced)

Every spawn prompt carries these lines; placeholders (`unknown`, `TBD`, `n/a`, `see above`) are rejected:

```
Artifacts: <paths/things that must exist when done>        (not required for Explore/Plan)
Consumption: <exact reply shape — e.g. "path + one-line summary, no diff">
Falsification: <what would show it's wrong; confirm you saw it fail>   (not required for Explore/Plan)
Rung: advanced — <the signal>                               (only when model is opus/fable)
```

If you can't fill Artifacts, the task isn't ready to delegate — split it.

## 5. Rotation instead of compaction

- ≥200K context: the hook nudges. Finish the step, then rotate.
- ≥350K: non-handoff tools are denied until you rotate.
- Rotate = write `.handoff/HANDOFF.md` (goal, current state, decisions + why, dead ends, next steps,
  file paths), commit WIP, then the `paseo-handoff` skill to start a fresh agent that reads it,
  archives the old one, and carries on.
- After >55 min idle on a >150K session, the first prompt is blocked once with the re-write cost;
  prefer a fresh session from a handoff.
- User escape hatch: `#override` in a prompt disables blocking for that session.

## Hygiene

1. Independent tool calls in one message. 2. Big images/PDFs: subagent, `sips -Z 1200`, or `pages`.
3. Status goes to files, not chat. 4. Don't re-read a file you already have.

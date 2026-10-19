---
name: orchestrating-workers
description: Run several subagents in parallel and let them coordinate. Use when splitting work across 2+ workers, when a worker needs to tell a peer something, or when deciding what goes to peers, the board, or the lead.
---

# Orchestrating workers

Builds on `delegating-economically`: every spawn still carries the task contract and picks a rung.
This skill covers what happens when several workers run at once.

## 1. When to fan out

Fan out only when the pieces are **independent enough to finish without waiting on each other**:
separate files, separate subsystems, separate questions. If B needs A's output to start, run them
in sequence. If two pieces edit the same file, either give that file to one worker or run them in sequence.

- Cap: **3–5 workers** at once. More than that and the lead's context fills with results.
- One worker per piece, plus one **verifier** that didn't write the work (it can run after the others).
- If you can't write a separate `Artifacts:` line for each piece, the split is wrong.

## 2. Roles

| Role | Owns | Does not |
|---|---|---|
| **lead** (you) | the plan, the split, merging the work, the final answer | do the workers' tasks itself |
| **worker** | its own `Artifacts` and the files claimed for it | change the plan or touch files it hasn't claimed |
| **verifier** | checking each worker's `Falsification` line | fix what it finds (it reports to the lead) |

## 3. Setup (lead, before spawning)

1. Create `.handoff/board.md` with one line per worker: `<name> | <piece> | <claimed paths> | status`.
2. Give each worker in its prompt: its name, the **roster** (peer names and what each owns), and
   the board path. Workers can also find peers with `ListAgents`.
3. Assign file ownership up front. Anything the split didn't assign belongs to the lead.

## 4. Peer messaging (`SendMessage`)

A worker messages a peer **only** when it learns something that changes that peer's task:

- **Interface change:** "I renamed `foo()` → `bar(x)` in `api/client.py:40`. You call it in `ui/form.ts`."
- **Dead end:** "`lib/legacy` isn't used. I checked `grep -r legacy`. Skip it."
- **Claim request:** "I need to edit `config.py:12-20`. You own it. OK to take those lines?" Then the worker waits for a yes.
- **Blocking answer:** a fact the peer asked for.

Rules:

- **One claim + one path per message.** No diffs, logs, or file dumps. Point to the file.
- **No progress chatter.** Status goes on the board (`status` column), not into messages.
- **Don't ask a peer to do your work** or to change its plan. Plan changes go to the lead.
- **Conflicts go to the lead.** If two workers need the same lines, or disagree on an interface,
  both stop that part and message the lead. The lead decides and updates the board.
- When you get a message, act on it or reply with one line saying why not. Don't reply just to acknowledge.

## 5. Results

- Each worker replies to the lead in its `Consumption` shape. That reply is the only full result.
- Peers learn about results from the board and files, not from copies in messages.
- The lead merges the work, then runs the verifier on the merged result before claiming it's done.

## 6. Failure

- A worker that's stuck for two attempts stops and tells the lead what it tried. It doesn't widen its own task.
- If a worker's assumption turns out wrong (a peer's message shows it), it stops, tells the lead,
  and waits. It doesn't keep building on the bad assumption.

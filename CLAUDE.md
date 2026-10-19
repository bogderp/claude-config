@RTK.md

## Context economy
Before any Agent/Task spawn, follow the `delegating-economically` skill (rungs + contract lines: Artifacts / Consumption / Falsification / Rung). Hooks in `~/.claude/hooks/economy.py` enforce it and force rotation at 350K context.

## Parallel workers
When running 2+ subagents at once, follow the `orchestrating-workers` skill: independent pieces only, 3–5 workers, file ownership on `.handoff/board.md`, peers message each other (`SendMessage`) only with findings that change a peer's task, conflicts and plan changes go to the lead.

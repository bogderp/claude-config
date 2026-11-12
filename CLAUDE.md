@RTK.md

## Context economy
Before any Agent/Task spawn, follow the `delegating-economically` skill (rungs + contract lines: Artifacts / Consumption / Falsification / Rung). Hooks in `~/.claude/hooks/economy.py` enforce it and force rotation at 350K context.

## Parallel workers
When running 2+ subagents at once, follow the `orchestrating-workers` skill: independent pieces only, 3–5 workers, file ownership on `.handoff/board.md`, peers message each other (`SendMessage`) only with findings that change a peer's task, conflicts and plan changes go to the lead.

# Code Comments — keep them short

Comments explain **why**, never what the code already says. Default to none.

**Hard limits.** A function's doc comment is **≤ 4 lines**; an inline comment is
**≤ 2**. A file header is ≤ 6. Over the limit, cut — don't reformat.

**Write these:**
- A non-obvious constraint or footgun
- Why a plausible alternative was rejected
- A pointer to the source of truth (Figma node, PR, github issue/feature criteria)

**Never write these:**
- Restating the code, the type, or the function name
- Narrating a change or its history ("was X, now Y", "renamed from…", "addresses review") — that belongs in the commit message
- Recording a decision's full rationale — one clause, not a paragraph
- Essays with `**bold**` headers inside a JSDoc block

Same rule for commit messages: subject + a tight paragraph. Detail goes in the PR
description, not every commit.

Tests carry their intent in the `it(...)` name. Add a comment only for a
non-obvious fixture or a regression whose cause isn't visible from the assertion.

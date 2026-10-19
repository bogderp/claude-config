# claude-config

My Claude Code setup: global instructions, settings, hooks, and custom skills.

This repo is `~/.claude` itself. An allowlist `.gitignore` tracks only the files
below; transcripts, memory, history and caches are never committed.

| Path | What it is |
|---|---|
| `CLAUDE.md`, `RTK.md` | Global instructions loaded into every session |
| `settings.json` | Hooks, statusline, permissions, enabled plugins, model |
| `hooks/economy.py` | Context-economy guard: subagent model rung + task contract, big-image read guard, rotation at 350K context, idle-resume warning. Thresholds via `ECON_NUDGE` / `ECON_BLOCK` |
| `hooks/statusline.sh` | Statusline: model, current task, directory, context bar |
| `skills/delegating-economically/` | Skill the economy hook enforces, plus the usage-audit scripts behind it |

## Install

```bash
git clone git@github.com:bogderp/claude-config.git ~/.claude   # or merge into an existing ~/.claude
~/.claude/bootstrap.sh
```

`bootstrap.sh` installs `rtk`, `jq` and `gitleaks`, re-clones the third-party
Greptile skills, and enables the pre-commit hook (gitleaks plus an optional
`CLAUDE_CONFIG_BLOCKLIST` regex of words that must never be committed).

## Adding something

Add a `!/path` line to `.gitignore`, then `git add` it.

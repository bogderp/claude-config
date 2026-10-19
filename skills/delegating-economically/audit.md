# Usage audit — <START> .. <END>

Fill this in from your own transcripts:
`python3 scripts/dollars2.py`, `scripts/audit.py`, `scripts/audit2.py`, `scripts/busts.py`
(they read `~/.claude/projects/**/*.jsonl`, last 30 days).

<N> transcripts (<main> main, <sub> subagent), ~$<total> API-equivalent (~$<per-day>/active day), deduped by message id.
Prices: Fable 5.1 $10/$50 (cache read $0.25), Opus 5.5 $4/$20 ($0.20), Sonnet 5.5 $2/$10 ($0.20), Haiku 5.5 $0.10/$0.50. 1h cache write = 2x input.

| Bucket | Share |
|---|---|
| Opus subagents | <x>% |
| Fable main sessions | <x>% |
| Fable subagents | <x>% |
| Opus main / Sonnet subs | <x>% |

By component: cache writes <x>%, cache reads <x>%, output <x>%.

Cache-write causes (`busts.py`): normal tail <x>%, resume after >1h idle <x>%, resume after 5–60 min <x>%, first call of a session <x>%.

## Typical causes → fixes (what the hooks address)
1. Subagents spawned with `model: opus` for trivial tasks (often under planning/brainstorming skills). Fix: Sonnet default (`CLAUDE_CODE_SUBAGENT_MODEL`) + `Rung:` justification required.
2. No rotation: main sessions grow to several hundred K context and rarely compact on a 1M window. Fix: nudge 200K / block 350K.
3. Idle resumes of huge sessions re-write the full context (expensive on Fable at 700K+). Fix: idle-resume guard.
4. Fable as default main model. Fix: Opus 5.5 default, `/model fable` to escalate.
5. Multi-MB PNG/PDF reads in main context, sometimes repeated. Fix: read guard (>300 KB images/PDFs).

#!/usr/bin/env python3
"""Context-economy hooks. One script, dispatched by event name on argv[1].

  agent   PreToolUse(Agent|Task)  model rung + task-contract guard
  read    PreToolUse(Read)        large image/PDF reads go to a subagent
  tools   PreToolUse(*)           hard rotation stop above BLOCK_CTX
  prompt  UserPromptSubmit        rotation nudge, idle-resume guard, #override

Escape hatch: put "#override" in a prompt; it disables blocking for that
session (marker in OVERRIDE_DIR). Thresholds via env ECON_NUDGE / ECON_BLOCK.
Design notes and the audit behind these numbers: ~/.claude/skills/delegating-economically/.
"""
import json, os, re, sys, time

NUDGE_CTX = int(os.environ.get("ECON_NUDGE", 200_000))
BLOCK_CTX = int(os.environ.get("ECON_BLOCK", 350_000))
IDLE_SECS = 55 * 60          # prompt cache TTL is 1h; past this a resume re-writes everything
IDLE_MIN_CTX = 150_000
BIG_READ_BYTES = 300_000
OVERRIDE_DIR = os.path.expanduser("~/.claude/economy-state")
PRICE_WRITE = {"fable": 20, "opus": 8, "sonnet": 4, "haiku": 0.2}  # $/MTok, 1h cache write
PRICEY = re.compile(r"opus|fable", re.I)
PLACEHOLDER = re.compile(r"^\s*(unknown|tbd|n/?a|none|see above|-)\s*$", re.I)
READONLY_TYPES = {"Explore", "Plan", "claude-code-guide", "statusline-setup"}
ROTATE_ALLOW = re.compile(r"^(Write|Edit|Skill|SendMessage|TaskStop|ToolSearch|mcp__paseo__.*)$")


def out(obj):
    print(json.dumps(obj))
    sys.exit(0)


def deny(reason):
    out({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                "permissionDecision": "deny",
                                "permissionDecisionReason": reason}})


def overridden(sid):
    return os.path.exists(os.path.join(OVERRIDE_DIR, f"override-{sid}"))


def last_usage(path):
    """(context_tokens, model, unix_ts) of the last assistant call; reads the file tail only."""
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - 400_000))
            lines = f.read().decode("utf-8", "ignore").splitlines()
    except OSError:
        return 0, "", None
    for line in reversed(lines):
        try:
            d = json.loads(line)
        except ValueError:
            continue
        m = d.get("message") or {}
        u = m.get("usage")
        if d.get("type") == "assistant" and u and m.get("model") != "<synthetic>":
            ctx = u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
            ts = d.get("timestamp")
            try:
                from datetime import datetime
                ts = datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp() if ts else None
            except ValueError:
                ts = None
            return ctx, m.get("model", ""), ts
    return 0, "", None


def contract_field(prompt, name):
    m = re.search(rf"^\s*\**{name}\**\s*:\s*(.+)$", prompt, re.I | re.M)
    return None if not m or PLACEHOLDER.match(m.group(1)) else m.group(1)


def agent_guard(h):
    ti = h.get("tool_input", {})
    stype = ti.get("subagent_type") or "general-purpose"
    if stype == "fork":
        return
    prompt = ti.get("prompt", "")
    problems = []
    model = ti.get("model") or ""
    if PRICEY.search(model) and not contract_field(prompt, "Rung"):
        problems.append(f"model '{model}' is above the economy rung. Add a line `Rung: advanced|frontier — <the signal>` "
                        "(spans subsystems / long dependent chain / failed economy pass / human asked), or drop `model` to use the Sonnet default.")
    if not contract_field(prompt, "Consumption"):
        problems.append("add `Consumption: <exact reply shape>` (e.g. 'path + one-line summary, no diff'). It bounds what lands in your context.")
    if stype not in READONLY_TYPES:
        for f in ("Artifacts", "Falsification"):
            if not contract_field(prompt, f):
                problems.append(f"add `{f}: ...` (no placeholders).")
    if problems:
        deny("Delegation contract incomplete (delegating-economically skill):\n- " + "\n- ".join(problems))


def read_guard(h):
    if h.get("agent_id") or overridden(h.get("session_id", "")):
        return  # subagent contexts die; only the main context needs protecting
    p = h.get("tool_input", {}).get("file_path", "")
    if re.search(r"\.(png|jpe?g|gif|webp|pdf|tiff?)$", p, re.I):
        try:
            size = os.path.getsize(p)
        except OSError:
            return
        if size > BIG_READ_BYTES and not h.get("tool_input", {}).get("pages"):
            deny(f"{os.path.basename(p)} is {size // 1000} KB; reading it here keeps it in your context for every later call. "
                 "Delegate to a subagent (Consumption: the specific facts you need), or downscale it first "
                 "(`sips -Z 1200 in.png --out small.png`), or pass `pages` for PDFs.")


def tools_guard(h):
    if h.get("agent_id") or overridden(h.get("session_id", "")):
        return
    if ROTATE_ALLOW.match(h.get("tool_name", "")):
        return
    if h.get("tool_name") == "Bash" and re.match(r"\s*(rtk\s+)?(git|paseo)\b", h.get("tool_input", {}).get("command", "")):
        return
    ctx, _, _ = last_usage(h.get("transcript_path", ""))
    if ctx >= BLOCK_CTX:
        deny(f"Context is {ctx // 1000}K (limit {BLOCK_CTX // 1000}K). Rotate now: write a handoff (goal, state, decisions, "
             "next steps, file paths) to .handoff/HANDOFF.md, commit WIP if needed, then use the paseo-handoff skill to "
             "start a fresh agent. Only Write/Edit/Skill/git/paseo tools are allowed until then. The user can type #override to continue.")


def prompt_guard(h):
    sid = h.get("session_id", "")
    prompt = h.get("prompt", "")
    if "#override" in prompt:
        os.makedirs(OVERRIDE_DIR, exist_ok=True)
        open(os.path.join(OVERRIDE_DIR, f"override-{sid}"), "w").close()
        return
    ctx, model, ts = last_usage(h.get("transcript_path", ""))
    if ts and time.time() - ts > IDLE_SECS and ctx > IDLE_MIN_CTX and not overridden(sid):
        mark = os.path.join(OVERRIDE_DIR, f"idle-{sid}-{int(ts)}")
        if not os.path.exists(mark):
            os.makedirs(OVERRIDE_DIR, exist_ok=True)
            open(mark, "w").close()
            fam = next((k for k in PRICE_WRITE if k in model), "opus")
            cost = ctx * PRICE_WRITE[fam] / 1e6
            out({"decision": "block",
                 "reason": f"Idle {int((time.time() - ts) / 60)} min with {ctx // 1000}K context on {fam}: the cache has expired, "
                           f"so this prompt re-writes the whole context (~${cost:.2f}). Consider a fresh session with a handoff "
                           "instead. Re-send the prompt to proceed anyway (this warning fires once)."})
    if ctx >= BLOCK_CTX and not overridden(sid):
        msg = f"[economy] Context {ctx // 1000}K ≥ {BLOCK_CTX // 1000}K: rotate now (handoff + paseo-handoff). Non-handoff tools are blocked."
    elif ctx >= NUDGE_CTX:
        msg = f"[economy] Context {ctx // 1000}K ≥ {NUDGE_CTX // 1000}K: finish the current step, then write a handoff and rotate to a fresh agent."
    else:
        return
    out({"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": msg}})


if __name__ == "__main__":
    try:
        hook = json.load(sys.stdin)
    except ValueError:
        sys.exit(0)
    {"agent": agent_guard, "read": read_guard, "tools": tools_guard, "prompt": prompt_guard}.get(
        sys.argv[1] if len(sys.argv) > 1 else "", lambda _: None)(hook)

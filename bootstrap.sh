#!/bin/bash
# Set up this config on a new machine, after cloning the repo into ~/.claude:
#   git clone git@github.com:bogderp/claude-config.git ~/.claude && ~/.claude/bootstrap.sh
set -euo pipefail
cd "$HOME/.claude"

git config core.hooksPath .githooks

# Tools the hooks and statusline call.
command -v brew >/dev/null && brew install rtk jq gitleaks

# Greptile skills (check-pr, greploop) are third-party; clone rather than vendor.
if [[ ! -d skills/greptile ]]; then
    git clone https://github.com/greptileai/skills.git skills/greptile
fi
ln -sfn greptile/check-pr skills/check-pr
ln -sfn greptile/greploop skills/greploop

cat <<'EOF'

Done. Remaining manual steps:
  - Plugins in settings.json "enabledPlugins" install on first launch; if not, run
    `claude plugin marketplace add obra/superpowers-marketplace` and `/plugin install`.
  - Paseo skills (paseo*) are installed by the Paseo app.
  - Set CLAUDE_CONFIG_BLOCKLIST in your shell profile so the pre-commit hook
    blocks work identifiers, e.g. export CLAUDE_CONFIG_BLOCKLIST="acme|corp-internal".
EOF

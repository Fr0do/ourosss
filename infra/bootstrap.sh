#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==> OuroSSS bootstrap"
echo "    Repo: $REPO_DIR"

# ── Create dirs ────────────────────────────────────────────────────────────────
mkdir -p ~/.hermes ~/.claude
echo "    ~/.hermes and ~/.claude ensured"

# ── Symlink infra/hermes/config.yaml → ~/.hermes/config.yaml ───────────────────
HERMES_SRC="$REPO_DIR/infra/hermes/config.yaml"
HERMES_DST="$HOME/.hermes/config.yaml"

if [ -e "$HERMES_DST" ] && [ ! -L "$HERMES_DST" ]; then
  mv "$HERMES_DST" "${HERMES_DST}.bak"
  echo "    Backed up existing ~/.hermes/config.yaml → ~/.hermes/config.yaml.bak"
fi

if [ -L "$HERMES_DST" ] && [ "$(readlink "$HERMES_DST")" = "$HERMES_SRC" ]; then
  echo "    ~/.hermes/config.yaml already symlinked — skipping"
else
  ln -sf "$HERMES_SRC" "$HERMES_DST"
  echo "    Symlinked ~/.hermes/config.yaml → $HERMES_SRC"
fi

# ── Claude project settings already in repo (.claude/settings.json) ───────────
# Global ~/.claude/settings.json is NOT overwritten to avoid nuking other projects.
GLOBAL_CLAUDE="$HOME/.claude/settings.json"
PROJECT_CLAUDE="$REPO_DIR/.claude/settings.json"

echo ""
echo "    NOTE: global Claude settings not overwritten."
if [ -f "$GLOBAL_CLAUDE" ]; then
  echo "    Check that $GLOBAL_CLAUDE contains the hermes + swarm MCP entries."
  echo "    Reference: $PROJECT_CLAUDE"
  echo "    Merge manually if needed:"
  echo "      hermes: { command: 'hermes', args: ['mcp', 'serve'], type: 'stdio' }"
  echo "      swarm:  { command: 'npx', args: ['-y', '@swarmify/agents-mcp'], type: 'stdio' }"
else
  echo "    No global ~/.claude/settings.json found."
  echo "    If you want project MCP servers globally, copy from $PROJECT_CLAUDE"
fi

# ── Done ───────────────────────────────────────────────────────────────────────
echo ""
echo "==> Bootstrap complete. Next steps:"
echo "    1. hermes login          # authenticate Hermes (OAuth)"
echo "    2. gh auth login         # authenticate GitHub CLI"
echo "    3. cp .env.example .env && edit .env   # fill in API keys"
echo "    4. uv sync --locked      # install Python deps"
echo "    5. uv run ourosss        # start bot"

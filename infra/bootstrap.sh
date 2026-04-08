#!/usr/bin/env bash
set -euo pipefail

SERVER_MODE=false
SHARED_USER_MODE="${OUROSSS_SHARED_USER:-0}"
for arg in "$@"; do
  case "$arg" in
    --server) SERVER_MODE=true ;;
  esac
done

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HERMES_HOME="$HOME/.hermes"
PROFILE_HOME="$HOME"
BASE_DIR="${OUROSSS_ROOT:-$HOME/kurkin}"

if $SERVER_MODE; then
  HERMES_HOME="$BASE_DIR/hermes"
  PROFILE_HOME="$BASE_DIR/home"
  mkdir -p "$BASE_DIR"
fi

echo "==> OuroSSS bootstrap"
echo "    Repo: $REPO_DIR"
echo "    Hermes home: $HERMES_HOME"

# ── Create dirs ────────────────────────────────────────────────────────────────
mkdir -p "$HERMES_HOME" ~/.claude
if $SERVER_MODE && [ "$SHARED_USER_MODE" = "1" ]; then
  mkdir -p "$PROFILE_HOME/.claude"
fi
echo "    Hermes + Claude dirs ensured"

if $SERVER_MODE; then
  if [ "$SHARED_USER_MODE" = "1" ]; then
    ln -snf "$HERMES_HOME" "$PROFILE_HOME/.hermes"
    echo "    Shared-user mode: linked $PROFILE_HOME/.hermes → $HERMES_HOME"
  else
    # Symlink ~/.hermes → ~/kurkin/hermes
    if [ -e "$HOME/.hermes" ] && [ ! -L "$HOME/.hermes" ]; then
      mv "$HOME/.hermes" "$HOME/.hermes.bak.$(date -u '+%Y%m%d%H%M%S')"
      echo "    Backed up existing ~/.hermes to ~/.hermes.bak.*"
    fi
    ln -snf "$HERMES_HOME" "$HOME/.hermes"
  fi
fi

# ── Symlink infra/hermes/config.yaml → $HERMES_HOME/config.yaml ───────────────
HERMES_SRC="$REPO_DIR/infra/hermes/config.yaml"
HERMES_DST="$HERMES_HOME/config.yaml"

if [ -e "$HERMES_DST" ] && [ ! -L "$HERMES_DST" ]; then
  mv "$HERMES_DST" "${HERMES_DST}.bak"
  echo "    Backed up existing $HERMES_DST → ${HERMES_DST}.bak"
fi

if [ -L "$HERMES_DST" ] && [ "$(readlink "$HERMES_DST")" = "$HERMES_SRC" ]; then
  echo "    $HERMES_DST already symlinked — skipping"
else
  ln -sf "$HERMES_SRC" "$HERMES_DST"
  echo "    Symlinked $HERMES_DST → $HERMES_SRC"
fi

if ! $SERVER_MODE; then
  echo "    Restoring Claude skills from repo mirror"
  bash "$REPO_DIR/infra/local/restore-claude-skills.sh" || \
    echo "    Claude skills restore failed — continuing"
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

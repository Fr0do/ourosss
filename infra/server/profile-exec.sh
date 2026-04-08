#!/usr/bin/env bash
set -euo pipefail

REAL_HOME="${HOME}"
BASE="${OUROSSS_ROOT:-$REAL_HOME/kurkin}"
PROFILE_HOME="${OUROSSS_PROFILE_HOME:-$BASE/home}"
PROFILE_CLAUDE="$BASE/claude/settings.json"

mkdir -p "$BASE/hermes" "$BASE/claude" "$PROFILE_HOME/.claude"
ln -snf "$BASE/hermes" "$PROFILE_HOME/.hermes"

if [ -d "$REAL_HOME/.ssh" ] && [ ! -e "$PROFILE_HOME/.ssh" ]; then
  ln -snf "$REAL_HOME/.ssh" "$PROFILE_HOME/.ssh"
fi

if [ ! -f "$PROFILE_CLAUDE" ]; then
  printf '{\n  "mcpServers": {}\n}\n' > "$PROFILE_CLAUDE"
fi

if [ "$#" -eq 0 ]; then
  exec env HOME="$PROFILE_HOME" "${SHELL:-/bin/bash}"
fi

exec env HOME="$PROFILE_HOME" "$@"

#!/usr/bin/env bash
set -euo pipefail

SOURCE_PATH="${BASH_SOURCE[0]}"
while [ -L "$SOURCE_PATH" ]; do
  LINK_DIR="$(cd "$(dirname "$SOURCE_PATH")" && pwd)"
  SOURCE_PATH="$(readlink "$SOURCE_PATH")"
  [[ "$SOURCE_PATH" != /* ]] && SOURCE_PATH="$LINK_DIR/$SOURCE_PATH"
done
SCRIPT_DIR="$(cd "$(dirname "$SOURCE_PATH")" && pwd)"
REAL_HOME="${HOME}"
BASE="${OUROSSS_ROOT:-$REAL_HOME/kurkin}"
PROFILE_SETTINGS="$BASE/claude/settings.json"

exec "$SCRIPT_DIR/profile-exec.sh" \
  claude \
  --setting-sources project \
  --settings "$PROFILE_SETTINGS" \
  "$@"

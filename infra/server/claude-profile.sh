#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REAL_HOME="${HOME}"
BASE="${OUROSSS_ROOT:-$REAL_HOME/kurkin}"
PROFILE_SETTINGS="$BASE/claude/settings.json"

exec "$SCRIPT_DIR/profile-exec.sh" \
  claude \
  --setting-sources project \
  --settings "$PROFILE_SETTINGS" \
  "$@"

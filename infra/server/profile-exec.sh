#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

PROFILE_HOME="$(ourosss_profile_home)"
ourosss_ensure_profile_layout
ourosss_ensure_claude_settings

if [ "$#" -eq 0 ]; then
  exec env HOME="$PROFILE_HOME" "${SHELL:-/bin/bash}"
fi

exec env HOME="$PROFILE_HOME" "$@"

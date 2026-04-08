#!/usr/bin/env bash
# Restore Claude Code user-scoped skills from the repo mirror.
# Usage: bash infra/local/restore-claude-skills.sh [--force]
#   --force  overwrite existing skills (default: rsync no-clobber, won't touch existing)

set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
SRC="$REPO/infra/claude/skills/"
DST="$HOME/.claude/skills/"

mkdir -p "$DST"

if [[ "${1:-}" == "--force" ]]; then
  echo "[restore-claude-skills] FORCE mode: overwriting existing skills"
  rsync -av --delete "$SRC" "$DST"
else
  echo "[restore-claude-skills] safe mode: only adding missing skills (use --force to overwrite)"
  rsync -av --ignore-existing "$SRC" "$DST"
fi

echo "[restore-claude-skills] Done. Skills now in $DST"
ls -1 "$DST" | sed 's/^/  /'

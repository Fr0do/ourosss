#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

BASE="$(ourosss_base_dir)"
PROFILE_HOME="$(ourosss_profile_home)"
LOG_FILE="$(ourosss_logs_dir)/sync.log"
mkdir -p "$(dirname "$LOG_FILE")"
exec >>"$LOG_FILE" 2>&1

stamp() { date -u '+%Y-%m-%dT%H:%M:%SZ'; }
log() { echo "[$(stamp)] $*"; }

on_err() {
  log "ERROR: sync-pull failed with status $?"
  exit 0  # do not crash the systemd timer; error already logged
}
trap on_err ERR

REPO="$(ourosss_repo_dir)"

log "---- sync start ----"
if [ ! -d "$REPO/.git" ]; then
  log "Repo missing at $REPO; skipping"
  exit 0
fi

cd "$REPO"
OLD="$(git rev-parse HEAD)"
log "Current HEAD: $OLD"

log "git pull --rebase --autostash"
if ! git pull --rebase --autostash >>"$LOG_FILE" 2>&1; then
  echo "[$(date -u +%FT%TZ)] git pull failed — aborting any in-progress rebase" >>"$LOG_FILE"
  git rebase --abort 2>/dev/null || true
  # Server repo is read-only (no local commits); hard reset is safe here.
  git reset --hard "origin/$(git rev-parse --abbrev-ref HEAD)" 2>/dev/null || true
  exit 0
fi

NEW="$(git rev-parse HEAD)"
log "New HEAD: $NEW"

if [ "$OLD" = "$NEW" ]; then
  log "No changes pulled"
  log "---- sync done ----"
  exit 0
fi

CHANGED_FILES="$(git diff --name-only "$OLD" "$NEW" || true)"
log "Changed files:"
printf '%s\n' "$CHANGED_FILES"

if printf '%s\n' "$CHANGED_FILES" | grep -q 'infra/hermes/skills-snapshot.yaml'; then
  if command -v hermes >/dev/null 2>&1 && [ -s "infra/hermes/skills-snapshot.yaml" ]; then
    log "Re-importing Hermes skills snapshot"
    env HOME="$PROFILE_HOME" hermes skills snapshot import infra/hermes/skills-snapshot.yaml || log "Hermes import failed"
  else
    log "Hermes CLI missing or snapshot empty; skipping import"
  fi
fi

if printf '%s\n' "$CHANGED_FILES" | grep -Eq '^(bot/|pyproject\.toml$|uv\.lock$)'; then
  log "Dependencies/bot changed; running uv sync --locked"
  uv sync --locked
  log "Restarting ourosss service"
  systemctl --user restart ourosss
fi

if printf '%s\n' "$CHANGED_FILES" | grep -Eq '^infra/server/.*\.(service|timer)$'; then
  log "Server units changed; updating systemd user units"
  mkdir -p "$HOME/.config/systemd/user"
  cp infra/server/ourosss.service infra/server/ourosss-sync.service infra/server/ourosss-sync.timer "$HOME/.config/systemd/user/"
  systemctl --user daemon-reload
  systemctl --user restart ourosss.service || true
  systemctl --user restart ourosss-sync.timer || true
fi

log "---- sync done ----"

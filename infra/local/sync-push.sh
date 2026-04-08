#!/usr/bin/env bash
set -euo pipefail

LOG_FILE="$HOME/Library/Logs/ourosss-sync.log"
mkdir -p "$(dirname "$LOG_FILE")"
exec >>"$LOG_FILE" 2>&1

stamp() { date -u '+%Y-%m-%dT%H:%M:%SZ'; }
log() { echo "[$(stamp)] $*"; }

REPO="${OUROSSS_REPO:-$(cd "$(dirname "$0")/../.." && pwd)}"
cd "$REPO"
log "---- push start ----"

if command -v hermes >/dev/null 2>&1; then
  log "Exporting Hermes skills snapshot"
  hermes skills snapshot export "$REPO/infra/hermes/skills-snapshot.yaml" >>"$LOG_FILE" 2>&1 || \
    echo "[$(date -u +%FT%TZ)] hermes skills export failed — continuing" >>"$LOG_FILE"
else
  echo "[$(date -u +%FT%TZ)] hermes CLI not found — skipping skills export" >>"$LOG_FILE"
fi

if [[ -f "$HOME/.hermes/memories/USER.md" ]]; then
  log "Copying USER.md memory"
  mkdir -p "$REPO/infra/hermes/memories"
  cp "$HOME/.hermes/memories/USER.md" "$REPO/infra/hermes/memories/USER.md"
else
  echo "[$(date -u +%FT%TZ)] ~/.hermes/memories/USER.md missing — skipping memory copy" >>"$LOG_FILE"
fi

if git diff --quiet infra/; then
  log "No infra changes to commit"
else
  log "Committing infra sync"
  git add infra/hermes/skills-snapshot.yaml infra/hermes/memories/USER.md
  COMMIT_MSG="[infra] auto-sync hermes state ($(date -u +%Y-%m-%dT%H:%MZ))"
  if git commit -m "$COMMIT_MSG"; then
    git push origin main
    log "Pushed commit: $COMMIT_MSG"
  else
    log "Git commit failed (possibly hook); aborting push"
    exit 1
  fi
fi

SERVER_HOST="${SERVER_HOST:-kurkin-vllm}"
if [ -n "$SERVER_HOST" ]; then
  log "Rsync secrets to $SERVER_HOST"
  rsync -avz "$HOME/.hermes/.env" "$SERVER_HOST:kurkin/secrets/hermes.env" || \
    echo "[$(date -u +%FT%TZ)] rsync hermes.env failed (network?) — continuing" >>"$LOG_FILE"
  rsync -avz "$HOME/.hermes/auth.json" "$SERVER_HOST:kurkin/secrets/auth.json" || \
    echo "[$(date -u +%FT%TZ)] rsync auth.json failed (network?) — continuing" >>"$LOG_FILE"
  rsync -avz "$REPO/.env" "$SERVER_HOST:kurkin/secrets/.env" || \
    echo "[$(date -u +%FT%TZ)] rsync bot .env failed (network?) — continuing" >>"$LOG_FILE"
else
  log "SERVER_HOST not set; skipping rsync"
fi

log "---- push done ----"

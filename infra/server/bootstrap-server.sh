#!/usr/bin/env bash
set -euo pipefail

stamp() { date -u '+%Y-%m-%dT%H:%M:%SZ'; }
log() { echo "[$(stamp)] $*"; }
warn() { echo "[$(stamp)] WARN: $*"; }
has_systemd_user_bus() {
  systemctl --user show-environment >/dev/null 2>&1
}

BASE="$HOME/kurkin"
BASE="${OUROSSS_ROOT:-$BASE}"
REPO="$BASE/ourosss"
HERMES_HOME="$BASE/hermes"
PROFILE_HOME="${OUROSSS_PROFILE_HOME:-$BASE/home}"
PROFILE_CLAUDE="$BASE/claude/settings.json"
SECRETS="$BASE/secrets"
LOGS="$BASE/logs"
SHARED_USER_MODE="${OUROSSS_SHARED_USER:-0}"

log "==> OuroSSS server bootstrap"
log "Base dir: $BASE"

mkdir -p "$BASE" "$REPO" "$HERMES_HOME" "$SECRETS" "$LOGS" "$BASE/bin" "$BASE/claude"
if [ "$SHARED_USER_MODE" = "1" ]; then
  mkdir -p "$PROFILE_HOME/.claude"
fi
log "Ensured dirs: $BASE/{ourosss,hermes,secrets,logs,bin,claude}"

if [ ! -d "$REPO/.git" ]; then
  log "Cloning repo into $REPO"
  git clone git@github.com:Fr0do/ourosss.git "$REPO"
else
  log "Repo exists; pulling latest"
  git -C "$REPO" pull --rebase --autostash
fi

# Symlink Hermes home either globally or into the isolated profile.
if [ "$SHARED_USER_MODE" = "1" ]; then
  ln -snf "$HERMES_HOME" "$PROFILE_HOME/.hermes"
  if [ "$(readlink "$PROFILE_HOME/.hermes")" = "$HERMES_HOME" ]; then
    log "Shared-user mode: symlinked $PROFILE_HOME/.hermes -> $HERMES_HOME"
  else
    warn "Symlink for $PROFILE_HOME/.hermes not set correctly"
  fi
else
  if [ -e "$HOME/.hermes" ] && [ ! -L "$HOME/.hermes" ]; then
    BACKUP="$HOME/.hermes.bak.$(date -u '+%Y%m%d%H%M%S')"
    mv "$HOME/.hermes" "$BACKUP"
    log "Backed up existing ~/.hermes to $BACKUP"
  fi

  ln -snf "$HERMES_HOME" "$HOME/.hermes"
  if [ "$(readlink "$HOME/.hermes")" = "$HERMES_HOME" ]; then
    log "Symlinked ~/.hermes -> $HERMES_HOME"
  else
    warn "Symlink for ~/.hermes not set correctly"
  fi
fi

# Run repo bootstrap with server flag
log "Running infra/bootstrap.sh --server"
(cd "$REPO/infra" && bash bootstrap.sh --server)

# Symlink USER.md memory (read-only target)
mkdir -p "$HERMES_HOME/memories"
MEM_SRC="$REPO/infra/hermes/memories/USER.md"
MEM_DST="$HERMES_HOME/memories/USER.md"
if [ -f "$MEM_SRC" ]; then
  # Note: USER.md is tracked in git — server-side hermes treats it as read-only by convention; do not chmod the tracked file or git pull will fail.
  if [ -f "$MEM_DST" ] && [ ! -L "$MEM_DST" ]; then
    BACKUP="$MEM_DST.bak.$(date +%s)"
    mv "$MEM_DST" "$BACKUP"
    log "Backed up existing memory file to $BACKUP"
  fi
  ln -snf "$MEM_SRC" "$MEM_DST"
  log "Symlinked memories USER.md"
else
  warn "Memory file missing at $MEM_SRC; skipping"
fi

# Import skills snapshot if available
SNAPSHOT="$REPO/infra/hermes/skills-snapshot.yaml"
if [ -s "$SNAPSHOT" ] && command -v hermes >/dev/null 2>&1; then
  log "Importing Hermes skills snapshot"
  env HOME="$PROFILE_HOME" hermes skills snapshot import "$SNAPSHOT" || warn "Hermes import failed"
else
  warn "Skills snapshot missing/empty or hermes CLI unavailable; skipping import"
fi

# Secrets symlinks (only if source exists)
if [ -f "$SECRETS/.env" ]; then
  ln -snf "$SECRETS/.env" "$REPO/.env"
  log "Linked bot .env into repo"
else
  warn "Secret missing: $SECRETS/.env (bot env)"
fi

if [ -f "$SECRETS/auth.json" ]; then
  ln -snf "$SECRETS/auth.json" "$HERMES_HOME/auth.json"
  log "Linked Hermes auth.json"
else
  warn "Secret missing: $SECRETS/auth.json (Hermes auth)"
fi

if [ -f "$SECRETS/hermes.env" ]; then
  ln -snf "$SECRETS/hermes.env" "$HERMES_HOME/.env"
  log "Linked Hermes env file"
else
  warn "Secret missing: $SECRETS/hermes.env (Hermes env)"
fi

if [ ! -f "$PROFILE_CLAUDE" ]; then
  cat > "$PROFILE_CLAUDE" <<'EOF'
{
  "mcpServers": {}
}
EOF
  log "Created per-profile Claude settings at $PROFILE_CLAUDE"
fi

ln -snf "$REPO/infra/server/profile-exec.sh" "$BASE/bin/ourosss-profile"
ln -snf "$REPO/infra/server/claude-profile.sh" "$BASE/bin/ourosss-claude"
ln -snf "$REPO/infra/server/ourosss-run.sh" "$BASE/bin/ourosss-run"
ln -snf "$REPO/infra/server/bootstrap-python.sh" "$BASE/bin/ourosss-bootstrap-python"
log "Installed profile wrappers in $BASE/bin"

if command -v hermes >/dev/null 2>&1; then
  log "Hermes CLI detected"
else
  warn "Hermes CLI not found in PATH; install it before running: $BASE/bin/ourosss-profile hermes login"
fi

if command -v claude >/dev/null 2>&1; then
  log "Claude CLI detected"
else
  warn "Claude CLI not found in PATH; install it before running: $BASE/bin/ourosss-claude"
fi

# Install systemd user units when a user bus is available.
if has_systemd_user_bus; then
  log "Installing systemd user units"
  mkdir -p "$HOME/.config/systemd/user"
  cp "$REPO"/infra/server/ourosss.service "$REPO"/infra/server/ourosss-sync.service "$REPO"/infra/server/ourosss-sync.timer "$HOME/.config/systemd/user/"
  systemctl --user daemon-reload
  systemctl --user enable --now ourosss.service
  systemctl --user enable --now ourosss-sync.timer
else
  warn "systemd --user bus unavailable; skipping user unit install"
  log "Fallback launcher available: $BASE/bin/ourosss-run {start|stop|restart|status|logs}"
fi

# linger
if command -v loginctl >/dev/null 2>&1 && loginctl enable-linger "$USER"; then
  log "Linger enabled for $USER"
else
  warn "loginctl enable-linger unavailable or requires sudo; run manually if needed"
fi

log "==> Bootstrap complete"
echo "Secrets (rsync from laptop):"
echo "  $SECRETS/.env        -> bot env"
echo "  $SECRETS/auth.json   -> hermes auth"
echo "  $SECRETS/hermes.env  -> hermes env"
echo "Logs: tail -f $LOGS/ourosss.log or journalctl --user -u ourosss -f"
echo "Restart bot: systemctl --user restart ourosss"
echo "Bootstrap pinned Python/uv: $BASE/bin/ourosss-bootstrap-python"
if [ "$SHARED_USER_MODE" = "1" ]; then
  echo "Shared-user mode:"
  echo "  Claude: $BASE/bin/ourosss-claude"
  echo "  Hermes: $BASE/bin/ourosss-profile hermes <subcommand>"
fi
echo "  Bot fallback launcher: $BASE/bin/ourosss-run {start|stop|restart|status|logs}"

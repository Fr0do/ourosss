#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

BASE="$(ourosss_base_dir)"
REPO="$(ourosss_repo_dir)"
SECRETS="$(ourosss_secrets_dir)/.env"
LOG_DIR="$(ourosss_logs_dir)"
PID_FILE="$LOG_DIR/ourosss.pid"
STDOUT_LOG="$LOG_DIR/ourosss.log"
STDERR_LOG="$LOG_DIR/ourosss.err.log"

mkdir -p "$LOG_DIR"

is_running() {
  if [ ! -f "$PID_FILE" ]; then
    return 1
  fi

  local pid
  pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null
}

load_env() {
  if [ -f "$SECRETS" ]; then
    set -a
    # shellcheck disable=SC1090
    source "$SECRETS"
    set +a
  fi
}

start() {
  if is_running; then
    echo "ourosss already running with pid $(cat "$PID_FILE")"
    return 0
  fi

  load_env
  (
    cd "$REPO"
    nohup /bin/bash -lc 'exec uv run ourosss' >>"$STDOUT_LOG" 2>>"$STDERR_LOG" &
    echo $! > "$PID_FILE"
  )
  echo "started ourosss with pid $(cat "$PID_FILE")"
}

stop() {
  if ! is_running; then
    rm -f "$PID_FILE"
    echo "ourosss is not running"
    return 0
  fi

  local pid
  pid="$(cat "$PID_FILE")"
  kill "$pid" 2>/dev/null || true

  for _ in 1 2 3 4 5 6 7 8 9 10; do
    if ! kill -0 "$pid" 2>/dev/null; then
      rm -f "$PID_FILE"
      echo "stopped ourosss"
      return 0
    fi
    sleep 1
  done

  kill -9 "$pid" 2>/dev/null || true
  rm -f "$PID_FILE"
  echo "force-stopped ourosss"
}

status() {
  if is_running; then
    echo "ourosss is running with pid $(cat "$PID_FILE")"
  else
    echo "ourosss is not running"
    return 1
  fi
}

logs() {
  touch "$STDOUT_LOG" "$STDERR_LOG"
  exec tail -n 100 -f "$STDOUT_LOG" "$STDERR_LOG"
}

case "${1:-}" in
  start) start ;;
  stop) stop ;;
  restart) stop || true; start ;;
  status) status ;;
  logs) shift; logs "$@" ;;
  *)
    echo "usage: $0 {start|stop|restart|status|logs}" >&2
    exit 2
    ;;
esac

"""
Training heartbeat monitor — checks kurkin-1 every 30 min for anomalies.
Sends Telegram alert on: dead tmux, stalled log, OOM/traceback, GPU at 0%.
Logs every run to artifacts/heartbeat.log.

Usage:
    python scripts/heartbeat_monitor.py
"""

import json
import logging
import os
import subprocess
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = ROOT / "artifacts" / "training_state.json"
HEARTBEAT_LOG = ROOT / "artifacts" / "heartbeat.log"

# Load .env
env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
_raw_users = os.getenv("AUTHORIZED_USERS", "")
CHAT_IDS = [int(x.strip()) for x in _raw_users.split(",") if x.strip()]

REMOTE = "kurkin-1"
PROJECTS = {
    "s_cot": {"tmux": "cot", "path": "/workspace-SR004.nfs2/kurkin/s_cot"},
    "long-vqa": {"tmux": "vqa", "path": "/workspace-SR004.nfs2/kurkin/long-vqa"},
    "bbbo": {"tmux": "bbbo", "path": "/workspace-SR004.nfs2/kurkin/bbbo/GeneralOptimizer"},
}

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(HEARTBEAT_LOG),
    ],
    level=logging.INFO,
)
log = logging.getLogger("heartbeat")


def ssh(cmd: str, timeout: int = 20) -> tuple[int, str]:
    """Run command on REMOTE, return (returncode, stdout+stderr)."""
    try:
        result = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=10", REMOTE, cmd],
            capture_output=True, text=True, timeout=timeout,
        )
        return result.returncode, (result.stdout + result.stderr).strip()
    except subprocess.TimeoutExpired:
        return -1, "SSH timeout"
    except Exception as e:
        return -1, str(e)


def tg_send(text: str):
    """Send text to all authorized Telegram users."""
    if not TELEGRAM_TOKEN or not CHAT_IDS:
        log.warning("No TELEGRAM_TOKEN or AUTHORIZED_USERS configured")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    for chat_id in CHAT_IDS:
        payload = json.dumps({"chat_id": chat_id, "text": text}).encode()
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if resp.status != 200:
                    log.warning(f"Telegram send failed: {resp.status}")
        except Exception as e:
            log.warning(f"Telegram send error: {e}")


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {}


def save_state(state: dict):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2))


def check_gpu() -> dict[str, str]:
    """Returns {index: util_pct} for all GPUs."""
    rc, out = ssh("nvidia-smi --query-gpu=index,utilization.gpu --format=csv,noheader")
    if rc != 0:
        return {}
    result = {}
    for line in out.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 2:
            idx = parts[0]
            util = parts[1].replace(" %", "")
            result[idx] = util
    return result


def check_tmux() -> set[str]:
    """Returns set of running tmux session names."""
    rc, out = ssh("tmux ls 2>/dev/null || true")
    if rc != 0 or not out.strip():
        return set()
    sessions = set()
    for line in out.splitlines():
        if ":" in line:
            sessions.add(line.split(":")[0].strip())
    return sessions


def check_log_tail(tmux_session: str) -> str:
    """Returns last 5 lines of tmux pane."""
    rc, out = ssh(f"tmux capture-pane -t {tmux_session} -p 2>/dev/null | tail -5")
    return out if rc == 0 else ""


def detect_errors(log_tail: str) -> list[str]:
    """Detect OOM, traceback, CUDA errors in log tail."""
    errors = []
    lower = log_tail.lower()
    if "out of memory" in lower or "oom" in lower:
        errors.append("OOM")
    if "traceback" in lower:
        errors.append("Traceback")
    if "cuda error" in lower:
        errors.append("CUDA error")
    if "killed" in lower and "process" in lower:
        errors.append("Process killed")
    return errors


def run():
    now = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    log.info(f"=== Heartbeat {now} ===")
    state = load_state()
    anomalies = []

    # Check GPU
    gpu_utils = check_gpu()
    log.info(f"GPU utils: {gpu_utils}")

    # Check each project
    running_sessions = check_tmux()
    log.info(f"Tmux sessions: {running_sessions}")

    # Detect which projects were previously active
    prev_active = state.get("active_projects", [])
    curr_active = []

    for proj, cfg in PROJECTS.items():
        sess = cfg["tmux"]
        if sess not in running_sessions:
            if proj in prev_active:
                # Was running before, now gone
                anomalies.append(f"DEAD: {proj} tmux session '{sess}' is gone")
                log.warning(f"Project {proj}: session dead")
            else:
                log.info(f"Project {proj}: not running (expected)")
            continue

        curr_active.append(proj)
        log.info(f"Project {proj}: session alive")

        # Check log staleness
        tail = check_log_tail(sess)
        prev_tail = state.get(f"log_tail_{proj}", "")
        if tail and tail == prev_tail:
            anomalies.append(f"STALLED: {proj} log unchanged for 30+ min")
            log.warning(f"Project {proj}: log stalled")
        state[f"log_tail_{proj}"] = tail

        # Check for errors
        errs = detect_errors(tail)
        if errs:
            anomalies.append(f"ERROR in {proj}: {', '.join(errs)}")
            log.warning(f"Project {proj}: errors detected: {errs}")

    # Check GPU idle while session is active
    any_active = len(curr_active) > 0
    if any_active and gpu_utils:
        all_idle = all(u == "0" for u in gpu_utils.values())
        if all_idle:
            anomalies.append(f"GPU IDLE: all GPUs at 0% but sessions active: {curr_active}")
            log.warning("All GPUs idle while training sessions active")

    state["active_projects"] = curr_active
    state["last_check"] = now
    state["gpu_utils"] = gpu_utils
    save_state(state)

    # Send Telegram if anomalies
    if anomalies:
        msg = f"TRAINING ALERT ({now})\n\n" + "\n".join(f"• {a}" for a in anomalies)
        tg_send(msg)
        log.warning(f"Sent alert: {anomalies}")
    else:
        log.info("OK — no anomalies")

    log.info("=== Done ===\n")


if __name__ == "__main__":
    run()

"""Persistent disk usage state — cached on disk as JSON."""
import json
import logging
import time
from pathlib import Path
from ..services.ssh import ssh_exec

logger = logging.getLogger("ouroboros")

NFS_HOST = "kurkin-1"
NFS_PATH = "/workspace-SR004.nfs2"
DUA_BIN = "~/.local/bin/dua"
MY_DIR = "kurkin"
STATE_FILE = Path(__file__).resolve().parent.parent.parent / ".disk_state.json"

WARN_PERCENT = 90
CRIT_PERCENT = 95
HISTORY_MAX = 48  # keep ~2 days of hourly samples


def _parse_dua_output(output: str) -> list[dict] | None:
    """Parse dua output into list of {size, path} entries."""
    if not output or "No such file" in output:
        return None
    entries = []
    for line in output.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 2)
        if len(parts) >= 3:
            entries.append({"size": f"{parts[0]} {parts[1]}", "path": parts[2]})
        elif len(parts) == 2:
            entries.append({"size": parts[0], "path": parts[1]})
    return entries


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


async def refresh_df() -> dict:
    """Quick df check — seconds. Appends to history."""
    df = await ssh_exec(NFS_HOST, f"df -h {NFS_PATH} | tail -1", timeout=15)
    parts = df.split() if df else []

    state = load_state()
    now = time.strftime("%Y-%m-%d %H:%M")
    state["df_updated"] = now

    if len(parts) >= 5:
        state["total"] = parts[1]
        state["used"] = parts[2]
        state["avail"] = parts[3]
        state["percent"] = int(parts[4].rstrip("%"))

        # Append to history for trend tracking
        history = state.get("history", [])
        history.append({"t": now, "pct": state["percent"], "avail": parts[3]})
        state["history"] = history[-HISTORY_MAX:]
    else:
        state["df_raw"] = df

    save_state(state)
    return state


async def refresh_dua(top_n: int = 20) -> dict:
    """Full dua scan — can take minutes."""
    output = await ssh_exec(
        NFS_HOST,
        f"{DUA_BIN} {NFS_PATH} -t {top_n} 2>/dev/null",
        timeout=600,
    )

    state = load_state()
    state["dua_updated"] = time.strftime("%Y-%m-%d %H:%M")

    entries = _parse_dua_output(output)
    if entries is not None:
        state["top_dirs"] = entries
    else:
        state["dua_error"] = output or "empty"

    save_state(state)
    return state


async def refresh_my_usage() -> dict:
    """Scan just our own directory — faster than full NFS."""
    output = await ssh_exec(
        NFS_HOST,
        f"{DUA_BIN} {NFS_PATH}/{MY_DIR} -t 15 2>/dev/null",
        timeout=120,
    )

    state = load_state()
    state["my_updated"] = time.strftime("%Y-%m-%d %H:%M")

    entries = _parse_dua_output(output)
    if entries is not None:
        state["my_dirs"] = entries
    else:
        state["my_error"] = output or "empty"

    save_state(state)
    return state


def _trend_line(state: dict) -> str:
    """Show recent trend from history."""
    history = state.get("history", [])
    if len(history) < 2:
        return ""

    recent = history[-1]
    oldest = history[0]
    delta = recent["pct"] - oldest["pct"]
    n = len(history)
    span = f"{oldest['t']} → {recent['t']}"

    if delta > 0:
        arrow = "📈"
        direction = f"+{delta}%"
    elif delta < 0:
        arrow = "📉"
        direction = f"{delta}%"
    else:
        arrow = "➡️"
        direction = "stable"

    return f"{arrow} Trend: {direction} over {n} samples ({span})"


def format_report(state: dict) -> str:
    """Format cached state into a Telegram message."""
    lines = []

    pct = state.get("percent")
    if pct is not None:
        if pct >= CRIT_PERCENT:
            lines.append(f"🔴 *CRITICAL — {pct}% full*")
        elif pct >= WARN_PERCENT:
            lines.append(f"🟡 *WARNING — {pct}% full*")
        else:
            lines.append(f"🟢 *{pct}% used*")

    used = state.get("used", "?")
    total = state.get("total", "?")
    avail = state.get("avail", "?")
    lines.append(f"{used} used / {total} total ({avail} free)")

    trend = _trend_line(state)
    if trend:
        lines.append(trend)

    lines.append(f"_df: {state.get('df_updated', 'never')}_")

    # Top directories
    top_dirs = state.get("top_dirs")
    if top_dirs:
        dir_lines = [f"{e['size']:>10}  {e['path']}" for e in top_dirs[:20]]
        lines.append(f"\n*Top directories:*\n```\n" + "\n".join(dir_lines) + "\n```")
        lines.append(f"_dua: {state.get('dua_updated', 'never')}_")
    else:
        lines.append(f"\n_No dua scan yet. `/disk scan` to start._")

    return "\n".join(lines)


def format_my_report(state: dict) -> str:
    """Format personal usage report."""
    lines = [f"*Your usage* (`{NFS_PATH}/{MY_DIR}`):\n"]

    my_dirs = state.get("my_dirs")
    if my_dirs:
        dir_lines = [f"{e['size']:>10}  {e['path']}" for e in my_dirs[:15]]
        lines.append(f"```\n" + "\n".join(dir_lines) + "\n```")
        lines.append(f"_updated: {state.get('my_updated', 'never')}_")
    else:
        lines.append("_No scan yet. Running..._")

    return "\n".join(lines)

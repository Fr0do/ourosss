"""Agent cost dashboard — Claude Code, Codex, Gemini.

Shows token usage and estimated costs across all three CLIs.
Gemini has no local token tracking; session count is shown instead.

Usage:
    python scripts/agent_dashboard.py               # dashboard (remote data from cache)
    python scripts/agent_dashboard.py --days 30
    python scripts/agent_dashboard.py --fetch       # fetch remote data and update cache (VPN off)
    python scripts/agent_dashboard.py --json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from datetime import datetime, timedelta
from typing import Any

_CACHE_DIR = os.path.expanduser("~/.cache/agent-dashboard")

# ---------------------------------------------------------------------------
# Cost tables (as of Apr 2026, $/1M tokens)
# ---------------------------------------------------------------------------
COST = {
    # Claude models (input / output per 1M tokens)
    "claude-sonnet-4-6":         (3.0,   15.0),
    "claude-opus-4-6":           (15.0,  75.0),
    "claude-haiku-4-5":          (0.8,   4.0),
    # Codex CLI subscription models — estimated at capability-tier parity
    "gpt-5.4":                   (15.0,  75.0),
    "gpt-5.3-codex":             (3.0,   15.0),
    "gpt-5.3-codex-spark":       (0.8,   4.0),
    "gpt-5.2-codex":             (3.0,   15.0),
    # OpenAI API models
    "codex-mini-latest":         (1.5,   6.0),
    "gpt-4.1":                   (2.0,   8.0),
    "gpt-4.1-mini":              (0.4,   1.6),
    "gpt-4.1-nano":              (0.1,   0.4),
    "o4-mini":                   (1.1,   4.4),
    "o3":                        (10.0,  40.0),
    # Gemini
    "gemini-2.5-pro":            (1.25,  10.0),
    "gemini-2.0-flash":          (0.1,   0.4),
}
DEFAULT_COST_IN  = 15.0
DEFAULT_COST_OUT = 75.0


def _cost(model: str | None, input_tok: int, output_tok: int) -> float:
    model = (model or "").lower()
    for key, (c_in, c_out) in COST.items():
        if key in model:
            return (input_tok * c_in + output_tok * c_out) / 1_000_000
    return (input_tok * DEFAULT_COST_IN + output_tok * DEFAULT_COST_OUT) / 1_000_000


# ---------------------------------------------------------------------------
# Shared ccusage JSON parser
# ---------------------------------------------------------------------------

def _empty_totals() -> dict[str, Any]:
    return {
        "input_tokens": 0, "output_tokens": 0,
        "cache_read_tokens": 0, "cache_create_tokens": 0,
        "total_tokens": 0, "total_cost_usd": 0.0,
        "by_model": {}, "sources": [], "errors": [],
    }


def _parse_ccusage_json(data: Any, source: str, totals: dict) -> None:
    """Merge ccusage-format daily JSON into totals dict in-place."""
    if isinstance(data, dict):
        rows = data.get("daily", [])
    elif isinstance(data, list) and data and isinstance(data[0], list):
        rows = data[0][1] if len(data[0]) > 1 else []
    else:
        rows = data if isinstance(data, list) else []

    for row in rows:
        totals["input_tokens"]        += row.get("inputTokens", 0)
        totals["output_tokens"]       += row.get("outputTokens", 0)
        totals["cache_read_tokens"]   += row.get("cacheReadTokens", 0)
        totals["cache_create_tokens"] += row.get("cacheCreationTokens", 0)
        totals["total_tokens"]        += row.get("totalTokens", 0)
        totals["total_cost_usd"]      += row.get("totalCost", 0.0)
        for mb in row.get("modelBreakdowns", []):
            name = mb["modelName"]
            m = totals["by_model"].setdefault(name, {"tokens": 0, "cost": 0.0})
            m["tokens"] += mb.get("inputTokens", 0) + mb.get("outputTokens", 0)
            m["cost"]   += mb.get("cost", 0.0)
    totals["sources"].append(source)


# ---------------------------------------------------------------------------
# Remote cache helpers
# ---------------------------------------------------------------------------

def _cache_path(host: str) -> str:
    return os.path.join(_CACHE_DIR, f"{host}.json")


def _load_cache(host: str) -> tuple[dict | None, str | None]:
    """Return (data, fetched_at_str) or (None, None) if no cache."""
    path = _cache_path(host)
    if not os.path.exists(path):
        return None, None
    try:
        with open(path) as f:
            envelope = json.load(f)
        return envelope["data"], envelope["fetched_at"]
    except Exception:
        return None, None


def _save_cache(host: str, data: dict) -> None:
    os.makedirs(_CACHE_DIR, exist_ok=True)
    path = _cache_path(host)
    envelope = {"fetched_at": datetime.now().isoformat(timespec="minutes"), "data": data}
    with open(path, "w") as f:
        json.dump(envelope, f)


def fetch_remote_hosts(hosts: list[str], days: int) -> None:
    """SSH to each host, run ccusage, save to cache. Run with VPN off."""
    since = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
    for host in hosts:
        print(f"  Fetching {host}...", end=" ", flush=True)
        try:
            raw = subprocess.check_output(
                ["ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
                 host, f"bash -lc 'source ~/.nvm/nvm.sh && nvm use 24 --silent && "
                       f"npx ccusage daily --since {since} --json --offline'"],
                text=True, stderr=subprocess.DEVNULL, timeout=120,
            )
            data = json.loads(raw)
            _save_cache(host, data)
            days_found = len(data.get("daily", []))
            print(f"ok ({days_found} days cached)")
        except subprocess.TimeoutExpired:
            print("timeout")
        except Exception as e:
            print(f"error: {e}")


# ---------------------------------------------------------------------------
# Claude Code via ccusage (local + cached remote)
# ---------------------------------------------------------------------------

_REMOTE_HOSTS: list[str] = ["kurkin-1", "kurkin-4"]


def _claude_stats(days: int, remote_hosts: list[str] | None = None) -> dict[str, Any]:
    since_dt = datetime.now() - timedelta(days=days)
    since = since_dt.strftime("%Y%m%d")
    totals = _empty_totals()

    # Local
    try:
        raw = subprocess.check_output(
            ["ccusage", "daily", "--since", since, "--json", "--offline"],
            text=True, stderr=subprocess.DEVNULL,
        )
        _parse_ccusage_json(json.loads(raw), "local", totals)
    except FileNotFoundError:
        return {"error": "ccusage not installed (npm install -g ccusage)"}
    except Exception as e:
        totals["errors"].append(f"local: {e}")

    # Remote hosts — read from cache
    for host in (remote_hosts or []):
        cached_data, fetched_at = _load_cache(host)
        if cached_data is None:
            totals["errors"].append(f"{host}: no cache (run --fetch with VPN off)")
            continue
        # Filter cached daily rows to the requested window
        if isinstance(cached_data, dict) and "daily" in cached_data:
            rows = [r for r in cached_data["daily"]
                    if r.get("date", "") >= since_dt.strftime("%Y-%m-%d")]
            filtered = {"daily": rows}
        else:
            filtered = cached_data
        label = f"{host} (cached {fetched_at})"
        _parse_ccusage_json(filtered, label, totals)

    return totals


# ---------------------------------------------------------------------------
# Codex via @ccusage/codex
# ---------------------------------------------------------------------------

def _codex_stats(days: int) -> dict[str, Any]:
    since = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
    totals = _empty_totals()
    try:
        raw = subprocess.check_output(
            ["npx", "--yes", "@ccusage/codex", "daily", "--since", since, "--json"],
            text=True, stderr=subprocess.DEVNULL, timeout=60,
        )
        _parse_ccusage_json(json.loads(raw), "local", totals)
    except subprocess.TimeoutExpired:
        return {"error": "@ccusage/codex: timeout"}
    except FileNotFoundError:
        return {"error": "npx not found"}
    except Exception as e:
        return {"error": str(e)}
    return totals


# ---------------------------------------------------------------------------
# Gemini via session history count
# ---------------------------------------------------------------------------

_GEMINI_HISTORY = os.path.expanduser("~/.gemini/history")


def _gemini_stats(days: int) -> dict[str, Any]:
    if not os.path.isdir(_GEMINI_HISTORY):
        return {"error": f"history dir not found: {_GEMINI_HISTORY}"}

    cutoff = datetime.now() - timedelta(days=days)
    projects: list[str] = []
    for proj in os.listdir(_GEMINI_HISTORY):
        proj_path = os.path.join(_GEMINI_HISTORY, proj)
        if os.path.isdir(proj_path):
            mtime = datetime.fromtimestamp(os.path.getmtime(proj_path))
            if mtime >= cutoff:
                projects.append(proj)

    return {
        "active_projects": len(projects),
        "projects": projects,
        "note": "Gemini CLI has no local token tracking. Check Google Cloud Console for usage.",
    }


# ---------------------------------------------------------------------------
# Render
# ---------------------------------------------------------------------------

def _fmt_tok(n: int | None) -> str:
    if n is None:
        return "N/A"
    if n >= 1_000_000_000:
        return f"{n/1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(n)


def _render_ccusage_section(label: str, data: dict, w: int) -> None:
    print(f"\n  {label}")
    print("  " + "─" * (w - 4))
    if "error" in data:
        print(f"  ⚠  {data['error']}")
        return
    sources = data.get("sources", [])
    src_str = " + ".join(sources) if sources else "?"
    print(f"  Sources   : {src_str}")
    print(f"  Input     : {_fmt_tok(data.get('input_tokens', 0)):>8}")
    print(f"  Output    : {_fmt_tok(data.get('output_tokens', 0)):>8}")
    cr = data.get("cache_read_tokens", 0)
    cc = data.get("cache_create_tokens", 0)
    if cr or cc:
        print(f"  Cache read: {_fmt_tok(cr):>8}")
        print(f"  Cache wrt : {_fmt_tok(cc):>8}")
    print(f"  Total tok : {_fmt_tok(data.get('total_tokens', 0)):>8}")
    print(f"  Cost      : ${data.get('total_cost_usd', 0.0):>7.2f}")
    print()
    for model, info in sorted(data.get("by_model", {}).items(), key=lambda x: -x[1]["cost"]):
        short = model.replace("claude-", "").replace("-20251001", "")
        print(f"    {short:<30} {_fmt_tok(info['tokens']):>7}  ${info['cost']:.2f}")
    for err in data.get("errors", []):
        print(f"  ⚠  {err}")


def render_dashboard(claude: dict, codex: dict, gemini: dict, days: int) -> None:
    w = 66
    print("=" * w)
    print(f"  Agent Dashboard  (last {days} day{'s' if days != 1 else ''})")
    print("=" * w)

    _render_ccusage_section("CLAUDE CODE", claude, w)
    _render_ccusage_section("CODEX (OpenAI)", codex, w)

    print("\n  GEMINI (Google)")
    print("  " + "─" * (w - 4))
    if "error" in gemini:
        print(f"  ⚠  {gemini['error']}")
    else:
        print(f"  Active projects: {gemini.get('active_projects', 0)}")
        for p in (gemini.get("projects") or []):
            print(f"    · {p}")
        print(f"  ⚠  {gemini.get('note', '')}")

    print("\n" + "=" * w)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Unified agent cost dashboard")
    parser.add_argument("--days", type=int, default=7, help="Lookback window in days (default 7)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of formatted table")
    parser.add_argument("--fetch", action="store_true",
                        help="Fetch remote host data via SSH and update cache (run with VPN off)")
    parser.add_argument("--remote", nargs="*", metavar="HOST",
                        default=_REMOTE_HOSTS,
                        help=f"Remote SSH hosts (default: {_REMOTE_HOSTS}). Pass --remote with no args to disable.")
    args = parser.parse_args()

    remote_hosts = args.remote if args.remote is not None else []

    if args.fetch:
        print(f"Fetching remote hosts (last {args.days} days)...")
        fetch_remote_hosts(remote_hosts or _REMOTE_HOSTS, args.days)
        print("Done. Cache updated.")
        return

    claude = _claude_stats(args.days, remote_hosts=remote_hosts)
    codex  = _codex_stats(args.days)
    gemini = _gemini_stats(args.days)

    if args.json:
        print(json.dumps({"claude": claude, "codex": codex, "gemini": gemini}, indent=2))
    else:
        render_dashboard(claude, codex, gemini, args.days)


if __name__ == "__main__":
    main()

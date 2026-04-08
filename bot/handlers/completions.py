"""
/completions <project> [flags...] — flexible GRPO completions dashboard.

Flags (mix & match in any order):
  step <IDX>   — Python-style index/slice (default: -1 i.e. latest)
                 Examples: 0, -1, -3:, 0:5, ::2, 1:-1
  last <N>     — shorthand for step -N: (last N steps, stats mode)
  <N>          — bare number = sample count (default: 3)
  correct      — filter correct completions only
  wrong        — filter wrong completions only
  traces       — full prompt+completion in separate messages
  stats        — aggregate reward trend chart (PNG)
  baseline     — comprehensive 3x2 analysis across all steps
  numeric      — deep numeric stats for all columns (beyond describe)
  brief        — truncate completions (default for non-trace)

Examples:
  /completions s_cot                — latest step dashboard
  /completions s_cot traces         — 3 full traces from latest
  /completions s_cot wrong traces 2 — 2 wrong traces
  /completions s_cot stats          — reward trend chart
  /completions s_cot stats last 50  — last 50 steps chart
  /completions s_cot step 50        — step at index 50
  /completions s_cot step -1        — latest step (default)
  /completions s_cot step -3:       — last 3 steps
  /completions s_cot step 0:5       — first 5 steps
  /completions s_cot step ::2       — every other step
  /completions s_cot step 50 traces correct — traces from step at index 50
  /completions s_cot numeric        — deep numeric analysis
"""
import json
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from ..services.config import PROJECTS
from ..services.ssh import ssh_exec
from ..services.tg import send_long, require_project
from ..services.completions import (
    _fmt_sample_brief,
    _fmt_stats_header,
    _fmt_trace,
    _parse_flags,
    _remote_script,
    _send_chart,
)

PYTHON = "/workspace-SR004.nfs2/kurkin/envs/kurkin_313_torch/bin/python"

COMPLETIONS_DIRS = {"s_cot": "spectral-r1-checkpoints/fixed/completions"}


async def completions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/completions <project> [flags...]"""
    args = context.args or []
    if not args:
        await update.message.reply_text(
            "Usage: /completions <project> [flags...]\n\n"
            "Flags (mix & match):\n"
            "  stats        — reward trend chart (PNG)\n"
            "  baseline     — full analysis across all steps\n"
            "  numeric      — deep numeric stats for all columns\n"
            "  traces       — full prompt+completion\n"
            "  step <IDX>   — Python-style index/slice\n"
            "                  e.g. 0, -1, -3:, 0:5, ::2\n"
            "  last <N>     — shorthand for step -N:\n"
            "  <N>          — sample count (default 3)\n"
            "  correct      — filter correct only\n"
            "  wrong        — filter wrong only\n"
            "  brief        — truncate (default for dashboard)\n\n"
            "Examples:\n"
            "  /completions s_cot\n"
            "  /completions s_cot traces wrong 2\n"
            "  /completions s_cot stats last 50\n"
            "  /completions s_cot step -3: stats\n"
            "  /completions s_cot step 0 traces correct",
        )
        return

    name, err = require_project(args, "/completions <project> [flags...]")
    if err:
        await update.message.reply_text(err)
        return

    comp_subdir = COMPLETIONS_DIRS.get(name)
    if not comp_subdir:
        await update.message.reply_text(f"No completions path configured for {name}.")
        return

    proj = PROJECTS[name]
    parquet_glob = f"{proj['path']}/{comp_subdir}/completions_*.parquet"
    opts = _parse_flags(args[1:])

    script = _remote_script(parquet_glob, opts)
    escaped = script.replace("'", "'\\''")
    cmd = f"{PYTHON} -c '{escaped}'"

    label = opts["mode"]
    if opts["step"] is not None:
        sel = opts["step"]
        if "index" in sel:
            label += f" step[{sel['index']}]"
        elif "slice" in sel:
            s = sel["slice"]
            parts = [str(x) if x is not None else "" for x in s]
            label += f" step[{':'.join(parts)}]"
    if opts["filter"]:
        label += f" {opts['filter']}"
    await update.message.reply_text(f"Analyzing {name} completions ({label})...")

    timeout = 180 if opts["mode"] in ("baseline", "numeric") else 120 if opts["mode"] == "stats" else 60
    raw = await ssh_exec(proj["remote"], cmd, timeout=timeout)
    if not raw.strip():
        await update.message.reply_text("No output from remote script.")
        return

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Script printed plain text (error or debug)
        await send_long(update, raw)
        return

    if "error" in data:
        await update.message.reply_text(data["error"])
        return

    if data["type"] in ("baseline", "numeric", "stats"):
        await _send_chart(update, data)
    elif data["type"] == "traces":
        # Stats header first
        header = _fmt_stats_header(data["stats"])
        n_samples = len(data["samples"])
        filt_label = f" ({opts['filter']})" if opts["filter"] else ""
        await update.message.reply_text(
            f"{header}\n\nShowing {n_samples} trace(s){filt_label}:"
        )
        for i, s in enumerate(data["samples"], 1):
            trace = _fmt_trace(s, i)
            await send_long(update, trace)

    else:
        header = _fmt_stats_header(data["stats"])
        parts = [header, f"\n{len(data['samples'])} samples:"]
        for s in data["samples"]:
            parts.append("")
            parts.append(_fmt_sample_brief(s))
        text = "\n".join(parts)
        await send_long(update, text)


handler = CommandHandler("completions", completions_handler)

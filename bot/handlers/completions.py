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
"""
import base64
import io
import json
import textwrap
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from ..services.config import PROJECTS
from ..services.ssh import ssh_exec
from ..services.tg import send_long, require_project

PYTHON = "/workspace-SR004.nfs2/kurkin/envs/kurkin_313_torch/bin/python"

COMPLETIONS_DIRS = {
    "s_cot": "spectral-r1-checkpoints/fixed/completions",
}


def _parse_step(raw: str) -> dict:
    """Parse a Python-style index or slice string.

    Returns {"index": int} for single index, or
    {"slice": [start|None, stop|None, step|None]} for slices.
    """
    if ":" in raw:
        parts = raw.split(":")
        def _int_or_none(s):
            s = s.strip()
            return int(s) if s else None
        if len(parts) == 2:
            return {"slice": [_int_or_none(parts[0]), _int_or_none(parts[1]), None]}
        elif len(parts) == 3:
            return {"slice": [_int_or_none(parts[0]), _int_or_none(parts[1]), _int_or_none(parts[2])]}
        raise ValueError(f"Invalid slice: {raw}")
    return {"index": int(raw)}


def _parse_flags(args: list[str]) -> dict:
    """Parse flexible flag list into options dict."""
    opts = {
        "mode": "dashboard",  # dashboard | stats | traces
        "step": None,         # {"index": N} or {"slice": [start, stop, step]} or None
        "last": None,         # last N steps (stats mode) — shorthand for step -N:
        "count": 3,           # number of samples
        "filter": None,       # correct | wrong | None
        "brief": None,        # True/False/None (auto)
    }
    i = 0
    while i < len(args):
        a = args[i].lower()
        if a == "stats":
            opts["mode"] = "stats"
        elif a == "traces":
            opts["mode"] = "traces"
        elif a == "correct":
            opts["filter"] = "correct"
        elif a == "wrong":
            opts["filter"] = "wrong"
        elif a == "brief":
            opts["brief"] = True
        elif a == "step" and i + 1 < len(args):
            i += 1
            try:
                opts["step"] = _parse_step(args[i])
            except (ValueError, IndexError):
                pass  # ignore malformed step, use default
        elif a == "last" and i + 1 < len(args):
            i += 1
            opts["last"] = int(args[i])
        elif a.isdigit():
            opts["count"] = int(a)
        i += 1
    # `last N` is shorthand for `step -N:`
    if opts["last"] and opts["step"] is None:
        opts["step"] = {"slice": [-opts["last"], None, None]}
    # Auto-brief: dashboard=brief, traces=full
    if opts["brief"] is None:
        opts["brief"] = opts["mode"] != "traces"
    return opts


def _remote_script(parquet_glob: str, opts: dict) -> str:
    """Build a Python script that outputs JSON for the handler to format."""
    opts_json = json.dumps(opts)
    return textwrap.dedent(f'''\
import glob, json, sys, random, base64, io
import pandas as pd

files = sorted(glob.glob("{parquet_glob}"))
if not files:
    print(json.dumps({{"error": "No completions found."}}))
    sys.exit(0)

opts = json.loads('{opts_json}')
mode = opts["mode"]
step_sel = opts.get("step")  # {{"index": N}} or {{"slice": [start, stop, step]}} or None
count = opts.get("count", 3)
filt = opts.get("filter")
brief = opts.get("brief", True)

def select_files(files, sel):
    """Select files using Python-style index or slice."""
    if sel is None:
        return [files[-1]]
    if "index" in sel:
        idx = sel["index"]
        try:
            return [files[idx]]
        except IndexError:
            return None
    if "slice" in sel:
        s = sel["slice"]
        return files[slice(s[0], s[1], s[2])]
    return [files[-1]]

def step_stats(df):
    d = {{}}
    d["step"] = int(df["step"].iloc[0])
    d["n"] = len(df)
    d["acc_mean"] = float(df["accuracy_reward_func"].mean())
    d["acc_pos"] = int((df["accuracy_reward_func"] == 1).sum())
    d["acc_neg"] = int((df["accuracy_reward_func"] == -1).sum())
    d["fmt_mean"] = float(df["format_reward_func"].mean())
    d["fmt_min"] = float(df["format_reward_func"].min())
    d["fmt_max"] = float(df["format_reward_func"].max())
    if "spectral_reward_func" in df.columns:
        d["spec_mean"] = float(df["spectral_reward_func"].mean())
    d["adv_mean"] = float(df["advantage"].mean())
    d["adv_std"] = float(df["advantage"].std())
    d["comp_len_mean"] = float(df["completion"].str.len().mean())
    return d

def get_samples(df, n, filt, brief):
    if filt == "correct":
        df = df[df["accuracy_reward_func"] == 1.0]
    elif filt == "wrong":
        df = df[df["accuracy_reward_func"] != 1.0]
    if len(df) == 0:
        return []
    rows = df.sample(min(n, len(df)))
    samples = []
    for _, row in rows.iterrows():
        s = {{
            "prompt": str(row["prompt"]),
            "completion": str(row["completion"]),
            "acc": float(row["accuracy_reward_func"]),
            "fmt": float(row["format_reward_func"]),
            "adv": float(row["advantage"]),
        }}
        if "spectral_reward_func" in df.columns:
            s["spec"] = float(row["spectral_reward_func"])
        if brief:
            s["completion"] = s["completion"][:600]
            s["prompt"] = s["prompt"][:200]
        samples.append(s)
    return samples

def render_chart(trend):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    steps = [t["step"] for t in trend]
    acc = [t["acc_pos"] / t["n"] * 100 for t in trend]
    fmt = [t["fmt_mean"] for t in trend]
    has_spec = "spec_mean" in trend[0]
    spec = [t.get("spec_mean", 0) for t in trend] if has_spec else None
    comp_len = [t.get("comp_len_mean", 0) for t in trend]

    n_panels = 3 if has_spec else 2
    fig, axes = plt.subplots(n_panels, 1, figsize=(10, 3 * n_panels), sharex=True)
    fig.patch.set_facecolor("#1a1a2e")
    for ax in axes:
        ax.set_facecolor("#16213e")
        ax.tick_params(colors="#e0e0e0")
        ax.spines["bottom"].set_color("#333")
        ax.spines["left"].set_color("#333")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.yaxis.label.set_color("#e0e0e0")
        ax.xaxis.label.set_color("#e0e0e0")
        ax.title.set_color("#e0e0e0")

    # Smoothing helper
    def smooth(y, w=7):
        if len(y) < w:
            return y
        return np.convolve(y, np.ones(w)/w, mode="valid").tolist()

    smooth_steps = steps[len(steps)-len(smooth(acc)):]

    # Panel 1: Accuracy
    ax = axes[0]
    ax.plot(steps, acc, alpha=0.3, color="#4cc9f0", linewidth=0.8)
    ax.plot(smooth_steps, smooth(acc), color="#4cc9f0", linewidth=2, label="accuracy %")
    ax.set_ylabel("Accuracy %")
    ax.set_ylim(-5, 105)
    ax.axhline(y=50, color="#555", linestyle="--", linewidth=0.5)
    ax.legend(facecolor="#16213e", edgecolor="#333", labelcolor="#e0e0e0")
    ax.set_title(f"GRPO Completions  |  steps {{steps[0]}}-{{steps[-1]}}  |  {{len(trend)}} checkpoints")

    # Panel 2: Format reward + completion length
    ax = axes[1]
    ax.plot(steps, fmt, alpha=0.3, color="#f72585", linewidth=0.8)
    ax.plot(smooth_steps, smooth(fmt), color="#f72585", linewidth=2, label="format reward")
    ax.set_ylabel("Format Reward")
    ax2 = ax.twinx()
    ax2.plot(steps, comp_len, alpha=0.2, color="#7209b7", linewidth=0.8)
    ax2.plot(smooth_steps, smooth(comp_len), color="#7209b7", linewidth=1.5, label="completion len", linestyle="--")
    ax2.set_ylabel("Completion Length", color="#7209b7")
    ax2.tick_params(colors="#7209b7")
    ax2.spines["right"].set_color("#7209b7")
    ax2.spines["top"].set_visible(False)
    ax.legend(loc="upper left", facecolor="#16213e", edgecolor="#333", labelcolor="#e0e0e0")
    ax2.legend(loc="upper right", facecolor="#16213e", edgecolor="#333", labelcolor="#e0e0e0")

    # Panel 3: Spectral reward (if available)
    if has_spec:
        ax = axes[2]
        ax.plot(steps, spec, alpha=0.3, color="#4361ee", linewidth=0.8)
        ax.plot(smooth_steps, smooth(spec), color="#4361ee", linewidth=2, label="spectral reward")
        ax.set_ylabel("Spectral Reward")
        ax.set_xlabel("Step")
        ax.legend(facecolor="#16213e", edgecolor="#333", labelcolor="#e0e0e0")
    else:
        axes[-1].set_xlabel("Step")

    plt.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()

if mode == "stats":
    use_files = select_files(files, step_sel) if step_sel else files
    if use_files is None or len(use_files) == 0:
        print(json.dumps({{"error": f"Index out of range. {{len(files)}} files available."}}))
        sys.exit(0)
    trend = []
    for f in use_files:
        df = pd.read_parquet(f)
        trend.append(step_stats(df))
    chart_b64 = render_chart(trend)
    first, last = trend[0], trend[-1]
    acc_first = first["acc_pos"] / first["n"] * 100
    acc_last = last["acc_pos"] / last["n"] * 100
    caption = f"Steps {{first['step']}}-{{last['step']}} ({{len(trend)}} ckpts)\\n"
    caption += f"Accuracy: {{acc_first:.0f}}% -> {{acc_last:.0f}}%\\n"
    caption += f"Format: {{first['fmt_mean']:.3f}} -> {{last['fmt_mean']:.3f}}"
    if "spec_mean" in first:
        caption += f"\\nSpectral: {{first['spec_mean']:.4f}} -> {{last['spec_mean']:.4f}}"
    print(json.dumps({{"type": "stats", "chart": chart_b64, "caption": caption}}))

else:
    # dashboard or traces — select files, then load
    selected = select_files(files, step_sel)
    if selected is None or len(selected) == 0:
        print(json.dumps({{"error": f"Index out of range. {{len(files)}} files available."}}))
        sys.exit(0)
    # For single-step modes, use first selected file
    df = pd.read_parquet(selected[0])

    result = {{
        "type": mode,
        "stats": step_stats(df),
        "samples": get_samples(df, count, filt, brief),
        "total_steps": len(files),
    }}
    print(json.dumps(result))
''')


def _fmt_stats_header(s: dict) -> str:
    """Format a step stats dict into a compact header."""
    lines = [f"Step {s['step']} -- {s['n']} completions"]
    lines.append(f"  Accuracy:  mean={s['acc_mean']:.2f}  +1={s['acc_pos']}  -1={s['acc_neg']}")
    lines.append(f"  Format:    mean={s['fmt_mean']:.3f}  [{s['fmt_min']:.2f}, {s['fmt_max']:.2f}]")
    if "spec_mean" in s:
        lines.append(f"  Spectral:  mean={s['spec_mean']:.4f}")
    lines.append(f"  Advantage: mean={s['adv_mean']:.3f}  std={s['adv_std']:.3f}")
    return "\n".join(lines)


def _fmt_sample_brief(s: dict) -> str:
    """Format a sample as a brief inline block."""
    tag = "+" if s["acc"] == 1.0 else "-"
    reward = f"acc={s['acc']:.0f} fmt={s['fmt']:.2f}"
    if "spec" in s:
        reward += f" spec={s['spec']:.3f}"
    comp = s["completion"].replace("\n", " ")[:500]
    return f"[{tag}] {reward}\n{comp}"


def _fmt_trace(s: dict, idx: int) -> str:
    """Format a full trace for a separate message."""
    tag = "+" if s["acc"] == 1.0 else "-"
    header = f"[{tag}] acc={s['acc']:.0f} fmt={s['fmt']:.2f}"
    if "spec" in s:
        header += f" spec={s['spec']:.3f}"
    header += f" adv={s['adv']:.3f}"

    # Extract the user portion of the prompt (skip system message)
    prompt = s["prompt"]
    user_start = prompt.find("\nuser\n")
    if user_start >= 0:
        prompt = prompt[user_start + 6:]
    assistant_start = prompt.find("\nassistant\n")
    if assistant_start >= 0:
        prompt = prompt[:assistant_start]
    prompt = prompt.strip()

    parts = [f"--- Trace {idx} {header} ---", f"PROMPT: {prompt}", f"\n{s['completion']}"]
    return "\n".join(parts)


async def completions_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/completions <project> [flags...]"""
    args = context.args or []
    if not args:
        await update.message.reply_text(
            "Usage: /completions <project> [flags...]\n\n"
            "Flags (mix & match):\n"
            "  stats        — reward trend chart (PNG)\n"
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

    timeout = 120 if opts["mode"] == "stats" else 60
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

    if data["type"] == "stats":
        # Send chart as photo
        img_bytes = base64.b64decode(data["chart"])
        await update.message.reply_photo(
            photo=io.BytesIO(img_bytes),
            caption=data.get("caption", ""),
        )

    elif data["type"] == "traces":
        # Stats header first
        header = _fmt_stats_header(data["stats"])
        n_samples = len(data["samples"])
        filt_label = f" ({opts['filter']})" if opts["filter"] else ""
        await update.message.reply_text(
            f"{header}\n\nShowing {n_samples} trace(s){filt_label}:"
        )
        # Each trace as a separate message
        for i, s in enumerate(data["samples"], 1):
            trace = _fmt_trace(s, i)
            await send_long(update, trace)

    else:
        # Dashboard: stats header + brief samples inline
        header = _fmt_stats_header(data["stats"])
        parts = [header, f"\n{len(data['samples'])} samples:"]
        for s in data["samples"]:
            parts.append("")
            parts.append(_fmt_sample_brief(s))
        text = "\n".join(parts)
        await send_long(update, text)


handler = CommandHandler("completions", completions_handler)

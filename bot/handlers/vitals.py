"""
/vitals — project health dashboard with charts or text summary.

Usage:
  /vitals          — 2x2 chart (commits, codebase, issues, tasks)
  /vitals chart    — same as above
  /vitals text     — text-only summary
"""
import io
import logging

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from ..services.vitals import collect_all
from ..services.tg import send_long

logger = logging.getLogger("ourosss")

# Apple-minimal palette
BLUE = "#4A90D9"
GREEN = "#7ED321"
AMBER = "#F5A623"
RED = "#D0021B"
LIGHT_GRAY = "#E5E5E5"
DARK_TEXT = "#333333"


def _style_ax(ax):
    """Apply Apple-minimal styling to an axes."""
    ax.set_facecolor("white")
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors=DARK_TEXT, labelsize=8)
    ax.title.set_color(DARK_TEXT)
    ax.title.set_fontsize(10)
    ax.title.set_fontweight("semibold")
    ax.xaxis.label.set_color(DARK_TEXT)
    ax.yaxis.label.set_color(DARK_TEXT)
    ax.grid(False)


def _render_chart(data: dict) -> io.BytesIO:
    """Render a 2x2 dashboard figure, return as BytesIO PNG."""
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    fig.patch.set_facecolor("white")
    fig.subplots_adjust(hspace=0.35, wspace=0.30)

    for row in axes:
        for ax in row:
            _style_ax(ax)

    # --- Top-left: commits per day (bar chart, last 30 days) ---
    ax = axes[0][0]
    git = data.get("git", {})
    commits = git.get("commits_per_day", [])
    if commits:
        # Take last 30 days
        commits = commits[-30:]
        dates = [c[0] for c in commits]
        counts = [c[1] for c in commits]
        ax.bar(range(len(dates)), counts, color=BLUE, width=0.7)
        # Show sparse x-labels to avoid overlap
        step = max(1, len(dates) // 6)
        ax.set_xticks(range(0, len(dates), step))
        ax.set_xticklabels([dates[i] for i in range(0, len(dates), step)],
                           rotation=30, ha="right", fontsize=7)
    ax.set_title("Commits / Day (last 30d)")
    ax.set_ylabel("commits", fontsize=8)

    # --- Top-right: codebase composition (horizontal bar) ---
    ax = axes[0][1]
    cb = data.get("codebase", {})
    handlers = cb.get("handlers", 0)
    services = cb.get("services", 0)
    total_files = cb.get("total_files", 0)
    other = max(0, total_files - handlers - services)
    labels = ["handlers", "services", "other"]
    values = [handlers, services, other]
    colors = [BLUE, GREEN, LIGHT_GRAY]
    bars = ax.barh(labels, values, color=colors, height=0.5)
    for bar, val in zip(bars, values):
        if val > 0:
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                    str(val), va="center", fontsize=8, color=DARK_TEXT)
    ax.set_title("Codebase Composition")
    ax.set_xlabel("files", fontsize=8)

    # --- Bottom-left: issues (bar: open vs closed) ---
    ax = axes[1][0]
    gh = data.get("github", {})
    open_i = gh.get("open_issues", 0)
    closed_i = gh.get("closed_issues", 0)
    issue_labels = ["open", "closed"]
    issue_vals = [open_i, closed_i]
    issue_colors = [AMBER, GREEN]
    bars = ax.bar(issue_labels, issue_vals, color=issue_colors, width=0.5)
    for bar, val in zip(bars, issue_vals):
        if val > 0:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                    str(val), ha="center", fontsize=9, color=DARK_TEXT)
    ax.set_title("GitHub Issues")
    ax.set_ylabel("count", fontsize=8)

    # --- Bottom-right: hidden (was Team Tasks, removed) ---
    axes[1][1].set_visible(False)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight",
                facecolor="white", edgecolor="none")
    plt.close(fig)
    buf.seek(0)
    return buf


def _format_text(data: dict) -> str:
    """Format vitals data as a plain-text summary."""
    lines = []

    git = data.get("git", {})
    lines.append("Git")
    lines.append(f"  Total commits: {git.get('total_commits', '?')}")
    lines.append(f"  Authors: {', '.join(git.get('authors', []))}")
    lines.append(f"  LOC added: +{git.get('loc_added', '?')}  deleted: -{git.get('loc_deleted', '?')}")
    recent = git.get("commits_per_day", [])[-7:]
    if recent:
        total_7d = sum(c[1] for c in recent)
        lines.append(f"  Last 7 days: {total_7d} commits")

    lines.append("")
    cb = data.get("codebase", {})
    lines.append("Codebase")
    lines.append(f"  Files: {cb.get('total_files', '?')}  LOC: {cb.get('total_loc', '?')}")
    lines.append(f"  Handlers: {cb.get('handlers', '?')}  Services: {cb.get('services', '?')}")

    lines.append("")
    gh = data.get("github", {})
    lines.append("GitHub")
    open_i, closed_i, total_i = gh.get('open_issues', '?'), gh.get('closed_issues', '?'), gh.get('total_issues', '?')
    lines.append(f"  Issues: {open_i} open / {closed_i} closed ({total_i} total)")
    release = gh.get("latest_release")
    if release:
        lines.append(f"  Latest release: {release}")

    return "\n".join(lines)


def _build_caption(data: dict) -> str:
    """Short caption for the chart photo."""
    git = data.get("git", {})
    cb = data.get("codebase", {})
    gh = data.get("github", {})

    parts = []
    parts.append(f"Commits: {git.get('total_commits', '?')}")
    parts.append(f"Files: {cb.get('total_files', '?')}")
    parts.append(f"Issues: {gh.get('open_issues', '?')} open")
    return " | ".join(parts)


async def vitals_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/vitals [text|chart] — project health dashboard."""
    args = context.args or []
    mode = args[0].lower() if args else "chart"

    if mode not in ("text", "chart"):
        await update.message.reply_text("Usage: /vitals [text|chart]")
        return

    await update.message.reply_text("Collecting vitals...")

    try:
        data = await collect_all()
    except Exception as e:
        logger.error(f"Vitals collection failed: {e}")
        await update.message.reply_text(f"Error collecting vitals: {e}")
        return

    if mode == "text":
        text = _format_text(data)
        await send_long(update, text)
    else:
        buf = _render_chart(data)
        caption = _build_caption(data)
        await update.message.reply_photo(photo=buf, caption=caption)


handler = CommandHandler("vitals", vitals_handler)

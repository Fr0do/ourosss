import re
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from ..services.config import PROJECTS
from ..services.ssh import ssh_tmux_capture
from ..services.tg import require_project


async def metrics_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/metrics <project> [n=50] — extract training metrics from recent tmux output."""
    name, err = require_project(context.args or [], "/metrics <project> [lines]")
    if err:
        await update.message.reply_text(err, parse_mode="Markdown")
        return

    args = context.args
    n = int(args[1]) if len(args) > 1 else 50
    proj = PROJECTS[name]
    raw = await ssh_tmux_capture(proj["remote"], proj["tmux"], lines=n)

    if not raw.strip():
        await update.message.reply_text(f"No output from *{name}*.", parse_mode="Markdown")
        return

    metric_patterns = re.compile(
        r"(loss|accuracy|acc|reward|lr|learning.rate|step|epoch|eval|train|grad.norm"
        r"|perplexity|ppl|f1|bleu|rouge|score|metric|val)"
        r".*[:=].*\d",
        re.IGNORECASE,
    )

    metric_lines = []
    for line in raw.split("\n"):
        line = line.strip()
        if metric_patterns.search(line):
            metric_lines.append(line)

    if not metric_lines:
        progress = re.compile(r"\d+[/|]\d+|\d+\.\d{2,}")
        metric_lines = [l.strip() for l in raw.split("\n") if progress.search(l)]

    if not metric_lines:
        await update.message.reply_text(
            f"No metrics found in last {n} lines of *{name}*. Try `/logs {name}`.",
            parse_mode="Markdown",
        )
        return

    output = "\n".join(metric_lines[-15:])
    if len(output) > 3900:
        output = output[-3900:]

    await update.message.reply_text(
        f"*{name}* metrics:\n```\n{output}\n```",
        parse_mode="Markdown",
    )


handler = CommandHandler("metrics", metrics_handler)

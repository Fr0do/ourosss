"""
/crashlog <project> [lines] — dump tmux scrollback for crash debugging.

Captures up to N screens of history (default 2000 lines), saves to a
timestamped file on remote, and sends the last portion via Telegram.
"""
import re
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from ..services.config import PROJECTS
from ..services.ssh import ssh_tmux_dump
from ..services.tg import require_project, send_long


def _extract_crash_context(text: str, tail: int = 150) -> str:
    """Extract the most useful portion: last N lines, prioritising tracebacks."""
    lines = text.splitlines()
    if not lines:
        return "(empty)"

    tb_start = None
    for i in range(len(lines) - 1, -1, -1):
        if re.match(r"Traceback \(most recent call last\)", lines[i]):
            tb_start = i
            break

    if tb_start is not None:
        start = max(0, tb_start - 20)
        context = lines[start:]
    else:
        context = lines[-tail:]

    return "\n".join(context)


async def crashlog_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/crashlog <project> [lines=2000] — dump tmux scrollback for debugging."""
    name, err = require_project(context.args or [], "/crashlog <project> [lines]")
    if err:
        await update.message.reply_text(err, parse_mode="Markdown")
        return

    args = context.args
    history_lines = int(args[1]) if len(args) > 1 else 2000
    proj = PROJECTS[name]
    host = proj["remote"]
    session = proj["tmux"]

    await update.message.reply_text(f"Capturing {history_lines} lines from *{name}* tmux...", parse_mode="Markdown")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_path = f"{proj['path']}/crashlogs/{ts}.log"

    text = await ssh_tmux_dump(host, session, history_lines=history_lines, save_path=save_path)

    if not text.strip():
        await update.message.reply_text(f"No output from tmux session `{session}`.", parse_mode="Markdown")
        return

    total_lines = len(text.splitlines())
    crash_context = _extract_crash_context(text)

    has_traceback = "Traceback (most recent call last)" in crash_context

    header = f"*{name}* crashlog — {total_lines} lines captured"
    if has_traceback:
        header += " (traceback found)"
    header += f"\nSaved: `{save_path}`"

    await update.message.reply_text(header, parse_mode="Markdown")
    await send_long(update, f"```\n{crash_context}\n```", parse_mode="Markdown")

    if has_traceback:
        error_lines = [l for l in crash_context.splitlines() if re.match(r"^\w*(Error|Exception|Fault)", l)]
        if error_lines:
            await update.message.reply_text(f"Error: `{error_lines[-1]}`", parse_mode="Markdown")


handler = CommandHandler("crashlog", crashlog_handler)

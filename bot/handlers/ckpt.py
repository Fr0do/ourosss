from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from ..services.config import PROJECTS
from ..services.ssh import ssh_exec
from ..services.tg import require_project


async def ckpt_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/ckpt <project> — list checkpoints with step, size, date."""
    name, err = require_project(context.args or [], "/ckpt <project>")
    if err:
        await update.message.reply_text(err, parse_mode="Markdown")
        return

    proj = PROJECTS[name]
    cmd = (
        f"cd {proj['path']} && "
        f"find . -maxdepth 3 -type d -name 'checkpoint-*' -o -name 'step_*' -o -name 'epoch_*' | "
        f"head -20 | while read d; do "
        f"  size=$(du -sh \"$d\" 2>/dev/null | cut -f1); "
        f"  date=$(stat -c '%y' \"$d\" 2>/dev/null | cut -d. -f1 || stat -f '%Sm' \"$d\" 2>/dev/null); "
        f"  echo \"$d  $size  $date\"; "
        f"done | sort -t- -k2 -n 2>/dev/null || echo 'No checkpoints found.'"
    )
    output = await ssh_exec(proj["remote"], cmd, timeout=30)

    if not output.strip():
        output = "No checkpoints found."

    if len(output) > 3900:
        output = output[-3900:]

    await update.message.reply_text(
        f"*{name}* checkpoints:\n```\n{output}\n```",
        parse_mode="Markdown",
    )


handler = CommandHandler("ckpt", ckpt_handler)

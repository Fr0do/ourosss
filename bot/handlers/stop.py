from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from ..services.config import PROJECTS
from ..services.ssh import ssh_exec
from ..services.tg import require_project


async def stop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/stop <project> — send Ctrl-C to project's tmux session."""
    name, err = require_project(context.args or [], "/stop <project>")
    if err:
        await update.message.reply_text(err, parse_mode="Markdown")
        return

    proj = PROJECTS[name]
    await ssh_exec(proj["remote"], f"tmux send-keys -t {proj['tmux']} C-c")
    await update.message.reply_text(f"Sent `Ctrl-C` to *{name}* (`{proj['tmux']}`)", parse_mode="Markdown")


handler = CommandHandler("stop", stop_handler)

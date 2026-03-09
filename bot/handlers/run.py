from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from ..services.config import PROJECTS
from ..services.ssh import ssh_tmux_send
from ..services.tg import require_project


async def run_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/run <project> [custom command]"""
    name, err = require_project(context.args or [], "/run <project> [command]")
    if err:
        await update.message.reply_text(err, parse_mode="Markdown")
        return

    proj = PROJECTS[name]
    args = context.args
    custom_cmd = " ".join(args[1:]) if len(args) > 1 else proj["train_cmd"]
    full_cmd = f"conda activate {proj['conda']} && cd {proj['path']} && {custom_cmd}"

    result = await ssh_tmux_send(proj["remote"], proj["tmux"], full_cmd)
    await update.message.reply_text(
        f"Sent to *{name}* (`{proj['tmux']}`):\n`{custom_cmd}`\n\nUse `/logs {name}` to monitor.",
        parse_mode="Markdown",
    )


handler = CommandHandler("run", run_handler)

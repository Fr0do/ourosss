"""OuroSSS — Claude Research Agent Bot."""
import logging
from telegram import Update, BotCommand
from telegram.ext import Application, ContextTypes, CommandHandler

from .services.config import TELEGRAM_TOKEN, AUTHORIZED_USERS, PROJECTS
from .services.ssh import gpu_status
from .handlers.status import handler as status_handler
from .handlers.run import handler as run_handler
from .handlers.stop import handler as stop_handler
from .handlers.logs import handler as logs_handler
from .handlers.note import note_cmd, task_cmd
from .handlers.update import handler as update_handler
from .handlers.ckpt import handler as ckpt_handler
from .handlers.disk import handler as disk_handler, schedule_watchdog
from .handlers.sync import handler as sync_handler
from .handlers.metrics import handler as metrics_handler
from .handlers.completions import handler as completions_handler
from .handlers.crashlog import handler as crashlog_handler

LOG_FILE = "bot.log"
logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(LOG_FILE),
    ],
)
logger = logging.getLogger("ouroboros")



async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/start — show user ID and available commands."""
    uid = update.effective_user.id
    projects_list = ", ".join(PROJECTS.keys())
    await update.message.reply_text(
        f"*OuroSSS* | Claude Research Agent\n"
        f"User: `{uid}` | Projects: {projects_list}\n\n"
        f"*Training*\n"
        f"/status — project states + GPU\n"
        f"/run _project_ \\[cmd] — execute in tmux\n"
        f"/stop _project_ — send Ctrl\\-C\n"
        f"/logs _project_ \\[n] — tail output\n"
        f"/metrics _project_ — extract training metrics\n"
        f"/ckpt _project_ — list checkpoints\n"
        f"/completions _project_ — latest step dashboard\n"
        f"/completions _project_ stats — accuracy trend chart\n"
        f"/completions _project_ traces \\[N] — full traces\n"
        f"/completions _project_ step _IDX_ — python index/slice\n"
        f"  _e\\.g\\. 0, \\-1, \\-3:, 0:5, ::2_\n\n"
        f"*Infrastructure*\n"
        f"/gpu — nvidia\\-smi all remotes\n"
        f"/disk — NFS usage \\(cached, hourly alert\\)\n"
        f"/disk scan — full dua rescan\n"
        f"/disk me — your directory breakdown\n"
        f"/sync _project_ \\[subpath] — rsync to local\n\n"
        f"*Notes*\n"
        f"/note _project_ _text_ — log to Notion\n"
        f"/task _text_ — add to backlog\n\n"
        f"*System*\n"
        f"/crashlog _project_ — dump tmux scrollback on crash\n"
        f"/update — git pull \\+ restart\n"
        f"/help — this message",
        parse_mode="MarkdownV2",
    )


async def gpu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/gpu — show GPU status from all remotes."""
    hosts_seen = set()
    lines = []
    for proj in PROJECTS.values():
        h = proj["remote"]
        if h not in hosts_seen:
            hosts_seen.add(h)
            gpu = await gpu_status(h)
            lines.append(f"*{h}*:\n```\n{gpu}\n```")

    await update.message.reply_text("\n".join(lines) or "No GPU info.", parse_mode="Markdown")


async def post_init(app: Application):
    """Set bot commands and start background jobs."""
    # Schedule disk watchdog for all authorized users
    if AUTHORIZED_USERS:
        for uid in AUTHORIZED_USERS:
            schedule_watchdog(app.job_queue, chat_id=uid)
        logger.info("Disk watchdog scheduled (hourly)")

    await app.bot.set_my_commands([
        BotCommand("help", "Show all commands"),
        BotCommand("status", "Project states + GPU"),
        BotCommand("run", "Run command on project"),
        BotCommand("stop", "Stop project (Ctrl-C)"),
        BotCommand("logs", "Tail tmux logs"),
        BotCommand("note", "Log note to Notion"),
        BotCommand("task", "Add to backlog"),
        BotCommand("gpu", "GPU utilization"),
        BotCommand("update", "Git pull + restart"),
        BotCommand("ckpt", "List checkpoints"),
        BotCommand("disk", "Workspace disk usage"),
        BotCommand("sync", "Rsync results to local"),
        BotCommand("metrics", "Training metrics summary"),
        BotCommand("completions", "Analyse GRPO completions"),
        BotCommand("crashlog", "Dump tmux scrollback for debugging"),
    ])


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).post_init(post_init).build()

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", start_handler))
    app.add_handler(CommandHandler("gpu", gpu_handler))
    app.add_handler(status_handler)
    app.add_handler(run_handler)
    app.add_handler(stop_handler)
    app.add_handler(logs_handler)
    app.add_handler(note_cmd)
    app.add_handler(task_cmd)
    app.add_handler(update_handler)
    app.add_handler(ckpt_handler)
    app.add_handler(disk_handler)
    app.add_handler(sync_handler)
    app.add_handler(metrics_handler)
    app.add_handler(completions_handler)
    app.add_handler(crashlog_handler)

    logger.info("OuroSSS bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

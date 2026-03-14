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
from .handlers.update import handler as update_handler
from .handlers.ckpt import handler as ckpt_handler
from .handlers.disk import handler as disk_handler, schedule_watchdog
from .handlers.sync import handler as sync_handler
from .handlers.metrics import handler as metrics_handler
from .handlers.completions import handler as completions_handler
from .handlers.crashlog import handler as crashlog_handler
from .handlers.vitals import handler as vitals_handler
from .handlers.feature import handler as feature_handler
from .handlers.page import handler as page_handler
from .handlers.qr import handler as qr_handler, photo_handler as qr_photo_handler
from .handlers.eval import handler as eval_handler
from .handlers.research import handler as research_handler

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
        f"*OuroSSS* \\| Claude Research Agent\n"
        f"User: `{uid}` \\| Projects: {projects_list}\n\n"
        f"*Training \\& Monitoring*\n"
        f"/status — project states \\+ GPU\n"
        f"/run _project_ \\[cmd] — execute in tmux\n"
        f"/stop _project_ — send Ctrl\\-C\n"
        f"/logs _project_ \\[n] — tail output\n"
        f"/metrics _project_ — extract training metrics\n"
        f"/ckpt _project_ — list checkpoints\n"
        f"/completions _project_ — latest step dashboard\n"
        f"/completions _project_ stats — accuracy trend chart\n"
        f"/completions _project_ baseline — full analysis report\n"
        f"/completions _project_ traces \\[N] — full traces\n"
        f"/completions _project_ step _IDX_ — python index/slice\n"
        f"  _e\\.g\\. 0, \\-1, \\-3:, 0:5, ::2_\n"
        f"/gpu — nvidia\\-smi all remotes\n\n"
        f"*Research*\n"
        f"/research log _project type title_ \\| _summary_ \\[\\| _metrics_] — log entry\n"
        f"/research list \\[project] \\[limit] — recent entries\n"
        f"/research sync — sync status\n"
        f"/eval push _ckpt step bench topo acc fmt len_ — push to Notion\n"
        f"/eval list \\[limit] — recent eval results\n"
        f"/eval summary — latest per benchmark\n\n"
        f"*Infrastructure*\n"
        f"/disk — NFS usage \\(cached, alert at \\<1\\.5T free\\)\n"
        f"/disk scan — full dua rescan\n"
        f"/disk me — your directory breakdown\n"
        f"/sync _project_ \\[subpath] — rsync to local\n"
        f"/vitals — project health dashboard \\(chart\\)\n"
        f"/vitals text — text\\-only summary\n\n"
        f"*Artifacts*\n"
        f"/feature _description_ — file GitHub issue from chat\n"
        f"/page — update project page with current vitals\n"
        f"/page _text_ — add status entry to timeline\n"
        f"/page finding _title_ \\| _body_ — tagged entry\n"
        f"/qr _text_ — generate a QR code\n"
        f"  _photo\\+caption_ — QR mosaic blend\n\n"
        f"*System*\n"
        f"/update — git pull \\+ restart\n"
        f"/crashlog _project_ — dump tmux scrollback on crash\n"
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
        BotCommand("metrics", "Training metrics summary"),
        BotCommand("ckpt", "List checkpoints"),
        BotCommand("completions", "Analyse GRPO completions"),
        BotCommand("gpu", "GPU utilization"),
        BotCommand("research", "Research log (Notion)"),
        BotCommand("eval", "Eval tracking (Notion)"),
        BotCommand("disk", "NFS usage (alert at <1.5T free)"),
        BotCommand("sync", "Rsync results to local"),
        BotCommand("vitals", "Project health dashboard"),
        BotCommand("feature", "File a feature request"),
        BotCommand("page", "Update project page"),
        BotCommand("qr", "Generate QR code / mosaic"),
        BotCommand("update", "Git pull + restart"),
        BotCommand("crashlog", "Dump tmux scrollback for debugging"),
    ])


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """Global error handler — log and notify user instead of silent failure."""
    logger.error("Unhandled exception:", exc_info=context.error)
    if isinstance(update, Update) and update.message:
        msg = str(context.error)[:200]
        try:
            await update.message.reply_text(f"Error: `{msg}`", parse_mode="Markdown")
        except Exception:
            pass


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).post_init(post_init).build()
    app.add_error_handler(error_handler)

    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help", start_handler))
    app.add_handler(CommandHandler("gpu", gpu_handler))
    app.add_handler(status_handler)
    app.add_handler(run_handler)
    app.add_handler(stop_handler)
    app.add_handler(logs_handler)
    app.add_handler(update_handler)
    app.add_handler(ckpt_handler)
    app.add_handler(disk_handler)
    app.add_handler(sync_handler)
    app.add_handler(metrics_handler)
    app.add_handler(completions_handler)
    app.add_handler(crashlog_handler)
    app.add_handler(vitals_handler)
    app.add_handler(feature_handler)
    app.add_handler(page_handler)
    app.add_handler(qr_handler)
    app.add_handler(qr_photo_handler)
    app.add_handler(eval_handler)
    app.add_handler(research_handler)

    logger.info("OuroSSS bot starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

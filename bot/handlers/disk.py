import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, JobQueue
from ..services.disk_state import (
    load_state, refresh_df, refresh_dua, refresh_my_usage,
    format_report, format_my_report, WARN_PERCENT,
)

logger = logging.getLogger("ouroboros")

CHECK_INTERVAL_SECONDS = 3600  # hourly


async def disk_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/disk — cached stats. /disk scan — full rescan. /disk me — your dirs."""
    args = context.args or []
    sub = args[0] if args else ""

    if sub == "scan":
        top_n = int(args[1]) if len(args) > 1 else 20
        msg = await update.message.reply_text("Starting dua scan (may take minutes)...")
        async def _scan():
            await refresh_df()
            state = await refresh_dua(top_n)
            report = format_report(state)
            await msg.edit_text(report, parse_mode="Markdown")

        asyncio.create_task(_scan())
        return

    if sub == "me":
        msg = await update.message.reply_text("Scanning your directory...")

        async def _my_scan():
            state = await refresh_my_usage()
            report = format_my_report(state)
            await msg.edit_text(report, parse_mode="Markdown")

        asyncio.create_task(_my_scan())
        return

    # Default: quick df refresh + cached dua
    state = await refresh_df()
    report = format_report(state)
    await update.message.reply_text(report, parse_mode="Markdown")


async def _disk_watchdog(context: ContextTypes.DEFAULT_TYPE):
    """Hourly: refresh df, run dua if critical, alert if bad."""
    try:
        state = await refresh_df()
    except Exception as e:
        logger.error(f"Disk watchdog df failed: {e}")
        return

    pct = state.get("percent")
    if pct is None:
        return

    # Auto-refresh dua breakdown when critical
    if pct >= WARN_PERCENT:
        try:
            state = await refresh_dua(top_n=20)
        except Exception as e:
            logger.error(f"Disk watchdog dua failed: {e}")

    if pct < WARN_PERCENT:
        return

    report = format_report(state)
    chat_id = context.job.data
    await context.bot.send_message(chat_id=chat_id, text=report, parse_mode="Markdown")


def schedule_watchdog(job_queue: JobQueue | None, chat_id: int):
    if job_queue is None:
        logger.warning("JobQueue unavailable — install python-telegram-bot[job-queue]")
        return
    job_queue.run_repeating(
        _disk_watchdog,
        interval=CHECK_INTERVAL_SECONDS,
        first=60,
        data=chat_id,
        name="disk_watchdog",
    )


handler = CommandHandler("disk", disk_handler)

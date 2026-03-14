import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler, JobQueue
from ..services.disk_state import (
    refresh_df, refresh_dua, refresh_my_usage,
    format_report, format_my_report, WARN_FREE_TB, parse_size_tb,
    _trend_line,
)

logger = logging.getLogger("ouroboros")

CHECK_INTERVAL_SECONDS = 21600  # every 6 hours


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
    """Every 6h: refresh df and alert if free space < WARN_FREE_TB."""
    try:
        state = await refresh_df()
    except Exception as e:
        logger.error(f"Disk watchdog df failed: {e}")
        return

    avail = state.get("avail")
    if avail is None:
        return

    free_tb = parse_size_tb(avail)
    if free_tb >= WARN_FREE_TB:
        return

    pct = state.get("percent", "?")
    used = state.get("used", "?")
    total = state.get("total", "?")
    trend = _trend_line(state)
    trend_part = f"\n{trend}" if trend else ""

    if free_tb < 0.5:
        emoji = "🔴"
        level = "CRITICAL"
    else:
        emoji = "🟡"
        level = "WARNING"

    msg = (
        f"{emoji} *Disk {level}* — only {avail} free\n"
        f"{used} used / {total} total ({pct}% full)"
        f"{trend_part}"
    )

    chat_id = context.job.data
    await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="Markdown")


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

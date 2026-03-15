"""
/page — update the ouroboros project page with current vitals.

Usage:
  /page                       — refresh metrics only
  /page <title>               — add status entry + refresh
  /page <title> | <body>      — add entry with description
  /page finding <title> | ... — tag as finding (default: status)
  /page milestone <title> ... — tag as milestone
"""
import logging

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from ..services.tg import authorized
from ..services.page import update_page

logger = logging.getLogger("ourosss")

VALID_TAGS = {"status", "finding", "milestone"}


@authorized
async def page_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/page — update project page, optionally add a status entry."""
    text = " ".join(context.args) if context.args else ""

    status_entry = None
    if text:
        # Parse optional tag prefix
        tag = "status"
        words = text.split(None, 1)
        if words[0].lower() in VALID_TAGS:
            tag = words[0].lower()
            text = words[1] if len(words) > 1 else ""

        # Split title | body
        if "|" in text:
            title, body = text.split("|", 1)
            title = title.strip()
            body = body.strip()
        else:
            title = text.strip()
            body = ""

        if title:
            status_entry = {"title": title, "body": body, "tag": tag}

    if status_entry:
        msg = await update.message.reply_text(
            f"Adding: {status_entry['title']}\nUpdating page..."
        )
    else:
        msg = await update.message.reply_text("Updating project page...")

    try:
        result = await update_page(status_entry=status_entry)
    except Exception as e:
        logger.error(f"/page failed: {e}")
        await msg.edit_text(f"Error updating page: {e}")
        return

    await msg.edit_text(result)


handler = CommandHandler("page", page_handler)

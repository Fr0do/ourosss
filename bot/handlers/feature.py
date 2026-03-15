"""
/feature — file a GitHub issue from Telegram chat.

Usage:
  /feature <description>  — create a [feat] issue on Fr0do/ourosss
"""
import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from ..services.config import GH_BIN
from ..services.tg import authorized

logger = logging.getLogger("ourosss")

REPO = "Fr0do/ourosss"


def _make_title(description: str, max_len: int = 60) -> str:
    """Build issue title: [feat] + first ~max_len chars, truncated at word boundary."""
    if len(description) <= max_len:
        return f"[feat] {description}"
    truncated = description[:max_len].rsplit(" ", 1)[0]
    return f"[feat] {truncated}"


def _make_body(description: str) -> str:
    """Build structured issue body."""
    return (
        f"## Motivation\n\n"
        f"{description}\n\n"
        f"## Status\n\n"
        f"Filed via Telegram /feature command.\n"
        f"Label: `auto-dev` — awaiting pickup by a terminal agent."
    )


@authorized
async def feature_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/feature <description> — create a GitHub issue."""
    args = context.args or []
    if not args:
        await update.message.reply_text(
            "Usage: `/feature <description>`", parse_mode="Markdown"
        )
        return

    description = " ".join(args)
    title = _make_title(description)
    body = _make_body(description)

    await update.message.reply_text("Creating GitHub issue...")

    try:
        proc = await asyncio.create_subprocess_exec(
            GH_BIN, "issue", "create",
            "--repo", REPO,
            "--title", title,
            "--body", body,
            "--label", "auto-dev",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
    except FileNotFoundError:
        await update.message.reply_text("Error: `gh` CLI not found on this host.")
        return

    if proc.returncode != 0:
        err = stderr.decode().strip()
        logger.error(f"/feature gh failed (rc={proc.returncode}): {err}")
        await update.message.reply_text(f"GitHub CLI error:\n```\n{err}\n```", parse_mode="Markdown")
        return

    url = stdout.decode().strip()
    await update.message.reply_text(f"Issue created: {url}")


handler = CommandHandler("feature", feature_handler)

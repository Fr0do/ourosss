"""
/research — collaborator-facing research log via Notion.

Usage:
  /research log <project> <type> <title> | <summary> [| <metrics>]
  /research list [project] [limit]
  /research sync — show pending sync status
"""
import logging

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from ..services.tg import authorized, send_long
from ..services.notion import (
    push_research_log,
    get_research_log,
    format_research_log,
    RESEARCH_PROJECTS,
    RESEARCH_TYPES,
)
from ..services.config import NOTION_SECRET, NOTION_RESEARCH_DB_ID

logger = logging.getLogger("ouroboros")

USAGE = (
    "*Usage:*\n"
    "`/research log <project> <type> <title> | <summary> [| <metrics>]`\n"
    "`/research list [project] [limit]`\n"
    "`/research sync`\n\n"
    f"Projects: {', '.join(sorted(RESEARCH_PROJECTS))}\n"
    f"Types: {', '.join(sorted(RESEARCH_TYPES))}"
)


def _check_notion() -> str | None:
    """Return an error message if research log Notion DB is not configured, else None."""
    if not NOTION_SECRET or not NOTION_RESEARCH_DB_ID:
        return "Research log not configured. Set NOTION_SECRET and NOTION_RESEARCH_DB_ID in .env."
    return None


@authorized
async def research_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/research — research log tracking."""
    args = context.args or []
    if not args:
        await update.message.reply_text(USAGE, parse_mode="Markdown")
        return

    subcmd = args[0].lower()

    if subcmd == "log":
        await _log(update, context)
    elif subcmd == "list":
        await _list(update, args[1:])
    elif subcmd == "sync":
        await _sync(update)
    else:
        await update.message.reply_text(USAGE, parse_mode="Markdown")


async def _log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Parse and push a research log entry."""
    err = _check_notion()
    if err:
        await update.message.reply_text(err)
        return

    # Reconstruct full text after "log" subcommand, then split on |
    raw = update.message.text or ""
    # Strip the command prefix (e.g. "/research log ") and split on |
    after_cmd = raw.split(None, 2)  # ["/research", "log", "rest..."]
    if len(after_cmd) < 3:
        await update.message.reply_text(
            "Need: `/research log <project> <type> <title> | <summary> [| <metrics>]`",
            parse_mode="Markdown",
        )
        return

    rest = after_cmd[2]
    parts = [p.strip() for p in rest.split("|")]

    # First part contains: <project> <type> <title>
    head = parts[0].split(None, 2)
    if len(head) < 3:
        await update.message.reply_text(
            "Need: `/research log <project> <type> <title> | <summary> [| <metrics>]`",
            parse_mode="Markdown",
        )
        return

    project, type_, title = head[0], head[1], head[2]

    if project not in RESEARCH_PROJECTS:
        await update.message.reply_text(
            f"Unknown project. Options: {', '.join(sorted(RESEARCH_PROJECTS))}"
        )
        return

    if type_ not in RESEARCH_TYPES:
        await update.message.reply_text(
            f"Unknown type. Options: {', '.join(sorted(RESEARCH_TYPES))}"
        )
        return

    if len(parts) < 2 or not parts[1]:
        await update.message.reply_text("Summary is required after `|`.", parse_mode="Markdown")
        return

    summary = parts[1]
    metrics = parts[2] if len(parts) > 2 else ""

    try:
        result = push_research_log(
            project=project,
            type=type_,
            title=title,
            summary=summary,
            metrics=metrics,
        )
    except Exception as e:
        logger.error(f"/research log failed: {e}")
        await update.message.reply_text(f"Notion error: {e}")
        return

    if result:
        await update.message.reply_text(
            f"Logged: *{title}*\n{project} | {type_}", parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("Failed to save (Notion returned None).")


async def _list(update: Update, args: list[str]):
    """List recent research log entries."""
    err = _check_notion()
    if err:
        await update.message.reply_text(err)
        return

    project = None
    limit = 10

    for arg in args:
        if arg in RESEARCH_PROJECTS:
            project = arg
        else:
            try:
                limit = int(arg)
            except ValueError:
                pass

    try:
        entries = get_research_log(project=project, limit=limit)
    except Exception as e:
        logger.error(f"/research list failed: {e}")
        await update.message.reply_text(f"Notion error: {e}")
        return

    text = format_research_log(entries)
    await send_long(update, text, parse_mode="Markdown")


async def _sync(update: Update):
    """Show sync status — placeholder for future push-on-commit integration."""
    err = _check_notion()
    if err:
        await update.message.reply_text(err)
        return

    try:
        entries = get_research_log(limit=5)
    except Exception as e:
        logger.error(f"/research sync failed: {e}")
        await update.message.reply_text(f"Notion error: {e}")
        return

    count = len(entries)
    latest = entries[0]["date"] if entries else "none"
    await update.message.reply_text(
        f"Research log: *{count}* recent entries (showing last 5)\nLatest: {latest}\n\n"
        f"Auto-sync not yet configured — use `/research log` to push manually.",
        parse_mode="Markdown",
    )


handler = CommandHandler("research", research_handler)

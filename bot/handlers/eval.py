"""
/eval -- s_cot evaluation tracking via Notion.

Usage:
  /eval push <checkpoint> <step> <benchmark> <topology> <accuracy> <valid_fmt> <avg_len> [model] [notes]
  /eval list [limit]
  /eval summary
"""
import logging

from telegram import Update
from telegram.ext import ContextTypes, CommandHandler

from ..services.tg import authorized, send_long
from ..services.notion import (
    push_eval_result,
    get_recent_evals,
    format_eval_summary,
    BENCHMARKS,
    TOPOLOGIES,
    MODELS,
)
from ..services.config import NOTION_SECRET, NOTION_DB_ID

logger = logging.getLogger("ouroboros")

DEFAULT_MODEL = "LFM2.5-1.2B-Thinking"

USAGE = (
    "*Usage:*\n"
    "`/eval push <ckpt> <step> <bench> <topo> <acc> <fmt> <len> [model] [notes]`\n"
    "`/eval list [limit]`\n"
    "`/eval summary`\n\n"
    f"Benchmarks: {', '.join(sorted(BENCHMARKS))}\n"
    f"Topologies: {', '.join(sorted(TOPOLOGIES))}"
)


def _check_notion() -> str | None:
    """Return an error message if Notion is not configured, else None."""
    if not NOTION_SECRET or not NOTION_DB_ID:
        return "Notion not configured. Set NOTION_SECRET and NOTION_DB_ID in .env."
    return None


@authorized
async def eval_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/eval — s_cot eval tracking."""
    args = context.args or []
    if not args:
        await update.message.reply_text(USAGE, parse_mode="Markdown")
        return

    subcmd = args[0].lower()

    if subcmd == "push":
        await _push(update, args[1:])
    elif subcmd == "list":
        await _list(update, args[1:])
    elif subcmd == "summary":
        await _summary(update)
    else:
        await update.message.reply_text(USAGE, parse_mode="Markdown")


async def _push(update: Update, args: list[str]):
    """Push an eval result to Notion."""
    err = _check_notion()
    if err:
        await update.message.reply_text(err)
        return

    # Required: checkpoint, step, benchmark, topology, accuracy, valid_fmt, avg_len
    if len(args) < 7:
        await update.message.reply_text(
            "Need at least 7 args: checkpoint step benchmark topology accuracy valid_fmt avg_len\n"
            f"Example: `/eval push checkpoint-500 500 json_pathfinder mixed 0.85 0.95 180`",
            parse_mode="Markdown",
        )
        return

    checkpoint = args[0]
    try:
        step = int(args[1])
    except ValueError:
        await update.message.reply_text("Step must be an integer.")
        return

    benchmark = args[2]
    if benchmark not in BENCHMARKS:
        await update.message.reply_text(f"Unknown benchmark. Options: {', '.join(sorted(BENCHMARKS))}")
        return

    topology = args[3]
    if topology not in TOPOLOGIES:
        await update.message.reply_text(f"Unknown topology. Options: {', '.join(sorted(TOPOLOGIES))}")
        return

    try:
        accuracy = float(args[4])
        valid_fmt = float(args[5])
        avg_len = float(args[6])
    except ValueError:
        await update.message.reply_text("accuracy, valid_fmt, avg_len must be numbers.")
        return

    model = args[7] if len(args) > 7 else DEFAULT_MODEL
    if model not in MODELS:
        await update.message.reply_text(f"Unknown model. Options: {', '.join(sorted(MODELS))}")
        return

    notes = " ".join(args[8:]) if len(args) > 8 else ""

    try:
        result = push_eval_result(
            checkpoint=checkpoint,
            step=step,
            benchmark=benchmark,
            topology=topology,
            accuracy=accuracy,
            valid_format_pct=valid_fmt,
            avg_completion_len=avg_len,
            model=model,
            notes=notes,
        )
    except Exception as e:
        logger.error(f"/eval push failed: {e}")
        await update.message.reply_text(f"Notion error: {e}")
        return

    if result:
        await update.message.reply_text(f"Saved: {checkpoint} | {benchmark} | acc={accuracy}")
    else:
        await update.message.reply_text("Failed to save (Notion returned None).")


async def _list(update: Update, args: list[str]):
    """List recent eval results."""
    err = _check_notion()
    if err:
        await update.message.reply_text(err)
        return

    limit = 10
    if args:
        try:
            limit = int(args[0])
        except ValueError:
            pass

    try:
        results = get_recent_evals(limit=limit)
    except Exception as e:
        logger.error(f"/eval list failed: {e}")
        await update.message.reply_text(f"Notion error: {e}")
        return

    text = format_eval_summary(results)
    await send_long(update, text, parse_mode="Markdown")


async def _summary(update: Update):
    """Show latest result per benchmark."""
    err = _check_notion()
    if err:
        await update.message.reply_text(err)
        return

    try:
        results = get_recent_evals(limit=50)
    except Exception as e:
        logger.error(f"/eval summary failed: {e}")
        await update.message.reply_text(f"Notion error: {e}")
        return

    # Keep only the latest entry per benchmark
    seen = {}
    for r in results:
        key = r["benchmark"]
        if key and key not in seen:
            seen[key] = r

    latest = list(seen.values())
    text = format_eval_summary(latest)
    if latest:
        text = text.replace("Recent Eval Results", "Latest per Benchmark")
    await send_long(update, text, parse_mode="Markdown")


handler = CommandHandler("eval", eval_handler)

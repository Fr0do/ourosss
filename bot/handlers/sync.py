import asyncio
from telegram import Update
from telegram.ext import ContextTypes, CommandHandler
from ..services.config import PROJECTS
from ..services.tg import require_project


async def sync_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """/sync <project> [subpath] — rsync results from remote to local."""
    name, err = require_project(context.args or [], "/sync <project> [subpath]")
    if err:
        await update.message.reply_text(err, parse_mode="Markdown")
        return

    proj = PROJECTS[name]
    local = proj.get("local")
    if not local:
        await update.message.reply_text(f"No local path configured for *{name}*.", parse_mode="Markdown")
        return

    args = context.args
    subpath = args[1] if len(args) > 1 else ""
    remote_path = f"{proj['path']}/{subpath}".rstrip("/") + "/"
    local_path = f"{local}/{subpath}".rstrip("/") + "/"
    src = f"{proj['remote']}:{remote_path}"

    await update.message.reply_text(f"Syncing `{src}` → `{local_path}` ...", parse_mode="Markdown")

    proc = await asyncio.create_subprocess_exec(
        "rsync", "-avz", "--progress", "--exclude", "__pycache__",
        "--exclude", ".git", "--exclude", "*.pyc",
        src, local_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=300)
    except asyncio.TimeoutError:
        proc.kill()
        await update.message.reply_text("Sync timed out (5 min limit).")
        return

    out = stdout.decode().strip()
    summary_lines = [l for l in out.split("\n") if l.startswith("sent ") or l.startswith("total ") or "speedup" in l]
    summary = "\n".join(summary_lines[-3:]) if summary_lines else out[-500:]

    if proc.returncode != 0:
        err_text = stderr.decode().strip()
        await update.message.reply_text(f"Sync error:\n```\n{err_text[:1000]}\n```", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"Synced *{name}*:\n```\n{summary}\n```", parse_mode="Markdown")


handler = CommandHandler("sync", sync_handler)

#!/usr/bin/env python3
"""Batch-archive inactive Telegram chats (inactive > 180 days, not pinned, not already archived).

Safe to re-run: skips already-archived chats on every run.

Usage:
    python scripts/tg-archive-batch.py                   # dry-run: show candidates
    python scripts/tg-archive-batch.py --apply           # archive them
    python scripts/tg-archive-batch.py --apply --batch-size 20 --cooldown 60
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.errors import FloodWaitError

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
SESSION = str(Path(__file__).resolve().parent.parent / ".tg_session")

INACTIVE_THRESHOLD_DAYS = 180

logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.INFO)
log = logging.getLogger("tg-archive-batch")


def days_since(dt) -> int:
    if dt is None:
        return 9999
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - dt).days


async def fetch_candidates(client: TelegramClient) -> list:
    """Return dialogs that are non-archived, non-pinned, inactive > threshold."""
    log.info("Fetching all dialogs...")
    dialogs = await client.get_dialogs(limit=None)
    log.info(f"Fetched {len(dialogs)} dialogs total")

    candidates = []
    for d in dialogs:
        if d.archived:
            continue
        if d.pinned:
            continue
        inactive = days_since(d.date)
        if inactive > INACTIVE_THRESHOLD_DAYS:
            candidates.append((d, inactive))

    candidates.sort(key=lambda x: -x[1])  # most stale first
    return candidates


async def archive_batches(
    client: TelegramClient,
    candidates: list,
    batch_size: int,
    cooldown: int,
) -> dict:
    total = len(candidates)
    ok = 0
    skipped = 0
    failed = 0

    log.info(f"Archiving {total} chats in batches of {batch_size} (cooldown={cooldown}s)")

    for batch_start in range(0, total, batch_size):
        batch = candidates[batch_start : batch_start + batch_size]
        batch_num = batch_start // batch_size + 1
        total_batches = (total + batch_size - 1) // batch_size
        log.info(f"--- Batch {batch_num}/{total_batches} ({len(batch)} chats) ---")

        for i, (dialog, inactive_days) in enumerate(batch):
            # Re-check: dialog might have been archived since we fetched
            entity = dialog.entity
            title = getattr(entity, "title", None) or getattr(entity, "first_name", None) or str(entity.id)

            attempt = 0
            while True:
                attempt += 1
                try:
                    await client.edit_folder(entity, 1)
                    ok += 1
                    log.info(f"  [{batch_start + i + 1}/{total}] Archived: {title} ({inactive_days}d)")
                    break
                except FloodWaitError as e:
                    wait = e.seconds + 5
                    log.warning(f"  FloodWait {e.seconds}s — sleeping {wait}s then retrying")
                    await asyncio.sleep(wait)
                    # retry the same chat
                    continue
                except Exception as e:
                    err_str = str(e)
                    # Already archived or peer gone — treat as success
                    if "ALREADY_ARCHIVED" in err_str or "PEER_ID_INVALID" in err_str:
                        skipped += 1
                        log.info(f"  [{batch_start + i + 1}/{total}] Skipped (already archived / invalid): {title}")
                    else:
                        failed += 1
                        log.warning(f"  [{batch_start + i + 1}/{total}] Failed: {title}: {e}")
                    break

            await asyncio.sleep(0.5)

        # Cooldown between batches (skip after the last one)
        if batch_start + batch_size < total:
            log.info(f"Batch {batch_num} done. Cooling down {cooldown}s...")
            await asyncio.sleep(cooldown)

    return {"total": total, "ok": ok, "skipped": skipped, "failed": failed}


async def main():
    parser = argparse.ArgumentParser(description="Batch-archive stale Telegram chats")
    parser.add_argument("--apply", action="store_true",
                        help="Actually archive (default: dry-run, show candidates only)")
    parser.add_argument("--batch-size", type=int, default=40, metavar="N",
                        help="Chats per batch (default: 40)")
    parser.add_argument("--cooldown", type=int, default=30, metavar="N",
                        help="Seconds to wait between batches (default: 30)")
    args = parser.parse_args()

    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.start()
    log.info("Connected to Telegram")

    candidates = await fetch_candidates(client)

    if not candidates:
        print("\nNothing to archive — no inactive non-pinned non-archived chats found.")
        await client.disconnect()
        return

    print(f"\nFound {len(candidates)} candidate(s) to archive (inactive >{INACTIVE_THRESHOLD_DAYS}d):")
    for dialog, inactive in candidates[:30]:
        entity = dialog.entity
        title = getattr(entity, "title", None) or getattr(entity, "first_name", None) or str(entity.id)
        print(f"  {inactive:>4}d  {title}")
    if len(candidates) > 30:
        print(f"  ... and {len(candidates) - 30} more")
    print()

    if not args.apply:
        print("Dry-run complete. Pass --apply to archive these chats.")
        await client.disconnect()
        return

    stats = await archive_batches(client, candidates, args.batch_size, args.cooldown)

    print("\n" + "=" * 50)
    print("  ARCHIVE SUMMARY")
    print("=" * 50)
    print(f"  Candidates :  {stats['total']}")
    print(f"  Archived   :  {stats['ok']}")
    print(f"  Skipped    :  {stats['skipped']}  (already archived / invalid peer)")
    print(f"  Failed     :  {stats['failed']}")
    print("=" * 50)

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

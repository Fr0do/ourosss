#!/usr/bin/env python3
"""Telegram chat organizer — audit, categorize, and restructure folders/pins.

Usage:
    python scripts/tg-organize.py                  # audit current state
    python scripts/tg-organize.py --plan           # show proposed changes
    python scripts/tg-organize.py --apply          # apply changes (interactive confirm)
    python scripts/tg-organize.py --config folders.yaml  # use custom folder config
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import re

import yaml
from dotenv import load_dotenv
from telethon import TelegramClient, functions, types
from telethon.tl.types import (
    Channel,
    Chat,
    DialogFilter,
    DialogFilterDefault,
    InputPeerChannel,
    InputPeerChat,
    InputPeerUser,
    User,
)

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

API_ID = int(os.environ["TELEGRAM_API_ID"])
API_HASH = os.environ["TELEGRAM_API_HASH"]
SESSION = str(Path(__file__).resolve().parent.parent / ".tg_session")

logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=logging.INFO)
log = logging.getLogger("tg-organize")

# ── Default config ───────────────────────────────────────────────────────
# Only creates NEW folders and archives dead chats.
# Existing folders are never modified unless explicitly listed in a YAML config.
RESEARCH_KEYWORDS = [
    "ai", "ml", "dl", "nlp", "cv", "llm", "grpo", "rl", "rlhf",
    "arxiv", "paper", "neurips", "icml", "iclr", "acl", "emnlp", "cvpr",
    "research", "lab", "science", "deep learning", "machine learning",
    "neural", "transformer", "diffusion", "spectral",
    "airi", "skoltech", "phd", "gonzo", "hugging", "openai",
]

DEFAULT_FOLDERS = {
    "Research": {
        "keywords": RESEARCH_KEYWORDS,
        "flags": {"groups": True, "broadcasts": True},
    },
}

ARCHIVE_AFTER_DAYS = 180

# Short keywords that need word-boundary matching to avoid false positives
_SHORT_KEYWORDS = {"ai", "ml", "dl", "nlp", "cv", "rl", "llm", "rlhf"}


def _keyword_match(title: str, keywords: list[str]) -> bool:
    """Match keywords against title. Short keywords use word boundaries."""
    title_lower = title.lower()
    for kw in keywords:
        if kw in _SHORT_KEYWORDS:
            if re.search(rf'\b{re.escape(kw)}\b', title_lower):
                return True
        else:
            if kw in title_lower:
                return True
    return False


# ── Helpers ──────────────────────────────────────────────────────────────

def classify_entity(entity) -> str:
    """Return a type string: private, bot, group, supergroup, channel."""
    if isinstance(entity, User):
        return "bot" if entity.bot else "private"
    if isinstance(entity, Channel):
        return "channel" if entity.broadcast else "supergroup"
    if isinstance(entity, Chat):
        return "group"
    return "unknown"


def entity_title(entity) -> str:
    if isinstance(entity, User):
        parts = [entity.first_name or "", entity.last_name or ""]
        name = " ".join(p for p in parts if p)
        return name or entity.username or str(entity.id)
    return getattr(entity, "title", None) or str(entity.id)


def to_input_peer(entity):
    if isinstance(entity, User):
        return InputPeerUser(entity.id, entity.access_hash or 0)
    if isinstance(entity, Channel):
        return InputPeerChannel(entity.id, entity.access_hash or 0)
    if isinstance(entity, Chat):
        return InputPeerChat(entity.id)
    return None


def days_since(dt) -> int:
    if dt is None:
        return 9999
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - dt).days


# ── Audit ────────────────────────────────────────────────────────────────

async def audit(client: TelegramClient) -> dict:
    """Fetch all dialogs and current folders, return structured audit."""
    dialogs = await client.get_dialogs(limit=None)
    log.info(f"Fetched {len(dialogs)} dialogs")

    chats = []
    for d in dialogs:
        entity = d.entity
        chats.append({
            "id": d.id,
            "title": entity_title(entity),
            "type": classify_entity(entity),
            "unread": d.unread_count,
            "pinned": d.pinned,
            "archived": d.archived,
            "muted": d.dialog.notify_settings.mute_until is not None
                     if hasattr(d.dialog, "notify_settings") and d.dialog.notify_settings else False,
            "last_activity": d.date,
            "days_inactive": days_since(d.date),
            "entity": entity,
        })

    # Current folders
    result = await client(functions.messages.GetDialogFiltersRequest())
    filters = result.filters if hasattr(result, "filters") else result
    folders = []
    for f in filters:
        if isinstance(f, DialogFilterDefault):
            folders.append({"id": 0, "title": "All Chats", "builtin": True})
            continue
        if isinstance(f, DialogFilter):
            folders.append({
                "id": f.id,
                "title": f.title if isinstance(f.title, str) else f.title.text,
                "pinned_count": len(f.pinned_peers),
                "include_count": len(f.include_peers),
                "exclude_count": len(f.exclude_peers),
                "flags": {
                    "contacts": f.contacts,
                    "non_contacts": f.non_contacts,
                    "groups": f.groups,
                    "broadcasts": f.broadcasts,
                    "bots": f.bots,
                    "exclude_muted": f.exclude_muted,
                    "exclude_read": f.exclude_read,
                    "exclude_archived": f.exclude_archived,
                },
                "builtin": False,
            })

    return {"chats": chats, "folders": folders}


def print_audit(data: dict):
    chats = data["chats"]
    folders = data["folders"]

    # Stats
    by_type = defaultdict(int)
    for c in chats:
        by_type[c["type"]] += 1
    pinned = [c for c in chats if c["pinned"]]
    archived = [c for c in chats if c["archived"]]
    dead = [c for c in chats if c["days_inactive"] > 90 and not c["pinned"]]

    print("\n" + "=" * 60)
    print("  TELEGRAM AUDIT")
    print("=" * 60)
    print(f"\n  Total dialogs: {len(chats)}")
    for t, n in sorted(by_type.items()):
        print(f"    {t}: {n}")
    print(f"\n  Pinned: {len(pinned)}")
    for c in pinned:
        print(f"    * {c['title']} ({c['type']})")
    print(f"\n  Archived: {len(archived)}")
    print(f"  Inactive >90d: {len(dead)}")

    print(f"\n  Current folders ({len(folders)}):")
    for f in folders:
        if f["builtin"]:
            print(f"    [{f['id']}] {f['title']} (default)")
        else:
            print(f"    [{f['id']}] {f['title']}  "
                  f"pinned={f['pinned_count']} include={f['include_count']} "
                  f"exclude={f['exclude_count']}")
            flags_on = [k for k, v in f["flags"].items() if v]
            if flags_on:
                print(f"         flags: {', '.join(flags_on)}")

    if dead:
        print("\n  Dead chats (>90 days, candidates for archive):")
        for c in sorted(dead, key=lambda x: -x["days_inactive"])[:20]:
            print(f"    {c['days_inactive']:>4}d  {c['title']} ({c['type']})")
        if len(dead) > 20:
            print(f"    ... and {len(dead) - 20} more")

    print()


# ── Planning ─────────────────────────────────────────────────────────────

def load_folder_config(path: str | None) -> dict:
    if path:
        with open(path) as f:
            return yaml.safe_load(f) or {}
    return DEFAULT_FOLDERS


def plan_changes(data: dict, folder_config: dict) -> list[dict]:
    """Generate a list of changes to apply.

    Strategy: create or update folders from config using exclusive priority-based
    assignment (YAML order = priority), and archive dead chats.
    """
    chats = data["chats"]
    existing = {f["title"]: f for f in data["folders"] if not f.get("builtin")}
    changes = []
    next_id = max((f["id"] for f in data["folders"] if not f.get("builtin")), default=1) + 1

    # Build pool of fresh (non-archived, active within ARCHIVE_AFTER_DAYS) chats
    pool = {c["id"]: c for c in chats
            if not c["archived"] and c["days_inactive"] <= ARCHIVE_AFTER_DAYS}

    for fname, fconf in folder_config.items():
        # Determine action and ID: update existing folder or create new one
        if fname in existing:
            action = "update_folder"
            folder_id = existing[fname]["id"]
        else:
            action = "create_folder"
            folder_id = next_id
            next_id += 1

        # Keyword-match against the remaining pool (exclusive assignment)
        keywords = [k.lower() for k in fconf.get("keywords", [])]
        matched = []
        skip_types = set(fconf.get("skip_types", ["private", "bot"]))
        for c in list(pool.values()):
            if c["type"] in skip_types:
                continue
            if _keyword_match(c["title"], keywords):
                matched.append(c)

        # catch_types: also grab all remaining chats of these types (e.g. ["channel"])
        catch_types = fconf.get("catch_types", [])
        if catch_types:
            for c in list(pool.values()):
                if c["type"] in catch_types and c not in matched:
                    matched.append(c)

        # Remove matched chats from pool so they can't appear in later folders
        for c in matched:
            pool.pop(c["id"], None)

        changes.append({
            "action": action,
            "name": fname,
            "id": folder_id,
            "chats": matched,
            "emoticon": fconf.get("emoticon"),
            "color": fconf.get("color"),
        })


    # Archive dead chats (>ARCHIVE_AFTER_DAYS inactive, not pinned, not already archived)
    dead = [c for c in chats
            if c["days_inactive"] > ARCHIVE_AFTER_DAYS
            and not c["pinned"] and not c["archived"]]
    if dead:
        changes.append({
            "action": "archive",
            "chats": dead,
        })

    return changes


def print_plan(changes: list[dict]):
    print("\n" + "=" * 60)
    print("  PROPOSED CHANGES")
    print("=" * 60)

    for ch in changes:
        if ch["action"] in ("create_folder", "update_folder"):
            verb = "CREATE" if ch["action"] == "create_folder" else "UPDATE"
            print(f"\n  [{verb}] Folder: {ch['name']} (id={ch['id']})")
            if ch["chats"]:
                print(f"    Explicitly include ({len(ch['chats'])} chats):")
                for c in ch["chats"][:15]:
                    print(f"      + {c['title']} ({c['type']})")
                if len(ch["chats"]) > 15:
                    print(f"      ... +{len(ch['chats']) - 15} more")
            else:
                print("    (no chats matched keywords)")

        elif ch["action"] == "archive":
            print(f"\n  [ARCHIVE] {len(ch['chats'])} dead chats (>180 days inactive):")
            for c in sorted(ch["chats"], key=lambda x: -x["days_inactive"])[:10]:
                print(f"    → {c['title']} ({c['days_inactive']}d)")
            if len(ch["chats"]) > 10:
                print(f"    ... +{len(ch['chats']) - 10} more")

    print()


# ── Apply ────────────────────────────────────────────────────────────────

async def apply_changes(client: TelegramClient, changes: list[dict]):
    for ch in changes:
        if ch["action"] in ("create_folder", "update_folder"):
            title = ch["name"]

            # Only include peers with valid access hashes
            include_peers = []
            for c in ch.get("chats", []):
                entity = c["entity"]
                ah = getattr(entity, "access_hash", None)
                if ah is None or ah == 0:
                    continue
                ip = to_input_peer(entity)
                if ip:
                    include_peers.append(ip)

            verb = "Creating" if ch["action"] == "create_folder" else "Updating"
            log.info(f"{verb} folder: {title} (id={ch['id']}, {len(include_peers)} peers)")

            # Validate peers by trying with all, then falling back to empty + flags only
            async def _try_create(peers):
                f = DialogFilter(
                    id=ch["id"],
                    title=types.TextWithEntities(text=title, entities=[]),
                    pinned_peers=[],
                    include_peers=peers,
                    exclude_peers=[],
                    contacts=False,
                    non_contacts=False,
                    groups=False,
                    broadcasts=False,
                    bots=False,
                    exclude_muted=False,
                    exclude_read=False,
                    exclude_archived=True,
                    emoticon=ch.get("emoticon"),
                    color=ch.get("color"),
                )
                await client(functions.messages.UpdateDialogFilterRequest(
                    id=ch["id"], filter=f))

            try:
                await _try_create(include_peers)
            except Exception as e:
                if "CHATLIST_INCLUDE_INVALID" in str(e) or "CHAT_ID_INVALID" in str(e):
                    # Binary-split to find valid subset
                    log.warning(f"  Bulk include failed ({e}), binary-split validating...")

                    async def _find_valid(peers):
                        if not peers:
                            return []
                        try:
                            await _try_create(peers)
                            return peers  # all valid
                        except Exception:
                            if len(peers) == 1:
                                log.warning(f"  Skipping invalid peer: {peers[0]}")
                                return []
                            mid = len(peers) // 2
                            left = await _find_valid(peers[:mid])
                            right = await _find_valid(peers[mid:])
                            return left + right

                    valid_peers = await _find_valid(include_peers)
                    if valid_peers:
                        await _try_create(valid_peers)
                    else:
                        # Create folder with flags only, no explicit peers
                        await _try_create([])
                    log.info(f"  Valid peers: {len(valid_peers)}/{len(include_peers)}")
                else:
                    raise

        elif ch["action"] == "archive":
            total = len(ch["chats"])
            log.info(f"Archiving {total} dead chats...")
            ok, fail = 0, 0
            for i, c in enumerate(ch["chats"]):
                try:
                    await client.edit_folder(c["entity"], 1)
                    ok += 1
                except Exception as e:
                    fail += 1
                    wait = getattr(e, "seconds", 0)
                    if wait:
                        log.warning(f"  Flood wait {wait}s at {i}/{total}")
                        await asyncio.sleep(wait + 2)
                        try:
                            await client.edit_folder(c["entity"], 1)
                            ok += 1
                            fail -= 1
                        except Exception:
                            pass
                    else:
                        log.warning(f"  [{i}/{total}] Failed: {c['title']}: {e}")
                # Pace requests: 0.5s between each, extra pause every 50
                if (i + 1) % 50 == 0:
                    log.info(f"  Progress: {i+1}/{total} (ok={ok}, fail={fail})")
                    await asyncio.sleep(10)
                else:
                    await asyncio.sleep(0.5)
            log.info(f"Archived: {ok} ok, {fail} failed out of {total}")

    # Reorder folders — must include ALL folder IDs, not just new ones
    new_ids = {ch["id"] for ch in changes
               if ch["action"] in ("create_folder", "update_folder")}
    if new_ids:
        try:
            result = await client(functions.messages.GetDialogFiltersRequest())
            all_filters = result.filters if hasattr(result, "filters") else result
            all_ids = [f.id for f in all_filters
                       if not isinstance(f, DialogFilterDefault)]
            # Append any new IDs not yet in the list (just created)
            for nid in sorted(new_ids):
                if nid not in all_ids:
                    all_ids.append(nid)
            log.info(f"Setting folder order: {all_ids}")
            await client(functions.messages.UpdateDialogFiltersOrderRequest(
                order=all_ids,
            ))
        except Exception as e:
            log.warning(f"Folder reorder failed (non-critical): {e}")

    log.info("Done!")


# ── Main ─────────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="Telegram chat organizer")
    parser.add_argument("--plan", action="store_true", help="Show proposed changes")
    parser.add_argument("--dump-fresh", action="store_true",
                        help="Print all non-archived chats with days_inactive <= 180, grouped by type")
    parser.add_argument("--apply", action="store_true", help="Apply changes")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation")
    parser.add_argument("--config", type=str, help="YAML folder config file")
    parser.add_argument("--skip-archive", action="store_true", help="Skip archiving, only create/update folders")
    args = parser.parse_args()

    client = TelegramClient(SESSION, API_ID, API_HASH)
    await client.start()
    log.info("Connected to Telegram")

    data = await audit(client)
    print_audit(data)

    if args.dump_fresh:
        type_order = ["channel", "supergroup", "group", "private", "bot"]
        fresh = [c for c in data["chats"] if not c["archived"] and c["days_inactive"] <= 180]
        by_type = defaultdict(list)
        for c in fresh:
            by_type[c["type"]].append(c)
        for t in type_order:
            group = by_type.get(t)
            if not group:
                continue
            print(f"\n── {t} ──")
            for c in sorted(group, key=lambda x: x["title"].lower()):
                print(f"  {c['type']:12s}  {c['days_inactive']:>4}d  {c['title']}")
        # Print any types not in the predefined order
        for t, group in sorted(by_type.items()):
            if t not in type_order:
                print(f"\n── {t} ──")
                for c in sorted(group, key=lambda x: x["title"].lower()):
                    print(f"  {c['type']:12s}  {c['days_inactive']:>4}d  {c['title']}")
        await client.disconnect()
        sys.exit(0)

    if args.plan or args.apply:
        folder_config = load_folder_config(args.config)
        changes = plan_changes(data, folder_config)
        if args.skip_archive:
            changes = [c for c in changes if c["action"] != "archive"]
        print_plan(changes)

        if args.apply:
            if args.yes:
                await apply_changes(client, changes)
            else:
                answer = input("\nApply these changes? [y/N] ")
                if answer.strip().lower() == "y":
                    await apply_changes(client, changes)
                else:
                    print("Aborted.")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

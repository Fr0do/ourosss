# TG-Organize — Telegram Chat Organizer

## Overview

A set of scripts for auditing, categorizing, and restructuring Telegram folders (dialog filters) using the MTProto API via Telethon. The main tool (`tg-organize.py`) reads a YAML folder config, matches chats against keyword rules using priority-based exclusive assignment, creates or updates folders in Telegram, and archives stale chats. Supplementary scripts handle batch archiving, folder migration from old to new folder IDs, and orphan auditing.

## Setup

**Environment variables** (in `.env` at repo root):

```
TELEGRAM_API_ID=<your numeric API id>
TELEGRAM_API_HASH=<your API hash>
```

Obtain these at https://my.telegram.org under "API development tools".

**Dependencies:**

```bash
pip install telethon pyyaml python-dotenv
```

**Session file:** On first run, Telethon will prompt for your phone number and a login code, then write `.tg_session.session` to the repo root. Subsequent runs reuse it silently.

## Quick Start

```bash
# 1. Audit current state — show dialog counts, folder list, and dead chats
python scripts/tg-organize.py

# 2. Preview proposed changes without touching anything
python scripts/tg-organize.py --plan --config scripts/folders.yaml

# 3. Apply changes (prompts for confirmation)
python scripts/tg-organize.py --apply --config scripts/folders.yaml

# Skip confirmation
python scripts/tg-organize.py --apply --config scripts/folders.yaml --yes

# Show all active (non-archived, <180d inactive) chats grouped by type
python scripts/tg-organize.py --dump-fresh

# Apply folders only, skip archiving stale chats
python scripts/tg-organize.py --apply --config scripts/folders.yaml --skip-archive
```

## Folder Config (folders.yaml)

Each top-level key is a folder name. YAML order determines priority — a chat matched by the first folder is removed from the pool and will not appear in any later folder.

```yaml
Research:
  emoticon: "🔬"      # optional; shown in Telegram sidebar
  color: 6            # optional; 0=blue 1=yellow 2=green 3=cyan 4=red 5=pink 6=purple
  keywords:           # substring match against chat title (case-insensitive)
    - arxiv
    - deep learning
    - nlp             # short keywords (ai, ml, dl, rl, etc.) use word-boundary matching

Life:
  emoticon: "🎸"
  color: 1
  keywords:
    - gym
    - meme

News:
  emoticon: "📰"
  color: 0
  catch_types: [channel]   # grab ALL remaining chats of these types not already assigned
  keywords:
    - news
```

**Fields:**

| Field | Required | Description |
|---|---|---|
| `keywords` | no | List of substrings to match against chat title |
| `catch_types` | no | After keyword matching, sweep up all remaining chats of these types (e.g. `channel`, `supergroup`, `group`) |
| `skip_types` | no | Types to exclude from this folder (default: `[private, bot]`) |
| `emoticon` | no | Folder icon string |
| `color` | no | Integer 0–6 (see comment in folders.yaml) |

Private chats and bots are excluded from all folders by default (via `skip_types`). Only chats active within the last 180 days enter the matching pool; older ones are candidates for archiving.

## Scripts

| Script | Description |
|---|---|
| `tg-organize.py` | Main tool: audit, plan, and apply folder changes + archive stale chats |
| `tg-archive-batch.py` | Standalone batch archiver with configurable batch size and cooldown |
| `tg-folder-cleanup.py` | One-time migration: move peers from named old folder IDs into new folders, then delete old folders |
| `tg-folder-migrate.py` | Read-only audit: resolve and print all folder contents, report chats in old folders not covered by new ones |
| `folders.yaml` | Folder definitions used by `tg-organize.py --config` |

## Architecture Notes

- **Exclusive assignment (first-match-wins):** Chats are drawn from a shared pool. Once a chat is assigned to a folder, it is removed from the pool and cannot appear in any subsequent folder. YAML order is therefore priority order.
- **No auto-include flags:** Folders are built with explicit peer lists only. Type-wide flags (`groups`, `broadcasts`, etc.) are not set, so the folder contents are precisely what the keyword rules select. The exception is `catch_types`, which sweeps remaining unassigned chats of a given type into a folder.
- **Private chats and bots excluded by default:** `skip_types` defaults to `["private", "bot"]`. Override per-folder if needed.
- **Stale chat threshold:** 180 days. Chats inactive beyond this are excluded from the folder-assignment pool and queued for archiving (unless pinned or already archived).
- **Binary-split peer validation:** When Telegram rejects a bulk peer list with `CHATLIST_INCLUDE_INVALID`, the apply step recursively bisects the list to identify and drop only the invalid peers.

## Archiving

`tg-archive-batch.py` is the dedicated archiver. It is safe to re-run: already-archived chats are skipped.

```bash
# Dry run — list candidates only
python scripts/tg-archive-batch.py

# Archive with defaults (batch=40, cooldown=30s)
python scripts/tg-archive-batch.py --apply

# Custom batch size and cooldown (useful if hitting flood limits)
python scripts/tg-archive-batch.py --apply --batch-size 20 --cooldown 60
```

**Rate limits:** The script paces requests at 0.5s per chat and waits `batch cooldown` seconds between batches. On `FloodWaitError` it automatically sleeps for the required duration and retries the same chat. If you still hit limits, reduce `--batch-size` and increase `--cooldown`.

`tg-organize.py --apply` also archives stale chats as part of its run (same 0.5s pacing, automatic flood-wait handling). Use `--skip-archive` to suppress this and run archiving separately.

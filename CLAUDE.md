# CLAUDE.md — Ouroboros (Meta-Project)

## What Is This
Root governance project for all of Max's research. Contains:
- **OUROBOROS.md** — research meta-protocol (project registry, workflow, principles)
- **bot/** — Telegram control panel for autonomous agent oversight
- **notion_bootstrap.py** — one-time Notion workspace initializer

## Environment
- Local macOS: SSH access to kurkin-1, kurkin-4
- Secrets in .env (TELEGRAM_TOKEN, NOTION_SECRET)
- Python deps: python-telegram-bot, notion-client, python-dotenv

## Model Strategy
- **Plan with Opus, implement with Sonnet**: For non-trivial tasks, use Opus for planning/architecture, then delegate implementation to Sonnet subagents (cheaper, faster for code writing)
- If Opus rate limits are not a concern, Opus implementation is fine
- Heavy code generation, refactoring, and boilerplate → prefer Sonnet subagents
- Design decisions, debugging strategy, complex reasoning → keep in Opus

## RTK
Active via Claude Code hook. All shell ops auto-optimized.

## Key Files
| File | Purpose |
|---|---|
| OUROBOROS.md | Global research governance — read first |
| .env | Secrets (gitignored) |
| bot/main.py | Telegram bot entry point |
| bot/services/tg.py | Shared Telegram helpers (send_long, require_project) |
| bot/services/ssh.py | SSH/tmux/GPU operations |
| notion_bootstrap.py | One-time Notion workspace setup |

## Issue Journaling
- **Create issues** for meaningful features/fixes before implementing
- **Comment progress** on issues: what was done, blockers hit, commit hashes
- **Reference in commits**: `fixes #N` to auto-close, or mention `#N` if work continues
- **Triage at session start**: check `gh issue list --repo Fr0do/ouroboros --state open`

## Feature Dispatch (auto-dev)
- A `UserPromptSubmit` hook (`.claude/hooks/check-auto-dev.sh`) checks for `auto-dev` labeled issues
- If you see "AUTO-DEV" in hook output, pick up the issue immediately
- Comment "Picked up" on the issue to claim it (prevents other agents from duplicating work)
- Implement, commit with `fixes #N`, the label is removed when the issue closes
- See OUROBOROS.md "Feature Dispatch" for full protocol

## Commit Conventions
- Prefix: `[feat]`, `[fix]`, `[doc]`, `[infra]`, `[bot]`, `[s_cot]`
- Include a summary of major edits in commit messages (not just what changed in this repo)
- For remote-only changes (e.g. s_cot training code uploaded via scp), document them in the commit body
- Format: short title line, blank line, bullet list of all significant changes including remote/subproject work
- Always note which subproject was affected and what was changed conceptually

## Subprojects (see OUROBOROS.md for full map)
- s_cot → ~/experiments/s_cot_tex + kurkin-1:/workspace-SR004.nfs2/kurkin/s_cot
- long-vqa → ~/experiments/long-vqa + kurkin-1:/workspace-SR004.nfs2/kurkin/long-vqa
- bbbo → kurkin-1:/workspace-SR004.nfs2/kurkin/bbbo/GeneralOptimizer

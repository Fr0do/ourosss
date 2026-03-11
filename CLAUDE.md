# CLAUDE.md — Ouroboros (Meta-Project)

## What Is This
Root governance project for all of Max's research. Contains:
- **OUROBOROS.md** — research meta-protocol (project registry, workflow, principles)
- **bot/** — Telegram control panel for autonomous agent oversight

## Environment
- Local macOS: SSH access to kurkin-1, kurkin-4
- Secrets in .env (TELEGRAM_TOKEN)
- Python deps: python-telegram-bot, python-dotenv

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
| scripts/auto-dev.sh | Autonomous feature implementation agent |

## Issue Journaling
- **ALWAYS create an issue FIRST** — before writing any code for a feature or non-trivial fix. No exceptions. Even if the user doesn't ask, create the issue, then implement. If you forget, create one retroactively and reference it.
- **Comment progress** on issues: what was done, blockers hit, commit hashes
- **Reference in commits**: `fixes #N` to auto-close, or mention `#N` if work continues
- **Triage at session start**: check `gh issue list --repo Fr0do/ouroboros --state open`

## Feature Dispatch (auto-dev)
- A `UserPromptSubmit` hook (`.claude/hooks/check-auto-dev.sh`) checks for `auto-dev` labeled issues
- If you see "AUTO-DEV" in hook output, pick up the issue immediately
- Comment "Picked up" on the issue to claim it (prevents other agents from duplicating work)
- Implement, commit with `fixes #N`, the label is removed when the issue closes
- See OUROBOROS.md "Feature Dispatch" for full protocol

## Secrets & env.example
- **Never** echo, print, or write actual secrets (tokens, keys, passwords) to files, terminal, or commits
- Every repo that uses `.env` must have an `env.example` with keys only (no values), committed to git
- When adding a new env var: update `env.example` in the same commit
- `.env` is always gitignored; `env.example` is always tracked

## Commit Conventions
- Prefix: `[feat]`, `[fix]`, `[doc]`, `[infra]`, `[bot]`, `[s_cot]`
- Include a summary of major edits in commit messages (not just what changed in this repo)
- For remote-only changes (e.g. s_cot training code uploaded via scp), document them in the commit body
- Format: short title line, blank line, bullet list of all significant changes including remote/subproject work
- Always note which subproject was affected and what was changed conceptually

## Subprojects (see OUROBOROS.md for full map)
- s_cot → ~/experiments/s_cot_tex + kurkin-1:/workspace-SR004.nfs2/kurkin/s_cot
- mmred → ~/experiments/mmred + kurkin-1:/workspace-SR004.nfs2/kurkin/mmred
- bbbo → kurkin-1:/workspace-SR004.nfs2/kurkin/bbbo/GeneralOptimizer

# CLAUDE.md — Ouroboros

## What Is This
Root governance for Max's research. Bot (`bot/`), governance protocol (`OUROBOROS.md`).

## Cost Discipline
Delegation is mandatory, not optional.

| Task type | Model | Examples |
|---|---|---|
| Planning, architecture, debugging | **Opus** (you) | Design decisions, complex reasoning, code review |
| Implementation (>20 lines) | **Sonnet subagent** | New files, handlers, refactoring, tests, HTML/CSS |
| Exploration, search, summarization | **Haiku subagent** | Codebase search, file exploration, rote transforms |

**Hard rule**: before writing >20 lines of code yourself, launch a Sonnet `Agent` subagent. No exceptions. Opus writes plans and reviews; Sonnet writes code.

## Environment
- Secrets in `.env` (gitignored). `env.example` tracked — update both together.
- Deps: `uv sync --locked` to install. `uv lock` after changing deps. `uv run ouroboros` to start bot.

## Key Files
| File | Purpose |
|---|---|
| OUROBOROS.md | Research pipeline protocol |
| PROJECTS.md | Workflow and issue routing |
| CHANGELOG.md | Version history |
| bot/main.py | Telegram bot entry |
| scripts/auto-dev.sh | Autonomous agent for `auto-dev` labeled issues |

## Issue Journaling
- **Create issue FIRST** — before any feature/fix code. No exceptions. Retroactive if forgotten.
- `fixes #N` in commits to auto-close. Comment progress + commit hashes.
- Triage: `gh issue list --repo Fr0do/ouroboros --state open`

## Auto-Dev Dispatch
Hook (`.claude/hooks/check-auto-dev.sh`) injects pending `auto-dev` issues into context.
If you see `[AUTO-DEV DISPATCH]` → claim it ("Picked up"), implement, commit with `fixes #N`.

## Git
- Linear history (rebase, not merge). Commit & push by default.
- Prefix: `[feat]`, `[fix]`, `[doc]`, `[infra]`, `[bot]`, `[s_cot]`
- Commit body: bullet list of all significant changes

## Design Style
Apple-minimalist. White backgrounds, clean lines, generous whitespace. No dark themes for print.

# CLAUDE.md — Ouroboros

## What Is This
Root governance for Max's research. Bot (`bot/`), governance protocol (`OUROBOROS.md`).

## Cost Discipline
**Budget: $20/day.** Opus was 98% of $108 over 4 days. Delegation is mandatory, not optional.

| Task type | Model | Examples |
|---|---|---|
| Planning, architecture, debugging | **Opus** (you) | Design decisions, complex reasoning, code review |
| Implementation (>20 lines) | **Sonnet subagent** | New files, handlers, refactoring, tests, HTML/CSS |
| Exploration, search, summarization | **Haiku subagent** | Codebase search, file exploration, rote transforms |

**Hard rule**: before writing >20 lines of code yourself, launch a Sonnet `Agent` subagent. No exceptions. Opus writes plans and reviews; Sonnet writes code.

## Environment
- macOS → SSH to kurkin-1, kurkin-4 (shared NFS: `/workspace-SR004.nfs2/kurkin/`)
- Secrets in `.env` (gitignored). `env.example` tracked — update both together.
- Deps: `uv sync --locked` to install. `uv lock` after changing deps. `uv run ouroboros` to start bot.

## Key Files
| File | Purpose |
|---|---|
| OUROBOROS.md | Research philosophy and principles |
| PROJECTS.md | Project registry, infrastructure, workflow |
| CHANGELOG.md | Version history |
| bot/main.py | Telegram bot entry (18 handlers) |
| bot/services/tg.py | Shared helpers (send_long, @authorized, require_project) |
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
- Commit body: bullet list of all significant changes including remote/subproject work

## Subprojects
- s_cot → `~/experiments/s_cot_tex` + `kurkin-1:.../s_cot` (don't edit local — use scp)
- mmred → `~/experiments/mmred` + `kurkin-1:.../mmred`
- bbbo → `kurkin-1:.../bbbo/GeneralOptimizer`

## Design Style
Apple-minimalist. White backgrounds, clean lines, generous whitespace. No dark themes for print.

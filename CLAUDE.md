# CLAUDE.md — OuroSSS

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

## MCP Servers

Two MCP servers are configured in `.claude/settings.json`:
- **hermes** — `hermes mcp serve` — self-improving agent, memory, skills, delegation
- **swarm** — `npx -y @swarmify/agents-mcp` — codex/gemini parallel subagents

## Hermes (Self-Improving Agent)

Hermes wraps Claude (primary) and Codex as providers with a closed learning loop.
Config: `~/.hermes/config.yaml` · Model: `claude-opus-4-6` via Anthropic.

### Key MCP tools
| Tool category | Use when |
|---|---|
| `memory` | Store/retrieve cross-session facts, decisions, context |
| `skills` | Browse/install/run reusable agent skills from registry |
| `todo` | Break tasks into tracked subtasks |
| `delegation` | Spawn isolated subagents for parallel work |
| `session_search` | Search past reasoning traces (FTS5) |
| `cronjob` | Schedule recurring autonomous tasks |
| `rl` *(disabled)* | Export trajectories for RL training |

### Self-improvement loop
Hermes autonomously creates skills from successful reasoning traces and improves them during use.
- Browse skill registry: `hermes skills browse`
- View past sessions: `hermes sessions`
- Analyze costs/patterns: `hermes insights --days 7`
- Update hermes: `hermes update`

## Swarm Orchestration

### Agent × effort → model

| Agent | `effort` | Model | Tier | Best for |
|---|---|---|---|---|
| **codex** | `detailed` | gpt-5.4 | ≈ Opus | Architecture, complex rewrites |
| **codex** | `default` | gpt-5.3-codex | ≈ Sonnet | Standard implementation |
| **codex** | `fast` | gpt-5.3-codex-spark | ≈ Haiku | Simple fixes, renames, boilerplate |
| **gemini** | `detailed` | gemini-3.1-pro | ≈ Opus | Multi-system features, paper edits |
| **gemini** | `fast` | gemini-3-flash | ≈ Haiku | Search, exploration, summarization |
| **claude** | any | sonnet-4-6 | ≈ Sonnet | Avoid — same provider as orchestrator |

Gemini default model: `~/.gemini/settings.json` → `gemini-3.1-pro`. Flash via `effort="fast"`.

### Pipeline pattern

```
1. Implement  — codex/gemini edit agents in parallel (independent tasks)
2. Review     — codex plan+detailed agent on changed files
3. Commit     — orchestrator (you) does git add/commit after review passes
```

### Swarm rules
- Never spawn claude subagents (same provider, wasteful).
- Always pass `cwd`; match `effort` to task complexity.
- `mode="edit"` for implementation, `mode="plan"` for review/exploration, `mode="ralph"` for backlog.
- **Commits**: agents run in a git sandbox — YOU commit after agents finish.
- Poll with `Swarm.Status(task_name)` — wait ≥2 min before first check.
- Cost: `/agent-dashboard`

### Review agent invocation
```
Swarm.Spawn(task_name="X-review", agent_type="codex", mode="plan", effort="detailed", cwd=...,
  prompt="Review changes in [files]. Report: correctness, edge cases, test gaps, style.
          Format: numbered list with severity (critical / warn / nit).")
```
Fix all `critical` before committing; use judgment on `warn`.

## Environment
- Secrets in `.env` (gitignored). `.env.example` tracked — update both together.
- Deps: `uv sync --locked` to install. `uv lock` after changing deps. `uv run ourosss` to start bot.

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
- Triage: `gh issue list --repo Fr0do/ourosss --state open`

## Auto-Dev Dispatch
Hook (`.claude/hooks/check-auto-dev.sh`) injects pending `auto-dev` issues into context.
If you see `[AUTO-DEV DISPATCH]` → claim it ("Picked up"), implement, commit with `fixes #N`.

## Git
- Linear history (rebase, not merge). Commit & push by default.
- Prefix: `[feat]`, `[fix]`, `[doc]`, `[infra]`, `[bot]`, `[s_cot]`
- Commit body: bullet list of all significant changes

## Design Style
Apple-minimalist. White backgrounds, clean lines, generous whitespace. No dark themes for print.

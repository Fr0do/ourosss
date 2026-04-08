# CLAUDE.md — OuroSSS

## What Is This
Root governance for Max's research. Bot (`bot/`), governance protocol (`OUROBOROS.md`).

## Cost Discipline
Delegation is mandatory, not optional. **Codex has the fattest limits — burn it first.** Anthropic models are reserved for planning only.

### Provider priority

1. **Opus** (orchestrator, you) — planning, architecture, code review, final decisions. **Only Anthropic model used.** No Sonnet/Haiku subagents.
2. **Codex** (via Swarm) — *default* implementation, refactoring, tests, exploration, summarization. Use until daily limits exhausted.
3. **Gemini** (via Swarm) — *fallback after Codex* and for tasks Gemini is genuinely better at: huge-context reads (>200k tokens), multi-file paper edits, multimodal (image/PDF), search-heavy exploration via `gemini-3-flash`.

| Task type | Route to |
|---|---|
| Planning, architecture, debugging, review | **Opus** (you) |
| Implementation (>20 lines), refactoring, tests | **codex** subagent (Swarm) |
| Simple fixes, renames, boilerplate | **codex** `effort=fast` |
| Huge-context / multimodal / paper edits | **gemini** `effort=detailed` |
| Search, exploration, summarization | **gemini** `effort=fast` (cheap) or **codex** `effort=fast` |

**Hard rule**: before writing >20 lines of code yourself, spawn a **codex** Swarm agent. No exceptions. Do NOT spawn Sonnet/Haiku subagents via the `Agent` tool for implementation — that burns the same Anthropic quota Opus runs on. Use `Agent` only for read-only research tasks where context isolation matters.

**Fallback chain**: codex → (on rate limit / quota exhausted) → gemini. Track via `/agent-dashboard`.

## MCP Servers

Two MCP servers are configured in `.claude/settings.json`:
- **hermes** — `hermes mcp serve` — self-improving agent, memory, skills, delegation
- **swarm** — `npx -y @swarmify/agents-mcp` — codex/gemini parallel subagents

## Portable Config

Config lives in `infra/` (tracked in repo). On a new machine:

```bash
bash infra/bootstrap.sh   # symlinks infra/hermes/config.yaml → ~/.hermes/config.yaml
hermes login              # OAuth auth
```

See `infra/README.md` for full prerequisites and manual auth steps.

## Hermes (Self-Improving Agent)

Hermes wraps Claude (primary) and Codex as providers with a closed learning loop.
Config: `infra/hermes/config.yaml` (symlinked to `~/.hermes/config.yaml`) · Model: `claude-opus-4-6` via Anthropic.
Repos: https://github.com/NousResearch/hermes-agent · https://github.com/NousResearch/hermes-agent-self-evolution

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
Skills are stored as structured markdown in `~/.hermes/skills/<category>/`. After tasks with 5+ tool calls Hermes auto-generates skills; every ~15 tasks it self-evaluates against past solutions (`creation_nudge_interval: 15` in config.yaml).

A companion repo (`hermes-agent-self-evolution`) runs **GEPA (Genetic-Pareto Prompt Evolution) + DSPy**: reads execution traces, identifies failure causes, proposes improved skills/tool descriptions/system prompts as PRs. Cost ~$2–10/run, no GPU.

RL trajectory logging via `rl_cli.py` + Tinker-Atropos submodule is available but disabled in this config (`rl` toolset not in `platform_toolsets.cli`).

- Sync skills across machines: `hermes skills snapshot export > infra/hermes/skills-snapshot.yaml`
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
- **Default agent type is `codex`** — fattest limits, burn first. Fall back to `gemini` only when codex is rate-limited or the task plays to Gemini's strengths (long context, multimodal, paper edits).
- Never spawn claude subagents (same provider as orchestrator, wasteful).
- Always pass `cwd`; match `effort` to task complexity.
- `mode="edit"` for implementation, `mode="plan"` for review/exploration, `mode="ralph"` for backlog grinding (see `RALPH.md` for invocation, stop conditions, and guards).
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
| RALPH.md | Swarm ralph-mode backlog grinder |
| CHANGELOG.md | Version history |
| infra/USAGE.md | Portable container cheat sheet |
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

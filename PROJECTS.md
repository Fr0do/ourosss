# Projects & Infrastructure

See Notion Research HQ for project details, infrastructure setup, and current state.

## Workflow

### Task Intake
Three entry points, all funnel to the same orchestrator:
- **Telegram bot** (`/status`, `/run`, `/stop`, `/logs`, `/gpu`, `/disk`, `/ckpt`, `/completions`, `/metrics`, `/eval`, `/research`, `/sync`, `/vitals`, `/feature`, `/qr`, `/page`) — `bot/handlers/`
- **Claude Code CLI** directly in `~/experiments/ourosss`
- **Hermes** MCP — memory, skills, delegation, cronjob; running locally and on `kurkin-vllm` via `infra/server/` systemd units

### Issue Routing
- Infra issues: `gh issue create --repo Fr0do/ourosss`
- Research issues: `gh issue create --repo Fr0do/<project>` (s_cot, mmred, bbbo)
- Collaborator updates: `/research log` via Telegram bot → Notion

### Feature Dispatch
`/feature <desc>` via Telegram → GitHub issue with `auto-dev` label → hook injects into terminal agent → agent claims, implements, commits `fixes #N`. First to comment "Picked up" owns it.

Auto-dev agent: `./scripts/auto-dev.sh [--watch|N]` — headless Claude (Opus, planner) with pre-approved permissions, 30min budget; under the hood it spawns codex Swarm agents for the actual edits per the codex-first delegation policy in `CLAUDE.md`. For backlog grinding (multiple issues in a row), use `mode="ralph"` — see `RALPH.md`.

### Delegation
- **Opus** (you, orchestrator) — planning, review, final commit
- **codex** via Swarm — default executor (fattest limits, burn first)
- **gemini** via Swarm — fallback / long-context / multimodal / paper edits
- See `CLAUDE.md` for the agent×effort routing matrix.

### Portable infra
Hermes config + Claude skills + systemd units live in `infra/`. Bootstrap a fresh laptop or server with `bash infra/bootstrap.sh` (laptop) or `bash infra/server/bootstrap-server.sh` (server). Daily cheat sheet: `infra/USAGE.md`.

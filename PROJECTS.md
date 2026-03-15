# Projects & Infrastructure

See Notion Research HQ for project details, infrastructure setup, and current state.

## Workflow

### Task Intake
Telegram bot (`/status`, `/run`, `/stop`, `/logs`) or Claude Code CLI directly.

### Issue Routing
- Infra issues: `gh issue create --repo Fr0do/ourosss`
- Research issues: `gh issue create --repo Fr0do/<project>` (s_cot, mmred, bbbo)
- Collaborator updates: `/research log` via Telegram bot → Notion

### Feature Dispatch
`/feature <desc>` via Telegram → GitHub issue with `auto-dev` label → hook injects into terminal agent → agent claims, implements, commits `fixes #N`. First to comment "Picked up" owns it.

Auto-dev agent: `./scripts/auto-dev.sh [--watch|N]` — headless Claude with pre-approved permissions, 30min budget, claims+implements+pushes.

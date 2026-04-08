---
name: agent-dashboard
description: Show unified agent cost dashboard across Claude Code, Codex, and Gemini. Use when the user asks about agent costs, token usage, spending, or wants to see a dashboard of all AI CLI usage.
allowed-tools: Bash
---

Run the unified agent cost dashboard script.

## Steps

Run:

```bash
python ~/.claude/skills/agent-dashboard/dashboard.py --days 7
```

Adjust `--days` based on user request:
- "today" / "за день" → `--days 1`
- "this week" / "за неделю" → `--days 7`
- "this month" / "за месяц" → `--days 30`

If the user wants raw JSON: add `--json`.

## Fetching remote data (VPN off)

Remote hosts (kurkin-1, kurkin-4) require VPN to be OFF. When VPN is off, fetch and cache:

```bash
python ~/.claude/skills/agent-dashboard/dashboard.py --fetch --days 30
```

Cache is stored in `~/.cache/agent-dashboard/{host}.json` and used automatically on next dashboard run.
SSH requires the mlspace key: `ssh-add ~/.ssh/mlspace__private_key.txt`

## Notes

- Claude Code: `ccusage` locally + cached SSH data from remotes
- Codex: `npx @ccusage/codex daily --json`
- Gemini: no local token tracking, shows active project count only
- VPN conflict: Claude API needs VPN on, kurkin SSH needs VPN off → use cache

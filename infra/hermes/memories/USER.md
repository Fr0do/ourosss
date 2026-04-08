Uses iTerm2 on macOS with zsh. Prefers dark/black terminal background — yellow on white is unreadable.

# Workflow & Stack
- Primary project: ourosss (/Users/mkurkin/experiments/ourosss) — Telegram bot + research orchestration. Repo: Fr0do/ourosss.
- Active research lines: s_cot (chain-of-thought training), long-vqa, bbbo, mmred (skipped from auto-dev).
- Compute: remote nodes kurkin-1, kurkin-4, kurkin-vllm, kurkin-metric.
- Package mgr: uv (uv sync --locked, uv lock, uv run ourosss).

# Delegation Policy (codex-first, 2026-04)
Provider priority:
1. Opus (claude-opus-4-6) — orchestrator only. Planning, architecture, code review, final decisions. NO Sonnet/Haiku subagents (same Anthropic quota).
2. Codex via Swarm — DEFAULT for implementation, refactoring, tests, exploration. Burn first (fattest limits).
3. Gemini via Swarm — fallback after codex AND for: long-context (>200k), multimodal (PDF/images), multi-file paper edits, cheap search via gemini-3-flash.
Hard rule: >20 lines of code → spawn codex Swarm agent, not write inline.

# MCP Stack
hermes (memory/skills/delegation/cronjob), Swarm (codex+gemini), context7 (lib docs), mcp-agent-mail, sentrux (code health), arxiv-mcp-server, playwright.
Portable config: /Users/mkurkin/experiments/ourosss/infra/ — bootstrap.sh symlinks ~/.hermes/config.yaml.

# Conventions
- Issue FIRST before any feature/fix code (gh issue create), close via "fixes #N" in commit.
- Commit prefix: [feat] [fix] [doc] [infra] [bot] [s_cot]. Linear history (rebase, not merge).
- Design: Apple-minimalist, white bg, no dark themes for print.

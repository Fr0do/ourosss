# OuroSSS — Bootstrap Guide

Clone the repo on a new machine and run one script to wire up Hermes + Claude config.

## Prerequisites

| Tool | Install |
|---|---|
| `uv` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| `node` / `npx` | `brew install node` or via nvm |
| `gh` | `brew install gh` |
| `hermes` | `curl -fsSL https://hermes.sh \| bash` |
| Claude Code | `npm install -g @anthropic-ai/claude-code` |

## Bootstrap Steps

```bash
git clone https://github.com/Fr0do/ourosss && cd ourosss
bash infra/bootstrap.sh
cp .env.example .env && $EDITOR .env   # fill in secrets
uv sync --locked
```

## Manual Auth Steps

After bootstrap, authenticate each service once:

```bash
hermes login          # OAuth via browser → Nous Portal (unlocks Codex, OpenAI-Codex fallback)
gh auth login         # GitHub token for auto-dev + issue commands
# Set ANTHROPIC_API_KEY in .env (required for Claude Code + Hermes primary model)
# Set OPENAI_API_KEY  in .env (required for Swarm codex agents)
# Set GEMINI_API_KEY  in .env (required for Swarm gemini agents)
```

## What Gets Symlinked vs Copied

| Source (repo) | Target (machine) | Method |
|---|---|---|
| `infra/hermes/config.yaml` | `~/.hermes/config.yaml` | symlink (existing → `.bak`) |
| `.claude/settings.json` | already in repo, used in-place | — |

Global `~/.claude/settings.json` is NOT overwritten — bootstrap prints a hint so you can merge MCP entries manually if needed.

## Keeping Config in Sync

- Edit `infra/hermes/config.yaml` (in repo) — changes apply immediately via symlink.
- To export your Hermes skills to this repo: `hermes skills snapshot export > infra/hermes/skills-snapshot.yaml`
- Commit both together: `git add infra/ && git commit -m "[infra] sync hermes config"`

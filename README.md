<p align="center">
  <img src="assets/claude-research-logo.svg" width="200" alt="Ouroboros">
</p>

<h1 align="center">Ouroboros</h1>

<p align="center">
  Research governance meta-project — the serpent eats its own tail.
</p>

<p align="center">
  <img src="https://img.shields.io/github/v/release/Fr0do/ouroboros?label=release" alt="Latest release">
  <img src="https://img.shields.io/github/issues/Fr0do/ouroboros" alt="Open issues">
</p>

---

## What It Does

Ouroboros is a coordination layer for autonomous research across multiple projects, machines, and AI agents:

- **Telegram bot** — remote control panel for training runs, monitoring, and crash alerts (`bot/`)
- **Multi-agent orchestration** — native Claude Code agent teams + filesystem fallback (`team/`)
- **Research protocol** — project registry, workflow conventions, cross-project syncing
- **Self-improving workflow** — issue journaling, automatic triage, feature requests from Telegram

## Setup

```bash
cp .env.example .env   # fill in TELEGRAM_TOKEN, AUTHORIZED_USERS
uv sync --locked
uv run ouroboros
```

## Coordination

All updates to shared files are **atomic** — each change is a single, self-contained commit that doesn't leave the repo in a broken state. This enables safe parallel work by multiple Claude Code terminals (see `team/README.md`).

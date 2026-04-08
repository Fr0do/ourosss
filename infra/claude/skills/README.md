# Claude Code Skills — Inventory

Mirror of `~/.claude/skills/` (user-scoped). Source of truth is the laptop;
this dir is the git-tracked backup. Auto-synced by `infra/local/sync-push.sh`
(launchd, every 30 min). Restore on a new laptop with
`bash infra/local/restore-claude-skills.sh`.

**Total: 16 skills · 2026-04-08**

## Research workflow
| Skill | Purpose |
|---|---|
| [compare-runs](compare-runs/SKILL.md) | Compare two GRPO training runs (accuracy/reward/advantage deltas). |
| [completions](completions/SKILL.md) | Analyze GRPO completions/parquets for stats and traces. |
| [deep-research](deep-research/SKILL.md) | Bootstrap a LaTeX paper project with deep literature review. |
| [label-dataset](label-dataset/SKILL.md) | Label datasets via Claude CLI with resume-safe JSONL. |
| [research-log](research-log/SKILL.md) | Log research notes and optionally push to Notion. |
| [research-status](research-status/SKILL.md) | Morning dashboard for active research projects. |
| [review-paper](review-paper/SKILL.md) | Structured review of LaTeX papers. |
| [sync-results](sync-results/SKILL.md) | Sync experiment results from remote to local. |

## Remote / compute
| Skill | Purpose |
|---|---|
| [check-ckpt](check-ckpt/SKILL.md) | List training checkpoints with steps, sizes, and dates. |
| [check-disk](check-disk/SKILL.md) | Check disk usage on remote research servers. |
| [check-gpu](check-gpu/SKILL.md) | Check GPU utilization and memory on remote nodes. |
| [check-training](check-training/SKILL.md) | Check training status across remote nodes and tmux sessions. |
| [remote-exec](remote-exec/SKILL.md) | Run arbitrary commands on remote research servers. |

## General utilities
| Skill | Purpose |
|---|---|
| [agent-dashboard](agent-dashboard/SKILL.md) | Unified agent cost dashboard across Claude Code, Codex, and Gemini. |
| [agent-mail](agent-mail/SKILL.md) | MCP Agent Mail: messaging, identities, and file leases. |
| [bd-to-br-migration](bd-to-br-migration/SKILL.md) | Migrate docs from bd to br with strict transforms. |

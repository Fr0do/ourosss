# OUROBOROS — Research Governance Protocol

> The serpent eats its own tail: each project feeds the next, and the meta-process improves itself.

**Owner**: Maxim Kurkin · **Scope**: all active research · **Interface**: Claude Code + Telegram bot

---

## Active Projects

| Codename | Location | Description | Status |
|---|---|---|---|
| **s_cot** | `kurkin-1:.../s_cot` + `~/experiments/s_cot_tex` | Spectral-R1: energy-based GRPO reasoning (NeurIPS 2025) | Training + paper |
| **mmred** | `kurkin-1:.../mmred` + `~/experiments/mmred` | MMReD: cross-modal dense context benchmark | Eval ongoing |
| **bbbo** | `kurkin-1:.../bbbo/GeneralOptimizer` | Bayesian black-box optimization | Active dev |
| **ouroboros** | `~/experiments/ouroboros` | This meta-project | Bootstrapping |

### s_cot State
- Model: LFM2.5-1.2B-Thinking · Training: GRPO + spectral/accuracy/format rewards, FSDP2, vLLM colocate
- Dataset v4: curriculum (25% med, 35% hard, 40% expert), adjacency lists, 3-6 nodes
- Eval: JSONPathfinder (own), NLGraph, Reasoning-Gym · Baselines: 10 models via vLLM
- Completions: parquets in `spectral-r1-checkpoints/fixed/completions/`
- Roadmap: curriculum training → ablations → results analysis → paper finalization → NeurIPS submission

---

## Infrastructure

- **Compute**: kurkin-1/kurkin-4 share NFS at `/workspace-SR004.nfs2/kurkin/`
- **Python**: `/workspace-SR004.nfs2/kurkin/envs/kurkin_313_torch/bin/python` (conda in tmux broken — use direct paths)
- **Training**: `accelerate launch --config_file fsdp2.yaml train.py` · Set `DS_BUILD_OPS=0` (no nvcc)
- **Services**: Telegram bot on kurkin-1, ClearML (project=s_cot), Notion (eval tracking)
- **CI**: ruff lint on push, release on tag, upstream sync daily, health ping daily
- **RTK**: auto-proxied via hook, 78% token savings

---

## Workflow

### Task Intake
Telegram bot (`/status`, `/run`, `/stop`, `/logs`) or Claude Code CLI directly.

### Team Mode
Native agent teams (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`): lead + 3-5 teammates, shared task list, plan approval gates. Use subagents for focused tasks that only report back.

### Solo Mode
1. Read CLAUDE.md → OUROBOROS.md
2. **Plan in Opus, implement in Sonnet** (mandatory — see CLAUDE.md cost rules)
3. Commit working state before experiments
4. Report completion/blockers to Telegram

### Feature Dispatch
`/feature <desc>` via Telegram → GitHub issue with `auto-dev` label → hook injects into terminal agent → agent claims, implements, commits `fixes #N`. First to comment "Picked up" owns it.

Auto-dev agent: `./scripts/auto-dev.sh [--watch|N]` — headless Claude with pre-approved permissions, 30min budget, claims+implements+pushes.

---

## Conventions

- **Issues-first**: create GH issue before coding any feature/fix. `fixes #N` in commits. Comment progress.
- **Atomic commits**: self-contained, non-breaking. Linear history (rebase).
- **Secrets**: never echo/commit. `.env` gitignored, `env.example` tracked.
- **Design**: Apple-minimalist. White backgrounds, clean lines.
- **Don't**: edit local s_cot (use scp), auto-run training, skip issues for non-trivial work.

---

## Principles

1. **Autonomy with accountability** — agents log everything
2. **Minimal overhead** — RTK, Telegram, GitHub
3. **Reproducibility** — config + seed + commit hash
4. **Cross-pollination** — projects share insights
5. **The loop closes** — this doc evolves
6. **Atomic updates** — self-contained commits
7. **Minimalism** — single source of truth; delete over deprecate

---

## Version
- v6.30.1 — 2026-03-11 — Notion eval tracking, s_cot website page, cost optimization
- v6.30.0 — 2026-03-10 — GitHub Pages, /page command, auto-vitals
- v6.29.0 — 2026-03-09 — /completions baseline, /feature, /vitals, issue journaling
- v6.28.4 — 2026-03-09 — Deep research (22 refs), curriculum dataset, RCD refactor
- v0.1.0 — 2026-03-08 — Initial bootstrap

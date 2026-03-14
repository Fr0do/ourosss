# Projects & Infrastructure

## Active Projects

| Codename | Location | Description | Status |
|---|---|---|---|
| **s_cot** | `kurkin-1:.../s_cot` + `~/experiments/s_cot_tex` | Spectral-R1: energy-based GRPO reasoning | Training + paper |
| **mmred** | `kurkin-1:.../mmred` + `~/experiments/mmred` | MMReD: cross-modal dense context benchmark | Eval ongoing |
| **bbbo** | `kurkin-1:.../bbbo/GeneralOptimizer` | Bayesian black-box optimization | Active dev |
| **ouroboros** | `~/experiments/ouroboros` | Meta-project: governance, bot, tooling | Active |

### s_cot State
- Model: LFM2.5-1.2B-Thinking · Training: GRPO + spectral/accuracy/format rewards, FSDP2, vLLM colocate
- Dataset v4: curriculum (25% med, 35% hard, 40% expert), adjacency lists, 3-6 nodes
- Eval: JSONPathfinder (own), NLGraph, Reasoning-Gym · Baselines: 10 models via vLLM
- Completions: parquets in `spectral-r1-checkpoints/fixed/completions/`
- Roadmap: curriculum training → ablations → results analysis → paper finalization → submission

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

### Issue Routing
- Infra issues: `gh issue create --repo Fr0do/ouroboros`
- Research issues: `gh issue create --repo Fr0do/<project>` (s_cot, mmred, bbbo)
- Collaborator updates: `/research log` via Telegram bot → Notion

### Feature Dispatch
`/feature <desc>` via Telegram → GitHub issue with `auto-dev` label → hook injects into terminal agent → agent claims, implements, commits `fixes #N`. First to comment "Picked up" owns it.

Auto-dev agent: `./scripts/auto-dev.sh [--watch|N]` — headless Claude with pre-approved permissions, 30min budget, claims+implements+pushes.

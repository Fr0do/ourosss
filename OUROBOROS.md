# OUROBOROS — Research Governance Protocol

> The serpent eats its own tail: each project feeds the next, and the meta-process improves itself.

## Identity

**Owner**: Maxim Kurkin (maximbider@gmail.com)
**Scope**: All active research projects — local machine + kurkin-1/kurkin-4 remotes
**Interface layer**: Claude (Cowork for high-level, Code CLI for execution, Telegram bot for fast control)

---

## Active Projects

| Codename | Location | Description | Status |
|---|---|---|---|
| **s_cot** | `kurkin-1:/workspace-SR004.nfs2/kurkin/s_cot` + `~/experiments/s_cot_tex` (paper) | Spectral-R1: latent energy-based GRPO reasoning. NeurIPS 2025. | Training + paper writing |

### s_cot Research Roadmap
1. ~~Literature review: RL for reasoning, PRM, latent steering, spectral methods~~ (done — 22 refs)
2. ~~Paper sections: abstract, introduction, related work, methodology~~ (drafted)
3. **Curriculum training**: Run GRPO with v4 dataset (medium/hard/expert mix) on LFM2.5-1.2B-Thinking
4. **Ablation experiments**: spectral reward on/off, curriculum vs flat difficulty, conciseness reward weight
5. **Results analysis**: accuracy trend, spectral energy correlation with correctness, reasoning length distribution
6. **Paper finalization**: results tables, figures (gen_viz.py), theoretical analysis section, conclusion
7. **Submission**: NeurIPS 2025 deadline

#### s_cot Technical State
- **Model**: LiquidAI/LFM2.5-1.2B-Thinking (hidden=2048, 16 layers)
- **Architecture**: Lfm2Spectral class (`lfm2_spectral.py`) with RayleighConjugateDescent
- **Training**: GRPO with spectral + accuracy + format rewards, vLLM colocate mode, FSDP2
- **Dataset v3**: adjacency list format, 3–6 nodes, single-letter names, forced 2+ hops
- **Trainer v2**: strong conciseness rewards (+0.3 <200chars, −0.3 >1000), max_completion_length=512
- **Completions**: saved as parquets in `spectral-r1-checkpoints/fixed/completions/`

| **long-vqa** | `~/experiments/long-vqa` + `kurkin-1:/workspace-SR004.nfs2/kurkin/long-vqa` | MMReD: cross-modal dense context reasoning benchmark. MERA integration. | Benchmark complete, eval ongoing |
| **bbbo** | `kurkin-1:/workspace-SR004.nfs2/kurkin/bbbo/GeneralOptimizer` | Bayesian black-box optimization framework | Active development |
| **ouroboros** | `~/experiments/ouroboros` | This meta-project: governance, Telegram bot, Notion integration | Bootstrapping |

---

## Infrastructure

### Compute
- **kurkin-1**: `ssh kurkin-1` → `ssh-sr004-jupyter.ai.cloud.ru:2222` (workspace node)
- **kurkin-4**: `ssh kurkin-4` → same host, different user (GPU node)
- **Shared NFS**: `/workspace-SR004.nfs2/kurkin/` (visible from both)
- **Conda env**: `kurkin_313_torch` (Python 3.13, PyTorch, TRL, vLLM, etc.)
- **HF cache**: `/workspace-SR004.nfs2/.cache/huggingface`
- **Conda envs**: `/workspace-SR004.nfs2/kurkin/envs/` (shared across hosts)
- **Direct python**: `/workspace-SR004.nfs2/kurkin/envs/kurkin_313_torch/bin/python`
- **Training launch**: `accelerate launch --config_file fsdp2.yaml train.py`

#### Gotchas
- No nvcc on compute nodes — set `DS_BUILD_OPS=0` to prevent DeepSpeed build errors
- Conda activation in tmux is broken — use direct python/accelerate paths instead

### Services
- **Notion** (notes/knowledge base): Integration ID in `.env`
- **Telegram** (fast control panel): Bot runs on kurkin-1, needs `LOCAL_HOSTNAME=kurkin-1` in `.env`. `/update` command does git pull + restart from Telegram
- **ClearML** (experiment tracking): project=s_cot, auto-logged from training scripts
- **GitLab** (ai.cloud.ru): Source hosting for remote projects

### Token Efficiency
- **RTK** (Rust Token Killer) is installed globally for Claude Code CLI
- All shell commands auto-proxied via hook: `git status` → `rtk git status`
- 60–90% token savings on dev operations
- Run `rtk gain` to see analytics

### GitHub CI
- **Lint** — on push to `main` and PRs, ruff via pre-commit
- **Release automation** — on tag push `v*`, auto-create GitHub release with changelog
- **Upstream sync** — daily ff of `ouroboros-stable` from `razzant/ouroboros:main`
- **Remote health ping** — daily SSH-ping to kurkin-1, Telegram alert on failure

---

## Workflow Protocol

### 1. Task Intake
- **High-level direction**: Cowork mode (this interface) or Telegram `/task` command
- **Execution**: Claude Code CLI on local or remote machines
- **Quick control**: Telegram bot (`/status`, `/run`, `/stop`, `/logs`)

### 2. Team Mode (multi-agent)

**Native agent teams** (preferred): Claude Code has built-in experimental support for coordinated multi-agent work. Enable via settings:

```json
// settings.json
{ "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" } }
```

Architecture: one **team lead** coordinates, **teammates** work in parallel. Shared task list with auto-claiming, direct inter-agent messaging via mailbox, plan approval gates.

Key practices:
- **3–5 teammates** optimal; 5–6 tasks per teammate keeps everyone productive
- **Avoid file conflicts** — each teammate owns different files
- **Plan approval** for risky tasks: teammate plans in read-only mode, lead approves before implementation
- **Subagents vs teams**: use subagents for focused tasks that only report back; use teams when agents need to discuss, challenge, and coordinate
- Display modes: **in-process** (Shift+Down to cycle) or **split panes** (tmux/iTerm2)
- Quality gates via hooks: `TeammateIdle` (keep working), `TaskCompleted` (block completion)
- Cleanup: always via lead (`Clean up the team`), never from teammates
- Limitations: no session resumption for in-process teammates, no nested teams, one team per session

Best use cases: research/review, parallel new modules, debugging with competing hypotheses, cross-layer coordination.

**Filesystem fallback** (`team/`): for manual coordination when native teams aren't available. Uses `team/tasks/*.yaml` (pending→claimed→done) and `team/results/*.md`. See `team/README.md`.

### 3. Solo Mode (single terminal)
When Claude Code runs autonomously on a project:
1. Read CLAUDE.md in the project root first (always)
2. Read OUROBOROS.md for cross-project context
3. **Plan with Opus, implement with Sonnet** — use Opus for design/architecture, delegate code writing to Sonnet subagents when feasible (skip if Opus limits are fine)
4. Commit working state before any experiment
5. Log all runs: name, config, key metrics
6. Push notes to Notion (project page + daily log)
7. Report completion / blockers to Telegram

### 4. Cross-Project Syncing
- s_cot training results → s_cot_tex paper (via scp or git)
- long-vqa eval metrics → s_cot paper (comparison baselines)
- bbbo optimizer → potential hyperparameter backend for s_cot/long-vqa
- All project milestones → Notion research timeline

### 5. Notion Structure
```
Ouroboros (root page)
├── Research Timeline       # Weekly milestones, decisions, blockers
├── s_cot                   # Training logs, metrics, paper drafts
├── long-vqa (MMReD)        # Benchmark results, MERA submission status
├── bbbo                    # Optimizer benchmarks, comparisons
├── Ideas & Backlog         # Future directions, paper ideas
└── Infrastructure          # Env configs, credentials (private), setup notes
```

### 6. Paper Pipeline
1. Experiments run on remotes (kurkin-1/4)
2. Results sync to local `~/experiments/<project>_tex/`
3. LaTeX compiled locally (latexmk)
4. PDF reviewed, iterated
5. Camera-ready → submission

---

## Agent Conventions

### Issues-First Workflow
- **Journaling**: when a user request is a meaningful feature or fix, create a GitHub issue first, then implement and reference it in the commit
- **Progress comments**: comment on the issue with what was done, issues hit, and commit hashes before closing
- **Reopen if needed**: if an issue is closed prematurely (e.g. by `fixes #N` but follow-up work remains), reopen it
- Keeps a public trail of decisions, rationale, and evolution — the project's journal
- Trivial fixes (typos, one-liners) skip the issue — use judgment
- Issue title: short and descriptive. Body: context, motivation, acceptance criteria when relevant

### Feature Dispatch (Telegram → Terminal Agent)
When the user sends `/feature <description>` via Telegram:
1. The bot creates a GitHub issue with the `auto-dev` label
2. A `UserPromptSubmit` hook (`.claude/hooks/check-auto-dev.sh`) runs on every user message in any terminal agent
3. The hook checks `gh issue list --label auto-dev --state open` and injects context if issues exist
4. The terminal agent sees the pending issue, reads it, implements it, commits with `fixes #N`
5. After implementation, remove the `auto-dev` label (auto-removed when issue closes via `fixes #N`)

**Agent responsibilities when picking up an auto-dev issue:**
- Read the full issue body with `gh issue view <N>`
- Comment on the issue acknowledging pickup: "Picked up by terminal agent. Starting implementation."
- Implement the feature following all project conventions (atomic commits, issue references)
- Comment with progress, commit hashes, any blockers
- Close via `fixes #N` in the commit message
- If the task is too large or unclear, comment asking for clarification instead of guessing

**Concurrency**: if multiple terminals are alive, only one should claim the issue. First agent to comment "Picked up" owns it — others should skip.

### Issue Triage Routine
- **At conversation start**: check `gh issue list --repo Fr0do/ouroboros --state open` for new issues
- **Periodically during long sessions**: re-check for newly filed issues (the `UserPromptSubmit` hook does this automatically)
- Triage: read the issue, assess priority, either act on it or acknowledge and plan
- If an issue is filed by the user while working — treat it as a task interrupt
- Issues labeled `auto-dev` have highest priority — implement immediately

### Git Workflow
- **Default: commit & push** for routine changes — no confirmation needed
- **PR + Telegram notify** only for major changes requiring review
- Reference issue numbers in commits (`fixes #N`) to auto-close
- Don't edit local s_cot — update remote via scp or provide filenames
- Don't auto-run training — let user debug and launch

### Design Style
- **Apple-minimalist**: white/transparent backgrounds, clean lines, generous whitespace
- Applies to paper figures, TikZ diagrams, visual abstracts, any generated visuals
- No dark themes for paper/print artifacts — dark is for terminal UIs only

---

## Principles

1. **Autonomy with accountability** — agents work independently but log everything
2. **Minimal overhead** — RTK for tokens, Telegram for control, Notion for memory
3. **Reproducibility** — every experiment has a config, seed, and commit hash
4. **Cross-pollination** — projects share insights, not just code
5. **The loop closes** — OUROBOROS.md itself gets updated as the process improves
6. **Atomic updates** — every file change is a self-contained, non-breaking commit
7. **Minimalism** — single source of truth for every concept; no semantic duplicates in code or docs; delete over deprecate; every file earns its place

---

## Active Task Backlog (GitHub Issues)
All current issues resolved. Check `gh issue list --state open` for latest.

## Version
- v6.30.0 — 2026-03-10 — GitHub Pages site (fr0do.github.io), /page command, /project-page skill, auto-vitals
- v6.29.0 — 2026-03-09 — /completions baseline, /feature→GH issues, /vitals, issue journaling, disk 6h timeout
- v6.28.4 — 2026-03-09 — Deep research (22 refs), curriculum dataset, RCD refactor, crashlog, task backlog
- v6.28.3 (τ) — 2026-03-09 — Telegram bot, GRPO completions, research governance
- v0.1.0 — 2026-03-08 — Initial bootstrap via Cowork

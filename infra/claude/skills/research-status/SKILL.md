---
name: research-status
description: Morning dashboard for all active research projects. Shows tmux sessions, GPU utilization, latest checkpoint step, latest accuracy, and git dirty status in a single table. Use when the user wants a quick overview of all running experiments.
allowed-tools: Bash, Read
---

One-command research status dashboard. Runs all checks in parallel and prints a single summary table.

## Setup

Read `~/.claude/research-env.md` to resolve: remote hosts, project names, remote paths, tmux session names, completions globs, local paper repo paths, and remote Python interpreter path.

## Steps

1. Run all of the following in parallel (single message, multiple Bash calls):

   **a. Tmux sessions:**
   SSH to primary remote, run `tmux ls`.

   **b. GPU utilization:**
   SSH to primary remote, run `nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader`.

   **c. Latest checkpoint step per project:**
   SSH to primary remote. For each project's `remote_path`, find the latest `checkpoint-*` directory (sorted numerically).

   **d. Latest accuracy from completions parquets:**
   SSH to primary remote. For each project, use the remote Python interpreter to load the latest completions parquet via pandas. Auto-detect accuracy reward columns (`*accuracy*reward*`), print mean accuracy.

   **e. Git dirty check for paper repos:**
   For each local paper repo path, run `git status --short | wc -l`.

2. Synthesize all results into a single compact dashboard table:

   ```
   === Research Status — YYYY-MM-DD HH:MM ===

   PROJECT    | TMUX    | LAST_CKPT      | ACCURACY | GIT_DIRTY
   -----------+---------+----------------+----------+----------
   project_a  | sess ✓  | checkpoint-500 | 0.742    | 3 files
   project_b  | sess ✗  | checkpoint-200 | 0.581    | 0 files

   GPU: 0: 95% (38GB/80GB)  1: 12% (4GB/80GB)
   ```

   - ✓ = tmux session exists, ✗ = not running
   - Show `—` for missing data rather than errors
   - Highlight anomalies (GPU 0%, session missing for running project, accuracy drop)

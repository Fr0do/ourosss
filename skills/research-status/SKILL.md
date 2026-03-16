---
name: research-status
description: Morning dashboard for all active research projects. Shows tmux sessions, GPU utilization, latest checkpoint step, latest accuracy, and git dirty status in a single table. Use when the user wants a quick overview of all running experiments.
allowed-tools: Bash
---

One-command research status dashboard. Runs all checks in parallel and prints a single summary table.

## Steps

1. Run all of the following in parallel (single message, multiple Bash calls):

   **a. Tmux sessions:**
   ```bash
   ssh kurkin-1 "tmux ls 2>&1 || echo 'no sessions'"
   ```

   **b. GPU utilization:**
   ```bash
   ssh kurkin-1 "nvidia-smi --query-gpu=index,utilization.gpu,memory.used,memory.total --format=csv,noheader"
   ```

   **c. Latest checkpoint step per project:**
   ```bash
   ssh kurkin-1 "for proj in s_cot long-vqa bbbo/GeneralOptimizer; do base=/workspace-SR004.nfs2/kurkin/\$proj; latest=\$(find \$base -maxdepth 3 -type d -name 'checkpoint-*' 2>/dev/null | sort -t- -k2 -n | tail -1); if [ -n \"\$latest\" ]; then echo \"\$proj: \$(basename \$latest)\"; else echo \"\$proj: no checkpoints\"; fi; done"
   ```

   **d. Latest accuracy from completions parquets:**
   ```bash
   ssh kurkin-1 "/workspace-SR004.nfs2/kurkin/envs/kurkin_313_torch/bin/python -c \"
   import glob, pandas as pd, os
   projects = {
       's_cot': '/workspace-SR004.nfs2/kurkin/s_cot/spectral-r1-checkpoints/fixed/completions/completions_*.parquet',
       'long-vqa': '/workspace-SR004.nfs2/kurkin/long-vqa/**/completions_*.parquet',
       'bbbo': '/workspace-SR004.nfs2/kurkin/bbbo/GeneralOptimizer/**/completions_*.parquet',
   }
   for proj, pattern in projects.items():
       files = sorted(glob.glob(pattern, recursive=True))
       if not files:
           print(f'{proj}: no completions')
           continue
       df = pd.read_parquet(files[-1])
       acc_cols = [c for c in df.columns if 'accuracy' in c and 'reward' in c]
       if acc_cols:
           acc = df[acc_cols[0]].mean()
           print(f'{proj}: acc={acc:.3f} (step {os.path.basename(files[-1])})')
       else:
           print(f'{proj}: no accuracy col')
   \""
   ```

   **e. Git dirty check for paper repos:**
   ```bash
   for repo in ~/experiments/s_cot_tex ~/experiments/long-vqa; do
     if [ -d "$repo" ]; then
       status=$(git -C "$repo" status --short 2>/dev/null | wc -l | tr -d ' ')
       echo "$repo: $status dirty files"
     fi
   done
   ```

2. Synthesize all results into a single compact dashboard table:

   ```
   === Research Status — YYYY-MM-DD HH:MM ===

   PROJECT    | TMUX    | LAST_CKPT      | ACCURACY | GIT_DIRTY
   -----------+---------+----------------+----------+----------
   s_cot      | cot ✓   | checkpoint-500 | 0.742    | 3 files
   long-vqa   | vqa ✗   | checkpoint-200 | 0.581    | 0 files
   bbbo       | bbbo ✓  | checkpoint-100 | —        | —

   GPU: 0: 95% (38GB/80GB)  1: 12% (4GB/80GB)
   ```

   - ✓ = tmux session exists, ✗ = not running
   - Show `—` for missing data rather than errors
   - Highlight anomalies (GPU 0%, session missing for running project, accuracy drop)

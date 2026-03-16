---
name: compare-runs
description: Compare two GRPO training runs side-by-side. Shows accuracy, reward, and advantage delta between two checkpoints or step ranges. Use when the user wants to compare ablations, hyperparameter sweeps, or two training configurations.
allowed-tools: Bash
---

Compare two training runs from the same project. Loads completions parquets for both runs and prints a side-by-side table with delta column.

## Arguments

Parse `$ARGUMENTS`:

- **project**: s_cot (default), long-vqa, bbbo
- **run A** and **run B**: specified as:
  - Step indices: `500 1000` (compare step 500 vs step 1000)
  - Step ranges: `0:50 100:150` (first 50 steps vs steps 100-150, shows mean)
  - Directory suffixes or run IDs: `run_lr1e4 run_lr3e4`
  - `latest` keyword: compare latest two checkpoints
- **metric**: `accuracy` (default), `all` (all reward columns)

## Steps

1. Parse project and run identifiers from `$ARGUMENTS`. Default: s_cot, latest two completions files.

2. SSH to kurkin-1 and run a Python one-liner/heredoc using `/workspace-SR004.nfs2/kurkin/envs/kurkin_313_torch/bin/python`:

   ```python
   import glob, pandas as pd, numpy as np, os

   project = "<project>"
   base_pattern = "<completions_glob_pattern>"

   files = sorted(glob.glob(base_pattern))
   if not files:
       print("No completions found")
       exit(1)

   # Select files for run A and run B
   # If step indices: files[A], files[B]
   # If ranges: files[a_start:a_end], files[b_start:b_end]

   def load_stats(file_list):
       dfs = [pd.read_parquet(f) for f in file_list]
       df = pd.concat(dfs, ignore_index=True)
       reward_cols = [c for c in df.columns if c.endswith('_reward_func')]
       stats = {}
       for col in reward_cols:
           stats[col.replace('_reward_func', '')] = df[col].mean()
       stats['advantage_mean'] = df['advantage'].mean() if 'advantage' in df.columns else float('nan')
       stats['advantage_std'] = df['advantage'].std() if 'advantage' in df.columns else float('nan')
       stats['n_samples'] = len(df)
       stats['steps'] = [os.path.basename(f) for f in file_list]
       return stats

   a_stats = load_stats(files_a)
   b_stats = load_stats(files_b)

   # Print table
   metrics = [k for k in a_stats if k not in ('n_samples', 'steps')]
   print(f"{'Metric':<22} {'Run A':>10} {'Run B':>10} {'Delta':>10}")
   print("-" * 56)
   for m in metrics:
       va = a_stats.get(m, float('nan'))
       vb = b_stats.get(m, float('nan'))
       delta = vb - va
       arrow = '↑' if delta > 0.001 else ('↓' if delta < -0.001 else '→')
       print(f"{m:<22} {va:>10.4f} {vb:>10.4f} {delta:>+10.4f} {arrow}")
   print(f"{'n_samples':<22} {a_stats['n_samples']:>10} {b_stats['n_samples']:>10}")
   print(f"\nRun A: {a_stats['steps']}")
   print(f"Run B: {b_stats['steps']}")
   ```

3. Present the output with:
   - Header: `Run A` and `Run B` labels (file names or user-specified labels)
   - Each reward metric row with delta and direction arrow (↑ better, ↓ worse)
   - Highlight the accuracy row (most important)
   - Note: for accuracy, higher is better; for format rewards, higher is better

## Project Paths (completions)
- s_cot: kurkin-1:/workspace-SR004.nfs2/kurkin/s_cot/spectral-r1-checkpoints/fixed/completions/completions_*.parquet
- long-vqa: kurkin-1:/workspace-SR004.nfs2/kurkin/long-vqa/**/completions_*.parquet
- bbbo: kurkin-1:/workspace-SR004.nfs2/kurkin/bbbo/GeneralOptimizer/**/completions_*.parquet

## Example Usage

```
/compare-runs s_cot latest
/compare-runs s_cot 500 1000
/compare-runs s_cot step -10: step -5:
/compare-runs long-vqa 0:20 50:70
```

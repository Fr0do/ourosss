---
name: compare-runs
description: Compare two GRPO training runs side-by-side. Shows accuracy, reward, and advantage delta between two checkpoints or step ranges. Use when the user wants to compare ablations, hyperparameter sweeps, or two training configurations.
allowed-tools: Bash, Read
---

Compare two training runs from the same project. Loads completions parquets for both runs and prints a side-by-side table with delta column.

## Setup

Read `~/.claude/research-env.md` to resolve: remote host, project remote paths, completions glob patterns, and remote Python interpreter path.

## Arguments

Parse `$ARGUMENTS`:

- **project**: project name from research-env (default: first listed)
- **run A** and **run B**: specified as:
  - Step indices: `500 1000` (compare step 500 vs step 1000)
  - Step ranges: `0:50 100:150` (first 50 steps vs steps 100-150, shows mean)
  - Directory suffixes or run IDs: `run_lr1e4 run_lr3e4`
  - `latest` keyword: compare latest two checkpoints
- **metric**: `accuracy` (default), `all` (all reward columns)

## Steps

1. Parse project and run identifiers from `$ARGUMENTS`.

2. SSH to remote host and run a Python heredoc using the remote interpreter:

   - Glob the project's completions pattern to find all parquet files
   - Select files for run A and run B based on parsed indices/ranges
   - For each run, load parquets with pandas and compute:
     - Auto-detected reward columns: `[c for c in df.columns if c.endswith('_reward_func')]`
     - Mean of each reward column
     - Advantage mean and std (if `advantage` column exists)
     - Sample count

3. Print comparison table:

   ```
   Metric                    Run A      Run B      Delta
   --------------------------------------------------------
   accuracy                 0.4130     0.5200    +0.1070 ↑
   format                   0.9800     0.9900    +0.0100 ↑
   advantage_mean           0.0234    -0.0102    -0.0336 ↓
   advantage_std            1.2340     0.9870    -0.2470 ↓
   n_samples                    64         64
   ```

   - Delta column with direction arrows: ↑ (delta > 0.001), ↓ (delta < -0.001), → (unchanged)
   - Show run file names at the bottom for reference

## Example Usage

```
/compare-runs latest
/compare-runs 500 1000
/compare-runs step -10: step -5:
```

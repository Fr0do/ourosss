---
name: completions
description: Analyse GRPO completions from TRL parquet files. Use when the user asks about completions, model outputs, reward distributions, accuracy trends, or wants to inspect training samples.
allowed-tools: Bash
---

Analyse GRPO completions saved as parquet files (TRL standard format) on remote servers.

## Arguments

Parse `$ARGUMENTS` for flags (any order, all optional):

- **project**: s_cot (default), long-vqa, bbbo
- **stats**: show reward trends across steps
- **traces [N]**: print full prompt+completion for N samples (default 3)
- **step IDX**: Python-style index or slice into the sorted file list (default: -1 = latest)
  - Single index: `step 0` (first), `step -1` (latest), `step -3` (third from end)
  - Slice: `step -3:` (last 3), `step 0:5` (first 5), `step ::2` (every other), `step 1:-1` (all but first and last)
  - With slices, stats mode charts the selected range; dashboard/traces use the first selected file
- **last N**: shorthand for `step -N:` (last N steps, stats mode)
- **correct / wrong**: filter by accuracy reward
- **N** (bare number): sample count

Examples: `s_cot stats last 50`, `traces wrong 2`, `step -1 correct`, `stats step -10:`, `step 0:5 stats`

## Completions paths

Each project may store completions in a known subdirectory:
- s_cot: `spectral-r1-checkpoints/fixed/completions/completions_*.parquet`

## Parquet schema (TRL standard)

Columns: `step`, `prompt`, `completion`, `advantage`, plus reward columns named `*_reward_func` (e.g. `accuracy_reward_func`, `format_reward_func`, `spectral_reward_func`).

## Steps

1. Parse flags from `$ARGUMENTS`. Default: project=s_cot, mode=dashboard (stats summary + 3 brief samples from latest step).

2. SSH to the remote and run a Python one-liner or heredoc script using `/workspace-SR004.nfs2/kurkin/envs/kurkin_313_torch/bin/python`. Use pandas to read parquets.

3. Depending on mode:

   **Dashboard** (default): Load the latest (or specified) step parquet. Print:
   - Step number, completion count
   - Per-reward-column: mean, min, max
   - Advantage: mean, std
   - N brief samples (completion truncated to ~500 chars), each prefixed with reward values

   **Stats**: Load all (or `last N`) parquets. For each step compute accuracy rate (fraction where `accuracy_reward_func == 1`) and mean of each reward column. Print a compact table.

   **Traces**: Load the step parquet. Apply filter if requested. For each sample print the FULL prompt and FULL completion with reward values. These are long — present each trace clearly separated.

4. Auto-detect reward columns — don't hardcode column names. Use `[c for c in df.columns if c.endswith('_reward_func')]`.

5. For filtering: `correct` means `accuracy_reward_func == 1.0`, `wrong` means `accuracy_reward_func != 1.0`.

## Project paths
- s_cot: kurkin-1:/workspace-SR004.nfs2/kurkin/s_cot
- long-vqa: kurkin-1:/workspace-SR004.nfs2/kurkin/long-vqa
- bbbo: kurkin-1:/workspace-SR004.nfs2/kurkin/bbbo/GeneralOptimizer

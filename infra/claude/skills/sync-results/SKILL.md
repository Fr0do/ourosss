---
name: sync-results
description: Sync experiment results from remote servers to local machine. Use when the user wants to download checkpoints, logs, or results from kurkin-1/kurkin-4.
disable-model-invocation: true
allowed-tools: Bash
---

Sync experiment results from remote to local.

## Project sync paths

| Project | Remote path | Local path |
|---------|------------|------------|
| s_cot | `kurkin-1:/workspace-SR004.nfs2/kurkin/s_cot/spectral-r1-checkpoints/` | `~/experiments/s_cot_tex/results/` |
| long-vqa | `kurkin-1:/workspace-SR004.nfs2/kurkin/long-vqa/results/` | `~/experiments/long-vqa/results/` |
| bbbo | `kurkin-1:/workspace-SR004.nfs2/kurkin/bbbo/GeneralOptimizer/results/` | `~/experiments/bbbo-results/` |

## Usage

Sync results for `$ARGUMENTS`:

1. Create local target directory if it doesn't exist
2. Use `rsync -avz --progress` (or `scp -r` as fallback) to download
3. Report what was transferred and total size

If no project specified, show available projects and ask which to sync.

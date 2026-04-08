---
name: check-ckpt
description: List training checkpoints on remote servers with step numbers, sizes, and dates. Use when the user asks about checkpoints, saved models, or training progress snapshots.
allowed-tools: Bash
---

List checkpoints for a research project on remote servers.

## Steps

1. Parse `$ARGUMENTS` to identify the project (s_cot, long-vqa, bbbo). Default to s_cot if ambiguous.

2. SSH to the project's remote host and find checkpoint directories:
   ```bash
   ssh <host> "cd <project_path> && find . -maxdepth 3 -type d \( -name 'checkpoint-*' -o -name 'step_*' -o -name 'epoch_*' \) | while read d; do size=\$(du -sh \"\$d\" 2>/dev/null | cut -f1); date=\$(stat -c '%y' \"\$d\" 2>/dev/null | cut -d. -f1); echo \"\$d  \$size  \$date\"; done | sort -t- -k2 -n"
   ```

3. Present results as a table: path, size, timestamp.

Project paths:
- s_cot: kurkin-1:/workspace-SR004.nfs2/kurkin/s_cot
- long-vqa: kurkin-1:/workspace-SR004.nfs2/kurkin/long-vqa
- bbbo: kurkin-1:/workspace-SR004.nfs2/kurkin/bbbo/GeneralOptimizer

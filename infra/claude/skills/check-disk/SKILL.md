---
name: check-disk
description: Check disk usage on remote research servers and workspace directories. Use when the user asks about free space, disk usage, or storage.
allowed-tools: Bash
---

Check disk usage on remote compute nodes.

## Steps

1. Run these commands in parallel for kurkin-1:
   ```bash
   ssh kurkin-1 "df -h /workspace-SR004.nfs2 | tail -1"
   ssh kurkin-1 "du -sh /workspace-SR004.nfs2/kurkin/s_cot /workspace-SR004.nfs2/kurkin/long-vqa /workspace-SR004.nfs2/kurkin/bbbo /workspace-SR004.nfs2/.cache/huggingface 2>/dev/null"
   ```

2. Present results showing:
   - Filesystem total/used/available/percentage
   - Per-project directory sizes
   - HuggingFace cache size
   - Highlight if usage is above 85%

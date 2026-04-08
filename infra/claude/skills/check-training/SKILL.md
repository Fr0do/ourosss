---
name: check-training
description: Check status of training runs on remote servers. Use when the user asks about training progress, whether jobs are running, or wants to see recent training logs. Covers s_cot, long-vqa, bbbo and any new projects on kurkin-1, kurkin-4, kurkin-vllm, kurkin-metric.
allowed-tools: Bash
---

Check the status of training runs on all remote compute nodes.

## Infrastructure
- **kurkin-1** (1×A100, SR004): tmux sessions for s_cot (cot), long-vqa (vqa), bbbo (bbbo)
- **kurkin-4** (4×A100, SR004): shared NFS with kurkin-1
- **kurkin-vllm** (4×H100, SR008): vLLM inference server
- **kurkin-metric** (4×H100, SR008): reward/eval runs

## Steps

1. Check tmux sessions in parallel on all nodes:
   ```bash
   ssh kurkin-1 "tmux ls 2>&1 || echo 'No sessions'"
   ssh kurkin-4 "tmux ls 2>&1 || echo 'No sessions'"
   ssh kurkin-vllm "tmux ls 2>&1 || echo 'No sessions'"
   ssh kurkin-metric "tmux ls 2>&1 || echo 'No sessions'"
   ```

2. For each active session, capture last 30 lines of output.
   Known sessions on kurkin-1:
   - **s_cot** (`cot`): `ssh kurkin-1 "tmux capture-pane -t cot -p 2>/dev/null | tail -30"`
   - **long-vqa** (`vqa`): `ssh kurkin-1 "tmux capture-pane -t vqa -p 2>/dev/null | tail -30"`
   - **bbbo** (`bbbo`): `ssh kurkin-1 "tmux capture-pane -t bbbo -p 2>/dev/null | tail -30"`
   For kurkin-4/vllm/metric — check whatever sessions are active.

3. Check GPU usage on all nodes in parallel.

4. Summarize:
   - Which projects are actively training / serving
   - Key metrics (loss, step, accuracy)
   - GPU utilization per node
   - Any errors

If `$ARGUMENTS` specifies a project name or host, focus on that only.

---
name: check-gpu
description: Check GPU utilization and memory on remote compute nodes (kurkin-1, kurkin-4, kurkin-vllm, kurkin-metric). Use when the user asks about GPU status, available resources, or whether GPUs are free.
allowed-tools: Bash
---

Check GPU status on all remote compute nodes.

## Nodes
- kurkin-1: 1×A100 (SR004)
- kurkin-4: 4×A100 (SR004)
- kurkin-vllm: 4×H100 (SR008)
- kurkin-metric: 4×H100 (SR008)

## Steps

Run all 4 SSH commands in parallel:
```bash
ssh kurkin-1 "nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader"
ssh kurkin-4 "nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader"
ssh kurkin-vllm "nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader"
ssh kurkin-metric "nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total --format=csv,noheader"
```

Present results as a compact table: node | GPU# | model | util% | mem used/total.
Highlight idle GPUs (0%) and nearly full (>90% memory).

---
name: remote-exec
description: Execute commands on remote research servers via SSH. Use when the user wants to run something on kurkin-1 or kurkin-4, check remote file systems, or interact with remote environments.
allowed-tools: Bash
---

Execute commands on remote compute nodes via SSH.

## Remote hosts
- **kurkin-1**: 1×A100, main workspace (`ssh kurkin-1`), NFS: `/workspace-SR004.nfs2/kurkin/`
- **kurkin-4**: 4×A100 (`ssh kurkin-4`), NFS: `/workspace-SR004.nfs2/kurkin/` (shared с kurkin-1)
- **kurkin-vllm**: 4×H100 (`ssh kurkin-vllm`), NFS: `/workspace-SR008.nfs2/kurkin/`
- **kurkin-metric**: 4×H100 (`ssh kurkin-metric`), NFS: `/workspace-SR008.nfs2/kurkin/`
- **Conda env**: `kurkin_313_torch` (на SR004; на SR008 уточнить после первого логина)

## Usage

Run `$ARGUMENTS` on the appropriate remote host.

If no host is specified, default to kurkin-1. If the command needs conda, wrap it:
```
ssh kurkin-1 "source activate kurkin_313_torch && cd /workspace-SR004.nfs2/kurkin/<project> && <command>"
```

## Project paths
- s_cot: `/workspace-SR004.nfs2/kurkin/s_cot`
- long-vqa: `/workspace-SR004.nfs2/kurkin/long-vqa`
- bbbo: `/workspace-SR004.nfs2/kurkin/bbbo/GeneralOptimizer`

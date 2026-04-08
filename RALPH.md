# RALPH.md — Swarm Ralph Mode

> "Ralph Wiggum" — keeps grinding through a backlog without supervision until someone tells him to stop.

Ralph mode is a **backlog-grinding loop** for the Swarm MCP. Where `mode="edit"` runs one task to completion and `mode="plan"` does a single read-only pass, `mode="ralph"` repeatedly picks the next item off a backlog (GitHub issues, a todo file, a checklist), implements it, commits, and immediately moves to the next — without re-prompting the orchestrator.

This is the right mode for unsupervised overnight grinding, sweeps across many independent files, or chewing through stale `auto-dev` issues while you sleep.

---

## When to use ralph

| Situation | Mode |
|---|---|
| Single feature, you'll review the diff | `edit` |
| Read-only review / exploration / search | `plan` |
| Backlog of >3 independent items, minimal supervision | **`ralph`** |
| Long-context multi-file paper edit | `edit` (gemini, `effort=detailed`) |

Don't use ralph when:
- Items in the backlog have inter-dependencies (one breaks the next)
- You need to review each diff before the next starts
- The work touches shared infrastructure that can break the bot/server

---

## How ralph drives a backlog

```
loop:
  1. fetch next item   (gh issue list / todo file / queue)
  2. claim it           (comment "picked up", set label, lock file)
  3. implement          (read context, make edits, run smoke checks)
  4. commit + push      (referencing the item id)
  5. report             (comment with summary + commit hash)
  6. unless --max reached or queue empty: goto 1
```

The agent runs in its own git sandbox. Commits land directly on the branch the orchestrator pointed it at. The orchestrator (you, Opus) is **not** in the loop between iterations — that's the whole point.

---

## Invocation

### Via Swarm MCP (preferred)

```
Swarm.Spawn(
  task_name="auto-dev-overnight",
  agent_type="codex",
  mode="ralph",
  effort="default",
  cwd="/Users/mkurkin/experiments/ourosss",
  prompt="""Grind through open `auto-dev` labeled issues in Fr0do/ourosss.
For each issue:
  1. Read the issue body and any linked files.
  2. Comment 'Picked up by ralph' to claim it.
  3. Implement following CLAUDE.md conventions.
  4. Run `python -m py_compile` on touched .py files.
  5. Commit with `fixes #N` and push.
  6. Comment with summary + commit hash.
Stop conditions:
  - Backlog empty.
  - Any commit fails to push.
  - You hit a destructive operation (training run, db drop, force push).
Skip patterns: s_cot, mmred, bbbo (research projects, not auto-dev targets).
Max iterations: 10."""
)
```

### Via auto-dev.sh

The existing `scripts/auto-dev.sh` already implements a ralph-style loop in bash (`steam` mode). Use Swarm ralph instead when you want:
- An isolated git sandbox per attempt (auto-dev.sh runs in the live worktree)
- Codex/Gemini executor instead of Claude (cheaper)
- Multiple ralph workers in parallel on disjoint label slices

To run side-by-side:

```bash
./scripts/auto-dev.sh --watch &              # Opus, watches for label-injected issues
# + Swarm ralph in another terminal for the bulk backlog
```

---

## Stop conditions (mandatory)

Ralph runs unattended, so the prompt **must** specify when it stops. Always include at least:

1. **Max iterations** — hard cap (e.g. `Max iterations: 10`)
2. **Empty queue** — what "no more work" looks like for this backlog
3. **Hard guards** — operations the agent must refuse and bail on:
   - Any training run (`accelerate launch`, `torchrun`, `python train.py`)
   - Destructive ops (`rm -rf`, `git push --force`, `DROP TABLE`)
   - Touching `infra/server/` or systemd units (these need review)
   - Modifying `bot/services/config.py` or `.env*` (secrets path)

If the agent hits a guard, it should comment on the current issue with the reason and exit non-zero.

---

## Polling and inspection

```
Swarm.Status(task_name="auto-dev-overnight")    # full diff + bash log
Swarm.Tasks()                                    # all running ralph workers
```

Wait ≥2 min before the first poll. Each loop iteration is typically 3–8 min.

---

## Cost discipline

Ralph multiplies token spend by the loop count. Always:
- Default `agent_type="codex"` (codex limits are the fattest — burn first per `CLAUDE.md`)
- Use `effort="default"` unless the items genuinely need `detailed`
- Set a **finite** `max iterations` — never an unbounded loop
- Monitor via `/agent-dashboard`

Never spawn ralph with `agent_type="claude"` — that drains the same Anthropic quota Opus runs on.

---

## Integration with MCP stack

| MCP server | Role in ralph loops |
|---|---|
| **swarm** | Spawns the ralph worker itself (`mode="ralph"`) |
| **hermes** | Cronjob can trigger ralph nightly (`hermes cronjob add 'swarm spawn ...' --schedule '0 2 * * *'`); memory persists cross-iteration learnings |
| **agent-mail** | File reservations prevent two ralph workers from clobbering each other on shared files |
| **sentrux** | Run `sentrux scan` after a ralph batch to catch coupling/cohesion regressions |

---

## See also

- `CLAUDE.md` — codex-first delegation, agent×effort matrix, Swarm rules
- `scripts/auto-dev.sh` — bash-based predecessor of ralph mode
- `infra/USAGE.md` — portable container ops
- `OUROBOROS.md` — research pipeline this loop ultimately serves

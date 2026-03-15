# Team — Model-Aware Task Dispatch

Tasks are automatically routed to the optimal model based on their type.

## Model routing

| Task type | Model | Agent tool param | When to use |
|---|---|---|---|
| `plan` | Opus (lead) | — | Architecture, design decisions, complex debugging |
| `implement` | Sonnet | `model: "sonnet"` | Code >20 lines, new files, refactoring, tests |
| `explore` | Haiku | `model: "haiku"` | Codebase search, file discovery, summarization |
| `review` | Opus (lead) | — | Code review, security audit, quality check |

## Task YAML schema

```yaml
id: "042"
type: implement          # plan | implement | explore | review
title: "Add /research handler"
project: ourosss         # ourosss | s_cot | mmred | bbbo
status: pending          # pending | running | done | failed
context: |
  Description of what needs to be done.
  Include file paths, acceptance criteria.
result: null             # filled on completion
created: "2026-03-15"
```

## Usage

Tasks can be created via:
- `/feature` Telegram command → auto-creates task YAML
- `gh issue` with `auto-dev` label → picked up by `scripts/auto-dev.sh`
- Manual YAML in `team/tasks/`

The lead (Opus) orchestrates: reads tasks, delegates to subagents with the correct `model` parameter, reviews results.

## Dispatch logic

```
if type == "plan" or "review":
    lead handles directly (Opus)
elif type == "implement":
    Agent(model="sonnet", prompt=context)
elif type == "explore":
    Agent(model="haiku", subagent_type="Explore", prompt=context)
```

Collect project vital stats and display a Unicode terminal dashboard.

Run these commands and collect their output:

```bash
# Git activity (30 days)
git log --oneline --since="30 days ago" | wc -l
git log --format="%ad" --date=short --since="30 days ago" | sort | uniq -c | sort -rn | head -10
git log --shortstat --since="30 days ago" | awk '/files? changed/{a+=$4; d+=$6} END{print "+"a, "-"d}'

# Codebase
find bot -name "*.py" | wc -l
cat bot/**/*.py | wc -l
ls bot/handlers/*.py | wc -l
ls bot/services/*.py | wc -l

# GitHub
gh issue list --repo Fr0do/ouroboros --state open --json number,title
gh issue list --repo Fr0do/ouroboros --state closed --json number | jq length
gh release list --repo Fr0do/ouroboros --limit 1

# Team tasks
ls team/tasks/*.yaml 2>/dev/null | wc -l
grep -l "status: done" team/tasks/*.yaml 2>/dev/null | wc -l
grep -l "status: pending" team/tasks/*.yaml 2>/dev/null | wc -l
```

Format the results as a Unicode dashboard:

```
+------------------------------------------+
|         OUROBOROS VITAL STATS             |
+------------------------------------------+
| Git (30d)                                |
|   Commits: N   |  +X / -Y LOC           |
|   Most active: YYYY-MM-DD (N commits)    |
+------------------------------------------+
| Codebase                                 |
|   Python files: N  |  LOC: N            |
|   Handlers: N  |  Services: N           |
+------------------------------------------+
| GitHub                                   |
|   Issues: N open / N closed             |
|   Latest: vX.Y.Z                        |
+------------------------------------------+
| Team Tasks                               |
|   Total: N  |  Done: N  Pending: N      |
+------------------------------------------+
```

If any command fails, show "N/A" for that section. Keep it concise.

Collect project vital stats + RTK token savings and display a Unicode terminal dashboard.

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

# RTK Token Savings
rtk gain --format json --project
rtk gain --format json --daily --project
```

Format the results as a Unicode dashboard:

```
╔══════════════════════════════════════════╗
║         OUROBOROS VITAL STATS            ║
╠══════════════════════════════════════════╣
║ Git (30d)                                ║
║   Commits: N   |  +X / -Y LOC           ║
║   Most active: YYYY-MM-DD (N commits)    ║
╠──────────────────────────────────────────╣
║ Codebase                                 ║
║   Python files: N  |  LOC: N             ║
║   Handlers: N  |  Services: N            ║
╠──────────────────────────────────────────╣
║ GitHub                                   ║
║   Issues: N open / N closed              ║
║   Latest: vX.Y.Z                         ║
╠──────────────────────────────────────────╣
║ Team Tasks                               ║
║   Total: N  |  Done: N  Pending: N       ║
╠══════════════════════════════════════════╣
║ RTK Token Savings (this project)         ║
║   Commands: N   |  Savings: 83%          ║
║   Tokens saved: 161K / 195K input        ║
║   Avg latency: 274ms                     ║
║   ████████████████████░░░░ 83%           ║
╠──────────────────────────────────────────╣
║ Daily RTK Activity                       ║
║   (render a text sparkline/bar chart     ║
║    from the daily breakdown data)        ║
╚══════════════════════════════════════════╝
```

For the RTK section:
- Parse the JSON summary: total_commands, total_saved, total_input, avg_savings_pct, avg_time_ms
- Build a progress bar from avg_savings_pct (e.g. 83% = 20 filled blocks out of 24)
- From daily data, render a sparkline showing savings per day

After displaying the dashboard, also update the RTK badge data:
```bash
# Write badge JSON for shields.io endpoint badge
python3 -c "
import json
data = json.loads('''$(rtk gain --format json --project)''')
s = data['summary']
pct = s['avg_savings_pct']
color = 'brightgreen' if pct > 70 else 'green' if pct > 50 else 'yellow' if pct > 30 else 'red'
badge = {'schemaVersion': 1, 'label': 'RTK savings', 'message': f\"{pct:.0f}% ({s['total_saved']//1000}K tokens)\", 'color': color}
with open('.github/rtk-badge.json', 'w') as f:
    json.dump(badge, f)
print(f'Badge updated: {pct:.0f}%')
"
```
Then tell the user if the badge JSON was updated so they can commit it.

If any command fails, show "N/A" for that section. Keep it concise.

Update the ourosss project page on fr0do.github.io with current vitals data.

Run these steps:

1. Collect current project vitals:
```bash
cd ~/experiments/ouroboros
# Get git stats
COMMITS=$(git log --oneline --since="30 days ago" | wc -l | tr -d ' ')
LOC=$(cat bot/**/*.py | wc -l | tr -d ' ')
FILES=$(find bot -name "*.py" | wc -l | tr -d ' ')
HANDLERS=$(ls bot/handlers/*.py | wc -l | tr -d ' ')
SERVICES=$(ls bot/services/*.py | wc -l | tr -d ' ')

# GitHub stats
OPEN=$(gh issue list --repo Fr0do/ourosss --state open --json number --jq length 2>/dev/null || echo "—")
CLOSED=$(gh issue list --repo Fr0do/ourosss --state closed --json number --jq length 2>/dev/null || echo "—")
VERSION=$(grep "^- v" OUROBOROS.md | head -1 | sed 's/^- \(v[^ ]*\).*/\1/')
```

2. Update the ouroboros page at `~/experiments/fr0do.github.io/ouroboros/index.html`:
   - Replace metric card values between `<!-- VITALS:START -->` and `<!-- VITALS:END -->` with actual numbers
   - Update the landing page stats at `~/experiments/fr0do.github.io/index.html` too

3. Commit and push:
```bash
cd ~/experiments/fr0do.github.io
git add -A
git commit -m "vitals: update ouroboros metrics ($COMMITS commits, $LOC LOC)"
git push
```

4. Report what was updated: commits, LOC, files, handlers, services, issues, version.

Keep the HTML structure intact — only update the text content inside the metric value divs.

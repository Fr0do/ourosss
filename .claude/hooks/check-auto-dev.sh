#!/bin/bash
# Hook: check for auto-dev issues awaiting implementation.
# Runs on UserPromptSubmit — outputs context if there are pending issues.
# Respects AUTO_DEV_SKIP env var (comma-separated patterns to ignore).
# Exit 0 with stdout → added to Claude's context.

export PATH="$HOME/.local/bin:$PATH:/opt/homebrew/bin:/usr/local/bin"

# Fetch open auto-dev issues with titles
issues_json=$(gh issue list --repo Fr0do/ouroboros --label auto-dev --state open \
    --json number,title 2>/dev/null)

[ -z "$issues_json" ] && exit 0

# Always skip research projects + user-defined patterns
all_skip="s_cot,mmred,bbbo${AUTO_DEV_SKIP:+,$AUTO_DEV_SKIP}"
jq_filter='.'
for pat in $(echo "$all_skip" | tr ',' ' '); do
    pat_lower=$(echo "$pat" | tr '[:upper:]' '[:lower:]')
    jq_filter="${jq_filter} | map(select(.title | ascii_downcase | contains(\"${pat_lower}\") | not))"
done
issues_json=$(echo "$issues_json" | jq "$jq_filter")

issues=$(echo "$issues_json" | jq -r '.[] | "#\(.number): \(.title)"' 2>/dev/null)

if [ -n "$issues" ]; then
    count=$(echo "$issues" | wc -l | tr -d ' ')
    cat <<EOF
[AUTO-DEV DISPATCH] ${count} issue(s) awaiting implementation:
${issues}

To handle: run ./scripts/auto-dev.sh in a separate terminal.
Or implement manually: gh issue view <N> --repo Fr0do/ouroboros
EOF
fi

exit 0

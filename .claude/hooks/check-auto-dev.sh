#!/bin/bash
# Hook: check for auto-dev issues awaiting implementation.
# Runs on UserPromptSubmit — outputs context if there are pending issues.
# Exit 0 with stdout → added to Claude's context.

export PATH="$HOME/.local/bin:$PATH:/opt/homebrew/bin:/usr/local/bin"

issues=$(gh issue list --repo Fr0do/ouroboros --label auto-dev --state open --json number,title --jq '.[] | "#\(.number): \(.title)"' 2>/dev/null)

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

#!/bin/bash
# Hook: check for auto-dev issues awaiting implementation.
# Runs on UserPromptSubmit — outputs context if there are pending issues.
# Terminal agents see this output and can pick up the work.
# Exit 0 with stdout → added to Claude's context.

# Ensure gh is on PATH
export PATH="$HOME/.local/bin:$PATH:/opt/homebrew/bin:/usr/local/bin"

issues=$(gh issue list --repo Fr0do/ouroboros --label auto-dev --state open --json number,title --jq '.[] | "#\(.number): \(.title)"' 2>/dev/null)

if [ -n "$issues" ]; then
    count=$(echo "$issues" | wc -l | tr -d ' ')
    cat <<EOF
[AUTO-DEV DISPATCH] ${count} issue(s) awaiting implementation:
${issues}

ACTION REQUIRED: Pick up an auto-dev issue now.
1. Read it: gh issue view <N> --repo Fr0do/ouroboros
2. Claim it: gh issue comment <N> --repo Fr0do/ouroboros --body "Picked up by terminal agent."
3. Implement the feature following project conventions
4. Commit with 'fixes #N' to auto-close
See OUROBOROS.md "Feature Dispatch" for full protocol.
EOF
fi

exit 0

#!/bin/bash
# auto-dev.sh — Launch a fully autonomous Claude Code agent to implement a GitHub issue.
#
# Usage:
#   ./scripts/auto-dev.sh              # pick up oldest auto-dev issue
#   ./scripts/auto-dev.sh 15           # implement specific issue #15
#   ./scripts/auto-dev.sh --watch      # watch mode: poll for new auto-dev issues
#
# The agent runs non-interactively with pre-approved permissions.
# It reads the issue, implements the feature, commits, pushes, and closes the issue.

set -euo pipefail
cd "$(dirname "$0")/.."

REPO="Fr0do/ouroboros"
MAX_TURNS="${AUTO_DEV_MAX_TURNS:-30}"
MAX_BUDGET="${AUTO_DEV_MAX_BUDGET:-3.00}"
POLL_INTERVAL="${AUTO_DEV_POLL_INTERVAL:-60}"  # seconds, for --watch mode

# ─── Resolve issue number ───

resolve_issue() {
    if [ -n "${1:-}" ] && [ "$1" != "--watch" ]; then
        echo "$1"
        return
    fi
    # Pick oldest open auto-dev issue
    gh issue list --repo "$REPO" --label auto-dev --state open \
        --json number --jq 'last.number' 2>/dev/null
}

# ─── Claim issue (comment to prevent other agents from duplicating) ───

claim_issue() {
    local num=$1
    # Check if already claimed
    local claimed
    claimed=$(gh issue view "$num" --repo "$REPO" --json comments \
        --jq '.comments[].body' 2>/dev/null | grep -c "Picked up by" || true)
    if [ "$claimed" -gt 0 ]; then
        echo "Issue #$num already claimed by another agent. Skipping."
        return 1
    fi
    gh issue comment "$num" --repo "$REPO" \
        --body "Picked up by auto-dev agent. Starting autonomous implementation." >/dev/null 2>&1
    return 0
}

# ─── Run agent ───

run_agent() {
    local num=$1
    echo "[auto-dev] Implementing issue #$num..."

    # Fetch issue details
    local issue_json
    issue_json=$(gh issue view "$num" --repo "$REPO" --json title,body)
    local title body
    title=$(echo "$issue_json" | jq -r '.title')
    body=$(echo "$issue_json" | jq -r '.body')

    local prompt
    prompt="$(cat <<PROMPT
You are an autonomous feature development agent for the ouroboros project.

## Task
Implement GitHub issue #${num}: ${title}

## Issue Description
${body}

## Instructions
1. Read the issue carefully. If the task is unclear, comment on the issue asking for clarification and stop.
2. Read relevant existing code to understand context before making changes.
3. Implement the feature following project conventions (see CLAUDE.md, OUROBOROS.md).
4. Run \`python -m py_compile <file>\` on all modified Python files.
5. Commit with a message referencing \`fixes #${num}\`.
6. Push to main.
7. Comment on the issue with a summary of what was done and commit hashes.

## Constraints
- Follow Apple-minimalist design style for any UI/visual work.
- Keep changes atomic — one self-contained commit per logical change.
- Do NOT modify files unrelated to the issue.
- Do NOT run training or destructive operations.
- If you need user input, comment on the issue and stop.
PROMPT
)"

    claude -p "$prompt" \
        --allowedTools "Read,Edit,Write,Glob,Grep,Bash(git *),Bash(gh *),Bash(python *),Bash(python3 *),Bash(rtk *),Bash(ls *),Bash(wc *),Bash(mkdir *),Bash(chmod *),Bash(cp *)" \
        --dangerously-skip-permissions \
        --append-system-prompt-file "CLAUDE.md" \
        --max-turns "$MAX_TURNS" \
        --output-format text \
        2>&1 | tee "/tmp/auto-dev-${num}.log"

    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo "[auto-dev] Issue #$num implementation complete."
    else
        echo "[auto-dev] Issue #$num agent exited with code $exit_code."
        gh issue comment "$num" --repo "$REPO" \
            --body "Auto-dev agent finished with exit code $exit_code. Manual review may be needed." >/dev/null 2>&1
    fi
}

# ─── Main ───

if [ "${1:-}" = "--watch" ]; then
    echo "[auto-dev] Watch mode. Polling every ${POLL_INTERVAL}s for auto-dev issues..."
    while true; do
        num=$(resolve_issue "")
        if [ -n "$num" ] && [ "$num" != "null" ]; then
            if claim_issue "$num"; then
                run_agent "$num"
            fi
        fi
        sleep "$POLL_INTERVAL"
    done
else
    num=$(resolve_issue "${1:-}")
    if [ -z "$num" ] || [ "$num" = "null" ]; then
        echo "[auto-dev] No auto-dev issues found."
        exit 0
    fi
    if claim_issue "$num"; then
        run_agent "$num"
    fi
fi

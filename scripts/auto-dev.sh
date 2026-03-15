#!/bin/bash
# auto-dev.sh — Autonomous Claude Code agent for implementing GitHub issues.
#
# Usage:
#   ./scripts/auto-dev.sh              # grind all open issues (30min each), oldest first
#   ./scripts/auto-dev.sh 15           # implement only issue #15
#   ./scripts/auto-dev.sh --watch      # poll mode: check for new issues every 60s
#   ./scripts/auto-dev.sh --skip s_cot --skip bbbo   # skip issues matching patterns
#
# Skip patterns match against issue titles (case-insensitive).
# Persistent skips via AUTO_DEV_SKIP env var (comma-separated):
#   AUTO_DEV_SKIP="s_cot,bbbo,mmred" ./scripts/auto-dev.sh
#
# Priority: auto-dev labeled issues first, then oldest open issue.
# The agent can escalate to team mode for complex issues.

cd "$(dirname "$0")/.."

REPO="Fr0do/ourosss"
MAX_TURNS="${AUTO_DEV_MAX_TURNS:-50}"
POLL_INTERVAL="${AUTO_DEV_POLL_INTERVAL:-60}"
TOTAL_TIMEOUT="${AUTO_DEV_TIMEOUT:-1800}"  # 30 min total budget

log() { echo "[auto-dev] $(date '+%H:%M:%S') $*"; }

# ─── Skip patterns ───

SKIP_ISSUES=""        # space-separated issue numbers to skip (runtime)
SKIP_PATTERNS=""      # space-separated title patterns to skip (case-insensitive)

# Research projects are never auto-dev targets
SKIP_PATTERNS="s_cot mmred bbbo"

# Load additional skips from env (comma-separated)
if [ -n "${AUTO_DEV_SKIP:-}" ]; then
    for pat in $(echo "$AUTO_DEV_SKIP" | tr ',' ' '); do
        SKIP_PATTERNS="$SKIP_PATTERNS $pat"
    done
fi

# ─── Resolve issue number ───

resolve_issue() {
    if [ -n "${1:-}" ] && [[ "$1" != --* ]]; then
        echo "$1"
        return
    fi

    # Build jq filter: exclude skipped issue numbers
    local jq_filter='sort_by(.number)'
    for skip in $SKIP_ISSUES; do
        jq_filter="${jq_filter} | map(select(.number != ${skip}))"
    done

    # Exclude issues whose title matches any skip pattern (case-insensitive)
    for pat in $SKIP_PATTERNS; do
        jq_filter="${jq_filter} | map(select(.title | ascii_downcase | contains(\"$(echo "$pat" | tr '[:upper:]' '[:lower:]')\") | not))"
    done

    jq_filter="${jq_filter} | first.number"

    # Only process issues explicitly labeled 'auto-dev'
    local num
    num=$(gh issue list --repo "$REPO" --label auto-dev --state open \
        --json number,title --jq "$jq_filter" 2>/dev/null || true)
    if [ -n "$num" ] && [ "$num" != "null" ]; then
        echo "$num"
        return
    fi
    # No fallback — auto-dev only handles labeled issues
    log "No auto-dev issues found. Nothing to do." >&2
}

# ─── Claim issue ───

claim_issue() {
    local num=$1
    # Check the last comment — if it's a "Picked up" without a follow-up
    # result/timeout/release comment, the issue is still actively claimed.
    local last_comment
    last_comment=$(gh issue view "$num" --repo "$REPO" --json comments \
        --jq '.comments[-1].body // ""' 2>/dev/null || true)
    if echo "$last_comment" | grep -q "Picked up by auto-dev" && \
       ! echo "$last_comment" | grep -q -E "complete|exited|timed out|Releasing|ran out"; then
        log "Issue #$num actively claimed. Skipping."
        return 1
    fi
    gh issue comment "$num" --repo "$REPO" \
        --body "Picked up by auto-dev agent. Starting autonomous implementation." >/dev/null 2>&1
    return 0
}

# ─── Build agent prompt ───

build_prompt() {
    local num=$1 title=$2 body=$3
    cat <<PROMPT
You are an autonomous feature development agent for the ourosss project.

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

## Team Escalation
If the issue is complex (multi-file, multi-component, needs parallel work), you may escalate to a team:
1. Comment on issue #${num} with your **implementation plan** — list subtasks, affected files, risks.
2. Launch a native agent team using \`claude --agent-team\` or spawn subagents via the Agent tool.
3. Coordinate work via issue comments: post progress updates, blockers, and subtask completions.
4. Each teammate should work on a separate concern (e.g. backend vs frontend, tests vs implementation).
5. The team directory \`team/tasks/\` can be used for filesystem-based coordination if needed.
6. After all subtasks complete, do a final integration check before committing.

Only escalate if the issue genuinely needs it — simple features should stay single-agent.

## Constraints
- Follow Apple-minimalist design style for any UI/visual work.
- Keep changes atomic — one self-contained commit per logical change.
- Do NOT modify files unrelated to the issue.
- Do NOT run training or destructive operations.
- If you need user input, comment on the issue and stop.
PROMPT
}

# ─── Run agent ───

run_agent() {
    local num=$1
    local agent_timeout=${2:-$TOTAL_TIMEOUT}  # per-issue cap (or remaining budget)
    local logfile="/tmp/auto-dev-${num}.log"
    log "Implementing issue #$num..."

    local issue_json title body
    issue_json=$(gh issue view "$num" --repo "$REPO" --json title,body) || {
        log "Failed to fetch issue #$num"
        return 1
    }
    title=$(echo "$issue_json" | jq -r '.title')
    body=$(echo "$issue_json" | jq -r '.body')

    local prompt
    prompt="$(build_prompt "$num" "$title" "$body")"

    timeout --foreground "$agent_timeout" claude -p "$prompt" \
        --allowedTools "Read,Edit,Write,Glob,Grep,Agent,Bash(git *),Bash(gh *),Bash(python *),Bash(python3 *),Bash(rtk *),Bash(ls *),Bash(wc *),Bash(mkdir *),Bash(chmod *),Bash(cp *),Bash(claude *)" \
        --dangerously-skip-permissions \
        --append-system-prompt-file "CLAUDE.md" \
        --max-turns "$MAX_TURNS" \
        --verbose \
        --output-format stream-json \
        2>&1 | tee "$logfile"
    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        log "Issue #$num complete."
    elif [ $exit_code -eq 124 ]; then
        log "Issue #$num killed (time budget)."
        gh issue comment "$num" --repo "$REPO" \
            --body "Auto-dev agent ran out of time budget. Work may be partial." >/dev/null 2>&1 || true
    else
        log "Issue #$num exited with code $exit_code."
        gh issue comment "$num" --repo "$REPO" \
            --body "Auto-dev agent finished with exit code $exit_code. Check /tmp/auto-dev-${num}.log." >/dev/null 2>&1 || true
    fi
    log "Log: $logfile"
    return $exit_code
}

# ─── Main ───

MODE="steam"  # default: grind all open issues
ISSUE_ARG=""

while [ $# -gt 0 ]; do
    case "$1" in
        --watch)  MODE="watch" ;;
        --skip)   shift; SKIP_PATTERNS="$SKIP_PATTERNS $1" ;;
        [0-9]*)   MODE="single"; ISSUE_ARG="$1" ;;
    esac
    shift
done

if [ -n "$SKIP_PATTERNS" ]; then
    log "Skip patterns:$SKIP_PATTERNS"
fi

case "$MODE" in
    steam)
        DEADLINE=$(( $(date +%s) + TOTAL_TIMEOUT ))
        log "Grinding through open issues (budget: $((TOTAL_TIMEOUT/60))min)..."
        completed=0
        failed=0
        while true; do
            remaining=$(( DEADLINE - $(date +%s) ))
            if [ "$remaining" -le 0 ]; then
                log "Time budget exhausted. Completed: $completed, Failed: $failed."
                break
            fi
            num=$(resolve_issue "")
            if [ -z "$num" ] || [ "$num" = "null" ]; then
                log "All issues done. Completed: $completed, Failed: $failed."
                break
            fi
            if claim_issue "$num"; then
                log "$((remaining / 60))m remaining."
                if run_agent "$num" "$remaining"; then
                    ((completed++))
                else
                    ((failed++))
                    log "Moving to next issue..."
                fi
                SKIP_ISSUES="$SKIP_ISSUES $num"
            else
                SKIP_ISSUES="$SKIP_ISSUES $num"
            fi
            sleep 5
        done
        ;;

    watch)
        log "Watch mode. Polling every ${POLL_INTERVAL}s..."
        while true; do
            num=$(resolve_issue "")
            if [ -n "$num" ] && [ "$num" != "null" ]; then
                if claim_issue "$num"; then
                    run_agent "$num" || log "Agent failed, continuing watch..."
                fi
            fi
            sleep "$POLL_INTERVAL"
        done
        ;;

    single)
        num=$(resolve_issue "$ISSUE_ARG")
        if [ -z "$num" ] || [ "$num" = "null" ]; then
            log "No open issues found."
            exit 0
        fi
        if claim_issue "$num"; then
            run_agent "$num"
        fi
        ;;
esac

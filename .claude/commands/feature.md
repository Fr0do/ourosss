File a GitHub issue for a new feature, then optionally implement it end-to-end.

## Step 1 — Get the description

If `$ARGUMENTS` is non-empty, use it as the feature description. Otherwise ask: "Describe the feature you want."

## Step 2 — Create the issue

From the description, draft a GitHub issue:

- **Title**: `[feat] <concise summary>` (under 70 chars)
- **Body** (use a HEREDOC for formatting):
  ```
  ## Motivation
  <why this matters, derived from the user's description>

  ## Proposed Change
  <your interpretation of what needs to be built/changed>

  ## Acceptance Criteria
  - [ ] <criterion 1>
  - [ ] <criterion 2>
  - [ ] ...
  ```

Create it:
```bash
gh issue create --repo Fr0do/ourosss --title "[feat] ..." --body "$(cat <<'EOF'
...
EOF
)"
```

Print the issue URL.

## Step 3 — Offer to implement

Ask: **"Want me to implement this now?"**

If **yes**:
1. Read the issue for the spec
2. Plan the work (files to touch, approach)
3. Spawn subagents for parallelizable parts; otherwise implement directly
4. Commit with message referencing `fixes #N`
5. Push to the current branch

If **no**: confirm the issue was filed and stop.

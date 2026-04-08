---
name: research-log
description: Log research notes, experiment results, or ideas. Use when the user wants to record findings, log experiment metrics, or add notes to the research knowledge base.
allowed-tools: Bash, Read, Edit, Write
---

Log research activity to the Ouroboros knowledge base.

## Steps

1. Parse the input: `$ARGUMENTS`
   - Identify: project name (s_cot, long-vqa, bbbo, or general), note type (experiment, idea, blocker, milestone)
   - Extract key content

2. Append to the local research log at `~/experiments/ouroboros/research_log.md`:
   ```markdown
   ### [DATE] - [PROJECT] - [TYPE]
   [Content]
   ```

3. If Notion credentials are available (check `~/experiments/ouroboros/.env`), also push to Notion using:
   ```bash
   cd ~/experiments/ouroboros && python -c "
   from notion_client_lib import add_note
   add_note('PROJECT', 'CONTENT')
   "
   ```

4. Confirm what was logged and where.

Always include a timestamp. Keep entries concise but include enough context to be useful later.

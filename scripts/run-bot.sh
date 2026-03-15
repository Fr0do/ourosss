#!/bin/bash
SESSION_NAME="ouro"
PYTHON="/workspace-SR004.nfs2/kurkin/envs/kurkin_313_torch/bin/python"
DIR="/workspace-SR004.nfs2/kurkin/ouroboros"

cd "$DIR"
git pull --ff-only origin main 2>/dev/null || echo "git pull skipped"

tmux has-session -t "$SESSION_NAME" 2>/dev/null && tmux kill-session -t "$SESSION_NAME"

tmux new-session -d -s "$SESSION_NAME" \
  "cd $DIR && $PYTHON -m bot 2>&1; \
   echo '=== EXITED WITH CODE:' \$? '==='; sleep 86400"

echo "Bot launched in tmux session: $SESSION_NAME"
echo "  tmux a -t $SESSION_NAME"

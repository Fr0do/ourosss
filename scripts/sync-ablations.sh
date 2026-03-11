#!/bin/bash
# Sync ablation experiment files to remote server
# Usage: ./scripts/sync-ablations.sh

LOCAL_DIR="$HOME/experiments/s_cot_tex/s_cot/ablations"
REMOTE="kurkin-1:/workspace-SR004.nfs2/kurkin/s_cot/ablations"

if [ ! -d "$LOCAL_DIR" ]; then
    echo "ERROR: Local ablations dir not found: $LOCAL_DIR"
    exit 1
fi

echo "Syncing ablations to remote..."
scp -r "$LOCAL_DIR/" "$REMOTE/"
echo "Done. Files synced to $REMOTE"
echo ""
echo "To run ablations on remote:"
echo "  ssh kurkin-1"
echo "  cd /workspace-SR004.nfs2/kurkin/s_cot"
echo "  bash ablations/run_ablations.sh [baseline|spectral|curriculum|conciseness|full]"

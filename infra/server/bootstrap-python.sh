#!/usr/bin/env bash
set -euo pipefail

stamp() { date -u '+%Y-%m-%dT%H:%M:%SZ'; }
log() { echo "[$(stamp)] $*"; }
warn() { echo "[$(stamp)] WARN: $*"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck disable=SC1091
source "$SCRIPT_DIR/common.sh"

BASE="$(ourosss_base_dir)"
REPO="$(ourosss_repo_dir)"
CONDA_ENV_PREFIX="${OUROSSS_CONDA_PREFIX:-$BASE/envs/ourosss-py312}"
PYTHON_SPEC="${OUROSSS_PYTHON_SPEC:-python=3.12}"
UV_VERSION="${OUROSSS_UV_VERSION:-0.11.4}"

if ! command -v conda >/dev/null 2>&1; then
  warn "conda not found in PATH"
  echo "Install Miniconda/Mambaforge first, then rerun this script." >&2
  exit 1
fi

CONDA_BASE="$(conda info --base)"
# shellcheck disable=SC1091
source "$CONDA_BASE/etc/profile.d/conda.sh"

mkdir -p "$(dirname "$CONDA_ENV_PREFIX")"

if [ -x "$CONDA_ENV_PREFIX/bin/python" ]; then
  log "Conda env prefix already exists at $CONDA_ENV_PREFIX"
else
  log "Creating conda env prefix $CONDA_ENV_PREFIX with $PYTHON_SPEC"
  conda create -p "$CONDA_ENV_PREFIX" "$PYTHON_SPEC" -y
fi

log "Activating conda env prefix $CONDA_ENV_PREFIX"
conda activate "$CONDA_ENV_PREFIX"

log "Python: $(python --version 2>&1)"
log "Installing pinned uv==$UV_VERSION into $CONDA_ENV_PREFIX"
python -m pip install -U pip
python -m pip install "uv==$UV_VERSION"

if [ ! -d "$REPO" ]; then
  warn "Repo missing at $REPO"
  echo "Clone ourosss into $REPO before running this script." >&2
  exit 1
fi

cd "$REPO"
log "Running uv sync --locked with $(which python)"
uv sync --locked --python "$(which python)"

cat <<EOF

Python bootstrap complete.
Conda env: $CONDA_ENV_PREFIX
Python:    $(which python)
uv:        $(which uv)

To reuse this environment in a new shell:
  source "$CONDA_BASE/etc/profile.d/conda.sh"
  conda activate "$CONDA_ENV_PREFIX"
EOF

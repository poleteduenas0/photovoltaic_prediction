#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# setup.sh - Project setup script for Python projects
#
# This script:
#   - Checks for Python 3.11+ and exits if not found.
#   - Creates a virtual environment in .venv if it doesn't exist.
#   - Activates the virtual environment.
#   - Upgrades pip and wheel.
#   - Installs dependencies from requirements.txt if present.
#   - Installs the project in editable mode if pyproject.toml is present.
#   - Prints instructions for activating the environment and running tests.
# -----------------------------------------------------------------------------
set -euo pipefail

PROJECT_NAME="$(basename "$(pwd)")"
PYTHON_MIN=3.11

echo "[setup] Project: $PROJECT_NAME"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python3 not found. Install Python $PYTHON_MIN+ first." >&2
  exit 1
fi

PY_VER=$(python3 - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)

REQ_MAJOR=${PY_VER%%.*}
REQ_MINOR=${PY_VER#*.}

if [ "$REQ_MAJOR" -lt 3 ] || { [ "$REQ_MAJOR" -eq 3 ] && [ "$REQ_MINOR" -lt 11 ]; }; then
  echo "Python $PYTHON_MIN+ required (found $PY_VER)" >&2
  exit 1
fi

if [ ! -d .venv ]; then
  echo "[setup] Creating virtual environment (.venv)"
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
if [ -f ".venv/bin/activate" ]; then
  source .venv/bin/activate
elif [ -f ".venv/Scripts/activate" ]; then
  source .venv/Scripts/activate
else
  echo "Could not find the virtual environment activation script (.venv/bin/activate or .venv/Scripts/activate)." >&2
  exit 1
fi

python -m pip install --upgrade pip wheel
if [ -f requirements.txt ]; then
  echo "[setup] Installing dependencies from requirements.txt"
  pip install -r requirements.txt
fi

if [ -f pyproject.toml ]; then
  echo "[setup] Installing project in editable mode"
  pip install -e .
fi

if [ -f ".venv/bin/activate" ]; then
  echo "[setup] Done. Activate with: source .venv/bin/activate"
elif [ -f ".venv/Scripts/activate" ]; then
  echo "[setup] Done. Activate with: source .venv/Scripts/activate"
else
  echo "[setup] Done. Could not find activation script."
fi
echo "[setup] Run tests: pytest -q"

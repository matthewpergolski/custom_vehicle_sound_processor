#!/usr/bin/env bash
# Lint and format-check the repo, then run tests if any exist.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

RUFF_VERSION="0.17.3"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found; installing uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  if [[ -f "${HOME}/.local/bin/env" ]]; then
    # shellcheck disable=SC1091
    source "${HOME}/.local/bin/env"
  fi
  export PATH="${HOME}/.local/bin:${PATH}"
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "error: uv is not available" >&2
  exit 1
fi

uvx "ruff==${RUFF_VERSION}" check .
uvx "ruff==${RUFF_VERSION}" format --check .

# No test suite is part of this repository. Discover only files that already
# exist so the script does not invent a suite or a test dependency.
shopt -s nullglob globstar
test_files=(test_*.py *_test.py tests/**/*.py test/**/*.py)
if ((${#test_files[@]} == 0)); then
  echo "No tests found."
  exit 0
fi

echo "Running existing tests: ${test_files[*]}"
python -m unittest discover -s . -p 'test_*.py'

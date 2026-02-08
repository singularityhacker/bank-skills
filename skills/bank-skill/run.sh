#!/usr/bin/env bash
set -euo pipefail

# Prefer uv if present, fall back to python
if command -v uv >/dev/null 2>&1; then
  uv run python -m bankskills.core.bank.handler "$@"
else
  python -m bankskills.core.bank.handler "$@"
fi

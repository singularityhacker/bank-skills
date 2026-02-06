#!/usr/bin/env bash
# Publish a skill to npm (skills.sh registry)

set -euo pipefail

SKILL_NAME="${1:-}"
if [ -z "$SKILL_NAME" ]; then
    echo "Usage: $0 <skill_name>" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Build npm package
python "$SCRIPT_DIR/build_bundle.py" "$SKILL_NAME" --output-dir "$PROJECT_ROOT/dist/npm"

PACKAGE_DIR="$PROJECT_ROOT/dist/npm/$SKILL_NAME"

if [ ! -d "$PACKAGE_DIR" ]; then
    echo "Error: Package directory not found: $PACKAGE_DIR" >&2
    exit 1
fi

# Navigate to package directory and publish
cd "$PACKAGE_DIR"

# Check if already logged in
if ! npm whoami &>/dev/null; then
    echo "Error: Not logged in to npm. Run 'npm login' first." >&2
    exit 1
fi

# Publish
echo "Publishing $SKILL_NAME to npm..."
npm publish

echo "Successfully published $SKILL_NAME to npm"

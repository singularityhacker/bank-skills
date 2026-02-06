#!/usr/bin/env bash
# Publish a skill to ClawHub

set -euo pipefail

SKILL_NAME="${1:-}"
if [ -z "$SKILL_NAME" ]; then
    echo "Usage: $0 <skill_name>" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Build bundle
BUNDLE_PATH=$(python "$SCRIPT_DIR/build_bundle.py" "$SKILL_NAME" --output-dir "$PROJECT_ROOT/dist")

if [ ! -f "$BUNDLE_PATH" ]; then
    echo "Error: Bundle not found: $BUNDLE_PATH" >&2
    exit 1
fi

# Check if clawhub is installed
if ! command -v clawhub &>/dev/null; then
    echo "Error: clawhub CLI not found. Install with: npm i -g clawhub" >&2
    exit 1
fi

# Check if logged in
if ! clawhub whoami &>/dev/null; then
    echo "Error: Not logged in to ClawHub. Run 'clawhub login' first." >&2
    exit 1
fi

# Extract version from bundle name (format: skill-name-version.zip)
BUNDLE_BASENAME=$(basename "$BUNDLE_PATH" .zip)
VERSION=$(echo "$BUNDLE_BASENAME" | sed 's/.*-//')

# Publish to ClawHub
echo "Publishing $SKILL_NAME v$VERSION to ClawHub..."
clawhub publish "$BUNDLE_PATH" \
    --slug "$SKILL_NAME" \
    --name "$SKILL_NAME" \
    --version "$VERSION" \
    --tags latest

echo "Successfully published $SKILL_NAME to ClawHub"

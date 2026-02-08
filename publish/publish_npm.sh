#!/usr/bin/env bash
# Publish a skill to npm (skills.sh registry)

set -euo pipefail

SKILL_NAME="${1:-}"
DRY_RUN="${2:-}"

if [ -z "$SKILL_NAME" ]; then
    echo "Usage: $0 <skill_name> [--dry-run]" >&2
    echo "" >&2
    echo "Options:" >&2
    echo "  --dry-run    Build package and preview contents without publishing" >&2
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Build npm package (not the zip bundle)
echo "Building npm package for $SKILL_NAME..."
python -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path('$PROJECT_ROOT/src')))
from bankskills.publishing.builder import SkillBundleBuilder
builder = SkillBundleBuilder()
package_dir = builder.build_npm_package('$SKILL_NAME', Path('$PROJECT_ROOT/dist/npm'))
print(f'Built npm package at: {package_dir}')
"

PACKAGE_DIR="$PROJECT_ROOT/dist/npm/$SKILL_NAME"

if [ ! -d "$PACKAGE_DIR" ]; then
    echo "Error: Package directory not found: $PACKAGE_DIR" >&2
    exit 1
fi

# Navigate to package directory and publish
cd "$PACKAGE_DIR"

# Check if already logged in (skip for dry-run)
if [ "$DRY_RUN" != "--dry-run" ]; then
    if ! npm whoami &>/dev/null; then
        echo "Error: Not logged in to npm. Run 'npm login' first." >&2
        exit 1
    fi
fi

# Show package contents
echo ""
echo "📦 Package contents:"
echo "-------------------"
npm pack --dry-run
echo ""

if [ "$DRY_RUN" = "--dry-run" ]; then
    echo "✅ DRY RUN - Package built but not published"
    echo ""
    echo "Package details:"
    cat package.json | grep -E '"name"|"version"|"description"'
    echo ""
    echo "To publish for real, run:"
    echo "  ./publish/publish_npm.sh $SKILL_NAME"
    exit 0
fi

# Publish (--access public makes it free for scoped packages)
echo "🚀 Publishing $SKILL_NAME to npm..."
npm publish --access public

echo ""
echo "✅ Successfully published $SKILL_NAME to npm!"
echo "View at: https://www.npmjs.com/package/@singularityhacker/$SKILL_NAME"

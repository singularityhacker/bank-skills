#!/usr/bin/env bash
# Build clean ClawHub skill package - minimal, self-contained, ready for registry submission
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SOURCE_SKILL="$PROJECT_ROOT/skills/bank-skill"
OUTPUT_DIR="$PROJECT_ROOT/dist/clawhub-package"

echo "🏗️  Building ClawHub skill package..."
echo ""

# Clean and create output directory
rm -rf "$OUTPUT_DIR"
mkdir -p "$OUTPUT_DIR/bankskills"

# Copy essential documentation
echo "📄 Copying documentation..."
cp "$SOURCE_SKILL/SKILL.md" "$OUTPUT_DIR/"
cp "$SOURCE_SKILL/CHANGELOG.md" "$OUTPUT_DIR/"
cp "$PROJECT_ROOT/README.md" "$OUTPUT_DIR/"
cp "$PROJECT_ROOT/lobster-bank.png" "$OUTPUT_DIR/"

# Copy executable and metadata
echo "🔧 Copying skill files..."
cp "$SOURCE_SKILL/run.sh" "$OUTPUT_DIR/"
cp "$SOURCE_SKILL/skill.json" "$OUTPUT_DIR/"
cp "$SOURCE_SKILL/pyproject.toml" "$OUTPUT_DIR/"

# Copy examples
echo "📋 Copying examples..."
cp -r "$SOURCE_SKILL/examples" "$OUTPUT_DIR/"

# Copy ONLY essential Python modules (no MCP, CLI, web, publishing)
echo "🐍 Copying essential Python modules..."

# Core modules
cp "$SOURCE_SKILL/bankskills/__init__.py" "$OUTPUT_DIR/bankskills/"
cp "$SOURCE_SKILL/bankskills/sweeper.py" "$OUTPUT_DIR/bankskills/"
cp "$SOURCE_SKILL/bankskills/wallet.py" "$OUTPUT_DIR/bankskills/"

# Core banking (Wise API)
mkdir -p "$OUTPUT_DIR/bankskills/core/bank"
cp -r "$SOURCE_SKILL/bankskills/core/"*.py "$OUTPUT_DIR/bankskills/core/" 2>/dev/null || true
cp -r "$SOURCE_SKILL/bankskills/core/bank/"*.py "$OUTPUT_DIR/bankskills/core/bank/"

# Runtime (handles run.sh execution)
mkdir -p "$OUTPUT_DIR/bankskills/runtime"
cp -r "$SOURCE_SKILL/bankskills/runtime/"*.py "$OUTPUT_DIR/bankskills/runtime/"

# Clean up Mac system files
echo "🧹 Removing .DS_Store files..."
find "$OUTPUT_DIR" -name ".DS_Store" -type f -delete

echo ""
echo "✅ ClawHub package built: $OUTPUT_DIR"
echo ""
echo "Package contents:"
cd "$OUTPUT_DIR"
tree -L 2 -a 2>/dev/null || find . -type f | head -20
echo ""
echo "Package size:"
du -sh "$OUTPUT_DIR"
echo ""
echo "Next steps:"
echo "  1. Review: ls -la $OUTPUT_DIR"
echo "  2. Test locally: cd $OUTPUT_DIR && echo '{\"action\": \"balance\"}' | ./run.sh"
echo "  3. Submit to ClawHub: Upload the $OUTPUT_DIR directory"

#!/usr/bin/env bash
# Build the .mcpb extension for Claude Desktop from mcp-extension/
# Output: dist/bank-skills-0.1.0.mcpb (or mcp-extension/bank-skills-0.1.0.mcpb for local testing)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
MCP_DIR="$PROJECT_ROOT/mcp-extension"
DIST_DIR="$PROJECT_ROOT/dist"
VERSION="0.1.0"
OUTPUT_NAME="bank-skills-${VERSION}.mcpb"

echo "🔨 Building MCP extension (.mcpb)..."
echo ""

# Create dist if needed
mkdir -p "$DIST_DIR"

# Build from mcp-extension, excluding .mcpbignore patterns
cd "$MCP_DIR"
zip -r "$DIST_DIR/$OUTPUT_NAME" . \
  -x ".venv/*" \
  -x "*__pycache__*" \
  -x "*.pyc" \
  -x "*.DS_Store" \
  -x "*/.DS_Store" \
  -x "*.mcpb" \
  -q

echo "✅ Built: $DIST_DIR/$OUTPUT_NAME"
echo ""
echo "To install locally:"
echo "  1. Double-click $DIST_DIR/$OUTPUT_NAME"
echo "  2. Click 'Install' when Claude Desktop prompts"
echo "  3. Add your WISE_API_TOKEN in Settings → Extensions → Bank Skills"
echo "  4. Restart Claude Desktop"
echo ""
echo "Test prompts:"
echo "  - \"Check my Wise balance\" (Wise)"
echo "  - \"Create a ClawBank wallet\" (Sweeper)"
echo "  - \"What's in my wallet?\" (Sweeper)"

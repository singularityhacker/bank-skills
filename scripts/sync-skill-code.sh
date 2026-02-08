#!/usr/bin/env bash
# Sync source code from src/ to skills/bank-skill/
# Run this after making changes to src/bankskills/ code

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SKILL_DIR="$PROJECT_ROOT/skills/bank-skill"
SRC_DIR="$PROJECT_ROOT/src/bankskills"

echo "🔄 Syncing source code to skill directory..."
echo ""

# Remove old bankskills directory in skill
if [ -d "$SKILL_DIR/bankskills" ]; then
    echo "  Removing old bankskills/ directory..."
    rm -rf "$SKILL_DIR/bankskills"
fi

# Copy fresh source code
echo "  Copying src/bankskills/ → skills/bank-skill/bankskills/..."
cp -r "$SRC_DIR" "$SKILL_DIR/bankskills"

# Update pyproject.toml with minimal dependencies (only what the skill needs)
echo "  Updating pyproject.toml..."
cat > "$SKILL_DIR/pyproject.toml" << 'EOF'
[project]
name = "bank-skill"
version = "0.1.4"
description = "Bank skills: check balances, send money, and get receive details via Wise"
requires-python = ">=3.10"
dependencies = [
    "fastmcp>=0.9.0",
    "httpx>=0.25.0",
    "pydantic>=2.0.0",
]
EOF

echo ""
echo "✅ Sync complete!"
echo ""
echo "Updated:"
echo "  - skills/bank-skill/bankskills/ (all Python source code)"
echo "  - skills/bank-skill/pyproject.toml (dependencies)"
echo ""
echo "Next steps:"
echo "  1. Test locally: cd skills/bank-skill && echo '{\"action\": \"balance\"}' | ./run.sh"
echo "  2. Commit changes: git add skills/bank-skill/ && git commit -m 'Update skill code'"
echo "  3. Push to GitHub: git push"

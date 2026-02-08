# Publishing Guide

## Prerequisites

1. **npm account** - Create at [npmjs.com](https://npmjs.com)
2. **npm login** - Run `npm login` and authenticate
3. **GitHub repo** - Already set: `https://github.com/singularityhacker/bank-skills`

## Publishing to skills.sh (via npm)

Skills.sh uses npm as its backend registry. When you publish to npm, it automatically becomes discoverable on skills.sh.

### Step 1: Build the Package

```bash
python publish/build_bundle.py bank-skill --output-dir dist/npm
```

This creates:
- `dist/npm/bank-skill/` directory
- `dist/npm/bank-skill/package.json` with proper metadata
- All skill files (SKILL.md, run.sh, examples/)

### Step 2: Review package.json

Check the generated package:

```bash
cat dist/npm/bank-skill/package.json
```

Expected structure:
```json
{
  "name": "@singularityhacker/bank-skill",
  "version": "0.1.0",
  "description": "Check balances, send money, and share receive details via Wise",
  "files": ["SKILL.md", "run.sh", "src"],
  "bin": {
    "bank-skill": "./run.sh"
  }
}
```

### Step 3: Publish to npm

**Option A: Manual publish**

```bash
cd dist/npm/bank-skill
npm publish
```

**Option B: Use publish script**

```bash
./publish/publish_npm.sh bank-skill
```

The script:
- Builds the package
- Checks npm login status
- Publishes to npm registry

### Step 4: Verify on skills.sh

After publishing, your skill should appear on:
- **npm**: `https://www.npmjs.com/package/@singularityhacker/bank-skill`
- **skills.sh**: `https://skills.sh/` (search for "bank-skill")

### Installation by Users

Once published, users can install via:

```bash
npx skills add singularityhacker/bank-skills
```

Or via ClawHub:

```bash
claw skill add singularityhacker/bank-skills
```

## Alternative: Direct GitHub Installation

Users can also install directly from GitHub without npm:

```bash
npx skills add singularityhacker/bank-skills
```

This pulls from your GitHub repo's `skills/bank-skill/` directory.

## Publishing Updates

To publish a new version:

1. Update version in `skills/bank-skill/skill.json`
2. Rebuild bundle: `python publish/build_bundle.py bank-skill`
3. Republish: `./publish/publish_npm.sh bank-skill`

## ClawHub Publishing (Alternative)

If you want to publish to ClawHub instead of npm:

```bash
./publish/publish_clawhub.sh bank-skill
```

Requires `CLAWHUB_TOKEN` environment variable.

## Troubleshooting

### "Not logged in to npm"
Run `npm login` first.

### "Package name too similar"
Change package name in builder.py from `@singularityhacker/bank-skill` to `@your-org/bank-skill`.

### "Version already exists"
Increment version in `skills/bank-skill/skill.json` and rebuild.

## Distribution Channels Summary

1. **npm/skills.sh** (Recommended)
   - Widest reach
   - Auto-indexed on skills.sh
   - Standard package management

2. **GitHub Direct**
   - No npm account needed
   - Users install via `npx skills add owner/repo`
   - Always uses latest code

3. **MCP Extension (.mcpb)**
   - For Claude Desktop users only
   - Double-click install
   - Separate from skills.sh

4. **ClawHub**
   - Alternative registry
   - Requires separate account

## Current Status

- ✅ Bundle built: `dist/bank-skill-0.1.0.zip`
- ✅ MCP extension built: `dist/bank-skills-0.1.0.mcpb`
- ✅ GitHub repo ready
- ✅ LICENSE added
- ⏳ **Ready to publish to npm/skills.sh**

## Next Steps

1. Ensure `npm login` is complete
2. Run `./publish/publish_npm.sh bank-skill`
3. Verify package appears on npmjs.com
4. Check skills.sh for indexing (may take a few minutes)
5. Update README with installation instructions

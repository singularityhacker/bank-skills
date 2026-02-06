# Skill Shop Template

This repository serves as a template for creating new skill projects. Use this as a starting point when building new skills that will be published to multiple registries.

## Using This Template

### Option 1: GitHub Template

1. Click "Use this template" on GitHub
2. Create a new repository from this template
3. Clone your new repository
4. Customize for your specific skill

### Option 2: Manual Copy

1. Copy this entire repository structure
2. Remove the `skills/example-skill/` directory
3. Create your own skill in `skills/<your-skill-name>/`
4. Update project metadata in `pyproject.toml`

## Creating a New Skill

1. **Create skill directory**:
   ```bash
   mkdir -p skills/my-new-skill/examples
   ```

2. **Create SKILL.md** with YAML frontmatter:
   ```markdown
   ---
   name: my-new-skill
   description: What this skill does
   homepage: https://github.com/yourusername/my-new-skill
   metadata: {"openclaw":{"emoji":"🔧","requires":{"bins":["python"],"env":[]},"primaryEnv":""}}
   ---
   
   # My New Skill
   
   ## Purpose
   ...
   ```

3. **Create run.sh** wrapper:
   ```bash
   #!/usr/bin/env bash
   set -euo pipefail
   
   if command -v uv >/dev/null 2>&1; then
     uv run python -m skillshop.runtime.runner "my-new-skill" "$@"
     else
     python -m skillshop.runtime.runner "my-new-skill" "$@"
   fi
   ```
   Make it executable: `chmod +x skills/my-new-skill/run.sh`

4. **Create skill.json** (optional):
   ```json
   {
     "name": "my-new-skill",
     "version": "0.1.0",
     "entrypoint": "./run.sh",
     "interfaces": ["cli", "mcp"],
     "inputs": "json-stdin",
     "outputs": "json-stdout"
   }
   ```

5. **Add examples** in `examples/` directory (documentation only)

6. **Implement core logic** in `src/skillshop/core/` or in the skill's own directory

## Development Workflow

1. **Local development**:
   ```bash
   # Install dependencies
   pip install -e .
   
   # Run CLI
   python -m skillshop.cli.app
   
   # Run web UI
   textual-web run skillshop.web.app
   
   # Run MCP server
   python -m skillshop.mcp.server
   ```

2. **Test skill execution**:
   ```bash
   python -m skillshop.runtime.runner my-new-skill --arg value
   ```

3. **Build bundle**:
   ```bash
   python publish/build_bundle.py my-new-skill
   ```

4. **Publish**:
   ```bash
   # To npm (skills.sh)
   bash publish/publish_npm.sh my-new-skill
   
   # To ClawHub
   bash publish/publish_clawhub.sh my-new-skill
   ```

## Key Principles

- **Python-first**: All business logic in Python
- **Self-contained skills**: Each skill should be independently shippable
- **Multi-surface**: Support CLI, Web UI, and MCP
- **Multi-registry**: Publish to skills.sh, ClawHub, and skillsmp.com
- **Documentation**: Link to repository, keep examples as documentation

## Customization Points

- Update `pyproject.toml` with your project name and dependencies
- Modify `src/skillshop/core/base.py` if you need custom base classes
- Extend `src/skillshop/runtime/runner.py` for custom execution logic
- Update `.github/workflows/publish.yml` for your CI/CD needs

## Next Steps

1. Remove this TEMPLATE.md (or customize it)
2. Update README.md with your project-specific information
3. Create your first skill following the structure above
4. Test locally before publishing
5. Set up registry credentials (NPM_TOKEN, CLAWHUB_TOKEN) in GitHub Secrets

---

*Remember: This is a template. Customize it to fit your needs!*

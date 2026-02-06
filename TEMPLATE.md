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

---

# Original Readme

# Skill Shop

A factory system for creating, testing, and publishing AI agent skills to multiple registries. This project provides a repeatable, autonomous production process that transforms seed ideas into fully-functional, distributable skills.

## Mission

**Skill Shop** is designed to demonstrate AI development capabilities through the systematic creation and publication of agent skills. By establishing a streamlined factory process, we can:

- Generate a steady stream of small, impactful projects
- Maximize visibility by publishing to multiple registries with minimal overhead
- Create a repeatable, improvable production workflow
- Build skills that are primarily Python-based with natural language interfaces

## The Factory Process

The Skill Shop operates through a six-stage pipeline that transforms ideas into published skills:

### 1. Seed Input
**Input**: A seed idea in the form of:
- A link to documentation or an API
- A public API specification
- A code package or library
- A problem statement

**Output**: Raw material for skill development

### 2. QA Discovery
An AI agent performs research and generates Q&A questions to fully scope the skill requirements. This stage ensures all edge cases, dependencies, and constraints are identified before development begins.

### 3. PRD (Product Requirements Document)
An agent compiles all research documents and Q&A into a comprehensive Product Requirements Document. This PRD must be **approved by a human** before proceeding to the next stage, ensuring alignment with goals and feasibility.

### 4. User Stories
The PRD is analyzed and broken down into small, independently testable user stories. Each story is designed to:
- Be completable within a single context window
- Minimize dependency on broader project context
- Be independently testable and verifiable

### 5. The Development Loop
A semi-autonomous development loop that:
- Consumes user stories one by one
- Marks stories complete in a checklist
- Can operate across multiple context windows (e.g., overnight)
- Includes **closed-loop verification**:
  - CLI functionality is tested and visible
  - Web UI is tested and visible
  - Integration across all components is verified
- Logs bugs as new todo items
- Continues until integration passes, no new bugs are created, and the process completes

### 6. Generated Artifacts
Each skill produces a complete set of artifacts:

- **Raw Python files** (Python-first approach)
- **CLI interface** (Textual TUI)
- **Web application** (Textual Web - same codebase as CLI)
- **MCP server** (FastMCP)
- **Standard skill format** following the [AgentSkills pattern](https://github.com/agentskills/agentskills)

## Technical Architecture

### Core Principles

1. **Python-First Runtime**: All business logic lives in Python. Node/npm is used only as a distribution and orchestration layer, not as the execution runtime.

2. **Skill as Contract**: A skill is a folder containing:
   - `SKILL.md` - Natural language interface contract (what the agent reads)
   - `run.sh` - Executable wrapper that calls Python
   - Optional: `skill.json`, examples, tests

3. **One Codebase, Multiple Surfaces**:
   - Script/library API (pure Python)
   - CLI + Web UI (Textual)
   - MCP server (FastMCP)

4. **Multi-Registry Publishing**: Skills are packaged once but can be published to multiple registries:
   - [skills.sh](https://skills.sh/) (npm-based distribution)
   - [ClawHub](https://clawhub.ai/) (OpenClaw ecosystem)
   - [skillsmp.com](https://skillsmp.com/)

### Repository Structure (Proposed)

```
skill-shop/
├── pyproject.toml
├── README.md
├── src/
│   └── skillshop/
│       ├── core/              # Pure Python logic (no UI, no MCP)
│       ├── cli/               # Textual TUI
│       ├── web/               # Textual web mode
│       ├── mcp/               # FastMCP server
│       ├── runtime/           # Skill loader + execution harness
│       └── publishing/        # Multi-registry publishing helpers
├── skills/                    # Agent-facing skill registry
│   └── <skill-name>/
│       ├── SKILL.md          # YAML frontmatter + instructions
│       ├── skill.json        # Optional metadata
│       ├── run.sh            # Wrapper entrypoint
│       └── examples/          # Golden input/output examples
├── publish/                   # Publishing toolchain
│   ├── build_bundle.py
│   ├── publish_npm.sh
│   └── publish_clawhub.sh
└── .github/
    └── workflows/
        └── publish.yml       # CI/CD for multi-registry publishing
```

### Skill Format

Each skill follows the standard format:

**SKILL.md** (with YAML frontmatter):
```markdown
---
name: my-skill
description: One-liner describing what it does.
homepage: https://example.com
metadata: {"openclaw":{"emoji":"🦞","requires":{"bins":["uv"],"env":["MY_API_KEY"]},"primaryEnv":"MY_API_KEY"}}
---

# My Skill

## Purpose
One sentence describing what it does.

## Inputs
- List inputs (types, format, constraints)

## Outputs
- What it returns (types, format)

## Usage
Command: `<entrypoint> --arg1 ...`

## Failure modes
- What errors look like
- Retry guidance
```

**run.sh** (execution wrapper):
```bash
#!/usr/bin/env bash
set -euo pipefail

# Prefer uv if present, fall back to python
if command -v uv >/dev/null 2>&1; then
  uv run python -m skillshop.runtime.runner "<skill_name>" "$@"
else
  python -m skillshop.runtime.runner "<skill_name>" "$@"
fi
```

## Design Decisions

### Distribution Strategy

**npm as Universal Transport Layer**: npm has become a universal binary distribution layer, not just a JavaScript ecosystem. It handles OS detection, versioning, caching, and global installs with zero-friction user experience. Python skills are wrapped in minimal npm packages that contain `SKILL.md` and wrapper scripts, bootstrap Python environments on install, and call Python entrypoints—never executing Node code for business logic.

**Multi-Registry Publishing**: Skills are packaged once but published to multiple registries:
- **skills.sh**: Git-based discovery, npm distribution, ephemeral CLI (`npx skills add`)
- **ClawHub**: Versioned bundle registry, persistent tool (`clawhub publish`)
- **skillsmp.com**: Additional distribution channel

The publishing layer handles format conversions and registry-specific requirements automatically. Versions are synchronized across registries to keep the process simple and maintainable.

### Development Process

**PRD Approval**: Human approval of the PRD focuses on ensuring the project hasn't diverged from the original business use case, rather than detailed technical review. This provides a lightweight gate while maintaining alignment with goals.

**User Story Granularity**: User stories are designed to consume no more than 60% of a typical context window, ensuring they can be completed independently within a single session while minimizing dependencies on broader project context.

**Development Loop Autonomy**: The development loop operates semi-autonomously, with initial iterations being observed to establish appropriate guardrails. The system is designed to learn and adapt based on experience.

**Testing Approach**: Unit tests are written for each user story during development. Integration tests run when all user stories are complete. The UI is made visible to the agent for testing purposes, though visual regression testing may be added later based on need.

**Bug Handling**: The development loop can continue with non-critical bugs, allowing progress while issues are tracked and addressed. Critical bugs may require intervention depending on their impact.

### Technical Architecture

**Self-Contained Skills**: Each skill is designed to be independently shippable and self-contained. This ensures skills can be distributed, installed, and used without dependencies on the broader Skill Shop infrastructure.

**MCP Integration**: An MCP server is built for each skill to support frameworks that don't yet support the SKILLS approach. By building the MCP server, we automatically advertise its availability. MCP registry integration will be explored as the ecosystem evolves.

**Textual UI Constraints**: The UI is built using the Textual framework, working within its capabilities and limitations. This provides a consistent, terminal-native experience across CLI and web modes.

**Dependency Management**: The approach to dependency management (shared vs. per-skill `pyproject.toml`) is still being refined based on practical experience with skill development.

### Quality & Standards

**Documentation**: Skills link to their source repositories for detailed documentation. This project serves as a template for future skill development, with each skill having its own repository. Examples are provided as documentation rather than executable tests.

**Skill Validation**: Validation requirements for publishing (SKILL.md format, run.sh correctness, etc.) are still being defined and will evolve based on registry requirements and practical experience.

**Publishing Automation**: The automation strategy for publishing (fully automated vs. manual approval) and versioning approach are still being determined based on workflow needs.

### Project Scope

**Template System**: This project is designed as a template that can be instantiated for new skill projects. It establishes the patterns, structure, and tooling that will be reused across all skill development.

**Skill Discovery**: The project relies on external registries for skill discovery rather than maintaining a local registry. A personal website will showcase all created skills for portfolio purposes.

**Success Metrics**: Success is measured through GitHub stars and community engagement rather than telemetry or usage tracking. This keeps the focus on building useful, discoverable skills.

**Project Nature**: This is a personal project designed to demonstrate agentic development capabilities and build a portfolio of work in the AI agent ecosystem. While contributions are welcome, the primary goal is showcasing expertise in this domain.

## References

- [Skills Standard](https://github.com/anthropics/skills) - The canonical skill format
- [FastMCP](https://gofastmcp.com/getting-started/welcome) - Python MCP server framework
- [Textual](https://www.textualize.io/projects/) - Python TUI framework
- [Textual Web](https://github.com/Textualize/textual-web) - Web mode for Textual apps
- [AgentSkills Pattern](https://github.com/agentskills/agentskills) - Standard skill structure

---

*"Skillshop as a product, skills as content."*


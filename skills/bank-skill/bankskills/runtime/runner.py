"""
Skill execution runner.

This module provides the execution harness for running skills.
It's called by the run.sh wrappers in each skill directory.
"""

import sys
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional
from bankskills.runtime.registry import SkillRegistry


class SkillRunner:
    """
    Executes skills from the registry.
    """
    
    def __init__(self, registry: Optional[SkillRegistry] = None):
        """
        Initialize the skill runner.
        
        Args:
            registry: Optional skill registry instance
        """
        self.registry = registry or SkillRegistry()
    
    def run_skill(self, skill_name: str, args: Optional[list] = None, stdin_data: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute a skill.
        
        Args:
            skill_name: Name of the skill to execute
            args: Command-line arguments for the skill
            stdin_data: Optional stdin input (JSON string)
            
        Returns:
            Dictionary containing execution results
        """
        try:
            skill_metadata = self.registry.load_skill_metadata(skill_name)
            skill_path = self.registry.get_skill_path(skill_name)
            
            # Find the run script
            run_script = skill_path / "run.sh"
            if not run_script.exists():
                return {
                    "success": False,
                    "error": f"run.sh not found for skill '{skill_name}'"
                }
            
            # Prepare command
            cmd = [str(run_script)] + (args or [])
            
            # Execute
            result = subprocess.run(
                cmd,
                input=stdin_data.encode() if stdin_data else None,
                capture_output=True,
                text=True,
                cwd=str(skill_path)
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def main():
    """
    CLI entry point for skill runner.
    
    Usage: python -m bankskills.runtime.runner <skill_name> [args...]
    """
    if len(sys.argv) < 2:
        print("Usage: python -m bankskills.runtime.runner <skill_name> [args...]", file=sys.stderr)
        sys.exit(1)
    
    skill_name = sys.argv[1]
    args = sys.argv[2:] if len(sys.argv) > 2 else []
    
    # Read stdin if available (for JSON input)
    stdin_data = None
    if not sys.stdin.isatty():
        stdin_data = sys.stdin.read()
    
    runner = SkillRunner()
    result = runner.run_skill(skill_name, args, stdin_data)
    
    if result["success"]:
        if result.get("stdout"):
            print(result["stdout"], end="")
        sys.exit(0)
    else:
        error_msg = result.get("error", "Unknown error")
        if result.get("stderr"):
            print(result["stderr"], file=sys.stderr)
        print(f"Error: {error_msg}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

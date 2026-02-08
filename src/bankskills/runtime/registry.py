"""
Skill registry for discovering and loading skills.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
import yaml
import json


class SkillRegistry:
    """
    Registry for discovering and managing skills.
    
    Scans the skills/ directory and provides access to skill metadata
    and execution capabilities.
    """
    
    def __init__(self, skills_dir: Optional[Path] = None):
        """
        Initialize the skill registry.
        
        Args:
            skills_dir: Path to skills directory. Defaults to project root/skills
        """
        if skills_dir is None:
            # Assume we're in the project root
            project_root = Path(__file__).parent.parent.parent.parent
            skills_dir = project_root / "skills"
        self.skills_dir = Path(skills_dir)
        self._skills_cache: Dict[str, Dict] = {}
    
    def discover_skills(self) -> List[str]:
        """
        Discover all skills in the skills directory.
        
        Returns:
            List of skill names
        """
        if not self.skills_dir.exists():
            return []
        
        skills = []
        for item in self.skills_dir.iterdir():
            if item.is_dir() and (item / "SKILL.md").exists():
                skills.append(item.name)
        
        return sorted(skills)
    
    def load_skill_metadata(self, skill_name: str) -> Dict:
        """
        Load metadata for a specific skill.
        
        Args:
            skill_name: Name of the skill
            
        Returns:
            Dictionary containing skill metadata
        """
        if skill_name in self._skills_cache:
            return self._skills_cache[skill_name]
        
        skill_dir = self.skills_dir / skill_name
        
        if not skill_dir.exists():
            raise ValueError(f"Skill '{skill_name}' not found")
        
        metadata = {
            "name": skill_name,
            "path": str(skill_dir),
        }
        
        # Load SKILL.md frontmatter
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text()
            if content.startswith("---"):
                # Extract YAML frontmatter
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    frontmatter = yaml.safe_load(parts[1])
                    metadata.update(frontmatter or {})
        
        # Load skill.json if present
        skill_json = skill_dir / "skill.json"
        if skill_json.exists():
            with open(skill_json) as f:
                metadata.update(json.load(f))
        
        self._skills_cache[skill_name] = metadata
        return metadata
    
    def get_skill_path(self, skill_name: str) -> Path:
        """
        Get the path to a skill's directory.
        
        Args:
            skill_name: Name of the skill
            
        Returns:
            Path to skill directory
        """
        skill_dir = self.skills_dir / skill_name
        if not skill_dir.exists():
            raise ValueError(f"Skill '{skill_name}' not found")
        return skill_dir

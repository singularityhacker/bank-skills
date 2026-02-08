"""
Build skill bundles for publishing to registries.
"""

import json
import zipfile
from pathlib import Path
from typing import Dict, Optional
from bankskills.runtime.registry import SkillRegistry


class SkillBundleBuilder:
    """
    Builds skill bundles for distribution.
    """
    
    def __init__(self, registry: Optional[SkillRegistry] = None):
        """
        Initialize the bundle builder.
        
        Args:
            registry: Optional skill registry instance
        """
        self.registry = registry or SkillRegistry()
    
    def build_bundle(self, skill_name: str, output_dir: Optional[Path] = None) -> Path:
        """
        Build a zip bundle for a skill.
        
        Args:
            skill_name: Name of the skill to bundle
            output_dir: Directory to write bundle to. Defaults to dist/
            
        Returns:
            Path to the created bundle file
        """
        skill_metadata = self.registry.load_skill_metadata(skill_name)
        skill_path = self.registry.get_skill_path(skill_name)
        
        if output_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            output_dir = project_root / "dist"
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        version = skill_metadata.get("version", "1.0.0")
        bundle_name = f"{skill_name}-{version}.zip"
        bundle_path = output_dir / bundle_name
        
        # Create zip bundle
        with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add all files from skill directory
            for file_path in skill_path.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(skill_path)
                    zipf.write(file_path, arcname)
        
        return bundle_path
    
    def build_npm_package(self, skill_name: str, output_dir: Optional[Path] = None) -> Path:
        """
        Build an npm package structure for a skill.
        
        Args:
            skill_name: Name of the skill to package
            output_dir: Directory to write package to. Defaults to dist/
            
        Returns:
            Path to the package directory
        """
        skill_metadata = self.registry.load_skill_metadata(skill_name)
        skill_path = self.registry.get_skill_path(skill_name)
        
        if output_dir is None:
            project_root = Path(__file__).parent.parent.parent.parent
            output_dir = project_root / "dist" / "npm"
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        package_dir = output_dir / skill_name
        package_dir.mkdir(exist_ok=True)
        
        # Create package.json
        package_json = {
            "name": f"@skill-shop/{skill_name}",
            "version": skill_metadata.get("version", "1.0.0"),
            "description": skill_metadata.get("description", ""),
            "files": ["SKILL.md", "run.sh", "src"],
            "bin": {
                skill_name: "./run.sh"
            }
        }
        
        with open(package_dir / "package.json", "w") as f:
            json.dump(package_json, f, indent=2)
        
        # Copy SKILL.md and run.sh
        import shutil
        if (skill_path / "SKILL.md").exists():
            shutil.copy2(skill_path / "SKILL.md", package_dir / "SKILL.md")
        if (skill_path / "run.sh").exists():
            shutil.copy2(skill_path / "run.sh", package_dir / "run.sh")
            # Make executable
            (package_dir / "run.sh").chmod(0o755)
        
        # Copy src directory if it exists
        if (skill_path / "src").exists():
            shutil.copytree(skill_path / "src", package_dir / "src", dirs_exist_ok=True)
        
        return package_dir

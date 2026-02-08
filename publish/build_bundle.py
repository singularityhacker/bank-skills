#!/usr/bin/env python3
"""
Build skill bundles for publishing.

Usage:
    python publish/build_bundle.py <skill_name> [--output-dir DIR]
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bankskills.publishing.builder import SkillBundleBuilder


def main():
    parser = argparse.ArgumentParser(description="Build skill bundle")
    parser.add_argument("skill_name", help="Name of the skill to bundle")
    parser.add_argument("--output-dir", type=Path, help="Output directory (default: dist/)")
    
    args = parser.parse_args()
    
    builder = SkillBundleBuilder()
    bundle_path = builder.build_bundle(args.skill_name, args.output_dir)
    
    print(f"Built bundle: {bundle_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

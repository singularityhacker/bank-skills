"""Tests for Story 01 — Bank skill directory structure."""

import os
import stat
from pathlib import Path

# Root of the repository
REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / "skills" / "bank-skill"


def test_bank_skill_directory_exists():
    assert SKILL_DIR.is_dir(), "skills/bank-skill/ directory must exist"


def test_examples_directory_exists():
    assert (SKILL_DIR / "examples").is_dir(), "skills/bank-skill/examples/ directory must exist"


def test_run_sh_exists():
    run_sh = SKILL_DIR / "run.sh"
    assert run_sh.is_file(), "skills/bank-skill/run.sh must exist"


def test_run_sh_is_executable():
    run_sh = SKILL_DIR / "run.sh"
    mode = run_sh.stat().st_mode
    assert mode & stat.S_IXUSR, "run.sh must be executable by owner"


def test_run_sh_invokes_handler():
    run_sh = SKILL_DIR / "run.sh"
    content = run_sh.read_text()
    assert "bankskills.core.bank.handler" in content, "run.sh must invoke the bank skill handler"

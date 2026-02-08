"""Tests for Story 03 — skill.json registry metadata."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_JSON = REPO_ROOT / "skills" / "bank-skill" / "skill.json"


def test_skill_json_exists():
    assert SKILL_JSON.is_file(), "skills/bank-skill/skill.json must exist"


def test_skill_json_is_valid_json():
    data = json.loads(SKILL_JSON.read_text())
    assert isinstance(data, dict)


def test_skill_json_has_name():
    data = json.loads(SKILL_JSON.read_text())
    assert data["name"] == "bank-skill"


def test_skill_json_has_version():
    data = json.loads(SKILL_JSON.read_text())
    assert "version" in data
    assert isinstance(data["version"], str)


def test_skill_json_has_entrypoint():
    data = json.loads(SKILL_JSON.read_text())
    assert data["entrypoint"] == "./run.sh"


def test_skill_json_has_interfaces():
    data = json.loads(SKILL_JSON.read_text())
    interfaces = data["interfaces"]
    assert "cli" in interfaces
    assert "mcp" in interfaces


def test_skill_json_has_inputs_outputs():
    data = json.loads(SKILL_JSON.read_text())
    assert "inputs" in data
    assert "outputs" in data

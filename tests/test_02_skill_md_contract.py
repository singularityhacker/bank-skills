"""Tests for Story 02 — SKILL.md agent contract."""

import re
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_MD = REPO_ROOT / "skills" / "bank-skill" / "SKILL.md"


def _parse_frontmatter(text: str):
    """Extract YAML frontmatter from markdown text."""
    match = re.match(r"^---\n(.*?)\n---", text, re.DOTALL)
    assert match, "SKILL.md must start with YAML frontmatter"
    return yaml.safe_load(match.group(1))


def test_skill_md_exists():
    assert SKILL_MD.is_file(), "skills/bank-skill/SKILL.md must exist"


def test_frontmatter_has_required_fields():
    content = SKILL_MD.read_text()
    fm = _parse_frontmatter(content)
    assert "name" in fm, "Frontmatter must contain 'name'"
    assert "description" in fm, "Frontmatter must contain 'description'"
    assert "homepage" in fm, "Frontmatter must contain 'homepage'"
    assert "metadata" in fm, "Frontmatter must contain 'metadata'"


def test_frontmatter_name_is_bank_skill():
    content = SKILL_MD.read_text()
    fm = _parse_frontmatter(content)
    assert fm["name"] == "bank-skill"


def test_metadata_requires_wise_api_token():
    content = SKILL_MD.read_text()
    fm = _parse_frontmatter(content)
    metadata = fm["metadata"]
    if isinstance(metadata, str):
        import json
        metadata = json.loads(metadata)
    requires_env = metadata["openclaw"]["requires"]["env"]
    assert "WISE_API_TOKEN" in requires_env, "metadata must require WISE_API_TOKEN"


def test_documents_balance_operation():
    content = SKILL_MD.read_text()
    assert "balance" in content.lower()
    assert '"balance"' in content


def test_documents_receive_details_operation():
    content = SKILL_MD.read_text()
    assert "receive" in content.lower()
    assert '"receive-details"' in content


def test_documents_send_money_operation():
    content = SKILL_MD.read_text()
    assert "send" in content.lower()
    assert '"send"' in content


def test_documents_failure_modes():
    content = SKILL_MD.read_text()
    assert "WISE_API_TOKEN" in content
    assert "insufficient funds" in content.lower()


def test_no_real_token_in_examples():
    content = SKILL_MD.read_text()
    # Should not contain anything that looks like a real Bearer token
    assert "Bearer " not in content, "SKILL.md must not contain Bearer tokens"

"""Tests for Story 04 — Golden input/output examples."""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES_DIR = REPO_ROOT / "skills" / "bank-skill" / "examples"

EXPECTED_PAIRS = [
    ("balance-input.json", "balance-output.json"),
    ("receive-details-input.json", "receive-details-output.json"),
    ("send-input.json", "send-output.json"),
]

SENSITIVE_PATTERNS = ["sk_live_", "sk_test_", "Bearer ", "token:", "password"]


def test_examples_directory_exists():
    assert EXAMPLES_DIR.is_dir()


def test_all_example_pairs_exist():
    for inp, out in EXPECTED_PAIRS:
        assert (EXAMPLES_DIR / inp).is_file(), f"{inp} must exist"
        assert (EXAMPLES_DIR / out).is_file(), f"{out} must exist"


def test_all_examples_are_valid_json():
    for f in EXAMPLES_DIR.glob("*.json"):
        data = json.loads(f.read_text())
        assert isinstance(data, dict), f"{f.name} must be a JSON object"


def test_input_examples_have_action():
    for inp, _ in EXPECTED_PAIRS:
        data = json.loads((EXAMPLES_DIR / inp).read_text())
        assert "action" in data, f"{inp} must have an 'action' field"


def test_output_examples_have_success():
    for _, out in EXPECTED_PAIRS:
        data = json.loads((EXAMPLES_DIR / out).read_text())
        assert "success" in data, f"{out} must have a 'success' field"


def test_no_secrets_in_examples():
    for f in EXAMPLES_DIR.glob("*.json"):
        content = f.read_text()
        for pattern in SENSITIVE_PATTERNS:
            assert pattern not in content, f"{f.name} must not contain '{pattern}'"

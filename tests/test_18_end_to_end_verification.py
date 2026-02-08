"""Tests for Story 18 — End-to-end verification."""

import json
import os
import zipfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


PROJECT_ROOT = Path(__file__).parent.parent
SKILL_DIR = PROJECT_ROOT / "skills" / "bank-skill"

# ---------------------------------------------------------------------------
# Sample data used across all end-to-end tests
# ---------------------------------------------------------------------------

SAMPLE_BALANCES = [
    {"currency": "USD", "amount": 1000.00, "reservedAmount": 0.0},
    {"currency": "EUR", "amount": 500.00, "reservedAmount": 10.0},
]

SAMPLE_DETAILS = [
    {
        "currency": "USD",
        "accountHolder": "Test Business",
        "accountNumber": "1234567890",
        "routingNumber": "026073150",
        "bankName": "Community Federal Savings Bank",
    },
]

SAMPLE_TRANSFER = {
    "id": 99999,
    "status": "processing",
    "sourceAmount": 50.0,
    "sourceCurrency": "USD",
    "targetAmount": 45.0,
    "targetCurrency": "EUR",
}

MOCK_CREDENTIALS_ENV = {
    "WISE_API_TOKEN": "test-token",
}


# ===========================================================================
# 1. run.sh handler end-to-end (balance, receive-details, send)
# ===========================================================================


class TestRunShEndToEnd:
    """Verify the handler works for all three actions with mocked API."""

    @patch("bankskills.core.bank.balances.fetch_balances")
    @patch("bankskills.core.bank.client.WiseClient")
    @patch.dict(os.environ, MOCK_CREDENTIALS_ENV, clear=False)
    def test_balance_via_handler(self, mock_client_cls, mock_fetch):
        from bankskills.core.bank.handler import handle

        mock_fetch.return_value = SAMPLE_BALANCES
        result = handle({"action": "balance"})
        assert result["success"] is True
        assert len(result["balances"]) == 2

    @patch("bankskills.core.bank.account_details.fetch_account_details")
    @patch("bankskills.core.bank.client.WiseClient")
    @patch.dict(os.environ, MOCK_CREDENTIALS_ENV, clear=False)
    def test_receive_details_via_handler(self, mock_client_cls, mock_fetch):
        from bankskills.core.bank.handler import handle

        mock_fetch.return_value = SAMPLE_DETAILS
        result = handle({"action": "receive-details"})
        assert result["success"] is True
        assert result["details"][0]["accountNumber"] == "1234567890"

    @patch("bankskills.core.bank.transfer.send_money")
    @patch("bankskills.core.bank.client.WiseClient")
    @patch.dict(os.environ, MOCK_CREDENTIALS_ENV, clear=False)
    def test_send_via_handler(self, mock_client_cls, mock_send):
        from bankskills.core.bank.handler import handle

        mock_send.return_value = SAMPLE_TRANSFER
        result = handle({
            "action": "send",
            "sourceCurrency": "USD",
            "targetCurrency": "EUR",
            "amount": 50,
            "recipientName": "Jane Doe",
            "recipientAccount": "DE89370400440532013000",  # IBAN
        })
        assert result["success"] is True
        assert result["transfer"]["id"] == 99999


# ===========================================================================
# 2. CLI end-to-end (balance, receive-details, send)
# ===========================================================================


class TestCLIEndToEnd:
    """Verify CLI commands work end-to-end with mocked API."""

    @patch("bankskills.cli.bank.main.WiseClient")
    @patch("bankskills.cli.bank.main.load_credentials")
    @patch("bankskills.core.bank.balances.fetch_balances")
    def test_cli_balance(self, mock_fetch, mock_creds, mock_client_cls, capsys):
        from bankskills.cli.bank.main import main

        mock_fetch.return_value = SAMPLE_BALANCES
        code = main(["--json", "balance"])
        assert code == 0
        data = json.loads(capsys.readouterr().out)
        assert data["success"] is True
        assert len(data["balances"]) == 2

    @patch("bankskills.cli.bank.main.WiseClient")
    @patch("bankskills.cli.bank.main.load_credentials")
    @patch("bankskills.core.bank.account_details.fetch_account_details")
    def test_cli_receive_details(self, mock_fetch, mock_creds, mock_client_cls, capsys):
        from bankskills.cli.bank.main import main

        mock_fetch.return_value = SAMPLE_DETAILS
        code = main(["--json", "receive-details"])
        assert code == 0
        data = json.loads(capsys.readouterr().out)
        assert data["success"] is True

    @patch("bankskills.cli.bank.main.WiseClient")
    @patch("bankskills.cli.bank.main.load_credentials")
    @patch("bankskills.core.bank.transfer.send_money")
    def test_cli_send(self, mock_send, mock_creds, mock_client_cls, capsys):
        from bankskills.cli.bank.main import main

        mock_send.return_value = SAMPLE_TRANSFER
        code = main([
            "--json", "send",
            "--source-currency", "USD",
            "--target-currency", "EUR",
            "--amount", "50",
            "--recipient-name", "Jane Doe",
            "--recipient-account", "DE89370400440532013000",  # IBAN
        ])
        assert code == 0
        data = json.loads(capsys.readouterr().out)
        assert data["success"] is True
        assert data["transfer"]["id"] == 99999


# ===========================================================================
# 3. MCP tools work when server is configured
# ===========================================================================


class TestMCPEndToEnd:
    """Verify MCP server exposes all three bank tools correctly."""

    def test_mcp_has_all_bank_tools(self):
        from bankskills.mcp.server import mcp

        tool_names = [t.name for t in mcp._tool_manager._tools.values()]
        assert "check_balance" in tool_names
        assert "get_receive_details" in tool_names
        assert "send_money" in tool_names

    def test_mcp_tools_have_descriptions(self):
        from bankskills.mcp.server import mcp

        for tool in mcp._tool_manager._tools.values():
            if tool.name in ("check_balance", "get_receive_details", "send_money"):
                assert tool.description, f"{tool.name} missing description"


# ===========================================================================
# 4. build_bundle.py produces a publishable bundle
# ===========================================================================


class TestBuildBundle:
    """Verify build_bundle produces a valid zip for bank-skill."""

    def test_build_bundle_creates_zip(self, tmp_path):
        from bankskills.publishing.builder import SkillBundleBuilder

        builder = SkillBundleBuilder()
        bundle_path = builder.build_bundle("bank-skill", output_dir=tmp_path)
        assert bundle_path.exists()
        assert bundle_path.suffix == ".zip"

    def test_bundle_contains_required_files(self, tmp_path):
        from bankskills.publishing.builder import SkillBundleBuilder

        builder = SkillBundleBuilder()
        bundle_path = builder.build_bundle("bank-skill", output_dir=tmp_path)
        with zipfile.ZipFile(bundle_path, "r") as zf:
            names = zf.namelist()
            assert "SKILL.md" in names
            assert "skill.json" in names
            assert "run.sh" in names

    def test_bundle_contains_examples(self, tmp_path):
        from bankskills.publishing.builder import SkillBundleBuilder

        builder = SkillBundleBuilder()
        bundle_path = builder.build_bundle("bank-skill", output_dir=tmp_path)
        with zipfile.ZipFile(bundle_path, "r") as zf:
            names = zf.namelist()
            example_files = [n for n in names if n.startswith("examples/")]
            assert len(example_files) >= 6  # 3 input + 3 output


# ===========================================================================
# 5. No secrets in bundle or examples
# ===========================================================================


SECRET_PATTERNS = [
    "WISE_API_TOKEN=",
    "Bearer ",
    "sk-",
    "api_key",
    "secret_key",
    "password",
]


class TestNoSecretsInBundle:
    """Verify no secrets leak into the skill bundle or examples."""

    def test_no_secrets_in_example_files(self):
        examples_dir = SKILL_DIR / "examples"
        for f in examples_dir.glob("*.json"):
            content = f.read_text()
            for pattern in SECRET_PATTERNS:
                assert pattern not in content, (
                    f"Possible secret '{pattern}' found in {f.name}"
                )

    def test_no_secrets_in_skill_md(self):
        content = (SKILL_DIR / "SKILL.md").read_text()
        for pattern in SECRET_PATTERNS:
            assert pattern not in content, (
                f"Possible secret '{pattern}' found in SKILL.md"
            )

    def test_no_secrets_in_bundle_contents(self, tmp_path):
        from bankskills.publishing.builder import SkillBundleBuilder

        builder = SkillBundleBuilder()
        bundle_path = builder.build_bundle("bank-skill", output_dir=tmp_path)
        with zipfile.ZipFile(bundle_path, "r") as zf:
            for name in zf.namelist():
                content = zf.read(name).decode("utf-8", errors="ignore")
                for pattern in SECRET_PATTERNS:
                    assert pattern not in content, (
                        f"Possible secret '{pattern}' found in bundle file {name}"
                    )

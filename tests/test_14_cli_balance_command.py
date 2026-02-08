"""Tests for Story 14 — CLI: balance command."""

from io import StringIO
from unittest.mock import MagicMock, patch

import pytest

from bankskills.cli.bank.main import main, cmd_balance
from bankskills.core.bank.client import WiseClient
from bankskills.core.bank.credentials import WiseCredentials


SAMPLE_BALANCES = [
    {"currency": "USD", "amount": 1250.00, "reservedAmount": 0.00},
    {"currency": "EUR", "amount": 500.75, "reservedAmount": 10.00},
]


@pytest.fixture
def mock_client():
    creds = WiseCredentials(api_token="test-token", profile_id="12345")
    return WiseClient(credentials=creds)


class TestCLIBalanceCommand:
    @patch("bankskills.cli.bank.main.WiseClient")
    @patch("bankskills.cli.bank.main.load_credentials")
    @patch("bankskills.core.bank.balances.fetch_balances")
    def test_balance_command_exit_0(self, mock_fetch, mock_creds, mock_client_cls):
        mock_fetch.return_value = SAMPLE_BALANCES
        code = main(["balance"])
        assert code == 0

    @patch("bankskills.cli.bank.main.WiseClient")
    @patch("bankskills.cli.bank.main.load_credentials")
    @patch("bankskills.core.bank.balances.fetch_balances")
    def test_balance_command_outputs_amounts(self, mock_fetch, mock_creds, mock_client_cls, capsys):
        mock_fetch.return_value = SAMPLE_BALANCES
        main(["balance"])
        captured = capsys.readouterr()
        assert "USD" in captured.out
        assert "1250.00" in captured.out
        assert "EUR" in captured.out

    @patch("bankskills.cli.bank.main.WiseClient")
    @patch("bankskills.cli.bank.main.load_credentials")
    @patch("bankskills.core.bank.balances.fetch_balances")
    def test_balance_json_flag(self, mock_fetch, mock_creds, mock_client_cls, capsys):
        import json
        mock_fetch.return_value = SAMPLE_BALANCES
        main(["--json", "balance"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["success"] is True
        assert len(data["balances"]) == 2

    @patch("bankskills.cli.bank.main.WiseClient")
    @patch("bankskills.cli.bank.main.load_credentials")
    @patch("bankskills.core.bank.balances.fetch_balances")
    def test_balance_currency_filter(self, mock_fetch, mock_creds, mock_client_cls):
        mock_fetch.return_value = [SAMPLE_BALANCES[0]]
        main(["balance", "--currency", "USD"])
        _, kwargs = mock_fetch.call_args
        assert kwargs.get("currency") == "USD"

    @patch("bankskills.cli.bank.main.load_credentials")
    def test_missing_token_exit_nonzero(self, mock_creds):
        from bankskills.core.bank.credentials import MissingCredentialError
        mock_creds.side_effect = MissingCredentialError("WISE_API_TOKEN environment variable is not set")
        code = main(["balance"])
        assert code != 0

    @patch("bankskills.cli.bank.main.load_credentials")
    def test_missing_token_shows_error(self, mock_creds, capsys):
        from bankskills.core.bank.credentials import MissingCredentialError
        mock_creds.side_effect = MissingCredentialError("WISE_API_TOKEN environment variable is not set")
        main(["balance"])
        captured = capsys.readouterr()
        assert "WISE_API_TOKEN" in captured.err

    @patch("bankskills.cli.bank.main.WiseClient")
    @patch("bankskills.cli.bank.main.load_credentials")
    @patch("bankskills.core.bank.balances.fetch_balances")
    def test_balance_api_error_exit_nonzero(self, mock_fetch, mock_creds, mock_client_cls):
        from bankskills.core.bank.balances import BalanceError
        mock_fetch.side_effect = BalanceError("server error")
        code = main(["balance"])
        assert code != 0

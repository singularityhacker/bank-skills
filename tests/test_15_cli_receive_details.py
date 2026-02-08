"""Tests for Story 15 — CLI: receive-details command."""

from unittest.mock import patch

from bankskills.cli.bank.main import main


SAMPLE_DETAILS = [
    {
        "currency": "USD",
        "accountHolder": "Test Business",
        "accountNumber": "1234567890",
        "routingNumber": "026073150",
        "bankName": "Community Federal Savings Bank",
    },
]


class TestCLIReceiveDetailsCommand:
    @patch("bankskills.cli.bank.main.WiseClient")
    @patch("bankskills.cli.bank.main.load_credentials")
    @patch("bankskills.core.bank.account_details.fetch_account_details")
    def test_receive_details_exit_0(self, mock_fetch, mock_creds, mock_client_cls):
        mock_fetch.return_value = SAMPLE_DETAILS
        code = main(["receive-details"])
        assert code == 0

    @patch("bankskills.cli.bank.main.WiseClient")
    @patch("bankskills.cli.bank.main.load_credentials")
    @patch("bankskills.core.bank.account_details.fetch_account_details")
    def test_receive_details_outputs_info(self, mock_fetch, mock_creds, mock_client_cls, capsys):
        mock_fetch.return_value = SAMPLE_DETAILS
        main(["receive-details"])
        captured = capsys.readouterr()
        assert "Test Business" in captured.out
        assert "1234567890" in captured.out
        assert "026073150" in captured.out

    @patch("bankskills.cli.bank.main.WiseClient")
    @patch("bankskills.cli.bank.main.load_credentials")
    @patch("bankskills.core.bank.account_details.fetch_account_details")
    def test_receive_details_currency_flag(self, mock_fetch, mock_creds, mock_client_cls):
        mock_fetch.return_value = SAMPLE_DETAILS
        main(["receive-details", "--currency", "USD"])
        _, kwargs = mock_fetch.call_args
        assert kwargs.get("currency") == "USD"

    @patch("bankskills.cli.bank.main.WiseClient")
    @patch("bankskills.cli.bank.main.load_credentials")
    @patch("bankskills.core.bank.account_details.fetch_account_details")
    def test_receive_details_json_flag(self, mock_fetch, mock_creds, mock_client_cls, capsys):
        import json
        mock_fetch.return_value = SAMPLE_DETAILS
        main(["--json", "receive-details"])
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["success"] is True
        assert data["details"][0]["accountNumber"] == "1234567890"

    @patch("bankskills.cli.bank.main.load_credentials")
    def test_missing_token_exit_nonzero(self, mock_creds):
        from bankskills.core.bank.credentials import MissingCredentialError
        mock_creds.side_effect = MissingCredentialError("WISE_API_TOKEN environment variable is not set")
        code = main(["receive-details"])
        assert code != 0

    @patch("bankskills.cli.bank.main.WiseClient")
    @patch("bankskills.cli.bank.main.load_credentials")
    @patch("bankskills.core.bank.account_details.fetch_account_details")
    def test_api_error_exit_nonzero(self, mock_fetch, mock_creds, mock_client_cls):
        from bankskills.core.bank.account_details import AccountDetailsError
        mock_fetch.side_effect = AccountDetailsError("Not found")
        code = main(["receive-details"])
        assert code != 0

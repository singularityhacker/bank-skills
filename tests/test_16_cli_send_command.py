"""Tests for Story 16 — CLI: send command."""

from unittest.mock import patch

from bankskills.cli.bank.main import main


TRANSFER_RESULT = {
    "id": 88888,
    "status": "processing",
    "sourceAmount": 100.0,
    "sourceCurrency": "USD",
    "targetAmount": 100.0,
    "targetCurrency": "USD",
}

SEND_ARGS = [
    "send",
    "--source-currency", "USD",
    "--target-currency", "EUR",
    "--amount", "100",
    "--recipient-name", "Jane Doe",
    "--recipient-account", "DE89370400440532013000",  # IBAN
]


class TestCLISendCommand:
    @patch("bankskills.cli.bank.main.WiseClient")
    @patch("bankskills.cli.bank.main.load_credentials")
    @patch("bankskills.core.bank.transfer.send_money")
    def test_send_exit_0(self, mock_send, mock_creds, mock_client_cls):
        mock_send.return_value = TRANSFER_RESULT
        code = main(SEND_ARGS)
        assert code == 0

    @patch("bankskills.cli.bank.main.WiseClient")
    @patch("bankskills.cli.bank.main.load_credentials")
    @patch("bankskills.core.bank.transfer.send_money")
    def test_send_outputs_status(self, mock_send, mock_creds, mock_client_cls, capsys):
        mock_send.return_value = TRANSFER_RESULT
        main(SEND_ARGS)
        captured = capsys.readouterr()
        assert "88888" in captured.out
        assert "processing" in captured.out

    @patch("bankskills.cli.bank.main.WiseClient")
    @patch("bankskills.cli.bank.main.load_credentials")
    @patch("bankskills.core.bank.transfer.send_money")
    def test_send_json_flag(self, mock_send, mock_creds, mock_client_cls, capsys):
        import json
        mock_send.return_value = TRANSFER_RESULT
        main(["--json"] + SEND_ARGS)
        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["success"] is True
        assert data["transfer"]["id"] == 88888

    @patch("bankskills.cli.bank.main.WiseClient")
    @patch("bankskills.cli.bank.main.load_credentials")
    @patch("bankskills.core.bank.transfer.send_money")
    def test_send_insufficient_funds_exit_nonzero(self, mock_send, mock_creds, mock_client_cls):
        from bankskills.core.bank.transfer import InsufficientFundsError
        mock_send.side_effect = InsufficientFundsError("Insufficient funds")
        code = main(SEND_ARGS)
        assert code != 0

    @patch("bankskills.cli.bank.main.WiseClient")
    @patch("bankskills.cli.bank.main.load_credentials")
    @patch("bankskills.core.bank.transfer.send_money")
    def test_send_insufficient_funds_shows_error(self, mock_send, mock_creds, mock_client_cls, capsys):
        from bankskills.core.bank.transfer import InsufficientFundsError
        mock_send.side_effect = InsufficientFundsError("Insufficient funds in source balance")
        main(SEND_ARGS)
        captured = capsys.readouterr()
        assert "Insufficient funds" in captured.err

    @patch("bankskills.cli.bank.main.load_credentials")
    def test_missing_token_exit_nonzero(self, mock_creds):
        from bankskills.core.bank.credentials import MissingCredentialError
        mock_creds.side_effect = MissingCredentialError("WISE_API_TOKEN environment variable is not set")
        code = main(SEND_ARGS)
        assert code != 0

"""Tests for Story 13 — run.sh: send action."""

from unittest.mock import patch

from bankskills.core.bank.handler import handle


SEND_INPUT = {
    "action": "send",
    "sourceCurrency": "USD",
    "targetCurrency": "EUR",
    "amount": 100.0,
    "recipientName": "Jane Doe",
    "recipientAccount": "DE89370400440532013000",  # IBAN
}

TRANSFER_RESULT = {
    "id": 88888,
    "status": "processing",
    "sourceAmount": 100.0,
    "sourceCurrency": "USD",
    "targetAmount": 100.0,
    "targetCurrency": "USD",
}


class TestHandlerSendAction:
    @patch("bankskills.core.bank.handler.WiseClient")
    @patch("bankskills.core.bank.handler.load_credentials")
    @patch("bankskills.core.bank.transfer.send_money")
    def test_send_returns_success(self, mock_send, mock_creds, mock_client_cls):
        mock_send.return_value = TRANSFER_RESULT
        result = handle(SEND_INPUT)
        assert result["success"] is True
        assert result["transfer"]["id"] == 88888
        assert result["transfer"]["status"] == "processing"

    @patch("bankskills.core.bank.handler.WiseClient")
    @patch("bankskills.core.bank.handler.load_credentials")
    def test_send_missing_required_fields(self, mock_creds, mock_client_cls):
        result = handle({"action": "send", "sourceCurrency": "USD"})
        assert result["success"] is False
        assert "Missing required fields" in result["error"]

    @patch("bankskills.core.bank.handler.WiseClient")
    @patch("bankskills.core.bank.handler.load_credentials")
    @patch("bankskills.core.bank.transfer.send_money")
    def test_send_insufficient_funds(self, mock_send, mock_creds, mock_client_cls):
        from bankskills.core.bank.transfer import InsufficientFundsError
        mock_send.side_effect = InsufficientFundsError("Insufficient funds in source balance")
        result = handle(SEND_INPUT)
        assert result["success"] is False
        assert "Insufficient funds" in result["error"]

    @patch("bankskills.core.bank.handler.WiseClient")
    @patch("bankskills.core.bank.handler.load_credentials")
    @patch("bankskills.core.bank.transfer.send_money")
    def test_send_api_error(self, mock_send, mock_creds, mock_client_cls):
        from bankskills.core.bank.transfer import TransferError
        mock_send.side_effect = TransferError("Failed to create quote: HTTP 400")
        result = handle(SEND_INPUT)
        assert result["success"] is False
        assert "Failed to create quote" in result["error"]

    @patch("bankskills.core.bank.handler.WiseClient")
    @patch("bankskills.core.bank.handler.load_credentials")
    @patch("bankskills.core.bank.transfer.send_money")
    def test_send_output_is_json_serializable(self, mock_send, mock_creds, mock_client_cls):
        import json
        mock_send.return_value = TRANSFER_RESULT
        result = handle(SEND_INPUT)
        json_str = json.dumps(result)
        parsed = json.loads(json_str)
        assert parsed["success"] is True

    @patch("bankskills.core.bank.handler.load_credentials")
    def test_send_missing_token(self, mock_creds):
        from bankskills.core.bank.credentials import MissingCredentialError
        mock_creds.side_effect = MissingCredentialError("WISE_API_TOKEN environment variable is not set")
        result = handle(SEND_INPUT)
        assert result["success"] is False
        assert "WISE_API_TOKEN" in result["error"]

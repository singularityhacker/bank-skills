"""Tests for Story 12 — run.sh: receive-details action."""

from unittest.mock import patch

from bankskills.core.bank.handler import handle


SAMPLE_DETAILS = [
    {
        "currency": "USD",
        "accountHolder": "Test Business",
        "accountNumber": "1234567890",
        "routingNumber": "026073150",
        "bankName": "Community Federal Savings Bank",
    },
]


class TestHandlerReceiveDetailsAction:
    @patch("bankskills.core.bank.handler.WiseClient")
    @patch("bankskills.core.bank.handler.load_credentials")
    @patch("bankskills.core.bank.account_details.fetch_account_details")
    def test_receive_details_returns_success(self, mock_fetch, mock_creds, mock_client_cls):
        mock_fetch.return_value = SAMPLE_DETAILS
        result = handle({"action": "receive-details"})
        assert result["success"] is True
        assert result["details"] == SAMPLE_DETAILS

    @patch("bankskills.core.bank.handler.WiseClient")
    @patch("bankskills.core.bank.handler.load_credentials")
    @patch("bankskills.core.bank.account_details.fetch_account_details")
    def test_receive_details_passes_currency(self, mock_fetch, mock_creds, mock_client_cls):
        mock_fetch.return_value = SAMPLE_DETAILS
        result = handle({"action": "receive-details", "currency": "USD"})
        assert result["success"] is True
        _, kwargs = mock_fetch.call_args
        assert kwargs.get("currency") == "USD"

    @patch("bankskills.core.bank.handler.WiseClient")
    @patch("bankskills.core.bank.handler.load_credentials")
    @patch("bankskills.core.bank.account_details.fetch_account_details")
    def test_receive_details_api_error(self, mock_fetch, mock_creds, mock_client_cls):
        from bankskills.core.bank.account_details import AccountDetailsError
        mock_fetch.side_effect = AccountDetailsError("Profile not found")
        result = handle({"action": "receive-details"})
        assert result["success"] is False
        assert "not found" in result["error"]

    @patch("bankskills.core.bank.handler.WiseClient")
    @patch("bankskills.core.bank.handler.load_credentials")
    @patch("bankskills.core.bank.account_details.fetch_account_details")
    def test_output_contains_account_fields(self, mock_fetch, mock_creds, mock_client_cls):
        mock_fetch.return_value = SAMPLE_DETAILS
        result = handle({"action": "receive-details"})
        detail = result["details"][0]
        assert "accountHolder" in detail
        assert "accountNumber" in detail
        assert "routingNumber" in detail

    @patch("bankskills.core.bank.handler.load_credentials")
    def test_missing_token_returns_error(self, mock_creds):
        from bankskills.core.bank.credentials import MissingCredentialError
        mock_creds.side_effect = MissingCredentialError("WISE_API_TOKEN environment variable is not set")
        result = handle({"action": "receive-details"})
        assert result["success"] is False
        assert "WISE_API_TOKEN" in result["error"]

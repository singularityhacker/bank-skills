"""Tests for Story 11 — run.sh: balance action."""

from unittest.mock import MagicMock, patch

import pytest

from bankskills.core.bank.handler import handle


SAMPLE_BALANCES = [
    {"currency": "USD", "amount": 1250.00, "reservedAmount": 0.00},
    {"currency": "EUR", "amount": 500.75, "reservedAmount": 10.00},
]


class TestHandlerBalanceAction:
    @patch("bankskills.core.bank.handler.WiseClient")
    @patch("bankskills.core.bank.handler.load_credentials")
    @patch("bankskills.core.bank.balances.fetch_balances")
    def test_balance_action_returns_success(self, mock_fetch, mock_creds, mock_client_cls):
        mock_fetch.return_value = SAMPLE_BALANCES
        result = handle({"action": "balance"})
        assert result["success"] is True
        assert result["balances"] == SAMPLE_BALANCES

    @patch("bankskills.core.bank.handler.WiseClient")
    @patch("bankskills.core.bank.handler.load_credentials")
    @patch("bankskills.core.bank.balances.fetch_balances")
    def test_balance_action_passes_currency_filter(self, mock_fetch, mock_creds, mock_client_cls):
        mock_fetch.return_value = [SAMPLE_BALANCES[0]]
        result = handle({"action": "balance", "currency": "USD"})
        assert result["success"] is True
        mock_fetch.assert_called_once()
        _, kwargs = mock_fetch.call_args
        assert kwargs.get("currency") == "USD"

    @patch("bankskills.core.bank.handler.load_credentials")
    def test_missing_token_returns_error(self, mock_creds):
        from bankskills.core.bank.credentials import MissingCredentialError
        mock_creds.side_effect = MissingCredentialError("WISE_API_TOKEN environment variable is not set")
        result = handle({"action": "balance"})
        assert result["success"] is False
        assert "WISE_API_TOKEN" in result["error"]

    def test_missing_action_returns_error(self):
        result = handle({})
        assert result["success"] is False
        assert "action" in result["error"].lower()

    @patch("bankskills.core.bank.handler.WiseClient")
    @patch("bankskills.core.bank.handler.load_credentials")
    def test_unknown_action_returns_error(self, mock_creds, mock_client_cls):
        result = handle({"action": "unknown-action"})
        assert result["success"] is False
        assert "Unknown action" in result["error"]

    @patch("bankskills.core.bank.handler.WiseClient")
    @patch("bankskills.core.bank.handler.load_credentials")
    @patch("bankskills.core.bank.balances.fetch_balances")
    def test_balance_api_error_returns_failure(self, mock_fetch, mock_creds, mock_client_cls):
        from bankskills.core.bank.balances import BalanceError
        mock_fetch.side_effect = BalanceError("Authentication failed — check your WISE_API_TOKEN")
        result = handle({"action": "balance"})
        assert result["success"] is False
        assert "Authentication failed" in result["error"]

    @patch("bankskills.core.bank.handler.WiseClient")
    @patch("bankskills.core.bank.handler.load_credentials")
    @patch("bankskills.core.bank.balances.fetch_balances")
    def test_balance_output_is_json_serializable(self, mock_fetch, mock_creds, mock_client_cls):
        """Output must be JSON serializable."""
        import json
        mock_fetch.return_value = SAMPLE_BALANCES
        result = handle({"action": "balance"})
        json_str = json.dumps(result)
        parsed = json.loads(json_str)
        assert parsed["success"] is True

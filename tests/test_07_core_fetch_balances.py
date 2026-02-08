"""Tests for Story 07 — Core: fetch balances."""

from unittest.mock import MagicMock, patch

import pytest

from bankskills.core.bank.balances import BalanceError, fetch_balances
from bankskills.core.bank.client import WiseClient
from bankskills.core.bank.credentials import WiseCredentials


def _make_client(profile_id="12345"):
    creds = WiseCredentials(api_token="test-token", profile_id=profile_id)
    return WiseClient(credentials=creds)


def _mock_response(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or []
    return resp


SAMPLE_BALANCES = [
    {
        "id": 1,
        "currency": "USD",
        "amount": {"value": 1250.00, "currency": "USD", "reserved": 0.00},
    },
    {
        "id": 2,
        "currency": "EUR",
        "amount": {"value": 500.75, "currency": "EUR", "reserved": 10.00},
    },
]


class TestFetchBalances:
    @patch.object(WiseClient, "get")
    def test_returns_balances(self, mock_get):
        mock_get.return_value = _mock_response(200, SAMPLE_BALANCES)
        client = _make_client()
        result = fetch_balances(client)
        assert len(result) == 2
        assert result[0]["currency"] == "USD"
        assert result[0]["amount"] == 1250.00
        assert result[1]["currency"] == "EUR"

    @patch.object(WiseClient, "get")
    def test_currency_filter(self, mock_get):
        mock_get.return_value = _mock_response(200, SAMPLE_BALANCES)
        client = _make_client()
        result = fetch_balances(client, currency="USD")
        assert len(result) == 1
        assert result[0]["currency"] == "USD"

    @patch.object(WiseClient, "get")
    def test_currency_filter_case_insensitive(self, mock_get):
        mock_get.return_value = _mock_response(200, SAMPLE_BALANCES)
        client = _make_client()
        result = fetch_balances(client, currency="usd")
        assert len(result) == 1

    @patch.object(WiseClient, "get")
    def test_auth_error_raises(self, mock_get):
        mock_get.return_value = _mock_response(401)
        client = _make_client()
        with pytest.raises(BalanceError, match="Authentication failed"):
            fetch_balances(client)

    @patch.object(WiseClient, "get")
    def test_not_found_raises(self, mock_get):
        mock_get.return_value = _mock_response(404)
        client = _make_client()
        with pytest.raises(BalanceError, match="not found"):
            fetch_balances(client)

    @patch.object(WiseClient, "get")
    def test_server_error_raises(self, mock_get):
        mock_get.return_value = _mock_response(500)
        client = _make_client()
        with pytest.raises(BalanceError, match="server error"):
            fetch_balances(client)

    @patch.object(WiseClient, "get")
    def test_uses_correct_endpoint(self, mock_get):
        mock_get.return_value = _mock_response(200, [])
        client = _make_client(profile_id="99999")
        fetch_balances(client)
        mock_get.assert_called_once_with(
            "/v4/profiles/99999/balances", params={"types": "STANDARD"}
        )

    @patch.object(WiseClient, "get")
    def test_sends_bearer_header(self, mock_get):
        """Verify the client is constructed with the correct token."""
        mock_get.return_value = _mock_response(200, [])
        client = _make_client()
        headers = client._headers()
        assert "Bearer test-token" in headers["Authorization"]

    @patch.object(WiseClient, "get")
    def test_reserved_amount_returned(self, mock_get):
        mock_get.return_value = _mock_response(200, SAMPLE_BALANCES)
        client = _make_client()
        result = fetch_balances(client)
        assert result[1]["reservedAmount"] == 10.00

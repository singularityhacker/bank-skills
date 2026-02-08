"""Tests for Story 08 — Core: fetch account details."""

from unittest.mock import MagicMock, patch

import pytest

from bankskills.core.bank.account_details import AccountDetailsError, fetch_account_details
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


# Wise API shape: receiveOptions[].details[] with type/body
SAMPLE_ACCOUNT_DETAILS = [
    {
        "currency": "USD",
        "title": "Test Business",
        "receiveOptions": [
            {
                "details": [
                    {"type": "ACCOUNT_HOLDER", "body": "Test Business"},
                    {"type": "ACCOUNT_NUMBER", "body": "1234567890"},
                    {"type": "ROUTING_NUMBER", "body": "026073150"},
                    {"type": "BANK_NAME", "body": "Community Federal Savings Bank"},
                ],
            },
        ],
    },
    {
        "currency": "EUR",
        "title": "Test Business",
        "receiveOptions": [
            {
                "details": [
                    {"type": "ACCOUNT_HOLDER", "body": "Test Business"},
                    {"type": "IBAN", "body": "DE89370400440532013000"},
                    {"type": "SWIFT_CODE", "body": "COBADEFFXXX"},
                ],
            },
        ],
    },
]


class TestFetchAccountDetails:
    @patch.object(WiseClient, "get")
    def test_returns_details(self, mock_get):
        mock_get.return_value = _mock_response(200, SAMPLE_ACCOUNT_DETAILS)
        client = _make_client()
        result = fetch_account_details(client)
        assert len(result) == 2

    @patch.object(WiseClient, "get")
    def test_usd_details_parsed(self, mock_get):
        mock_get.return_value = _mock_response(200, SAMPLE_ACCOUNT_DETAILS)
        client = _make_client()
        result = fetch_account_details(client, currency="USD")
        assert len(result) == 1
        usd = result[0]
        assert usd["currency"] == "USD"
        assert usd["accountHolder"] == "Test Business"
        assert usd["accountNumber"] == "1234567890"
        assert usd["routingNumber"] == "026073150"
        assert usd["bankName"] == "Community Federal Savings Bank"

    @patch.object(WiseClient, "get")
    def test_eur_details_parsed(self, mock_get):
        mock_get.return_value = _mock_response(200, SAMPLE_ACCOUNT_DETAILS)
        client = _make_client()
        result = fetch_account_details(client, currency="EUR")
        assert len(result) == 1
        eur = result[0]
        assert eur["currency"] == "EUR"
        assert eur["iban"] == "DE89370400440532013000"
        assert eur["swiftBic"] == "COBADEFFXXX"

    @patch.object(WiseClient, "get")
    def test_currency_filter(self, mock_get):
        mock_get.return_value = _mock_response(200, SAMPLE_ACCOUNT_DETAILS)
        client = _make_client()
        result = fetch_account_details(client, currency="usd")
        assert len(result) == 1
        assert result[0]["currency"] == "USD"

    @patch.object(WiseClient, "get")
    def test_auth_error_raises(self, mock_get):
        mock_get.return_value = _mock_response(401)
        client = _make_client()
        with pytest.raises(AccountDetailsError, match="Authentication failed"):
            fetch_account_details(client)

    @patch.object(WiseClient, "get")
    def test_not_found_raises(self, mock_get):
        mock_get.return_value = _mock_response(404)
        client = _make_client()
        with pytest.raises(AccountDetailsError, match="not found"):
            fetch_account_details(client)

    @patch.object(WiseClient, "get")
    def test_server_error_raises(self, mock_get):
        mock_get.return_value = _mock_response(500)
        client = _make_client()
        with pytest.raises(AccountDetailsError, match="server error"):
            fetch_account_details(client)

    @patch.object(WiseClient, "get")
    def test_uses_correct_endpoint(self, mock_get):
        mock_get.return_value = _mock_response(200, [])
        client = _make_client(profile_id="99999")
        fetch_account_details(client)
        mock_get.assert_called_once_with("/v1/profiles/99999/account-details")

"""Tests for Story 09 — Core: send money flow."""

from unittest.mock import MagicMock, call, patch

import pytest

from bankskills.core.bank.client import WiseClient
from bankskills.core.bank.credentials import WiseCredentials
from bankskills.core.bank.transfer import TransferError, send_money


def _make_client(profile_id="12345"):
    creds = WiseCredentials(api_token="test-token", profile_id=profile_id)
    return WiseClient(credentials=creds)


def _mock_response(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    return resp


QUOTE_RESPONSE = {"id": "quote-uuid-123", "targetAmount": 95.50}
RECIPIENT_RESPONSE = {"id": 7777}
TRANSFER_RESPONSE = {"id": 88888, "status": "processing"}
FUND_RESPONSE = {"type": "BALANCE", "status": "COMPLETED"}


class TestSendMoney:
    @patch.object(WiseClient, "get")
    @patch.object(WiseClient, "post")
    def test_full_flow_success(self, mock_post, mock_get):
        mock_get.return_value = _mock_response(200, [])
        mock_post.side_effect = [
            _mock_response(200, QUOTE_RESPONSE),
            _mock_response(200, RECIPIENT_RESPONSE),
            _mock_response(200, TRANSFER_RESPONSE),
            _mock_response(200, FUND_RESPONSE),
        ]
        client = _make_client()
        result = send_money(
            client,
            source_currency="USD",
            target_currency="EUR",
            amount=100.0,
            recipient_name="Jane Doe",
            recipient_account="DE89370400440532013000",
        )
        assert result["id"] == 88888
        assert result["status"] == "processing"
        assert result["sourceAmount"] == 100.0
        assert result["sourceCurrency"] == "USD"
        assert result["targetAmount"] == 95.50
        assert result["targetCurrency"] == "EUR"

    @patch.object(WiseClient, "get")
    @patch.object(WiseClient, "post")
    def test_calls_quote_requirements_recipient_transfer_fund(self, mock_post, mock_get):
        mock_get.return_value = _mock_response(200, [])  # requirements
        mock_post.side_effect = [
            _mock_response(200, QUOTE_RESPONSE),
            _mock_response(200, RECIPIENT_RESPONSE),
            _mock_response(200, TRANSFER_RESPONSE),
            _mock_response(200, FUND_RESPONSE),
        ]
        client = _make_client(profile_id="99999")
        send_money(
            client,
            source_currency="USD",
            target_currency="USD",
            amount=50.0,
            recipient_name="John",
            recipient_account="1234567890",
            recipient_routing_number="026073150",
            recipient_country="US",
            recipient_address="123 Main St",
            recipient_city="New York",
            recipient_post_code="10001",
        )
        assert mock_get.call_count == 1  # account requirements
        assert mock_post.call_count == 4
        # Verify endpoints
        get_calls = mock_get.call_args_list
        assert "/v1/account-requirements" in get_calls[0].args[0]
        post_calls = mock_post.call_args_list
        assert "/v3/profiles/99999/quotes" in post_calls[0].args[0]
        assert "/v1/accounts" in post_calls[1].args[0]
        assert "/v1/transfers" in post_calls[2].args[0]
        assert "/payments" in post_calls[3].args[0]

    @patch.object(WiseClient, "get")
    @patch.object(WiseClient, "post")
    def test_quote_failure_raises(self, mock_post, mock_get):
        mock_get.return_value = _mock_response(200, [])
        mock_post.side_effect = [_mock_response(400)]
        client = _make_client()
        with pytest.raises(TransferError, match="Failed to create quote"):
            send_money(
                client,
                "USD",
                "USD",
                100.0,
                "Jane",
                "1234567890",
                recipient_routing_number="026073150",
                recipient_country="US",
                recipient_address="123 Main St",
                recipient_city="New York",
                recipient_post_code="10001",
            )

    @patch.object(WiseClient, "get")
    @patch.object(WiseClient, "post")
    def test_recipient_failure_raises(self, mock_post, mock_get):
        mock_get.return_value = _mock_response(200, [])
        mock_post.side_effect = [
            _mock_response(200, QUOTE_RESPONSE),
            _mock_response(422),
        ]
        client = _make_client()
        with pytest.raises(TransferError, match="Failed to create recipient"):
            send_money(
                client,
                "USD",
                "USD",
                100.0,
                "Jane",
                "1234567890",
                recipient_routing_number="026073150",
                recipient_country="US",
                recipient_address="123 Main St",
                recipient_city="New York",
                recipient_post_code="10001",
            )

    @patch.object(WiseClient, "get")
    @patch.object(WiseClient, "post")
    def test_transfer_failure_raises(self, mock_post, mock_get):
        mock_get.return_value = _mock_response(200, [])
        mock_post.side_effect = [
            _mock_response(200, QUOTE_RESPONSE),
            _mock_response(200, RECIPIENT_RESPONSE),
            _mock_response(400),
        ]
        client = _make_client()
        with pytest.raises(TransferError, match="Failed to create transfer"):
            send_money(
                client,
                "USD",
                "USD",
                100.0,
                "Jane",
                "1234567890",
                recipient_routing_number="026073150",
                recipient_country="US",
                recipient_address="123 Main St",
                recipient_city="New York",
                recipient_post_code="10001",
            )

    @patch.object(WiseClient, "get")
    @patch.object(WiseClient, "post")
    def test_fund_failure_raises(self, mock_post, mock_get):
        mock_get.return_value = _mock_response(200, [])
        mock_post.side_effect = [
            _mock_response(200, QUOTE_RESPONSE),
            _mock_response(200, RECIPIENT_RESPONSE),
            _mock_response(200, TRANSFER_RESPONSE),
            _mock_response(403),
        ]
        client = _make_client()
        with pytest.raises(TransferError, match="Failed to fund transfer"):
            send_money(
                client,
                "USD",
                "USD",
                100.0,
                "Jane",
                "1234567890",
                recipient_routing_number="026073150",
                recipient_country="US",
                recipient_address="123 Main St",
                recipient_city="New York",
                recipient_post_code="10001",
            )

    @patch.object(WiseClient, "get")
    @patch.object(WiseClient, "post")
    def test_auth_error_at_quote(self, mock_post, mock_get):
        mock_get.return_value = _mock_response(200, [])
        mock_post.side_effect = [_mock_response(401)]
        client = _make_client()
        with pytest.raises(TransferError, match="Authentication failed"):
            send_money(
                client,
                "USD",
                "USD",
                100.0,
                "Jane",
                "1234567890",
                recipient_routing_number="026073150",
                recipient_country="US",
                recipient_address="123 Main St",
                recipient_city="New York",
                recipient_post_code="10001",
            )

    @patch.object(WiseClient, "get")
    @patch.object(WiseClient, "post")
    def test_fund_uses_balance_type(self, mock_post, mock_get):
        mock_get.return_value = _mock_response(200, [])
        mock_post.side_effect = [
            _mock_response(200, QUOTE_RESPONSE),
            _mock_response(200, RECIPIENT_RESPONSE),
            _mock_response(200, TRANSFER_RESPONSE),
            _mock_response(200, FUND_RESPONSE),
        ]
        client = _make_client(profile_id="12345")
        send_money(
            client,
            "USD",
            "USD",
            100.0,
            "Jane",
            "1234567890",
            recipient_routing_number="026073150",
            recipient_country="US",
            recipient_address="123 Main St",
            recipient_city="New York",
            recipient_post_code="10001",
        )
        fund_call = mock_post.call_args_list[3]
        assert fund_call.kwargs["json_body"]["type"] == "BALANCE"

    @patch.object(WiseClient, "get")
    @patch.object(WiseClient, "post")
    def test_usd_ach_payload_uses_abartn_and_address_in_details(self, mock_post, mock_get):
        """USD ACH recipient payload: details.abartn (not routingNumber) and address INSIDE details."""
        mock_get.return_value = _mock_response(200, [])  # requirements
        mock_post.side_effect = [
            _mock_response(200, QUOTE_RESPONSE),
            _mock_response(200, RECIPIENT_RESPONSE),
            _mock_response(200, TRANSFER_RESPONSE),
            _mock_response(200, FUND_RESPONSE),
        ]
        client = _make_client()
        send_money(
            client,
            source_currency="USD",
            target_currency="USD",
            amount=10.0,
            recipient_name="Jane Doe",
            recipient_account="123456789",
            recipient_routing_number="111000025",
            recipient_country="US",
            recipient_address="123 Main St",
            recipient_city="Kent",
            recipient_post_code="44240",
        )
        recipient_call = mock_post.call_args_list[1]  # quote=0, recipient=1
        payload = recipient_call.kwargs["json_body"]
        assert payload["type"] == "aba"
        details = payload["details"]
        assert "abartn" in details
        assert details["abartn"] == "111000025"
        assert "routingNumber" not in details
        # Address must be inside details, not at top level
        assert "address" not in payload  # Should NOT be at top level
        address = details["address"]
        assert address["country"] == "US"
        assert address["city"] == "Kent"
        assert address["firstLine"] == "123 Main St"
        assert address["postCode"] == "44240"

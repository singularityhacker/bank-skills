"""Tests for Story 10 — Core: insufficient funds error."""

from unittest.mock import MagicMock, patch

import pytest

from bankskills.core.bank.client import WiseClient
from bankskills.core.bank.credentials import WiseCredentials
from bankskills.core.bank.transfer import (
    InsufficientFundsError,
    TransferError,
    send_money,
)


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


class TestInsufficientFunds:
    @patch.object(WiseClient, "get")
    @patch.object(WiseClient, "post")
    def test_insufficient_funds_error_in_response_body(self, mock_post, mock_get):
        mock_get.return_value = _mock_response(200, [])
        """Wise returns error with errorCode in the response body."""
        mock_post.side_effect = [
            _mock_response(200, QUOTE_RESPONSE),
            _mock_response(200, RECIPIENT_RESPONSE),
            _mock_response(200, TRANSFER_RESPONSE),
            _mock_response(
                403,
                {"errorCode": "transfer.insufficient_funds", "message": "Not enough"},
            ),
        ]
        client = _make_client()
        with pytest.raises(InsufficientFundsError, match="Insufficient funds"):
            send_money(
                client,
                "USD",
                "USD",
                999999.0,
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
    def test_insufficient_funds_is_subclass_of_transfer_error(self, mock_post, mock_get):
        mock_get.return_value = _mock_response(200, [])
        """InsufficientFundsError should be catchable as TransferError."""
        mock_post.side_effect = [
            _mock_response(200, QUOTE_RESPONSE),
            _mock_response(200, RECIPIENT_RESPONSE),
            _mock_response(200, TRANSFER_RESPONSE),
            _mock_response(
                403,
                {"errorCode": "transfer.insufficient_funds"},
            ),
        ]
        client = _make_client()
        with pytest.raises(TransferError):
            send_money(
                client,
                "USD",
                "USD",
                999999.0,
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
    def test_rejected_status_with_insufficient_funds(self, mock_post, mock_get):
        mock_get.return_value = _mock_response(200, [])
        """Wise returns 200 but status REJECTED with errorCode."""
        mock_post.side_effect = [
            _mock_response(200, QUOTE_RESPONSE),
            _mock_response(200, RECIPIENT_RESPONSE),
            _mock_response(200, TRANSFER_RESPONSE),
            _mock_response(
                200,
                {
                    "status": "REJECTED",
                    "errorCode": "transfer.insufficient_funds",
                },
            ),
        ]
        client = _make_client()
        with pytest.raises(InsufficientFundsError, match="Insufficient funds"):
            send_money(
                client,
                "USD",
                "USD",
                999999.0,
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
    def test_error_message_is_human_readable(self, mock_post, mock_get):
        mock_get.return_value = _mock_response(200, [])
        mock_post.side_effect = [
            _mock_response(200, QUOTE_RESPONSE),
            _mock_response(200, RECIPIENT_RESPONSE),
            _mock_response(200, TRANSFER_RESPONSE),
            _mock_response(
                403,
                {"errorCode": "transfer.insufficient_funds"},
            ),
        ]
        client = _make_client()
        with pytest.raises(InsufficientFundsError) as exc_info:
            send_money(
                client,
                "USD",
                "USD",
                999999.0,
                "Jane",
                "1234567890",
                recipient_routing_number="026073150",
                recipient_country="US",
                recipient_address="123 Main St",
                recipient_city="New York",
                recipient_post_code="10001",
            )
        msg = str(exc_info.value)
        assert "Insufficient funds" in msg
        # Should be human-readable, not a raw error code
        assert "transfer.insufficient_funds" not in msg

    @patch.object(WiseClient, "get")
    @patch.object(WiseClient, "post")
    def test_no_retry_on_insufficient_funds(self, mock_post, mock_get):
        mock_get.return_value = _mock_response(200, [])
        """Verify send_money does NOT retry — post is called exactly 4 times."""
        mock_post.side_effect = [
            _mock_response(200, QUOTE_RESPONSE),
            _mock_response(200, RECIPIENT_RESPONSE),
            _mock_response(200, TRANSFER_RESPONSE),
            _mock_response(
                403,
                {"errorCode": "transfer.insufficient_funds"},
            ),
        ]
        client = _make_client()
        with pytest.raises(InsufficientFundsError):
            send_money(
                client,
                "USD",
                "USD",
                999999.0,
                "Jane",
                "1234567890",
                recipient_routing_number="026073150",
                recipient_country="US",
                recipient_address="123 Main St",
                recipient_city="New York",
                recipient_post_code="10001",
            )
        assert mock_post.call_count == 4

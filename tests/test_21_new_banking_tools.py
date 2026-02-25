"""Tests for new banking tools — Phase 1/2/3 from roadmap.

Covers core modules, MCP tool registration, descriptions, and parameters
for all 13 new tools: get_exchange_rate, list_currencies, get_profile,
get_transfer_status, list_recipients, get_delivery_estimate, get_quote,
list_transfers, delete_recipient, convert_balance, save_recipient,
get_balance_statement, get_activity.
"""

from unittest.mock import MagicMock, patch

import pytest

from bankskills.core.bank.client import WiseClient
from bankskills.core.bank.credentials import WiseCredentials
from bankskills.mcp.server import mcp


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client(profile_id="12345"):
    creds = WiseCredentials(api_token="test-token", profile_id=profile_id)
    return WiseClient(credentials=creds)


def _mock_response(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data if json_data is not None else []
    return resp


def _tool_names():
    return [t.name for t in mcp._tool_manager._tools.values()]


def _get_tool(name):
    for t in mcp._tool_manager._tools.values():
        if t.name == name:
            return t
    return None


# ===========================================================================
# Phase 1 — Core module tests
# ===========================================================================


class TestFetchExchangeRate:
    @patch.object(WiseClient, "get")
    def test_returns_rate(self, mock_get):
        mock_get.return_value = _mock_response(200, [
            {"rate": 1.166, "source": "EUR", "target": "USD", "time": "2025-01-01T00:00:00+0000"}
        ])
        from bankskills.core.bank.rates import fetch_exchange_rate
        client = _make_client()
        result = fetch_exchange_rate(client, source="EUR", target="USD")
        assert len(result) == 1
        assert result[0]["rate"] == 1.166
        assert result[0]["source"] == "EUR"

    @patch.object(WiseClient, "get")
    def test_passes_correct_params(self, mock_get):
        mock_get.return_value = _mock_response(200, [])
        from bankskills.core.bank.rates import fetch_exchange_rate
        client = _make_client()
        fetch_exchange_rate(client, source="gbp", target="jpy")
        mock_get.assert_called_once_with("/v1/rates", params={"source": "GBP", "target": "JPY"})

    @patch.object(WiseClient, "get")
    def test_historical_rate_passes_time(self, mock_get):
        mock_get.return_value = _mock_response(200, [])
        from bankskills.core.bank.rates import fetch_exchange_rate
        client = _make_client()
        fetch_exchange_rate(client, source="USD", target="EUR", time="2025-01-15T12:00:00")
        args = mock_get.call_args
        assert args[1]["params"]["time"] == "2025-01-15T12:00:00"

    @patch.object(WiseClient, "get")
    def test_auth_error_raises(self, mock_get):
        mock_get.return_value = _mock_response(401)
        from bankskills.core.bank.rates import RateError, fetch_exchange_rate
        client = _make_client()
        with pytest.raises(RateError, match="Authentication"):
            fetch_exchange_rate(client, source="USD", target="EUR")

    @patch.object(WiseClient, "get")
    def test_server_error_raises(self, mock_get):
        mock_get.return_value = _mock_response(500)
        from bankskills.core.bank.rates import RateError, fetch_exchange_rate
        client = _make_client()
        with pytest.raises(RateError, match="server error"):
            fetch_exchange_rate(client, source="USD", target="EUR")


class TestFetchCurrencies:
    @patch.object(WiseClient, "get")
    def test_returns_currencies(self, mock_get):
        mock_get.return_value = _mock_response(200, [
            {"code": "USD", "name": "US Dollar", "symbol": "$"},
            {"code": "EUR", "name": "Euro", "symbol": "€"},
        ])
        from bankskills.core.bank.currencies import fetch_currencies
        client = _make_client()
        result = fetch_currencies(client)
        assert len(result) == 2
        assert result[0]["code"] == "USD"

    @patch.object(WiseClient, "get")
    def test_calls_correct_endpoint(self, mock_get):
        mock_get.return_value = _mock_response(200, [])
        from bankskills.core.bank.currencies import fetch_currencies
        client = _make_client()
        fetch_currencies(client)
        mock_get.assert_called_once_with("/v1/currencies")

    @patch.object(WiseClient, "get")
    def test_auth_error_raises(self, mock_get):
        mock_get.return_value = _mock_response(401)
        from bankskills.core.bank.currencies import CurrencyError, fetch_currencies
        client = _make_client()
        with pytest.raises(CurrencyError, match="Authentication"):
            fetch_currencies(client)


class TestGetTransferStatus:
    @patch.object(WiseClient, "get")
    def test_returns_status(self, mock_get):
        mock_get.return_value = _mock_response(200, {
            "id": 123, "status": "funds_converted",
            "sourceCurrency": "USD", "sourceValue": 100,
            "targetCurrency": "EUR", "targetValue": 89.5,
            "rate": 0.895, "created": "2025-01-01",
            "hasActiveIssues": False,
        })
        from bankskills.core.bank.transfers import get_transfer_status
        client = _make_client()
        result = get_transfer_status(client, transfer_id=123)
        assert result["status"] == "funds_converted"
        assert result["id"] == 123

    @patch.object(WiseClient, "get")
    def test_not_found_raises(self, mock_get):
        mock_get.return_value = _mock_response(404)
        from bankskills.core.bank.transfers import TransferStatusError, get_transfer_status
        client = _make_client()
        with pytest.raises(TransferStatusError, match="not found"):
            get_transfer_status(client, transfer_id=999)

    @patch.object(WiseClient, "get")
    def test_calls_correct_endpoint(self, mock_get):
        mock_get.return_value = _mock_response(200, {"id": 42})
        from bankskills.core.bank.transfers import get_transfer_status
        client = _make_client()
        get_transfer_status(client, transfer_id=42)
        mock_get.assert_called_once_with("/v1/transfers/42")


class TestListTransfers:
    @patch.object(WiseClient, "get")
    def test_returns_transfers(self, mock_get):
        mock_get.return_value = _mock_response(200, [
            {"id": 1, "status": "funds_converted", "sourceCurrency": "USD",
             "sourceValue": 100, "targetCurrency": "EUR", "targetValue": 89,
             "rate": 0.89, "created": "2025-01-01"},
        ])
        from bankskills.core.bank.transfers import list_transfers
        client = _make_client()
        result = list_transfers(client)
        assert len(result) == 1
        assert result[0]["id"] == 1

    @patch.object(WiseClient, "get")
    def test_passes_status_filter(self, mock_get):
        mock_get.return_value = _mock_response(200, [])
        from bankskills.core.bank.transfers import list_transfers
        client = _make_client()
        list_transfers(client, status="cancelled")
        args = mock_get.call_args
        assert args[1]["params"]["status"] == "cancelled"

    @patch.object(WiseClient, "get")
    def test_auth_error_raises(self, mock_get):
        mock_get.return_value = _mock_response(401)
        from bankskills.core.bank.transfers import TransferStatusError, list_transfers
        client = _make_client()
        with pytest.raises(TransferStatusError, match="Authentication"):
            list_transfers(client)


class TestGetDeliveryEstimate:
    @patch.object(WiseClient, "get")
    def test_returns_estimate(self, mock_get):
        mock_get.return_value = _mock_response(200, {
            "estimatedDeliveryDate": "2025-01-05T12:00:00Z"
        })
        from bankskills.core.bank.transfers import get_delivery_estimate
        client = _make_client()
        result = get_delivery_estimate(client, transfer_id=123)
        assert "estimatedDeliveryDate" in result

    @patch.object(WiseClient, "get")
    def test_not_found_raises(self, mock_get):
        mock_get.return_value = _mock_response(404)
        from bankskills.core.bank.transfers import DeliveryEstimateError, get_delivery_estimate
        client = _make_client()
        with pytest.raises(DeliveryEstimateError, match="not found"):
            get_delivery_estimate(client, transfer_id=999)


class TestListRecipients:
    @patch.object(WiseClient, "get")
    def test_returns_recipients(self, mock_get):
        mock_get.return_value = _mock_response(200, [
            {"id": 10, "accountHolderName": "John Doe", "currency": "GBP",
             "country": "GB", "type": "sort_code", "active": True},
        ])
        from bankskills.core.bank.recipients import list_recipients
        client = _make_client()
        result = list_recipients(client)
        assert len(result) == 1
        assert result[0]["accountHolderName"] == "John Doe"

    @patch.object(WiseClient, "get")
    def test_currency_filter(self, mock_get):
        mock_get.return_value = _mock_response(200, [])
        from bankskills.core.bank.recipients import list_recipients
        client = _make_client()
        list_recipients(client, currency="usd")
        args = mock_get.call_args
        assert args[1]["params"]["currency"] == "USD"

    @patch.object(WiseClient, "get")
    def test_auth_error_raises(self, mock_get):
        mock_get.return_value = _mock_response(401)
        from bankskills.core.bank.recipients import RecipientError, list_recipients
        client = _make_client()
        with pytest.raises(RecipientError, match="Authentication"):
            list_recipients(client)


# ===========================================================================
# Phase 2 — Core module tests
# ===========================================================================


class TestCreateQuote:
    @patch.object(WiseClient, "post")
    def test_returns_quote(self, mock_post):
        mock_post.return_value = _mock_response(200, {
            "id": "abc-123", "rate": 0.89,
            "sourceCurrency": "USD", "sourceAmount": 100,
            "targetCurrency": "EUR", "targetAmount": 89,
            "rateExpirationTime": "2025-01-01T01:00:00Z",
            "paymentOptions": [{"disabled": False, "fee": {"total": 1.5},
                                "formattedEstimatedDelivery": "by Jan 3"}],
        })
        from bankskills.core.bank.quotes import create_quote
        client = _make_client()
        result = create_quote(client, source_currency="USD", target_currency="EUR", amount=100)
        assert result["rate"] == 0.89
        assert result["fee"] == 1.5
        assert result["estimatedDelivery"] == "by Jan 3"

    @patch.object(WiseClient, "post")
    def test_auth_error_raises(self, mock_post):
        mock_post.return_value = _mock_response(401)
        from bankskills.core.bank.quotes import QuoteError, create_quote
        client = _make_client()
        with pytest.raises(QuoteError, match="Authentication"):
            create_quote(client, source_currency="USD", target_currency="EUR", amount=100)

    @patch.object(WiseClient, "post")
    def test_calls_correct_endpoint(self, mock_post):
        mock_post.return_value = _mock_response(200, {
            "id": "x", "rate": 1.0, "paymentOptions": [],
        })
        from bankskills.core.bank.quotes import create_quote
        client = _make_client(profile_id="999")
        create_quote(client, source_currency="GBP", target_currency="USD", amount=50)
        args = mock_post.call_args
        assert "/v3/profiles/999/quotes" in args[0][0]


class TestDeleteRecipient:
    @patch.object(WiseClient, "delete")
    def test_returns_deactivated(self, mock_delete):
        mock_delete.return_value = _mock_response(200, {
            "id": 42, "accountHolderName": "Jane", "currency": "EUR", "active": False,
        })
        from bankskills.core.bank.recipients import delete_recipient
        client = _make_client()
        result = delete_recipient(client, recipient_id=42)
        assert result["active"] is False
        assert result["id"] == 42

    @patch.object(WiseClient, "delete")
    def test_already_inactive_raises(self, mock_delete):
        mock_delete.return_value = _mock_response(403)
        from bankskills.core.bank.recipients import RecipientError, delete_recipient
        client = _make_client()
        with pytest.raises(RecipientError, match="already inactive"):
            delete_recipient(client, recipient_id=42)

    @patch.object(WiseClient, "delete")
    def test_not_found_raises(self, mock_delete):
        mock_delete.return_value = _mock_response(404)
        from bankskills.core.bank.recipients import RecipientError, delete_recipient
        client = _make_client()
        with pytest.raises(RecipientError, match="not found"):
            delete_recipient(client, recipient_id=999)

    @patch.object(WiseClient, "delete")
    def test_calls_correct_endpoint(self, mock_delete):
        mock_delete.return_value = _mock_response(200, {"id": 7, "active": False})
        from bankskills.core.bank.recipients import delete_recipient
        client = _make_client()
        delete_recipient(client, recipient_id=7)
        mock_delete.assert_called_once_with("/v2/accounts/7")


class TestCreateBalance:
    @patch.object(WiseClient, "post")
    def test_creates_balance(self, mock_post):
        mock_post.return_value = _mock_response(201, {
            "id": 999, "currency": "EUR", "type": "STANDARD",
        })
        from bankskills.core.bank.balance_convert import create_balance
        client = _make_client()
        result = create_balance(client, currency="EUR")
        assert result["id"] == 999
        assert result["currency"] == "EUR"

    @patch.object(WiseClient, "post")
    def test_sends_idempotence_header(self, mock_post):
        mock_post.return_value = _mock_response(201, {"id": 1, "currency": "EUR", "type": "STANDARD"})
        from bankskills.core.bank.balance_convert import create_balance
        client = _make_client()
        create_balance(client, currency="EUR")
        extra = mock_post.call_args[1].get("extra_headers", {})
        assert "X-idempotence-uuid" in extra

    @patch.object(WiseClient, "post")
    def test_auth_error_raises(self, mock_post):
        mock_post.return_value = _mock_response(401)
        from bankskills.core.bank.balance_convert import CreateBalanceError, create_balance
        client = _make_client()
        with pytest.raises(CreateBalanceError, match="Authentication"):
            create_balance(client, currency="EUR")

    @patch.object(WiseClient, "post")
    def test_calls_correct_endpoint(self, mock_post):
        mock_post.return_value = _mock_response(201, {"id": 1, "currency": "GBP", "type": "STANDARD"})
        from bankskills.core.bank.balance_convert import create_balance
        client = _make_client(profile_id="99999")
        create_balance(client, currency="GBP")
        assert "/v4/profiles/99999/balances" in mock_post.call_args[0][0]


class TestConvertBalance:
    @patch.object(WiseClient, "post")
    def test_returns_conversion(self, mock_post):
        mock_post.side_effect = [
            _mock_response(200, {
                "id": "q-1", "rate": 0.89, "targetAmount": 89,
                "paymentOptions": [{"payIn": "BALANCE", "payOut": "BALANCE", "disabled": False}],
            }),
            _mock_response(200, {"id": "m-1"}),
        ]
        from bankskills.core.bank.balance_convert import convert_balance
        client = _make_client()
        result = convert_balance(client, source_currency="USD", target_currency="EUR", amount=100)
        assert result["rate"] == 0.89
        assert result["sourceCurrency"] == "USD"
        assert result["targetCurrency"] == "EUR"

    @patch.object(WiseClient, "post")
    def test_quote_includes_payout_balance(self, mock_post):
        mock_post.side_effect = [
            _mock_response(200, {"id": "q-1", "rate": 0.89, "targetAmount": 89, "paymentOptions": []}),
            _mock_response(200, {"id": "m-1"}),
        ]
        from bankskills.core.bank.balance_convert import convert_balance
        client = _make_client()
        convert_balance(client, source_currency="USD", target_currency="EUR", amount=100)
        quote_call = mock_post.call_args_list[0]
        body = quote_call[1]["json_body"]
        assert body["payOut"] == "BALANCE"

    @patch.object(WiseClient, "post")
    def test_sends_idempotence_header(self, mock_post):
        mock_post.side_effect = [
            _mock_response(200, {"id": "q-1", "rate": 0.89, "targetAmount": 89, "paymentOptions": []}),
            _mock_response(200, {"id": "m-1"}),
        ]
        from bankskills.core.bank.balance_convert import convert_balance
        client = _make_client()
        convert_balance(client, source_currency="USD", target_currency="EUR", amount=100)
        balance_movement_call = mock_post.call_args_list[1]
        extra = balance_movement_call[1].get("extra_headers", {})
        assert "X-idempotence-uuid" in extra
        assert len(extra["X-idempotence-uuid"]) == 36

    @patch.object(WiseClient, "post")
    def test_disabled_balance_option_raises(self, mock_post):
        mock_post.return_value = _mock_response(200, {
            "id": "q-1", "rate": 0.89, "targetAmount": 89,
            "paymentOptions": [{
                "payIn": "BALANCE", "payOut": "BALANCE", "disabled": True,
                "disabledReason": {"message": "Target balance not found"},
            }],
        })
        from bankskills.core.bank.balance_convert import ConversionError, convert_balance
        client = _make_client()
        with pytest.raises(ConversionError, match="BALANCE payment option is disabled"):
            convert_balance(client, source_currency="USD", target_currency="EUR", amount=100)

    @patch.object(WiseClient, "post")
    def test_quote_auth_error_raises(self, mock_post):
        mock_post.return_value = _mock_response(401)
        from bankskills.core.bank.balance_convert import ConversionError, convert_balance
        client = _make_client()
        with pytest.raises(ConversionError, match="Authentication"):
            convert_balance(client, source_currency="USD", target_currency="EUR", amount=100)

    @patch.object(WiseClient, "post")
    def test_conversion_failure_raises(self, mock_post):
        mock_post.side_effect = [
            _mock_response(200, {"id": "q-1", "rate": 0.89, "targetAmount": 89, "paymentOptions": []}),
            _mock_response(400, {"message": "Insufficient funds"}),
        ]
        from bankskills.core.bank.balance_convert import ConversionError, convert_balance
        client = _make_client()
        with pytest.raises(ConversionError, match="Failed to convert"):
            convert_balance(client, source_currency="USD", target_currency="EUR", amount=100)


# ===========================================================================
# Phase 3 — Core module tests
# ===========================================================================


class TestSaveRecipient:
    @patch.object(WiseClient, "post")
    def test_saves_iban_recipient(self, mock_post):
        mock_post.return_value = _mock_response(201, {
            "id": 55, "accountHolderName": "Hans", "currency": "EUR",
            "type": "iban", "active": True,
        })
        from bankskills.core.bank.recipients import save_recipient
        client = _make_client()
        result = save_recipient(client, currency="EUR", recipient_name="Hans",
                                account_number="DE89370400440532013000")
        assert result["id"] == 55
        assert result["type"] == "iban"

    @patch.object(WiseClient, "post")
    def test_saves_aba_recipient(self, mock_post):
        mock_post.return_value = _mock_response(201, {
            "id": 56, "accountHolderName": "Jane", "currency": "USD",
            "type": "aba", "active": True,
        })
        from bankskills.core.bank.recipients import save_recipient
        client = _make_client()
        result = save_recipient(client, currency="USD", recipient_name="Jane",
                                account_number="123456789", recipient_type="aba",
                                routing_number="111000025", country="US",
                                address="123 Main St", city="NY", post_code="10001")
        assert result["type"] == "aba"

    @patch.object(WiseClient, "post")
    def test_aba_requires_routing_number(self, mock_post):
        from bankskills.core.bank.recipients import RecipientError, save_recipient
        client = _make_client()
        with pytest.raises(RecipientError, match="routing_number"):
            save_recipient(client, currency="USD", recipient_name="Jane",
                           account_number="123456789", recipient_type="aba")

    @patch.object(WiseClient, "post")
    def test_sort_code_requires_sort_code(self, mock_post):
        from bankskills.core.bank.recipients import RecipientError, save_recipient
        client = _make_client()
        with pytest.raises(RecipientError, match="sort_code"):
            save_recipient(client, currency="GBP", recipient_name="Bob",
                           account_number="12345678", recipient_type="sort_code")


class TestGetBalanceStatement:
    @patch.object(WiseClient, "get")
    def test_returns_statement(self, mock_get):
        mock_get.side_effect = [
            _mock_response(200, [{"id": 1, "currency": "USD"}]),
            _mock_response(200, {
                "endOfStatementBalance": {"value": 1000},
                "transactions": [
                    {"type": "CREDIT", "date": "2025-01-15", "amount": {"value": 500, "currency": "USD"},
                     "runningBalance": {"value": 1500}, "referenceNumber": "REF1",
                     "details": {"description": "Deposit"}},
                ],
            }),
        ]
        from bankskills.core.bank.statements import get_balance_statement
        client = _make_client()
        result = get_balance_statement(client, currency="USD",
                                       start_date="2025-01-01T00:00:00Z",
                                       end_date="2025-01-31T23:59:59Z")
        assert result["currency"] == "USD"
        assert len(result["transactions"]) == 1
        assert result["transactions"][0]["amount"] == 500

    @patch.object(WiseClient, "get")
    def test_missing_currency_raises(self, mock_get):
        mock_get.return_value = _mock_response(200, [{"id": 1, "currency": "EUR"}])
        from bankskills.core.bank.statements import StatementError, get_balance_statement
        client = _make_client()
        with pytest.raises(StatementError, match="No balance found"):
            get_balance_statement(client, currency="GBP",
                                  start_date="2025-01-01T00:00:00Z",
                                  end_date="2025-01-31T23:59:59Z")


class TestGetActivity:
    @patch.object(WiseClient, "get")
    def test_returns_activities(self, mock_get):
        mock_get.return_value = _mock_response(200, {
            "activities": [
                {"type": "TRANSFER", "title": "Sent USD", "description": "To John",
                 "primaryAmount": 100, "status": "COMPLETED", "createdOn": "2025-01-15"},
            ]
        })
        from bankskills.core.bank.activity import get_activity
        client = _make_client()
        result = get_activity(client)
        assert len(result) == 1
        assert result[0]["type"] == "TRANSFER"

    @patch.object(WiseClient, "get")
    def test_passes_date_filters(self, mock_get):
        mock_get.return_value = _mock_response(200, {"activities": []})
        from bankskills.core.bank.activity import get_activity
        client = _make_client()
        get_activity(client, since="2025-01-01T00:00:00Z", until="2025-01-31T23:59:59Z")
        args = mock_get.call_args
        assert args[1]["params"]["since"] == "2025-01-01T00:00:00Z"
        assert args[1]["params"]["until"] == "2025-01-31T23:59:59Z"

    @patch.object(WiseClient, "get")
    def test_auth_error_raises(self, mock_get):
        mock_get.return_value = _mock_response(401)
        from bankskills.core.bank.activity import ActivityError, get_activity
        client = _make_client()
        with pytest.raises(ActivityError, match="Authentication"):
            get_activity(client)

    @patch.object(WiseClient, "get")
    def test_handles_list_response(self, mock_get):
        mock_get.return_value = _mock_response(200, [
            {"type": "CARD", "title": "Card purchase", "status": "COMPLETED"},
        ])
        from bankskills.core.bank.activity import get_activity
        client = _make_client()
        result = get_activity(client)
        assert len(result) == 1
        assert result[0]["type"] == "CARD"


# ===========================================================================
# MCP Tool Registration — all 13 new tools
# ===========================================================================


class TestNewMCPToolsExist:
    """Verify every new tool is registered on the MCP server."""

    def test_has_get_exchange_rate(self):
        assert "get_exchange_rate" in _tool_names()

    def test_has_list_currencies(self):
        assert "list_currencies" in _tool_names()

    def test_has_get_profile(self):
        assert "get_profile" in _tool_names()

    def test_has_get_transfer_status(self):
        assert "get_transfer_status" in _tool_names()

    def test_has_list_recipients(self):
        assert "list_recipients" in _tool_names()

    def test_has_get_delivery_estimate(self):
        assert "get_delivery_estimate" in _tool_names()

    def test_has_get_quote(self):
        assert "get_quote" in _tool_names()

    def test_has_list_transfers(self):
        assert "list_transfers" in _tool_names()

    def test_has_delete_recipient(self):
        assert "delete_recipient" in _tool_names()

    def test_has_convert_balance(self):
        assert "convert_balance" in _tool_names()

    def test_has_save_recipient(self):
        assert "save_recipient" in _tool_names()

    def test_has_get_balance_statement(self):
        assert "get_balance_statement" in _tool_names()

    def test_has_get_activity(self):
        assert "get_activity" in _tool_names()

    def test_has_create_balance(self):
        assert "create_balance" in _tool_names()


class TestNewMCPToolDescriptions:
    """Verify every new tool has a meaningful docstring for LLM discovery."""

    def test_get_exchange_rate_description(self):
        tool = _get_tool("get_exchange_rate")
        assert tool.description
        assert "rate" in tool.description.lower()

    def test_list_currencies_description(self):
        tool = _get_tool("list_currencies")
        assert tool.description
        assert "currenc" in tool.description.lower()

    def test_get_profile_description(self):
        tool = _get_tool("get_profile")
        assert tool.description
        assert "profile" in tool.description.lower()

    def test_get_transfer_status_description(self):
        tool = _get_tool("get_transfer_status")
        assert tool.description
        assert "status" in tool.description.lower()

    def test_list_recipients_description(self):
        tool = _get_tool("list_recipients")
        assert tool.description
        assert "recipient" in tool.description.lower()

    def test_get_delivery_estimate_description(self):
        tool = _get_tool("get_delivery_estimate")
        assert tool.description
        assert "delivery" in tool.description.lower()

    def test_get_quote_description(self):
        tool = _get_tool("get_quote")
        assert tool.description
        assert "rate" in tool.description.lower() or "fee" in tool.description.lower()

    def test_list_transfers_description(self):
        tool = _get_tool("list_transfers")
        assert tool.description
        assert "transfer" in tool.description.lower()

    def test_delete_recipient_description(self):
        tool = _get_tool("delete_recipient")
        assert tool.description
        assert "deactivat" in tool.description.lower() or "remove" in tool.description.lower()

    def test_convert_balance_description(self):
        tool = _get_tool("convert_balance")
        assert tool.description
        assert "convert" in tool.description.lower()

    def test_save_recipient_description(self):
        tool = _get_tool("save_recipient")
        assert tool.description
        assert "recipient" in tool.description.lower()

    def test_get_balance_statement_description(self):
        tool = _get_tool("get_balance_statement")
        assert tool.description
        assert "statement" in tool.description.lower() or "transaction" in tool.description.lower()

    def test_get_activity_description(self):
        tool = _get_tool("get_activity")
        assert tool.description
        assert "activity" in tool.description.lower() or "feed" in tool.description.lower()

    def test_create_balance_description(self):
        tool = _get_tool("create_balance")
        assert tool.description
        assert "balance" in tool.description.lower()


class TestNewMCPToolParameters:
    """Verify required parameters are declared correctly."""

    def test_get_exchange_rate_requires_source_and_target(self):
        tool = _get_tool("get_exchange_rate")
        required = tool.parameters.get("required", [])
        assert "source" in required
        assert "target" in required

    def test_get_transfer_status_requires_transfer_id(self):
        tool = _get_tool("get_transfer_status")
        required = tool.parameters.get("required", [])
        assert "transfer_id" in required

    def test_get_delivery_estimate_requires_transfer_id(self):
        tool = _get_tool("get_delivery_estimate")
        required = tool.parameters.get("required", [])
        assert "transfer_id" in required

    def test_get_quote_requires_currencies_and_amount(self):
        tool = _get_tool("get_quote")
        required = tool.parameters.get("required", [])
        assert "source_currency" in required
        assert "target_currency" in required
        assert "amount" in required

    def test_delete_recipient_requires_recipient_id(self):
        tool = _get_tool("delete_recipient")
        required = tool.parameters.get("required", [])
        assert "recipient_id" in required

    def test_convert_balance_requires_currencies_and_amount(self):
        tool = _get_tool("convert_balance")
        required = tool.parameters.get("required", [])
        assert "source_currency" in required
        assert "target_currency" in required
        assert "amount" in required

    def test_save_recipient_requires_core_fields(self):
        tool = _get_tool("save_recipient")
        required = tool.parameters.get("required", [])
        assert "currency" in required
        assert "recipient_name" in required
        assert "account_number" in required

    def test_get_balance_statement_requires_currency_and_dates(self):
        tool = _get_tool("get_balance_statement")
        required = tool.parameters.get("required", [])
        assert "currency" in required
        assert "start_date" in required
        assert "end_date" in required

    def test_list_currencies_has_no_required_params(self):
        tool = _get_tool("list_currencies")
        required = tool.parameters.get("required", [])
        assert len(required) == 0

    def test_get_profile_has_no_required_params(self):
        tool = _get_tool("get_profile")
        required = tool.parameters.get("required", [])
        assert len(required) == 0

    def test_get_activity_has_optional_date_params(self):
        tool = _get_tool("get_activity")
        required = tool.parameters.get("required", [])
        props = tool.parameters.get("properties", {})
        assert len(required) == 0
        assert "since" in props
        assert "until" in props

    def test_list_recipients_has_optional_currency(self):
        tool = _get_tool("list_recipients")
        required = tool.parameters.get("required", [])
        props = tool.parameters.get("properties", {})
        assert "currency" not in required
        assert "currency" in props

    def test_create_balance_requires_currency(self):
        tool = _get_tool("create_balance")
        required = tool.parameters.get("required", [])
        assert "currency" in required


class TestWiseClientDelete:
    """Verify the new delete method on WiseClient."""

    def test_delete_method_exists(self):
        client = _make_client()
        assert hasattr(client, "delete")

    @patch("httpx.delete")
    def test_delete_sends_auth_header(self, mock_httpx_delete):
        mock_httpx_delete.return_value = _mock_response(200, {})
        client = _make_client()
        client.delete("/v2/accounts/1")
        args = mock_httpx_delete.call_args
        assert "Bearer test-token" in args[1]["headers"]["Authorization"]


class TestProfileIdParameter:
    """Verify profile_id is an optional parameter on all profile-scoped tools."""

    PROFILE_SCOPED_TOOLS = [
        "check_balance",
        "get_receive_details",
        "send_money",
        "list_recipients",
        "get_quote",
        "list_transfers",
        "convert_balance",
        "create_balance",
        "save_recipient",
        "get_balance_statement",
        "get_activity",
    ]

    def test_all_profile_scoped_tools_have_profile_id_param(self):
        for name in self.PROFILE_SCOPED_TOOLS:
            tool = _get_tool(name)
            assert tool is not None, f"Tool {name} not found"
            props = tool.parameters.get("properties", {})
            assert "profile_id" in props, f"{name} missing profile_id parameter"

    def test_profile_id_is_never_required(self):
        for name in self.PROFILE_SCOPED_TOOLS:
            tool = _get_tool(name)
            required = tool.parameters.get("required", [])
            assert "profile_id" not in required, f"{name} should not require profile_id"

    def test_profile_id_described_in_docstrings(self):
        for name in self.PROFILE_SCOPED_TOOLS:
            tool = _get_tool(name)
            assert "profile_id" in tool.description or "profile" in tool.description.lower(), \
                f"{name} description should mention profile_id"

    def test_non_profile_tools_lack_profile_id(self):
        non_profile_tools = [
            "get_exchange_rate", "list_currencies", "get_profile",
            "get_transfer_status", "get_delivery_estimate", "delete_recipient",
        ]
        for name in non_profile_tools:
            tool = _get_tool(name)
            if tool is None:
                continue
            props = tool.parameters.get("properties", {})
            assert "profile_id" not in props, f"{name} should NOT have profile_id"


class TestProfileIdPassthrough:
    """Verify profile_id is correctly passed through to core functions."""

    @patch.object(WiseClient, "get")
    def test_check_balance_passes_profile_id(self, mock_get):
        mock_get.return_value = _mock_response(200, [])
        from bankskills.core.bank.balances import fetch_balances
        client = _make_client(profile_id=None)
        fetch_balances(client, profile_id="83191616")
        args = mock_get.call_args
        assert "83191616" in args[0][0]

    @patch.object(WiseClient, "get")
    def test_check_balance_defaults_without_profile_id(self, mock_get):
        mock_get.return_value = _mock_response(200, [])
        from bankskills.core.bank.balances import fetch_balances
        client = _make_client(profile_id="17528870")
        fetch_balances(client)
        args = mock_get.call_args
        assert "17528870" in args[0][0]

    @patch.object(WiseClient, "get")
    def test_list_recipients_passes_profile_id(self, mock_get):
        mock_get.return_value = _mock_response(200, [])
        from bankskills.core.bank.recipients import list_recipients
        client = _make_client(profile_id=None)
        list_recipients(client, profile_id="83191616")
        args = mock_get.call_args
        assert args[1]["params"]["profile"] == "83191616"

    @patch.object(WiseClient, "get")
    def test_get_activity_passes_profile_id(self, mock_get):
        mock_get.return_value = _mock_response(200, {"activities": []})
        from bankskills.core.bank.activity import get_activity
        client = _make_client(profile_id=None)
        get_activity(client, profile_id="83191616")
        args = mock_get.call_args
        assert "83191616" in args[0][0]


class TestTotalToolCount:
    """Verify we now have 25 tools total (11 original + 14 new)."""

    def test_total_tool_count(self):
        names = _tool_names()
        assert len(names) >= 25, f"Expected >= 25 tools, got {len(names)}: {sorted(names)}"

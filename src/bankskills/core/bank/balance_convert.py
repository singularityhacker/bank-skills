"""Currency conversion and balance creation within a Wise multi-currency account."""

import uuid
from typing import Any, Dict, Optional

from bankskills.core.bank.client import WiseClient
from bankskills.core.bank.profiles import resolve_profile_id


class ConversionError(Exception):
    """Raised when a balance conversion fails."""


class CreateBalanceError(Exception):
    """Raised when opening a new currency balance fails."""


def create_balance(
    client: WiseClient,
    currency: str,
    profile_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Open a new STANDARD balance in the given currency.

    Wise requires a balance to exist in both the source and target
    currencies before a conversion can be executed. Call this if the
    target currency balance doesn't exist yet.

    Args:
        client: Configured WiseClient.
        currency: ISO currency code to open (e.g. "EUR", "GBP").
        profile_id: Profile ID (resolved automatically if None).

    Returns:
        Dict with id, currency, and type of the created balance.

    Raises:
        CreateBalanceError: on API error.
    """
    pid = resolve_profile_id(client, profile_id or client.credentials.profile_id)

    resp = client.post(
        f"/v4/profiles/{pid}/balances",
        json_body={
            "currency": currency.upper(),
            "type": "STANDARD",
        },
        extra_headers={"X-idempotence-uuid": str(uuid.uuid4())},
    )

    if resp.status_code == 401:
        raise CreateBalanceError("Authentication failed — check your WISE_API_TOKEN")
    if resp.status_code not in (200, 201):
        msg = f"Failed to create {currency} balance: HTTP {resp.status_code}"
        try:
            body = resp.json()
            if isinstance(body, dict):
                err = body.get("errors") or body.get("message") or body
                msg += f" — {err}"
        except Exception:
            pass
        raise CreateBalanceError(msg)

    data = resp.json()
    return {
        "id": data.get("id"),
        "currency": data.get("currency"),
        "type": data.get("type"),
    }


def convert_balance(
    client: WiseClient,
    source_currency: str,
    target_currency: str,
    amount: float,
    profile_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Convert money between currencies within the Wise multi-currency account.

    This does NOT send money externally — it moves funds between your own
    currency balances (e.g. USD balance -> EUR balance). Uses a two-step
    flow: create a quote with payOut=BALANCE, then execute the conversion.

    Both source and target currency balances must exist. If the target
    balance doesn't exist yet, call create_balance first.

    Args:
        client: Configured WiseClient.
        source_currency: Currency to convert from (e.g. "USD").
        target_currency: Currency to convert to (e.g. "EUR").
        amount: Amount in source currency to convert.
        profile_id: Profile ID (resolved automatically if None).

    Returns:
        Dict with quoteId, sourceCurrency, sourceAmount, targetCurrency,
        targetAmount, and rate.

    Raises:
        ConversionError: on API error.
    """
    pid = resolve_profile_id(client, profile_id or client.credentials.profile_id)

    quote_resp = client.post(
        f"/v3/profiles/{pid}/quotes",
        json_body={
            "sourceCurrency": source_currency.upper(),
            "targetCurrency": target_currency.upper(),
            "sourceAmount": amount,
            "targetAmount": None,
            "payOut": "BALANCE",
        },
    )

    if quote_resp.status_code == 401:
        raise ConversionError("Authentication failed — check your WISE_API_TOKEN")
    if quote_resp.status_code not in (200, 201):
        raise ConversionError(f"Failed to create conversion quote: HTTP {quote_resp.status_code}")

    quote = quote_resp.json()
    quote_id = quote.get("id")

    payment_options = quote.get("paymentOptions", [])
    balance_option = next(
        (opt for opt in payment_options
         if opt.get("payIn") == "BALANCE" and opt.get("payOut") == "BALANCE"),
        None,
    )
    if balance_option and balance_option.get("disabled"):
        reason = balance_option.get("disabledReason", {}).get("message", "")
        raise ConversionError(
            f"BALANCE payment option is disabled for {source_currency}->{target_currency}. "
            f"You may need to open a {target_currency} balance first using create_balance. "
            f"Wise says: {reason}"
        )

    convert_resp = client.post(
        f"/v2/profiles/{pid}/balance-movements",
        json_body={"quoteId": quote_id},
        extra_headers={"X-idempotence-uuid": str(uuid.uuid4())},
    )

    if convert_resp.status_code == 401:
        raise ConversionError("Authentication failed — check your WISE_API_TOKEN")
    if convert_resp.status_code >= 500:
        raise ConversionError(f"Wise API server error: HTTP {convert_resp.status_code}")
    if convert_resp.status_code not in (200, 201):
        msg = f"Failed to convert balance: HTTP {convert_resp.status_code}"
        try:
            body = convert_resp.json()
            if isinstance(body, dict):
                err = body.get("errors") or body.get("message") or body
                msg += f" — {err}"
        except Exception:
            pass
        raise ConversionError(msg)

    return {
        "quoteId": quote_id,
        "sourceCurrency": source_currency.upper(),
        "sourceAmount": amount,
        "targetCurrency": target_currency.upper(),
        "targetAmount": quote.get("targetAmount"),
        "rate": quote.get("rate"),
    }

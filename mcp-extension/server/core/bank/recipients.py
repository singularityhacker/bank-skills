"""Recipient (beneficiary) management via the Wise API."""

from typing import Any, Dict, List, Optional

from core.bank.client import WiseClient
from core.bank.profiles import resolve_profile_id


class RecipientError(Exception):
    """Raised when a recipient operation fails."""


def list_recipients(
    client: WiseClient,
    profile_id: Optional[str] = None,
    currency: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """List saved recipient accounts for the profile.

    Args:
        client: Configured WiseClient.
        profile_id: Profile ID (resolved automatically if None).
        currency: Optional currency filter (e.g. "USD").

    Returns:
        List of recipient dicts with id, accountHolderName, currency, type.

    Raises:
        RecipientError: on API error.
    """
    pid = resolve_profile_id(client, profile_id or client.credentials.profile_id)

    params: Dict[str, str] = {"profile": pid}
    if currency:
        params["currency"] = currency.upper()

    resp = client.get("/v1/accounts", params=params)

    if resp.status_code == 401:
        raise RecipientError("Authentication failed — check your WISE_API_TOKEN")
    if resp.status_code >= 500:
        raise RecipientError(f"Wise API server error: HTTP {resp.status_code}")
    if resp.status_code != 200:
        raise RecipientError(f"Unexpected API error: HTTP {resp.status_code}")

    raw = resp.json()
    recipients = []
    for r in raw:
        recipients.append({
            "id": r.get("id"),
            "accountHolderName": r.get("accountHolderName"),
            "currency": r.get("currency"),
            "country": r.get("country"),
            "type": r.get("type"),
            "active": r.get("active", True),
        })
    return recipients


def delete_recipient(
    client: WiseClient,
    recipient_id: int,
) -> Dict[str, Any]:
    """Deactivate a saved recipient account.

    Args:
        client: Configured WiseClient.
        recipient_id: The numeric recipient/account ID.

    Returns:
        Dict with id and active=False on success.

    Raises:
        RecipientError: on API error.
    """
    resp = client.delete(f"/v2/accounts/{recipient_id}")

    if resp.status_code == 401:
        raise RecipientError("Authentication failed — check your WISE_API_TOKEN")
    if resp.status_code == 403:
        raise RecipientError(f"Recipient {recipient_id} is already inactive or cannot be deleted")
    if resp.status_code == 404:
        raise RecipientError(f"Recipient {recipient_id} not found")
    if resp.status_code >= 500:
        raise RecipientError(f"Wise API server error: HTTP {resp.status_code}")
    if resp.status_code != 200:
        raise RecipientError(f"Unexpected API error: HTTP {resp.status_code}")

    data = resp.json()
    return {
        "id": data.get("id"),
        "accountHolderName": data.get("accountHolderName"),
        "currency": data.get("currency"),
        "active": data.get("active", False),
    }


def save_recipient(
    client: WiseClient,
    currency: str,
    recipient_name: str,
    account_number: str,
    recipient_type: str = "iban",
    profile_id: Optional[str] = None,
    sort_code: Optional[str] = None,
    routing_number: Optional[str] = None,
    account_type: Optional[str] = None,
    country: Optional[str] = None,
    address: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    post_code: Optional[str] = None,
) -> Dict[str, Any]:
    """Create and save a new recipient for future transfers.

    Args:
        client: Configured WiseClient.
        currency: 3-letter currency code (e.g. "USD", "EUR", "GBP").
        recipient_name: Full name of the recipient.
        account_number: Account number, IBAN, or other account identifier.
        recipient_type: Wise account type (e.g. "iban", "aba", "sort_code").
        profile_id: Profile ID (resolved automatically if None).
        sort_code: UK sort code (for GBP sort_code type).
        routing_number: US ABA routing number (for USD aba type).
        account_type: CHECKING or SAVINGS (for USD aba type).
        country: 2-letter country code for address (required for USD).
        address: Street address (required for USD).
        city: City (required for USD).
        state: State code (optional, for US addresses).
        post_code: ZIP/postal code (required for USD).

    Returns:
        Dict with id, accountHolderName, currency, type.

    Raises:
        RecipientError: on API error or missing required fields.
    """
    pid = resolve_profile_id(client, profile_id or client.credentials.profile_id)

    details: Dict[str, Any] = {"legalType": "PRIVATE"}
    currency_upper = currency.upper()

    if recipient_type == "aba":
        if not routing_number:
            raise RecipientError("USD (aba) recipients require a routing_number")
        details["accountNumber"] = account_number
        details["abartn"] = routing_number
        details["accountType"] = (account_type or "CHECKING").upper()
        if country or address or city or post_code:
            addr: Dict[str, str] = {}
            if country:
                addr["country"] = country.upper()
            if address:
                addr["firstLine"] = address
            if city:
                addr["city"] = city
            if post_code:
                addr["postCode"] = post_code
            if state:
                addr["state"] = state.upper()
            details["address"] = addr
    elif recipient_type == "sort_code":
        if not sort_code:
            raise RecipientError("GBP (sort_code) recipients require a sort_code")
        details["accountNumber"] = account_number
        details["sortCode"] = sort_code
    elif recipient_type == "iban":
        details["IBAN"] = account_number
    else:
        details["accountNumber"] = account_number

    payload = {
        "profile": int(pid),
        "accountHolderName": recipient_name,
        "currency": currency_upper,
        "type": recipient_type,
        "details": details,
    }

    resp = client.post("/v1/accounts", json_body=payload)

    if resp.status_code == 401:
        raise RecipientError("Authentication failed — check your WISE_API_TOKEN")
    if resp.status_code not in (200, 201):
        msg = f"Failed to create recipient: HTTP {resp.status_code}"
        try:
            body = resp.json()
            if isinstance(body, dict):
                err = body.get("errors") or body.get("message") or body
                msg += f" — {err}"
        except Exception:
            pass
        raise RecipientError(msg)

    data = resp.json()
    return {
        "id": data.get("id"),
        "accountHolderName": data.get("accountHolderName"),
        "currency": data.get("currency"),
        "type": data.get("type"),
        "active": data.get("active", True),
    }

"""Fetch balances from the Wise API."""

from typing import Any, Dict, List, Optional

from bankskills.core.bank.client import WiseClient
from bankskills.core.bank.profiles import resolve_profile_id


class BalanceError(Exception):
    """Raised when balance fetch fails."""


def fetch_balances(
    client: WiseClient,
    profile_id: Optional[str] = None,
    currency: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Fetch balances for the given profile.

    Args:
        client: Configured WiseClient.
        profile_id: Profile ID (resolved automatically if None).
        currency: Optional currency filter (e.g. "USD").

    Returns:
        List of balance dicts with at least currency, amount, reservedAmount.

    Raises:
        BalanceError: on API error.
    """
    pid = resolve_profile_id(client, profile_id or client.credentials.profile_id)

    params = {"types": "STANDARD"}
    resp = client.get(f"/v4/profiles/{pid}/balances", params=params)

    if resp.status_code == 401:
        raise BalanceError("Authentication failed — check your WISE_API_TOKEN")
    if resp.status_code == 404:
        raise BalanceError(f"Profile {pid} not found")
    if resp.status_code >= 500:
        raise BalanceError(f"Wise API server error: HTTP {resp.status_code}")
    if resp.status_code != 200:
        raise BalanceError(f"Unexpected API error: HTTP {resp.status_code}")

    raw_balances = resp.json()

    balances = []
    for b in raw_balances:
        entry = {
            "currency": b.get("currency"),
            "amount": b.get("amount", {}).get("value", 0),
            "reservedAmount": b.get("amount", {}).get("reserved", 0),
        }
        balances.append(entry)

    if currency:
        currency_upper = currency.upper()
        balances = [b for b in balances if b["currency"] == currency_upper]

    return balances

"""Balance statement retrieval from the Wise API."""

from typing import Any, Dict, List, Optional

from core.bank.client import WiseClient
from core.bank.profiles import resolve_profile_id


class StatementError(Exception):
    """Raised when statement fetch fails."""


def _resolve_balance_id(
    client: WiseClient,
    profile_id: str,
    currency: str,
) -> str:
    """Find the balance ID for a given currency."""
    resp = client.get(f"/v4/profiles/{profile_id}/balances", params={"types": "STANDARD"})
    if resp.status_code != 200:
        raise StatementError(f"Failed to fetch balances: HTTP {resp.status_code}")

    for b in resp.json():
        if (b.get("currency") or "").upper() == currency.upper():
            return str(b["id"])

    raise StatementError(f"No balance found for currency {currency}")


def get_balance_statement(
    client: WiseClient,
    currency: str,
    start_date: str,
    end_date: str,
    profile_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Fetch a balance statement (transaction history) for a currency.

    Returns all transactions — deposits, withdrawals, conversions,
    card transactions, and fees — for the given date range.

    Args:
        client: Configured WiseClient.
        currency: 3-letter currency code (e.g. "USD").
        start_date: Start of period, ISO-8601 (e.g. "2025-01-01T00:00:00Z").
        end_date: End of period, ISO-8601 (e.g. "2025-01-31T23:59:59Z").
        profile_id: Profile ID (resolved automatically if None).

    Returns:
        Dict with accountHolder, startDate, endDate, currency,
        openingBalance, closingBalance, and transactions list.

    Raises:
        StatementError: on API error or missing balance.
    """
    pid = resolve_profile_id(client, profile_id or client.credentials.profile_id)
    balance_id = _resolve_balance_id(client, pid, currency)

    params = {
        "intervalStart": start_date,
        "intervalEnd": end_date,
        "type": "COMPACT",
    }
    resp = client.get(
        f"/v1/profiles/{pid}/balance-statements/{balance_id}/statement.json",
        params=params,
    )

    if resp.status_code == 401:
        raise StatementError("Authentication failed — check your WISE_API_TOKEN")
    if resp.status_code == 404:
        raise StatementError(f"Statement not found for {currency} balance")
    if resp.status_code >= 500:
        raise StatementError(f"Wise API server error: HTTP {resp.status_code}")
    if resp.status_code != 200:
        raise StatementError(f"Unexpected API error: HTTP {resp.status_code}")

    data = resp.json()

    transactions = []
    for tx in data.get("transactions", []):
        transactions.append({
            "type": tx.get("type"),
            "date": tx.get("date"),
            "amount": tx.get("amount", {}).get("value"),
            "currency": tx.get("amount", {}).get("currency"),
            "runningBalance": tx.get("runningBalance", {}).get("value"),
            "referenceNumber": tx.get("referenceNumber"),
            "description": tx.get("details", {}).get("description"),
        })

    return {
        "currency": currency.upper(),
        "startDate": start_date,
        "endDate": end_date,
        "openingBalance": data.get("endOfStatementBalance", {}).get("value"),
        "transactions": transactions,
    }

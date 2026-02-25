"""Fetch supported currencies from the Wise API."""

from typing import Any, Dict, List

from bankskills.core.bank.client import WiseClient


class CurrencyError(Exception):
    """Raised when currency fetch fails."""


def fetch_currencies(client: WiseClient) -> List[Dict[str, Any]]:
    """Fetch the list of currencies Wise supports for transfers.

    Args:
        client: Configured WiseClient.

    Returns:
        List of currency dicts with code, name, and symbol fields.

    Raises:
        CurrencyError: on API error.
    """
    resp = client.get("/v1/currencies")

    if resp.status_code == 401:
        raise CurrencyError("Authentication failed — check your WISE_API_TOKEN")
    if resp.status_code >= 500:
        raise CurrencyError(f"Wise API server error: HTTP {resp.status_code}")
    if resp.status_code != 200:
        raise CurrencyError(f"Unexpected API error: HTTP {resp.status_code}")

    return resp.json()

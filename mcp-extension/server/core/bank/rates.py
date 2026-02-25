"""Fetch exchange rates from the Wise API."""

from typing import Any, Dict, List, Optional

from core.bank.client import WiseClient


class RateError(Exception):
    """Raised when rate fetch fails."""


def fetch_exchange_rate(
    client: WiseClient,
    source: str,
    target: str,
    time: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Fetch the current (or historical) mid-market exchange rate.

    Args:
        client: Configured WiseClient.
        source: Source currency code (e.g. "USD").
        target: Target currency code (e.g. "EUR").
        time: Optional ISO-8601 timestamp for a historical rate.

    Returns:
        List of rate dicts with rate, source, target, time.

    Raises:
        RateError: on API error.
    """
    params: Dict[str, str] = {"source": source.upper(), "target": target.upper()}
    if time:
        params["time"] = time

    resp = client.get("/v1/rates", params=params)

    if resp.status_code == 401:
        raise RateError("Authentication failed — check your WISE_API_TOKEN")
    if resp.status_code >= 500:
        raise RateError(f"Wise API server error: HTTP {resp.status_code}")
    if resp.status_code != 200:
        raise RateError(f"Unexpected API error: HTTP {resp.status_code}")

    return resp.json()

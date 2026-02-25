"""Quote creation via the Wise API."""

from typing import Any, Dict, Optional

from bankskills.core.bank.client import WiseClient
from bankskills.core.bank.profiles import resolve_profile_id


class QuoteError(Exception):
    """Raised when quote creation fails."""


def create_quote(
    client: WiseClient,
    source_currency: str,
    target_currency: str,
    amount: float,
    profile_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a quote to preview exchange rate, fees, and estimated delivery.

    Use this before send_money to see exactly what a transfer will cost
    without committing to it. The rate is locked for 30 minutes.

    Args:
        client: Configured WiseClient.
        source_currency: Source currency code (e.g. "USD").
        target_currency: Target currency code (e.g. "EUR").
        amount: Amount in source currency.
        profile_id: Profile ID (resolved automatically if None).

    Returns:
        Dict with id, rate, fee, sourceAmount, targetAmount,
        estimatedDelivery, and rateExpirationTime.

    Raises:
        QuoteError: on API error.
    """
    pid = resolve_profile_id(client, profile_id or client.credentials.profile_id)

    resp = client.post(
        f"/v3/profiles/{pid}/quotes",
        json_body={
            "sourceCurrency": source_currency.upper(),
            "targetCurrency": target_currency.upper(),
            "sourceAmount": amount,
            "targetAmount": None,
        },
    )

    if resp.status_code == 401:
        raise QuoteError("Authentication failed — check your WISE_API_TOKEN")
    if resp.status_code >= 500:
        raise QuoteError(f"Wise API server error: HTTP {resp.status_code}")
    if resp.status_code not in (200, 201):
        raise QuoteError(f"Unexpected API error: HTTP {resp.status_code}")

    data = resp.json()

    fee = None
    estimated_delivery = None
    payment_options = data.get("paymentOptions", [])
    for opt in payment_options:
        if not opt.get("disabled", True):
            fee = opt.get("fee", {}).get("total")
            estimated_delivery = opt.get("formattedEstimatedDelivery")
            break

    return {
        "id": data.get("id"),
        "rate": data.get("rate"),
        "fee": fee,
        "sourceCurrency": data.get("sourceCurrency"),
        "sourceAmount": data.get("sourceAmount"),
        "targetCurrency": data.get("targetCurrency"),
        "targetAmount": data.get("targetAmount"),
        "estimatedDelivery": estimated_delivery,
        "rateExpirationTime": data.get("rateExpirationTime"),
    }

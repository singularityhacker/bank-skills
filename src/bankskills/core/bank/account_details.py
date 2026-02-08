"""Fetch account/receive details from the Wise API."""

from typing import Any, Dict, List, Optional

from bankskills.core.bank.client import WiseClient
from bankskills.core.bank.profiles import resolve_profile_id


class AccountDetailsError(Exception):
    """Raised when account details fetch fails."""


def fetch_account_details(
    client: WiseClient,
    profile_id: Optional[str] = None,
    currency: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Fetch account/receive details for the given profile.

    Args:
        client: Configured WiseClient.
        profile_id: Profile ID (resolved automatically if None).
        currency: Optional currency filter (e.g. "USD").

    Returns:
        List of account detail dicts per currency with fields like
        accountHolder, accountNumber, routingNumber, iban, bankName, etc.

    Raises:
        AccountDetailsError: on API error.
    """
    pid = resolve_profile_id(client, profile_id or client.credentials.profile_id)

    resp = client.get(f"/v1/profiles/{pid}/account-details")

    if resp.status_code == 401:
        raise AccountDetailsError("Authentication failed — check your WISE_API_TOKEN")
    if resp.status_code == 404:
        raise AccountDetailsError(f"Profile {pid} not found")
    if resp.status_code >= 500:
        raise AccountDetailsError(f"Wise API server error: HTTP {resp.status_code}")
    if resp.status_code != 200:
        raise AccountDetailsError(f"Unexpected API error: HTTP {resp.status_code}")

    raw = resp.json()

    details = []
    for entry in raw:
        # Wise API may return currency as string or as {"code": "USD", "name": "..."}
        raw_currency = entry.get("currency")
        if isinstance(raw_currency, dict):
            currency_code = (raw_currency.get("code") or "").strip() or None
        else:
            currency_code = (raw_currency or "").strip() or None

        detail: Dict[str, Any] = {
            "currency": currency_code,
            "accountHolder": (entry.get("title") or "").strip(),
        }

        # Wise API uses receiveOptions[].details[] with type/body (not key/value)
        for option in entry.get("receiveOptions", []):
            for field in option.get("details", []):
                dtype = (field.get("type") or "").strip().upper()
                body = (field.get("body") or "").strip()
                if not body:
                    continue
                if dtype == "ACCOUNT_HOLDER":
                    detail["accountHolder"] = body or detail.get("accountHolder", "")
                elif dtype == "ACCOUNT_NUMBER":
                    detail["accountNumber"] = body
                elif dtype in ("ROUTING_NUMBER", "SORT_CODE", "BANK_CODE"):
                    detail["routingNumber"] = body
                elif dtype == "IBAN":
                    detail["iban"] = body
                elif dtype in ("SWIFT_CODE", "SWIFT / BIC", "BIC"):
                    detail["swiftBic"] = body
                elif dtype in ("BANK_NAME", "BANK NAME"):
                    detail["bankName"] = body
                elif dtype == "ADDRESS":
                    detail["address"] = body

        details.append(detail)

    if currency:
        currency_upper = currency.upper()
        details = [d for d in details if (d.get("currency") or "").upper() == currency_upper]

    return details

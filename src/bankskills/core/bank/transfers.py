"""Transfer status, listing, and delivery estimate operations."""

from typing import Any, Dict, List, Optional

from bankskills.core.bank.client import WiseClient
from bankskills.core.bank.profiles import resolve_profile_id


class TransferStatusError(Exception):
    """Raised when transfer status fetch fails."""


class DeliveryEstimateError(Exception):
    """Raised when delivery estimate fetch fails."""


def get_transfer_status(
    client: WiseClient,
    transfer_id: int,
) -> Dict[str, Any]:
    """Get the current status and details of a transfer.

    Args:
        client: Configured WiseClient.
        transfer_id: The numeric transfer ID returned by send_money.

    Returns:
        Transfer dict with id, status, sourceCurrency, sourceValue,
        targetCurrency, targetValue, rate, created, hasActiveIssues.

    Raises:
        TransferStatusError: on API error.
    """
    resp = client.get(f"/v1/transfers/{transfer_id}")

    if resp.status_code == 401:
        raise TransferStatusError("Authentication failed — check your WISE_API_TOKEN")
    if resp.status_code == 404:
        raise TransferStatusError(f"Transfer {transfer_id} not found")
    if resp.status_code >= 500:
        raise TransferStatusError(f"Wise API server error: HTTP {resp.status_code}")
    if resp.status_code != 200:
        raise TransferStatusError(f"Unexpected API error: HTTP {resp.status_code}")

    data = resp.json()
    return {
        "id": data.get("id"),
        "status": data.get("status"),
        "sourceCurrency": data.get("sourceCurrency"),
        "sourceValue": data.get("sourceValue"),
        "targetCurrency": data.get("targetCurrency"),
        "targetValue": data.get("targetValue"),
        "rate": data.get("rate"),
        "created": data.get("created"),
        "hasActiveIssues": data.get("hasActiveIssues", False),
    }


def list_transfers(
    client: WiseClient,
    profile_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 10,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """List transfers for the profile.

    Args:
        client: Configured WiseClient.
        profile_id: Profile ID (resolved automatically if None).
        status: Optional status filter (e.g. "funds_converted").
        limit: Max results to return (default 10).
        offset: Pagination offset.

    Returns:
        List of transfer summary dicts.

    Raises:
        TransferStatusError: on API error.
    """
    pid = resolve_profile_id(client, profile_id or client.credentials.profile_id)

    params: Dict[str, Any] = {
        "profile": pid,
        "limit": limit,
        "offset": offset,
    }
    if status:
        params["status"] = status

    resp = client.get("/v1/transfers", params=params)

    if resp.status_code == 401:
        raise TransferStatusError("Authentication failed — check your WISE_API_TOKEN")
    if resp.status_code >= 500:
        raise TransferStatusError(f"Wise API server error: HTTP {resp.status_code}")
    if resp.status_code != 200:
        raise TransferStatusError(f"Unexpected API error: HTTP {resp.status_code}")

    raw = resp.json()
    transfers = []
    for t in raw:
        transfers.append({
            "id": t.get("id"),
            "status": t.get("status"),
            "sourceCurrency": t.get("sourceCurrency"),
            "sourceValue": t.get("sourceValue"),
            "targetCurrency": t.get("targetCurrency"),
            "targetValue": t.get("targetValue"),
            "rate": t.get("rate"),
            "created": t.get("created"),
        })
    return transfers


def get_delivery_estimate(
    client: WiseClient,
    transfer_id: int,
) -> Dict[str, Any]:
    """Get the estimated delivery time for a transfer.

    Args:
        client: Configured WiseClient.
        transfer_id: The numeric transfer ID.

    Returns:
        Dict with estimatedDeliveryDate.

    Raises:
        DeliveryEstimateError: on API error.
    """
    resp = client.get(f"/v1/delivery-estimates/{transfer_id}")

    if resp.status_code == 401:
        raise DeliveryEstimateError("Authentication failed — check your WISE_API_TOKEN")
    if resp.status_code == 404:
        raise DeliveryEstimateError(f"Transfer {transfer_id} not found")
    if resp.status_code >= 500:
        raise DeliveryEstimateError(f"Wise API server error: HTTP {resp.status_code}")
    if resp.status_code != 200:
        raise DeliveryEstimateError(f"Unexpected API error: HTTP {resp.status_code}")

    return resp.json()

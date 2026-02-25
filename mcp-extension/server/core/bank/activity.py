"""Activity feed from the Wise API."""

from typing import Any, Dict, List, Optional

from core.bank.client import WiseClient
from core.bank.profiles import resolve_profile_id


class ActivityError(Exception):
    """Raised when activity fetch fails."""


def get_activity(
    client: WiseClient,
    profile_id: Optional[str] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Fetch the activity feed for a profile.

    Returns a unified list of all account actions — transfers,
    conversions, card transactions, deposits, etc.

    Args:
        client: Configured WiseClient.
        profile_id: Profile ID (resolved automatically if None).
        since: Optional ISO-8601 start timestamp (e.g. "2025-01-01T00:00:00Z").
        until: Optional ISO-8601 end timestamp.

    Returns:
        List of activity dicts with type, title, description, primaryAmount,
        status, and createdOn.

    Raises:
        ActivityError: on API error.
    """
    pid = resolve_profile_id(client, profile_id or client.credentials.profile_id)

    params: Dict[str, str] = {}
    if since:
        params["since"] = since
    if until:
        params["until"] = until

    resp = client.get(f"/v1/profiles/{pid}/activities", params=params)

    if resp.status_code == 401:
        raise ActivityError("Authentication failed — check your WISE_API_TOKEN")
    if resp.status_code == 404:
        raise ActivityError(f"Profile {pid} not found")
    if resp.status_code >= 500:
        raise ActivityError(f"Wise API server error: HTTP {resp.status_code}")
    if resp.status_code != 200:
        raise ActivityError(f"Unexpected API error: HTTP {resp.status_code}")

    raw = resp.json()
    activities_list = raw.get("activities", raw) if isinstance(raw, dict) else raw

    activities = []
    for a in activities_list:
        activities.append({
            "type": a.get("type"),
            "title": a.get("title"),
            "description": a.get("description"),
            "primaryAmount": a.get("primaryAmount"),
            "status": a.get("status"),
            "createdOn": a.get("createdOn"),
        })
    return activities

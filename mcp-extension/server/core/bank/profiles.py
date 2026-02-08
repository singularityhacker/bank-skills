"""Profile resolution for Wise API."""

from typing import Optional

from core.bank.client import WiseClient


class ProfileError(Exception):
    """Raised when profile cannot be resolved."""


def resolve_profile_id(client: WiseClient, profile_id: Optional[str] = None) -> str:
    """Resolve the Wise profile ID.

    If *profile_id* is provided, return it directly.
    Otherwise, fetch profiles from the API and return the first one.

    Raises:
        ProfileError: if no profiles are available.
    """
    if profile_id:
        return profile_id

    resp = client.get("/v2/profiles")
    if resp.status_code != 200:
        msg = f"Failed to fetch profiles: HTTP {resp.status_code}"
        if resp.status_code == 401:
            msg += ". Check that WISE_API_TOKEN is valid."
        raise ProfileError(msg)

    profiles = resp.json()
    if not profiles:
        raise ProfileError("No profiles found for this API token")

    return str(profiles[0]["id"])

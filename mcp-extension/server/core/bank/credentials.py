"""Credential handling for the bank skill.

Reads Wise API credentials from environment variables.
Never logs or includes the API token in error messages.
"""

import os
from dataclasses import dataclass
from typing import Optional


class MissingCredentialError(Exception):
    """Raised when a required credential is not set."""


@dataclass
class WiseCredentials:
    api_token: str
    profile_id: Optional[str] = None

    def __repr__(self) -> str:
        return "WiseCredentials(api_token='***', profile_id={!r})".format(self.profile_id)

    def __str__(self) -> str:
        return self.__repr__()


def load_credentials() -> WiseCredentials:
    """Load Wise credentials from environment variables.

    Reads:
        WISE_API_TOKEN (required)
        WISE_PROFILE_ID (optional)

    Returns:
        WiseCredentials instance.

    Raises:
        MissingCredentialError: if WISE_API_TOKEN is missing or empty.
    """
    token = os.environ.get("WISE_API_TOKEN", "").strip()
    if not token:
        raise MissingCredentialError(
            "WISE_API_TOKEN environment variable is not set"
        )

    profile_id = os.environ.get("WISE_PROFILE_ID", "").strip() or None

    return WiseCredentials(api_token=token, profile_id=profile_id)

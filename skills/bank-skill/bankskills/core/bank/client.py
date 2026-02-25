"""Wise API client."""

from typing import Any, Dict, Optional

import httpx

from bankskills.core.bank.credentials import WiseCredentials, load_credentials


class WiseClient:
    """HTTP client for the Wise API."""

    def __init__(
        self,
        credentials: Optional[WiseCredentials] = None,
        base_url: Optional[str] = None,
    ):
        self.credentials = credentials or load_credentials()
        self.base_url = base_url or "https://api.wise.com"

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.credentials.api_token}",
            "Content-Type": "application/json",
        }

    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> httpx.Response:
        url = f"{self.base_url}{path}"
        return httpx.get(url, headers=self._headers(), params=params)

    def post(self, path: str, json_body: Optional[Dict[str, Any]] = None, extra_headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        url = f"{self.base_url}{path}"
        headers = self._headers()
        if extra_headers:
            headers.update(extra_headers)
        return httpx.post(url, headers=headers, json=json_body)

    def delete(self, path: str) -> httpx.Response:
        url = f"{self.base_url}{path}"
        return httpx.delete(url, headers=self._headers())

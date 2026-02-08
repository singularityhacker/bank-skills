"""Tests for Story 05 — Read credentials from environment."""

import os

import pytest

from bankskills.core.bank.credentials import (
    MissingCredentialError,
    WiseCredentials,
    load_credentials,
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Remove Wise env vars before each test."""
    monkeypatch.delenv("WISE_API_TOKEN", raising=False)
    monkeypatch.delenv("WISE_PROFILE_ID", raising=False)


def test_load_credentials_reads_token(monkeypatch):
    monkeypatch.setenv("WISE_API_TOKEN", "test-token-123")
    creds = load_credentials()
    assert creds.api_token == "test-token-123"


def test_load_credentials_reads_profile_id(monkeypatch):
    monkeypatch.setenv("WISE_API_TOKEN", "test-token-123")
    monkeypatch.setenv("WISE_PROFILE_ID", "99999")
    creds = load_credentials()
    assert creds.profile_id == "99999"


def test_load_credentials_profile_id_optional(monkeypatch):
    monkeypatch.setenv("WISE_API_TOKEN", "test-token-123")
    creds = load_credentials()
    assert creds.profile_id is None


def test_missing_token_raises_error():
    with pytest.raises(MissingCredentialError, match="WISE_API_TOKEN"):
        load_credentials()


def test_empty_token_raises_error(monkeypatch):
    monkeypatch.setenv("WISE_API_TOKEN", "")
    with pytest.raises(MissingCredentialError, match="WISE_API_TOKEN"):
        load_credentials()


def test_whitespace_token_raises_error(monkeypatch):
    monkeypatch.setenv("WISE_API_TOKEN", "   ")
    with pytest.raises(MissingCredentialError, match="WISE_API_TOKEN"):
        load_credentials()


def test_token_never_in_error_message():
    """Error message must not contain the actual token value."""
    try:
        load_credentials()
    except MissingCredentialError as e:
        msg = str(e)
        # The error should mention the variable name, not a token value
        assert "WISE_API_TOKEN" in msg


def test_credentials_repr_redacts_token():
    creds = WiseCredentials(api_token="super-secret")
    text = repr(creds)
    assert "super-secret" not in text
    assert "***" in text


def test_credentials_str_redacts_token():
    creds = WiseCredentials(api_token="super-secret")
    text = str(creds)
    assert "super-secret" not in text
    assert "***" in text

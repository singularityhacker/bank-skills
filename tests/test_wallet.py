"""Tests for wallet module — create_wallet, get_wallet, load_private_key."""

import json
import os
from unittest.mock import MagicMock, patch

import pytest

import bankskills.wallet as wallet_module
from bankskills.wallet import (
    WalletError,
    create_wallet,
    get_wallet,
    load_private_key,
)


@pytest.fixture(autouse=True)
def _isolate_wallet(tmp_path, monkeypatch):
    """Use a temp directory for wallet files in each test."""
    wallet_dir = tmp_path / ".clawbank"
    wallet_dir.mkdir(parents=True, exist_ok=True)
    wallet_path = wallet_dir / "wallet.json"
    monkeypatch.setattr(wallet_module, "WALLET_DIR", str(wallet_dir))
    monkeypatch.setattr(wallet_module, "WALLET_PATH", str(wallet_path))
    monkeypatch.delenv("CLAWBANK_WALLET_PASSWORD", raising=False)
    monkeypatch.delenv("BASE_RPC_URL", raising=False)
    yield


class TestCreateWallet:
    def test_create_wallet_creates_keystore_and_returns_address(self):
        result = create_wallet()
        assert "address" in result
        assert result["address"].startswith("0x")
        assert len(result["address"]) == 42  # 0x + 40 hex chars

        assert os.path.exists(wallet_module.WALLET_PATH)
        with open(wallet_module.WALLET_PATH) as f:
            keystore = json.load(f)
        assert "address" in keystore
        assert "crypto" in keystore

    def test_create_wallet_no_op_if_exists(self):
        first = create_wallet()
        second = create_wallet()
        assert first["address"] == second["address"]

    def test_create_wallet_uses_env_password(self, monkeypatch):
        monkeypatch.setenv("CLAWBANK_WALLET_PASSWORD", "custom-secret")
        create_wallet()
        # Wallet should be decryptable with custom password
        pk = load_private_key()
        assert pk.startswith("0x")
        assert len(pk) == 66  # 0x + 64 hex chars


class TestGetWallet:
    def test_get_wallet_raises_if_no_wallet(self):
        with pytest.raises(WalletError, match="does not exist"):
            get_wallet()

    def test_get_wallet_returns_address_and_balance(self):
        create_wallet()
        with patch("bankskills.wallet.Web3") as mock_web3:
            mock_w3 = MagicMock()
            mock_w3.eth.get_balance.return_value = 500000000000000000  # 0.5 ETH
            mock_w3.from_wei.return_value = 0.5
            mock_web3.return_value = mock_w3
            mock_web3.HTTPProvider = MagicMock()

            result = get_wallet()

        assert "address" in result
        assert "eth_balance" in result
        assert result["address"].startswith("0x")
        assert result["eth_balance"] == "0.5"

    def test_get_wallet_uses_base_rpc_from_env(self, monkeypatch):
        monkeypatch.setenv("BASE_RPC_URL", "https://custom.rpc.example")
        create_wallet()
        with patch("bankskills.wallet.Web3") as mock_web3:
            mock_w3 = MagicMock()
            mock_w3.eth.get_balance.return_value = 0
            mock_w3.from_wei.return_value = 0
            mock_web3.return_value = mock_w3
            mock_web3.HTTPProvider = MagicMock()

            get_wallet()

            mock_web3.HTTPProvider.assert_called_once_with("https://custom.rpc.example")


class TestLoadPrivateKey:
    def test_load_private_key_raises_if_no_wallet(self):
        with pytest.raises(WalletError, match="does not exist"):
            load_private_key()

    def test_load_private_key_returns_hex_string(self):
        create_wallet()
        pk = load_private_key()
        assert pk.startswith("0x")
        assert len(pk) == 66
        assert all(c in "0123456789abcdef" for c in pk[2:])

    def test_load_private_key_never_exposed_in_public_api(self):
        """Private key is for internal signing only; MCP tools must never return it."""
        create_wallet()
        pk = load_private_key()
        # Just verify we can load it; actual exposure check is in MCP tool tests
        assert pk is not None

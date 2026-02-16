"""Wallet module for ClawBank Sweeper.

Creates and manages an encrypted keystore for on-chain token buyback on Base.
"""

import json
import os
import secrets
from typing import Dict, Any

from web3 import Web3

WALLET_DIR = os.path.expanduser("~/.clawbank")
WALLET_PATH = os.path.join(WALLET_DIR, "wallet.json")
WALLET_PASSWORD_ENV = "CLAWBANK_WALLET_PASSWORD"
BASE_RPC_URL_ENV = "BASE_RPC_URL"
DEFAULT_PASSWORD = "clawbank-default"
DEFAULT_RPC = "https://mainnet.base.org"


class WalletError(Exception):
    """Raised when wallet operations fail."""


def checksum(addr: str) -> str:
    """Normalize address to EIP-55 checksum for web3 compatibility."""
    return Web3.to_checksum_address(addr)


def create_wallet() -> Dict[str, Any]:
    """Create a new Ethereum wallet on first run.

    Saves encrypted keystore to ~/.clawbank/wallet.json.
    No-ops if wallet already exists.

    Returns:
        Dict with "address" key containing the wallet address (0x...).
    """
    if os.path.exists(WALLET_PATH):
        with open(WALLET_PATH) as f:
            keystore = json.load(f)
        return {"address": checksum("0x" + keystore["address"])}

    from eth_account import Account

    os.makedirs(WALLET_DIR, exist_ok=True)
    private_key = "0x" + secrets.token_hex(32)
    acct = Account.from_key(private_key)
    password = os.environ.get(WALLET_PASSWORD_ENV, DEFAULT_PASSWORD)
    keystore = Account.encrypt(private_key, password)

    with open(WALLET_PATH, "w") as f:
        json.dump(keystore, f, indent=2)

    return {"address": checksum("0x" + keystore["address"])}


def get_wallet() -> Dict[str, Any]:
    """Return the wallet address and ETH balance on Base.

    Returns:
        Dict with "address" and "eth_balance" keys.

    Raises:
        WalletError: If wallet does not exist.
    """
    if not os.path.exists(WALLET_PATH):
        raise WalletError("Wallet does not exist. Call create_wallet first.")

    with open(WALLET_PATH) as f:
        keystore = json.load(f)
    address = checksum("0x" + keystore["address"])

    rpc_url = os.environ.get(BASE_RPC_URL_ENV, DEFAULT_RPC)
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    balance_wei = w3.eth.get_balance(address)
    balance_eth = w3.from_wei(balance_wei, "ether")
    eth_balance_str = str(balance_eth)

    return {"address": address, "eth_balance": eth_balance_str}


def export_private_key() -> Dict[str, Any]:
    """Export the wallet private key for manual recovery or import into MetaMask.

    Returns:
        Dict with private_key, address, and security warning.
    """
    private_key = load_private_key()
    pk_hex = private_key if isinstance(private_key, str) and private_key.startswith("0x") else "0x" + private_key
    from eth_account import Account
    acct = Account.from_key(pk_hex)
    address = checksum(acct.address)
    return {
        "private_key": pk_hex,
        "address": address,
        "warning": "Do not share this key. Anyone with this key has full control of the wallet.",
    }


def load_private_key() -> str:
    """Decrypt keystore and return private key for signing.

    Internal use only. Never expose to MCP tool responses.

    Returns:
        Private key as hex string (0x...).

    Raises:
        WalletError: If wallet does not exist or decryption fails.
    """
    if not os.path.exists(WALLET_PATH):
        raise WalletError("Wallet does not exist. Call create_wallet first.")

    from eth_account import Account

    with open(WALLET_PATH) as f:
        keystore = json.load(f)
    password = os.environ.get(WALLET_PASSWORD_ENV, DEFAULT_PASSWORD)
    try:
        private_key = Account.decrypt(keystore, password)
        return private_key.hex() if isinstance(private_key, bytes) else private_key
    except Exception as e:
        raise WalletError(f"Failed to decrypt wallet: {e}") from e

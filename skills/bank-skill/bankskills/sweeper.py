"""Sweeper module for ClawBank — on-chain token buyback on Base."""

import os
import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from bankskills.wallet import checksum

SWEEP_CONFIG_DIR = os.path.expanduser("~/.clawbank")
SWEEP_CONFIG_PATH = os.path.join(SWEEP_CONFIG_DIR, "sweep.config")
BASE_RPC_URL_ENV = "BASE_RPC_URL"
DEFAULT_RPC = "https://mainnet.base.org"

# Uniswap Universal Router on Base (V4 router)
UNIVERSAL_ROUTER_ADDRESS = "0x6fF5693b99212Da76ad316178A184AB56D299b43"
WETH_ADDRESS = "0x4200000000000000000000000000000000000006"
GAS_RESERVE_ETH = 0.001
SLIPPAGE_BPS = 100  # 1%
# ClawBank V4 pool parameters (from successful transactions)
# NOTE: These are ClawBank-specific. For other tokens, pool params may differ.
# CLAWBANK_HOOKS is the hook contract for the ClawBank/WETH V4 pool on Base.
CLAWBANK_POOL_FEE = 0x800000  # Dynamic fee
CLAWBANK_TICK_SPACING = 200
CLAWBANK_HOOKS = "0xb429d62f8f3bFFb98CdB9569533eA23bF0Ba28CC"
# Note: hookData is empty (b""), not "unix..." - this is critical!
# Universal Router commands
WRAP_ETH = 0x0B
V4_SWAP = 0x10
# V4 actions (inside V4_SWAP)
SWAP_EXACT_IN = 0x07
SETTLE = 0x0B
TAKE = 0x0E
# Recipient codes
ADDRESS_THIS = "0x0000000000000000000000000000000000000002"  # Router itself

UNIVERSAL_ROUTER_ABI = [
    {
        "inputs": [
            {"name": "commands", "type": "bytes"},
            {"name": "inputs", "type": "bytes[]"},
            {"name": "deadline", "type": "uint256"},
        ],
        "name": "execute",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function",
    }
]

ERC20_ABI = [
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"type": "uint256"}],
        "type": "function",
    },
    {
        "inputs": [],
        "name": "symbol",
        "outputs": [{"type": "string"}],
        "type": "function",
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"type": "uint8"}],
        "type": "function",
    },
    {
        "inputs": [
            {"name": "to", "type": "address"},
            {"name": "amount", "type": "uint256"},
        ],
        "name": "transfer",
        "outputs": [{"type": "bool"}],
        "type": "function",
    },
]


class SweeperError(Exception):
    """Raised when sweeper operations fail."""


def _validate_address(addr: str) -> bool:
    """Validate Ethereum address format (0x + 40 hex chars)."""
    return bool(re.match(r"^0x[a-fA-F0-9]{40}$", addr or ""))


def _is_native_eth(addr: str) -> bool:
    """Return True if address represents native ETH (zero address, ETH, or native)."""
    if not addr:
        return False
    a = (addr or "").strip().lower()
    if a in ("eth", "native"):
        return True
    a = a.replace("0x", "").zfill(40)
    return len(a) == 40 and a == "0" * 40


def set_target_token(token_address: str) -> Dict[str, Any]:
    """Set the target token contract address in sweep.config.

    Validates address format and calls symbol() to confirm it's a valid ERC-20.

    Returns:
        Dict with status, token_address, token_symbol.
    """
    if not _validate_address(token_address):
        raise SweeperError(f"Invalid token address: {token_address}")

    addr = token_address if token_address.startswith("0x") else "0x" + token_address
    addr = checksum(addr)

    rpc_url = os.environ.get(BASE_RPC_URL_ENV, DEFAULT_RPC)
    from web3 import Web3

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    token_contract = w3.eth.contract(address=addr, abi=ERC20_ABI)
    try:
        symbol = token_contract.functions.symbol().call()
    except Exception as e:
        raise SweeperError(f"Invalid token at {addr}: {e}") from e

    os.makedirs(SWEEP_CONFIG_DIR, exist_ok=True)
    content = f"target={addr}\nnetwork=base\n"
    with open(SWEEP_CONFIG_PATH, "w") as f:
        f.write(content)

    return {"status": "ok", "token_address": addr, "token_symbol": symbol}


def get_sweep_config() -> Dict[str, Any]:
    """Return the current sweep configuration and recent log entries.

    Returns:
        Dict with target_token, token_symbol, network, recent_sweeps.
    """
    if not os.path.exists(SWEEP_CONFIG_PATH):
        return {
            "target_token": None,
            "token_symbol": None,
            "network": "base",
            "recent_sweeps": [],
        }

    with open(SWEEP_CONFIG_PATH) as f:
        content = f.read()

    target = None
    network = "base"
    recent_sweeps: List[Dict[str, str]] = []

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Parse sweep log lines: 2026-02-14 12:03:00 | spent: 0.25 ETH | bought: 4231.7 CLAW | tx: 0xabc...
        m = re.match(
            r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \| spent: ([^|]+) \| bought: ([^|]+) \| tx: (0x[a-fA-F0-9]+)",
            line,
        )
        if m:
            recent_sweeps.append(
                {
                    "timestamp": m.group(1),
                    "spent": m.group(2).strip(),
                    "bought": m.group(3).strip(),
                    "tx_hash": m.group(4),
                }
            )
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip()
            if k == "target":
                target = v
            elif k == "network":
                network = v

    token_symbol = None
    if target:
        target = checksum(target)
        try:
            rpc_url = os.environ.get(BASE_RPC_URL_ENV, DEFAULT_RPC)
            from web3 import Web3

            w3 = Web3(Web3.HTTPProvider(rpc_url))
            token_contract = w3.eth.contract(
                address=target, abi=ERC20_ABI
            )
            token_symbol = token_contract.functions.symbol().call()
        except Exception:
            pass

    return {
        "target_token": target,
        "token_symbol": token_symbol,
        "network": network,
        "recent_sweeps": recent_sweeps[-10:],  # Last 10
    }


def get_token_balance(token_address: str) -> Dict[str, Any]:
    """Return ERC-20 token balance for the ClawBank wallet.

    Args:
        token_address: ERC-20 contract address on Base.

    Returns:
        Dict with token_address, symbol, balance (human-readable), raw_balance.
    """
    from bankskills.wallet import get_wallet

    if not _validate_address(token_address):
        raise SweeperError(f"Invalid token address: {token_address}")

    addr = checksum(
        token_address if token_address.startswith("0x") else "0x" + token_address
    )
    wallet_info = get_wallet()
    address = wallet_info["address"]

    rpc_url = os.environ.get(BASE_RPC_URL_ENV, DEFAULT_RPC)
    from web3 import Web3

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    token = w3.eth.contract(address=addr, abi=ERC20_ABI)

    raw_balance = token.functions.balanceOf(address).call()
    decimals = token.functions.decimals().call()
    symbol = token.functions.symbol().call()
    balance = raw_balance / (10**decimals)

    balance_str = f"{balance:.{min(decimals, 18)}f}".rstrip("0").rstrip(".") or "0"

    return {
        "token_address": addr,
        "symbol": symbol,
        "balance": balance_str,
        "raw_balance": str(raw_balance),
    }


def _buy_token_v4_clawbank(amount_eth: float, target: str, address: str, w3, account, token_out, decimals: int, symbol: str, balance_before: int) -> Dict[str, Any]:
    """V4 swap specifically for ClawBank with its hook parameters.
    
    WORKING CODE - DO NOT MODIFY - Tested: https://basescan.org/tx/d0fa2d73e6fb88feb21fb584fc140f67f70cc215b12330a84a8ea1cd7cc77128
    
    This function is called as fallback when V3 fails for ClawBank.
    """
    from web3 import Web3
    from uniswap_universal_router_decoder import RouterCodec, FunctionRecipient
    
    codec = RouterCodec(w3=w3)
    amount_wei = w3.to_wei(amount_eth, "ether")

    # Build V4 pool key for ClawBank/WETH pool
    pool_key = codec.encode.v4_pool_key(
        Web3.to_checksum_address(target),  # ClawBank (lower address)
        Web3.to_checksum_address(WETH_ADDRESS),  # WETH
        CLAWBANK_POOL_FEE,
        CLAWBANK_TICK_SPACING,
        Web3.to_checksum_address(CLAWBANK_HOOKS),
    )

    # Build transaction using library (handles gas properly)
    trx_params = (
        codec.encode.chain()
        .wrap_eth(FunctionRecipient.ROUTER, amount_wei)
        .v4_swap()
            .swap_exact_in_single(
                pool_key=pool_key,
                zero_for_one=False,  # WETH -> ClawBank
                amount_in=amount_wei,
                amount_out_min=0,  # TODO: Use Quoter for slippage protection
                hook_data=b"",  # Empty hookData
            )
            .settle(Web3.to_checksum_address(WETH_ADDRESS), 0, False)
            .take_all(Web3.to_checksum_address(target), 0)
            .build_v4_swap()
        .build_transaction(
            address,
            value=amount_wei,
            ur_address=UNIVERSAL_ROUTER_ADDRESS
        )
    )

    # Sign and send
    signed = account.sign_transaction(trx_params)
    tx_hash_bytes = w3.eth.send_raw_transaction(signed.raw_transaction)
    tx_hash = tx_hash_bytes.hex()

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt["status"] != 1:
        raise SweeperError(f"Transaction failed: {tx_hash}")

    balance_after = token_out.functions.balanceOf(address).call()
    amount_out = balance_after - balance_before
    amount_out_human = amount_out / (10**decimals)

    # Append to sweep log
    os.makedirs(SWEEP_CONFIG_DIR, exist_ok=True)
    log_line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | spent: {amount_eth} ETH | bought: {amount_out_human} {symbol} | tx: {tx_hash}\n"
    with open(SWEEP_CONFIG_PATH, "a") as f:
        f.write(log_line)

    return {
        "tx_hash": tx_hash,
        "amount_in": f"{amount_eth} ETH",
        "amount_out": f"{amount_out_human} {symbol}",
        "status": "confirmed",
    }


def _try_v3_swap(amount_eth: float, target: str, address: str, w3, account, token_out, decimals: int, symbol: str, balance_before: int) -> Optional[Dict[str, Any]]:
    """Try V3 swap with common fee tiers (works for most tokens).
    
    Returns swap result if successful, None if no V3 pool found.
    """
    from eth_abi import encode as eth_abi_encode
    from web3 import Web3
    
    amount_wei = w3.to_wei(amount_eth, "ether")
    
    # V3 router address on Base
    V3_ROUTER = "0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD"
    
    # Try common V3 fee tiers in order of likelihood
    fee_tiers = [500, 3000, 10000]  # 0.05%, 0.3%, 1%
    
    weth_addr = Web3.to_checksum_address(WETH_ADDRESS)
    target_addr = Web3.to_checksum_address(target)
    
    for fee in fee_tiers:
        try:
            # Build V3 path: WETH + fee + target
            v3_path = weth_addr.lower().replace('0x', '')
            v3_path += format(fee, '06x')  # fee as 3 bytes
            v3_path += target_addr.lower().replace('0x', '')
            v3_path = bytes.fromhex(v3_path)
            
            # Commands: WRAP_ETH + V3_SWAP_EXACT_IN
            commands = bytes([WRAP_ETH, 0x00])  # 0x00 = V3_SWAP_EXACT_IN
            
            # Input 1: WRAP_ETH(recipient=ADDRESS_THIS, amountMin=amount_wei)
            wrap_input = eth_abi_encode(
                ["address", "uint256"],
                [Web3.to_checksum_address(ADDRESS_THIS), amount_wei]
            )
            
            # Input 2: V3_SWAP_EXACT_IN(recipient, amountIn, amountOutMin, path, payerIsUser)
            swap_input = eth_abi_encode(
                ["address", "uint256", "uint256", "bytes", "bool"],
                [
                    Web3.to_checksum_address(address),  # recipient
                    amount_wei,  # amountIn
                    0,  # amountOutMin
                    v3_path,  # path
                    False  # payerIsUser = False (router pays)
                ]
            )
            
            # Build execute() call
            deadline = int(time.time()) + 300
            calldata = eth_abi_encode(
                ["bytes", "bytes[]", "uint256"],
                [commands, [wrap_input, swap_input], deadline]
            )
            calldata = bytes.fromhex("3593564c") + calldata
            
            # Build transaction
            tx = {
                "from": address,
                "to": Web3.to_checksum_address(V3_ROUTER),
                "value": amount_wei,
                "data": calldata,
                "gas": 300000,
                "chainId": 8453,
                "nonce": w3.eth.get_transaction_count(address),
                "gasPrice": w3.eth.gas_price,
            }
            
            # Check if pool exists with gas estimation
            gas_estimate = w3.eth.estimate_gas(tx)
            
            # Pool exists! Execute the swap
            signed = account.sign_transaction(tx)
            tx_hash_bytes = w3.eth.send_raw_transaction(signed.raw_transaction)
            tx_hash = tx_hash_bytes.hex()
            
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            if receipt["status"] != 1:
                # Swap failed, try next fee tier
                continue
            
            balance_after = token_out.functions.balanceOf(address).call()
            amount_out = balance_after - balance_before
            amount_out_human = amount_out / (10**decimals)
            
            # Append to sweep log
            os.makedirs(SWEEP_CONFIG_DIR, exist_ok=True)
            log_line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | spent: {amount_eth} ETH | bought: {amount_out_human} {symbol} | tx: {tx_hash}\n"
            with open(SWEEP_CONFIG_PATH, "a") as f:
                f.write(log_line)
            
            return {
                "tx_hash": tx_hash,
                "amount_in": f"{amount_eth} ETH",
                "amount_out": f"{amount_out_human} {symbol}",
                "status": "confirmed",
            }
            
        except Exception:
            # This fee tier didn't work, try next
            continue
    
    # No V3 pool found with any fee tier
    return None


def buy_token(amount_eth: float) -> Dict[str, Any]:
    """Execute a token swap on Base: ETH → target token.
    
    Supports any token with V3 or V4 liquidity on Base:
    - Tries V3 first (works for most tokens: USDC, DAI, WBTC, etc.)
    - Falls back to V4 for ClawBank with its specific hook parameters
    
    Tested:
    - V3: https://basescan.org/tx/... (USDC worked first try)
    - V4: https://basescan.org/tx/d0fa2d73e6fb88feb21fb584fc140f67f70cc215b12330a84a8ea1cd7cc77128 (ClawBank)

    Returns:
        Dict with tx_hash, amount_in, amount_out, status.
    """
    from bankskills.wallet import get_wallet, load_private_key
    from web3 import Web3
    from eth_account import Account

    config = get_sweep_config()
    target = config.get("target_token")
    if not target:
        raise SweeperError("No target token set. Call set_target_token first.")

    target = checksum(target)
    wallet_info = get_wallet()
    address = wallet_info["address"]
    balance_eth = float(wallet_info["eth_balance"])

    if amount_eth <= 0:
        raise SweeperError("Amount must be greater than zero.")

    if amount_eth > balance_eth - GAS_RESERVE_ETH:
        raise SweeperError(
            f"Insufficient balance. Have {balance_eth} ETH, need {amount_eth} + {GAS_RESERVE_ETH} for gas."
        )

    rpc_url = os.environ.get(BASE_RPC_URL_ENV, DEFAULT_RPC)
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    private_key = load_private_key()
    account = Account.from_key(private_key)

    # Get token info
    token_out = w3.eth.contract(
        address=Web3.to_checksum_address(target), abi=ERC20_ABI
    )
    decimals = token_out.functions.decimals().call()
    symbol = token_out.functions.symbol().call()
    balance_before = token_out.functions.balanceOf(address).call()

    # Try V3 first (works for most tokens)
    v3_result = _try_v3_swap(amount_eth, target, address, w3, account, token_out, decimals, symbol, balance_before)
    if v3_result:
        return v3_result
    
    # V3 failed - if target is ClawBank, try V4 with its specific hook params
    CLAWBANK_ADDRESS = "0x16332535E2c27da578bC2e82bEb09Ce9d3C8EB07"
    if target.lower() == CLAWBANK_ADDRESS.lower():
        return _buy_token_v4_clawbank(amount_eth, target, address, w3, account, token_out, decimals, symbol, balance_before)
    
    # No pool found
    raise SweeperError(
        f"No liquidity pool found for {symbol}. "
        f"Tried V3 fee tiers (0.05%, 0.3%, 1%) with no success. "
        f"Token may not have WETH pair on Base or liquidity is insufficient."
    )


def send_token(token_address: str, to_address: str, amount: float) -> Dict[str, Any]:
    """Send ERC-20 tokens or native ETH from the ClawBank wallet.

    Args:
        token_address: ERC-20 contract address on Base, or "ETH"/"native"/0x0 for raw ETH.
        to_address: Recipient wallet address.
        amount: Amount to send (in token units; decimals handled internally).

    Returns:
        Dict with tx_hash and status on success.
    """
    from bankskills.wallet import get_wallet, load_private_key

    if amount <= 0:
        raise SweeperError("Amount must be greater than zero.")

    if not _validate_address(to_address):
        raise SweeperError(f"Invalid recipient address: {to_address}")

    to_address = checksum(to_address)
    wallet_info = get_wallet()
    address = wallet_info["address"]
    balance_eth = float(wallet_info["eth_balance"])

    rpc_url = os.environ.get(BASE_RPC_URL_ENV, DEFAULT_RPC)
    from web3 import Web3
    from eth_account import Account

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    private_key = load_private_key()
    account = Account.from_key(private_key)

    if _is_native_eth(token_address):
        amount_wei = w3.to_wei(amount, "ether")
        gas_limit = 21000  # Fixed for simple ETH transfer
        gas_price = w3.eth.gas_price
        gas_cost = gas_limit * gas_price
        if amount_wei + w3.to_wei(GAS_RESERVE_ETH, "ether") > w3.eth.get_balance(address):
            raise SweeperError(
                f"Insufficient ETH. Need {amount} ETH + {GAS_RESERVE_ETH} for gas. "
                f"Balance: {balance_eth} ETH."
            )
        tx = {
            "from": address,
            "to": to_address,
            "value": amount_wei,
            "chainId": 8453,
            "nonce": w3.eth.get_transaction_count(address),
            "gas": gas_limit,
            "gasPrice": gas_price,
        }
        if w3.eth.get_balance(address) < amount_wei + gas_cost:
            raise SweeperError(
                f"Insufficient ETH for transfer + gas. Need {amount} ETH + gas. "
                f"Balance: {balance_eth} ETH."
            )
    else:
        if not _validate_address(token_address):
            raise SweeperError(f"Invalid token address: {token_address}")

        token_address = checksum(
            token_address if token_address.startswith("0x") else "0x" + token_address
        )
        token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
        decimals = token_contract.functions.decimals().call()
        amount_wei = int(amount * (10**decimals))

        token_balance = token_contract.functions.balanceOf(address).call()
        if amount_wei > token_balance:
            symbol = token_contract.functions.symbol().call()
            balance_human = token_balance / (10**decimals)
            raise SweeperError(
                f"Insufficient {symbol} balance. Have {balance_human}, need {amount}."
            )

        tx = token_contract.functions.transfer(to_address, amount_wei).build_transaction(
            {
                "from": address,
                "chainId": 8453,
                "nonce": w3.eth.get_transaction_count(address),
                "gasPrice": w3.eth.gas_price,
            }
        )
        tx["gas"] = w3.eth.estimate_gas(tx)
        gas_cost = tx["gas"] * tx["gasPrice"]
        if w3.eth.get_balance(address) < gas_cost:
            raise SweeperError(
                f"Insufficient ETH for gas. Need ~{w3.from_wei(gas_cost, 'ether')} ETH. "
                f"Balance: {balance_eth} ETH."
            )

    signed = account.sign_transaction(tx)
    tx_hash_bytes = w3.eth.send_raw_transaction(signed.raw_transaction)
    tx_hash = tx_hash_bytes.hex()

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    if receipt["status"] != 1:
        raise SweeperError(f"Transaction failed: {tx_hash}")

    return {"tx_hash": tx_hash, "status": "confirmed"}

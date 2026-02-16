"""Tests for sweeper module — set_target_token, get_sweep_config, buy_token."""

import os
import sys
from unittest.mock import MagicMock, patch, Mock

import pytest

# Mock uniswap library before any imports that might use it
if 'uniswap_universal_router_decoder' not in sys.modules:
    mock_module = MagicMock()
    mock_module.RouterCodec = MagicMock
    mock_module.FunctionRecipient = MagicMock()
    sys.modules['uniswap_universal_router_decoder'] = mock_module

import bankskills.sweeper as sweeper_module
from bankskills.sweeper import (
    SweeperError,
    get_sweep_config,
    get_token_balance,
    set_target_token,
    buy_token,
    send_token,
)


@pytest.fixture(autouse=True)
def _isolate_sweep_config(tmp_path, monkeypatch):
    """Use a temp directory for sweep config in each test."""
    config_dir = tmp_path / ".clawbank"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "sweep.config"
    monkeypatch.setattr(sweeper_module, "SWEEP_CONFIG_DIR", str(config_dir))
    monkeypatch.setattr(sweeper_module, "SWEEP_CONFIG_PATH", str(config_path))
    monkeypatch.delenv("BASE_RPC_URL", raising=False)
    yield


class TestSetTargetToken:
    def test_invalid_address_raises(self):
        with pytest.raises(SweeperError, match="Invalid token address"):
            set_target_token("not-an-address")
        with pytest.raises(SweeperError, match="Invalid token address"):
            set_target_token("0x123")  # Too short
        with pytest.raises(SweeperError, match="Invalid token address"):
            set_target_token("0x" + "1" * 39 + "g")  # Invalid hex

    def test_valid_address_calls_symbol_and_writes_config(self):
        with patch("bankskills.sweeper.checksum", lambda x: x):
            with patch("web3.Web3") as mock_web3:
                mock_w3 = MagicMock()
                mock_contract = MagicMock()
                mock_contract.functions.symbol.return_value.call.return_value = "CLAW"
                mock_w3.eth.contract.return_value = mock_contract
                mock_web3.return_value = mock_w3
                mock_web3.HTTPProvider = MagicMock()
                mock_web3.to_checksum_address = lambda x: x

                result = set_target_token("0x16332535E2c27da578bC2e82bEb09Ce9d3C8EB07")

        assert result["status"] == "ok"
        assert result["token_address"] == "0x16332535E2c27da578bC2e82bEb09Ce9d3C8EB07"
        assert result["token_symbol"] == "CLAW"

        assert os.path.exists(sweeper_module.SWEEP_CONFIG_PATH)
        with open(sweeper_module.SWEEP_CONFIG_PATH) as f:
            content = f.read()
        assert "target=0x16332535E2c27da578bC2e82bEb09Ce9d3C8EB07" in content
        assert "network=base" in content


class TestGetSweepConfig:
    def test_returns_empty_when_no_config(self):
        result = get_sweep_config()
        assert result["target_token"] is None
        assert result["recent_sweeps"] == []
        assert result["network"] == "base"

    def test_parses_target_and_network(self):
        valid_addr = "0xabc1234567890123456789012345678901234567"
        with open(sweeper_module.SWEEP_CONFIG_PATH, "w") as f:
            f.write(f"target={valid_addr}\nnetwork=base\n")

        with patch("web3.Web3") as mock_web3:
            mock_w3 = MagicMock()
            mock_contract = MagicMock()
            mock_contract.functions.symbol.return_value.call.return_value = "TEST"
            mock_w3.eth.contract.return_value = mock_contract
            mock_web3.return_value = mock_w3
            mock_web3.HTTPProvider = MagicMock()
            mock_web3.to_checksum_address = lambda x: x

            result = get_sweep_config()

        # target_token is checksummed by get_sweep_config
        assert result["target_token"] == "0xAbc1234567890123456789012345678901234567"
        assert result["token_symbol"] == "TEST"
        assert result["network"] == "base"

    def test_parses_recent_sweeps(self):
        valid_addr = "0xabc1234567890123456789012345678901234567"
        with open(sweeper_module.SWEEP_CONFIG_PATH, "w") as f:
            f.write(f"target={valid_addr}\nnetwork=base\n")
            f.write("2026-02-14 12:03:00 | spent: 0.25 ETH | bought: 4231.7 CLAW | tx: 0xdef123\n")

        with patch("web3.Web3") as mock_web3:
            mock_w3 = MagicMock()
            mock_contract = MagicMock()
            mock_contract.functions.symbol.return_value.call.return_value = "CLAW"
            mock_w3.eth.contract.return_value = mock_contract
            mock_web3.return_value = mock_w3
            mock_web3.HTTPProvider = MagicMock()
            mock_web3.to_checksum_address = lambda x: x

            result = get_sweep_config()

        assert len(result["recent_sweeps"]) == 1
        assert result["recent_sweeps"][0]["timestamp"] == "2026-02-14 12:03:00"
        assert result["recent_sweeps"][0]["spent"] == "0.25 ETH"
        assert result["recent_sweeps"][0]["bought"] == "4231.7 CLAW"
        assert result["recent_sweeps"][0]["tx_hash"] == "0xdef123"


class TestBuyToken:
    def test_raises_when_no_target_set(self):
        """Test validation happens before library import."""
        with pytest.raises(SweeperError, match="No target token set"):
            with patch("bankskills.sweeper.get_sweep_config") as mock_cfg, \
                 patch("bankskills.wallet.get_wallet") as mock_wallet:
                mock_cfg.return_value = {"target_token": None}
                mock_wallet.return_value = {"address": "0x123", "eth_balance": "1.0"}
                buy_token(0.1)

    def test_raises_when_amount_zero_or_negative(self):
        valid_addr = "0xabc1234567890123456789012345678901234567"
        with patch("bankskills.sweeper.get_sweep_config") as mock_cfg, \
             patch("bankskills.wallet.get_wallet") as mock_get:
            mock_cfg.return_value = {"target_token": valid_addr}
            mock_get.return_value = {"address": "0x123", "eth_balance": "1.0"}
            with pytest.raises(SweeperError, match="Amount must be greater than zero"):
                buy_token(0)
            with pytest.raises(SweeperError, match="Amount must be greater than zero"):
                buy_token(-0.1)

    def test_raises_when_insufficient_balance(self):
        valid_addr = "0xabc1234567890123456789012345678901234567"
        with patch("bankskills.sweeper.get_sweep_config") as mock_cfg, \
             patch("bankskills.wallet.get_wallet") as mock_get:
            mock_cfg.return_value = {"target_token": valid_addr}
            mock_get.return_value = {"address": "0x123", "eth_balance": "0.0005"}
            with pytest.raises(SweeperError, match="Insufficient balance"):
                buy_token(0.1)

    def test_executes_swap_and_logs(self):
        """Test buy_token with mocked uniswap library."""
        with patch("bankskills.sweeper.get_sweep_config") as mock_cfg, \
             patch("bankskills.wallet.get_wallet") as mock_get, \
             patch("bankskills.wallet.load_private_key") as mock_pk, \
             patch("uniswap_universal_router_decoder.RouterCodec") as mock_codec_cls:
            
            mock_cfg.return_value = {"target_token": "0x16332535e2c27da578bc2e82beb09ce9d3c8eb07"}
            mock_get.return_value = {"address": "0x1234567890abcdef1234567890abcdef12345678", "eth_balance": "1.0"}
            mock_pk.return_value = "0x" + "1" * 64

            with patch("web3.Web3") as mock_web3:
                mock_w3 = MagicMock()
                mock_w3.to_wei.return_value = 100000000000000000
                mock_w3.to_checksum_address = lambda x: x
                mock_w3.eth.chain_id = 8453
                mock_web3.to_checksum_address = lambda x: x

                mock_token = MagicMock()
                mock_token.functions.decimals.return_value.call.return_value = 18
                mock_token.functions.balanceOf.return_value.call.side_effect = [
                    0,  # Before swap
                    5000000000000000000000,  # After swap (5000 tokens)
                ]
                mock_token.functions.symbol.return_value.call.return_value = "CLAW"
                mock_w3.eth.contract.return_value = mock_token

                # Mock codec
                mock_codec = MagicMock()
                mock_encode_chain = MagicMock()
                mock_codec.encode.chain.return_value = mock_encode_chain
                mock_codec.encode.v4_pool_key.return_value = ("0x123", "0x456", 0x800000, 200, "0x789")
                mock_codec.get_default_deadline.return_value = 1234567890
                
                # Setup method chain for codec
                mock_v4_swap = MagicMock()
                mock_encode_chain.wrap_eth.return_value = mock_v4_swap
                mock_v4_swap.v4_swap.return_value = mock_v4_swap
                mock_v4_swap.swap_exact_in_single.return_value = mock_v4_swap
                mock_v4_swap.settle.return_value = mock_v4_swap
                mock_v4_swap.take_all.return_value = mock_v4_swap
                mock_v4_swap.build_v4_swap.return_value = mock_v4_swap
                mock_v4_swap.build_transaction.return_value = {
                    "from": "0x1234567890abcdef1234567890abcdef12345678",
                    "to": "0x6fF5693b99212Da76ad316178A184AB56D299b43",
                    "value": 100000000000000000,
                    "data": "0x1234",
                    "gas": 500000,
                    "chainId": 8453,
                    "nonce": 0,
                    "maxFeePerGas": 1000000000,
                    "maxPriorityFeePerGas": 1000000000,
                }
                
                mock_codec_cls.return_value = mock_codec

                mock_account = MagicMock()
                mock_signed = MagicMock()
                mock_signed.raw_transaction = b"raw_tx"
                mock_account.sign_transaction.return_value = mock_signed

                mock_w3.eth.send_raw_transaction.return_value = b"\xab\xcd"
                mock_w3.eth.wait_for_transaction_receipt.return_value = {"status": 1, "logs": []}

                mock_web3.return_value = mock_w3
                mock_web3.HTTPProvider = MagicMock()

                with patch("eth_account.Account.from_key", return_value=mock_account):
                    result = buy_token(0.1)

        assert result["tx_hash"]
        assert "0.1" in result["amount_in"]
        assert "ETH" in result["amount_in"]
        assert "5000" in result["amount_out"]
        assert "CLAW" in result["amount_out"]
        assert result["status"] == "confirmed"

        with open(sweeper_module.SWEEP_CONFIG_PATH) as f:
            content = f.read()
        assert "spent:" in content
        assert "bought:" in content
        assert "tx:" in content


class TestGetTokenBalance:
    def test_invalid_address_raises(self):
        with pytest.raises(SweeperError, match="Invalid token address"):
            get_token_balance("not-an-address")
        with pytest.raises(SweeperError, match="Invalid token address"):
            get_token_balance("0x123")

    def test_returns_balance_with_symbol_and_decimals(self):
        with patch("bankskills.wallet.get_wallet") as mock_get:
            mock_get.return_value = {
                "address": "0x1234567890abcdef1234567890abcdef12345678",
                "eth_balance": "1.0",
            }
            with patch("web3.Web3") as mock_web3:
                mock_w3 = MagicMock()
                mock_contract = MagicMock()
                mock_contract.functions.balanceOf.return_value.call.return_value = (
                    1423500000000000000000
                )
                mock_contract.functions.decimals.return_value.call.return_value = 18
                mock_contract.functions.symbol.return_value.call.return_value = "CLAW"
                mock_w3.eth.contract.return_value = mock_contract
                mock_web3.return_value = mock_w3
                mock_web3.HTTPProvider = MagicMock()

                result = get_token_balance(
                    "0x16332535E2c27da578bC2e82bEb09Ce9d3C8EB07"
                )

        assert result["token_address"] == "0x16332535E2c27da578bC2e82bEb09Ce9d3C8EB07"
        assert result["symbol"] == "CLAW"
        assert result["balance"] == "1423.5"
        assert result["raw_balance"] == "1423500000000000000000"


class TestSendToken:
    """Tests for send_token validation and native ETH handling."""

    @pytest.fixture
    def _wallet_and_web3(self, tmp_path, monkeypatch):
        """Create wallet and patch for send_token tests."""
        wallet_dir = tmp_path / ".clawbank"
        wallet_dir.mkdir(parents=True, exist_ok=True)
        wallet_path = wallet_dir / "wallet.json"
        monkeypatch.setattr(
            "bankskills.wallet.WALLET_DIR", str(wallet_dir)
        )
        monkeypatch.setattr(
            "bankskills.wallet.WALLET_PATH", str(wallet_path)
        )
        # Create minimal keystore so load_private_key works
        from eth_account import Account
        acct = Account.create()
        keystore = Account.encrypt(acct.key, "test")
        with open(wallet_path, "w") as f:
            import json
            json.dump(keystore, f)
        return {
            "address": acct.address,
            "eth_balance": "0.1",
            "private_key": acct.key.hex(),
        }

    def test_raises_when_amount_zero_or_negative(self):
        with pytest.raises(SweeperError, match="Amount must be greater than zero"):
            send_token("ETH", "0x3838caF010Cc92496A3568b3ae71Ac4ceab21d37", 0)
        with pytest.raises(SweeperError, match="Amount must be greater than zero"):
            send_token("ETH", "0x3838caF010Cc92496A3568b3ae71Ac4ceab21d37", -0.001)

    def test_raises_when_invalid_to_address(self):
        with pytest.raises(SweeperError, match="Invalid recipient address"):
            send_token("ETH", "not-an-address", 0.001)
        with pytest.raises(SweeperError, match="Invalid recipient address"):
            send_token("ETH", "0x123", 0.001)

    def test_raises_when_insufficient_token_balance(self, _wallet_and_web3):
        """ERC-20 path: should fail fast when token balance < amount."""
        pk = _wallet_and_web3["private_key"]
        wallet_info = {"address": _wallet_and_web3["address"], "eth_balance": _wallet_and_web3["eth_balance"]}
        with patch("bankskills.wallet.get_wallet", return_value=wallet_info), \
             patch("bankskills.wallet.load_private_key", return_value=pk):
            with patch("web3.Web3") as mock_web3:
                mock_w3 = MagicMock()
                mock_w3.to_wei.return_value = 1000000000000000000
                mock_w3.eth.gas_price = 1000000000
                mock_w3.eth.get_transaction_count.return_value = 0
                mock_contract = MagicMock()
                mock_contract.functions.decimals.return_value.call.return_value = 18
                mock_contract.functions.balanceOf.return_value.call.return_value = 500  # Only 500 wei
                mock_contract.functions.symbol.return_value.call.return_value = "CLAW"
                mock_w3.eth.contract.return_value = mock_contract
                mock_web3.return_value = mock_w3
                mock_web3.HTTPProvider = MagicMock()

                token_addr = "0x16332535E2c27da578bC2e82bEb09Ce9d3C8EB07"
                with pytest.raises(SweeperError, match="Insufficient CLAW balance"):
                    send_token(token_addr, "0x3838caF010Cc92496A3568b3ae71Ac4ceab21d37", 1000)

"""Integration test for V4 ClawBank swap - validates the working implementation.

Tests the actual buy_token() function with the uniswap-universal-router-decoder library.
Based on successful transaction: https://basescan.org/tx/d0fa2d73e6fb88feb21fb584fc140f67f70cc215b12330a84a8ea1cd7cc77128
"""

import pytest
from unittest.mock import MagicMock, patch
from bankskills.sweeper import buy_token, SweeperError
import bankskills.sweeper as sweeper_module


@pytest.fixture(autouse=True)
def _isolate_sweep_config(tmp_path, monkeypatch):
    """Use a temp directory for sweep config in each test."""
    config_dir = tmp_path / ".clawbank"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "sweep.config"
    monkeypatch.setattr(sweeper_module, "SWEEP_CONFIG_DIR", str(config_dir))
    monkeypatch.setattr(sweeper_module, "SWEEP_CONFIG_PATH", str(config_path))
    yield


class TestV4SwapImplementation:
    """Test the actual V4 swap implementation details."""

    def test_uses_correct_v4_router_address(self):
        """Verify using V4 Universal Router, not V3."""
        assert sweeper_module.UNIVERSAL_ROUTER_ADDRESS == "0x6fF5693b99212Da76ad316178A184AB56D299b43"
        assert sweeper_module.UNIVERSAL_ROUTER_ADDRESS != "0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD"  # Not V3

    def test_uses_correct_clawbank_pool_parameters(self):
        """Verify ClawBank V4 pool params match successful transactions."""
        assert sweeper_module.CLAWBANK_POOL_FEE == 0x800000, "Fee should be 0x800000 (dynamic fee)"
        assert sweeper_module.CLAWBANK_TICK_SPACING == 200, "Tick spacing should be 200"
        assert sweeper_module.CLAWBANK_HOOKS == "0xb429d62f8f3bFFb98CdB9569533eA23bF0Ba28CC", "Hooks address incorrect"

    def test_uses_correct_v4_commands(self):
        """Verify correct V4 command bytes."""
        assert sweeper_module.WRAP_ETH == 0x0B, "WRAP_ETH command should be 0x0B"
        assert sweeper_module.V4_SWAP == 0x10, "V4_SWAP command should be 0x10"
        
        # V4 actions inside V4_SWAP
        assert sweeper_module.SWAP_EXACT_IN == 0x07, "SWAP_EXACT_IN action should be 0x07"
        assert sweeper_module.SETTLE == 0x0B, "SETTLE action should be 0x0B"
        assert sweeper_module.TAKE == 0x0E, "TAKE action should be 0x0E"

    def test_buy_token_uses_uniswap_decoder_library_for_clawbank(self):
        """Verify buy_token() uses the uniswap-universal-router-decoder library for ClawBank (V4 fallback)."""
        with patch("bankskills.sweeper.get_sweep_config") as mock_cfg, \
             patch("bankskills.wallet.get_wallet") as mock_wallet, \
             patch("bankskills.wallet.load_private_key") as mock_pk, \
             patch("web3.Web3") as mock_web3_cls, \
             patch("uniswap_universal_router_decoder.RouterCodec") as mock_codec_cls, \
             patch("bankskills.sweeper._try_v3_swap") as mock_v3:
            
            # Setup mocks - use ClawBank address to trigger V4 fallback
            CLAWBANK = "0x16332535E2c27da578bC2e82bEb09Ce9d3C8EB07"
            mock_cfg.return_value = {"target_token": CLAWBANK}
            mock_wallet.return_value = {"address": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd", "eth_balance": "1.0"}  # Generic test wallet
            mock_pk.return_value = "0x" + "1" * 64
            
            # Mock V3 to return None (simulate no V3 pool), forcing V4 fallback
            mock_v3.return_value = None
            
            mock_w3 = MagicMock()
            mock_w3.to_wei.return_value = 2000000000000000  # 0.002 ETH
            mock_w3.to_checksum_address = lambda x: x
            mock_web3_cls.return_value = mock_w3
            mock_web3_cls.HTTPProvider = MagicMock()
            mock_web3_cls.to_checksum_address = lambda x: x
            
            # Mock token contract
            mock_token = MagicMock()
            mock_token.functions.decimals.return_value.call.return_value = 18
            mock_token.functions.symbol.return_value.call.return_value = "ClawBank"
            mock_token.functions.balanceOf.return_value.call.side_effect = [0, 1000000000000000000000]
            mock_w3.eth.contract.return_value = mock_token
            
            # Mock codec
            mock_codec = MagicMock()
            mock_encode_chain = MagicMock()
            mock_codec.encode.chain.return_value = mock_encode_chain
            mock_codec.encode.v4_pool_key.return_value = ("0x123", "0x456", 0x800000, 200, "0x789")
            mock_codec.get_default_deadline.return_value = 1234567890
            
            # Setup method chain
            mock_v4_swap = MagicMock()
            mock_encode_chain.wrap_eth.return_value = mock_v4_swap
            mock_v4_swap.v4_swap.return_value = mock_v4_swap
            mock_v4_swap.swap_exact_in_single.return_value = mock_v4_swap
            mock_v4_swap.settle.return_value = mock_v4_swap
            mock_v4_swap.take_all.return_value = mock_v4_swap
            mock_v4_swap.build_v4_swap.return_value = mock_v4_swap
            mock_v4_swap.build_transaction.return_value = {
                "from": "0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",  # Generic test wallet
                "to": "0x6fF5693b99212Da76ad316178A184AB56D299b43",  # V4 Universal Router (protocol)
                "value": 2000000000000000,
                "data": "0x1234",
                "gas": 500000,
                "chainId": 8453,
                "nonce": 0,
                "maxFeePerGas": 1000000000,
                "maxPriorityFeePerGas": 1000000000,
            }
            
            mock_codec_cls.return_value = mock_codec
            
            # Mock account
            mock_account = MagicMock()
            mock_signed = MagicMock()
            mock_signed.raw_transaction = b"raw_tx"
            mock_account.sign_transaction.return_value = mock_signed
            mock_w3.eth.send_raw_transaction.return_value = b"\xab\xcd"
            mock_w3.eth.wait_for_transaction_receipt.return_value = {"status": 1}
            
            with patch("eth_account.Account.from_key", return_value=mock_account):
                result = buy_token(0.002)
            
            # Verify RouterCodec was instantiated with w3
            mock_codec_cls.assert_called_once()
            assert mock_codec_cls.call_args[1]["w3"] == mock_w3
            
            # Verify V3 was tried first
            mock_v3.assert_called_once()
            
            # Verify v4_pool_key was called with ClawBank parameters
            mock_codec.encode.v4_pool_key.assert_called_once()
            call_args = mock_codec.encode.v4_pool_key.call_args[0]
            assert call_args[0] == CLAWBANK  # ClawBank token
            assert call_args[1] == sweeper_module.WETH_ADDRESS
            assert call_args[2] == sweeper_module.CLAWBANK_POOL_FEE
            assert call_args[3] == sweeper_module.CLAWBANK_TICK_SPACING
            assert call_args[4] == sweeper_module.CLAWBANK_HOOKS
            
            # Verify wrap_eth was called
            mock_encode_chain.wrap_eth.assert_called_once()
            
            # Verify swap_exact_in_single was called with empty hookData
            mock_v4_swap.swap_exact_in_single.assert_called_once()
            swap_call = mock_v4_swap.swap_exact_in_single.call_args[1]
            assert swap_call["hook_data"] == b"", "hookData must be empty, not 'unix...'"
            assert swap_call["zero_for_one"] == False, "Should be WETH -> ClawBank (False)"
            assert swap_call["amount_out_min"] == 0, "Should have no slippage protection (for now)"
            
            # Verify settle and take_all were called
            mock_v4_swap.settle.assert_called_once()
            mock_v4_swap.take_all.assert_called_once()
            
            # Verify build_transaction was called (key for gas handling)
            mock_v4_swap.build_transaction.assert_called_once()
            
            assert result["status"] == "confirmed"


class TestV4SwapConfigValidation:
    """Test configuration and parameter validation."""
    
    def test_has_correct_weth_address_for_base(self):
        """WETH address must match Base network."""
        assert sweeper_module.WETH_ADDRESS == "0x4200000000000000000000000000000000000006"
    
    def test_gas_reserve_is_reasonable(self):
        """Gas reserve should protect against running out during swap."""
        assert sweeper_module.GAS_RESERVE_ETH == 0.001
        assert sweeper_module.GAS_RESERVE_ETH > 0
        assert sweeper_module.GAS_RESERVE_ETH < 0.01  # Not too conservative


class TestV4SwapErrorHandling:
    """Test error conditions specific to V4 swaps."""
    
    def test_requires_uniswap_library_installed(self):
        """Verify the uniswap-universal-router-decoder library is importable."""
        try:
            from uniswap_universal_router_decoder import RouterCodec, FunctionRecipient
            assert RouterCodec is not None
            assert FunctionRecipient is not None
        except ImportError:
            pytest.fail("uniswap-universal-router-decoder library is required but not installed")
    
    def test_library_has_required_methods(self):
        """Verify the library has all methods we use."""
        from uniswap_universal_router_decoder import RouterCodec
        from unittest.mock import MagicMock
        
        mock_w3 = MagicMock()
        codec = RouterCodec(w3=mock_w3)
        
        # Verify methods exist
        assert hasattr(codec.encode, "v4_pool_key")
        assert hasattr(codec.encode, "chain")
        assert hasattr(codec, "get_default_deadline")
        
        # Verify chain methods exist
        chain = codec.encode.chain()
        assert hasattr(chain, "wrap_eth")
        assert hasattr(chain, "v4_swap")
        assert hasattr(chain, "build")


@pytest.mark.integration
class TestV4SwapRealNetwork:
    """Integration tests that require real network access (mark as @pytest.mark.integration)."""
    
    @pytest.mark.skip(reason="Requires real Base RPC and costs gas - run manually only")
    def test_buy_token_end_to_end(self):
        """
        Real end-to-end test (MANUAL ONLY).
        
        To run: pytest tests/test_20_v4_swap_integration.py::TestV4SwapRealNetwork::test_buy_token_end_to_end -v -s
        
        Prerequisites:
        - Wallet configured in ~/.clawbank/wallet.json
        - At least 0.005 ETH in wallet
        - BASE_RPC_URL env var (or uses default)
        """
        from bankskills.sweeper import set_target_token, buy_token
        
        # Set target token (use actual ClawBank address for real integration test)
        # Note: This test is skipped by default - only run manually with real wallet
        clawbank_address = "0x16332535E2c27da578bC2e82bEb09Ce9d3C8EB07"
        result = set_target_token(clawbank_address)
        assert result["token_symbol"] == "ClawBank"
        
        # Execute small buy
        result = buy_token(0.002)
        assert result["status"] == "confirmed"
        assert "tx_hash" in result
        assert "ClawBank" in result["amount_out"]
        print(f"\n✓ Swap succeeded: {result['tx_hash']}")

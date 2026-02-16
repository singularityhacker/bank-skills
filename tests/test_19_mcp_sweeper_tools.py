"""Tests for Story 19 — MCP: sweeper tools exposed."""

from bankskills.mcp.server import mcp


class TestMCPSweeperToolsExist:
    def _tool_names(self):
        return [t.name for t in mcp._tool_manager._tools.values()]

    def test_mcp_server_has_create_wallet_tool(self):
        assert "create_wallet" in self._tool_names()

    def test_mcp_server_has_get_wallet_tool(self):
        assert "get_wallet" in self._tool_names()

    def test_mcp_server_has_set_target_token_tool(self):
        assert "set_target_token" in self._tool_names()

    def test_mcp_server_has_get_sweep_config_tool(self):
        assert "get_sweep_config" in self._tool_names()

    def test_mcp_server_has_get_token_balance_tool(self):
        assert "get_token_balance" in self._tool_names()

    def test_mcp_server_has_buy_token_tool(self):
        assert "buy_token" in self._tool_names()

    def test_mcp_server_has_send_token_tool(self):
        assert "send_token" in self._tool_names()

    def test_mcp_server_has_export_private_key_tool(self):
        assert "export_private_key" in self._tool_names()


class TestMCPSweeperToolSchemas:
    def _get_tool(self, name):
        for t in mcp._tool_manager._tools.values():
            if t.name == name:
                return t
        return None

    def test_create_wallet_has_no_required_params(self):
        tool = self._get_tool("create_wallet")
        assert tool is not None
        schema = tool.parameters
        required = schema.get("required", [])
        assert len(required) == 0

    def test_get_wallet_has_no_required_params(self):
        tool = self._get_tool("get_wallet")
        assert tool is not None
        schema = tool.parameters
        required = schema.get("required", [])
        assert len(required) == 0

    def test_set_target_token_has_token_address_param(self):
        tool = self._get_tool("set_target_token")
        assert tool is not None
        schema = tool.parameters
        assert "token_address" in schema.get("properties", {})
        required = schema.get("required", [])
        assert "token_address" in required

    def test_get_sweep_config_has_no_required_params(self):
        tool = self._get_tool("get_sweep_config")
        assert tool is not None
        schema = tool.parameters
        required = schema.get("required", [])
        assert len(required) == 0

    def test_get_token_balance_has_token_address_param(self):
        tool = self._get_tool("get_token_balance")
        assert tool is not None
        schema = tool.parameters
        assert "token_address" in schema.get("properties", {})
        required = schema.get("required", [])
        assert "token_address" in required

    def test_buy_token_has_amount_eth_param(self):
        tool = self._get_tool("buy_token")
        assert tool is not None
        schema = tool.parameters
        assert "amount_eth" in schema.get("properties", {})
        required = schema.get("required", [])
        assert "amount_eth" in required

    def test_send_token_has_required_params(self):
        tool = self._get_tool("send_token")
        assert tool is not None
        schema = tool.parameters
        assert "token_address" in schema.get("properties", {})
        assert "to_address" in schema.get("properties", {})
        assert "amount" in schema.get("properties", {})
        required = schema.get("required", [])
        assert "token_address" in required
        assert "to_address" in required
        assert "amount" in required

    def test_export_private_key_has_no_required_params(self):
        tool = self._get_tool("export_private_key")
        assert tool is not None
        schema = tool.parameters
        required = schema.get("required", [])
        assert len(required) == 0

"""Tests for Story 17 — MCP: bank tools exposed."""

from bankskills.mcp.server import mcp


class TestMCPToolsExist:
    def _tool_names(self):
        return [t.name for t in mcp._tool_manager._tools.values()]

    def test_mcp_server_has_check_balance_tool(self):
        assert "check_balance" in self._tool_names()

    def test_mcp_server_has_get_receive_details_tool(self):
        assert "get_receive_details" in self._tool_names()

    def test_mcp_server_has_send_money_tool(self):
        assert "send_money" in self._tool_names()


class TestMCPToolDescriptions:
    def _get_tool(self, name):
        for t in mcp._tool_manager._tools.values():
            if t.name == name:
                return t
        return None

    def test_check_balance_has_description(self):
        tool = self._get_tool("check_balance")
        assert tool is not None
        assert tool.description
        assert "balance" in tool.description.lower()

    def test_get_receive_details_has_description(self):
        tool = self._get_tool("get_receive_details")
        assert tool is not None
        assert tool.description
        assert "receive" in tool.description.lower() or "account" in tool.description.lower()

    def test_send_money_has_description(self):
        tool = self._get_tool("send_money")
        assert tool is not None
        assert tool.description
        assert "send" in tool.description.lower()


class TestMCPToolParameters:
    def _get_tool(self, name):
        for t in mcp._tool_manager._tools.values():
            if t.name == name:
                return t
        return None

    def test_check_balance_has_optional_currency_param(self):
        tool = self._get_tool("check_balance")
        schema = tool.parameters
        # currency should be in properties but not required
        assert "currency" in schema.get("properties", {})

    def test_send_money_has_required_params(self):
        tool = self._get_tool("send_money")
        schema = tool.parameters
        required = schema.get("required", [])
        assert "source_currency" in required
        assert "target_currency" in required
        assert "amount" in required
        assert "recipient_name" in required
        assert "recipient_account" in required

    def test_get_receive_details_has_optional_currency_param(self):
        tool = self._get_tool("get_receive_details")
        schema = tool.parameters
        assert "currency" in schema.get("properties", {})

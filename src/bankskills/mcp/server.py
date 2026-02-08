"""
FastMCP server implementation for Bank Skills.

Exposes skills as MCP tools that can be discovered and used by
MCP-compatible frameworks.
"""

from fastmcp import FastMCP
from typing import Any, Dict, List, Optional

# Initialize FastMCP server
mcp = FastMCP("Bank Skills")


@mcp.tool()
def list_skills() -> Dict[str, Any]:
    """
    List all available skills in the registry.

    Returns:
        Dictionary containing list of available skills
    """
    # TODO: Implement skill discovery from skills/ directory
    return {"skills": []}


@mcp.tool()
def run_skill(skill_name: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Execute a skill by name.

    Args:
        skill_name: Name of the skill to execute
        params: Optional skill-specific parameters

    Returns:
        Dictionary containing skill execution results
    """
    # TODO: Implement skill execution via runtime
    return {"status": "not_implemented", "skill": skill_name}


@mcp.tool()
def check_balance(currency: Optional[str] = None) -> Dict[str, Any]:
    """Check Wise multi-currency balances.

    Args:
        currency: Optional currency filter (e.g. "USD"). Returns all currencies if omitted.

    Returns:
        Dictionary with success status and list of balances (currency, amount, reservedAmount).
    """
    from bankskills.core.bank.credentials import MissingCredentialError, load_credentials
    from bankskills.core.bank.client import WiseClient
    from bankskills.core.bank.balances import BalanceError, fetch_balances

    try:
        credentials = load_credentials()
    except MissingCredentialError as e:
        return {"success": False, "error": str(e)}

    client = WiseClient(credentials=credentials)

    try:
        balances = fetch_balances(client, currency=currency)
        return {"success": True, "balances": balances}
    except BalanceError as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_receive_details(currency: Optional[str] = None) -> Dict[str, Any]:
    """Get account/routing details for receiving payments via Wise.

    Args:
        currency: Optional currency filter (e.g. "USD"). Returns all currencies if omitted.

    Returns:
        Dictionary with account holder, account number, routing number (or IBAN/SWIFT) per currency.
    """
    from bankskills.core.bank.credentials import MissingCredentialError, load_credentials
    from bankskills.core.bank.client import WiseClient
    from bankskills.core.bank.account_details import AccountDetailsError, fetch_account_details

    try:
        credentials = load_credentials()
    except MissingCredentialError as e:
        return {"success": False, "error": str(e)}

    client = WiseClient(credentials=credentials)

    try:
        details = fetch_account_details(client, currency=currency)
        return {"success": True, "details": details}
    except AccountDetailsError as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def send_money(
    source_currency: str,
    target_currency: str,
    amount: float,
    recipient_name: str,
    recipient_account: str,
    recipient_routing_number: Optional[str] = None,
    recipient_country: Optional[str] = None,
    recipient_account_type: Optional[str] = None,
    recipient_address: Optional[str] = None,
    recipient_city: Optional[str] = None,
    recipient_state: Optional[str] = None,
    recipient_post_code: Optional[str] = None,
) -> Dict[str, Any]:
    """Send money via Wise (quote -> recipient -> transfer -> fund).

    Args:
        source_currency: Source currency code (e.g. "USD").
        target_currency: Target currency code (e.g. "EUR").
        amount: Amount to send.
        recipient_name: Full name of the recipient.
        recipient_account: Recipient account number or IBAN.
        recipient_routing_number: For USD: 9-digit ABA routing number (required for USD).
        recipient_country: Two-letter country code (e.g. DE, US). Required for USD ACH.
        recipient_account_type: For USD ACH: CHECKING or SAVINGS (default CHECKING).
        recipient_address: For USD ACH: street address (required for USD).
        recipient_city: For USD ACH: city (required for USD).
        recipient_state: For USD ACH: state code (e.g. OH, NY). Optional.
        recipient_post_code: For USD ACH: post/ZIP code (required for USD).

    Returns:
        Dictionary with transfer ID, status, and amount details on success.
    """
    from bankskills.core.bank.credentials import MissingCredentialError, load_credentials
    from bankskills.core.bank.client import WiseClient
    from bankskills.core.bank.transfer import (
        InsufficientFundsError,
        TransferError,
        send_money as core_send_money,
    )

    try:
        credentials = load_credentials()
    except MissingCredentialError as e:
        return {"success": False, "error": str(e)}

    client = WiseClient(credentials=credentials)

    try:
        result = core_send_money(
            client,
            source_currency=source_currency,
            target_currency=target_currency,
            amount=amount,
            recipient_name=recipient_name,
            recipient_account=recipient_account,
            recipient_routing_number=recipient_routing_number,
            recipient_country=recipient_country,
            recipient_account_type=recipient_account_type,
            recipient_address=recipient_address,
            recipient_city=recipient_city,
            recipient_state=recipient_state,
            recipient_post_code=recipient_post_code,
        )
        return {"success": True, "transfer": result}
    except InsufficientFundsError as e:
        return {"success": False, "error": str(e)}
    except TransferError as e:
        return {"success": False, "error": str(e)}


def main():
    """Entry point for MCP server."""
    # FastMCP handles server startup
    mcp.run()


if __name__ == "__main__":
    main()

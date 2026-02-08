"""Bank skill handler — entry point for run.sh dispatching.

Reads JSON from stdin, routes to the correct action, and outputs JSON to stdout.
"""

import json
import sys
from typing import Any, Dict

from bankskills.core.bank.credentials import MissingCredentialError, load_credentials
from bankskills.core.bank.client import WiseClient


def handle(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Route an action to the appropriate core function.

    Args:
        input_data: Parsed JSON input with at least an "action" key.

    Returns:
        JSON-serializable result dict.
    """
    action = input_data.get("action", "").strip()

    if not action:
        return {"success": False, "error": "Missing 'action' field. Use: balance, receive-details, send"}

    try:
        credentials = load_credentials()
    except MissingCredentialError as e:
        return {"success": False, "error": str(e)}

    client = WiseClient(credentials=credentials)

    if action == "balance":
        return _handle_balance(client, input_data)
    elif action == "receive-details":
        return _handle_receive_details(client, input_data)
    elif action == "send":
        return _handle_send(client, input_data)
    else:
        return {"success": False, "error": f"Unknown action: {action}"}


def _handle_balance(client: WiseClient, input_data: Dict[str, Any]) -> Dict[str, Any]:
    from bankskills.core.bank.balances import BalanceError, fetch_balances

    currency = input_data.get("currency")
    try:
        balances = fetch_balances(client, currency=currency)
        return {"success": True, "balances": balances}
    except BalanceError as e:
        return {"success": False, "error": str(e)}


def _handle_receive_details(client: WiseClient, input_data: Dict[str, Any]) -> Dict[str, Any]:
    from bankskills.core.bank.account_details import AccountDetailsError, fetch_account_details

    currency = input_data.get("currency")
    try:
        details = fetch_account_details(client, currency=currency)
        return {"success": True, "details": details}
    except AccountDetailsError as e:
        return {"success": False, "error": str(e)}


def _handle_send(client: WiseClient, input_data: Dict[str, Any]) -> Dict[str, Any]:
    from bankskills.core.bank.transfer import InsufficientFundsError, TransferError, send_money

    required = ["sourceCurrency", "targetCurrency", "amount", "recipientName", "recipientAccount"]
    missing = [f for f in required if f not in input_data]
    if missing:
        return {"success": False, "error": f"Missing required fields: {', '.join(missing)}"}

    try:
        result = send_money(
            client,
            source_currency=input_data["sourceCurrency"],
            target_currency=input_data["targetCurrency"],
            amount=float(input_data["amount"]),
            recipient_name=input_data["recipientName"],
            recipient_account=input_data["recipientAccount"],
            recipient_routing_number=input_data.get("recipientRoutingNumber"),
            recipient_country=input_data.get("recipientCountry"),
            recipient_account_type=input_data.get("recipientAccountType"),
            recipient_address=input_data.get("recipientAddress"),
            recipient_city=input_data.get("recipientCity"),
            recipient_state=input_data.get("recipientState"),
            recipient_post_code=input_data.get("recipientPostCode"),
        )
        return {"success": True, "transfer": result}
    except InsufficientFundsError as e:
        return {"success": False, "error": str(e)}
    except TransferError as e:
        return {"success": False, "error": str(e)}


def main():
    """CLI entry point: read JSON from stdin, dispatch, print JSON to stdout."""
    # Read action from args or stdin
    input_data = {}

    # Check for action as first CLI arg
    args = sys.argv[1:]
    if args:
        input_data["action"] = args[0]

    # Read JSON from stdin if available
    if not sys.stdin.isatty():
        try:
            stdin_text = sys.stdin.read().strip()
            if stdin_text:
                stdin_data = json.loads(stdin_text)
                # stdin overrides / merges with args
                input_data.update(stdin_data)
        except json.JSONDecodeError as e:
            result = {"success": False, "error": f"Invalid JSON input: {e}"}
            json.dump(result, sys.stdout, indent=2)
            print()
            sys.exit(1)

    result = handle(input_data)

    json.dump(result, sys.stdout, indent=2)
    print()

    if not result.get("success", False):
        sys.exit(1)


if __name__ == "__main__":
    main()

"""Bank skill CLI — subcommands for balance, receive-details, send."""

import argparse
import json
import sys

from bankskills.core.bank.credentials import MissingCredentialError, load_credentials
from bankskills.core.bank.client import WiseClient


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="bank",
        description="Bank skill CLI — check balances, send money, get receive details via Wise",
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    sub = parser.add_subparsers(dest="command")

    # balance
    bal = sub.add_parser("balance", help="Check balances")
    bal.add_argument("--currency", help="Filter by currency (e.g. USD)")
    bal.add_argument("--json", action="store_true", dest="json_sub", help="Output as JSON")

    # receive-details
    rd = sub.add_parser("receive-details", help="Get account/routing details")
    rd.add_argument("--currency", help="Filter by currency (e.g. USD)")
    rd.add_argument("--json", action="store_true", dest="json_sub", help="Output as JSON")

    # send
    send = sub.add_parser("send", help="Send money")
    send.add_argument("--source-currency", required=True, help="Source currency")
    send.add_argument("--target-currency", required=True, help="Target currency")
    send.add_argument("--amount", required=True, type=float, help="Amount to send")
    send.add_argument("--recipient-name", required=True, help="Recipient full name")
    send.add_argument("--recipient-account", required=True, help="Recipient account number or IBAN")
    send.add_argument("--recipient-routing-number", help="For USD: 9-digit ABA routing number (required for USD)")
    send.add_argument("--recipient-country", help="Two-letter country code (e.g. DE, US). Required for USD ACH.")
    send.add_argument("--recipient-account-type", default="CHECKING", choices=["CHECKING", "SAVINGS"], help="For USD: CHECKING or SAVINGS (default: CHECKING)")
    send.add_argument("--recipient-address", help="For USD: street address (required for USD ACH)")
    send.add_argument("--recipient-city", help="For USD: city (required for USD ACH)")
    send.add_argument("--recipient-state", help="For USD: state code (e.g. OH, NY)")
    send.add_argument("--recipient-post-code", help="For USD: post/ZIP code (required for USD ACH)")
    send.add_argument("--json", action="store_true", dest="json_sub", help="Output as JSON")

    return parser


def cmd_balance(client: WiseClient, args: argparse.Namespace) -> int:
    from bankskills.core.bank.balances import BalanceError, fetch_balances

    try:
        balances = fetch_balances(client, currency=args.currency)
    except BalanceError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if getattr(args, "json", False):
        json.dump({"success": True, "balances": balances}, sys.stdout, indent=2)
        print()
    else:
        if not balances:
            print("No balances found.")
        else:
            for b in balances:
                reserved = b.get("reservedAmount", 0)
                line = f"  {b['currency']}: {b['amount']:.2f}"
                if reserved:
                    line += f"  (reserved: {reserved:.2f})"
                print(line)
    return 0


def cmd_receive_details(client: WiseClient, args: argparse.Namespace) -> int:
    from bankskills.core.bank.account_details import AccountDetailsError, fetch_account_details

    try:
        details = fetch_account_details(client, currency=args.currency)
    except AccountDetailsError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if getattr(args, "json", False):
        json.dump({"success": True, "details": details}, sys.stdout, indent=2)
        print()
    else:
        if not details:
            print("No account details found.")
        else:
            for d in details:
                print(f"  {d.get('currency', '?')}:")
                if d.get("accountHolder"):
                    print(f"    Account Holder: {d['accountHolder']}")
                if d.get("accountNumber"):
                    print(f"    Account Number: {d['accountNumber']}")
                if d.get("routingNumber"):
                    print(f"    Routing Number: {d['routingNumber']}")
                if d.get("iban"):
                    print(f"    IBAN: {d['iban']}")
                if d.get("swiftBic"):
                    print(f"    SWIFT/BIC: {d['swiftBic']}")
                if d.get("bankName"):
                    print(f"    Bank: {d['bankName']}")
    return 0


def cmd_send(client: WiseClient, args: argparse.Namespace) -> int:
    from bankskills.core.bank.transfer import InsufficientFundsError, TransferError, send_money

    try:
        result = send_money(
            client,
            source_currency=args.source_currency,
            target_currency=args.target_currency,
            amount=args.amount,
            recipient_name=args.recipient_name,
            recipient_account=args.recipient_account,
            recipient_routing_number=getattr(args, "recipient_routing_number", None),
            recipient_country=getattr(args, "recipient_country", None),
            recipient_account_type=getattr(args, "recipient_account_type", None),
            recipient_address=getattr(args, "recipient_address", None),
            recipient_city=getattr(args, "recipient_city", None),
            recipient_state=getattr(args, "recipient_state", None),
            recipient_post_code=getattr(args, "recipient_post_code", None),
        )
    except InsufficientFundsError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except TransferError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    if getattr(args, "json", False):
        json.dump({"success": True, "transfer": result}, sys.stdout, indent=2)
        print()
    else:
        print(f"  Transfer {result['id']}: {result['status']}")
        print(f"  {result['sourceAmount']} {result['sourceCurrency']} -> {result['targetAmount']} {result['targetCurrency']}")
    return 0


def main(argv=None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    # Support both "bank --json balance" and "bank balance --json"
    args.json = getattr(args, "json", False) or getattr(args, "json_sub", False)

    if not args.command:
        parser.print_help()
        return 1

    try:
        credentials = load_credentials()
    except MissingCredentialError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    client = WiseClient(credentials=credentials)

    if args.command == "balance":
        return cmd_balance(client, args)
    elif args.command == "receive-details":
        return cmd_receive_details(client, args)
    elif args.command == "send":
        return cmd_send(client, args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())

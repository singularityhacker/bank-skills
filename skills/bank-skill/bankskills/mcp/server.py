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
def get_exchange_rate(
    source: str,
    target: str,
    time: Optional[str] = None,
) -> Dict[str, Any]:
    """Get the current mid-market exchange rate between two currencies.

    Use this to check how much one currency is worth in another before sending
    money. Returns the live Wise mid-market rate (no markup). You can also
    pass a timestamp to get a historical rate.

    Args:
        source: Source currency code (e.g. "USD", "GBP", "EUR").
        target: Target currency code (e.g. "EUR", "JPY", "BRL").
        time: Optional ISO-8601 timestamp to get a historical rate (e.g. "2025-01-15T12:00:00").

    Returns:
        Dictionary with rate value, source currency, target currency, and timestamp.
    """
    from bankskills.core.bank.credentials import MissingCredentialError, load_credentials
    from bankskills.core.bank.client import WiseClient
    from bankskills.core.bank.rates import RateError, fetch_exchange_rate

    try:
        credentials = load_credentials()
    except MissingCredentialError as e:
        return {"success": False, "error": str(e)}

    client = WiseClient(credentials=credentials)

    try:
        rates = fetch_exchange_rate(client, source=source, target=target, time=time)
        return {"success": True, "rates": rates}
    except RateError as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_currencies() -> Dict[str, Any]:
    """List all currencies that Wise supports for transfers.

    Returns currency codes, full names, and symbols. Use this to discover
    which currencies are available before creating quotes or transfers.

    Returns:
        Dictionary with list of supported currencies (code, name, symbol).
    """
    from bankskills.core.bank.credentials import MissingCredentialError, load_credentials
    from bankskills.core.bank.client import WiseClient
    from bankskills.core.bank.currencies import CurrencyError, fetch_currencies

    try:
        credentials = load_credentials()
    except MissingCredentialError as e:
        return {"success": False, "error": str(e)}

    client = WiseClient(credentials=credentials)

    try:
        currencies = fetch_currencies(client)
        return {"success": True, "currencies": currencies}
    except CurrencyError as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_profile() -> Dict[str, Any]:
    """Get the Wise profile information (personal and/or business).

    Returns profile ID, type (personal or business), full name, and other
    details. Useful for confirming which account is active or retrieving
    your profile ID for other operations.

    Returns:
        Dictionary with list of profiles (id, type, fullName).
    """
    from bankskills.core.bank.credentials import MissingCredentialError, load_credentials
    from bankskills.core.bank.client import WiseClient

    try:
        credentials = load_credentials()
    except MissingCredentialError as e:
        return {"success": False, "error": str(e)}

    client = WiseClient(credentials=credentials)

    resp = client.get("/v2/profiles")
    if resp.status_code != 200:
        return {"success": False, "error": f"Failed to fetch profiles: HTTP {resp.status_code}"}

    return {"success": True, "profiles": resp.json()}


@mcp.tool()
def get_transfer_status(transfer_id: int) -> Dict[str, Any]:
    """Check the current status of a transfer by its ID.

    Use this after send_money to track whether a transfer has been
    completed, is still processing, or has any issues. Returns the
    full transfer details including status, amounts, and rate used.

    Args:
        transfer_id: The numeric transfer ID returned by send_money.

    Returns:
        Dictionary with transfer status, amounts, rate, and creation time.
    """
    from bankskills.core.bank.credentials import MissingCredentialError, load_credentials
    from bankskills.core.bank.client import WiseClient
    from bankskills.core.bank.transfers import TransferStatusError, get_transfer_status as _get_transfer_status

    try:
        credentials = load_credentials()
    except MissingCredentialError as e:
        return {"success": False, "error": str(e)}

    client = WiseClient(credentials=credentials)

    try:
        result = _get_transfer_status(client, transfer_id=transfer_id)
        return {"success": True, "transfer": result}
    except TransferStatusError as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_recipients(
    currency: Optional[str] = None,
    profile_id: Optional[int] = None,
) -> Dict[str, Any]:
    """List saved recipient accounts (people or businesses you've sent money to).

    Returns all saved recipients, optionally filtered by currency. Use the
    returned recipient IDs to quickly send money without re-entering bank
    details. Pairs with send_money and delete_recipient.

    Args:
        currency: Optional currency filter (e.g. "USD", "EUR"). Returns all if omitted.
        profile_id: Optional Wise profile ID. Omit for personal profile, or pass 83191616 for business (Fraction Software LLC).

    Returns:
        Dictionary with list of recipients (id, accountHolderName, currency, type).
    """
    from bankskills.core.bank.credentials import MissingCredentialError, load_credentials
    from bankskills.core.bank.client import WiseClient
    from bankskills.core.bank.recipients import RecipientError, list_recipients as _list_recipients

    try:
        credentials = load_credentials()
    except MissingCredentialError as e:
        return {"success": False, "error": str(e)}

    client = WiseClient(credentials=credentials)

    try:
        recipients = _list_recipients(client, profile_id=str(profile_id) if profile_id else None, currency=currency)
        return {"success": True, "recipients": recipients}
    except RecipientError as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_delivery_estimate(transfer_id: int) -> Dict[str, Any]:
    """Get the estimated delivery time for a transfer.

    Use this after send_money to find out when the recipient should
    expect to receive the funds.

    Args:
        transfer_id: The numeric transfer ID returned by send_money.

    Returns:
        Dictionary with estimated delivery date/time.
    """
    from bankskills.core.bank.credentials import MissingCredentialError, load_credentials
    from bankskills.core.bank.client import WiseClient
    from bankskills.core.bank.transfers import DeliveryEstimateError, get_delivery_estimate as _get_delivery_estimate

    try:
        credentials = load_credentials()
    except MissingCredentialError as e:
        return {"success": False, "error": str(e)}

    client = WiseClient(credentials=credentials)

    try:
        result = _get_delivery_estimate(client, transfer_id=transfer_id)
        return {"success": True, "estimate": result}
    except DeliveryEstimateError as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_quote(
    source_currency: str,
    target_currency: str,
    amount: float,
    profile_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Preview the exchange rate, fees, and delivery estimate for a transfer.

    Use this before send_money to see exactly what a transfer will cost
    without committing to it. The returned rate is locked for 30 minutes.

    Args:
        source_currency: Currency you're sending from (e.g. "USD").
        target_currency: Currency the recipient will receive (e.g. "EUR").
        amount: Amount in source currency to send.
        profile_id: Optional Wise profile ID. Omit for personal profile, or pass 83191616 for business (Fraction Software LLC).

    Returns:
        Dictionary with exchange rate, fee, source/target amounts, estimated
        delivery, and rate expiration time.
    """
    from bankskills.core.bank.credentials import MissingCredentialError, load_credentials
    from bankskills.core.bank.client import WiseClient
    from bankskills.core.bank.quotes import QuoteError, create_quote

    try:
        credentials = load_credentials()
    except MissingCredentialError as e:
        return {"success": False, "error": str(e)}

    client = WiseClient(credentials=credentials)

    try:
        result = create_quote(client, source_currency=source_currency, target_currency=target_currency, amount=amount, profile_id=str(profile_id) if profile_id else None)
        return {"success": True, "quote": result}
    except QuoteError as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def list_transfers(
    status: Optional[str] = None,
    limit: int = 10,
    profile_id: Optional[int] = None,
) -> Dict[str, Any]:
    """List recent transfers (transaction history).

    Returns a list of transfers with their status, amounts, and rates.
    Optionally filter by status. Use this to review past transfers or
    check for pending ones.

    Args:
        status: Optional status filter (e.g. "funds_converted", "cancelled").
        limit: Maximum number of transfers to return (default 10, max 50).
        profile_id: Optional Wise profile ID. Omit for personal profile, or pass 83191616 for business (Fraction Software LLC).

    Returns:
        Dictionary with list of transfers (id, status, amounts, rate, date).
    """
    from bankskills.core.bank.credentials import MissingCredentialError, load_credentials
    from bankskills.core.bank.client import WiseClient
    from bankskills.core.bank.transfers import TransferStatusError, list_transfers as _list_transfers

    try:
        credentials = load_credentials()
    except MissingCredentialError as e:
        return {"success": False, "error": str(e)}

    client = WiseClient(credentials=credentials)

    try:
        transfers = _list_transfers(client, profile_id=str(profile_id) if profile_id else None, status=status, limit=min(limit, 50))
        return {"success": True, "transfers": transfers}
    except TransferStatusError as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def delete_recipient(recipient_id: int) -> Dict[str, Any]:
    """Remove a saved recipient by deactivating them.

    Permanently deactivates the recipient so they no longer appear in
    list_recipients. Cannot be undone — create a new recipient with
    the same details if needed later.

    Args:
        recipient_id: The numeric recipient ID from list_recipients.

    Returns:
        Dictionary confirming deactivation (id, active=False).
    """
    from bankskills.core.bank.credentials import MissingCredentialError, load_credentials
    from bankskills.core.bank.client import WiseClient
    from bankskills.core.bank.recipients import RecipientError, delete_recipient as _delete_recipient

    try:
        credentials = load_credentials()
    except MissingCredentialError as e:
        return {"success": False, "error": str(e)}

    client = WiseClient(credentials=credentials)

    try:
        result = _delete_recipient(client, recipient_id=recipient_id)
        return {"success": True, "recipient": result}
    except RecipientError as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def create_balance(
    currency: str,
    profile_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Open a new currency balance in your Wise multi-currency account.

    You must have a balance in both the source and target currencies
    before you can convert between them. Use this to open a balance
    in a currency you don't have yet (e.g. open a EUR balance before
    converting USD to EUR).

    Safe to call if the balance already exists — Wise will return the
    existing balance.

    Args:
        currency: ISO currency code to open (e.g. "EUR", "GBP", "JPY").
        profile_id: Optional Wise profile ID. Omit for personal profile, or pass 83191616 for business (Fraction Software LLC).

    Returns:
        Dictionary with the created balance (id, currency, type).
    """
    from bankskills.core.bank.credentials import MissingCredentialError, load_credentials
    from bankskills.core.bank.client import WiseClient
    from bankskills.core.bank.balance_convert import CreateBalanceError, create_balance as _create_balance

    try:
        credentials = load_credentials()
    except MissingCredentialError as e:
        return {"success": False, "error": str(e)}

    client = WiseClient(credentials=credentials)

    try:
        result = _create_balance(client, currency=currency, profile_id=str(profile_id) if profile_id else None)
        return {"success": True, "balance": result}
    except CreateBalanceError as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def convert_balance(
    source_currency: str,
    target_currency: str,
    amount: float,
    profile_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Convert money between currencies within your Wise account.

    Moves funds between your own currency balances (e.g. USD -> EUR).
    This does NOT send money to anyone — it converts within your
    multi-currency account at the mid-market rate.

    Both source and target currency balances must exist first. If you
    get an error about the BALANCE payment option being disabled, use
    create_balance to open the target currency balance first.

    Args:
        source_currency: Currency to convert from (e.g. "USD").
        target_currency: Currency to convert to (e.g. "EUR").
        amount: Amount in source currency to convert.
        profile_id: Optional Wise profile ID. Omit for personal profile, or pass 83191616 for business (Fraction Software LLC).

    Returns:
        Dictionary with conversion details (rate, source/target amounts).
    """
    from bankskills.core.bank.credentials import MissingCredentialError, load_credentials
    from bankskills.core.bank.client import WiseClient
    from bankskills.core.bank.balance_convert import ConversionError, convert_balance as _convert_balance

    try:
        credentials = load_credentials()
    except MissingCredentialError as e:
        return {"success": False, "error": str(e)}

    client = WiseClient(credentials=credentials)

    try:
        result = _convert_balance(
            client,
            source_currency=source_currency,
            target_currency=target_currency,
            amount=amount,
            profile_id=str(profile_id) if profile_id else None,
        )
        return {"success": True, "conversion": result}
    except ConversionError as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def save_recipient(
    currency: str,
    recipient_name: str,
    account_number: str,
    recipient_type: str = "iban",
    sort_code: Optional[str] = None,
    routing_number: Optional[str] = None,
    account_type: Optional[str] = None,
    country: Optional[str] = None,
    address: Optional[str] = None,
    city: Optional[str] = None,
    state: Optional[str] = None,
    post_code: Optional[str] = None,
    profile_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Save a new recipient for future transfers.

    Creates and stores a recipient so you can send money to them later
    without re-entering their bank details. Use recipient_type to specify
    the payment method: "iban" for EUR/SEPA, "aba" for USD ACH,
    "sort_code" for GBP.

    Args:
        currency: 3-letter currency code (e.g. "USD", "EUR", "GBP").
        recipient_name: Full name of the recipient.
        account_number: Account number, IBAN, or other identifier.
        recipient_type: Payment type — "iban", "aba", or "sort_code" (default "iban").
        sort_code: UK sort code (required for GBP sort_code type).
        routing_number: US ABA routing number (required for USD aba type).
        account_type: "CHECKING" or "SAVINGS" (for USD, default "CHECKING").
        country: 2-letter country code (required for USD).
        address: Street address (required for USD).
        city: City (required for USD).
        state: State code, e.g. "NY" (optional, for US addresses).
        post_code: ZIP/postal code (required for USD).
        profile_id: Optional Wise profile ID. Omit for personal profile, or pass 83191616 for business (Fraction Software LLC).

    Returns:
        Dictionary with saved recipient details (id, name, currency, type).
    """
    from bankskills.core.bank.credentials import MissingCredentialError, load_credentials
    from bankskills.core.bank.client import WiseClient
    from bankskills.core.bank.recipients import RecipientError, save_recipient as _save_recipient

    try:
        credentials = load_credentials()
    except MissingCredentialError as e:
        return {"success": False, "error": str(e)}

    client = WiseClient(credentials=credentials)

    try:
        result = _save_recipient(
            client,
            currency=currency,
            recipient_name=recipient_name,
            account_number=account_number,
            recipient_type=recipient_type,
            profile_id=str(profile_id) if profile_id else None,
            sort_code=sort_code,
            routing_number=routing_number,
            account_type=account_type,
            country=country,
            address=address,
            city=city,
            state=state,
            post_code=post_code,
        )
        return {"success": True, "recipient": result}
    except RecipientError as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_balance_statement(
    currency: str,
    start_date: str,
    end_date: str,
    profile_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Get a detailed transaction statement for a currency balance.

    Returns all transactions — deposits, withdrawals, conversions,
    card transactions, and fees — for the given date range. This is
    the equivalent of a bank statement.

    Args:
        currency: 3-letter currency code (e.g. "USD").
        start_date: Start of period, ISO-8601 (e.g. "2025-01-01T00:00:00Z").
        end_date: End of period, ISO-8601 (e.g. "2025-01-31T23:59:59Z").
        profile_id: Optional Wise profile ID. Omit for personal profile, or pass 83191616 for business (Fraction Software LLC).

    Returns:
        Dictionary with statement details: currency, date range, opening balance,
        and list of transactions (type, date, amount, running balance, description).
    """
    from bankskills.core.bank.credentials import MissingCredentialError, load_credentials
    from bankskills.core.bank.client import WiseClient
    from bankskills.core.bank.statements import StatementError, get_balance_statement as _get_balance_statement

    try:
        credentials = load_credentials()
    except MissingCredentialError as e:
        return {"success": False, "error": str(e)}

    client = WiseClient(credentials=credentials)

    try:
        result = _get_balance_statement(
            client, currency=currency, start_date=start_date, end_date=end_date,
            profile_id=str(profile_id) if profile_id else None,
        )
        return {"success": True, "statement": result}
    except StatementError as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_activity(
    since: Optional[str] = None,
    until: Optional[str] = None,
    profile_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Get the unified activity feed for your Wise account.

    Returns all recent account actions — transfers, conversions,
    card transactions, deposits, refunds — in chronological order.
    Optionally filter by date range.

    Args:
        since: Optional start timestamp, ISO-8601 (e.g. "2025-01-01T00:00:00Z").
        until: Optional end timestamp, ISO-8601 (e.g. "2025-01-31T23:59:59Z").
        profile_id: Optional Wise profile ID. Omit for personal profile, or pass 83191616 for business (Fraction Software LLC).

    Returns:
        Dictionary with list of activities (type, title, description,
        amount, status, date).
    """
    from bankskills.core.bank.credentials import MissingCredentialError, load_credentials
    from bankskills.core.bank.client import WiseClient
    from bankskills.core.bank.activity import ActivityError, get_activity as _get_activity

    try:
        credentials = load_credentials()
    except MissingCredentialError as e:
        return {"success": False, "error": str(e)}

    client = WiseClient(credentials=credentials)

    try:
        activities = _get_activity(client, profile_id=str(profile_id) if profile_id else None, since=since, until=until)
        return {"success": True, "activities": activities}
    except ActivityError as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def check_balance(
    currency: Optional[str] = None,
    profile_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Check Wise multi-currency balances.

    Args:
        currency: Optional currency filter (e.g. "USD"). Returns all currencies if omitted.
        profile_id: Optional Wise profile ID. Omit for personal profile, or pass 83191616 for business (Fraction Software LLC).

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
        balances = fetch_balances(client, profile_id=str(profile_id) if profile_id else None, currency=currency)
        return {"success": True, "balances": balances}
    except BalanceError as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_receive_details(
    currency: Optional[str] = None,
    profile_id: Optional[int] = None,
) -> Dict[str, Any]:
    """Get account/routing details for receiving payments via Wise.

    Args:
        currency: Optional currency filter (e.g. "USD"). Returns all currencies if omitted.
        profile_id: Optional Wise profile ID. Omit for personal profile, or pass 83191616 for business (Fraction Software LLC).

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
        details = fetch_account_details(client, profile_id=str(profile_id) if profile_id else None, currency=currency)
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
    profile_id: Optional[int] = None,
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
        profile_id: Optional Wise profile ID. Omit for personal profile, or pass 83191616 for business (Fraction Software LLC).

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
            profile_id=str(profile_id) if profile_id else None,
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


# --- Sweeper tools (on-chain token buyback on Base) ---


@mcp.tool()
def create_wallet() -> Dict[str, Any]:
    """Create a new Ethereum wallet for ClawBank Sweeper.

    Saves encrypted keystore to ~/.clawbank/wallet.json.
    No-ops if wallet already exists.

    Returns:
        Dict with address on success, or error on failure.
    """
    try:
        from bankskills.wallet import create_wallet as _create_wallet

        result = _create_wallet()
        return {"success": True, "address": result["address"]}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_wallet() -> Dict[str, Any]:
    """Return the ClawBank wallet address and ETH balance on Base.

    Returns:
        Dict with address and eth_balance on success, or error if wallet does not exist.
    """
    try:
        from bankskills.wallet import WalletError, get_wallet as _get_wallet

        result = _get_wallet()
        return {"success": True, "address": result["address"], "eth_balance": result["eth_balance"]}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def set_target_token(token_address: str) -> Dict[str, Any]:
    """Set the target token for sweeps in sweep.config.

    Args:
        token_address: ERC-20 contract address on Base (0x...).

    Returns:
        Dict with status, token_address, token_symbol on success.
    """
    try:
        from bankskills.sweeper import SweeperError, set_target_token as _set_target_token

        result = _set_target_token(token_address)
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_sweep_config() -> Dict[str, Any]:
    """Return the current sweep configuration and recent sweep log.

    Returns:
        Dict with target_token, token_symbol, network, recent_sweeps.
    """
    try:
        from bankskills.sweeper import get_sweep_config as _get_sweep_config

        result = _get_sweep_config()
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_token_balance(token_address: str) -> Dict[str, Any]:
    """Check ERC-20 token balance for the ClawBank wallet on Base.

    Args:
        token_address: ERC-20 contract address on Base (0x...).

    Returns:
        Dict with token_address, symbol, balance (human-readable), raw_balance on success.
    """
    try:
        from bankskills.sweeper import get_token_balance as _get_token_balance

        result = _get_token_balance(token_address)
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def buy_token(amount_eth: float) -> Dict[str, Any]:
    """Execute a token swap on Base: ETH → target token.

    Uses Uniswap V3. Reserves 0.001 ETH for gas. Requires target token to be set.

    Args:
        amount_eth: Amount of ETH to spend.

    Returns:
        Dict with tx_hash, amount_in, amount_out, status on success.
    """
    try:
        from bankskills.sweeper import buy_token as _buy_token

        result = _buy_token(amount_eth)
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def send_token(
    token_address: str,
    to_address: str,
    amount: float,
) -> Dict[str, Any]:
    """Send ERC-20 tokens or native ETH from the ClawBank wallet.

    Args:
        token_address: ERC-20 contract address on Base, or "ETH"/"native" for raw ETH.
        to_address: Recipient wallet address.
        amount: Amount to send (in token units; decimals handled internally).

    Returns:
        Dict with tx_hash and status on success.
    """
    try:
        from bankskills.sweeper import send_token as _send_token

        result = _send_token(token_address, to_address, amount)
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def export_private_key() -> Dict[str, Any]:
    """Export the ClawBank wallet private key for manual recovery or import into MetaMask.

    Returns:
        Dict with private_key, address, and security warning.
    """
    try:
        from bankskills.wallet import export_private_key as _export_private_key

        result = _export_private_key()
        return {"success": True, **result}
    except Exception as e:
        return {"success": False, "error": str(e)}


def main():
    """Entry point for MCP server."""
    # FastMCP handles server startup
    mcp.run()


if __name__ == "__main__":
    main()

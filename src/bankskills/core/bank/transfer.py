"""Send money via the Wise API (quote -> recipient -> transfer -> fund)."""

from typing import Any, Dict, Optional

from bankskills.core.bank.client import WiseClient
from bankskills.core.bank.profiles import resolve_profile_id


class TransferError(Exception):
    """Raised when any step of the transfer flow fails."""


class InsufficientFundsError(TransferError):
    """Raised when the source balance has insufficient funds."""


def send_money(
    client: WiseClient,
    source_currency: str,
    target_currency: str,
    amount: float,
    recipient_name: str,
    recipient_account: str,
    profile_id: Optional[str] = None,
    recipient_routing_number: Optional[str] = None,
    recipient_country: Optional[str] = None,
    recipient_account_type: Optional[str] = None,
    recipient_address: Optional[str] = None,
    recipient_city: Optional[str] = None,
    recipient_state: Optional[str] = None,
    recipient_post_code: Optional[str] = None,
) -> Dict[str, Any]:
    """Execute the full Wise transfer flow.

    Steps:
        1. Create quote
        2. Get account requirements (Wise's dynamic forms)
        3. Create recipient
        4. Create transfer
        5. Fund transfer from balance

    Args:
        client: Configured WiseClient.
        source_currency: e.g. "USD".
        target_currency: e.g. "EUR".
        amount: Amount to send.
        recipient_name: Full name of recipient.
        recipient_account: Account number or IBAN.
        profile_id: Optional profile ID (resolved automatically).
        recipient_routing_number: Required for USD: 9-digit ABA routing number.
        recipient_country: Two-letter country code (e.g. US, DE). Required for USD ACH.
        recipient_account_type: For USD ACH: CHECKING or SAVINGS (default CHECKING).
        recipient_address: For USD ACH: street address (firstLine). Required for USD.
        recipient_city: For USD ACH: city. Required for USD.
        recipient_state: For USD ACH: state code (e.g. OH, NY). Optional.
        recipient_post_code: For USD ACH: post/ZIP code. Required for USD.

    Returns:
        Dict with transfer id, status, and amount details.

    Raises:
        TransferError: on any API failure.
    """
    pid = resolve_profile_id(client, profile_id or client.credentials.profile_id)

    # Step 1: Create quote
    quote = _create_quote(client, pid, source_currency, target_currency, amount)

    # Step 2: Get account requirements (Wise's dynamic forms approach)
    # This tells us exactly what fields Wise needs for this currency pair
    requirements = _get_account_requirements(
        client,
        source_currency=source_currency,
        target_currency=target_currency,
        amount=amount,
    )
    
    # Step 3: Create recipient using the requirements
    recipient = _create_recipient(
        client,
        pid,
        recipient_name,
        recipient_account,
        target_currency,
        recipient_routing_number=recipient_routing_number,
        recipient_country=recipient_country,
        recipient_account_type=recipient_account_type,
        recipient_address=recipient_address,
        recipient_city=recipient_city,
        recipient_state=recipient_state,
        recipient_post_code=recipient_post_code,
        requirements=requirements,
    )

    # Step 4: Create transfer
    transfer = _create_transfer(client, quote["id"], recipient["id"])

    # Step 5: Fund transfer
    _fund_transfer(client, pid, transfer["id"])

    return {
        "id": transfer["id"],
        "status": transfer.get("status", "processing"),
        "sourceAmount": amount,
        "sourceCurrency": source_currency,
        "targetAmount": quote.get("targetAmount", amount),
        "targetCurrency": target_currency,
    }


def _create_quote(
    client: WiseClient,
    profile_id: str,
    source_currency: str,
    target_currency: str,
    amount: float,
) -> Dict[str, Any]:
    resp = client.post(
        "/v3/profiles/{}/quotes".format(profile_id),
        json_body={
            "sourceCurrency": source_currency,
            "targetCurrency": target_currency,
            "sourceAmount": amount,
            "targetAmount": None,
        },
    )
    if resp.status_code == 401:
        raise TransferError("Authentication failed — check your WISE_API_TOKEN")
    if resp.status_code not in (200, 201):
        raise TransferError(f"Failed to create quote: HTTP {resp.status_code}")
    return resp.json()


def _get_account_requirements(
    client: WiseClient,
    source_currency: str,
    target_currency: str,
    amount: float,
) -> Dict[str, Any]:
    """Fetch account requirements from Wise's dynamic forms API."""
    params = {
        "source": source_currency,
        "target": target_currency,
        "sourceAmount": amount,
    }
    resp = client.get("/v1/account-requirements", params=params)
    if resp.status_code not in (200, 201):
        raise TransferError(f"Failed to fetch account requirements: HTTP {resp.status_code}")
    
    requirements = resp.json()
    
    return requirements


def _looks_like_iban(s: str) -> bool:
    """True if s looks like an IBAN (2 letters, 2 digits, then 11–30 alphanumeric)."""
    s = (s or "").strip().upper()
    if len(s) < 15 or len(s) > 34:
        return False
    if len(s) < 4:
        return False
    return s[0].isalpha() and s[1].isalpha() and s[2].isdigit() and s[3].isdigit() and all(c.isalnum() for c in s[4:])


def _create_recipient(
    client: WiseClient,
    profile_id: str,
    name: str,
    account: str,
    currency: str,
    recipient_routing_number: Optional[str] = None,
    recipient_country: Optional[str] = None,
    recipient_account_type: Optional[str] = None,
    recipient_address: Optional[str] = None,
    recipient_city: Optional[str] = None,
    recipient_state: Optional[str] = None,
    recipient_post_code: Optional[str] = None,
    requirements: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    # Per Wise API: USD ACH requires type "aba", details.abartn (not routingNumber), and full address inside details.
    currency_upper = (currency or "").strip().upper()
    account_clean = (account or "").strip()
    country_clean = (recipient_country or "").strip().upper() or None

    if currency_upper == "USD":
        routing = (recipient_routing_number or "").strip()
        if not routing:
            raise TransferError(
                "USD transfers require a recipient bank account: use --recipient-routing-number "
                "(9-digit ABA) and pass the account number as --recipient-account."
            )
        # Wise requires address for USD ACH (compliance/KYC). Embed address directly in recipient payload.
        first_line = (recipient_address or "").strip()
        city = (recipient_city or "").strip()
        state = (recipient_state or "").strip() if recipient_state else None
        post_code = (recipient_post_code or "").strip()
        if not country_clean:
            raise TransferError(
                "USD ACH requires recipient address: use --recipient-country (e.g. US), "
                "--recipient-address, --recipient-city, --recipient-post-code."
            )
        if not first_line or not city or not post_code:
            raise TransferError(
                "USD ACH requires full recipient address: --recipient-address (street), "
                "--recipient-city, --recipient-post-code."
            )
        account_type = (recipient_account_type or "CHECKING").strip().upper()
        if account_type not in ("CHECKING", "SAVINGS"):
            account_type = "CHECKING"
        
        address_payload = {
            "country": country_clean,
            "city": city,
            "firstLine": first_line,
            "postCode": post_code,
        }
        if state:
            address_payload["state"] = state.upper()
        
        # CRITICAL: address goes INSIDE details for USD ACH, not at top level!
        payload = {
            "profile": int(profile_id),
            "accountHolderName": name,
            "currency": currency_upper,
            "type": "aba",
            "details": {
                "legalType": "PRIVATE",
                "accountNumber": account_clean,
                "abartn": routing,
                "accountType": account_type,
                "address": address_payload,
            },
        }
    elif currency_upper == "EUR" or _looks_like_iban(account_clean):
        if not _looks_like_iban(account_clean):
            raise TransferError(
                "EUR (and most non-USD currencies) require an IBAN: "
                "pass IBAN as --recipient-account."
            )
        # Doc uses details.IBAN (capital) for EUR
        payload = {
            "profile": int(profile_id),
            "accountHolderName": name,
            "currency": currency_upper if currency_upper else "EUR",
            "type": "iban",
            "details": {
                "legalType": "PRIVATE",
                "IBAN": account_clean,
            },
        }
        if country_clean:
            payload["country"] = country_clean
    else:
        raise TransferError(
            f"Unsupported currency or recipient type: {currency_upper}. "
            "Use USD with routing number and account number, or EUR/other currencies with IBAN."
        )

    resp = client.post("/v1/accounts", json_body=payload)
    if resp.status_code == 401:
        raise TransferError("Authentication failed — check your WISE_API_TOKEN")
    if resp.status_code not in (200, 201):
        msg = f"Failed to create recipient: HTTP {resp.status_code}"
        try:
            body = resp.json()
            if isinstance(body, dict):
                err = body.get("errors") or body.get("message") or body.get("errorCode") or body
                msg += f" — {err}"
            else:
                msg += f" — {body}"
        except Exception:
            pass
        raise TransferError(msg)
    return resp.json()


def _create_transfer(
    client: WiseClient,
    quote_id: int,
    recipient_id: int,
) -> Dict[str, Any]:
    import uuid

    resp = client.post(
        "/v1/transfers",
        json_body={
            "targetAccount": recipient_id,
            "quoteUuid": str(quote_id),
            "customerTransactionId": str(uuid.uuid4()),
        },
    )
    if resp.status_code == 401:
        raise TransferError("Authentication failed — check your WISE_API_TOKEN")
    if resp.status_code not in (200, 201):
        msg = f"Failed to create transfer: HTTP {resp.status_code}"
        try:
            body = resp.json()
            if isinstance(body, dict):
                err = body.get("errors") or body.get("message") or body.get("errorCode") or body
                msg += f" — {err}"
            else:
                msg += f" — {body}"
        except Exception:
            pass
        raise TransferError(msg)
    return resp.json()


def _fund_transfer(
    client: WiseClient,
    profile_id: str,
    transfer_id: int,
) -> Dict[str, Any]:
    resp = client.post(
        f"/v3/profiles/{profile_id}/transfers/{transfer_id}/payments",
        json_body={"type": "BALANCE"},
    )
    if resp.status_code == 401:
        raise TransferError("Authentication failed — check your WISE_API_TOKEN")
    if resp.status_code not in (200, 201):
        # Check for insufficient funds in the response body
        body = {}
        try:
            body = resp.json()
        except Exception:
            pass
        error_code = body.get("errorCode", "") or body.get("type", "")
        if "insufficient_funds" in str(error_code).lower():
            raise InsufficientFundsError(
                "Insufficient funds in source balance"
            )
        raise TransferError(f"Failed to fund transfer: HTTP {resp.status_code}")
    # Also check the response body for rejected status
    data = resp.json()
    if data.get("status") == "REJECTED":
        error_code = data.get("errorCode", "")
        if "insufficient_funds" in str(error_code).lower():
            raise InsufficientFundsError(
                "Insufficient funds in source balance"
            )
    return data

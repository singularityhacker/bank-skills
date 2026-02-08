---
name: bank-skill
description: Check balances, send money, and share receive details via Wise
homepage: https://github.com/singularityhacker/bank-skills
metadata: {"openclaw":{"emoji":"🏦","requires":{"bins":["python"],"env":["WISE_API_TOKEN"]},"primaryEnv":"WISE_API_TOKEN"}}
---

# Bank Skill

## Purpose

Gives AI agents banking capabilities via the Wise API. Agents can check multi-currency balances, send money, and retrieve account/routing details for receiving payments.

## Prerequisites

- `WISE_API_TOKEN` environment variable set to a valid Wise API token
- Optional: `WISE_PROFILE_ID` (defaults to first available profile)

## Operations

### 1. Check Balance

**Purpose:** Query Wise multi-currency balances for the configured profile.

**Inputs:**
- `action`: `"balance"` (required)
- `currency`: Currency code filter, e.g. `"USD"` (optional — returns all if omitted)

**Outputs:**
- JSON array of balance objects, each with `currency`, `amount`, and `reservedAmount`

**Usage:**
```bash
echo '{"action": "balance"}' | ./run.sh
echo '{"action": "balance", "currency": "USD"}' | ./run.sh
```

**Example output:**
```json
{
  "success": true,
  "balances": [
    {"currency": "USD", "amount": 1250.00, "reservedAmount": 0.00},
    {"currency": "EUR", "amount": 500.75, "reservedAmount": 10.00}
  ]
}
```

### 2. Get Receive Details

**Purpose:** Retrieve account number, routing number, IBAN, and related info so others can send you payments.

**Inputs:**
- `action`: `"receive-details"` (required)
- `currency`: Currency code, e.g. `"USD"` (optional — returns all if omitted)

**Outputs:**
- JSON object with account holder name, account number, routing number (or IBAN/SWIFT for non-USD), and bank name

**Usage:**
```bash
echo '{"action": "receive-details"}' | ./run.sh
echo '{"action": "receive-details", "currency": "USD"}' | ./run.sh
```

**Example output:**
```json
{
  "success": true,
  "details": [
    {
      "currency": "USD",
      "accountHolder": "Your Business Name",
      "accountNumber": "1234567890",
      "routingNumber": "026073150",
      "bankName": "Community Federal Savings Bank"
    }
  ]
}
```

### 3. Send Money

**Purpose:** Initiate a transfer from your Wise balance to a recipient.

**Inputs:**
- `action`: `"send"` (required)
- `sourceCurrency`: Source currency code, e.g. `"USD"` (required)
- `targetCurrency`: Target currency code, e.g. `"EUR"` (required)
- `amount`: Amount to send as a number (required)
- `recipientName`: Full name of the recipient (required)
- `recipientAccount`: Recipient account number or IBAN (required)

**Additional fields for USD ACH transfers:**
- `recipientRoutingNumber`: 9-digit ABA routing number (required)
- `recipientCountry`: Two-letter country code, e.g. `"US"` (required)
- `recipientAddress`: Street address (required)
- `recipientCity`: City (required)
- `recipientState`: State code, e.g. `"NY"` (required)
- `recipientPostCode`: ZIP/postal code (required)
- `recipientAccountType`: `"CHECKING"` or `"SAVINGS"` (optional, defaults to `"CHECKING"`)

**Outputs:**
- JSON object with transfer ID, status, and confirmation details

**USD ACH Transfer Example:**
```bash
echo '{
  "action": "send",
  "sourceCurrency": "USD",
  "targetCurrency": "USD",
  "amount": 100.00,
  "recipientName": "John Smith",
  "recipientAccount": "123456789",
  "recipientRoutingNumber": "111000025",
  "recipientCountry": "US",
  "recipientAddress": "123 Main St",
  "recipientCity": "New York",
  "recipientState": "NY",
  "recipientPostCode": "10001",
  "recipientAccountType": "CHECKING"
}' | ./run.sh
```

**EUR IBAN Transfer Example (simpler):**
```bash
echo '{
  "action": "send",
  "sourceCurrency": "USD",
  "targetCurrency": "EUR",
  "amount": 100.00,
  "recipientName": "Jane Doe",
  "recipientAccount": "DE89370400440532013000"
}' | ./run.sh
```

**Example output:**
```json
{
  "success": true,
  "transfer": {
    "id": 12345678,
    "status": "processing",
    "sourceAmount": 100.00,
    "sourceCurrency": "USD",
    "targetAmount": 93.50,
    "targetCurrency": "EUR"
  }
}
```

## Failure Modes

- **Missing `WISE_API_TOKEN`:** Returns `{"success": false, "error": "WISE_API_TOKEN environment variable is not set"}`. Set the token and retry.
- **Invalid API token:** Returns `{"success": false, "error": "Authentication failed — check your WISE_API_TOKEN"}`.
- **Insufficient funds:** Returns `{"success": false, "error": "Insufficient funds in USD balance"}`. Check balance before retrying with a smaller amount.
- **Invalid recipient details:** Returns `{"success": false, "error": "Invalid recipient account details"}`. Verify recipient information and retry.
- **Unknown action:** Returns `{"success": false, "error": "Unknown action: <action>"}`. Use one of: `balance`, `receive-details`, `send`.

## When to Use

Use this skill when you need to check bank balances, send money to someone, or share your account details so someone can pay you.

## When Not to Use

- Do not use for crypto transactions (Wise restricts crypto use)
- Do not use with accounts holding significant funds (R&D only)

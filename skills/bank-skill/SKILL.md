---
name: bank-skill
version: 0.1.4
description: Traditional banking via Wise API + on-chain token swaps on Base
homepage: https://github.com/singularityhacker/bank-skills
metadata: {"openclaw":{"emoji":"🏦","requires":{"bins":["python"],"env":["WISE_API_TOKEN"]},"primaryEnv":"WISE_API_TOKEN","optionalEnv":["WISE_PROFILE_ID","CLAWBANK_WALLET_PASSWORD","BASE_RPC_URL"]}}
---

# Bank Skill

## Purpose

Gives AI agents **traditional banking** capabilities (via Wise API) and **on-chain token operations** (via Uniswap on Base). Agents can check balances, send money, retrieve account details, create Ethereum wallets, swap tokens, and send tokens—all through a single skill.

## Prerequisites

**For Banking (Wise API):**
- `WISE_API_TOKEN` environment variable (required)
- Optional: `WISE_PROFILE_ID` (defaults to first available profile)

**For Token Operations (Base Network):**
- Optional: `CLAWBANK_WALLET_PASSWORD` (wallet keystore password, defaults to "clawbank-default")
- Optional: `BASE_RPC_URL` (Base RPC endpoint, defaults to https://mainnet.base.org)

## Operations

### Banking Operations (Wise API)

#### 1. Check Balance

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

#### 2. Get Receive Details

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

#### 3. Send Money

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

### Token Operations (Base Network)

#### 4. Create Wallet

**Purpose:** Generate a new Ethereum wallet for token operations on Base.

**Inputs:**
- `action`: `"create-wallet"` (required)

**Outputs:**
- Wallet address (keystore saved to `~/.clawbank/wallet.json`)

**Usage:**
```bash
echo '{"action": "create-wallet"}' | ./run.sh
```

#### 5. Get Wallet

**Purpose:** Get current wallet address and ETH balance on Base.

**Inputs:**
- `action`: `"get-wallet"` (required)

**Outputs:**
- Wallet address and ETH balance

**Usage:**
```bash
echo '{"action": "get-wallet"}' | ./run.sh
```

#### 6. Set Target Token

**Purpose:** Set the target token address for swaps.

**Inputs:**
- `action`: `"set-target-token"` (required)
- `tokenAddress`: ERC-20 contract address on Base (required)

**Usage:**
```bash
echo '{"action": "set-target-token", "tokenAddress": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"}' | ./run.sh
```

#### 7. Get Sweep Config

**Purpose:** View current target token and swap history.

**Inputs:**
- `action`: `"get-sweep-config"` (required)

**Usage:**
```bash
echo '{"action": "get-sweep-config"}' | ./run.sh
```

#### 8. Get Token Balance

**Purpose:** Check ERC-20 token balance for the wallet.

**Inputs:**
- `action`: `"get-token-balance"` (required)
- `tokenAddress`: ERC-20 contract address (required)

**Usage:**
```bash
echo '{"action": "get-token-balance", "tokenAddress": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"}' | ./run.sh
```

#### 9. Buy Token

**Purpose:** Swap ETH for any token on Base via Uniswap (universal V3+V4 support).

**Inputs:**
- `action`: `"buy-token"` (required)
- `amountEth`: Amount of ETH to swap (required)

**Outputs:**
- Transaction hash, amount in, amount out, status

**Usage:**
```bash
echo '{"action": "buy-token", "amountEth": 0.001}' | ./run.sh
```

**Supported tokens:** Any ERC-20 with WETH liquidity on Base (USDC, DAI, WBTC, ClawBank, etc.)

#### 10. Send Token

**Purpose:** Send ERC-20 tokens or native ETH from the wallet.

**Inputs:**
- `action`: `"send-token"` (required)
- `tokenAddress`: ERC-20 contract address, or "ETH" for native ETH (required)
- `toAddress`: Recipient wallet address (required)
- `amount`: Amount to send in token units (required)

**Usage:**
```bash
echo '{"action": "send-token", "tokenAddress": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "toAddress": "0x...", "amount": 5.0}' | ./run.sh
```

#### 11. Export Private Key

**Purpose:** Export wallet's private key for recovery or import.

**Inputs:**
- `action`: `"export-private-key"` (required)

**Outputs:**
- Private key (hex string) and wallet address

**Usage:**
```bash
echo '{"action": "export-private-key"}' | ./run.sh
```

## Failure Modes

**Banking Operations:**
- **Missing `WISE_API_TOKEN`:** Returns `{"success": false, "error": "WISE_API_TOKEN environment variable is not set"}`. Set the token and retry.
- **Invalid API token:** Returns `{"success": false, "error": "Authentication failed — check your WISE_API_TOKEN"}`.
- **Insufficient funds:** Returns `{"success": false, "error": "Insufficient funds in USD balance"}`. Check balance before retrying.
- **Invalid recipient details:** Returns `{"success": false, "error": "Invalid recipient account details"}`.

**Token Operations:**
- **No wallet:** Returns `{"success": false, "error": "Wallet does not exist. Call create-wallet first"}`.
- **Insufficient ETH:** Returns `{"success": false, "error": "Insufficient balance. Have X ETH, need Y + 0.001 for gas"}`.
- **No target token set:** Returns `{"success": false, "error": "No target token set. Call set-target-token first"}`.
- **No liquidity pool:** Returns `{"success": false, "error": "No liquidity pool found for [token]"}`.
- **Unknown action:** Returns `{"success": false, "error": "Unknown action: <action>"}`. See Operations section for valid actions.

## When to Use

**Banking:** Check balances, send international transfers, share account details for receiving payments

**Token Operations:** Create wallets, swap tokens on Base (any token with Uniswap liquidity), send tokens, track balances

## When Not to Use

- Do not use Wise for crypto on/off-ramps (Wise restricts crypto)
- Do not use with accounts holding significant funds (R&D only)
- Token operations require Base network access and ETH for gas

## Technical Details

**Token Swap Implementation:**
- Hybrid V3+V4 routing (tries V3 first, falls back to V4 for tokens with hooks)
- Supports any token with WETH liquidity on Base
- Automatic fee tier detection (0.05%, 0.3%, 1%)
- Gas costs: ~250k (V3) or ~450k (V4)

**Security:**
- Wallet keystore encrypted with password
- Private keys never logged or exposed
- All transactions signed locally
- No external API calls for token operations (direct blockchain interaction)

# Bank Skills

A skill pack that gives AI agents banking capabilities via the [Wise API](https://docs.wise.com/api-reference). Agents can check balances, send money, and share account and routing details for receiving payments—all through a standard skill package (SKILL.md + run.sh) compatible with CLI and MCP.

## Features

- **Check balances** — Query Wise multi-currency balances for the configured profile
- **Send money** — Initiate transfers (quote → recipient → transfer → fund flow)
- **Share receive details** — Retrieve account number, routing number, IBAN, and related info so agents can share them for inbound payments

## Prerequisites

1. A [Wise](https://wise.com) personal account
2. A Wise **business** account (required for API access)
3. API token generated from Settings → API tokens (2FA required)

## Setup

Configure credentials via environment variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `WISE_API_TOKEN` | Yes | Personal API token from Wise dashboard |
| `WISE_PROFILE_ID` | No | Profile ID (defaults to first available) |

The skill reads credentials from the environment at runtime. Do not store tokens in config files that other skills might access.

## Security & API Key Management

### How API Keys Are Stored

This skill follows the standard convention used across the skills ecosystem: **API keys are never stored in the skill code**. Instead, they're read from environment variables at runtime.

**Storage varies by deployment method:**

| Method | Storage Location | Security |
|--------|-----------------|----------|
| **Claude Desktop (.mcpb)** | OS credential manager (Keychain/Windows Credential Manager) | ✅ Encrypted, secure |
| **CLI / Direct Usage** | Shell environment (`export WISE_API_TOKEN='...'`) | ⚠️ User-managed |
| **OpenClaw/ClawdBot** | `~/.openclaw/openclaw.json` under `skills.entries.bank-skill.env` | ⚠️ File permissions |
| **MCP Server** | Shell environment | ⚠️ User-managed |

**The skill's responsibility:** 
- ✅ Read from `WISE_API_TOKEN` environment variable
- ✅ Fail gracefully with clear error if missing
- ✅ Never log or expose the token value
- ✅ Declare requirements in SKILL.md metadata

**Your responsibility:**
- Set the environment variable before running
- Keep your API token secure
- Don't commit tokens to version control

### Wise API Security Features

Wise provides additional security controls for API tokens:

- **IP Address Whitelisting** — Restrict API token usage to specific IP addresses in your Wise dashboard (Settings → API Tokens). This prevents unauthorized access even if your token is compromised.
- **2FA Required** — Token generation requires two-factor authentication
- **Token Scopes** — Business accounts can create tokens with limited permissions
- **Token Rotation** — Generate new tokens and revoke old ones at any time

**Recommended:** Enable IP whitelisting for production use to limit token usage to your server/workstation IP addresses.

## Surfaces

- **MCP Desktop Extension** — .mcpb bundle for Claude Desktop (double-click install)
- **Skill package** — SKILL.md + run.sh for agent discovery and invocation
- **CLI** — Terminal commands for testing and scripting
- **MCP Server** — Standalone server for MCP-compatible frameworks

## Quick Start

### For Claude Desktop Users (MCP Extension)

**Requirements:**
- Claude Desktop 1.1+ with UV runtime support
- Wise Business Account with API access
- macOS, Windows, or Linux (no manual setup needed)

**Installation:**

1. **Download** `dist/bank-skills-0.1.0.mcpb` (110KB)
2. **Install** - Double-click the file OR Settings → Extensions → Install Extension
3. **Configure** - Enter your Wise API token in the settings UI (stored securely in Keychain)
4. **Restart** Claude Desktop
5. **Test** - Ask Claude: "Check my Wise balance"

**Getting Your API Token:**

1. Log in to your [Wise Business Account](https://wise.com)
2. Go to Settings → API Tokens
3. Create a new token (requires 2FA)
4. Copy and paste into Claude Desktop extension settings

**Available Tools:**
- `check_balance` - Query Wise balances
- `get_receive_details` - Get account/routing details for receiving payments
- `send_money` - Initiate transfers

**Test Prompts:**
```
"Check my Wise balance"
"What are my USD account details for receiving money?"
"Send $10 to John Smith at account 123456789, routing 111000025..."
```

**Troubleshooting:**
- If tools don't appear: restart Claude Desktop completely
- If you get "not configured" error: verify API token is set in Settings → Extensions
- For transfer errors: ensure you provide all required fields (routing number, address, etc. for USD)

### For Developers / CLI Users

```bash
# Install dependencies
uv sync

# Set your API token
export WISE_API_TOKEN='your-api-key-here'

# Check balances
uv run python -m bankskills.cli.bank.main balance

# Get receive details (account/routing info)
uv run python -m bankskills.cli.bank.main receive-details

# Send money (USD ACH example)
uv run python -m bankskills.cli.bank.main send \
  --source-currency USD --target-currency USD \
  --amount 10.00 \
  --recipient-name "John Smith" \
  --recipient-account "123456789" \
  --recipient-routing-number "111000025" \
  --recipient-country US \
  --recipient-address "123 Main St" \
  --recipient-city "New York" \
  --recipient-state NY \
  --recipient-post-code "10001"
```

## CLI Usage

### Check Balances

```bash
# All currencies
uv run python -m bankskills.cli.bank.main balance

# JSON output
uv run python -m bankskills.cli.bank.main balance --json

# Filter by currency
uv run python -m bankskills.cli.bank.main balance --currency USD
```

### Get Receive Details

```bash
# All currencies
uv run python -m bankskills.cli.bank.main receive-details

# Filter by currency
uv run python -m bankskills.cli.bank.main receive-details --currency USD --json
```

### Send Money

**USD ACH Transfer:**

```bash
uv run python -m bankskills.cli.bank.main send \
  --source-currency USD --target-currency USD \
  --amount 10.00 \
  --recipient-name "Recipient Name" \
  --recipient-account "123456789" \
  --recipient-routing-number "111000025" \
  --recipient-country US \
  --recipient-address "123 Main St" \
  --recipient-city "New York" \
  --recipient-state NY \
  --recipient-post-code "10001" \
  --recipient-account-type CHECKING
```

**EUR IBAN Transfer:**

```bash
uv run python -m bankskills.cli.bank.main send \
  --source-currency USD --target-currency EUR \
  --amount 10.00 \
  --recipient-name "Recipient Name" \
  --recipient-account "DE89370400440532013000"
```

## Skill Package Usage

The skill can be invoked via `run.sh` with JSON input:

```bash
# Balance
echo '{"action": "balance"}' | skills/bank-skill/run.sh

# Receive details
echo '{"action": "receive-details", "currency": "USD"}' | skills/bank-skill/run.sh

# Send money
echo '{
  "action": "send",
  "sourceCurrency": "USD",
  "targetCurrency": "USD",
  "amount": 10.0,
  "recipientName": "Recipient Name",
  "recipientAccount": "123456789",
  "recipientRoutingNumber": "111000025",
  "recipientCountry": "US",
  "recipientAddress": "123 Main St",
  "recipientCity": "New York",
  "recipientState": "NY",
  "recipientPostCode": "10001"
}' | skills/bank-skill/run.sh
```

## MCP Server

Start the MCP server:

```bash
export WISE_API_TOKEN='your-api-key-here'
uv run python -m bankskills.mcp.server
```

Available tools:
- `check_balance` — Query Wise balances
- `get_receive_details` — Get account/routing details
- `send_money` — Initiate transfers

## Running Tests

```bash
uv run pytest tests/ -v
```

## Development

The project structure:

```
bank-skills/
├── src/bankskills/           # Core implementation (primary source)
│   ├── cli/bank/             # CLI commands
│   ├── core/bank/            # Wise API client & operations
│   ├── mcp/                  # MCP server
│   └── runtime/              # Skill runner
├── skills/bank-skill/        # Packaged skill (self-contained)
│   ├── bankskills/           # Copy of src/bankskills/ (synced)
│   ├── SKILL.md              # Skill documentation
│   └── run.sh                # Skill entry point
├── scripts/                  # Build and sync scripts
│   └── sync-skill-code.sh    # Sync src/ to skills/
├── tests/                    # Test suite
└── publish/                  # Build/bundle scripts
```

### Making Code Changes

After editing code in `src/bankskills/`, sync it to the skill package:

```bash
./scripts/sync-skill-code.sh
```

This ensures the self-contained skill in `skills/bank-skill/` stays up to date.

See [DEVELOPMENT-WORKFLOW.md](DEVELOPMENT-WORKFLOW.md) for the complete development guide.

## Disclaimer

Banking is heavily regulated and requires KYC. You must create a business bank account and assume full liability. This project is for **R&D and exploration only**.

- Use at your own risk
- Do not use a personal bank account
- Do not connect an agent to an account holding significant funds
- Wise restricts crypto use; avoid crypto on/off-ramps
- Automation may conflict with Wise's terms of service—review before use

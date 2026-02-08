# MCP Desktop Extension Installation

**Bank Skills** is available as a Claude Desktop Extension (.mcpb) for easy installation.

## Quick Install

### Method 1: Double-Click (Easiest)

1. Download `dist/bank-skills-0.1.0.mcpb`
2. Double-click the file
3. Claude Desktop will open and prompt you to install
4. Enter your Wise API token when prompted
5. Restart Claude Desktop

### Method 2: Via Claude Desktop Settings

1. Open Claude Desktop
2. Go to **Settings** → **Extensions**
3. Click **Install Extension…**
4. Select `bank-skills-0.1.0.mcpb`
5. Enter your Wise API token in the settings UI
6. Restart Claude Desktop

## Getting Your API Token

1. Log in to your [Wise Business Account](https://wise.com)
2. Go to **Settings** → **API Tokens**
3. Create a new token (requires 2FA)
4. Copy the token
5. Paste it into Claude Desktop's extension settings

**Important:** The API token is stored securely in your macOS Keychain (not in plaintext).

## Verify Installation

After restarting Claude Desktop:

1. Open a new chat
2. Click the **+** button or check the connectors menu
3. You should see these tools available:
   - `check_balance` - Query Wise balances
   - `get_receive_details` - Get account/routing details
   - `send_money` - Initiate transfers

## Test the Tools

Try these prompts:

```
"Check my Wise balance"
"What are my USD account details for receiving money?"
"Send $5 to John Smith..."
```

Claude will use the appropriate tools automatically.

## Requirements

- **Claude Desktop** version 1.1 or later (with UV runtime support)
- **Wise Business Account** with API access
- **macOS, Windows, or Linux** (Python and dependencies managed automatically by uv)
- No manual setup needed - everything is handled automatically!

## Troubleshooting

### Tools don't appear after install

1. Restart Claude Desktop completely (quit and reopen)
2. Check Settings → Extensions → Bank Skills - verify API token is set
3. Look for errors in Claude Desktop's developer logs

### "WISE_API_TOKEN not configured" error

1. Open Settings → Extensions → Bank Skills
2. Enter your API token in the field
3. Click Save
4. Restart Claude Desktop

### Transfer fails with "insufficient funds"

Check your balance first with `check_balance` tool. Ensure you have enough in the source currency.

### Transfer fails with "Invalid recipient details"

For USD transfers, you must provide:
- Routing number (9 digits)
- Account number
- Full address (street, city, state, postal code)
- Country code ("US")

For EUR transfers, you only need the recipient's IBAN.

## Security Notes

- Your API token is stored in macOS Keychain (secure storage)
- The server never logs or displays your API token
- All banking operations use HTTPS
- This is for R&D/exploration only - don't use with accounts holding significant funds

## Uninstalling

1. Open Claude Desktop Settings → Extensions
2. Find "Bank Skills"
3. Click Remove
4. Your API token will be deleted from Keychain

## Technical Details

- **Runtime:** UV runtime (manages Python and dependencies automatically)
- **Protocol:** MCP via stdio transport
- **Dependencies:** fastmcp, httpx (installed automatically by uv)
- **Bundle size:** 12KB
- **Manifest version:** 0.4 (UV runtime support)
- **API:** Wise Production API (https://api.wise.com)

## Support

- GitHub: https://github.com/singularityhacker/bank-skills
- Issues: https://github.com/singularityhacker/bank-skills/issues

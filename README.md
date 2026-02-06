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
| `WISE_ENV` | No | `sandbox` or `production` (default: `production`) |

The skill reads credentials from the environment at runtime. Do not store tokens in config files that other skills might access.

## Surfaces

- **Skill package** — SKILL.md + run.sh for agent discovery and invocation
- **CLI** — Terminal commands for testing and scripting
- **MCP** — Tools exposed for MCP-compatible agent frameworks

## Sandbox

Use `WISE_ENV=sandbox` to test against [Wise Sandbox](https://wise-sandbox.com) without real funds. Sandbox accounts come pre-funded with test credit.

---

## Disclaimer

Banking is heavily regulated and requires KYC. You must create a business bank account and assume full liability. This project is for **R&D and exploration only**.

- Use at your own risk
- Do not use a personal bank account
- Do not connect an agent to an account holding significant funds
- Wise restricts crypto use; avoid crypto on/off-ramps
- Automation may conflict with Wise's terms of service—review before use

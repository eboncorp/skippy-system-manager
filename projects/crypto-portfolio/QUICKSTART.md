# Claude Code Integration - Quick Start Guide

This guide gets you up and running with the Crypto Portfolio MCP server in Claude Code in under 5 minutes.

## Prerequisites

- Python 3.10+
- Claude Code installed
- At least one exchange API key (read-only recommended)

## Step 1: Install Dependencies

```bash
cd crypto-portfolio-analyzer
pip install -r requirements.txt
```

## Step 2: Configure API Keys

```bash
# Copy the example config
cp .env.example .env

# Edit with your keys (use your preferred editor)
nano .env
```

At minimum, add one exchange:

```env
PAPER_TRADING=true
COINBASE_API_KEY=your_key_here
COINBASE_API_SECRET=your_secret_here
```

## Step 3: Test the MCP Server

```bash
# Test that it starts without errors
python crypto_portfolio_mcp.py --help

# You should see:
# usage: crypto_portfolio_mcp.py [-h] [--http] [--port PORT]
```

## Step 4: Configure Claude Code

Create or edit `~/.config/claude-code/mcp.json`:

```json
{
  "mcpServers": {
    "crypto-portfolio": {
      "command": "python",
      "args": ["/full/path/to/crypto_portfolio_mcp.py"],
      "env": {
        "PAPER_TRADING": "true",
        "COINBASE_API_KEY": "your_key",
        "COINBASE_API_SECRET": "your_secret"
      }
    }
  }
}
```

> **Important**: Replace `/full/path/to/` with the actual path to your installation.

## Step 5: Restart Claude Code

Close and reopen Claude Code to load the new MCP server.

## Step 6: Test It Out!

In Claude Code, try these queries:

```
"Show me my portfolio summary"

"What are my staking positions?"

"Run an AI analysis of my portfolio"

"Calculate my BTC cost basis using FIFO"
```

## Troubleshooting

### "Server not found" error

1. Verify the path in your mcp.json is correct
2. Run the server manually to check for import errors:
   ```bash
   python /path/to/crypto_portfolio_mcp.py
   ```

### "Authentication failed" 

1. Double-check API keys in your config
2. Ensure the keys have "View" or "Read" permissions enabled
3. Check if IP whitelisting is blocking the connection

### "No data returned"

1. Verify `PAPER_TRADING=true` is set (uses mock data)
2. For real data, ensure exchange has funds/positions

## Available Tools

| Ask Claude Code... | Tool Used |
|-------------------|-----------|
| "portfolio summary" | `crypto_portfolio_summary` |
| "holdings on Coinbase" | `crypto_exchange_holdings` |
| "staking rewards" | `crypto_staking_positions` |
| "DeFi positions" | `crypto_defi_positions` |
| "analyze my portfolio" | `crypto_ai_analysis` |
| "calculate taxes" | `crypto_cost_basis` |
| "arbitrage opportunities" | `crypto_arbitrage_opportunities` |
| "transaction history" | `crypto_transaction_history` |
| "my alerts" | `crypto_alerts_status` |
| "DCA bot status" | `crypto_dca_bot_status` |

## Pro Tips

### Get JSON Output for Further Analysis

```
"Give me my portfolio summary in JSON format"
```

Claude Code can then process the structured data programmatically.

### Combine with Other Analysis

```
"Get my portfolio summary, then create a pie chart of my allocation"
```

### Export Tax Reports

```
"Calculate my 2024 cost basis using HIFO and save to a CSV file"
```

### Monitor Specific Assets

```
"Show me all my ETH holdings across exchanges including staking and DeFi"
```

## Security Reminders

- ✅ Use read-only API keys when possible
- ✅ Enable `PAPER_TRADING=true` while testing  
- ✅ Enable IP whitelisting on exchanges
- ❌ Never share API keys or commit to git
- ❌ Don't enable withdrawal permissions unless absolutely needed

---

Need help? Check the full [README.md](README.md) for detailed documentation.

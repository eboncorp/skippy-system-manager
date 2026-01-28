# Crypto Portfolio Analyzer

A comprehensive multi-exchange cryptocurrency portfolio management suite with AI-powered analysis, staking support, DeFi tracking, and Claude Code integration via MCP.

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Command Line](#command-line)
  - [Claude Code Integration](#claude-code-integration)
  - [API Reference](#api-reference)
- [Modules](#modules)
- [Security](#security)
- [Development](#development)
- [Troubleshooting](#troubleshooting)

---

## Features

### Multi-Exchange Support
- **Coinbase** - Full trading, staking, and advanced orders
- **Kraken** - Spot trading, margin, staking, and futures
- **Crypto.com** - Trading, staking, and earn products
- **Gemini** - Trading, ActiveTrader, and earn

### Portfolio Management
- Real-time portfolio valuation across all exchanges
- Historical portfolio snapshots with configurable intervals
- Asset allocation tracking and visualization
- Performance metrics (returns, Sharpe ratio, max drawdown)

### Staking & Rewards
- Unified staking interface across all exchanges
- APY tracking and comparison
- Reward accumulation monitoring
- Lock period and unbonding status

### DeFi Integration
- **Aave** - Lending/borrowing positions with health factor monitoring
- **Uniswap** - Liquidity positions with impermanent loss tracking
- **Lido** - Liquid staking (stETH) positions
- **Compound** - Supply/borrow tracking
- **Curve** - LP positions and gauge rewards

### Tax & Compliance
- Cost basis calculation (FIFO, LIFO, HIFO, Average)
- Tax lot tracking with acquisition dates
- Short-term vs long-term gains classification
- Export-ready tax reports

### Automation
- Multi-exchange DCA bots
- Price and portfolio alerts
- Cross-exchange arbitrage detection
- Notification system (email, SMS, webhooks)

### AI Analysis
- Portfolio health scoring
- Risk assessment and recommendations
- Rebalancing suggestions
- Tax optimization strategies
- Performance attribution

### Claude Code Integration
- MCP server for seamless Claude Code access
- Structured JSON output for programmatic analysis
- Natural language portfolio queries
- Automated reporting and insights

---

## Architecture

```
crypto-portfolio-analyzer/
├── crypto_portfolio_mcp.py    # MCP server for Claude Code
├── main.py                    # CLI entry point
├── config.py                  # Configuration management
├── requirements.txt           # Python dependencies
│
├── exchanges/                 # Exchange API integrations
│   ├── __init__.py
│   ├── base.py               # Abstract exchange interface
│   ├── coinbase.py           # Coinbase Pro/Advanced Trade
│   ├── kraken.py             # Kraken Spot & Futures
│   ├── crypto_com.py         # Crypto.com Exchange
│   └── gemini.py             # Gemini Exchange
│
├── staking/                   # Staking module
│   ├── __init__.py
│   ├── manager.py            # Unified staking interface
│   ├── coinbase_staking.py
│   ├── kraken_staking.py
│   └── rewards_tracker.py
│
├── defi/                      # DeFi protocol integrations
│   ├── __init__.py
│   ├── aave.py               # Aave V3 integration
│   ├── uniswap.py            # Uniswap V3 positions
│   ├── lido.py               # Lido liquid staking
│   └── on_chain.py           # Generic on-chain queries
│
├── analysis/                  # Analysis engines
│   ├── __init__.py
│   ├── portfolio.py          # Portfolio calculations
│   ├── cost_basis.py         # Tax lot tracking
│   ├── performance.py        # Performance metrics
│   ├── risk.py               # Risk calculations
│   └── ai_analysis.py        # AI-powered insights
│
├── automation/                # Automation features
│   ├── __init__.py
│   ├── dca_bot.py            # Dollar cost averaging
│   ├── alerts.py             # Price/portfolio alerts
│   ├── arbitrage.py          # Arbitrage scanner
│   └── notifications.py      # Notification dispatch
│
├── storage/                   # Data persistence
│   ├── __init__.py
│   ├── database.py           # SQLite/PostgreSQL
│   ├── snapshots.py          # Historical snapshots
│   └── cache.py              # Redis caching
│
└── tests/                     # Test suite
    ├── __init__.py
    ├── test_exchanges.py
    ├── test_staking.py
    ├── test_defi.py
    └── test_analysis.py
```

---

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager
- (Optional) Redis for caching
- (Optional) PostgreSQL for production storage

### Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/crypto-portfolio-analyzer.git
cd crypto-portfolio-analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Copy example config
cp .env.example .env

# Edit configuration with your API keys
nano .env
```

### Dependencies

```txt
# requirements.txt
httpx>=0.25.0
pydantic>=2.0.0
python-dotenv>=1.0.0
aiohttp>=3.9.0
websockets>=12.0
sqlalchemy>=2.0.0
alembic>=1.13.0
redis>=5.0.0
web3>=6.0.0
mcp>=0.1.0
rich>=13.0.0
typer>=0.9.0
pandas>=2.0.0
numpy>=1.24.0
```

---

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# =============================================================================
# GENERAL SETTINGS
# =============================================================================
PAPER_TRADING=true              # Enable paper trading mode (recommended for testing)
LOG_LEVEL=INFO                  # DEBUG, INFO, WARNING, ERROR
DATABASE_URL=sqlite:///portfolio.db

# =============================================================================
# EXCHANGE API KEYS
# =============================================================================
# Coinbase
COINBASE_API_KEY=your_api_key
COINBASE_API_SECRET=your_api_secret
COINBASE_PASSPHRASE=your_passphrase  # For Pro API

# Kraken
KRAKEN_API_KEY=your_api_key
KRAKEN_API_SECRET=your_api_secret

# Crypto.com
CRYPTO_COM_API_KEY=your_api_key
CRYPTO_COM_API_SECRET=your_api_secret

# Gemini
GEMINI_API_KEY=your_api_key
GEMINI_API_SECRET=your_api_secret

# =============================================================================
# WALLET ADDRESSES (for DeFi tracking)
# =============================================================================
ETH_WALLET_1=0x742d35Cc6634C0532925a3b844Bc9e7595f8e2f8
ETH_WALLET_2=0x...

# =============================================================================
# NOTIFICATIONS (optional)
# =============================================================================
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
NOTIFICATION_EMAIL=alerts@yourdomain.com

TWILIO_SID=your_twilio_sid
TWILIO_TOKEN=your_twilio_token
TWILIO_FROM=+1234567890
NOTIFICATION_PHONE=+1987654321

WEBHOOK_URL=https://your-webhook-endpoint.com/alerts

# =============================================================================
# OPTIONAL SERVICES
# =============================================================================
REDIS_URL=redis://localhost:6379/0
ETHERSCAN_API_KEY=your_etherscan_key
COINGECKO_API_KEY=your_coingecko_key  # For price data fallback
```

### API Key Permissions

For security, create API keys with minimal required permissions:

| Exchange | Required Permissions |
|----------|---------------------|
| Coinbase | View, Trade (if trading), Withdraw (if staking) |
| Kraken | Query Funds, Query Open Orders, Query Closed Orders |
| Crypto.com | Read (trading requires additional permissions) |
| Gemini | Fund Management (Auditor role for read-only) |

> ⚠️ **Security Warning**: Never enable withdrawal permissions unless absolutely necessary. Always use IP whitelisting when available.

---

## Usage

### Command Line

```bash
# View portfolio summary
python main.py portfolio summary

# View holdings by exchange
python main.py holdings --exchange coinbase

# View staking positions
python main.py staking list

# Run AI analysis
python main.py analyze --type comprehensive

# Calculate cost basis
python main.py tax cost-basis --method fifo --year 2024

# Check arbitrage opportunities
python main.py arbitrage scan --min-spread 0.5

# Manage DCA bots
python main.py dca list
python main.py dca create --asset BTC --amount 100 --frequency weekly

# View alerts
python main.py alerts list
```

### Claude Code Integration

The MCP server enables Claude Code to interact with your portfolio directly.

#### Setup

1. **Install the MCP server:**

```bash
# Install in development mode
pip install -e .

# Or install the mcp package
pip install mcp
```

2. **Configure Claude Code:**

Add to your Claude Code MCP configuration (`~/.config/claude-code/mcp.json` or project-level `.claude/mcp.json`):

```json
{
  "mcpServers": {
    "crypto-portfolio": {
      "command": "python",
      "args": ["/path/to/crypto-portfolio-analyzer/crypto_portfolio_mcp.py"],
      "env": {
        "PAPER_TRADING": "true",
        "COINBASE_API_KEY": "${COINBASE_API_KEY}",
        "COINBASE_API_SECRET": "${COINBASE_API_SECRET}",
        "KRAKEN_API_KEY": "${KRAKEN_API_KEY}",
        "KRAKEN_API_SECRET": "${KRAKEN_API_SECRET}"
      }
    }
  }
}
```

3. **Test the connection:**

```bash
# Start Claude Code and verify the server is loaded
claude-code

# In Claude Code, you can now ask:
# "Show me my portfolio summary"
# "What's my cost basis for BTC using FIFO?"
# "Are there any arbitrage opportunities?"
```

#### Available MCP Tools

| Tool | Description |
|------|-------------|
| `crypto_portfolio_summary` | Get comprehensive portfolio overview |
| `crypto_exchange_holdings` | View holdings by exchange |
| `crypto_staking_positions` | View staking positions and rewards |
| `crypto_defi_positions` | View DeFi protocol positions |
| `crypto_ai_analysis` | Run AI-powered portfolio analysis |
| `crypto_cost_basis` | Calculate tax lots and cost basis |
| `crypto_arbitrage_opportunities` | Scan for price discrepancies |
| `crypto_transaction_history` | Query transaction records |
| `crypto_alerts_status` | View alert configuration and triggers |
| `crypto_dca_bot_status` | Check DCA bot status and performance |

#### Example Claude Code Queries

```
"Give me a summary of my crypto portfolio including staking"

"What's my unrealized profit/loss on ETH?"

"Calculate my 2024 tax obligations using HIFO method"

"Are there any arbitrage opportunities above 0.5% spread?"

"Run a comprehensive AI analysis and give me recommendations"

"Show my transaction history for BTC in January 2024"

"What are my DeFi positions on Aave?"
```

### API Reference

#### Portfolio Summary

```python
from analysis.portfolio import PortfolioAnalyzer

analyzer = PortfolioAnalyzer()
summary = await analyzer.get_summary(
    include_staking=True,
    include_defi=True
)

print(f"Total Value: ${summary['total_value_usd']:,.2f}")
print(f"24h Change: {summary['change_24h_percent']:.2f}%")
```

#### Cost Basis Calculation

```python
from analysis.cost_basis import CostBasisCalculator

calculator = CostBasisCalculator(method='fifo')
report = await calculator.calculate(
    asset='BTC',
    tax_year=2024
)

print(f"Cost Basis: ${report['total_cost_basis']:,.2f}")
print(f"Unrealized Gain: ${report['unrealized_gain']:,.2f}")
```

#### AI Analysis

```python
from analysis.ai_analysis import AIAnalyzer

ai = AIAnalyzer()
analysis = await ai.analyze(
    analysis_type='comprehensive',
    time_range_days=30,
    include_recommendations=True
)

print(f"Health Score: {analysis['portfolio_health_score']}/100")
for rec in analysis['recommendations']:
    print(f"[{rec['priority'].upper()}] {rec['action']}")
```

---

## Modules

### Exchange Module

The exchange module provides a unified interface for interacting with different cryptocurrency exchanges.

```python
from exchanges import get_exchange

# Get exchange instance
coinbase = await get_exchange('coinbase')

# Fetch balances
balances = await coinbase.get_balances()

# Place order (requires trading permissions)
if not PAPER_TRADING:
    order = await coinbase.place_order(
        symbol='BTC-USD',
        side='buy',
        amount=0.01,
        order_type='market'
    )
```

### Staking Module

```python
from staking import StakingManager

manager = StakingManager()

# Get all staking positions
positions = await manager.get_all_positions()

# Get rewards summary
rewards = await manager.get_rewards_summary()

# Stake assets (requires permissions)
result = await manager.stake(
    exchange='coinbase',
    asset='ETH',
    amount=1.0
)
```

### DeFi Module

```python
from defi import DeFiTracker

tracker = DeFiTracker(wallet_addresses=['0x...'])

# Get all DeFi positions
positions = await tracker.get_all_positions()

# Get Aave positions specifically
aave = await tracker.get_aave_positions()

# Track Uniswap LP positions
uniswap = await tracker.get_uniswap_positions()
```

### Automation Module

```python
from automation import DCABot, AlertManager

# Create DCA bot
bot = DCABot(
    asset='BTC',
    amount_usd=100,
    frequency='weekly',
    exchange='coinbase'
)
await bot.start()

# Set up alerts
alerts = AlertManager()
await alerts.create_price_alert(
    asset='BTC',
    condition='above',
    threshold=50000,
    notification_channels=['email', 'sms']
)
```

---

## Security

### Best Practices

1. **API Key Management**
   - Use read-only API keys when possible
   - Enable IP whitelisting on all exchanges
   - Never commit API keys to version control
   - Rotate keys periodically

2. **Paper Trading**
   - Always test with `PAPER_TRADING=true` first
   - Verify all logic before enabling real trading

3. **Wallet Security**
   - Use hardware wallets for significant holdings
   - Only track wallet addresses, never store private keys
   - Verify contract addresses before DeFi interactions

4. **Data Protection**
   - Encrypt local database
   - Use secure connections (HTTPS/WSS)
   - Audit logs regularly

### Environment Isolation

```bash
# Development
cp .env.example .env.development
export ENV=development

# Production
cp .env.example .env.production
# Use secrets manager for production keys
```

---

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_exchanges.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black .

# Lint
ruff check .

# Type checking
mypy .
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

---

## Troubleshooting

### Common Issues

#### "Authentication failed" errors

- Verify API keys are correct in `.env`
- Check API key permissions match requirements
- Ensure IP whitelisting includes your IP
- Some exchanges require passphrase (Coinbase Pro)

#### "Rate limit exceeded"

- Reduce request frequency
- Enable Redis caching: `REDIS_URL=redis://localhost:6379/0`
- Use WebSocket feeds for real-time data

#### MCP server not connecting

- Verify Python path in MCP config
- Check environment variables are passed correctly
- Run server manually to see error messages:
  ```bash
  python crypto_portfolio_mcp.py
  ```

#### DeFi positions not loading

- Verify wallet addresses are correct
- Check Etherscan API key is configured
- Some protocols may have rate limits

### Debug Mode

```bash
# Enable debug logging
LOG_LEVEL=DEBUG python main.py portfolio summary

# MCP server debug
python crypto_portfolio_mcp.py 2>&1 | tee mcp.log
```

### Getting Help

- Check the [FAQ](docs/FAQ.md)
- Search [existing issues](https://github.com/yourusername/crypto-portfolio-analyzer/issues)
- Join our [Discord community](https://discord.gg/yourserver)
- Open a new issue with debug logs

---

## License

MIT License - See [LICENSE](LICENSE) for details.

---

## Acknowledgments

- Exchange API documentation teams
- MCP Protocol developers at Anthropic
- Open-source DeFi integration libraries
- Community contributors

---

*Built with ❤️ for the crypto community*

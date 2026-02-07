# Crypto Portfolio MCP - Extended Components

This document covers all the additional infrastructure built for the MCP server.

## 📁 Project Structure

```
crypto-portfolio-mcp/
├── crypto_portfolio_mcp.py     # Main MCP server (24 tools)
├── additional_tools.py         # 14 additional tools (trading, etc.)
├── cli.py                      # Command-line interface
├── exchanges/
│   ├── __init__.py
│   └── mock.py                 # Mock exchange clients for testing
├── database/
│   ├── __init__.py
│   ├── models.py               # SQLAlchemy ORM models
│   └── migrations/             # Alembic migrations
├── automation/
│   ├── __init__.py
│   └── worker.py               # Background job scheduler
├── websocket_feeds.py          # Real-time WebSocket feeds
├── notifications.py            # Multi-channel notifications
├── caching.py                  # Redis caching layer
├── monitoring.py               # Prometheus metrics & health checks
├── .github/workflows/          # CI/CD pipelines
│   ├── test.yml
│   ├── lint.yml
│   └── release.yml
├── docker-compose.yml          # Docker deployment
├── Dockerfile
└── monitoring/
    ├── prometheus.yml
    └── grafana/                # Grafana dashboards
```

---

## 1. Mock Exchange Clients

**File:** `exchanges/mock.py`

Simulated exchange APIs for development and testing without real API keys or funds.

### Features
- Paper trading with virtual balances
- Simulated order book and matching engine
- Configurable latency simulation
- Error injection for testing error handling
- Historical data replay for backtesting

### Usage

```python
from exchanges.mock import MockExchangeFactory

# Create mock Coinbase with custom balance
coinbase = MockExchangeFactory.create(
    "coinbase",
    initial_balances={"USD": 10000, "BTC": 0.5},
    seed=42  # Reproducible randomness
)

# Get balances
balances = await coinbase.get_balances()

# Place paper trade
order = await coinbase.place_order(
    symbol="BTC-USD",
    side="buy",
    amount=0.1,
    order_type="market"
)

# Simulate staking
position = await coinbase.stake("ETH", 2.0)

# Enable error injection for testing
coinbase.error_injector.enable()
coinbase.error_injector.set_error_rate("rate_limit", 0.3)
```

### Supported Exchanges
- `MockCoinbase`
- `MockKraken`
- `MockCryptoCom`
- `MockGemini`

---

## 2. Database Models & Migrations

**File:** `database/models.py`

SQLAlchemy models with Alembic migrations for persistent storage.

### Tables
| Table | Purpose |
|-------|---------|
| `portfolios` | Portfolio snapshots over time |
| `transactions` | All buy/sell/transfer records |
| `tax_lots` | Cost basis tracking per lot |
| `staking_positions` | Staking history & rewards |
| `dca_bots` | Bot configs & execution log |
| `alerts` | Alert configs & trigger history |
| `wallets` | Tracked wallet addresses |
| `defi_positions` | DeFi protocol positions |
| `price_cache` | Cached price data |
| `settings` | Application settings |

### Usage

```python
from database import get_async_engine, get_session, Portfolio, Transaction

# Create async engine
engine = get_async_engine("postgresql+asyncpg://user:pass@localhost/db")

# Create tables
await create_tables_async(engine)

# Use session
async with get_session(engine) as session:
    portfolio = Portfolio(
        total_value_usd=127834.56,
        holdings_by_asset={"BTC": {"amount": "1.5", "value_usd": "67500"}}
    )
    session.add(portfolio)
    # Auto-commit on context exit
```

### Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 3. CI/CD Configuration

**Directory:** `.github/workflows/`

GitHub Actions workflows for automated testing and deployment.

### Workflows

| Workflow | Trigger | Actions |
|----------|---------|---------|
| `test.yml` | PR, push | pytest + coverage, multi-Python |
| `lint.yml` | PR, push | ruff, black, mypy, bandit |
| `release.yml` | Tag push | Build, Docker push, GitHub release |

### Running Locally

```bash
# Run tests
pytest tests/ -v --cov=. --cov-report=html

# Run linting
ruff check .
black --check .
mypy crypto_portfolio_mcp.py
```

---

## 4. Docker Setup

**Files:** `Dockerfile`, `docker-compose.yml`

Containerized deployment with all services.

### Quick Start

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f mcp-server

# Stop
docker-compose down
```

### Services

| Service | Port | Purpose |
|---------|------|---------|
| `mcp-server` | 8080 | Main MCP server |
| `postgres` | 5432 | Database |
| `redis` | 6379 | Cache |
| `worker` | - | Background jobs |
| `prometheus` | 9090 | Metrics (optional) |
| `grafana` | 3000 | Dashboards (optional) |

### Enable Monitoring

```bash
docker-compose --profile monitoring up -d
```

---

## 5. CLI Interface

**File:** `cli.py`

Typer-based command line for direct usage without Claude Code.

### Installation

```bash
pip install typer rich
```

### Commands

```bash
# Portfolio
crypto-portfolio portfolio summary
crypto-portfolio portfolio history --days 30

# Holdings
crypto-portfolio holdings list --exchange coinbase
crypto-portfolio holdings list --asset BTC

# Staking
crypto-portfolio staking list
crypto-portfolio staking stake ETH 5.0 --exchange coinbase

# DCA Bots
crypto-portfolio dca list
crypto-portfolio dca create BTC 100 weekly --exchange coinbase
crypto-portfolio dca pause bot_123

# Alerts
crypto-portfolio alerts list
crypto-portfolio alerts create price_above 50000 --asset BTC

# Tax
crypto-portfolio tax cost-basis --method fifo --year 2024
crypto-portfolio tax export 2024 --format turbotax

# Analysis
crypto-portfolio analyze --type comprehensive

# Arbitrage
crypto-portfolio arbitrage --min-spread 0.5

# Configuration
crypto-portfolio config
crypto-portfolio version
```

### JSON Output

```bash
crypto-portfolio portfolio summary --json | jq .
```

---

## 6. WebSocket Real-Time Feeds

**File:** `websocket_feeds.py`

Live price updates and order book streams from exchanges.

### Features
- Price streaming from multiple exchanges
- Order book updates
- Trade stream
- Automatic reconnection
- Callback-based architecture

### Usage

```python
from websocket_feeds import PriceFeedManager, PriceUpdate

def on_price(update: PriceUpdate):
    print(f"[{update.exchange}] {update.symbol}: ${update.price:.2f}")

manager = PriceFeedManager(exchanges=["coinbase", "kraken"])

# Subscribe to price updates
manager.subscribe("BTC-USD", on_price)
manager.subscribe("ETH-USD", on_price)

# Start feeds (runs until stopped)
await manager.start()
```

### Supported Exchanges
- Coinbase (Advanced Trade WebSocket)
- Kraken
- Binance (reference implementation)

---

## 7. Notification System

**File:** `notifications.py`

Multi-channel alert delivery.

### Channels

| Channel | Backend | Config Env Vars |
|---------|---------|-----------------|
| Email | SMTP | `SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD` |
| SMS | Twilio | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_FROM_NUMBER` |
| Discord | Webhook | `DISCORD_WEBHOOK_URL` |
| Slack | Webhook | `SLACK_WEBHOOK_URL` |
| Telegram | Bot API | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` |
| Webhook | Custom | `CUSTOM_WEBHOOK_URL` |

### Usage

```python
from notifications import NotificationManager, Notification, NotificationTemplates

manager = NotificationManager()

# Send custom notification
await manager.send(Notification(
    title="Price Alert",
    message="BTC hit $50,000!",
    channels=["discord", "telegram", "email"],
    priority="high"
))

# Use templates
notification = NotificationTemplates.price_alert(
    asset="BTC",
    price=50125.50,
    target=50000,
    direction="above"
)
await manager.send(notification)

# Broadcast to all configured channels
await manager.broadcast(
    title="System Alert",
    message="Maintenance starting in 5 minutes",
    priority="critical"
)
```

---

## 8. Caching Layer

**File:** `caching.py`

Redis-based caching to reduce API calls.

### TTL Configuration

| Data Type | Default TTL |
|-----------|-------------|
| Prices | 10 seconds |
| Balances | 30 seconds |
| Transactions | 5 minutes |
| Staking rates | 1 hour |
| Market data | 1 minute |
| Portfolio | 1 minute |

### Usage

```python
from caching import CacheManager, init_cache

# Initialize (auto-detects Redis or falls back to in-memory)
cache = await init_cache()

# Cache prices
await cache.set_price("BTC", 45000.50)
price = await cache.get_price("BTC")

# Cache portfolio
await cache.set_portfolio({"total_value": 127834.56})
portfolio = await cache.get_portfolio()

# Get statistics
stats = cache.get_stats()  # {"hits": 100, "misses": 10, "hit_rate": "90.9%"}

# Invalidate cache
await cache.invalidate_portfolio()
await cache.invalidate_pattern("balance:*")
```

### Decorator

```python
from caching import cached, CacheTTL

@cached("user:{user_id}", ttl=CacheTTL.BALANCE)
async def get_user_balance(user_id: str):
    return await fetch_from_api(user_id)
```

---

## 9. Metrics & Monitoring

**File:** `monitoring.py`

Prometheus metrics and health checks.

### Health Checks

```python
from monitoring import HealthCheck

health = HealthCheck()
status = await health.check_all()

print(status.status)  # healthy, degraded, unhealthy
print(status.to_dict())
```

### Metrics

```python
from monitoring import MetricsCollector

metrics = MetricsCollector()

# Record API call
metrics.record_api_call("coinbase", "get_balances", 0.234, success=True)

# Record portfolio value
metrics.record_portfolio_value(127834.56)

# Export for Prometheus
prometheus_output = metrics.to_prometheus()
```

### Prometheus Endpoint

Add to your HTTP server:

```python
@app.get("/metrics")
async def get_metrics():
    return Response(metrics.to_prometheus(), media_type="text/plain")

@app.get("/health")
async def get_health():
    status = await health.check_all()
    return status.to_dict()
```

---

## 10. Background Job System

**File:** `scheduler.py`

APScheduler-based task scheduler for recurring operations.
The `automation/worker.py` module has been archived.

### Default Jobs

| Job | Frequency | Purpose |
|-----|-----------|---------|
| `PriceCacheJob` | 10s | Refresh price cache |
| `AlertCheckJob` | 30s | Check and trigger alerts |
| `DCAExecutionJob` | 1m | Execute scheduled DCA |
| `PortfolioSnapshotJob` | 1h | Take portfolio snapshots |
| `BalanceSyncJob` | 5m | Sync exchange balances |
| `StakingRewardsJob` | 24h | Check staking rewards |
| `DataCleanupJob` | 24h | Clean up old data |

### Usage

```python
from scheduler import Scheduler

# scheduler.py runs all jobs automatically via APScheduler
# See scheduler.py for job configuration
```

### Run as Standalone Worker

```bash
python scheduler.py
```

See `scheduler.py` for adding new scheduled tasks.

---

## Environment Variables Summary

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/crypto_portfolio

# Redis
REDIS_URL=redis://localhost:6379/0

# Paper Trading Mode
PAPER_TRADING=true

# Exchange API Keys
COINBASE_API_KEY=
COINBASE_API_SECRET=
KRAKEN_API_KEY=
KRAKEN_API_SECRET=

# Notifications
SMTP_HOST=smtp.gmail.com
SMTP_USER=
SMTP_PASSWORD=
NOTIFICATION_EMAIL=
DISCORD_WEBHOOK_URL=
SLACK_WEBHOOK_URL=
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# Monitoring
SENTRY_DSN=

# Worker
AUTO_CLAIM_REWARDS=false
DATA_RETENTION_DAYS=90
```

---

## Quick Start

```bash
# 1. Clone and install
git clone <repo>
cd crypto-portfolio-mcp
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your settings

# 3. Start with Docker
docker-compose up -d

# 4. Or run directly
python crypto_portfolio_mcp.py

# 5. Use CLI
crypto-portfolio portfolio summary
```

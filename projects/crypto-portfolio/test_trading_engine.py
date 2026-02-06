"""
Tests for TradingEngine — the core trade execution layer.

Covers:
- Safety limit enforcement (max trade, daily limits, cooldowns, blacklist/whitelist)
- Paper trading mode execution
- Trade record tracking
- BUY/SELL validation
- Fee estimation
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from config import TradingConfig, TradingMode, SafetyLimits
from trading_engine import TradingEngine, TradeRecord


@pytest.fixture
def mock_client():
    """Create a mock Coinbase client."""
    client = MagicMock()
    client.get_spot_price.return_value = 50000.0  # BTC at $50k
    return client


@pytest.fixture
def paper_config(tmp_path):
    """Paper trading config with known limits."""
    return TradingConfig(
        mode=TradingMode.PAPER,
        safety=SafetyLimits(
            max_trade_usd=500.0,
            max_trades_per_day=5,
            max_daily_volume_usd=2000.0,
            trade_cooldown_seconds=60,
            max_sell_percent=25.0,
            blacklist=["SHIB", "DOGE"],
            whitelist=None,
        ),
        log_file=str(tmp_path / "test_trading.log"),
        verbose=False,
    )


@pytest.fixture
def engine(mock_client, paper_config):
    """Create a TradingEngine in paper mode."""
    return TradingEngine(mock_client, paper_config)


class TestSafetyLimits:
    """Test safety limit enforcement."""

    def test_max_trade_usd_blocks_large_trade(self, engine):
        record = engine.execute_trade("BTC-USD", "BUY", usd_amount=600.0)
        assert not record.executed
        assert "exceeds max" in record.error

    def test_max_trade_usd_allows_within_limit(self, engine):
        record = engine.execute_trade("BTC-USD", "BUY", usd_amount=100.0)
        assert record.executed

    def test_daily_trade_count_limit(self, engine):
        for i in range(5):
            engine.execute_trade("BTC-USD", "BUY", usd_amount=10.0)
            # Reset cooldown so we can trade again
            engine.last_trade_time.clear()

        record = engine.execute_trade("BTC-USD", "BUY", usd_amount=10.0)
        assert not record.executed
        assert "Daily trade limit" in record.error

    def test_daily_volume_limit(self, engine):
        # Trade $450 x 4 = $1800, then try $300 which would exceed $2000
        for _ in range(4):
            engine.execute_trade("BTC-USD", "BUY", usd_amount=450.0)
            engine.last_trade_time.clear()

        record = engine.execute_trade("BTC-USD", "BUY", usd_amount=300.0)
        assert not record.executed
        assert "daily volume limit" in record.error

    def test_blacklist_blocks_trade(self, engine):
        record = engine.execute_trade("SHIB-USD", "BUY", usd_amount=10.0)
        assert not record.executed
        assert "blacklisted" in record.error

    def test_non_blacklisted_allowed(self, engine):
        record = engine.execute_trade("ETH-USD", "BUY", usd_amount=50.0)
        assert record.executed

    def test_whitelist_enforcement(self, engine):
        engine.config.safety.whitelist = ["BTC", "ETH"]

        record = engine.execute_trade("SOL-USD", "BUY", usd_amount=50.0)
        assert not record.executed
        assert "not in whitelist" in record.error

        record2 = engine.execute_trade("BTC-USD", "BUY", usd_amount=50.0)
        assert record2.executed

    def test_cooldown_blocks_rapid_trades(self, engine):
        engine.execute_trade("BTC-USD", "BUY", usd_amount=50.0)
        # Second trade on same asset within cooldown
        record = engine.execute_trade("BTC-USD", "BUY", usd_amount=50.0)
        assert not record.executed
        assert "Cooldown" in record.error

    def test_cooldown_different_assets_ok(self, engine):
        engine.execute_trade("BTC-USD", "BUY", usd_amount=50.0)
        # Different asset should not be blocked
        engine.mock_client = engine.client
        engine.client.get_spot_price.return_value = 3000.0
        record = engine.execute_trade("ETH-USD", "BUY", usd_amount=50.0)
        assert record.executed


class TestPaperTrading:
    """Test paper trading mode execution."""

    def test_paper_buy_executes(self, engine):
        record = engine.buy("BTC", 100.0)
        assert record.executed
        assert record.side == "BUY"
        assert record.product_id == "BTC-USD"
        assert record.requested_usd == 100.0
        assert record.order_id.startswith("PAPER-")

    def test_paper_buy_calculates_asset_amount(self, engine):
        record = engine.buy("BTC", 100.0)
        # $100 / $50000 = 0.002 BTC
        assert record.fill_amount == pytest.approx(0.002, rel=1e-6)
        assert record.fill_price == 50000.0

    def test_paper_buy_estimates_fees(self, engine):
        record = engine.buy("BTC", 100.0)
        # 0.6% fee on $100 = $0.60
        assert record.fees == pytest.approx(0.60, rel=1e-2)

    def test_paper_sell_executes(self, engine):
        record = engine.sell("BTC", 0.01)
        assert record.executed
        assert record.side == "SELL"
        # 0.01 BTC * $50000 = $500
        assert record.requested_usd == pytest.approx(500.0)

    def test_paper_trade_no_real_api_call(self, engine):
        engine.buy("BTC", 100.0)
        # Should not call any order placement methods
        engine.client.market_buy.assert_not_called()
        engine.client.market_sell.assert_not_called()
        engine.client.limit_buy.assert_not_called()
        engine.client.limit_sell.assert_not_called()


class TestTradeValidation:
    """Test input validation."""

    def test_buy_requires_usd_amount(self, engine):
        record = engine.execute_trade("BTC-USD", "BUY")
        assert not record.executed
        assert "usd_amount" in record.error

    def test_sell_requires_asset_amount(self, engine):
        record = engine.execute_trade("BTC-USD", "SELL")
        assert not record.executed
        assert "asset_amount" in record.error

    def test_zero_price_handling(self, engine):
        engine.client.get_spot_price.return_value = 0
        record = engine.execute_trade("BTC-USD", "BUY", usd_amount=100.0)
        # With zero price, asset_amount would be 0
        assert record.requested_amount == 0

    def test_none_price_handling(self, engine):
        engine.client.get_spot_price.return_value = None
        record = engine.execute_trade("BTC-USD", "BUY", usd_amount=100.0)
        # current_price defaults to 0 via `or 0`
        assert record.requested_amount == 0


class TestTradeTracking:
    """Test trade history and daily counters."""

    def test_trade_history_recorded(self, engine):
        engine.buy("BTC", 50.0)
        assert len(engine.trade_history) == 1
        assert engine.trade_history[0].side == "BUY"

    def test_daily_counters_increment(self, engine):
        engine.buy("BTC", 50.0)
        assert engine.daily_trades == 1
        assert engine.daily_volume_usd == 50.0

    def test_failed_trade_not_counted(self, engine):
        engine.execute_trade("SHIB-USD", "BUY", usd_amount=10.0)  # blacklisted
        assert engine.daily_trades == 0
        assert engine.daily_volume_usd == 0.0

    def test_daily_reset_on_new_day(self, engine):
        engine.buy("BTC", 50.0)
        engine.last_trade_time.clear()  # clear cooldown
        # Simulate yesterday
        engine.daily_reset_time = datetime.now() - timedelta(days=1)
        engine.buy("BTC", 30.0)
        assert engine.daily_trades == 1  # reset happened
        assert engine.daily_volume_usd == 30.0

    def test_trade_summary(self, engine):
        engine.buy("BTC", 100.0)
        summary = engine.get_trade_summary()
        assert summary["mode"] == "paper"
        assert summary["today"]["trades"] == 1
        assert summary["today"]["volume_usd"] == 100.0
        assert len(summary["recent_trades"]) == 1

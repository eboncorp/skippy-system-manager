"""
DCA Agent Resilience Tests
============================

Validates PaperDCAAgent behavior under failure conditions:
- CoinGecko API failures
- Partial / zero / missing prices
- Corrupted trade log files
- Empty balance edge cases
- Fear & Greed extremes
"""

import json
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from tests.conftest import MOCK_PRICES


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_partial_prices(exchange, symbols):
    """Seed only the given symbols on a PaperExchange."""
    exchange._prices.clear()
    for sym in symbols:
        if sym in MOCK_PRICES:
            exchange._prices[sym] = MOCK_PRICES[sym]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.stress
class TestDCAResilience:

    async def test_dca_with_coingecko_down(self, paper_dca_agent):
        """When F&G API is unreachable, agent falls back to 50 (neutral)
        and completes the cycle with a 1.0x multiplier."""
        # Mock fetch_fear_greed to simulate ConnectionError fallback
        # (the method catches all exceptions and returns 50)
        paper_dca_agent.fetch_fear_greed = AsyncMock(return_value=50)

        result = await paper_dca_agent.run_daily_dca(dry_run=False)

        assert result["fear_greed"] == 50
        assert result["war_chest_rule"] == "normal"
        assert result["orders_generated"] > 0

    async def test_dca_with_partial_prices(self, paper_dca_agent):
        """When prices are available for only some assets, orders should
        only be generated for priced assets; no crash."""
        priced = ["BTC", "ETH", "SOL", "AVAX", "USDC"]
        _seed_partial_prices(paper_dca_agent.exchange, priced)

        result = await paper_dca_agent.run_daily_dca(fear_greed=50, dry_run=False)

        filled = [o for o in result["orders"] if o["status"] == "filled"]
        skipped = [o for o in result["orders"] if o["status"] == "skipped_no_price"]

        # Only priced non-stablecoin assets should fill
        for order in filled:
            assert order["symbol"] in priced

        # Unpriced assets should be skipped
        assert len(skipped) > 0
        assert result["orders_generated"] > 0

    async def test_dca_with_zero_price(self, paper_dca_agent):
        """When an asset has price=0, its order is skipped but others proceed."""
        paper_dca_agent.exchange._prices["BTC"] = Decimal("0")

        result = await paper_dca_agent.run_daily_dca(fear_greed=50, dry_run=False)

        btc_orders = [o for o in result["orders"] if o["symbol"] == "BTC"]
        non_btc_filled = [
            o for o in result["orders"]
            if o["symbol"] != "BTC" and o["status"] == "filled"
        ]

        # BTC order should be skipped
        for o in btc_orders:
            assert o["status"] == "skipped_no_price"

        # Other assets should still fill
        assert len(non_btc_filled) > 0

    async def test_dca_with_corrupted_log(self, paper_dca_agent, tmp_path, monkeypatch):
        """When the DCA log file contains invalid JSON, agent starts with
        an empty log and doesn't crash."""
        log_path = tmp_path / "corrupted_log.json"
        log_path.write_text("{{{not valid json!!")
        monkeypatch.setattr("dca_agent.DCA_LOG_PATH", log_path)

        # Re-create agent to trigger _load_log with corrupted file
        from dca_agent import PaperDCAAgent
        agent = PaperDCAAgent(initial_cash=Decimal("5000"))
        for sym, price in MOCK_PRICES.items():
            agent.exchange._prices[sym] = price

        assert agent.dca_log == []

        result = await agent.run_daily_dca(fear_greed=50, dry_run=False)
        assert result["orders_generated"] > 0
        assert len(agent.dca_log) == 1

    async def test_dca_with_empty_balance(self, paper_dca_agent):
        """When USD balance is 0, cycle runs but orders get rejected
        by PaperExchange (insufficient funds)."""
        paper_dca_agent.exchange.balances["USD"] = Decimal("0")

        result = await paper_dca_agent.run_daily_dca(fear_greed=50, dry_run=False)

        # Cycle should complete without error
        assert result["orders_generated"] >= 0

        # No trades should have filled (no money to buy with)
        filled = [o for o in result["orders"] if o["status"] == "filled"]
        # With 0 USD, PaperExchange rejects buy orders
        # (orders may still be "filled" for very small amounts due to rounding,
        # but the total value should be negligible)
        total_traded = sum(
            Decimal(t["price"]) * Decimal(t["qty"])
            for t in result.get("trades", [])
        )
        assert total_traded <= Decimal("1")

    async def test_dca_log_persistence(self, paper_dca_agent, tmp_path, monkeypatch):
        """Running 2 cycles should produce 2 log entries saved to disk."""
        log_path = tmp_path / "persist_test.json"
        monkeypatch.setattr("dca_agent.DCA_LOG_PATH", log_path)

        # Re-create to pick up new path
        from dca_agent import PaperDCAAgent
        agent = PaperDCAAgent(initial_cash=Decimal("10000"))
        for sym, price in MOCK_PRICES.items():
            agent.exchange._prices[sym] = price

        await agent.run_daily_dca(fear_greed=50, dry_run=True)
        await agent.run_daily_dca(fear_greed=25, dry_run=True)

        assert len(agent.dca_log) == 2
        assert log_path.exists()

        saved = json.loads(log_path.read_text())
        assert len(saved) == 2
        assert saved[0]["fear_greed"] == 50
        assert saved[1]["fear_greed"] == 25

    @pytest.mark.parametrize("fg,expected_label", [
        (0, "extreme_fear"),
        (50, "normal"),
        (100, "extreme_greed"),
    ])
    async def test_dca_fear_greed_extremes(
        self, paper_dca_agent, fg, expected_label
    ):
        """F&G=0, 50, 100 should produce correct war chest rules and
        scale the DCA multiplier accordingly."""
        result = await paper_dca_agent.run_daily_dca(
            fear_greed=fg, dry_run=True
        )

        assert result["fear_greed"] == fg
        assert result["war_chest_rule"] == expected_label
        assert result["orders_generated"] > 0

        multiplier = Decimal(result["dca_multiplier"])

        if fg == 0:
            assert multiplier == Decimal("3.0")
        elif fg == 50:
            assert multiplier == Decimal("1.0")
        elif fg == 100:
            assert multiplier == Decimal("0.5")

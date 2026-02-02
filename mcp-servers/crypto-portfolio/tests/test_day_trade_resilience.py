"""
Day-Trading Agent Resilience Tests
=====================================

Validates PaperDayTrader behavior under failure conditions:
- No prices available
- Signal analyzer failure
- Ranging market (neutral scores)
- Budget limit enforcement
"""

from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import MOCK_PRICES


@pytest.mark.stress
class TestDayTradeResilience:

    async def test_day_trade_with_no_prices(self, paper_day_trader):
        """When exchange returns 0 for all prices, cycle completes
        with 0 trades and no crash."""
        # Clear all prices from paper exchange
        paper_day_trader.exchange._prices.clear()

        await paper_day_trader.initialize()

        summary = await paper_day_trader.run_paper_session(hours=1)

        assert summary["total_trades"] == 0
        assert summary["cycles_completed"] <= 1

    async def test_day_trade_with_signal_failure(self, paper_day_trader):
        """When the signal analyzer raises an exception, the cycle
        catches it, logs a warning, and continues with default score=0."""
        await paper_day_trader.initialize(prices=dict(MOCK_PRICES))

        # Patch the UnifiedSignalAnalyzer to raise on analyze()
        mock_analyzer = MagicMock()
        mock_analyzer.analyze = AsyncMock(
            side_effect=RuntimeError("Signal API unavailable")
        )
        mock_analyzer.close = AsyncMock()

        with patch(
            "agents.unified_analyzer.UnifiedSignalAnalyzer",
            return_value=mock_analyzer,
        ):
            summary = await paper_day_trader.run_paper_session(hours=1)

        # Session should complete, not crash
        assert summary["cycles_completed"] == 1
        # With score=0 (default), market is "ranging" (-30 to 30)
        if summary["cycle_log"]:
            assert summary["cycle_log"][0]["signal_score"] == 0.0

    async def test_day_trade_ranging_market(self, paper_day_trader):
        """With a neutral signal score (between -30 and 30), the strategy
        should classify market as 'ranging' and trade conservatively."""
        await paper_day_trader.initialize(prices=dict(MOCK_PRICES))

        # Mock analyzer to return neutral score
        mock_analyzer = MagicMock()
        mock_result = MagicMock()
        mock_result.composite_score = 15.0
        mock_result.market_condition.value = "neutral"
        mock_result.cycle_phase.value = "neutral"
        mock_analyzer.analyze = AsyncMock(return_value=mock_result)
        mock_analyzer.close = AsyncMock()

        with patch(
            "agents.unified_analyzer.UnifiedSignalAnalyzer",
            return_value=mock_analyzer,
        ):
            summary = await paper_day_trader.run_paper_session(hours=1)

        assert summary["cycles_completed"] == 1
        if summary["cycle_log"]:
            assert summary["cycle_log"][0]["strategy_mode"] == "ranging"

    async def test_day_trade_budget_limit(self, paper_day_trader):
        """Total traded value should not exceed the daily budget ($12)."""
        await paper_day_trader.initialize(prices=dict(MOCK_PRICES))

        # Mock analyzer to return strong buy signal to maximize trades
        mock_analyzer = MagicMock()
        mock_result = MagicMock()
        mock_result.composite_score = -50.0
        mock_result.market_condition.value = "fear"
        mock_result.cycle_phase.value = "accumulation"
        mock_analyzer.analyze = AsyncMock(return_value=mock_result)
        mock_analyzer.close = AsyncMock()

        with patch(
            "agents.unified_analyzer.UnifiedSignalAnalyzer",
            return_value=mock_analyzer,
        ):
            summary = await paper_day_trader.run_paper_session(hours=3)

        # Total bought should not exceed $12 budget per day (with some
        # tolerance for rounding/fees)
        total_bought = Decimal(summary["total_bought_usd"])
        from etf_config import PERSONAL_DAILY_BUDGET

        assert total_bought <= PERSONAL_DAILY_BUDGET + Decimal("1"), (
            f"Total bought ${total_bought} exceeds budget "
            f"${PERSONAL_DAILY_BUDGET}"
        )

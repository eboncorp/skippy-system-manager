"""
Agent Runner Resilience Tests
================================

Validates AgentRunner scheduler, lifecycle, and isolation:
- Paper vs live mode initial behavior
- Cycle limit enforcement
- Exception isolation between agents
- Trade log save failures
- Price fetch timeout handling
"""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from tests.conftest import MOCK_PRICES


@pytest.mark.stress
class TestAgentRunner:

    async def _init_runner(self, runner):
        """Helper to initialize runner with mocked CoinGecko prices."""
        with patch.object(
            runner, "_fetch_prices", new_callable=AsyncMock,
            return_value=dict(MOCK_PRICES),
        ):
            await runner.initialize(max_cycles=1)

    async def test_paper_mode_runs_immediately(self, agent_runner, monkeypatch):
        """In paper mode, start() should run cycles before waiting
        for scheduled cycles."""
        monkeypatch.setenv("AGENT_MODE", "paper")
        await self._init_runner(agent_runner)

        with patch.object(
            agent_runner, "_fetch_prices", new_callable=AsyncMock,
            return_value=dict(MOCK_PRICES),
        ):
            await agent_runner.start()

        # After start(), at least one cycle should have completed
        assert agent_runner._cycle_count >= 1

    async def test_live_mode_skips_immediate(self, agent_runner, monkeypatch):
        """In live mode, start() should NOT run cycles immediately —
        only schedule them."""
        monkeypatch.setenv("AGENT_MODE", "live")
        await self._init_runner(agent_runner)

        # Track if cycles were called
        biz_called = False
        pers_called = False

        original_biz = agent_runner._run_business_cycle
        original_pers = agent_runner._run_personal_cycle

        async def track_biz():
            nonlocal biz_called
            biz_called = True
            return await original_biz()

        async def track_pers():
            nonlocal pers_called
            pers_called = True
            return await original_pers()

        agent_runner._run_business_cycle = track_biz
        agent_runner._run_personal_cycle = track_pers

        with patch.object(
            agent_runner, "_fetch_prices", new_callable=AsyncMock,
            return_value=dict(MOCK_PRICES),
        ):
            await agent_runner.start()

        # In live mode, no immediate cycles should run
        assert not biz_called
        assert not pers_called

    async def test_cycle_limit_stops_runner(self, agent_runner, monkeypatch):
        """Setting max_cycles=2 should stop the runner after 2 cycles."""
        monkeypatch.setenv("AGENT_MODE", "paper")

        with patch.object(
            agent_runner, "_fetch_prices", new_callable=AsyncMock,
            return_value=dict(MOCK_PRICES),
        ):
            await agent_runner.initialize(max_cycles=2)
            await agent_runner.run_immediate(cycles=2)

        assert agent_runner._cycle_count == 2

    async def test_business_cycle_exception_doesnt_kill_runner(
        self, agent_runner, monkeypatch
    ):
        """If the business agent raises, the personal agent should
        still run and the runner should stay alive."""
        monkeypatch.setenv("AGENT_MODE", "paper")
        await self._init_runner(agent_runner)

        # Make business agent blow up
        agent_runner.business_agent.run_daily_dca = AsyncMock(
            side_effect=RuntimeError("Business agent exploded")
        )

        personal_ran = False
        original_personal = agent_runner._run_personal_cycle

        async def track_personal():
            nonlocal personal_ran
            personal_ran = True
            return await original_personal()

        agent_runner._run_personal_cycle = track_personal

        with patch.object(
            agent_runner, "_fetch_prices", new_callable=AsyncMock,
            return_value=dict(MOCK_PRICES),
        ):
            # This should not raise even though business agent fails
            await agent_runner.run_immediate(cycles=1)

        assert personal_ran

    async def test_personal_cycle_exception_doesnt_kill_runner(
        self, agent_runner, monkeypatch
    ):
        """If the personal agent raises, the business agent should
        still have run and the runner should stay alive."""
        monkeypatch.setenv("AGENT_MODE", "paper")
        await self._init_runner(agent_runner)

        # Make personal agent blow up
        agent_runner.personal_agent.run_paper_session = AsyncMock(
            side_effect=RuntimeError("Personal agent exploded")
        )

        business_ran = False
        original_business = agent_runner._run_business_cycle

        async def track_business():
            nonlocal business_ran
            business_ran = True
            return await original_business()

        agent_runner._run_business_cycle = track_business

        with patch.object(
            agent_runner, "_fetch_prices", new_callable=AsyncMock,
            return_value=dict(MOCK_PRICES),
        ):
            await agent_runner.run_immediate(cycles=1)

        assert business_ran

    async def test_trade_log_save_failure(self, agent_runner, monkeypatch):
        """When the log directory is unwritable, a warning is logged
        but the cycle still completes."""
        monkeypatch.setenv("AGENT_MODE", "paper")
        await self._init_runner(agent_runner)

        # Make the log dir unwritable by pointing to a non-existent
        # path that can't be created
        agent_runner.log_dir = Path("/proc/nonexistent/impossible")

        with patch.object(
            agent_runner, "_fetch_prices", new_callable=AsyncMock,
            return_value=dict(MOCK_PRICES),
        ):
            # Should not raise — _save_trade_log catches exceptions
            await agent_runner.run_immediate(cycles=1)

        # Cycle still completed
        assert agent_runner._cycle_count >= 1

    async def test_price_fetch_timeout(self, agent_runner, monkeypatch):
        """When CoinGecko times out, empty prices are returned and the
        cycle uses whatever prices the exchange already has."""
        monkeypatch.setenv("AGENT_MODE", "paper")

        # First init with good prices
        with patch.object(
            agent_runner, "_fetch_prices", new_callable=AsyncMock,
            return_value=dict(MOCK_PRICES),
        ):
            await agent_runner.initialize(max_cycles=1)

        # Now make price fetch return empty (simulating timeout)
        with patch.object(
            agent_runner, "_fetch_prices", new_callable=AsyncMock,
            return_value={},
        ):
            # Should not crash — agents work with whatever prices
            # they already have
            await agent_runner.run_immediate(cycles=1)

        assert agent_runner._cycle_count >= 1

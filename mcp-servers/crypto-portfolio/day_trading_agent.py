#!/usr/bin/env python3
"""
Paper Day-Trading Agent
========================

Orchestrates adaptive day trading using the signal system in paper mode.
Uses AdaptiveDayTradeStrategy which switches between momentum and mean-reversion
based on market conditions.

Personal accounts only. Budget: $12/day from etf_config.PERSONAL_DAILY_BUDGET.

Usage:
    python day_trading_agent.py --hours 8
    python day_trading_agent.py --hours 2 --assets BTC,ETH,SOL
"""

import argparse
import asyncio
import logging
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from agents.trading_agent import (
    AdaptiveDayTradeStrategy,
    Order,
    OrderSide,
    OrderStatus,
    PaperExchange,
    Portfolio,
    RiskLimits,
    Trade,
    TradingAgent,
    TradingConfig,
    TradingMode,
)
from etf_config import PERSONAL_DAILY_BUDGET

logger = logging.getLogger(__name__)

# Default tradeable assets for personal day trading
DEFAULT_DAY_TRADE_ASSETS = [
    "BTC", "ETH", "SOL", "AVAX", "LINK",
    "NEAR", "SUI", "RENDER", "FET", "DOGE",
]


class PaperDayTrader:
    """Paper day-trading orchestrator.

    Creates a TradingAgent with AdaptiveDayTradeStrategy on a PaperExchange,
    runs hourly cycles, and tracks all trades + P&L.
    """

    def __init__(
        self,
        assets: Optional[List[str]] = None,
        initial_cash: Decimal = Decimal("1000"),
    ):
        self.assets = assets or DEFAULT_DAY_TRADE_ASSETS

        # Configure for day trading
        self.config = TradingConfig(
            mode=TradingMode.PAPER,
            supported_assets=self.assets,
            dca_base_amount=PERSONAL_DAILY_BUDGET,
            dca_frequency_hours=1,  # hourly cycles
            risk_limits=RiskLimits(
                max_position_size_pct=Decimal("0.15"),
                max_portfolio_risk_pct=Decimal("0.02"),
                max_daily_loss_pct=Decimal("0.05"),
                max_drawdown_pct=Decimal("0.15"),
                min_cash_reserve_pct=Decimal("0.20"),
                max_open_positions=len(self.assets),
                max_orders_per_hour=50,
            ),
        )

        # Paper exchange with initial cash
        balances = {"USD": initial_cash}
        for asset in self.assets:
            balances[asset] = Decimal("0")
        self.exchange = PaperExchange(initial_balances=balances)

        # Strategy
        self.strategy = AdaptiveDayTradeStrategy(self.config)
        self.strategy.daily_budget = PERSONAL_DAILY_BUDGET

        # Agent
        self.agent = TradingAgent(
            config=self.config,
            exchange=self.exchange,
            strategies=[self.strategy],
        )

        # Session tracking
        self.session_trades: List[Trade] = []
        self.cycle_log: List[dict] = []
        self.start_time: Optional[datetime] = None

    async def initialize(self, prices: Optional[Dict[str, Decimal]] = None):
        """Initialize the agent. Optionally seed prices for testing."""
        if prices:
            for symbol, price in prices.items():
                self.exchange._prices[symbol] = price

        # Set portfolio state directly instead of full initialize
        # (avoids needing the signal analyzer for portfolio setup)
        self.agent.portfolio = Portfolio(
            cash_balance=await self.exchange.get_balance("USD"),
            positions={},
            initial_value=await self.exchange.get_balance("USD"),
        )
        self.agent.portfolio.total_value = self.agent.portfolio.initial_value
        self.agent.risk_manager.peak_value = self.agent.portfolio.total_value

    async def run_paper_session(self, hours: int = 8) -> dict:
        """Run a paper trading session for the specified number of hours.

        In paper mode, each cycle simulates one hour. Fetches live signal data
        if the analyzer is available, otherwise uses simulated scores.

        Returns a session summary dict.
        """
        self.start_time = datetime.utcnow()
        self.session_trades = []
        self.cycle_log = []

        logger.info(f"Starting paper day-trading session: {hours} cycles, "
                     f"{len(self.assets)} assets, ${PERSONAL_DAILY_BUDGET}/day budget")

        # Try to initialize signal analyzer
        analyzer = None
        try:
            from agents.unified_analyzer import UnifiedSignalAnalyzer
            analyzer = UnifiedSignalAnalyzer()
        except ImportError:
            logger.warning("Signal analyzer unavailable, using simulated scores")

        try:
            for cycle in range(hours):
                cycle_start = datetime.utcnow()

                # Get signal data
                signal_score = 0.0
                market_condition = "neutral"
                cycle_phase = "neutral"

                if analyzer:
                    try:
                        analysis = await analyzer.analyze("BTC")
                        signal_score = analysis.composite_score
                        market_condition = analysis.market_condition.value
                        cycle_phase = analysis.cycle_phase.value
                    except Exception as e:
                        logger.warning(f"Signal analysis failed: {e}")

                # Get current prices
                current_prices: Dict[str, Decimal] = {}
                for asset in self.assets:
                    price = await self.exchange.get_price(asset)
                    if price > 0:
                        current_prices[asset] = price

                if not current_prices:
                    logger.warning(f"Cycle {cycle+1}: No prices available, skipping")
                    continue

                # Update portfolio
                await self.agent._update_portfolio()

                # Evaluate strategy
                actions = await self.strategy.evaluate(
                    signal_score=signal_score,
                    market_condition=market_condition,
                    cycle_phase=cycle_phase,
                    portfolio=self.agent.portfolio,
                    current_prices=current_prices,
                )

                # Execute actions through the agent's order pipeline
                cycle_trades = []
                for action in actions:
                    if action.action == "hold":
                        continue

                    order = Order(
                        id="",
                        symbol=action.symbol,
                        side=OrderSide.BUY if "buy" in action.action else OrderSide.SELL,
                        order_type=__import__('agents.trading_agent', fromlist=['OrderType']).OrderType.MARKET,
                        quantity=action.suggested_quantity,
                        price=action.suggested_price,
                        metadata={
                            "strategy": action.reasoning,
                            "signal_score": action.signal_score,
                        },
                    )

                    is_valid, reason = self.agent.risk_manager.validate_order(
                        order, self.agent.portfolio, action.suggested_price or Decimal("0")
                    )

                    if not is_valid:
                        logger.debug(f"Order rejected: {reason}")
                        continue

                    try:
                        executed = await self.exchange.place_order(order)
                        if executed.status == OrderStatus.FILLED:
                            trade = Trade(
                                id=f"T-{executed.id}",
                                symbol=executed.symbol,
                                side=executed.side,
                                quantity=executed.filled_quantity,
                                price=executed.filled_price,
                                fees=executed.fees,
                                timestamp=datetime.utcnow(),
                                order_id=executed.id,
                                strategy=action.reasoning,
                            )
                            cycle_trades.append(trade)
                            self.session_trades.append(trade)
                            self.agent.risk_manager.update_tracking(trade, self.agent.portfolio)
                    except Exception as e:
                        logger.error(f"Order execution failed: {e}")

                # Log cycle
                await self.agent._update_portfolio()
                self.cycle_log.append({
                    "cycle": cycle + 1,
                    "signal_score": signal_score,
                    "market_condition": market_condition,
                    "strategy_mode": self.strategy._classify_market(signal_score),
                    "trades": len(cycle_trades),
                    "portfolio_value": str(self.agent.portfolio.total_value),
                    "cash": str(self.agent.portfolio.cash_balance),
                })

                logger.info(
                    f"Cycle {cycle+1}/{hours}: score={signal_score:.1f} "
                    f"mode={self.strategy._classify_market(signal_score)} "
                    f"trades={len(cycle_trades)} "
                    f"portfolio=${self.agent.portfolio.total_value:.2f}"
                )

        finally:
            if analyzer:
                await analyzer.close()

        return self.get_session_summary()

    def get_session_summary(self) -> dict:
        """Generate a session summary."""
        total_trades = len(self.session_trades)
        buys = [t for t in self.session_trades if t.side == OrderSide.BUY]
        sells = [t for t in self.session_trades if t.side == OrderSide.SELL]
        total_fees = sum(t.fees for t in self.session_trades)
        total_bought = sum(t.quantity * t.price for t in buys)
        total_sold = sum(t.quantity * t.price for t in sells)

        return {
            "session_start": self.start_time.isoformat() if self.start_time else None,
            "session_end": datetime.utcnow().isoformat(),
            "cycles_completed": len(self.cycle_log),
            "total_trades": total_trades,
            "buys": len(buys),
            "sells": len(sells),
            "total_bought_usd": str(total_bought),
            "total_sold_usd": str(total_sold),
            "total_fees": str(total_fees),
            "portfolio_value": str(self.agent.portfolio.total_value),
            "cash_balance": str(self.agent.portfolio.cash_balance),
            "pnl": str(self.agent.portfolio.total_pnl),
            "pnl_pct": str(self.agent.portfolio.total_pnl_percent),
            "positions": {
                sym: {
                    "qty": str(pos.quantity),
                    "entry": str(pos.entry_price),
                    "current": str(pos.current_price),
                    "pnl_pct": str(pos.pnl_percent),
                }
                for sym, pos in self.agent.portfolio.positions.items()
            },
            "cycle_log": self.cycle_log,
            "trades": [
                {
                    "id": t.id,
                    "symbol": t.symbol,
                    "side": t.side.value,
                    "qty": str(t.quantity),
                    "price": str(t.price),
                    "fees": str(t.fees),
                    "strategy": t.strategy,
                    "time": t.timestamp.isoformat(),
                }
                for t in self.session_trades
            ],
        }

    def format_summary_markdown(self, summary: Optional[dict] = None) -> str:
        """Format session summary as markdown."""
        s = summary or self.get_session_summary()

        md = f"""# Paper Day-Trading Session Summary

**Period:** {s['session_start']} to {s['session_end']}
**Cycles:** {s['cycles_completed']}

## Performance
| Metric | Value |
|--------|-------|
| Portfolio Value | ${Decimal(s['portfolio_value']):,.2f} |
| Cash Balance | ${Decimal(s['cash_balance']):,.2f} |
| P&L | ${Decimal(s['pnl']):,.2f} ({Decimal(s['pnl_pct']):.2f}%) |
| Total Fees | ${Decimal(s['total_fees']):,.4f} |

## Trades
| Total | Buys | Sells | Bought | Sold |
|-------|------|-------|--------|------|
| {s['total_trades']} | {s['buys']} | {s['sells']} | ${Decimal(s['total_bought_usd']):,.2f} | ${Decimal(s['total_sold_usd']):,.2f} |

"""
        if s['positions']:
            md += "## Open Positions\n"
            md += "| Asset | Qty | Entry | Current | P&L % |\n"
            md += "|-------|-----|-------|---------|-------|\n"
            for sym, pos in s['positions'].items():
                md += f"| {sym} | {pos['qty']} | ${Decimal(pos['entry']):,.2f} | ${Decimal(pos['current']):,.2f} | {Decimal(pos['pnl_pct']):+.2f}% |\n"

        if s['trades']:
            md += "\n## Trade Log\n"
            md += "| Time | Side | Symbol | Qty | Price | Strategy |\n"
            md += "|------|------|--------|-----|-------|----------|\n"
            for t in s['trades']:
                md += f"| {t['time'][:19]} | {t['side'].upper()} | {t['symbol']} | {t['qty']} | ${Decimal(t['price']):,.2f} | {t['strategy'][:40]} |\n"

        return md


async def main():
    parser = argparse.ArgumentParser(description="Paper Day-Trading Agent")
    parser.add_argument("--hours", type=int, default=8, help="Number of hourly cycles to run")
    parser.add_argument("--assets", type=str, default=None, help="Comma-separated asset list")
    parser.add_argument("--cash", type=float, default=1000, help="Initial paper cash")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    assets = args.assets.split(",") if args.assets else None

    trader = PaperDayTrader(assets=assets, initial_cash=Decimal(str(args.cash)))

    # Fetch live prices to seed the paper exchange
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            ids = ",".join(a.lower() for a in (assets or DEFAULT_DAY_TRADE_ASSETS))
            # Use CoinGecko for price seeding
            url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana,avalanche-2,chainlink,near,sui,render-token,fetch-ai,dogecoin&vs_currencies=usd"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    symbol_map = {
                        "bitcoin": "BTC", "ethereum": "ETH", "solana": "SOL",
                        "avalanche-2": "AVAX", "chainlink": "LINK", "near": "NEAR",
                        "sui": "SUI", "render-token": "RENDER", "fetch-ai": "FET",
                        "dogecoin": "DOGE",
                    }
                    prices = {}
                    for cg_id, sym in symbol_map.items():
                        if cg_id in data and sym in (assets or DEFAULT_DAY_TRADE_ASSETS):
                            prices[sym] = Decimal(str(data[cg_id]["usd"]))
                    await trader.initialize(prices=prices)
                    logger.info(f"Seeded {len(prices)} prices from CoinGecko")
                else:
                    await trader.initialize()
    except Exception as e:
        logger.warning(f"Could not fetch live prices: {e}")
        await trader.initialize()

    summary = await trader.run_paper_session(hours=args.hours)
    print(trader.format_summary_markdown(summary))


if __name__ == "__main__":
    asyncio.run(main())

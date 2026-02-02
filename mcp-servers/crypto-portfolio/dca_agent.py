#!/usr/bin/env python3
"""
Paper DCA Agent for GTI Virtual ETF
=====================================

Connects the GTI Virtual ETF manager to the trading agent framework.
Generates daily DCA orders based on ETF target allocations and Fear & Greed
index, then executes them through a PaperExchange.

Business accounts only. Budget: $28/day from etf_config.ETF_DAILY_BUDGET.

Usage:
    python dca_agent.py --dry-run          # Show orders without executing
    python dca_agent.py                    # Run one DCA cycle in paper mode
    python dca_agent.py --fear-greed 20    # Override F&G index
"""

import argparse
import asyncio
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional

from agents.trading_agent import (
    Order,
    OrderSide,
    OrderStatus,
    OrderType,
    PaperExchange,
    Trade,
)
from etf_config import (
    ETF_ASSETS,
    ETF_DAILY_BUDGET,
    get_war_chest_rule,
)
from etf_manager import GTIVirtualETF

logger = logging.getLogger(__name__)

DCA_LOG_PATH = Path("/home/dave/skippy/work/crypto/dca_paper_log.json")


class PaperDCAAgent:
    """Paper DCA agent that uses the GTI Virtual ETF manager.

    Workflow:
    1. Fetch current holdings and prices (or use paper state)
    2. Calculate ETF allocations vs targets
    3. Generate DCA orders (prioritizing underweight assets)
    4. Apply Fear & Greed war chest logic
    5. Execute orders on PaperExchange
    6. Record NAV and log results
    """

    def __init__(
        self,
        initial_cash: Decimal = Decimal("5000"),
        initial_holdings: Optional[Dict[str, Decimal]] = None,
    ):
        self.etf = GTIVirtualETF()

        # Build initial balances for paper exchange
        balances = {"USD": initial_cash}
        for symbol in ETF_ASSETS:
            balances[symbol] = Decimal("0")
        if initial_holdings:
            for symbol, qty in initial_holdings.items():
                balances[symbol] = qty

        self.exchange = PaperExchange(initial_balances=balances)
        self.trades: List[Trade] = []
        self.dca_log: List[dict] = []
        self._load_log()

    def _load_log(self):
        if DCA_LOG_PATH.exists():
            try:
                with open(DCA_LOG_PATH) as f:
                    self.dca_log = json.load(f)
            except Exception:
                self.dca_log = []

    def _save_log(self):
        DCA_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(DCA_LOG_PATH, "w") as f:
            json.dump(self.dca_log[-365:], f, indent=2, default=str)

    async def _get_holdings_and_prices(self) -> tuple:
        """Get current holdings and prices from the paper exchange."""
        holdings: Dict[str, Decimal] = {}
        prices: Dict[str, Decimal] = {}

        for symbol in ETF_ASSETS:
            qty = await self.exchange.get_balance(symbol)
            if qty > 0:
                holdings[symbol] = qty
            price = await self.exchange.get_price(symbol)
            if price > 0:
                prices[symbol] = price

        # Stablecoins always $1
        prices.setdefault("USDC", Decimal("1"))

        return holdings, prices

    async def seed_prices(self, prices: Dict[str, Decimal]):
        """Seed the paper exchange with prices."""
        for symbol, price in prices.items():
            self.exchange._prices[symbol] = price

    async def fetch_live_prices(self) -> Dict[str, Decimal]:
        """Fetch live prices from CoinGecko for all ETF assets."""
        from etf_config import get_coingecko_ids

        cg_ids = get_coingecko_ids()
        if not cg_ids:
            return {}

        # Reverse map: coingecko_id -> symbol
        id_to_symbol = {v: k for k, v in cg_ids.items()}
        ids_param = ",".join(cg_ids.values())

        prices = {}
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_param}&vs_currencies=usd"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for cg_id, price_data in data.items():
                            symbol = id_to_symbol.get(cg_id)
                            if symbol and "usd" in price_data:
                                prices[symbol] = Decimal(str(price_data["usd"]))
        except Exception as e:
            logger.warning(f"CoinGecko price fetch failed: {e}")

        # Stablecoins
        prices["USDC"] = Decimal("1")

        return prices

    async def fetch_fear_greed(self) -> int:
        """Fetch current Fear & Greed index."""
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.alternative.me/fng/",
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as resp:
                    data = await resp.json()
                    return int(data["data"][0]["value"])
        except Exception:
            return 50  # default neutral

    async def run_daily_dca(
        self,
        fear_greed: Optional[int] = None,
        dry_run: bool = False,
    ) -> dict:
        """Run one daily DCA cycle.

        Args:
            fear_greed: Override Fear & Greed value. Fetches live if None.
            dry_run: If True, generate orders but don't execute.

        Returns:
            Dict with orders, trades, and ETF status.
        """
        # Get Fear & Greed
        fg = fear_greed if fear_greed is not None else await self.fetch_fear_greed()
        wc_rule = get_war_chest_rule(fg)

        logger.info(f"DCA cycle: F&G={fg} ({wc_rule.label}), budget=${ETF_DAILY_BUDGET}/day")

        # Get holdings and prices
        holdings, prices = await self._get_holdings_and_prices()

        # Calculate allocations
        allocations = self.etf.calculate_allocations(holdings, prices)

        # Generate DCA orders
        dca_orders = self.etf.generate_dca_orders(allocations, fg)

        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "fear_greed": fg,
            "war_chest_rule": wc_rule.label,
            "dca_multiplier": str(wc_rule.dca_multiplier),
            "budget": str(ETF_DAILY_BUDGET),
            "orders_generated": len(dca_orders),
            "total_order_usd": str(sum(o.amount_usd for o in dca_orders)),
            "dry_run": dry_run,
            "orders": [],
            "trades": [],
            "nav_before": str(self.etf.get_etf_nav(holdings, prices)),
        }

        # Execute orders (or just list them for dry run)
        for dca_order in dca_orders:
            order_info = {
                "symbol": dca_order.symbol,
                "exchange": dca_order.exchange.value,
                "amount_usd": str(dca_order.amount_usd),
                "category": dca_order.category.value,
                "reason": dca_order.reason,
                "priority": dca_order.priority,
            }

            if dry_run:
                order_info["status"] = "dry_run"
                result["orders"].append(order_info)
                continue

            # Execute via paper exchange
            price = await self.exchange.get_price(dca_order.symbol)
            if price <= 0:
                order_info["status"] = "skipped_no_price"
                result["orders"].append(order_info)
                continue

            quantity = (dca_order.amount_usd / price).quantize(
                Decimal("0.00000001")
            )

            order = Order(
                id="",
                symbol=dca_order.symbol,
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=quantity,
                price=price,
                metadata={
                    "dca_reason": dca_order.reason,
                    "category": dca_order.category.value,
                },
            )

            try:
                executed = await self.exchange.place_order(order)
                if executed.status == OrderStatus.FILLED:
                    trade = Trade(
                        id=f"DCA-{executed.id}",
                        symbol=executed.symbol,
                        side=executed.side,
                        quantity=executed.filled_quantity,
                        price=executed.filled_price,
                        fees=executed.fees,
                        timestamp=datetime.now(timezone.utc),
                        order_id=executed.id,
                        strategy=f"ETF DCA: {dca_order.reason}",
                    )
                    self.trades.append(trade)
                    order_info["status"] = "filled"
                    order_info["filled_qty"] = str(executed.filled_quantity)
                    order_info["filled_price"] = str(executed.filled_price)
                    result["trades"].append({
                        "symbol": trade.symbol,
                        "qty": str(trade.quantity),
                        "price": str(trade.price),
                        "fees": str(trade.fees),
                    })
                else:
                    order_info["status"] = executed.status.value
            except Exception as e:
                order_info["status"] = f"error: {e}"

            result["orders"].append(order_info)

        # Post-execution NAV
        if not dry_run:
            holdings_after, prices_after = await self._get_holdings_and_prices()
            result["nav_after"] = str(self.etf.get_etf_nav(holdings_after, prices_after))

            # Record NAV
            self.etf.record_nav(holdings_after, prices_after)

        # Log
        self.dca_log.append(result)
        self._save_log()

        return result

    def format_result_markdown(self, result: dict) -> str:
        """Format DCA result as markdown."""
        md = f"""# Paper DCA Cycle Report

**Time:** {result['timestamp']}
**Fear & Greed:** {result['fear_greed']} ({result['war_chest_rule']})
**Budget:** ${Decimal(result['budget']):,.2f}
**Mode:** {'DRY RUN' if result['dry_run'] else 'Paper Trading'}

## Orders ({result['orders_generated']} generated, ${Decimal(result['total_order_usd']):,.2f} total)

| Symbol | Amount | Category | Reason | Status |
|--------|--------|----------|--------|--------|
"""
        for o in result['orders']:
            md += f"| {o['symbol']} | ${Decimal(o['amount_usd']):,.2f} | {o['category']} | {o['reason'][:30]} | {o['status']} |\n"

        if result.get('nav_before'):
            md += f"\n**NAV Before:** ${Decimal(result['nav_before']):,.2f}\n"
        if result.get('nav_after'):
            md += f"**NAV After:** ${Decimal(result['nav_after']):,.2f}\n"

        if result['trades']:
            md += "\n## Executed Trades\n"
            md += "| Symbol | Qty | Price | Fees |\n"
            md += "|--------|-----|-------|------|\n"
            for t in result['trades']:
                md += f"| {t['symbol']} | {t['qty']} | ${Decimal(t['price']):,.2f} | ${Decimal(t['fees']):,.4f} |\n"

        return md


async def main():
    parser = argparse.ArgumentParser(description="Paper DCA Agent for GTI Virtual ETF")
    parser.add_argument("--dry-run", action="store_true", help="Generate orders without executing")
    parser.add_argument("--fear-greed", type=int, default=None, help="Override Fear & Greed (0-100)")
    parser.add_argument("--cash", type=float, default=5000, help="Initial paper cash")
    parser.add_argument("--verbose", action="store_true", help="Verbose logging")
    args = parser.parse_args()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    agent = PaperDCAAgent(initial_cash=Decimal(str(args.cash)))

    # Fetch live prices
    logger.info("Fetching live prices from CoinGecko...")
    prices = await agent.fetch_live_prices()
    if prices:
        await agent.seed_prices(prices)
        logger.info(f"Seeded {len(prices)} asset prices")
    else:
        logger.warning("No live prices available. Paper exchange has no price data.")
        return

    result = await agent.run_daily_dca(
        fear_greed=args.fear_greed,
        dry_run=args.dry_run,
    )

    print(agent.format_result_markdown(result))


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Agent Runner — GTI Inc Trading Orchestrator
=============================================

Manages two dedicated trading agents:
  - Business Agent: ETF DCA on Coinbase GTI + Kraken Business ($28/day)
  - Personal Agent: Day trading on Coinbase Personal + Kraken Personal ($12/day)

Supports paper mode (default) and live mode. Paper mode uses PaperExchange
with real market prices. Live mode routes orders to real exchanges via
the adapter layer.

Usage:
    python agent_runner.py                         # Paper mode, run forever
    python agent_runner.py --mode paper --cycles 3 # Paper mode, 3 cycles then exit
    python agent_runner.py --mode live             # Live mode (requires exchange keys)
    python agent_runner.py --business-only         # Only run business agent
    python agent_runner.py --personal-only         # Only run personal agent

Environment:
    AGENT_MODE=paper|live       Override mode
    AGENT_LOG_DIR=path          Trade log directory (default: ./data/agent_logs)
"""

import argparse
import asyncio
import json
import logging
import os
import signal
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from dca_agent import PaperDCAAgent
from day_trading_agent import PaperDayTrader, DEFAULT_DAY_TRADE_ASSETS
from etf_config import (
    ETF_ASSETS,
    ETF_DAILY_BUDGET,
    PERSONAL_DAILY_BUDGET,
)

logger = logging.getLogger(__name__)

# Default log directory
DEFAULT_LOG_DIR = Path("./data/agent_logs")


class AgentRunner:
    """Orchestrates business + personal trading agents.

    In paper mode, both agents use PaperExchange instances with real prices
    fetched from CoinGecko. In live mode, they use LiveExchangeAdapter
    instances wrapping real exchange clients.
    """

    def __init__(
        self,
        mode: str = "paper",
        run_business: bool = True,
        run_personal: bool = True,
        log_dir: Optional[Path] = None,
    ):
        self.mode = mode
        self.run_business = run_business
        self.run_personal = run_personal
        self.log_dir = log_dir or DEFAULT_LOG_DIR

        self.business_agent: Optional[PaperDCAAgent] = None
        self.personal_agent: Optional[PaperDayTrader] = None
        self.analyzer = None
        self.scheduler = AsyncIOScheduler()
        self._running = False
        self._cycle_count = 0
        self._max_cycles: Optional[int] = None

        # Trade log
        self.trade_log: List[dict] = []
        self._exchange_clients = []  # for cleanup

        # Shared price cache with TTL (avoids duplicate CoinGecko calls)
        self._price_cache: Dict[str, Decimal] = {}
        self._price_cache_time: Optional[datetime] = None
        self._price_cache_ttl = 300  # 5 minutes

    async def initialize(self, max_cycles: Optional[int] = None):
        """Initialize agents and scheduler."""
        self._max_cycles = max_cycles
        self.log_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Initializing agent runner: mode={self.mode}, "
                     f"business={self.run_business}, personal={self.run_personal}")

        if self.mode == "paper":
            await self._init_paper_agents()
        elif self.mode == "live":
            await self._init_live_agents()
        else:
            raise ValueError(f"Unknown mode: {self.mode}")

        self._schedule_jobs()
        logger.info("Agent runner initialized")

    async def _init_paper_agents(self):
        """Initialize agents with PaperExchange and live prices."""
        # Fetch live prices for paper exchange seeding
        prices = await self._get_prices()

        if self.run_business:
            self.business_agent = PaperDCAAgent(initial_cash=Decimal("5000"))
            if prices:
                await self.business_agent.seed_prices(prices)
            logger.info("Business agent (ETF DCA) initialized in paper mode")

        if self.run_personal:
            self.personal_agent = PaperDayTrader(initial_cash=Decimal("1000"))
            if prices:
                await self.personal_agent.initialize(prices=prices)
            else:
                await self.personal_agent.initialize()
            logger.info("Personal agent (Day Trading) initialized in paper mode")

    async def _init_live_agents(self):
        """Initialize agents with real exchange adapters."""
        from exchanges import CoinbaseClient, KrakenClient
        from exchanges.adapter import LiveExchangeAdapter, MultiExchangeAdapter

        # --- Business exchanges ---
        coinbase_gti_key = os.path.expanduser(
            "~/.config/coinbase/gti_cdp_api_key.json"
        )
        kraken_biz_key = os.path.expanduser(
            "~/.config/kraken/business_api_key.json"
        )

        if self.run_business:
            biz_adapters = {}

            if os.path.exists(coinbase_gti_key):
                client = CoinbaseClient.from_key_file(coinbase_gti_key)
                self._exchange_clients.append(client)
                biz_adapters["coinbase_gti"] = LiveExchangeAdapter(
                    client, "coinbase_gti"
                )
                logger.info("Coinbase GTI connected (business)")

            if os.path.exists(kraken_biz_key):
                client = KrakenClient.from_key_file(kraken_biz_key)
                self._exchange_clients.append(client)
                biz_adapters["kraken_business"] = LiveExchangeAdapter(
                    client, "kraken_business"
                )
                logger.info("Kraken Business connected")

            if biz_adapters:
                # Build routing from ETF config
                biz_routing = {}
                for asset in ETF_ASSETS.values():
                    biz_routing[asset.symbol] = asset.exchange.value

                biz_exchange = MultiExchangeAdapter(biz_adapters, biz_routing)
                self.business_agent = PaperDCAAgent(exchange=biz_exchange)
                logger.info(
                    f"Business agent (ETF DCA) initialized in live mode "
                    f"with {len(biz_adapters)} exchanges"
                )
            else:
                logger.warning("No business exchange credentials found")

        # --- Personal exchanges ---
        coinbase_personal_key = os.path.expanduser(
            "~/.config/coinbase/cdp_api_key.json"
        )
        kraken_personal_key = os.path.expanduser(
            "~/.config/kraken/personal_api_key.json"
        )

        if self.run_personal:
            personal_adapters = {}

            if os.path.exists(coinbase_personal_key):
                client = CoinbaseClient.from_key_file(coinbase_personal_key)
                self._exchange_clients.append(client)
                personal_adapters["coinbase"] = LiveExchangeAdapter(
                    client, "coinbase"
                )
                logger.info("Coinbase Personal connected")

            if os.path.exists(kraken_personal_key):
                client = KrakenClient.from_key_file(kraken_personal_key)
                self._exchange_clients.append(client)
                personal_adapters["kraken"] = LiveExchangeAdapter(
                    client, "kraken"
                )
                logger.info("Kraken Personal connected")

            if personal_adapters:
                # Personal trades default to Coinbase
                personal_routing = {
                    asset: "coinbase" for asset in DEFAULT_DAY_TRADE_ASSETS
                }
                personal_exchange = MultiExchangeAdapter(
                    personal_adapters, personal_routing
                )
                self.personal_agent = PaperDayTrader(exchange=personal_exchange)

                # Fetch prices for initialization
                prices = await self._get_prices()
                await self.personal_agent.initialize(prices=prices if prices else None)

                logger.info(
                    f"Personal agent (Day Trading) initialized in live mode "
                    f"with {len(personal_adapters)} exchanges"
                )
            else:
                logger.warning("No personal exchange credentials found")

    def _schedule_jobs(self):
        """Set up scheduled jobs for both agents."""
        if self.run_business and self.business_agent:
            # Business ETF DCA: once daily at 10:00 UTC
            self.scheduler.add_job(
                self._run_business_cycle,
                CronTrigger(hour=10, minute=0),
                id="business_dca",
                name="Business ETF DCA",
                replace_existing=True,
            )
            logger.info("Scheduled: Business ETF DCA daily at 10:00 UTC")

        if self.run_personal and self.personal_agent:
            # Personal day trading: every hour
            self.scheduler.add_job(
                self._run_personal_cycle,
                IntervalTrigger(hours=1),
                id="personal_trade",
                name="Personal Day Trade",
                replace_existing=True,
            )
            logger.info("Scheduled: Personal day trading every hour")

    async def _run_business_cycle(self):
        """Execute one ETF DCA cycle."""
        if not self.business_agent:
            return

        logger.info("=" * 50)
        logger.info("BUSINESS AGENT: Starting ETF DCA cycle")
        logger.info("=" * 50)

        try:
            # Refresh prices in paper mode
            if self.mode == "paper":
                prices = await self._get_prices()
                if prices:
                    await self.business_agent.seed_prices(prices)

            result = await self.business_agent.run_daily_dca(dry_run=False)

            # Log result
            log_entry = {
                "agent": "business",
                "type": "etf_dca",
                "mode": self.mode,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "fear_greed": result.get("fear_greed"),
                "orders": result.get("orders_generated", 0),
                "total_usd": result.get("total_order_usd", "0"),
                "trades": len(result.get("trades", [])),
            }
            self.trade_log.append(log_entry)
            self._save_trade_log()

            logger.info(
                f"Business DCA complete: {result.get('orders_generated', 0)} orders, "
                f"${result.get('total_order_usd', '0')} total, "
                f"F&G={result.get('fear_greed', '?')}"
            )

        except Exception as e:
            logger.error(f"Business DCA cycle failed: {e}", exc_info=True)

    async def _run_personal_cycle(self):
        """Execute one day-trading cycle."""
        if not self.personal_agent:
            return

        logger.info("-" * 50)
        logger.info("PERSONAL AGENT: Starting day-trade cycle")
        logger.info("-" * 50)

        try:
            # Refresh prices in paper mode (TTL-cached, no duplicate fetches)
            if self.mode == "paper" and hasattr(
                self.personal_agent.exchange, '_prices'
            ):
                prices = await self._get_prices()
                if prices:
                    for sym, price in prices.items():
                        self.personal_agent.exchange._prices[sym] = price

            # Run single hourly cycle
            summary = await self.personal_agent.run_paper_session(hours=1)

            # Log result
            log_entry = {
                "agent": "personal",
                "type": "day_trade",
                "mode": self.mode,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "trades": summary.get("total_trades", 0),
                "buys": summary.get("buys", 0),
                "sells": summary.get("sells", 0),
                "portfolio_value": summary.get("portfolio_value", "0"),
                "pnl": summary.get("pnl", "0"),
            }
            self.trade_log.append(log_entry)
            self._save_trade_log()

            logger.info(
                f"Personal trade complete: {summary.get('total_trades', 0)} trades, "
                f"portfolio=${summary.get('portfolio_value', '0')}, "
                f"P&L={summary.get('pnl', '0')}"
            )

        except Exception as e:
            logger.error(f"Personal trade cycle failed: {e}", exc_info=True)

    def _check_cycle_limit(self):
        """Stop after max_cycles if set."""
        self._cycle_count += 1
        if self._max_cycles and self._cycle_count >= self._max_cycles:
            logger.info(f"Reached cycle limit ({self._max_cycles}), shutting down")
            self._running = False

    async def _get_prices(self) -> Dict[str, Decimal]:
        """Get prices with a 5-minute TTL cache.

        Both business and personal cycles call this. Only one actual
        CoinGecko request happens per TTL window, avoiding rate limits.
        """
        now = datetime.now(timezone.utc)
        if (
            self._price_cache
            and self._price_cache_time
            and (now - self._price_cache_time).total_seconds() < self._price_cache_ttl
        ):
            logger.debug(f"Using cached prices ({len(self._price_cache)} assets)")
            return self._price_cache

        prices = await self._fetch_prices_from_coingecko()
        if prices:
            self._price_cache = prices
            self._price_cache_time = now
            logger.info(f"Fetched fresh prices for {len(prices)} assets")
        elif self._price_cache:
            logger.warning("CoinGecko fetch failed, using cached prices")
            return self._price_cache

        return prices

    async def _fetch_prices_from_coingecko(self) -> Dict[str, Decimal]:
        """Raw CoinGecko price fetch (no caching)."""
        from etf_config import get_coingecko_ids

        cg_ids = get_coingecko_ids()
        if not cg_ids:
            return {}

        # Add personal trading assets
        personal_cg_map = {
            "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana",
            "AVAX": "avalanche-2", "LINK": "chainlink", "NEAR": "near",
            "SUI": "sui", "RENDER": "render-token", "FET": "fetch-ai",
            "DOGE": "dogecoin",
        }
        for sym, cg_id in personal_cg_map.items():
            cg_ids.setdefault(sym, cg_id)

        id_to_symbol = {v: k for k, v in cg_ids.items()}
        ids_param = ",".join(set(cg_ids.values()))

        prices = {}
        try:
            import aiohttp

            async with aiohttp.ClientSession() as session:
                url = (
                    f"https://api.coingecko.com/api/v3/simple/price"
                    f"?ids={ids_param}&vs_currencies=usd"
                )
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=20)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for cg_id, price_data in data.items():
                            symbol = id_to_symbol.get(cg_id)
                            if symbol and "usd" in price_data:
                                prices[symbol] = Decimal(str(price_data["usd"]))

        except Exception as e:
            logger.warning(f"CoinGecko price fetch failed: {e}")

        prices.setdefault("USDC", Decimal("1"))
        return prices

    def _save_trade_log(self):
        """Save trade log to disk."""
        log_file = self.log_dir / "trade_log.json"
        try:
            with open(log_file, "w") as f:
                json.dump(self.trade_log[-1000:], f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to save trade log: {e}")

    def get_status(self) -> dict:
        """Get current agent runner status."""
        return {
            "mode": self.mode,
            "running": self._running,
            "cycles_completed": self._cycle_count,
            "max_cycles": self._max_cycles,
            "business_agent": {
                "enabled": self.run_business,
                "initialized": self.business_agent is not None,
                "type": "etf_dca",
                "budget": str(ETF_DAILY_BUDGET),
            },
            "personal_agent": {
                "enabled": self.run_personal,
                "initialized": self.personal_agent is not None,
                "type": "day_trade",
                "budget": str(PERSONAL_DAILY_BUDGET),
            },
            "recent_trades": self.trade_log[-10:],
        }

    async def run_immediate(self, cycles: int = 1):
        """Run cycles immediately without waiting for scheduler.

        Useful for testing and initial validation.
        """
        for i in range(cycles):
            logger.info(f"\n{'='*60}")
            logger.info(f"IMMEDIATE CYCLE {i+1}/{cycles}")
            logger.info(f"{'='*60}\n")

            if self.run_business and self.business_agent:
                await self._run_business_cycle()

            if self.run_personal and self.personal_agent:
                await self._run_personal_cycle()

            self._cycle_count += 1

    async def start(self):
        """Start the scheduler and run until stopped."""
        logger.info("Starting agent runner...")
        self.scheduler.start()
        self._running = True

        # Only run immediately in paper mode — live mode waits for schedule
        agent_mode = os.environ.get("AGENT_MODE", "paper")
        if agent_mode == "paper":
            if self.run_business and self.business_agent:
                await self._run_business_cycle()

            if self.run_personal and self.personal_agent:
                await self._run_personal_cycle()

            self._cycle_count += 1
            self._check_cycle_limit()

        logger.info("Agent runner started. Waiting for scheduled cycles...")

    async def stop(self):
        """Stop the scheduler and clean up."""
        logger.info("Stopping agent runner...")
        self._running = False

        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)

        # Close signal analyzer
        if self.analyzer:
            try:
                await self.analyzer.close()
            except Exception:
                pass

        # Close exchange clients
        for client in self._exchange_clients:
            try:
                await client.close()
            except Exception:
                pass

        self._save_trade_log()
        logger.info("Agent runner stopped")

    async def run_forever(self):
        """Run until interrupted or cycle limit reached."""
        await self.start()

        loop = asyncio.get_event_loop()

        def signal_handler():
            logger.info("Received shutdown signal")
            self._running = False

        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)

        while self._running:
            await asyncio.sleep(1)

        await self.stop()

    def format_status_markdown(self) -> str:
        """Format current status as markdown."""
        status = self.get_status()

        biz = status["business_agent"]
        per = status["personal_agent"]

        md = f"""# Agent Runner Status

**Mode:** {status['mode'].upper()}
**Running:** {'Yes' if status['running'] else 'No'}
**Cycles Completed:** {status['cycles_completed']}

## Business Agent (ETF DCA)
| Property | Value |
|----------|-------|
| Enabled | {biz['enabled']} |
| Initialized | {biz['initialized']} |
| Budget | ${biz['budget']}/day |
| Strategy | GTI Virtual ETF DCA |
| Exchanges | Coinbase GTI + Kraken Business |

## Personal Agent (Day Trading)
| Property | Value |
|----------|-------|
| Enabled | {per['enabled']} |
| Initialized | {per['initialized']} |
| Budget | ${per['budget']}/day |
| Strategy | Adaptive Day Trade |
| Exchanges | Coinbase Personal + Kraken Personal |

"""
        if status["recent_trades"]:
            md += "## Recent Activity\n"
            md += "| Time | Agent | Type | Trades | Details |\n"
            md += "|------|-------|------|--------|--------|\n"
            for t in status["recent_trades"]:
                ts = t.get("timestamp", "")[:19]
                agent = t.get("agent", "?")
                ttype = t.get("type", "?")
                trades = t.get("trades", 0)
                details = ""
                if agent == "business":
                    details = f"F&G={t.get('fear_greed', '?')}, ${t.get('total_usd', '0')}"
                else:
                    details = f"P&L={t.get('pnl', '0')}"
                md += f"| {ts} | {agent} | {ttype} | {trades} | {details} |\n"

        return md


async def main():
    parser = argparse.ArgumentParser(
        description="GTI Inc Trading Agent Runner"
    )
    parser.add_argument(
        "--mode",
        choices=["paper", "live"],
        default=os.getenv("AGENT_MODE", "paper"),
        help="Trading mode (default: paper)",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=None,
        help="Number of cycles then exit (default: run forever)",
    )
    parser.add_argument(
        "--business-only",
        action="store_true",
        help="Only run business agent",
    )
    parser.add_argument(
        "--personal-only",
        action="store_true",
        help="Only run personal agent",
    )
    parser.add_argument(
        "--log-dir",
        type=str,
        default=os.getenv("AGENT_LOG_DIR", str(DEFAULT_LOG_DIR)),
        help="Directory for trade logs",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose logging",
    )
    args = parser.parse_args()

    # Ensure log directory exists before creating FileHandler
    log_dir_path = Path(args.log_dir)
    log_dir_path.mkdir(parents=True, exist_ok=True)

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                log_dir_path / "agent_runner.log", mode="a"
            ),
        ],
    )

    # Safety confirmation for live mode
    if args.mode == "live":
        print("\n" + "=" * 60)
        print("WARNING: LIVE TRADING MODE")
        print("=" * 60)
        print("This will place REAL orders with REAL money on:")
        if not args.personal_only:
            print("  - Coinbase GTI (Business)")
            print("  - Kraken Business")
        if not args.business_only:
            print("  - Coinbase Personal")
            print("  - Kraken Personal")
        print("=" * 60)
        confirm = input("Type 'yes' to confirm live trading: ").strip().lower()
        if confirm != "yes":
            print("Aborted. Use --mode paper for paper trading.")
            return

    run_business = not args.personal_only
    run_personal = not args.business_only

    runner = AgentRunner(
        mode=args.mode,
        run_business=run_business,
        run_personal=run_personal,
        log_dir=Path(args.log_dir),
    )

    await runner.initialize(max_cycles=args.cycles)

    if args.cycles:
        # Run N cycles immediately then exit
        await runner.run_immediate(cycles=args.cycles)
        await runner.stop()

        # Print summary
        print(runner.format_status_markdown())
    else:
        # Run forever with scheduler
        try:
            await runner.run_forever()
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt")
        finally:
            await runner.stop()

        print(runner.format_status_markdown())


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Local scheduler for automated portfolio management tasks.

Runs in the background and executes:
- Portfolio sync every 15 minutes
- DCA execution daily at configured time
- Staking rewards sync every 6 hours
- Drift checking every hour

Uses APScheduler for reliable task scheduling.
"""

import asyncio
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger

from config import settings, TARGET_ALLOCATION
from exchanges import CoinbaseClient, CoinbasePrimeClient, KrakenClient
from data.prices import PriceService
from data.storage import db
from tracking.portfolio import Portfolio
from tracking.staking import StakingTracker
from agents.rebalancer import Rebalancer
from agents.dca import DCAAgent
from agents.alerts import alert_manager
from agents.dip_buyer import DipBuyingAgent, MarketCondition

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("./data/scheduler.log"),
    ]
)
logger = logging.getLogger("scheduler")


class PortfolioScheduler:
    """Main scheduler for portfolio management tasks."""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.exchanges = {}
        self.clients = []
        self.price_service = None
        self.portfolio = None
        self.staking_tracker = None
        self.dca_agent = None
        self.rebalancer = None
        self.dip_buyer = None
        
        self._running = False
    
    def _init_clients(self):
        """Initialize exchange clients."""
        self.clients = []
        self.exchanges = {}
        
        if settings.coinbase.is_configured:
            client = CoinbaseClient(
                settings.coinbase.api_key,
                settings.coinbase.api_secret,
            )
            self.exchanges["coinbase"] = client
            self.clients.append(client)
            logger.info("Coinbase client initialized")
        
        if settings.coinbase_prime.is_configured:
            client = CoinbasePrimeClient(
                settings.coinbase_prime.api_key,
                settings.coinbase_prime.api_secret,
                settings.coinbase_prime.passphrase,
                settings.coinbase_prime.portfolio_id,
            )
            self.exchanges["coinbase_prime"] = client
            self.clients.append(client)
            logger.info("Coinbase Prime client initialized")
        
        if settings.kraken.is_configured:
            client = KrakenClient(
                settings.kraken.api_key,
                settings.kraken.api_secret,
            )
            self.exchanges["kraken"] = client
            self.clients.append(client)
            logger.info("Kraken client initialized")
        
        if not self.clients:
            logger.warning("No exchange clients configured!")
        
        # Initialize services
        self.price_service = PriceService()
        self.portfolio = Portfolio(self.clients, self.price_service, TARGET_ALLOCATION)
        self.staking_tracker = StakingTracker(self.clients, self.price_service)
        self.dca_agent = DCAAgent(self.exchanges, self.price_service)
        self.rebalancer = Rebalancer(self.portfolio, self.exchanges)
        self.dip_buyer = DipBuyingAgent(self.price_service)
    
    async def _job_sync_portfolio(self):
        """Sync portfolio balances."""
        logger.info("Running portfolio sync...")
        
        try:
            snapshot = await self.portfolio.sync()
            db.save_snapshot(snapshot)
            
            logger.info(
                f"Portfolio synced: ${float(snapshot.total_usd_value):,.2f} total, "
                f"${float(snapshot.total_staked_value):,.2f} staked"
            )
            
            # Save current prices
            for asset, position in snapshot.positions.items():
                if position.price > 0:
                    db.save_price(asset, position.price, snapshot.timestamp)
            
        except Exception as e:
            logger.error(f"Portfolio sync failed: {e}")
            await alert_manager.notify_error("Portfolio Sync Failed", str(e))
    
    async def _job_check_drift(self):
        """Check for allocation drift and send alerts."""
        logger.info("Checking allocation drift...")
        
        try:
            snapshot = await self.portfolio.sync()
            
            if snapshot.needs_rebalance(settings.portfolio.rebalance_threshold):
                # Find assets that need rebalancing
                drift_status = snapshot.get_drift_status(settings.portfolio.rebalance_threshold)
                out_of_balance = [
                    asset for asset, status in drift_status.items()
                    if status != "OK"
                ]
                
                total_drift = sum(abs(float(d)) for d in snapshot.drift.values())
                
                logger.warning(f"Portfolio drift detected: {out_of_balance}")
                
                await alert_manager.notify_rebalance_needed(
                    total_drift,
                    out_of_balance,
                )
            else:
                logger.info("Portfolio within acceptable drift range")
                
        except Exception as e:
            logger.error(f"Drift check failed: {e}")
    
    async def _job_sync_staking(self):
        """Sync staking rewards."""
        logger.info("Syncing staking rewards...")
        
        try:
            count = await self.staking_tracker.sync_rewards()
            
            if count > 0:
                logger.info(f"Added {count} new staking rewards")
                
                # Get recent rewards for notification
                summary = self.staking_tracker.get_summary()
                if summary.total_usd_value > 0:
                    # Notify about largest reward
                    if summary.entries:
                        latest = summary.entries[-1]
                        await alert_manager.notify_staking_reward(
                            latest.asset,
                            float(latest.amount),
                            float(latest.usd_value_at_receipt),
                            latest.source,
                        )
            else:
                logger.info("No new staking rewards")
                
        except Exception as e:
            logger.error(f"Staking sync failed: {e}")
    
    async def _job_check_dips(self):
        """Check for dip buying opportunities."""
        logger.info("Analyzing market for dip opportunities...")
        
        try:
            analysis = await self.dip_buyer.analyze_market()
            
            logger.info(
                f"Market condition: {analysis.overall_condition.value} | "
                f"BTC: {analysis.btc_drawdown:.1%} down | "
                f"ETH: {analysis.eth_drawdown:.1%} down | "
                f"F&G: {analysis.fear_greed_index} | "
                f"Multiplier: {analysis.overall_multiplier:.1f}x"
            )
            
            # Send alert if significant opportunity
            if analysis.overall_condition in (
                MarketCondition.SIGNIFICANT_DIP,
                MarketCondition.EXTREME_DIP,
            ):
                logger.warning(f"SIGNIFICANT DIP DETECTED: {analysis.recommended_action}")
                await self.dip_buyer.send_dip_alert(analysis)
                
        except Exception as e:
            logger.error(f"Dip analysis failed: {e}")
    
    async def _job_execute_dca(self):
        """Execute daily DCA purchases with dip-adjusted amounts."""
        logger.info("Executing DCA...")
        
        try:
            if not self.dca_agent.should_execute_today():
                logger.info("DCA already executed today, skipping")
                return
            
            # Analyze market for dip buying opportunity
            analysis = await self.dip_buyer.analyze_market()
            logger.info(
                f"Market condition: {analysis.overall_condition.value}, "
                f"multiplier: {analysis.overall_multiplier:.2f}x"
            )
            
            # Get adjusted DCA amounts based on dip analysis
            base_daily = float(settings.portfolio.dca_daily_amount)
            adjusted_amounts = self.dip_buyer.get_adjusted_dca_amounts(base_daily, analysis)
            
            # Calculate total adjusted amount
            total_adjusted = sum(float(a) for a in adjusted_amounts.values())
            logger.info(f"Base DCA: ${base_daily:.2f}, Adjusted: ${total_adjusted:.2f}")
            
            # Send alert if significant dip
            if analysis.overall_condition in (
                MarketCondition.MODERATE_DIP,
                MarketCondition.SIGNIFICANT_DIP,
                MarketCondition.EXTREME_DIP,
            ):
                await self.dip_buyer.send_dip_alert(analysis)
            
            # Execute with actual trades (not dry run)
            executions = await self.dca_agent.execute_dca(
                dry_run=False,
                custom_amounts=adjusted_amounts,
            )
            
            # Count successful executions
            successful = [e for e in executions if e.status == "executed"]
            failed = [e for e in executions if e.status == "failed"]
            
            if successful:
                total_amount = sum(float(e.usd_amount) for e in successful)
                assets = [e.asset for e in successful]
                
                logger.info(f"DCA executed: ${total_amount:.2f} across {len(assets)} assets")
                
                await alert_manager.notify_dca_executed(total_amount, assets)
                
                # Save to database
                for execution in successful:
                    db.save_dca_execution(execution)
                    
                    # Create tax lot for each purchase
                    if execution.filled_amount and execution.filled_price:
                        db.add_tax_lot(
                            asset=execution.asset,
                            amount=execution.filled_amount,
                            cost_basis=execution.usd_amount,
                            acquisition_date=execution.timestamp,
                            source="dca",
                        )
            
            if failed:
                for e in failed:
                    logger.error(f"DCA failed for {e.asset}: {e.error}")
                
        except Exception as e:
            logger.error(f"DCA execution failed: {e}")
            await alert_manager.notify_error("DCA Execution Failed", str(e))
    
    def _schedule_jobs(self):
        """Set up scheduled jobs."""
        
        # Portfolio sync - every N minutes
        self.scheduler.add_job(
            self._job_sync_portfolio,
            IntervalTrigger(minutes=settings.scheduler.sync_interval),
            id="sync_portfolio",
            name="Sync Portfolio",
            replace_existing=True,
        )
        
        # Drift check - every hour
        self.scheduler.add_job(
            self._job_check_drift,
            IntervalTrigger(hours=1),
            id="check_drift",
            name="Check Drift",
            replace_existing=True,
        )
        
        # Staking sync - every 6 hours
        self.scheduler.add_job(
            self._job_sync_staking,
            IntervalTrigger(hours=6),
            id="sync_staking",
            name="Sync Staking Rewards",
            replace_existing=True,
        )
        
        # DCA execution - daily at configured time
        hour, minute = settings.scheduler.dca_execution_time.split(":")
        self.scheduler.add_job(
            self._job_execute_dca,
            CronTrigger(hour=int(hour), minute=int(minute)),
            id="execute_dca",
            name="Execute DCA",
            replace_existing=True,
        )
        
        # Dip analysis - every 4 hours
        self.scheduler.add_job(
            self._job_check_dips,
            IntervalTrigger(hours=4),
            id="check_dips",
            name="Check for Dip Opportunities",
            replace_existing=True,
        )
        
        logger.info(f"Scheduled jobs:")
        logger.info(f"  - Portfolio sync: every {settings.scheduler.sync_interval} minutes")
        logger.info(f"  - Drift check: every hour")
        logger.info(f"  - Staking sync: every 6 hours")
        logger.info(f"  - DCA execution: daily at {settings.scheduler.dca_execution_time} UTC")
        logger.info(f"  - Dip analysis: every 4 hours")
    
    async def start(self):
        """Start the scheduler."""
        logger.info("Starting portfolio scheduler...")
        
        self._init_clients()
        self._schedule_jobs()
        
        self.scheduler.start()
        self._running = True
        
        # Run initial sync
        await self._job_sync_portfolio()
        
        logger.info("Scheduler started successfully")
    
    async def stop(self):
        """Stop the scheduler."""
        logger.info("Stopping scheduler...")
        
        self._running = False
        self.scheduler.shutdown()
        
        # Close clients
        for client in self.clients:
            await client.close()
        
        if self.price_service:
            await self.price_service.close()
        
        if self.dip_buyer:
            await self.dip_buyer.close()
        
        logger.info("Scheduler stopped")
    
    async def run_forever(self):
        """Run the scheduler until interrupted."""
        await self.start()
        
        # Set up signal handlers
        loop = asyncio.get_event_loop()
        
        def signal_handler():
            logger.info("Received shutdown signal")
            asyncio.create_task(self.stop())
        
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)
        
        # Keep running
        while self._running:
            await asyncio.sleep(1)


async def main():
    """Main entry point."""
    # Create data directory
    Path("./data").mkdir(exist_ok=True)
    
    scheduler = PortfolioScheduler()
    
    try:
        await scheduler.run_forever()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        await scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main())

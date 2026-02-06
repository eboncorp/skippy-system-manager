"""
Background Job System
=====================

Async task processing for scheduled operations.

Jobs:
- DCA executions (per bot config)
- Alert checks (every 30-60s)
- Portfolio snapshots (hourly/daily)
- Price cache refresh (every 10s)
- Staking reward claims (daily)

Usage:
    from automation.worker import JobScheduler, DCAJob, AlertJob
    
    scheduler = JobScheduler()
    scheduler.add_job(DCAJob())
    scheduler.add_job(AlertJob())
    await scheduler.start()
"""

import asyncio
import logging
import os
import signal
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# JOB CONFIGURATION
# =============================================================================


class JobFrequency(str, Enum):
    """Job execution frequency."""
    SECONDS_10 = "10s"
    SECONDS_30 = "30s"
    MINUTE_1 = "1m"
    MINUTES_5 = "5m"
    MINUTES_15 = "15m"
    MINUTES_30 = "30m"
    HOURLY = "1h"
    DAILY = "24h"
    
    def to_seconds(self) -> int:
        mapping = {
            "10s": 10,
            "30s": 30,
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "30m": 1800,
            "1h": 3600,
            "24h": 86400,
        }
        return mapping[self.value]


class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class JobResult:
    """Result of a job execution."""
    job_name: str
    status: JobStatus
    started_at: datetime
    completed_at: datetime = None
    duration_ms: float = 0
    message: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    def __post_init__(self):
        if self.completed_at is None:
            self.completed_at = datetime.utcnow()
        if self.duration_ms == 0:
            self.duration_ms = (self.completed_at - self.started_at).total_seconds() * 1000


@dataclass
class JobStats:
    """Statistics for a job."""
    total_runs: int = 0
    successful_runs: int = 0
    failed_runs: int = 0
    skipped_runs: int = 0
    total_duration_ms: float = 0
    last_run_at: Optional[datetime] = None
    last_status: Optional[JobStatus] = None
    last_error: Optional[str] = None
    
    @property
    def success_rate(self) -> float:
        total = self.total_runs - self.skipped_runs
        return self.successful_runs / total if total > 0 else 0.0
    
    @property
    def avg_duration_ms(self) -> float:
        return self.total_duration_ms / self.total_runs if self.total_runs > 0 else 0.0


# =============================================================================
# BASE JOB CLASS
# =============================================================================


class BaseJob(ABC):
    """Base class for background jobs."""
    
    def __init__(
        self,
        name: str,
        frequency: JobFrequency = JobFrequency.MINUTE_1,
        enabled: bool = True,
        max_retries: int = 3,
        retry_delay_seconds: int = 5,
    ):
        self.name = name
        self.frequency = frequency
        self.enabled = enabled
        self.max_retries = max_retries
        self.retry_delay = retry_delay_seconds
        self.stats = JobStats()
        self._last_run: Optional[datetime] = None
    
    @abstractmethod
    async def execute(self) -> JobResult:
        """Execute the job. Override in subclass."""
        pass
    
    async def run(self) -> JobResult:
        """Run the job with retry logic."""
        if not self.enabled:
            return JobResult(
                job_name=self.name,
                status=JobStatus.SKIPPED,
                started_at=datetime.utcnow(),
                message="Job disabled",
            )
        
        started_at = datetime.utcnow()
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                result = await self.execute()
                self._update_stats(result)
                return result
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"Job {self.name} attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        
        # All retries failed
        result = JobResult(
            job_name=self.name,
            status=JobStatus.FAILED,
            started_at=started_at,
            error=last_error,
            message=f"Failed after {self.max_retries} attempts",
        )
        self._update_stats(result)
        return result
    
    def _update_stats(self, result: JobResult):
        """Update job statistics."""
        self.stats.total_runs += 1
        self.stats.total_duration_ms += result.duration_ms
        self.stats.last_run_at = result.completed_at
        self.stats.last_status = result.status
        
        if result.status == JobStatus.SUCCESS:
            self.stats.successful_runs += 1
        elif result.status == JobStatus.FAILED:
            self.stats.failed_runs += 1
            self.stats.last_error = result.error
        elif result.status == JobStatus.SKIPPED:
            self.stats.skipped_runs += 1
        
        self._last_run = datetime.utcnow()
    
    def should_run(self) -> bool:
        """Check if job should run based on frequency."""
        if self._last_run is None:
            return True
        
        next_run = self._last_run + timedelta(seconds=self.frequency.to_seconds())
        return datetime.utcnow() >= next_run


# =============================================================================
# CONCRETE JOB IMPLEMENTATIONS
# =============================================================================


class PriceCacheJob(BaseJob):
    """Refresh price cache from exchanges."""
    
    def __init__(self):
        super().__init__(
            name="price_cache",
            frequency=JobFrequency.SECONDS_10,
        )
        self.assets = ["BTC", "ETH", "SOL", "AVAX", "MATIC", "LINK", "UNI", "AAVE"]
    
    async def execute(self) -> JobResult:
        started_at = datetime.utcnow()
        
        try:
            # Import here to avoid circular imports
            from caching import get_cache_manager
            
            cache = get_cache_manager()
            
            # Mock price fetch - replace with real API calls
            prices = {}
            for asset in self.assets:
                # Simulated prices
                base_prices = {"BTC": 45000, "ETH": 2750, "SOL": 120, "AVAX": 35}
                price = base_prices.get(asset, 10)
                prices[asset] = price
            
            # Update cache
            await cache.set_prices(prices)
            
            return JobResult(
                job_name=self.name,
                status=JobStatus.SUCCESS,
                started_at=started_at,
                message=f"Updated {len(prices)} prices",
                data={"prices": prices},
            )
            
        except Exception as e:
            return JobResult(
                job_name=self.name,
                status=JobStatus.FAILED,
                started_at=started_at,
                error=str(e),
            )


class AlertCheckJob(BaseJob):
    """Check and trigger alerts."""
    
    def __init__(self):
        super().__init__(
            name="alert_check",
            frequency=JobFrequency.SECONDS_30,
        )
    
    async def execute(self) -> JobResult:
        started_at = datetime.utcnow()
        
        try:
            # Import dependencies
            from caching import get_cache_manager
            
            cache = get_cache_manager()
            triggered = 0
            
            # Mock alert checking - replace with real implementation
            # alerts = await get_active_alerts()
            # for alert in alerts:
            #     price = await cache.get_price(alert.asset)
            #     if should_trigger(alert, price):
            #         await trigger_alert(alert, price)
            #         triggered += 1
            
            return JobResult(
                job_name=self.name,
                status=JobStatus.SUCCESS,
                started_at=started_at,
                message=f"Checked alerts, triggered {triggered}",
                data={"triggered": triggered},
            )
            
        except Exception as e:
            return JobResult(
                job_name=self.name,
                status=JobStatus.FAILED,
                started_at=started_at,
                error=str(e),
            )


class DCAExecutionJob(BaseJob):
    """Execute scheduled DCA purchases."""
    
    def __init__(self):
        super().__init__(
            name="dca_execution",
            frequency=JobFrequency.MINUTE_1,
            max_retries=1,  # Don't retry DCA to avoid double purchases
        )
    
    async def execute(self) -> JobResult:
        started_at = datetime.utcnow()
        
        try:
            executed = 0
            failed = 0
            
            # Mock DCA execution - replace with real implementation
            # bots = await get_due_dca_bots()
            # for bot in bots:
            #     try:
            #         await execute_dca_purchase(bot)
            #         executed += 1
            #     except Exception as e:
            #         failed += 1
            #         logger.error(f"DCA bot {bot.id} failed: {e}")
            
            return JobResult(
                job_name=self.name,
                status=JobStatus.SUCCESS,
                started_at=started_at,
                message=f"Executed {executed} DCA purchases, {failed} failed",
                data={"executed": executed, "failed": failed},
            )
            
        except Exception as e:
            return JobResult(
                job_name=self.name,
                status=JobStatus.FAILED,
                started_at=started_at,
                error=str(e),
            )


class PortfolioSnapshotJob(BaseJob):
    """Take periodic portfolio snapshots."""
    
    def __init__(self):
        super().__init__(
            name="portfolio_snapshot",
            frequency=JobFrequency.HOURLY,
        )
    
    async def execute(self) -> JobResult:
        started_at = datetime.utcnow()
        
        try:
            # Mock snapshot - replace with real implementation
            # portfolio = await aggregate_portfolio()
            # await save_portfolio_snapshot(portfolio)
            
            total_value = 127834.56  # Mock value
            
            return JobResult(
                job_name=self.name,
                status=JobStatus.SUCCESS,
                started_at=started_at,
                message=f"Snapshot saved: ${total_value:,.2f}",
                data={"total_value": total_value},
            )
            
        except Exception as e:
            return JobResult(
                job_name=self.name,
                status=JobStatus.FAILED,
                started_at=started_at,
                error=str(e),
            )


class StakingRewardsJob(BaseJob):
    """Check and optionally claim staking rewards."""
    
    def __init__(self):
        super().__init__(
            name="staking_rewards",
            frequency=JobFrequency.DAILY,
        )
        self.auto_claim = os.getenv("AUTO_CLAIM_REWARDS", "false").lower() == "true"
    
    async def execute(self) -> JobResult:
        started_at = datetime.utcnow()
        
        try:
            # Mock rewards check - replace with real implementation
            # positions = await get_staking_positions()
            # total_pending = sum(p.pending_rewards for p in positions)
            # 
            # if self.auto_claim and total_pending > 0:
            #     await claim_all_rewards()
            
            total_pending = 0.0234  # Mock ETH rewards
            
            return JobResult(
                job_name=self.name,
                status=JobStatus.SUCCESS,
                started_at=started_at,
                message=f"Pending rewards: {total_pending} ETH",
                data={"pending_rewards": total_pending, "auto_claimed": self.auto_claim},
            )
            
        except Exception as e:
            return JobResult(
                job_name=self.name,
                status=JobStatus.FAILED,
                started_at=started_at,
                error=str(e),
            )


class BalanceSyncJob(BaseJob):
    """Sync balances from all exchanges."""
    
    def __init__(self):
        super().__init__(
            name="balance_sync",
            frequency=JobFrequency.MINUTES_5,
        )
    
    async def execute(self) -> JobResult:
        started_at = datetime.utcnow()
        
        try:
            synced = 0
            exchanges = ["coinbase", "kraken", "gemini"]
            
            for exchange in exchanges:
                # Mock sync - replace with real implementation
                # balances = await fetch_balances(exchange)
                # await cache.set_balance(exchange, balances)
                synced += 1
            
            return JobResult(
                job_name=self.name,
                status=JobStatus.SUCCESS,
                started_at=started_at,
                message=f"Synced {synced} exchanges",
                data={"synced_exchanges": synced},
            )
            
        except Exception as e:
            return JobResult(
                job_name=self.name,
                status=JobStatus.FAILED,
                started_at=started_at,
                error=str(e),
            )


class DataCleanupJob(BaseJob):
    """Clean up old data (price history, logs, etc.)."""
    
    def __init__(self):
        super().__init__(
            name="data_cleanup",
            frequency=JobFrequency.DAILY,
        )
        self.retention_days = int(os.getenv("DATA_RETENTION_DAYS", "90"))
    
    async def execute(self) -> JobResult:
        started_at = datetime.utcnow()
        
        try:
            deleted = 0
            
            # Mock cleanup - replace with real implementation
            # cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
            # deleted += await delete_old_price_history(cutoff)
            # deleted += await delete_old_snapshots(cutoff)
            
            return JobResult(
                job_name=self.name,
                status=JobStatus.SUCCESS,
                started_at=started_at,
                message=f"Cleaned up {deleted} old records",
                data={"deleted_records": deleted, "retention_days": self.retention_days},
            )
            
        except Exception as e:
            return JobResult(
                job_name=self.name,
                status=JobStatus.FAILED,
                started_at=started_at,
                error=str(e),
            )


# =============================================================================
# JOB SCHEDULER
# =============================================================================


class JobScheduler:
    """
    Background job scheduler.
    
    Usage:
        scheduler = JobScheduler()
        scheduler.add_job(PriceCacheJob())
        scheduler.add_job(AlertCheckJob())
        await scheduler.start()
    """
    
    def __init__(self):
        self.jobs: Dict[str, BaseJob] = {}
        self.running = False
        self._tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
    
    def add_job(self, job: BaseJob):
        """Add a job to the scheduler."""
        self.jobs[job.name] = job
        logger.info(f"Added job: {job.name} (frequency: {job.frequency.value})")
    
    def remove_job(self, job_name: str):
        """Remove a job from the scheduler."""
        if job_name in self.jobs:
            del self.jobs[job_name]
            logger.info(f"Removed job: {job_name}")
    
    def enable_job(self, job_name: str):
        """Enable a job."""
        if job_name in self.jobs:
            self.jobs[job_name].enabled = True
    
    def disable_job(self, job_name: str):
        """Disable a job."""
        if job_name in self.jobs:
            self.jobs[job_name].enabled = False
    
    async def run_job(self, job_name: str) -> Optional[JobResult]:
        """Manually run a specific job."""
        if job_name in self.jobs:
            return await self.jobs[job_name].run()
        return None
    
    async def _job_loop(self, job: BaseJob):
        """Main loop for a single job."""
        while self.running:
            try:
                if job.should_run():
                    result = await job.run()
                    
                    if result.status == JobStatus.FAILED:
                        logger.warning(f"Job {job.name} failed: {result.error}")
                    else:
                        logger.debug(f"Job {job.name} completed: {result.message}")
                
                # Sleep for a fraction of the frequency to check more often
                await asyncio.sleep(min(job.frequency.to_seconds() / 2, 10))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Job loop error for {job.name}: {e}")
                await asyncio.sleep(5)
    
    async def start(self):
        """Start the scheduler."""
        self.running = True
        logger.info(f"Starting job scheduler with {len(self.jobs)} jobs")
        
        # Setup signal handlers
        for sig in (signal.SIGTERM, signal.SIGINT):
            asyncio.get_event_loop().add_signal_handler(
                sig,
                lambda: asyncio.create_task(self.stop())
            )
        
        # Start job loops
        for job in self.jobs.values():
            task = asyncio.create_task(self._job_loop(job))
            self._tasks.append(task)
        
        # Wait for shutdown
        await self._shutdown_event.wait()
    
    async def stop(self):
        """Stop the scheduler."""
        logger.info("Stopping job scheduler...")
        self.running = False
        
        # Cancel all tasks
        for task in self._tasks:
            task.cancel()
        
        await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []
        self._shutdown_event.set()
        
        logger.info("Job scheduler stopped")
    
    def get_stats(self) -> Dict[str, Dict]:
        """Get statistics for all jobs."""
        return {
            name: {
                "enabled": job.enabled,
                "frequency": job.frequency.value,
                "total_runs": job.stats.total_runs,
                "success_rate": f"{job.stats.success_rate:.1%}",
                "avg_duration_ms": f"{job.stats.avg_duration_ms:.1f}",
                "last_run": job.stats.last_run_at.isoformat() if job.stats.last_run_at else None,
                "last_status": job.stats.last_status.value if job.stats.last_status else None,
                "last_error": job.stats.last_error,
            }
            for name, job in self.jobs.items()
        }


# =============================================================================
# WORKER PROCESS
# =============================================================================


async def run_worker():
    """Main worker process entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    logger.info("Starting background worker...")
    
    # Initialize cache
    from caching import init_cache
    await init_cache()
    
    # Create scheduler with default jobs
    scheduler = JobScheduler()
    scheduler.add_job(PriceCacheJob())
    scheduler.add_job(AlertCheckJob())
    scheduler.add_job(DCAExecutionJob())
    scheduler.add_job(PortfolioSnapshotJob())
    scheduler.add_job(BalanceSyncJob())
    scheduler.add_job(StakingRewardsJob())
    scheduler.add_job(DataCleanupJob())
    
    # Disable DCA in paper trading mode
    if os.getenv("PAPER_TRADING", "true").lower() == "true":
        logger.info("Paper trading mode - DCA execution disabled")
        scheduler.disable_job("dca_execution")
    
    # Run scheduler
    try:
        await scheduler.start()
    except KeyboardInterrupt:
        await scheduler.stop()
    
    logger.info("Background worker stopped")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


def main():
    """CLI entry point for the worker."""
    asyncio.run(run_worker())


if __name__ == "__main__":
    main()

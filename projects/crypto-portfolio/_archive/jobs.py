"""
Background Job System
=====================

Async task processing for scheduled operations.

Jobs:
- DCA bot executions
- Alert monitoring
- Portfolio snapshots
- Price cache refresh
- Staking reward claims

Usage:
    from jobs import JobScheduler, Job
    
    scheduler = JobScheduler()
    
    @scheduler.job("price_refresh", interval=30)
    async def refresh_prices():
        ...
    
    await scheduler.start()
"""

import asyncio
import functools
import logging
import os
import signal
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
import uuid

logger = logging.getLogger(__name__)


# =============================================================================
# JOB CONFIGURATION
# =============================================================================


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(int, Enum):
    LOW = 1
    NORMAL = 5
    HIGH = 10
    CRITICAL = 20


@dataclass
class JobConfig:
    """Job configuration."""
    name: str
    interval: Optional[int] = None  # Seconds between runs
    cron: Optional[str] = None  # Cron expression
    timeout: int = 300  # Max execution time
    retries: int = 3  # Number of retries on failure
    retry_delay: int = 60  # Seconds between retries
    priority: JobPriority = JobPriority.NORMAL
    enabled: bool = True


@dataclass
class JobResult:
    """Result of job execution."""
    job_id: str
    job_name: str
    status: JobStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0
    result: Any = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    retry_count: int = 0


@dataclass
class ScheduledJob:
    """A scheduled job instance."""
    id: str
    config: JobConfig
    func: Callable
    next_run: datetime
    last_run: Optional[datetime] = None
    last_result: Optional[JobResult] = None
    run_count: int = 0
    error_count: int = 0
    is_running: bool = False


# =============================================================================
# CRON PARSER (SIMPLE)
# =============================================================================


class SimpleCronParser:
    """
    Simple cron expression parser.
    
    Supports:
    - * (any)
    - */n (every n)
    - n (specific value)
    - n,m,o (list)
    
    Format: minute hour day_of_month month day_of_week
    """
    
    @staticmethod
    def parse(expression: str) -> Dict[str, List[int]]:
        """Parse cron expression."""
        parts = expression.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {expression}")
        
        ranges = [
            (0, 59),   # minute
            (0, 23),   # hour
            (1, 31),   # day of month
            (1, 12),   # month
            (0, 6),    # day of week (0 = Sunday)
        ]
        
        result = {}
        names = ["minute", "hour", "day", "month", "weekday"]
        
        for i, (part, (min_val, max_val)) in enumerate(zip(parts, ranges)):
            result[names[i]] = SimpleCronParser._parse_field(part, min_val, max_val)
        
        return result
    
    @staticmethod
    def _parse_field(field: str, min_val: int, max_val: int) -> List[int]:
        """Parse a single cron field."""
        if field == "*":
            return list(range(min_val, max_val + 1))
        
        if field.startswith("*/"):
            step = int(field[2:])
            return list(range(min_val, max_val + 1, step))
        
        if "," in field:
            return [int(v) for v in field.split(",")]
        
        return [int(field)]
    
    @staticmethod
    def next_run(expression: str, from_time: Optional[datetime] = None) -> datetime:
        """Calculate next run time for cron expression."""
        parsed = SimpleCronParser.parse(expression)
        now = from_time or datetime.utcnow()
        
        # Start from next minute
        candidate = now.replace(second=0, microsecond=0) + timedelta(minutes=1)
        
        # Search for next matching time (max 1 year ahead)
        max_iterations = 365 * 24 * 60
        for _ in range(max_iterations):
            if (candidate.minute in parsed["minute"] and
                candidate.hour in parsed["hour"] and
                candidate.day in parsed["day"] and
                candidate.month in parsed["month"] and
                candidate.weekday() in parsed["weekday"]):
                return candidate
            candidate += timedelta(minutes=1)
        
        raise ValueError(f"Could not find next run time for: {expression}")


# =============================================================================
# JOB SCHEDULER
# =============================================================================


class JobScheduler:
    """
    Async job scheduler.
    
    Usage:
        scheduler = JobScheduler()
        
        @scheduler.job("price_refresh", interval=30)
        async def refresh_prices():
            # Refresh price cache
            pass
        
        @scheduler.job("dca_execution", cron="0 * * * *")  # Every hour
        async def execute_dca_bots():
            # Execute DCA bots
            pass
        
        await scheduler.start()
    """
    
    def __init__(self, max_concurrent: int = 10):
        self.jobs: Dict[str, ScheduledJob] = {}
        self.max_concurrent = max_concurrent
        self.running = False
        self._semaphore: Optional[asyncio.Semaphore] = None
        self._tasks: List[asyncio.Task] = []
        self._shutdown_event = asyncio.Event()
        
        # Job history (last N results)
        self.history: List[JobResult] = []
        self.max_history = 1000
        
        # Metrics
        self.metrics = {
            "jobs_executed": 0,
            "jobs_succeeded": 0,
            "jobs_failed": 0,
            "total_duration": 0.0
        }
    
    def job(
        self,
        name: str,
        interval: Optional[int] = None,
        cron: Optional[str] = None,
        timeout: int = 300,
        retries: int = 3,
        priority: JobPriority = JobPriority.NORMAL,
        enabled: bool = True
    ):
        """
        Decorator to register a job.
        
        Args:
            name: Unique job name
            interval: Seconds between runs (mutually exclusive with cron)
            cron: Cron expression (mutually exclusive with interval)
            timeout: Max execution time in seconds
            retries: Number of retry attempts
            priority: Job priority
            enabled: Whether job is enabled
        """
        if not interval and not cron:
            raise ValueError("Either interval or cron must be specified")
        
        def decorator(func: Callable):
            config = JobConfig(
                name=name,
                interval=interval,
                cron=cron,
                timeout=timeout,
                retries=retries,
                priority=priority,
                enabled=enabled
            )
            
            self.register(config, func)
            
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)
            
            return wrapper
        
        return decorator
    
    def register(self, config: JobConfig, func: Callable):
        """Register a job with configuration."""
        # Calculate initial next run
        if config.interval:
            next_run = datetime.utcnow() + timedelta(seconds=config.interval)
        else:
            next_run = SimpleCronParser.next_run(config.cron)
        
        job = ScheduledJob(
            id=str(uuid.uuid4()),
            config=config,
            func=func,
            next_run=next_run
        )
        
        self.jobs[config.name] = job
        logger.info(f"Registered job: {config.name}, next run: {next_run}")
    
    def unregister(self, name: str):
        """Unregister a job."""
        if name in self.jobs:
            del self.jobs[name]
            logger.info(f"Unregistered job: {name}")
    
    def enable(self, name: str):
        """Enable a job."""
        if name in self.jobs:
            self.jobs[name].config.enabled = True
    
    def disable(self, name: str):
        """Disable a job."""
        if name in self.jobs:
            self.jobs[name].config.enabled = False
    
    async def run_job(self, name: str, force: bool = False) -> JobResult:
        """
        Run a job immediately.
        
        Args:
            name: Job name
            force: Run even if disabled
        
        Returns:
            JobResult
        """
        if name not in self.jobs:
            raise ValueError(f"Unknown job: {name}")
        
        job = self.jobs[name]
        
        if not force and not job.config.enabled:
            raise ValueError(f"Job {name} is disabled")
        
        return await self._execute_job(job)
    
    async def _execute_job(self, job: ScheduledJob, retry_count: int = 0) -> JobResult:
        """Execute a job with retry handling."""
        job_id = str(uuid.uuid4())
        started_at = datetime.utcnow()
        job.is_running = True
        
        result = JobResult(
            job_id=job_id,
            job_name=job.config.name,
            status=JobStatus.RUNNING,
            started_at=started_at,
            retry_count=retry_count
        )
        
        try:
            logger.info(f"Starting job: {job.config.name} (attempt {retry_count + 1})")
            
            # Execute with timeout
            if asyncio.iscoroutinefunction(job.func):
                job_result = await asyncio.wait_for(
                    job.func(),
                    timeout=job.config.timeout
                )
            else:
                # Run sync function in executor
                loop = asyncio.get_event_loop()
                job_result = await asyncio.wait_for(
                    loop.run_in_executor(None, job.func),
                    timeout=job.config.timeout
                )
            
            result.status = JobStatus.COMPLETED
            result.result = job_result
            
            job.run_count += 1
            self.metrics["jobs_succeeded"] += 1
            
            logger.info(f"Job completed: {job.config.name}")
            
        except asyncio.TimeoutError:
            result.status = JobStatus.FAILED
            result.error = f"Job timed out after {job.config.timeout}s"
            logger.error(f"Job timeout: {job.config.name}")
            
        except Exception as e:
            result.status = JobStatus.FAILED
            result.error = str(e)
            result.traceback = traceback.format_exc()
            logger.error(f"Job failed: {job.config.name}: {e}")
            
            # Retry if configured
            if retry_count < job.config.retries:
                logger.info(f"Retrying job {job.config.name} in {job.config.retry_delay}s")
                await asyncio.sleep(job.config.retry_delay)
                return await self._execute_job(job, retry_count + 1)
            
            job.error_count += 1
            self.metrics["jobs_failed"] += 1
        
        finally:
            result.completed_at = datetime.utcnow()
            result.duration_seconds = (result.completed_at - started_at).total_seconds()
            job.is_running = False
            job.last_run = started_at
            job.last_result = result
            
            self.metrics["jobs_executed"] += 1
            self.metrics["total_duration"] += result.duration_seconds
            
            # Update next run
            if job.config.interval:
                job.next_run = datetime.utcnow() + timedelta(seconds=job.config.interval)
            else:
                job.next_run = SimpleCronParser.next_run(job.config.cron)
            
            # Add to history
            self.history.insert(0, result)
            if len(self.history) > self.max_history:
                self.history = self.history[:self.max_history]
        
        return result
    
    async def _scheduler_loop(self):
        """Main scheduler loop."""
        logger.info("Scheduler loop started")
        
        while self.running:
            now = datetime.utcnow()
            
            # Find jobs that need to run
            pending_jobs = [
                job for job in self.jobs.values()
                if job.config.enabled and
                not job.is_running and
                job.next_run <= now
            ]
            
            # Sort by priority (highest first)
            pending_jobs.sort(key=lambda j: j.config.priority, reverse=True)
            
            # Schedule jobs (respecting concurrency limit)
            for job in pending_jobs:
                if self._semaphore:
                    asyncio.create_task(self._run_with_semaphore(job))
                else:
                    asyncio.create_task(self._execute_job(job))
            
            # Sleep until next check (1 second)
            await asyncio.sleep(1)
    
    async def _run_with_semaphore(self, job: ScheduledJob):
        """Run job with semaphore for concurrency control."""
        async with self._semaphore:
            await self._execute_job(job)
    
    async def start(self):
        """Start the scheduler."""
        if self.running:
            return
        
        self.running = True
        self._semaphore = asyncio.Semaphore(self.max_concurrent)
        self._shutdown_event.clear()
        
        logger.info(f"Starting job scheduler with {len(self.jobs)} jobs")
        
        # Start scheduler loop
        task = asyncio.create_task(self._scheduler_loop())
        self._tasks.append(task)
        
        # Wait for shutdown
        await self._shutdown_event.wait()
    
    async def stop(self):
        """Stop the scheduler gracefully."""
        logger.info("Stopping job scheduler...")
        self.running = False
        
        # Wait for running jobs to complete (with timeout)
        running_jobs = [j for j in self.jobs.values() if j.is_running]
        if running_jobs:
            logger.info(f"Waiting for {len(running_jobs)} running jobs to complete...")
            await asyncio.sleep(5)  # Give jobs time to finish
        
        # Cancel remaining tasks
        for task in self._tasks:
            task.cancel()
        
        self._shutdown_event.set()
        logger.info("Job scheduler stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get scheduler status."""
        return {
            "running": self.running,
            "jobs": {
                name: {
                    "enabled": job.config.enabled,
                    "is_running": job.is_running,
                    "next_run": job.next_run.isoformat() if job.next_run else None,
                    "last_run": job.last_run.isoformat() if job.last_run else None,
                    "run_count": job.run_count,
                    "error_count": job.error_count,
                    "last_status": job.last_result.status.value if job.last_result else None
                }
                for name, job in self.jobs.items()
            },
            "metrics": self.metrics
        }


# =============================================================================
# PREDEFINED JOBS
# =============================================================================


class CryptoJobs:
    """
    Predefined jobs for crypto portfolio management.
    
    Usage:
        jobs = CryptoJobs(scheduler, cache, exchanges)
        jobs.register_all()
    """
    
    def __init__(
        self,
        scheduler: JobScheduler,
        cache=None,
        exchanges=None,
        notifications=None
    ):
        self.scheduler = scheduler
        self.cache = cache
        self.exchanges = exchanges or {}
        self.notifications = notifications
    
    def register_all(self):
        """Register all predefined jobs."""
        self.register_price_refresh()
        self.register_portfolio_snapshot()
        self.register_alert_monitor()
        self.register_dca_executor()
        self.register_staking_rewards()
    
    def register_price_refresh(self, interval: int = 30):
        """Register price cache refresh job."""
        
        @self.scheduler.job("price_refresh", interval=interval, priority=JobPriority.HIGH)
        async def refresh_prices():
            """Refresh cached prices from exchanges."""
            if not self.cache:
                return {"skipped": "no cache configured"}
            
            prices = {}
            for name, exchange in self.exchanges.items():
                try:
                    # Get prices for common assets
                    for asset in ["BTC", "ETH", "SOL", "AVAX"]:
                        symbol = f"{asset}-USD"
                        price = await exchange.get_price(symbol)
                        prices[asset] = float(price)
                except Exception as e:
                    logger.error(f"Failed to get prices from {name}: {e}")
            
            if prices:
                await self.cache.set_prices(prices)
            
            return {"updated": len(prices), "prices": prices}
        
        return refresh_prices
    
    def register_portfolio_snapshot(self, cron: str = "0 * * * *"):
        """Register hourly portfolio snapshot job."""
        
        @self.scheduler.job("portfolio_snapshot", cron=cron)
        async def take_snapshot():
            """Take portfolio snapshot for historical tracking."""
            total_value = 0
            holdings = {}
            
            for name, exchange in self.exchanges.items():
                try:
                    balances = await exchange.get_balances()
                    for asset, balance in balances.items():
                        if float(balance.get("total", 0)) > 0:
                            holdings[f"{name}:{asset}"] = {
                                "amount": str(balance["total"]),
                                "available": str(balance["available"])
                            }
                except Exception as e:
                    logger.error(f"Failed to get balances from {name}: {e}")
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "holdings_count": len(holdings),
                "total_value_usd": total_value
            }
        
        return take_snapshot
    
    def register_alert_monitor(self, interval: int = 60):
        """Register alert monitoring job."""
        
        @self.scheduler.job("alert_monitor", interval=interval, priority=JobPriority.HIGH)
        async def check_alerts():
            """Check price alerts and trigger notifications."""
            triggered = []
            
            # This would integrate with the database to check active alerts
            # For now, return placeholder
            
            return {
                "checked": 0,
                "triggered": triggered
            }
        
        return check_alerts
    
    def register_dca_executor(self, cron: str = "*/15 * * * *"):
        """Register DCA bot executor job."""
        
        @self.scheduler.job("dca_executor", cron=cron, timeout=600)
        async def execute_dca_bots():
            """Execute pending DCA bot orders."""
            executed = []
            
            # This would integrate with the database to find pending DCA executions
            # For now, return placeholder
            
            return {
                "executed": len(executed),
                "orders": executed
            }
        
        return execute_dca_bots
    
    def register_staking_rewards(self, cron: str = "0 0 * * *"):
        """Register daily staking rewards claim job."""
        
        @self.scheduler.job("staking_rewards", cron=cron, timeout=900)
        async def claim_staking_rewards():
            """Claim accumulated staking rewards."""
            claimed = {}
            
            for name, exchange in self.exchanges.items():
                try:
                    rewards = await exchange.claim_staking_rewards()
                    if rewards:
                        claimed[name] = rewards
                except Exception as e:
                    logger.error(f"Failed to claim rewards from {name}: {e}")
            
            return {
                "claimed": claimed,
                "total_exchanges": len(claimed)
            }
        
        return claim_staking_rewards


# =============================================================================
# WORKER PROCESS
# =============================================================================


async def run_worker():
    """
    Run the background worker process.
    
    This is the main entry point for the worker container.
    """
    logger.info("Starting crypto portfolio worker...")
    
    # Initialize components
    scheduler = JobScheduler(max_concurrent=5)
    
    # Import and initialize dependencies
    try:
        from cache import CacheManager
        cache = CacheManager()
        await cache.connect()
    except ImportError:
        cache = None
        logger.warning("Cache module not available")
    
    try:
        from exchanges.mock import MockExchangeFactory
        exchanges = MockExchangeFactory.create_all()
    except ImportError:
        exchanges = {}
        logger.warning("Exchange modules not available")
    
    # Register jobs
    jobs = CryptoJobs(scheduler, cache, exchanges)
    jobs.register_all()
    
    # Setup signal handlers
    loop = asyncio.get_event_loop()
    
    def handle_shutdown(sig):
        logger.info(f"Received signal {sig}, shutting down...")
        asyncio.create_task(scheduler.stop())
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, functools.partial(handle_shutdown, sig))
    
    # Start scheduler
    try:
        await scheduler.start()
    except asyncio.CancelledError:
        pass
    finally:
        if cache:
            await cache.disconnect()
        logger.info("Worker shutdown complete")


# =============================================================================
# EXAMPLE USAGE
# =============================================================================


async def example_usage():
    """Demonstrate job scheduler."""
    scheduler = JobScheduler()
    
    # Register a simple interval job
    @scheduler.job("heartbeat", interval=5)
    async def heartbeat():
        logger.info("Heartbeat!")
        return {"time": datetime.utcnow().isoformat()}
    
    # Register a cron job
    @scheduler.job("hourly_task", cron="0 * * * *", enabled=False)
    async def hourly_task():
        logger.info("Running hourly task")
        return {"status": "completed"}
    
    # Register a job that might fail
    @scheduler.job("flaky_job", interval=10, retries=2)
    async def flaky_job():
        import random
        if random.random() < 0.5:
            raise Exception("Random failure!")
        return {"success": True}
    
    # Print status
    print("Registered jobs:")
    for name, job in scheduler.jobs.items():
        print(f"  - {name}: next run {job.next_run}")
    
    # Run for 20 seconds
    async def shutdown_after(seconds):
        await asyncio.sleep(seconds)
        await scheduler.stop()
    
    asyncio.create_task(shutdown_after(20))
    
    await scheduler.start()
    
    # Print final status
    print("\nFinal status:")
    print(json.dumps(scheduler.get_status(), indent=2, default=str))


if __name__ == "__main__":
    import json
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_usage())

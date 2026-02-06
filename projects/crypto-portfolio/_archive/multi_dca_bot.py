"""
Multi-Exchange DCA (Dollar-Cost Averaging) Bot
Schedule recurring purchases across Coinbase, Kraken, Crypto.com, and Gemini.

Features:
- Configurable schedules per asset/exchange
- Smart routing to lowest-fee exchange
- Notifications on execution
- Dry-run mode for testing
"""

import os
import json
import time
import schedule
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv


class DCAInterval(Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


@dataclass
class DCASchedule:
    """A DCA schedule configuration."""
    schedule_id: str
    asset: str
    amount_usd: float
    interval: DCAInterval
    exchange: str  # "coinbase", "kraken", "cryptocom", "gemini", or "auto"
    enabled: bool = True
    day_of_week: int = None  # 0=Monday, 6=Sunday (for weekly)
    day_of_month: int = None  # 1-28 (for monthly)
    hour: int = 9  # Hour to execute (0-23)
    last_execution: datetime = None
    total_invested: float = 0
    total_units_bought: float = 0
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d["interval"] = self.interval.value
        d["last_execution"] = self.last_execution.isoformat() if self.last_execution else None
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'DCASchedule':
        data["interval"] = DCAInterval(data["interval"])
        if data.get("last_execution"):
            data["last_execution"] = datetime.fromisoformat(data["last_execution"])
        return cls(**data)


@dataclass 
class DCAExecution:
    """Record of a DCA execution."""
    schedule_id: str
    timestamp: datetime
    asset: str
    amount_usd: float
    units_bought: float
    price_per_unit: float
    exchange: str
    order_id: Optional[str] = None
    status: str = "success"  # success, failed, dry_run
    error: Optional[str] = None


class MultiExchangeDCABot:
    """
    DCA bot supporting multiple exchanges.
    """
    
    CONFIG_FILE = "dca_config.json"
    HISTORY_FILE = "dca_history.json"
    
    def __init__(self, config_dir: str = None, dry_run: bool = False):
        load_dotenv()
        
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(__file__), "data")
        
        self.config_dir = config_dir
        Path(config_dir).mkdir(parents=True, exist_ok=True)
        
        self.config_path = os.path.join(config_dir, self.CONFIG_FILE)
        self.history_path = os.path.join(config_dir, self.HISTORY_FILE)
        
        self.dry_run = dry_run
        self.schedules: Dict[str, DCASchedule] = self._load_schedules()
        self.history: List[DCAExecution] = []
        
        # Initialize exchange clients
        self.clients = {}
        self._init_clients()
        
        # Notification manager (optional)
        self.notifier = None
        self._init_notifier()
    
    def _init_clients(self):
        """Initialize exchange clients."""
        from coinbase_client import CoinbaseClient
        from kraken_client import KrakenClient
        from cryptocom_client import CryptoComClient
        from gemini_client import GeminiClient
        
        # Coinbase
        if os.getenv("COINBASE_API_KEY"):
            self.clients["coinbase"] = CoinbaseClient(
                os.getenv("COINBASE_API_KEY"),
                os.getenv("COINBASE_API_SECRET")
            )
        
        # Kraken
        if os.getenv("KRAKEN_API_KEY"):
            self.clients["kraken"] = KrakenClient(
                os.getenv("KRAKEN_API_KEY"),
                os.getenv("KRAKEN_API_SECRET")
            )
        
        # Crypto.com
        if os.getenv("CRYPTOCOM_API_KEY"):
            self.clients["cryptocom"] = CryptoComClient(
                os.getenv("CRYPTOCOM_API_KEY"),
                os.getenv("CRYPTOCOM_API_SECRET")
            )
        
        # Gemini
        if os.getenv("GEMINI_API_KEY"):
            self.clients["gemini"] = GeminiClient(
                os.getenv("GEMINI_API_KEY"),
                os.getenv("GEMINI_API_SECRET")
            )
    
    def _init_notifier(self):
        """Initialize notification manager if configured."""
        try:
            from notifications import NotificationManager
            self.notifier = NotificationManager()
        except ImportError:
            pass
    
    def _load_schedules(self) -> Dict[str, DCASchedule]:
        """Load DCA schedules from config file."""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                return {
                    k: DCASchedule.from_dict(v)
                    for k, v in data.items()
                }
        return {}
    
    def _save_schedules(self):
        """Save DCA schedules to config file."""
        with open(self.config_path, 'w') as f:
            json.dump(
                {k: v.to_dict() for k, v in self.schedules.items()},
                f,
                indent=2
            )
    
    def _save_execution(self, execution: DCAExecution):
        """Save execution to history."""
        history = []
        if os.path.exists(self.history_path):
            with open(self.history_path, 'r') as f:
                history = json.load(f)
        
        history.append({
            "schedule_id": execution.schedule_id,
            "timestamp": execution.timestamp.isoformat(),
            "asset": execution.asset,
            "amount_usd": execution.amount_usd,
            "units_bought": execution.units_bought,
            "price_per_unit": execution.price_per_unit,
            "exchange": execution.exchange,
            "order_id": execution.order_id,
            "status": execution.status,
            "error": execution.error
        })
        
        with open(self.history_path, 'w') as f:
            json.dump(history, f, indent=2)
    
    def add_schedule(
        self,
        asset: str,
        amount_usd: float,
        interval: DCAInterval,
        exchange: str = "auto",
        day_of_week: int = None,
        day_of_month: int = None,
        hour: int = 9
    ) -> DCASchedule:
        """
        Add a new DCA schedule.
        
        Args:
            asset: Asset to buy (e.g., "BTC", "ETH")
            amount_usd: USD amount per purchase
            interval: How often to buy
            exchange: Exchange to use ("auto" picks best price)
            day_of_week: Day for weekly schedules (0=Monday)
            day_of_month: Day for monthly schedules (1-28)
            hour: Hour to execute (0-23)
        """
        import uuid
        
        schedule_id = str(uuid.uuid4())[:8]
        
        sched = DCASchedule(
            schedule_id=schedule_id,
            asset=asset.upper(),
            amount_usd=amount_usd,
            interval=interval,
            exchange=exchange.lower(),
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            hour=hour
        )
        
        self.schedules[schedule_id] = sched
        self._save_schedules()
        
        return sched
    
    def remove_schedule(self, schedule_id: str):
        """Remove a DCA schedule."""
        if schedule_id in self.schedules:
            del self.schedules[schedule_id]
            self._save_schedules()
            print(f"✓ Removed schedule {schedule_id}")
        else:
            print(f"Schedule {schedule_id} not found")
    
    def enable_schedule(self, schedule_id: str, enabled: bool = True):
        """Enable or disable a schedule."""
        if schedule_id in self.schedules:
            self.schedules[schedule_id].enabled = enabled
            self._save_schedules()
            status = "enabled" if enabled else "disabled"
            print(f"✓ Schedule {schedule_id} {status}")
    
    def list_schedules(self) -> List[DCASchedule]:
        """List all schedules."""
        return list(self.schedules.values())
    
    def get_best_exchange(self, asset: str) -> Optional[str]:
        """Find exchange with best price for an asset."""
        best_exchange = None
        best_price = float('inf')
        
        for exchange_name, client in self.clients.items():
            try:
                price = client.get_spot_price(asset, "USD")
                if price and price < best_price:
                    best_price = price
                    best_exchange = exchange_name
            except Exception as e:
                print(f"Error getting price from {exchange_name}: {e}")
        
        return best_exchange
    
    def get_exchange_product_id(self, exchange: str, asset: str) -> str:
        """Get the product/pair ID for an exchange."""
        if exchange == "coinbase":
            return f"{asset}-USD"
        elif exchange == "kraken":
            # Kraken uses XBT for BTC
            kraken_asset = "XBT" if asset == "BTC" else asset
            return f"{kraken_asset}USD"
        elif exchange == "cryptocom":
            return f"{asset}_USD"
        elif exchange == "gemini":
            return f"{asset.lower()}usd"
        return f"{asset}-USD"
    
    def execute_buy(
        self,
        schedule: DCASchedule
    ) -> DCAExecution:
        """Execute a DCA buy order."""
        timestamp = datetime.now()
        
        # Determine exchange
        exchange = schedule.exchange
        if exchange == "auto":
            exchange = self.get_best_exchange(schedule.asset)
            if not exchange:
                return DCAExecution(
                    schedule_id=schedule.schedule_id,
                    timestamp=timestamp,
                    asset=schedule.asset,
                    amount_usd=schedule.amount_usd,
                    units_bought=0,
                    price_per_unit=0,
                    exchange="unknown",
                    status="failed",
                    error="No exchange available"
                )
        
        if exchange not in self.clients:
            return DCAExecution(
                schedule_id=schedule.schedule_id,
                timestamp=timestamp,
                asset=schedule.asset,
                amount_usd=schedule.amount_usd,
                units_bought=0,
                price_per_unit=0,
                exchange=exchange,
                status="failed",
                error=f"Exchange {exchange} not configured"
            )
        
        client = self.clients[exchange]
        product_id = self.get_exchange_product_id(exchange, schedule.asset)
        
        # Get current price
        price = client.get_spot_price(schedule.asset, "USD")
        if not price:
            return DCAExecution(
                schedule_id=schedule.schedule_id,
                timestamp=timestamp,
                asset=schedule.asset,
                amount_usd=schedule.amount_usd,
                units_bought=0,
                price_per_unit=0,
                exchange=exchange,
                status="failed",
                error="Could not get price"
            )
        
        units_to_buy = schedule.amount_usd / price
        
        # Execute or simulate
        if self.dry_run:
            execution = DCAExecution(
                schedule_id=schedule.schedule_id,
                timestamp=timestamp,
                asset=schedule.asset,
                amount_usd=schedule.amount_usd,
                units_bought=units_to_buy,
                price_per_unit=price,
                exchange=exchange,
                status="dry_run"
            )
        else:
            try:
                # Execute market buy
                result = client.market_buy(product_id, schedule.amount_usd)
                
                if result:
                    # Extract order ID (varies by exchange)
                    order_id = None
                    if isinstance(result, dict):
                        order_id = result.get("order_id") or result.get("txid") or result.get("id")
                    
                    execution = DCAExecution(
                        schedule_id=schedule.schedule_id,
                        timestamp=timestamp,
                        asset=schedule.asset,
                        amount_usd=schedule.amount_usd,
                        units_bought=units_to_buy,
                        price_per_unit=price,
                        exchange=exchange,
                        order_id=str(order_id) if order_id else None,
                        status="success"
                    )
                    
                    # Update schedule stats
                    schedule.last_execution = timestamp
                    schedule.total_invested += schedule.amount_usd
                    schedule.total_units_bought += units_to_buy
                    self._save_schedules()
                else:
                    execution = DCAExecution(
                        schedule_id=schedule.schedule_id,
                        timestamp=timestamp,
                        asset=schedule.asset,
                        amount_usd=schedule.amount_usd,
                        units_bought=0,
                        price_per_unit=price,
                        exchange=exchange,
                        status="failed",
                        error="Order returned no result"
                    )
            
            except Exception as e:
                execution = DCAExecution(
                    schedule_id=schedule.schedule_id,
                    timestamp=timestamp,
                    asset=schedule.asset,
                    amount_usd=schedule.amount_usd,
                    units_bought=0,
                    price_per_unit=price,
                    exchange=exchange,
                    status="failed",
                    error=str(e)
                )
        
        # Save execution history
        self._save_execution(execution)
        
        # Send notification
        if self.notifier:
            if execution.status == "success":
                self.notifier.send_trade_alert(
                    action="BUY",
                    asset=execution.asset,
                    amount=execution.units_bought,
                    price=execution.price_per_unit,
                    exchange=execution.exchange,
                    order_id=execution.order_id
                )
            elif execution.status == "failed":
                self.notifier.send_alert(
                    title=f"DCA Failed: {execution.asset}",
                    message=f"Failed to buy {execution.asset} on {execution.exchange}\nError: {execution.error}",
                    level="warning"
                )
        
        return execution
    
    def should_execute(self, schedule: DCASchedule) -> bool:
        """Check if a schedule should execute now."""
        if not schedule.enabled:
            return False
        
        now = datetime.now()
        
        # Check hour
        if now.hour != schedule.hour:
            return False
        
        # Check interval-specific conditions
        if schedule.interval == DCAInterval.HOURLY:
            # Execute every hour at the start of the hour
            if schedule.last_execution:
                hours_since = (now - schedule.last_execution).total_seconds() / 3600
                return hours_since >= 1
            return True
        
        elif schedule.interval == DCAInterval.DAILY:
            if schedule.last_execution:
                days_since = (now - schedule.last_execution).days
                return days_since >= 1
            return True
        
        elif schedule.interval == DCAInterval.WEEKLY:
            target_day = schedule.day_of_week or 0  # Default Monday
            if now.weekday() != target_day:
                return False
            if schedule.last_execution:
                days_since = (now - schedule.last_execution).days
                return days_since >= 7
            return True
        
        elif schedule.interval == DCAInterval.BIWEEKLY:
            target_day = schedule.day_of_week or 0
            if now.weekday() != target_day:
                return False
            if schedule.last_execution:
                days_since = (now - schedule.last_execution).days
                return days_since >= 14
            return True
        
        elif schedule.interval == DCAInterval.MONTHLY:
            target_day = schedule.day_of_month or 1
            if now.day != target_day:
                return False
            if schedule.last_execution:
                # Check if we're in a new month
                return now.month != schedule.last_execution.month
            return True
        
        return False
    
    def run_due_schedules(self) -> List[DCAExecution]:
        """Check and execute any due schedules."""
        executions = []
        
        for schedule in self.schedules.values():
            if self.should_execute(schedule):
                print(f"\n⏰ Executing DCA: {schedule.asset} (${schedule.amount_usd})")
                execution = self.execute_buy(schedule)
                executions.append(execution)
                
                if execution.status == "success":
                    print(f"  ✓ Bought {execution.units_bought:.8f} {execution.asset}")
                    print(f"    @ ${execution.price_per_unit:,.2f} on {execution.exchange}")
                elif execution.status == "dry_run":
                    print(f"  🔵 [DRY RUN] Would buy {execution.units_bought:.8f} {execution.asset}")
                else:
                    print(f"  ✗ Failed: {execution.error}")
        
        return executions
    
    def run_daemon(self, check_interval_minutes: int = 5):
        """Run as a daemon, checking schedules periodically."""
        print(f"🤖 DCA Bot started ({'DRY RUN' if self.dry_run else 'LIVE'})")
        print(f"   Checking every {check_interval_minutes} minutes")
        print(f"   Active schedules: {len([s for s in self.schedules.values() if s.enabled])}")
        print("   Press Ctrl+C to stop\n")
        
        # Schedule the check
        schedule.every(check_interval_minutes).minutes.do(self.run_due_schedules)
        
        # Initial check
        self.run_due_schedules()
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n\n🛑 DCA Bot stopped")
    
    def get_stats(self) -> Dict:
        """Get DCA statistics."""
        total_invested = sum(s.total_invested for s in self.schedules.values())
        total_units = {}
        
        for s in self.schedules.values():
            if s.asset not in total_units:
                total_units[s.asset] = 0
            total_units[s.asset] += s.total_units_bought
        
        return {
            "total_invested": total_invested,
            "total_units_by_asset": total_units,
            "active_schedules": len([s for s in self.schedules.values() if s.enabled]),
            "total_schedules": len(self.schedules)
        }


# CLI interface
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Multi-Exchange DCA Bot")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without executing")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List DCA schedules")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add DCA schedule")
    add_parser.add_argument("asset", help="Asset to buy (BTC, ETH, etc.)")
    add_parser.add_argument("amount", type=float, help="USD amount per purchase")
    add_parser.add_argument(
        "--interval", "-i",
        choices=["hourly", "daily", "weekly", "biweekly", "monthly"],
        default="weekly",
        help="Purchase interval"
    )
    add_parser.add_argument(
        "--exchange", "-e",
        choices=["coinbase", "kraken", "cryptocom", "gemini", "auto"],
        default="auto",
        help="Exchange to use"
    )
    add_parser.add_argument("--day", type=int, help="Day of week (0-6) or month (1-28)")
    add_parser.add_argument("--hour", type=int, default=9, help="Hour to execute (0-23)")
    
    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove DCA schedule")
    remove_parser.add_argument("schedule_id", help="Schedule ID to remove")
    
    # Enable/Disable commands
    enable_parser = subparsers.add_parser("enable", help="Enable a schedule")
    enable_parser.add_argument("schedule_id", help="Schedule ID")
    
    disable_parser = subparsers.add_parser("disable", help="Disable a schedule")
    disable_parser.add_argument("schedule_id", help="Schedule ID")
    
    # Run command
    run_parser = subparsers.add_parser("run", help="Run DCA bot")
    run_parser.add_argument("--once", action="store_true", help="Run once and exit")
    
    # Execute command (manual)
    exec_parser = subparsers.add_parser("execute", help="Execute a schedule now")
    exec_parser.add_argument("schedule_id", help="Schedule ID to execute")
    
    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show DCA statistics")
    
    args = parser.parse_args()
    
    bot = MultiExchangeDCABot(dry_run=args.dry_run)
    
    if args.command == "list":
        schedules = bot.list_schedules()
        
        if not schedules:
            print("No DCA schedules configured.")
            print("Add one with: python multi_dca_bot.py add BTC 100 --interval weekly")
            return
        
        print("\n📅 DCA Schedules")
        print("=" * 70)
        
        for s in schedules:
            status = "✓" if s.enabled else "○"
            print(f"\n{status} [{s.schedule_id}] {s.asset} - ${s.amount_usd}/purchase")
            print(f"   Interval: {s.interval.value}")
            print(f"   Exchange: {s.exchange}")
            print(f"   Total Invested: ${s.total_invested:,.2f}")
            print(f"   Units Bought: {s.total_units_bought:.8f}")
            if s.last_execution:
                print(f"   Last Execution: {s.last_execution}")
    
    elif args.command == "add":
        interval = DCAInterval(args.interval)
        
        day_of_week = None
        day_of_month = None
        if args.day:
            if interval in (DCAInterval.WEEKLY, DCAInterval.BIWEEKLY):
                day_of_week = args.day
            elif interval == DCAInterval.MONTHLY:
                day_of_month = args.day
        
        schedule = bot.add_schedule(
            asset=args.asset,
            amount_usd=args.amount,
            interval=interval,
            exchange=args.exchange,
            day_of_week=day_of_week,
            day_of_month=day_of_month,
            hour=args.hour
        )
        
        print(f"\n✓ Added DCA schedule: {schedule.schedule_id}")
        print(f"  Asset: {schedule.asset}")
        print(f"  Amount: ${schedule.amount_usd}")
        print(f"  Interval: {schedule.interval.value}")
        print(f"  Exchange: {schedule.exchange}")
    
    elif args.command == "remove":
        bot.remove_schedule(args.schedule_id)
    
    elif args.command == "enable":
        bot.enable_schedule(args.schedule_id, True)
    
    elif args.command == "disable":
        bot.enable_schedule(args.schedule_id, False)
    
    elif args.command == "run":
        if args.once:
            bot.run_due_schedules()
        else:
            bot.run_daemon()
    
    elif args.command == "execute":
        if args.schedule_id in bot.schedules:
            schedule = bot.schedules[args.schedule_id]
            execution = bot.execute_buy(schedule)
            
            if execution.status == "success":
                print(f"✓ Executed: Bought {execution.units_bought:.8f} {execution.asset}")
            elif execution.status == "dry_run":
                print(f"🔵 [DRY RUN] Would buy {execution.units_bought:.8f} {execution.asset}")
            else:
                print(f"✗ Failed: {execution.error}")
        else:
            print(f"Schedule {args.schedule_id} not found")
    
    elif args.command == "stats":
        stats = bot.get_stats()
        
        print("\n📊 DCA Statistics")
        print("=" * 50)
        print(f"Active Schedules: {stats['active_schedules']}/{stats['total_schedules']}")
        print(f"Total Invested: ${stats['total_invested']:,.2f}")
        print("\nUnits Acquired:")
        for asset, units in stats['total_units_by_asset'].items():
            print(f"  {asset}: {units:.8f}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

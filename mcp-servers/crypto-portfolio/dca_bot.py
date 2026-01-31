"""
Dollar Cost Averaging (DCA) Bot

Automate recurring cryptocurrency purchases on a schedule.
"""

import json
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

from exchanges import CoinbaseClient
from trading_engine import TradingEngine, TradeRecord
from config import TradingConfig, DCAConfig


@dataclass
class DCASchedule:
    """Tracks DCA schedule and execution history."""
    asset: str
    usd_amount: float
    interval: str
    last_executed: Optional[datetime] = None
    next_execution: Optional[datetime] = None
    total_invested: float = 0.0
    total_purchased: float = 0.0
    execution_count: int = 0


class DCABot:
    """
    Dollar Cost Averaging automation.
    
    Features:
    - Scheduled recurring purchases
    - Multiple interval options (hourly, daily, weekly, monthly)
    - Skip purchases near price highs
    - Execution history tracking
    - Persistent state between runs
    """
    
    STATE_FILE = "dca_state.json"
    
    def __init__(
        self,
        client: CoinbaseClient,
        engine: TradingEngine,
        config: TradingConfig = None
    ):
        self.client = client
        self.engine = engine
        self.config = config or TradingConfig()
        self.dca_config = self.config.dca
        
        self.schedules: Dict[str, DCASchedule] = {}
        self.running = False
        self._thread: Optional[threading.Thread] = None
        
        # Initialize schedules from config
        self._init_schedules()
        self._load_state()
    
    def _init_schedules(self):
        """Initialize DCA schedules from config."""
        for asset, amount in self.dca_config.dca_amounts.items():
            if asset not in self.schedules:
                self.schedules[asset] = DCASchedule(
                    asset=asset,
                    usd_amount=amount,
                    interval=self.dca_config.interval
                )
            self.schedules[asset].usd_amount = amount
            self.schedules[asset].interval = self.dca_config.interval
            self._calculate_next_execution(asset)
    
    def _calculate_next_execution(self, asset: str):
        """Calculate when the next DCA purchase should occur."""
        schedule = self.schedules.get(asset)
        if not schedule:
            return
        
        now = datetime.now()
        interval = schedule.interval.lower()
        
        if interval == "hourly":
            # Next hour
            next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        
        elif interval == "daily":
            # Tomorrow at configured hour
            next_time = now.replace(
                hour=self.dca_config.hour, 
                minute=0, 
                second=0, 
                microsecond=0
            )
            if next_time <= now:
                next_time += timedelta(days=1)
        
        elif interval == "weekly":
            # Next configured day of week
            days_ahead = self.dca_config.day_of_week - now.weekday()
            if days_ahead <= 0:  # Target day already passed this week
                days_ahead += 7
            next_time = now.replace(
                hour=self.dca_config.hour,
                minute=0,
                second=0,
                microsecond=0
            ) + timedelta(days=days_ahead)
            
            # If it's the target day but past the hour, go to next week
            if days_ahead == 7 and next_time <= now:
                next_time += timedelta(days=7)
        
        elif interval == "biweekly":
            # Every 2 weeks
            days_ahead = self.dca_config.day_of_week - now.weekday()
            if days_ahead <= 0:
                days_ahead += 14
            next_time = now.replace(
                hour=self.dca_config.hour,
                minute=0,
                second=0,
                microsecond=0
            ) + timedelta(days=days_ahead)
        
        elif interval == "monthly":
            # Next month on configured day
            target_day = min(self.dca_config.day_of_month, 28)  # Safe for all months
            
            if now.day < target_day:
                next_time = now.replace(
                    day=target_day,
                    hour=self.dca_config.hour,
                    minute=0,
                    second=0,
                    microsecond=0
                )
            else:
                # Next month
                if now.month == 12:
                    next_time = now.replace(
                        year=now.year + 1,
                        month=1,
                        day=target_day,
                        hour=self.dca_config.hour,
                        minute=0,
                        second=0,
                        microsecond=0
                    )
                else:
                    next_time = now.replace(
                        month=now.month + 1,
                        day=target_day,
                        hour=self.dca_config.hour,
                        minute=0,
                        second=0,
                        microsecond=0
                    )
        else:
            # Default to daily
            next_time = now + timedelta(days=1)
        
        schedule.next_execution = next_time
    
    def _should_skip_purchase(self, asset: str) -> tuple[bool, str]:
        """
        Check if we should skip this purchase (e.g., price near high).
        Returns (should_skip, reason).
        """
        if self.dca_config.skip_if_near_high_days <= 0:
            return False, ""
        
        # Get price history
        product_id = f"{asset}-USD"
        now = int(time.time())
        days = self.dca_config.skip_if_near_high_days
        
        try:
            candles = self.client._get_candles(
                product_id,
                now - (days * 86400),
                now,
                "ONE_DAY"
            )
            
            if not candles:
                return False, ""
            
            # Find highest price in period
            highs = [float(c["high"]) for c in candles]
            period_high = max(highs)
            current_price = self.client.get_spot_price(asset)
            
            if not current_price:
                return False, ""
            
            # Skip if within 5% of the high
            threshold = period_high * 0.95
            if current_price >= threshold:
                return True, f"Price ${current_price:.2f} is within 5% of {days}-day high ${period_high:.2f}"
        
        except Exception as e:
            # If we can't check, don't skip
            pass
        
        return False, ""
    
    def execute_dca(self, asset: str = None) -> List[TradeRecord]:
        """
        Execute DCA purchases for one or all assets.
        
        Args:
            asset: Specific asset to purchase, or None for all scheduled assets
        
        Returns:
            List of TradeRecords for executed purchases
        """
        results = []
        assets_to_buy = [asset] if asset else list(self.schedules.keys())
        
        for asset_name in assets_to_buy:
            schedule = self.schedules.get(asset_name)
            if not schedule:
                continue
            
            # Check if it's time
            now = datetime.now()
            if schedule.next_execution and now < schedule.next_execution:
                time_remaining = schedule.next_execution - now
                print(f"⏰ {asset_name}: Next purchase in {time_remaining}")
                continue
            
            # Check if we should skip
            should_skip, skip_reason = self._should_skip_purchase(asset_name)
            if should_skip:
                print(f"⏭️  {asset_name}: Skipping - {skip_reason}")
                self._calculate_next_execution(asset_name)
                continue
            
            # Execute the purchase
            print(f"\n💰 DCA Purchase: ${schedule.usd_amount:.2f} of {asset_name}")
            
            record = self.engine.execute_trade(
                product_id=f"{asset_name}-USD",
                side="BUY",
                usd_amount=schedule.usd_amount
            )
            results.append(record)
            
            # Update schedule
            if record.executed:
                schedule.last_executed = now
                schedule.total_invested += schedule.usd_amount
                schedule.total_purchased += record.fill_amount or 0
                schedule.execution_count += 1
                print(f"✅ Purchased {record.fill_amount:.8f} {asset_name}")
            else:
                print(f"❌ Purchase failed: {record.error}")
            
            self._calculate_next_execution(asset_name)
        
        self._save_state()
        return results
    
    def add_schedule(self, asset: str, usd_amount: float, interval: str = None):
        """Add or update a DCA schedule."""
        if asset not in self.schedules:
            self.schedules[asset] = DCASchedule(
                asset=asset,
                usd_amount=usd_amount,
                interval=interval or self.dca_config.interval
            )
        else:
            self.schedules[asset].usd_amount = usd_amount
            if interval:
                self.schedules[asset].interval = interval
        
        self._calculate_next_execution(asset)
        self._save_state()
        print(f"✅ DCA schedule set: ${usd_amount:.2f} {asset} {self.schedules[asset].interval}")
    
    def remove_schedule(self, asset: str):
        """Remove a DCA schedule."""
        if asset in self.schedules:
            del self.schedules[asset]
            self._save_state()
            print(f"🗑️  Removed DCA schedule for {asset}")
    
    def display_schedules(self):
        """Print all DCA schedules."""
        print("\n" + "="*70)
        print("📅 DCA SCHEDULES")
        print("="*70)
        
        if not self.schedules:
            print("No DCA schedules configured.")
            return
        
        for asset, schedule in self.schedules.items():
            print(f"\n{asset}:")
            print(f"  Amount:      ${schedule.usd_amount:.2f} {schedule.interval}")
            print(f"  Next Buy:    {schedule.next_execution.strftime('%Y-%m-%d %H:%M') if schedule.next_execution else 'Not scheduled'}")
            print(f"  Last Buy:    {schedule.last_executed.strftime('%Y-%m-%d %H:%M') if schedule.last_executed else 'Never'}")
            print(f"  Total:       {schedule.execution_count} purchases, ${schedule.total_invested:.2f} invested")
            if schedule.total_purchased > 0:
                avg_price = schedule.total_invested / schedule.total_purchased
                print(f"  Accumulated: {schedule.total_purchased:.8f} {asset} (avg ${avg_price:.2f})")
        
        print("\n" + "="*70)
    
    def start_daemon(self, check_interval: int = 60):
        """
        Start background thread to execute DCA on schedule.
        
        Args:
            check_interval: How often to check schedules (seconds)
        """
        if self.running:
            print("DCA daemon already running")
            return
        
        self.running = True
        
        def run_loop():
            print("🤖 DCA Daemon started")
            while self.running:
                try:
                    self.execute_dca()
                except Exception as e:
                    print(f"DCA error: {e}")
                time.sleep(check_interval)
            print("🤖 DCA Daemon stopped")
        
        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()
    
    def stop_daemon(self):
        """Stop the background DCA thread."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
    
    def _save_state(self):
        """Save DCA state to file."""
        state = {}
        for asset, schedule in self.schedules.items():
            state[asset] = {
                "asset": schedule.asset,
                "usd_amount": schedule.usd_amount,
                "interval": schedule.interval,
                "last_executed": schedule.last_executed.isoformat() if schedule.last_executed else None,
                "next_execution": schedule.next_execution.isoformat() if schedule.next_execution else None,
                "total_invested": schedule.total_invested,
                "total_purchased": schedule.total_purchased,
                "execution_count": schedule.execution_count
            }
        
        with open(self.STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    
    def _load_state(self):
        """Load DCA state from file."""
        try:
            with open(self.STATE_FILE, "r") as f:
                state = json.load(f)
            
            for asset, data in state.items():
                if asset in self.schedules:
                    self.schedules[asset].last_executed = (
                        datetime.fromisoformat(data["last_executed"]) 
                        if data.get("last_executed") else None
                    )
                    self.schedules[asset].total_invested = data.get("total_invested", 0)
                    self.schedules[asset].total_purchased = data.get("total_purchased", 0)
                    self.schedules[asset].execution_count = data.get("execution_count", 0)
                    self._calculate_next_execution(asset)
        
        except FileNotFoundError:
            pass  # No state file yet
        except Exception as e:
            print(f"Warning: Could not load DCA state: {e}")


def quick_dca(
    api_key: str,
    api_secret: str,
    amounts: Dict[str, float],
    interval: str = "weekly"
):
    """
    Convenience function to set up and display DCA schedules.
    
    Example:
        quick_dca(key, secret, {"BTC": 50, "ETH": 25}, "weekly")
    """
    from config import TradingConfig, TradingMode
    
    client = CoinbaseClient(api_key, api_secret)
    config = TradingConfig(mode=TradingMode.CONFIRM)
    config.dca.dca_amounts = amounts
    config.dca.interval = interval
    
    engine = TradingEngine(client, config)
    bot = DCABot(client, engine, config)
    
    bot.display_schedules()
    return bot

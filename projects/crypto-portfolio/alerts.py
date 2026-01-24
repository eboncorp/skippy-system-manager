"""
Price Alert Monitor

Monitor positions for stop-loss and take-profit triggers.
"""

import json
import time
import threading
from datetime import datetime
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from coinbase_client import CoinbaseClient
from trading_engine import TradingEngine, TradeRecord
from config import TradingConfig, AlertConfig


class AlertType(Enum):
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    TRAILING_STOP = "trailing_stop"


@dataclass
class Alert:
    """Individual price alert configuration."""
    asset: str
    alert_type: AlertType
    trigger_percent: Optional[float] = None  # For stop-loss/take-profit
    trigger_price: Optional[float] = None    # For price alerts
    reference_price: Optional[float] = None  # Price when alert was set
    peak_price: Optional[float] = None       # For trailing stops
    action: str = "NOTIFY"  # NOTIFY, SELL, or SELL_PERCENT
    sell_percent: float = 100.0              # Percent to sell if triggered
    enabled: bool = True
    triggered: bool = False
    triggered_at: Optional[datetime] = None


@dataclass 
class AlertEvent:
    """Record of a triggered alert."""
    timestamp: datetime
    asset: str
    alert_type: AlertType
    trigger_price: float
    current_price: float
    action_taken: str
    trade_result: Optional[TradeRecord] = None


class AlertMonitor:
    """
    Price alert monitor with automated responses.
    
    Features:
    - Stop-loss monitoring
    - Take-profit triggers
    - Price threshold alerts
    - Trailing stop-loss
    - Automated sell execution
    - Notification callbacks
    """
    
    STATE_FILE = "alerts_state.json"
    
    def __init__(
        self,
        client: CoinbaseClient,
        engine: TradingEngine,
        config: TradingConfig = None
    ):
        self.client = client
        self.engine = engine
        self.config = config or TradingConfig()
        self.alert_config = self.config.alerts
        
        self.alerts: Dict[str, List[Alert]] = {}  # asset -> list of alerts
        self.events: List[AlertEvent] = []
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable[[AlertEvent], None]] = []
        
        # Track cost basis for reference
        self.cost_basis: Dict[str, float] = {}
        
        self._init_from_config()
        self._load_state()
    
    def _init_from_config(self):
        """Initialize alerts from config."""
        # Stop-loss alerts
        for asset, threshold in self.alert_config.stop_loss_percent.items():
            self.add_stop_loss(asset, threshold)
        
        # Take-profit alerts  
        for asset, threshold in self.alert_config.take_profit_percent.items():
            self.add_take_profit(asset, threshold)
    
    def add_stop_loss(
        self,
        asset: str,
        percent: float,
        action: str = "SELL",
        sell_percent: float = 100.0
    ):
        """
        Add a stop-loss alert.
        
        Args:
            asset: Asset to monitor (e.g., "BTC")
            percent: Negative percentage threshold (e.g., -20 for 20% drop)
            action: What to do when triggered ("NOTIFY" or "SELL")
            sell_percent: Percentage of holdings to sell (if action=SELL)
        """
        if asset not in self.alerts:
            self.alerts[asset] = []
        
        # Remove existing stop-loss for this asset
        self.alerts[asset] = [a for a in self.alerts[asset] 
                             if a.alert_type != AlertType.STOP_LOSS]
        
        # Get current/reference price
        ref_price = self._get_reference_price(asset)
        
        alert = Alert(
            asset=asset,
            alert_type=AlertType.STOP_LOSS,
            trigger_percent=percent,
            reference_price=ref_price,
            action=action,
            sell_percent=sell_percent
        )
        self.alerts[asset].append(alert)
        self._save_state()
        
        trigger_price = ref_price * (1 + percent/100) if ref_price else None
        print(f"🛑 Stop-loss set: {asset} at {percent}% (${trigger_price:.2f if trigger_price else 'N/A'})")
    
    def add_take_profit(
        self,
        asset: str,
        percent: float,
        action: str = "SELL",
        sell_percent: float = None
    ):
        """
        Add a take-profit alert.
        
        Args:
            asset: Asset to monitor
            percent: Positive percentage threshold (e.g., 50 for 50% gain)
            action: What to do when triggered
            sell_percent: Percentage to sell (defaults to config value)
        """
        if asset not in self.alerts:
            self.alerts[asset] = []
        
        # Remove existing take-profit for this asset
        self.alerts[asset] = [a for a in self.alerts[asset] 
                             if a.alert_type != AlertType.TAKE_PROFIT]
        
        ref_price = self._get_reference_price(asset)
        
        alert = Alert(
            asset=asset,
            alert_type=AlertType.TAKE_PROFIT,
            trigger_percent=percent,
            reference_price=ref_price,
            action=action,
            sell_percent=sell_percent or self.alert_config.take_profit_sell_percent
        )
        self.alerts[asset].append(alert)
        self._save_state()
        
        trigger_price = ref_price * (1 + percent/100) if ref_price else None
        print(f"🎯 Take-profit set: {asset} at +{percent}% (${trigger_price:.2f if trigger_price else 'N/A'})")
    
    def add_trailing_stop(
        self,
        asset: str,
        trail_percent: float,
        action: str = "SELL",
        sell_percent: float = 100.0
    ):
        """
        Add a trailing stop-loss.
        
        The stop price rises as the asset price rises, but never falls.
        
        Args:
            asset: Asset to monitor
            trail_percent: Distance below peak to trigger (e.g., 10 for 10% below high)
        """
        if asset not in self.alerts:
            self.alerts[asset] = []
        
        # Remove existing trailing stop
        self.alerts[asset] = [a for a in self.alerts[asset]
                             if a.alert_type != AlertType.TRAILING_STOP]
        
        current_price = self.client.get_spot_price(asset)
        
        alert = Alert(
            asset=asset,
            alert_type=AlertType.TRAILING_STOP,
            trigger_percent=-trail_percent,
            reference_price=current_price,
            peak_price=current_price,
            action=action,
            sell_percent=sell_percent
        )
        self.alerts[asset].append(alert)
        self._save_state()
        
        print(f"📈 Trailing stop set: {asset} at {trail_percent}% below peak (current: ${current_price:.2f if current_price else 'N/A'})")
    
    def add_price_alert(
        self,
        asset: str,
        price: float,
        direction: str = "above",  # "above" or "below"
        action: str = "NOTIFY"
    ):
        """Add a simple price threshold alert."""
        if asset not in self.alerts:
            self.alerts[asset] = []
        
        alert_type = AlertType.PRICE_ABOVE if direction == "above" else AlertType.PRICE_BELOW
        
        alert = Alert(
            asset=asset,
            alert_type=alert_type,
            trigger_price=price,
            reference_price=self.client.get_spot_price(asset),
            action=action
        )
        self.alerts[asset].append(alert)
        self._save_state()
        
        print(f"🔔 Price alert set: {asset} {direction} ${price:.2f}")
    
    def remove_alert(self, asset: str, alert_type: AlertType = None):
        """Remove alerts for an asset."""
        if asset not in self.alerts:
            return
        
        if alert_type:
            self.alerts[asset] = [a for a in self.alerts[asset] 
                                 if a.alert_type != alert_type]
        else:
            del self.alerts[asset]
        
        self._save_state()
        print(f"🗑️  Removed alerts for {asset}")
    
    def set_cost_basis(self, asset: str, price: float):
        """Set the cost basis for an asset (used for stop-loss/take-profit calculation)."""
        self.cost_basis[asset] = price
        
        # Update reference prices for existing alerts
        if asset in self.alerts:
            for alert in self.alerts[asset]:
                if self.alert_config.reference_price == "cost_basis":
                    alert.reference_price = price
        
        self._save_state()
        print(f"💵 Cost basis set: {asset} at ${price:.2f}")
    
    def _get_reference_price(self, asset: str) -> Optional[float]:
        """Get the reference price for calculating gains/losses."""
        ref_type = self.alert_config.reference_price
        
        if ref_type == "cost_basis" and asset in self.cost_basis:
            return self.cost_basis[asset]
        
        # For time-based references, get historical price
        current = self.client.get_spot_price(asset)
        if ref_type == "current" or not current:
            return current
        
        changes = self.client.get_price_changes(asset)
        if not changes:
            return current
        
        # Calculate historical price from changes
        if ref_type == "24h" and changes.get("change_24h") is not None:
            return current / (1 + changes["change_24h"]/100)
        elif ref_type == "7d" and changes.get("change_7d") is not None:
            return current / (1 + changes["change_7d"]/100)
        elif ref_type == "30d" and changes.get("change_30d") is not None:
            return current / (1 + changes["change_30d"]/100)
        
        return current
    
    def check_alerts(self) -> List[AlertEvent]:
        """
        Check all alerts and trigger any that hit their thresholds.
        Returns list of triggered events.
        """
        triggered_events = []
        
        for asset, alerts in self.alerts.items():
            current_price = self.client.get_spot_price(asset)
            if not current_price:
                continue
            
            for alert in alerts:
                if not alert.enabled or alert.triggered:
                    continue
                
                event = self._check_single_alert(alert, current_price)
                if event:
                    triggered_events.append(event)
                    self.events.append(event)
                    
                    # Notify callbacks
                    for callback in self._callbacks:
                        try:
                            callback(event)
                        except Exception as e:
                            print(f"Callback error: {e}")
        
        if triggered_events:
            self._save_state()
        
        return triggered_events
    
    def _check_single_alert(self, alert: Alert, current_price: float) -> Optional[AlertEvent]:
        """Check a single alert and return event if triggered."""
        triggered = False
        trigger_value = None
        
        if alert.alert_type == AlertType.STOP_LOSS:
            if alert.reference_price and alert.trigger_percent:
                change = ((current_price - alert.reference_price) / alert.reference_price) * 100
                if change <= alert.trigger_percent:
                    triggered = True
                    trigger_value = alert.trigger_percent
        
        elif alert.alert_type == AlertType.TAKE_PROFIT:
            if alert.reference_price and alert.trigger_percent:
                change = ((current_price - alert.reference_price) / alert.reference_price) * 100
                if change >= alert.trigger_percent:
                    triggered = True
                    trigger_value = alert.trigger_percent
        
        elif alert.alert_type == AlertType.TRAILING_STOP:
            # Update peak if price has risen
            if current_price > (alert.peak_price or 0):
                alert.peak_price = current_price
            
            # Check if price has fallen enough from peak
            if alert.peak_price and alert.trigger_percent:
                drop = ((current_price - alert.peak_price) / alert.peak_price) * 100
                if drop <= alert.trigger_percent:
                    triggered = True
                    trigger_value = alert.peak_price
        
        elif alert.alert_type == AlertType.PRICE_ABOVE:
            if alert.trigger_price and current_price >= alert.trigger_price:
                triggered = True
                trigger_value = alert.trigger_price
        
        elif alert.alert_type == AlertType.PRICE_BELOW:
            if alert.trigger_price and current_price <= alert.trigger_price:
                triggered = True
                trigger_value = alert.trigger_price
        
        if not triggered:
            return None
        
        # Handle the alert
        print(f"\n🚨 ALERT TRIGGERED: {alert.asset} {alert.alert_type.value}")
        print(f"   Current: ${current_price:.2f}, Trigger: {trigger_value}")
        
        trade_result = None
        action_taken = alert.action
        
        if alert.action == "SELL" or alert.action == "SELL_PERCENT":
            trade_result = self._execute_sell(alert, current_price)
            if trade_result and trade_result.executed:
                action_taken = f"SOLD {alert.sell_percent}%"
        
        # Mark as triggered
        alert.triggered = True
        alert.triggered_at = datetime.now()
        
        return AlertEvent(
            timestamp=datetime.now(),
            asset=alert.asset,
            alert_type=alert.alert_type,
            trigger_price=trigger_value or current_price,
            current_price=current_price,
            action_taken=action_taken,
            trade_result=trade_result
        )
    
    def _execute_sell(self, alert: Alert, current_price: float) -> Optional[TradeRecord]:
        """Execute a sell based on alert configuration."""
        # Get current holdings
        accounts = self.client.get_accounts()
        balance = 0
        
        for account in accounts:
            if account.get("currency") == alert.asset:
                balance = float(account.get("available_balance", {}).get("value", 0))
                break
        
        if balance <= 0:
            print(f"   No {alert.asset} balance to sell")
            return None
        
        # Calculate sell amount
        sell_amount = balance * (alert.sell_percent / 100)
        
        return self.engine.execute_trade(
            product_id=f"{alert.asset}-USD",
            side="SELL",
            asset_amount=sell_amount
        )
    
    def add_callback(self, callback: Callable[[AlertEvent], None]):
        """Add a callback function to be called when alerts trigger."""
        self._callbacks.append(callback)
    
    def display_alerts(self):
        """Print all configured alerts."""
        print("\n" + "="*70)
        print("🔔 ACTIVE ALERTS")
        print("="*70)
        
        if not self.alerts:
            print("No alerts configured.")
            return
        
        for asset, alerts in self.alerts.items():
            current = self.client.get_spot_price(asset)
            print(f"\n{asset} (Current: ${current:.2f if current else 'N/A'}):")
            
            for alert in alerts:
                status = "✅" if alert.enabled and not alert.triggered else ("🔴" if alert.triggered else "⏸️")
                
                if alert.alert_type == AlertType.STOP_LOSS:
                    trigger = alert.reference_price * (1 + alert.trigger_percent/100) if alert.reference_price else None
                    print(f"  {status} Stop-Loss: {alert.trigger_percent}% (${trigger:.2f if trigger else 'N/A'}) → {alert.action}")
                
                elif alert.alert_type == AlertType.TAKE_PROFIT:
                    trigger = alert.reference_price * (1 + alert.trigger_percent/100) if alert.reference_price else None
                    print(f"  {status} Take-Profit: +{alert.trigger_percent}% (${trigger:.2f if trigger else 'N/A'}) → {alert.action} {alert.sell_percent}%")
                
                elif alert.alert_type == AlertType.TRAILING_STOP:
                    print(f"  {status} Trailing Stop: {abs(alert.trigger_percent)}% below peak (Peak: ${alert.peak_price:.2f if alert.peak_price else 'N/A'}) → {alert.action}")
                
                elif alert.alert_type in [AlertType.PRICE_ABOVE, AlertType.PRICE_BELOW]:
                    direction = "above" if alert.alert_type == AlertType.PRICE_ABOVE else "below"
                    print(f"  {status} Price {direction} ${alert.trigger_price:.2f} → {alert.action}")
        
        print("\n" + "="*70)
    
    def start_monitoring(self, interval: int = None):
        """Start background monitoring thread."""
        if self.running:
            print("Monitor already running")
            return
        
        check_interval = interval or self.alert_config.check_interval
        self.running = True
        
        def run_loop():
            print(f"👁️  Alert monitor started (checking every {check_interval}s)")
            while self.running:
                try:
                    events = self.check_alerts()
                    if events:
                        print(f"   {len(events)} alert(s) triggered")
                except Exception as e:
                    print(f"Monitor error: {e}")
                time.sleep(check_interval)
            print("👁️  Alert monitor stopped")
        
        self._thread = threading.Thread(target=run_loop, daemon=True)
        self._thread.start()
    
    def stop_monitoring(self):
        """Stop the monitoring thread."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None
    
    def _save_state(self):
        """Save alert state to file."""
        state = {
            "cost_basis": self.cost_basis,
            "alerts": {}
        }
        
        for asset, alerts in self.alerts.items():
            state["alerts"][asset] = []
            for alert in alerts:
                state["alerts"][asset].append({
                    "asset": alert.asset,
                    "alert_type": alert.alert_type.value,
                    "trigger_percent": alert.trigger_percent,
                    "trigger_price": alert.trigger_price,
                    "reference_price": alert.reference_price,
                    "peak_price": alert.peak_price,
                    "action": alert.action,
                    "sell_percent": alert.sell_percent,
                    "enabled": alert.enabled,
                    "triggered": alert.triggered,
                    "triggered_at": alert.triggered_at.isoformat() if alert.triggered_at else None
                })
        
        with open(self.STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    
    def _load_state(self):
        """Load alert state from file."""
        try:
            with open(self.STATE_FILE, "r") as f:
                state = json.load(f)
            
            self.cost_basis = state.get("cost_basis", {})
            
            for asset, alerts_data in state.get("alerts", {}).items():
                if asset not in self.alerts:
                    self.alerts[asset] = []
                
                for data in alerts_data:
                    alert = Alert(
                        asset=data["asset"],
                        alert_type=AlertType(data["alert_type"]),
                        trigger_percent=data.get("trigger_percent"),
                        trigger_price=data.get("trigger_price"),
                        reference_price=data.get("reference_price"),
                        peak_price=data.get("peak_price"),
                        action=data.get("action", "NOTIFY"),
                        sell_percent=data.get("sell_percent", 100),
                        enabled=data.get("enabled", True),
                        triggered=data.get("triggered", False),
                        triggered_at=datetime.fromisoformat(data["triggered_at"]) if data.get("triggered_at") else None
                    )
                    
                    # Don't duplicate alerts from config
                    existing = [a for a in self.alerts[asset] 
                               if a.alert_type == alert.alert_type]
                    if not existing:
                        self.alerts[asset].append(alert)
        
        except FileNotFoundError:
            pass
        except Exception as e:
            print(f"Warning: Could not load alert state: {e}")

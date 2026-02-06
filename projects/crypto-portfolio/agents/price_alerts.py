"""
Price alerts module.

Set price targets and get notified when assets hit them.
Supports:
- Above/below price targets
- Percentage change alerts
- Multi-asset monitoring
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any

from data.prices import PriceService

logger = logging.getLogger(__name__)
from agents.alerts import alert_manager, Alert, AlertType


class AlertCondition(Enum):
    """Conditions that trigger an alert."""
    ABOVE = "above"          # Price goes above target
    BELOW = "below"          # Price goes below target
    CHANGE_UP = "change_up"  # Price increases by X%
    CHANGE_DOWN = "change_down"  # Price decreases by X%


@dataclass
class PriceAlert:
    """A price alert configuration."""
    id: str
    asset: str
    condition: AlertCondition
    target_value: Decimal  # Price for above/below, percentage for change
    created_at: datetime
    triggered: bool = False
    triggered_at: Optional[datetime] = None
    triggered_price: Optional[Decimal] = None
    note: str = ""
    repeat: bool = False  # If True, alert can trigger multiple times
    cooldown_minutes: int = 60  # Minimum time between repeat triggers
    last_triggered: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "asset": self.asset,
            "condition": self.condition.value,
            "target_value": str(self.target_value),
            "created_at": self.created_at.isoformat(),
            "triggered": self.triggered,
            "triggered_at": self.triggered_at.isoformat() if self.triggered_at else None,
            "triggered_price": str(self.triggered_price) if self.triggered_price else None,
            "note": self.note,
            "repeat": self.repeat,
            "cooldown_minutes": self.cooldown_minutes,
            "last_triggered": self.last_triggered.isoformat() if self.last_triggered else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PriceAlert":
        return cls(
            id=data["id"],
            asset=data["asset"],
            condition=AlertCondition(data["condition"]),
            target_value=Decimal(data["target_value"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            triggered=data.get("triggered", False),
            triggered_at=datetime.fromisoformat(data["triggered_at"]) if data.get("triggered_at") else None,
            triggered_price=Decimal(data["triggered_price"]) if data.get("triggered_price") else None,
            note=data.get("note", ""),
            repeat=data.get("repeat", False),
            cooldown_minutes=data.get("cooldown_minutes", 60),
            last_triggered=datetime.fromisoformat(data["last_triggered"]) if data.get("last_triggered") else None,
        )


class PriceAlertManager:
    """Manages price alerts."""
    
    def __init__(
        self,
        price_service: Optional[PriceService] = None,
        storage_path: str = "./data/price_alerts.json",
    ):
        self.price_service = price_service or PriceService()
        self.storage_path = Path(storage_path)
        
        self._alerts: List[PriceAlert] = []
        self._reference_prices: Dict[str, Decimal] = {}  # For percentage change alerts
        self._load_alerts()
    
    def _load_alerts(self):
        """Load alerts from storage."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    self._alerts = [PriceAlert.from_dict(a) for a in data.get("alerts", [])]
                    self._reference_prices = {
                        k: Decimal(v) for k, v in data.get("reference_prices", {}).items()
                    }
            except Exception as e:
                logger.warning("Failed to load alerts: %s", e)
                self._alerts = []
    
    def _save_alerts(self):
        """Save alerts to storage."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w") as f:
            json.dump({
                "alerts": [a.to_dict() for a in self._alerts],
                "reference_prices": {k: str(v) for k, v in self._reference_prices.items()},
            }, f, indent=2)
    
    def create_alert(
        self,
        asset: str,
        condition: AlertCondition,
        target_value: Decimal,
        note: str = "",
        repeat: bool = False,
        cooldown_minutes: int = 60,
    ) -> PriceAlert:
        """Create a new price alert."""
        alert = PriceAlert(
            id=f"alert_{asset}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            asset=asset.upper(),
            condition=condition,
            target_value=target_value,
            created_at=datetime.now(),
            note=note,
            repeat=repeat,
            cooldown_minutes=cooldown_minutes,
        )
        
        self._alerts.append(alert)
        self._save_alerts()
        
        return alert
    
    def create_price_target(
        self,
        asset: str,
        target_price: Decimal,
        direction: str = "above",
        note: str = "",
    ) -> PriceAlert:
        """Convenience method to create a simple price target alert."""
        condition = AlertCondition.ABOVE if direction == "above" else AlertCondition.BELOW
        return self.create_alert(asset, condition, target_price, note)
    
    def create_change_alert(
        self,
        asset: str,
        percentage: Decimal,
        direction: str = "up",
        repeat: bool = True,
    ) -> PriceAlert:
        """Create an alert for percentage price change."""
        condition = AlertCondition.CHANGE_UP if direction == "up" else AlertCondition.CHANGE_DOWN
        return self.create_alert(asset, condition, percentage, repeat=repeat)
    
    def delete_alert(self, alert_id: str) -> bool:
        """Delete an alert by ID."""
        initial_count = len(self._alerts)
        self._alerts = [a for a in self._alerts if a.id != alert_id]
        
        if len(self._alerts) < initial_count:
            self._save_alerts()
            return True
        return False
    
    def get_active_alerts(self) -> List[PriceAlert]:
        """Get all active (non-triggered or repeating) alerts."""
        return [
            a for a in self._alerts
            if not a.triggered or a.repeat
        ]
    
    def get_all_alerts(self) -> List[PriceAlert]:
        """Get all alerts."""
        return self._alerts.copy()
    
    def get_triggered_alerts(self) -> List[PriceAlert]:
        """Get all triggered alerts."""
        return [a for a in self._alerts if a.triggered]
    
    async def check_alerts(self) -> List[PriceAlert]:
        """
        Check all active alerts against current prices.
        
        Returns:
            List of alerts that were triggered
        """
        active_alerts = self.get_active_alerts()
        if not active_alerts:
            return []
        
        # Get unique assets
        assets = list(set(a.asset for a in active_alerts))
        
        # Fetch current prices
        prices = await self.price_service.get_prices(assets)
        
        triggered = []
        
        for alert in active_alerts:
            current_price = prices.get(alert.asset)
            if current_price is None:
                continue
            
            # Check cooldown for repeat alerts
            if alert.repeat and alert.last_triggered:
                elapsed = (datetime.now() - alert.last_triggered).total_seconds() / 60
                if elapsed < alert.cooldown_minutes:
                    continue
            
            # Check condition
            should_trigger = False
            
            if alert.condition == AlertCondition.ABOVE:
                should_trigger = current_price >= alert.target_value
            
            elif alert.condition == AlertCondition.BELOW:
                should_trigger = current_price <= alert.target_value
            
            elif alert.condition == AlertCondition.CHANGE_UP:
                ref_price = self._reference_prices.get(alert.asset)
                if ref_price and ref_price > 0:
                    change_pct = (current_price - ref_price) / ref_price * 100
                    should_trigger = change_pct >= alert.target_value
                else:
                    # Set reference price on first check
                    self._reference_prices[alert.asset] = current_price
            
            elif alert.condition == AlertCondition.CHANGE_DOWN:
                ref_price = self._reference_prices.get(alert.asset)
                if ref_price and ref_price > 0:
                    change_pct = (ref_price - current_price) / ref_price * 100
                    should_trigger = change_pct >= alert.target_value
                else:
                    self._reference_prices[alert.asset] = current_price
            
            if should_trigger:
                alert.triggered = True
                alert.triggered_at = datetime.now()
                alert.triggered_price = current_price
                alert.last_triggered = datetime.now()
                
                triggered.append(alert)
                
                # Send notification
                await self._send_alert_notification(alert, current_price)
        
        if triggered:
            self._save_alerts()
        
        return triggered
    
    async def _send_alert_notification(self, alert: PriceAlert, current_price: Decimal):
        """Send notification for triggered alert."""
        condition_text = {
            AlertCondition.ABOVE: f"above ${float(alert.target_value):,.2f}",
            AlertCondition.BELOW: f"below ${float(alert.target_value):,.2f}",
            AlertCondition.CHANGE_UP: f"up {float(alert.target_value):.1f}%",
            AlertCondition.CHANGE_DOWN: f"down {float(alert.target_value):.1f}%",
        }
        
        message = (
            f"{alert.asset} is now {condition_text[alert.condition]}!\n"
            f"Current price: ${float(current_price):,.2f}"
        )
        
        if alert.note:
            message += f"\nNote: {alert.note}"
        
        notification = Alert(
            type=AlertType.PRICE_ALERT,
            title=f"Price Alert: {alert.asset}",
            message=message,
            priority="high",
            data={
                "asset": alert.asset,
                "price": float(current_price),
                "target": float(alert.target_value),
                "condition": alert.condition.value,
            },
        )
        
        await alert_manager.send_alert(notification)
    
    def update_reference_prices(self, prices: Dict[str, Decimal]):
        """Update reference prices for percentage change alerts."""
        self._reference_prices.update(prices)
        self._save_alerts()
    
    def format_alerts(self, alerts: Optional[List[PriceAlert]] = None) -> str:
        """Format alerts for display."""
        alerts = alerts or self._alerts
        
        if not alerts:
            return "No price alerts configured."
        
        lines = []
        lines.append("Price Alerts")
        lines.append("=" * 60)
        
        # Active alerts
        active = [a for a in alerts if not a.triggered or a.repeat]
        if active:
            lines.append("\nActive Alerts:")
            lines.append("-" * 40)
            
            for alert in active:
                condition_str = {
                    AlertCondition.ABOVE: f"≥ ${float(alert.target_value):,.2f}",
                    AlertCondition.BELOW: f"≤ ${float(alert.target_value):,.2f}",
                    AlertCondition.CHANGE_UP: f"↑ {float(alert.target_value):.1f}%",
                    AlertCondition.CHANGE_DOWN: f"↓ {float(alert.target_value):.1f}%",
                }
                
                repeat_icon = "🔄" if alert.repeat else "1️⃣"
                lines.append(f"  {repeat_icon} {alert.asset} {condition_str[alert.condition]}")
                if alert.note:
                    lines.append(f"     └─ {alert.note}")
        
        # Triggered alerts
        triggered = [a for a in alerts if a.triggered and not a.repeat]
        if triggered:
            lines.append("\nTriggered Alerts:")
            lines.append("-" * 40)
            
            for alert in triggered:
                trigger_time = alert.triggered_at.strftime("%Y-%m-%d %H:%M") if alert.triggered_at else "?"
                lines.append(
                    f"  ✅ {alert.asset} @ ${float(alert.triggered_price or 0):,.2f} "
                    f"({trigger_time})"
                )
        
        return "\n".join(lines)


# Convenience functions
def create_price_alert(
    asset: str,
    target_price: float,
    direction: str = "above",
    note: str = "",
) -> PriceAlert:
    """Quick function to create a price alert."""
    manager = PriceAlertManager()
    return manager.create_price_target(
        asset,
        Decimal(str(target_price)),
        direction,
        note,
    )


async def check_price_alerts() -> List[PriceAlert]:
    """Quick function to check all alerts."""
    manager = PriceAlertManager()
    return await manager.check_alerts()

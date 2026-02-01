"""
Multi-Exchange Price Alerts & Auto-Trading
Monitor prices across all exchanges and execute stop-loss/take-profit orders.

Features:
- Price alerts (above/below thresholds)
- Stop-loss auto-sell
- Take-profit auto-sell
- Trailing stops
- Cross-exchange monitoring
- Notifications
"""

import os
import json
import time
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from dotenv import load_dotenv


class AlertType(Enum):
    PRICE_ABOVE = "price_above"
    PRICE_BELOW = "price_below"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TRAILING_STOP = "trailing_stop"


class AlertAction(Enum):
    NOTIFY = "notify"  # Just send notification
    SELL_ALL = "sell_all"  # Sell entire position
    SELL_PERCENT = "sell_percent"  # Sell percentage
    SELL_AMOUNT = "sell_amount"  # Sell specific amount


@dataclass
class PriceAlert:
    """A price alert configuration."""
    alert_id: str
    asset: str
    alert_type: AlertType
    trigger_price: Optional[float] = None  # For fixed price alerts
    trigger_percent: Optional[float] = None  # For percentage-based
    cost_basis: Optional[float] = None  # For gain/loss calculation
    action: AlertAction = AlertAction.NOTIFY
    action_percent: float = 100  # Percent to sell if SELL_PERCENT
    action_amount: float = None  # Amount to sell if SELL_AMOUNT
    exchange: str = "all"  # Specific exchange or "all"
    enabled: bool = True
    triggered: bool = False
    triggered_at: datetime = None
    created_at: datetime = None

    # For trailing stops
    trailing_distance_percent: float = None
    highest_price_seen: float = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["alert_type"] = self.alert_type.value
        d["action"] = self.action.value
        d["triggered_at"] = self.triggered_at.isoformat() if self.triggered_at else None
        d["created_at"] = self.created_at.isoformat() if self.created_at else None
        return d

    @classmethod
    def from_dict(cls, data: dict) -> 'PriceAlert':
        data["alert_type"] = AlertType(data["alert_type"])
        data["action"] = AlertAction(data["action"])
        if data.get("triggered_at"):
            data["triggered_at"] = datetime.fromisoformat(data["triggered_at"])
        if data.get("created_at"):
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        return cls(**data)


@dataclass
class AlertTriggerEvent:
    """Record of an alert being triggered."""
    alert_id: str
    timestamp: datetime
    asset: str
    alert_type: AlertType
    trigger_price: float
    current_price: float
    action_taken: str
    exchange: str = None
    order_result: dict = None


class MultiExchangeAlertMonitor:
    """
    Monitor prices across exchanges and trigger alerts.
    """

    CONFIG_FILE = "alerts_config.json"
    HISTORY_FILE = "alerts_history.json"

    def __init__(self, config_dir: str = None, dry_run: bool = False):
        load_dotenv()

        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(__file__), "data")

        self.config_dir = config_dir
        Path(config_dir).mkdir(parents=True, exist_ok=True)

        self.config_path = os.path.join(config_dir, self.CONFIG_FILE)
        self.history_path = os.path.join(config_dir, self.HISTORY_FILE)

        self.dry_run = dry_run
        self.alerts: Dict[str, PriceAlert] = self._load_alerts()

        # Initialize exchange clients
        self.clients = {}
        self._init_clients()

        # Notification manager
        self.notifier = None
        self._init_notifier()

        # Monitoring state
        self.running = False
        self.last_prices: Dict[str, Dict[str, float]] = {}  # {asset: {exchange: price}}

    def _init_clients(self):
        """Initialize exchange clients."""
        from exchanges import CoinbaseClient, KrakenClient, CryptoComClient, GeminiClient

        if os.getenv("COINBASE_API_KEY"):
            self.clients["coinbase"] = CoinbaseClient(
                os.getenv("COINBASE_API_KEY"),
                os.getenv("COINBASE_API_SECRET")
            )

        if os.getenv("KRAKEN_API_KEY"):
            self.clients["kraken"] = KrakenClient(
                os.getenv("KRAKEN_API_KEY"),
                os.getenv("KRAKEN_API_SECRET")
            )

        if os.getenv("CRYPTOCOM_API_KEY"):
            self.clients["cryptocom"] = CryptoComClient(
                os.getenv("CRYPTOCOM_API_KEY"),
                os.getenv("CRYPTOCOM_API_SECRET")
            )

        if os.getenv("GEMINI_API_KEY"):
            self.clients["gemini"] = GeminiClient(
                os.getenv("GEMINI_API_KEY"),
                os.getenv("GEMINI_API_SECRET")
            )

    def _init_notifier(self):
        """Initialize notification manager."""
        try:
            from notifications import NotificationManager, AlertLevel
            self.notifier = NotificationManager()
        except ImportError:
            pass

    def _load_alerts(self) -> Dict[str, PriceAlert]:
        """Load alerts from config file."""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                data = json.load(f)
                return {k: PriceAlert.from_dict(v) for k, v in data.items()}
        return {}

    def _save_alerts(self):
        """Save alerts to config file."""
        with open(self.config_path, 'w') as f:
            json.dump(
                {k: v.to_dict() for k, v in self.alerts.items()},
                f,
                indent=2
            )

    def _save_trigger_event(self, event: AlertTriggerEvent):
        """Save trigger event to history."""
        history = []
        if os.path.exists(self.history_path):
            with open(self.history_path, 'r') as f:
                history = json.load(f)

        history.append({
            "alert_id": event.alert_id,
            "timestamp": event.timestamp.isoformat(),
            "asset": event.asset,
            "alert_type": event.alert_type.value,
            "trigger_price": event.trigger_price,
            "current_price": event.current_price,
            "action_taken": event.action_taken,
            "exchange": event.exchange,
            "order_result": event.order_result
        })

        with open(self.history_path, 'w') as f:
            json.dump(history, f, indent=2)

    def add_price_alert(
        self,
        asset: str,
        direction: str,  # "above" or "below"
        price: float,
        action: AlertAction = AlertAction.NOTIFY,
        exchange: str = "all"
    ) -> PriceAlert:
        """Add a simple price alert."""
        import uuid

        alert_type = AlertType.PRICE_ABOVE if direction == "above" else AlertType.PRICE_BELOW

        alert = PriceAlert(
            alert_id=str(uuid.uuid4())[:8],
            asset=asset.upper(),
            alert_type=alert_type,
            trigger_price=price,
            action=action,
            exchange=exchange,
            created_at=datetime.now()
        )

        self.alerts[alert.alert_id] = alert
        self._save_alerts()
        return alert

    def add_stop_loss(
        self,
        asset: str,
        trigger_percent: float,  # e.g., -20 for 20% loss
        cost_basis: float = None,
        action: AlertAction = AlertAction.SELL_ALL,
        sell_percent: float = 100,
        exchange: str = "all"
    ) -> PriceAlert:
        """Add a stop-loss alert."""
        import uuid

        alert = PriceAlert(
            alert_id=str(uuid.uuid4())[:8],
            asset=asset.upper(),
            alert_type=AlertType.STOP_LOSS,
            trigger_percent=trigger_percent,
            cost_basis=cost_basis,
            action=action,
            action_percent=sell_percent,
            exchange=exchange,
            created_at=datetime.now()
        )

        self.alerts[alert.alert_id] = alert
        self._save_alerts()
        return alert

    def add_take_profit(
        self,
        asset: str,
        trigger_percent: float,  # e.g., 50 for 50% gain
        cost_basis: float,
        action: AlertAction = AlertAction.SELL_PERCENT,
        sell_percent: float = 50,  # Sell half by default
        exchange: str = "all"
    ) -> PriceAlert:
        """Add a take-profit alert."""
        import uuid

        alert = PriceAlert(
            alert_id=str(uuid.uuid4())[:8],
            asset=asset.upper(),
            alert_type=AlertType.TAKE_PROFIT,
            trigger_percent=trigger_percent,
            cost_basis=cost_basis,
            action=action,
            action_percent=sell_percent,
            exchange=exchange,
            created_at=datetime.now()
        )

        self.alerts[alert.alert_id] = alert
        self._save_alerts()
        return alert

    def add_trailing_stop(
        self,
        asset: str,
        distance_percent: float,  # e.g., 10 for 10% trailing
        action: AlertAction = AlertAction.SELL_ALL,
        exchange: str = "all"
    ) -> PriceAlert:
        """Add a trailing stop alert."""
        import uuid

        alert = PriceAlert(
            alert_id=str(uuid.uuid4())[:8],
            asset=asset.upper(),
            alert_type=AlertType.TRAILING_STOP,
            trailing_distance_percent=distance_percent,
            action=action,
            exchange=exchange,
            created_at=datetime.now()
        )

        self.alerts[alert.alert_id] = alert
        self._save_alerts()
        return alert

    def set_cost_basis(self, asset: str, cost_basis: float):
        """Set cost basis for an asset (affects all alerts for that asset)."""
        for alert in self.alerts.values():
            if alert.asset == asset.upper():
                alert.cost_basis = cost_basis
        self._save_alerts()

    def remove_alert(self, alert_id: str):
        """Remove an alert."""
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            self._save_alerts()
            print(f"✓ Removed alert {alert_id}")

    def get_current_prices(self) -> Dict[str, Dict[str, float]]:
        """Get current prices from all exchanges."""
        prices = {}

        # Get unique assets from alerts
        assets = set(a.asset for a in self.alerts.values() if a.enabled)

        for asset in assets:
            prices[asset] = {}

            for exchange_name, client in self.clients.items():
                try:
                    price = client.get_spot_price(asset, "USD")
                    if price:
                        prices[asset][exchange_name] = price
                except Exception as e:
                    pass  # Silently skip failed exchanges

        self.last_prices = prices
        return prices

    def check_alert(self, alert: PriceAlert, prices: Dict[str, float]) -> Optional[float]:
        """
        Check if an alert should trigger.
        Returns the triggering price, or None if not triggered.
        """
        if not alert.enabled or alert.triggered:
            return None

        # Get relevant prices
        if alert.exchange == "all":
            check_prices = list(prices.values())
        elif alert.exchange in prices:
            check_prices = [prices[alert.exchange]]
        else:
            return None

        if not check_prices:
            return None

        # Use average price for "all" exchanges, or specific price
        current_price = sum(check_prices) / len(check_prices)

        # Check different alert types
        if alert.alert_type == AlertType.PRICE_ABOVE:
            if current_price >= alert.trigger_price:
                return current_price

        elif alert.alert_type == AlertType.PRICE_BELOW:
            if current_price <= alert.trigger_price:
                return current_price

        elif alert.alert_type == AlertType.STOP_LOSS:
            if alert.cost_basis:
                loss_percent = ((current_price - alert.cost_basis) / alert.cost_basis) * 100
                if loss_percent <= alert.trigger_percent:
                    return current_price

        elif alert.alert_type == AlertType.TAKE_PROFIT:
            if alert.cost_basis:
                gain_percent = ((current_price - alert.cost_basis) / alert.cost_basis) * 100
                if gain_percent >= alert.trigger_percent:
                    return current_price

        elif alert.alert_type == AlertType.TRAILING_STOP:
            # Update highest price
            if alert.highest_price_seen is None or current_price > alert.highest_price_seen:
                alert.highest_price_seen = current_price
                self._save_alerts()

            # Check if price dropped from high
            if alert.highest_price_seen:
                drop_percent = ((alert.highest_price_seen - current_price) / alert.highest_price_seen) * 100
                if drop_percent >= alert.trailing_distance_percent:
                    return current_price

        return None

    def execute_action(self, alert: PriceAlert, trigger_price: float) -> AlertTriggerEvent:
        """Execute the action for a triggered alert."""
        timestamp = datetime.now()
        action_taken = "none"
        order_result = None
        exchange_used = None

        if alert.action == AlertAction.NOTIFY:
            action_taken = "notification_sent"

        elif alert.action in (AlertAction.SELL_ALL, AlertAction.SELL_PERCENT, AlertAction.SELL_AMOUNT):
            if self.dry_run:
                action_taken = "dry_run_sell"
            else:
                # Determine which exchange to sell on
                if alert.exchange != "all" and alert.exchange in self.clients:
                    exchanges_to_use = [alert.exchange]
                else:
                    # Use all available exchanges
                    exchanges_to_use = list(self.clients.keys())

                for exchange_name in exchanges_to_use:
                    client = self.clients[exchange_name]

                    try:
                        # Get holdings on this exchange
                        accounts = client.get_accounts()
                        holding = None

                        for account in accounts:
                            if account.get("currency") == alert.asset:
                                balance = float(account.get("available_balance", {}).get("value", 0))
                                if balance > 0:
                                    holding = balance
                                    break

                        if not holding:
                            continue

                        # Calculate sell amount
                        if alert.action == AlertAction.SELL_ALL:
                            sell_amount = holding
                        elif alert.action == AlertAction.SELL_PERCENT:
                            sell_amount = holding * (alert.action_percent / 100)
                        else:  # SELL_AMOUNT
                            sell_amount = min(alert.action_amount, holding)

                        # Get product ID
                        if exchange_name == "coinbase":
                            product_id = f"{alert.asset}-USD"
                        elif exchange_name == "kraken":
                            kraken_asset = "XBT" if alert.asset == "BTC" else alert.asset
                            product_id = f"{kraken_asset}USD"
                        elif exchange_name == "cryptocom":
                            product_id = f"{alert.asset}_USD"
                        elif exchange_name == "gemini":
                            product_id = f"{alert.asset.lower()}usd"
                        else:
                            continue

                        # Execute sell
                        result = client.market_sell(product_id, sell_amount)

                        if result:
                            action_taken = f"sold_{sell_amount:.8f}_{alert.asset}"
                            order_result = result
                            exchange_used = exchange_name
                            break  # Success on one exchange is enough

                    except Exception as e:
                        print(f"Error executing sell on {exchange_name}: {e}")
                        continue

        # Mark alert as triggered
        alert.triggered = True
        alert.triggered_at = timestamp
        self._save_alerts()

        # Create event
        event = AlertTriggerEvent(
            alert_id=alert.alert_id,
            timestamp=timestamp,
            asset=alert.asset,
            alert_type=alert.alert_type,
            trigger_price=alert.trigger_price or trigger_price,
            current_price=trigger_price,
            action_taken=action_taken,
            exchange=exchange_used,
            order_result=order_result
        )

        self._save_trigger_event(event)

        # Send notification
        if self.notifier:
            from notifications import AlertLevel

            if alert.alert_type == AlertType.STOP_LOSS:
                self.notifier.send_stop_loss_alert(
                    asset=alert.asset,
                    trigger_price=alert.trigger_price or alert.cost_basis,
                    current_price=trigger_price,
                    loss_percent=alert.trigger_percent,
                    action_taken=action_taken
                )
            else:
                level = AlertLevel.SUCCESS if "take_profit" in alert.alert_type.value else AlertLevel.WARNING
                self.notifier.send_alert(
                    title=f"🔔 Alert Triggered: {alert.asset}",
                    message=f"{alert.alert_type.value.replace('_', ' ').title()} triggered at ${trigger_price:,.2f}",
                    level=level,
                    data={
                        "Asset": alert.asset,
                        "Price": f"${trigger_price:,.2f}",
                        "Action": action_taken
                    }
                )

        return event

    def check_all_alerts(self) -> List[AlertTriggerEvent]:
        """Check all alerts and execute triggered ones."""
        prices = self.get_current_prices()
        events = []

        for alert in list(self.alerts.values()):
            if alert.asset not in prices:
                continue

            trigger_price = self.check_alert(alert, prices[alert.asset])

            if trigger_price:
                print(f"\n⚡ ALERT TRIGGERED: {alert.asset}")
                print(f"   Type: {alert.alert_type.value}")
                print(f"   Price: ${trigger_price:,.2f}")

                event = self.execute_action(alert, trigger_price)
                events.append(event)

                print(f"   Action: {event.action_taken}")

        return events

    def run_monitor(self, check_interval_seconds: int = 60):
        """Run the alert monitor continuously."""
        print(f"🔔 Alert Monitor started ({'DRY RUN' if self.dry_run else 'LIVE'})")
        print(f"   Checking every {check_interval_seconds} seconds")
        print(f"   Active alerts: {len([a for a in self.alerts.values() if a.enabled])}")
        print("   Press Ctrl+C to stop\n")

        self.running = True

        try:
            while self.running:
                self.check_all_alerts()
                time.sleep(check_interval_seconds)
        except KeyboardInterrupt:
            print("\n\n🛑 Alert Monitor stopped")
            self.running = False

    def list_alerts(self) -> List[PriceAlert]:
        """List all alerts."""
        return list(self.alerts.values())


# CLI interface
def main():
    import argparse

    parser = argparse.ArgumentParser(description="Multi-Exchange Alert Monitor")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without executing")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # List command
    list_parser = subparsers.add_parser("list", help="List alerts")

    # Add price alert
    price_parser = subparsers.add_parser("price", help="Add price alert")
    price_parser.add_argument("asset", help="Asset symbol (BTC, ETH)")
    price_parser.add_argument("direction", choices=["above", "below"])
    price_parser.add_argument("price", type=float, help="Trigger price")

    # Add stop-loss
    sl_parser = subparsers.add_parser("stop-loss", help="Add stop-loss")
    sl_parser.add_argument("asset", help="Asset symbol")
    sl_parser.add_argument("percent", type=float, help="Loss percent (e.g., -20)")
    sl_parser.add_argument("--cost-basis", type=float, help="Your cost basis")
    sl_parser.add_argument("--sell-percent", type=float, default=100)

    # Add take-profit
    tp_parser = subparsers.add_parser("take-profit", help="Add take-profit")
    tp_parser.add_argument("asset", help="Asset symbol")
    tp_parser.add_argument("percent", type=float, help="Gain percent (e.g., 50)")
    tp_parser.add_argument("cost_basis", type=float, help="Your cost basis")
    tp_parser.add_argument("--sell-percent", type=float, default=50)

    # Add trailing stop
    trail_parser = subparsers.add_parser("trailing", help="Add trailing stop")
    trail_parser.add_argument("asset", help="Asset symbol")
    trail_parser.add_argument("distance", type=float, help="Distance percent")

    # Remove alert
    remove_parser = subparsers.add_parser("remove", help="Remove alert")
    remove_parser.add_argument("alert_id", help="Alert ID")

    # Set cost basis
    cost_parser = subparsers.add_parser("cost-basis", help="Set cost basis")
    cost_parser.add_argument("asset", help="Asset symbol")
    cost_parser.add_argument("price", type=float, help="Cost basis price")

    # Run monitor
    run_parser = subparsers.add_parser("monitor", help="Run alert monitor")
    run_parser.add_argument("--interval", type=int, default=60, help="Check interval (seconds)")

    # Check now
    check_parser = subparsers.add_parser("check", help="Check alerts now")

    args = parser.parse_args()

    monitor = MultiExchangeAlertMonitor(dry_run=args.dry_run)

    if args.command == "list":
        alerts = monitor.list_alerts()

        if not alerts:
            print("No alerts configured.")
            return

        print("\n🔔 Price Alerts")
        print("=" * 70)

        for a in alerts:
            status = "✓" if a.enabled and not a.triggered else ("⚡" if a.triggered else "○")
            print(f"\n{status} [{a.alert_id}] {a.asset} - {a.alert_type.value}")

            if a.trigger_price:
                print(f"   Trigger: ${a.trigger_price:,.2f}")
            if a.trigger_percent:
                print(f"   Trigger: {a.trigger_percent:+.1f}%")
            if a.cost_basis:
                print(f"   Cost Basis: ${a.cost_basis:,.2f}")
            if a.trailing_distance_percent:
                print(f"   Trailing: {a.trailing_distance_percent}%")
                if a.highest_price_seen:
                    print(f"   Highest Seen: ${a.highest_price_seen:,.2f}")

            print(f"   Action: {a.action.value}")
            if a.triggered:
                print(f"   ⚡ Triggered: {a.triggered_at}")

    elif args.command == "price":
        alert = monitor.add_price_alert(
            asset=args.asset,
            direction=args.direction,
            price=args.price
        )
        print(f"✓ Added price alert: {alert.alert_id}")
        print(f"  {args.asset} {args.direction} ${args.price:,.2f}")

    elif args.command == "stop-loss":
        alert = monitor.add_stop_loss(
            asset=args.asset,
            trigger_percent=args.percent,
            cost_basis=args.cost_basis,
            sell_percent=args.sell_percent
        )
        print(f"✓ Added stop-loss: {alert.alert_id}")
        print(f"  Trigger at {args.percent}% loss")

    elif args.command == "take-profit":
        alert = monitor.add_take_profit(
            asset=args.asset,
            trigger_percent=args.percent,
            cost_basis=args.cost_basis,
            sell_percent=args.sell_percent
        )
        print(f"✓ Added take-profit: {alert.alert_id}")
        print(f"  Trigger at {args.percent}% gain, sell {args.sell_percent}%")

    elif args.command == "trailing":
        alert = monitor.add_trailing_stop(
            asset=args.asset,
            distance_percent=args.distance
        )
        print(f"✓ Added trailing stop: {alert.alert_id}")
        print(f"  Trigger at {args.distance}% below peak")

    elif args.command == "remove":
        monitor.remove_alert(args.alert_id)

    elif args.command == "cost-basis":
        monitor.set_cost_basis(args.asset, args.price)
        print(f"✓ Set cost basis for {args.asset}: ${args.price:,.2f}")

    elif args.command == "monitor":
        monitor.run_monitor(check_interval_seconds=args.interval)

    elif args.command == "check":
        events = monitor.check_all_alerts()
        if not events:
            print("No alerts triggered.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

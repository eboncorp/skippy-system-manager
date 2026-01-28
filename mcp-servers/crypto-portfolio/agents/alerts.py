"""
Alerts and notification system.

Sends notifications via Discord, Telegram, or email
for portfolio events, price alerts, and rebalancing triggers.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import settings


class AlertType(Enum):
    """Types of alerts."""
    PRICE_ALERT = "price_alert"
    DRIFT_ALERT = "drift_alert"
    REBALANCE_NEEDED = "rebalance_needed"
    REBALANCE_COMPLETE = "rebalance_complete"
    DCA_EXECUTED = "dca_executed"
    STAKING_REWARD = "staking_reward"
    ERROR = "error"
    INFO = "info"


@dataclass
class Alert:
    """An alert to be sent."""
    type: AlertType
    title: str
    message: str
    timestamp: datetime = None
    data: Dict[str, Any] = None
    priority: str = "normal"  # low, normal, high, urgent
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.data is None:
            self.data = {}


class NotificationChannel:
    """Base class for notification channels."""
    
    async def send(self, alert: Alert) -> bool:
        """Send an alert. Returns True if successful."""
        raise NotImplementedError


class DiscordChannel(NotificationChannel):
    """Discord webhook notification channel."""
    
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def _format_message(self, alert: Alert) -> dict:
        """Format alert as Discord embed."""
        color_map = {
            AlertType.PRICE_ALERT: 0x3498db,  # Blue
            AlertType.DRIFT_ALERT: 0xf1c40f,  # Yellow
            AlertType.REBALANCE_NEEDED: 0xe67e22,  # Orange
            AlertType.REBALANCE_COMPLETE: 0x2ecc71,  # Green
            AlertType.DCA_EXECUTED: 0x2ecc71,  # Green
            AlertType.STAKING_REWARD: 0x9b59b6,  # Purple
            AlertType.ERROR: 0xe74c3c,  # Red
            AlertType.INFO: 0x95a5a6,  # Gray
        }
        
        priority_emoji = {
            "low": "",
            "normal": "",
            "high": "⚠️ ",
            "urgent": "🚨 ",
        }
        
        return {
            "embeds": [{
                "title": f"{priority_emoji.get(alert.priority, '')}{alert.title}",
                "description": alert.message,
                "color": color_map.get(alert.type, 0x95a5a6),
                "timestamp": alert.timestamp.isoformat(),
                "footer": {"text": f"Crypto Portfolio Manager | {alert.type.value}"},
            }]
        }
    
    async def send(self, alert: Alert) -> bool:
        """Send alert to Discord."""
        if not self.webhook_url:
            return False
        
        payload = self._format_message(alert)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.webhook_url, json=payload) as resp:
                return resp.status in (200, 204)


class TelegramChannel(NotificationChannel):
    """Telegram bot notification channel."""
    
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
    
    def _format_message(self, alert: Alert) -> str:
        """Format alert as Telegram message."""
        priority_emoji = {
            "low": "ℹ️",
            "normal": "📊",
            "high": "⚠️",
            "urgent": "🚨",
        }
        
        emoji = priority_emoji.get(alert.priority, "📊")
        
        return f"{emoji} *{alert.title}*\n\n{alert.message}"
    
    async def send(self, alert: Alert) -> bool:
        """Send alert to Telegram."""
        if not self.bot_token or not self.chat_id:
            return False
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": self._format_message(alert),
            "parse_mode": "Markdown",
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                return resp.status == 200


class EmailChannel(NotificationChannel):
    """Email notification channel."""
    
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        username: str,
        password: str,
        to_address: str,
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.to_address = to_address
    
    async def send(self, alert: Alert) -> bool:
        """Send alert via email."""
        if not all([self.smtp_host, self.username, self.password, self.to_address]):
            return False
        
        msg = MIMEMultipart()
        msg["From"] = self.username
        msg["To"] = self.to_address
        msg["Subject"] = f"[Crypto Portfolio] {alert.title}"
        
        body = f"""
{alert.message}

---
Type: {alert.type.value}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
Priority: {alert.priority}
        """
        
        msg.attach(MIMEText(body, "plain"))
        
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_email, msg)
            return True
        except Exception as e:
            print(f"Email send failed: {e}")
            return False
    
    def _send_email(self, msg: MIMEMultipart):
        """Synchronous email sending."""
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)


class AlertManager:
    """Manages alerts and notifications."""
    
    def __init__(self):
        self.channels: List[NotificationChannel] = []
        self._alert_history: List[Alert] = []
        self._setup_channels()
    
    def _setup_channels(self):
        """Set up notification channels based on config."""
        method = settings.notifications.method
        
        if method == "discord" and settings.notifications.discord_webhook_url:
            self.channels.append(
                DiscordChannel(settings.notifications.discord_webhook_url)
            )
        
        elif method == "telegram":
            if settings.notifications.telegram_bot_token and settings.notifications.telegram_chat_id:
                self.channels.append(
                    TelegramChannel(
                        settings.notifications.telegram_bot_token,
                        settings.notifications.telegram_chat_id,
                    )
                )
        
        elif method == "email":
            self.channels.append(
                EmailChannel(
                    settings.notifications.smtp_host,
                    settings.notifications.smtp_port,
                    settings.notifications.smtp_user,
                    settings.notifications.smtp_password,
                    settings.notifications.email_to,
                )
            )
    
    async def send_alert(self, alert: Alert) -> bool:
        """Send an alert to all configured channels."""
        self._alert_history.append(alert)
        
        if not self.channels:
            # No channels configured, just log
            print(f"[ALERT] {alert.title}: {alert.message}")
            return True
        
        results = await asyncio.gather(
            *[channel.send(alert) for channel in self.channels],
            return_exceptions=True
        )
        
        return any(r is True for r in results)
    
    # Convenience methods for common alerts
    
    async def notify_drift(
        self,
        asset: str,
        drift_pct: float,
        target_pct: float,
        actual_pct: float,
    ):
        """Send drift alert."""
        direction = "over" if drift_pct > 0 else "under"
        
        alert = Alert(
            type=AlertType.DRIFT_ALERT,
            title=f"Portfolio Drift: {asset}",
            message=f"{asset} is {abs(drift_pct)*100:.1f}% {direction}weight.\n"
                    f"Target: {target_pct*100:.1f}% | Actual: {actual_pct*100:.1f}%",
            priority="normal",
        )
        await self.send_alert(alert)
    
    async def notify_rebalance_needed(self, total_drift: float, assets: List[str]):
        """Send rebalance needed alert."""
        alert = Alert(
            type=AlertType.REBALANCE_NEEDED,
            title="Portfolio Rebalancing Needed",
            message=f"Total drift: {total_drift*100:.1f}%\n"
                    f"Assets out of balance: {', '.join(assets)}",
            priority="high",
        )
        await self.send_alert(alert)
    
    async def notify_rebalance_complete(
        self,
        trades_executed: int,
        total_volume: float,
    ):
        """Send rebalance complete alert."""
        alert = Alert(
            type=AlertType.REBALANCE_COMPLETE,
            title="Rebalancing Complete",
            message=f"Executed {trades_executed} trades\n"
                    f"Total volume: ${total_volume:,.2f}",
            priority="normal",
        )
        await self.send_alert(alert)
    
    async def notify_dca_executed(
        self,
        total_amount: float,
        assets: List[str],
    ):
        """Send DCA execution alert."""
        alert = Alert(
            type=AlertType.DCA_EXECUTED,
            title="DCA Executed",
            message=f"Invested ${total_amount:,.2f} across {len(assets)} assets:\n"
                    f"{', '.join(assets)}",
            priority="low",
        )
        await self.send_alert(alert)
    
    async def notify_staking_reward(
        self,
        asset: str,
        amount: float,
        usd_value: float,
        source: str,
    ):
        """Send staking reward alert."""
        alert = Alert(
            type=AlertType.STAKING_REWARD,
            title=f"Staking Reward: {asset}",
            message=f"Received {amount:.6f} {asset} (${usd_value:.2f})\n"
                    f"Source: {source}",
            priority="low",
        )
        await self.send_alert(alert)
    
    async def notify_error(self, title: str, error: str):
        """Send error alert."""
        alert = Alert(
            type=AlertType.ERROR,
            title=title,
            message=error,
            priority="urgent",
        )
        await self.send_alert(alert)


# Global alert manager instance
alert_manager = AlertManager()

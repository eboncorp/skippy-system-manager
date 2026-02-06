"""
Notification System
===================

Multi-channel notification delivery for alerts and events.

Supported Channels:
- Email (SMTP/aiosmtplib)
- SMS (Twilio)
- Push Notifications (Firebase/APNS)
- Webhooks (Discord/Slack/Custom)
- Desktop (system notifications)

Usage:
    from notifications import NotificationManager
    
    manager = NotificationManager()
    await manager.send(
        channels=["email", "slack"],
        title="BTC Price Alert",
        message="BTC crossed $50,000!",
        data={"price": 50000, "asset": "BTC"}
    )
"""

import asyncio
import json
import logging
import os
import smtplib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from enum import Enum
from typing import Any, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


# =============================================================================
# DATA CLASSES
# =============================================================================


class NotificationPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Notification:
    """Notification to be sent."""
    title: str
    message: str
    channels: List[str]
    priority: NotificationPriority = NotificationPriority.NORMAL
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Tracking
    id: Optional[str] = None
    sent_to: List[str] = field(default_factory=list)
    failed_channels: List[str] = field(default_factory=list)


@dataclass
class NotificationResult:
    """Result of sending a notification."""
    channel: str
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


# =============================================================================
# BASE NOTIFIER
# =============================================================================


class BaseNotifier(ABC):
    """Base class for notification channels."""
    
    def __init__(self, name: str):
        self.name = name
        self.enabled = True
    
    @abstractmethod
    async def send(self, notification: Notification) -> NotificationResult:
        """Send notification through this channel."""
        pass
    
    @abstractmethod
    def is_configured(self) -> bool:
        """Check if this channel is properly configured."""
        pass


# =============================================================================
# EMAIL NOTIFIER
# =============================================================================


class EmailNotifier(BaseNotifier):
    """Send notifications via email."""
    
    def __init__(self):
        super().__init__("email")
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("SMTP_FROM", self.smtp_user)
        self.to_emails = os.getenv("NOTIFICATION_EMAIL", "").split(",")
    
    def is_configured(self) -> bool:
        return bool(self.smtp_user and self.smtp_password and self.to_emails[0])
    
    async def send(self, notification: Notification) -> NotificationResult:
        """Send email notification."""
        if not self.is_configured():
            return NotificationResult(
                channel=self.name,
                success=False,
                error="Email not configured"
            )
        
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"[Crypto Alert] {notification.title}"
            msg["From"] = self.from_email
            msg["To"] = ", ".join(self.to_emails)
            
            # Plain text
            text_content = f"{notification.title}\n\n{notification.message}"
            if notification.data:
                text_content += f"\n\nData: {json.dumps(notification.data, indent=2)}"
            
            # HTML
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: #1a1a2e; color: white; padding: 20px; border-radius: 10px;">
                    <h2 style="color: #f39c12; margin-top: 0;">🔔 {notification.title}</h2>
                    <p style="font-size: 16px; line-height: 1.6;">{notification.message}</p>
                    {self._format_data_html(notification.data) if notification.data else ""}
                    <hr style="border-color: #333;">
                    <p style="font-size: 12px; color: #888;">
                        Sent at {notification.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}
                    </p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(text_content, "plain"))
            msg.attach(MIMEText(html_content, "html"))
            
            # Send via SMTP (sync, but in executor)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._send_smtp, msg)
            
            return NotificationResult(
                channel=self.name,
                success=True,
                message_id=f"email_{notification.timestamp.timestamp()}"
            )
            
        except Exception as e:
            logger.error(f"Email send error: {e}")
            return NotificationResult(
                channel=self.name,
                success=False,
                error=str(e)
            )
    
    def _send_smtp(self, msg: MIMEMultipart):
        """Send email via SMTP (sync)."""
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)
    
    def _format_data_html(self, data: Dict[str, Any]) -> str:
        """Format data as HTML table."""
        rows = "".join(
            f"<tr><td style='padding: 5px; border-bottom: 1px solid #333;'>{k}</td>"
            f"<td style='padding: 5px; border-bottom: 1px solid #333;'>{v}</td></tr>"
            for k, v in data.items()
        )
        return f"""
        <table style="width: 100%; margin-top: 15px; border-collapse: collapse;">
            <thead>
                <tr style="background: #16213e;">
                    <th style="padding: 10px; text-align: left;">Field</th>
                    <th style="padding: 10px; text-align: left;">Value</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
        """


# =============================================================================
# SMS NOTIFIER (TWILIO)
# =============================================================================


class SMSNotifier(BaseNotifier):
    """Send notifications via SMS using Twilio."""
    
    def __init__(self):
        super().__init__("sms")
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID", "")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN", "")
        self.from_number = os.getenv("TWILIO_FROM_NUMBER", "")
        self.to_numbers = os.getenv("SMS_TO_NUMBERS", "").split(",")
        self.api_url = f"https://api.twilio.com/2010-04-01/Accounts/{self.account_sid}/Messages.json"
    
    def is_configured(self) -> bool:
        return bool(self.account_sid and self.auth_token and self.from_number and self.to_numbers[0])
    
    async def send(self, notification: Notification) -> NotificationResult:
        """Send SMS notification."""
        if not self.is_configured():
            return NotificationResult(
                channel=self.name,
                success=False,
                error="SMS not configured"
            )
        
        try:
            # Truncate message for SMS
            sms_message = f"{notification.title}: {notification.message}"[:160]
            
            async with aiohttp.ClientSession() as session:
                results = []
                for to_number in self.to_numbers:
                    if not to_number.strip():
                        continue
                    
                    auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)
                    data = {
                        "From": self.from_number,
                        "To": to_number.strip(),
                        "Body": sms_message
                    }
                    
                    async with session.post(self.api_url, auth=auth, data=data) as resp:
                        if resp.status == 201:
                            result = await resp.json()
                            results.append(result.get("sid"))
                        else:
                            error = await resp.text()
                            logger.error(f"SMS to {to_number} failed: {error}")
            
            return NotificationResult(
                channel=self.name,
                success=len(results) > 0,
                message_id=",".join(results) if results else None
            )
            
        except Exception as e:
            logger.error(f"SMS send error: {e}")
            return NotificationResult(
                channel=self.name,
                success=False,
                error=str(e)
            )


# =============================================================================
# WEBHOOK NOTIFIER (SLACK/DISCORD/CUSTOM)
# =============================================================================


class WebhookNotifier(BaseNotifier):
    """Send notifications via webhooks (Slack, Discord, custom)."""
    
    def __init__(self, name: str = "webhook"):
        super().__init__(name)
        self.slack_webhook = os.getenv("SLACK_WEBHOOK_URL", "")
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL", "")
        self.custom_webhook = os.getenv("CUSTOM_WEBHOOK_URL", "")
    
    def is_configured(self) -> bool:
        return bool(self.slack_webhook or self.discord_webhook or self.custom_webhook)
    
    async def send(self, notification: Notification) -> NotificationResult:
        """Send webhook notification."""
        if not self.is_configured():
            return NotificationResult(
                channel=self.name,
                success=False,
                error="No webhooks configured"
            )
        
        results = []
        
        async with aiohttp.ClientSession() as session:
            # Slack
            if self.slack_webhook:
                result = await self._send_slack(session, notification)
                results.append(("slack", result))
            
            # Discord
            if self.discord_webhook:
                result = await self._send_discord(session, notification)
                results.append(("discord", result))
            
            # Custom
            if self.custom_webhook:
                result = await self._send_custom(session, notification)
                results.append(("custom", result))
        
        success = any(r[1] for r in results)
        errors = [f"{r[0]}: failed" for r in results if not r[1]]
        
        return NotificationResult(
            channel=self.name,
            success=success,
            error=", ".join(errors) if errors else None
        )
    
    async def _send_slack(self, session: aiohttp.ClientSession, notification: Notification) -> bool:
        """Send Slack notification."""
        try:
            # Slack Block Kit format
            payload = {
                "blocks": [
                    {
                        "type": "header",
                        "text": {"type": "plain_text", "text": f"🔔 {notification.title}"}
                    },
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": notification.message}
                    }
                ]
            }
            
            # Add data fields
            if notification.data:
                fields = [
                    {"type": "mrkdwn", "text": f"*{k}:* {v}"}
                    for k, v in list(notification.data.items())[:10]
                ]
                payload["blocks"].append({
                    "type": "section",
                    "fields": fields[:10]  # Slack limit
                })
            
            async with session.post(self.slack_webhook, json=payload) as resp:
                return resp.status == 200
                
        except Exception as e:
            logger.error(f"Slack webhook error: {e}")
            return False
    
    async def _send_discord(self, session: aiohttp.ClientSession, notification: Notification) -> bool:
        """Send Discord notification."""
        try:
            # Discord embed format
            embed = {
                "title": f"🔔 {notification.title}",
                "description": notification.message,
                "color": self._get_discord_color(notification.priority),
                "timestamp": notification.timestamp.isoformat(),
                "fields": [
                    {"name": k, "value": str(v), "inline": True}
                    for k, v in list(notification.data.items())[:25]
                ]
            }
            
            payload = {"embeds": [embed]}
            
            async with session.post(self.discord_webhook, json=payload) as resp:
                return resp.status in [200, 204]
                
        except Exception as e:
            logger.error(f"Discord webhook error: {e}")
            return False
    
    async def _send_custom(self, session: aiohttp.ClientSession, notification: Notification) -> bool:
        """Send to custom webhook."""
        try:
            payload = {
                "title": notification.title,
                "message": notification.message,
                "priority": notification.priority.value,
                "data": notification.data,
                "timestamp": notification.timestamp.isoformat()
            }
            
            async with session.post(self.custom_webhook, json=payload) as resp:
                return resp.status in [200, 201, 204]
                
        except Exception as e:
            logger.error(f"Custom webhook error: {e}")
            return False
    
    def _get_discord_color(self, priority: NotificationPriority) -> int:
        """Get Discord embed color based on priority."""
        colors = {
            NotificationPriority.LOW: 0x3498db,      # Blue
            NotificationPriority.NORMAL: 0x2ecc71,   # Green
            NotificationPriority.HIGH: 0xf39c12,     # Orange
            NotificationPriority.URGENT: 0xe74c3c,   # Red
        }
        return colors.get(priority, 0x95a5a6)


# =============================================================================
# PUSH NOTIFICATION (FIREBASE)
# =============================================================================


class PushNotifier(BaseNotifier):
    """Send push notifications via Firebase Cloud Messaging."""
    
    def __init__(self):
        super().__init__("push")
        self.fcm_server_key = os.getenv("FCM_SERVER_KEY", "")
        self.fcm_url = "https://fcm.googleapis.com/fcm/send"
        self.device_tokens = os.getenv("FCM_DEVICE_TOKENS", "").split(",")
    
    def is_configured(self) -> bool:
        return bool(self.fcm_server_key and self.device_tokens[0])
    
    async def send(self, notification: Notification) -> NotificationResult:
        """Send push notification."""
        if not self.is_configured():
            return NotificationResult(
                channel=self.name,
                success=False,
                error="Push notifications not configured"
            )
        
        try:
            headers = {
                "Authorization": f"key={self.fcm_server_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "registration_ids": [t.strip() for t in self.device_tokens if t.strip()],
                "notification": {
                    "title": notification.title,
                    "body": notification.message,
                    "sound": "default",
                    "priority": "high" if notification.priority in [NotificationPriority.HIGH, NotificationPriority.URGENT] else "normal"
                },
                "data": notification.data
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.fcm_url, headers=headers, json=payload) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return NotificationResult(
                            channel=self.name,
                            success=result.get("success", 0) > 0,
                            message_id=str(result.get("multicast_id"))
                        )
                    else:
                        error = await resp.text()
                        return NotificationResult(
                            channel=self.name,
                            success=False,
                            error=error
                        )
                        
        except Exception as e:
            logger.error(f"Push notification error: {e}")
            return NotificationResult(
                channel=self.name,
                success=False,
                error=str(e)
            )


# =============================================================================
# IN-APP NOTIFIER (Database storage)
# =============================================================================


class InAppNotifier(BaseNotifier):
    """Store notifications in database for in-app display."""
    
    def __init__(self):
        super().__init__("app")
        self.notifications: List[Notification] = []  # In-memory for now
        self.max_notifications = 100
    
    def is_configured(self) -> bool:
        return True  # Always available
    
    async def send(self, notification: Notification) -> NotificationResult:
        """Store notification for in-app display."""
        try:
            self.notifications.insert(0, notification)
            
            # Trim old notifications
            if len(self.notifications) > self.max_notifications:
                self.notifications = self.notifications[:self.max_notifications]
            
            return NotificationResult(
                channel=self.name,
                success=True,
                message_id=f"app_{len(self.notifications)}"
            )
            
        except Exception as e:
            return NotificationResult(
                channel=self.name,
                success=False,
                error=str(e)
            )
    
    def get_notifications(self, limit: int = 20) -> List[Notification]:
        """Get recent notifications."""
        return self.notifications[:limit]
    
    def mark_read(self, notification_id: str):
        """Mark notification as read."""
        pass  # Implement with database


# =============================================================================
# NOTIFICATION MANAGER
# =============================================================================


class NotificationManager:
    """
    Manages all notification channels.
    
    Usage:
        manager = NotificationManager()
        
        await manager.send(
            channels=["email", "slack", "app"],
            title="Price Alert",
            message="BTC has crossed $50,000!",
            priority="high",
            data={"price": 50000, "change": "+5%"}
        )
    """
    
    def __init__(self):
        self.notifiers: Dict[str, BaseNotifier] = {}
        self._register_default_notifiers()
    
    def _register_default_notifiers(self):
        """Register all default notification channels."""
        self.notifiers["email"] = EmailNotifier()
        self.notifiers["sms"] = SMSNotifier()
        self.notifiers["webhook"] = WebhookNotifier()
        self.notifiers["slack"] = WebhookNotifier("slack")  # Alias
        self.notifiers["discord"] = WebhookNotifier("discord")  # Alias
        self.notifiers["push"] = PushNotifier()
        self.notifiers["app"] = InAppNotifier()
    
    def register(self, name: str, notifier: BaseNotifier):
        """Register a custom notifier."""
        self.notifiers[name] = notifier
    
    def get_configured_channels(self) -> List[str]:
        """Get list of properly configured channels."""
        return [name for name, notifier in self.notifiers.items() if notifier.is_configured()]
    
    async def send(
        self,
        channels: List[str],
        title: str,
        message: str,
        priority: str = "normal",
        data: Optional[Dict[str, Any]] = None
    ) -> List[NotificationResult]:
        """
        Send notification to multiple channels.
        
        Args:
            channels: List of channel names
            title: Notification title
            message: Notification body
            priority: low, normal, high, urgent
            data: Additional data to include
        
        Returns:
            List of NotificationResult for each channel
        """
        notification = Notification(
            title=title,
            message=message,
            channels=channels,
            priority=NotificationPriority(priority),
            data=data or {}
        )
        
        results = []
        tasks = []
        
        for channel in channels:
            if channel not in self.notifiers:
                results.append(NotificationResult(
                    channel=channel,
                    success=False,
                    error=f"Unknown channel: {channel}"
                ))
                continue
            
            notifier = self.notifiers[channel]
            if not notifier.enabled:
                results.append(NotificationResult(
                    channel=channel,
                    success=False,
                    error="Channel disabled"
                ))
                continue
            
            tasks.append(notifier.send(notification))
        
        # Send all in parallel
        if tasks:
            task_results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in task_results:
                if isinstance(result, Exception):
                    results.append(NotificationResult(
                        channel="unknown",
                        success=False,
                        error=str(result)
                    ))
                else:
                    results.append(result)
        
        return results
    
    async def send_price_alert(
        self,
        asset: str,
        price: float,
        alert_type: str,
        threshold: float,
        channels: Optional[List[str]] = None
    ) -> List[NotificationResult]:
        """Send a price alert notification."""
        channels = channels or ["app", "email"]
        
        if alert_type == "above":
            title = f"🚀 {asset} Price Alert"
            message = f"{asset} has risen above ${threshold:,.2f}! Current price: ${price:,.2f}"
        else:
            title = f"📉 {asset} Price Alert"
            message = f"{asset} has dropped below ${threshold:,.2f}! Current price: ${price:,.2f}"
        
        return await self.send(
            channels=channels,
            title=title,
            message=message,
            priority="high",
            data={
                "asset": asset,
                "price": price,
                "threshold": threshold,
                "alert_type": alert_type
            }
        )
    
    async def send_trade_notification(
        self,
        asset: str,
        side: str,
        amount: float,
        price: float,
        exchange: str,
        channels: Optional[List[str]] = None
    ) -> List[NotificationResult]:
        """Send trade execution notification."""
        channels = channels or ["app"]
        
        emoji = "🟢" if side == "buy" else "🔴"
        title = f"{emoji} Trade Executed"
        message = f"{side.upper()} {amount} {asset} at ${price:,.2f} on {exchange}"
        
        return await self.send(
            channels=channels,
            title=title,
            message=message,
            data={
                "asset": asset,
                "side": side,
                "amount": amount,
                "price": price,
                "exchange": exchange,
                "total": amount * price
            }
        )


# =============================================================================
# EXAMPLE USAGE
# =============================================================================


async def example_usage():
    """Demonstrate notification system."""
    manager = NotificationManager()
    
    # Check configured channels
    print(f"Configured channels: {manager.get_configured_channels()}")
    
    # Send test notification
    results = await manager.send(
        channels=["app"],
        title="Test Alert",
        message="This is a test notification from the crypto portfolio analyzer.",
        priority="normal",
        data={"test": True, "timestamp": datetime.utcnow().isoformat()}
    )
    
    for result in results:
        print(f"{result.channel}: {'✓' if result.success else '✗'} {result.error or ''}")
    
    # Send price alert
    await manager.send_price_alert(
        asset="BTC",
        price=51234.56,
        alert_type="above",
        threshold=50000,
        channels=["app"]
    )


if __name__ == "__main__":
    asyncio.run(example_usage())

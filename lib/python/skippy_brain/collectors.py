"""
Log Collectors - Gather logs from all sources into unified format.
"""

import json
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterator, Optional
from dataclasses import dataclass, asdict


@dataclass
class LogEvent:
    """Unified log event format."""
    timestamp: str
    source: str  # system, app, claude
    category: str  # auth, mcp, tool, etc.
    level: str  # info, warning, error, critical
    message: str
    metadata: dict = None

    def to_dict(self):
        return asdict(self)

    def to_json(self):
        return json.dumps(self.to_dict())


class BaseCollector:
    """Base class for log collectors."""

    def __init__(self):
        self.events = []

    def collect(self, since: Optional[datetime] = None) -> list[LogEvent]:
        """Collect logs since given time. Override in subclasses."""
        raise NotImplementedError

    def parse_timestamp(self, ts_str: str) -> str:
        """Parse various timestamp formats to ISO format."""
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%b %d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f",
        ]
        for fmt in formats:
            try:
                dt = datetime.strptime(ts_str.strip(), fmt)
                if dt.year == 1900:  # syslog format without year
                    dt = dt.replace(year=datetime.now().year)
                return dt.isoformat()
            except ValueError:
                continue
        return datetime.now().isoformat()


class SystemCollector(BaseCollector):
    """Collect system logs (journald, auth, fail2ban)."""

    def collect(self, since: Optional[datetime] = None) -> list[LogEvent]:
        events = []
        since = since or datetime.now() - timedelta(hours=24)

        # Journald errors
        events.extend(self._collect_journald(since))

        # Auth log
        events.extend(self._collect_auth_log(since))

        # Fail2ban
        events.extend(self._collect_fail2ban(since))

        return events

    def _collect_journald(self, since: datetime) -> list[LogEvent]:
        """Collect errors from journald."""
        events = []
        try:
            since_str = since.strftime("%Y-%m-%d %H:%M:%S")
            result = subprocess.run(
                ["journalctl", "-p", "err", "--since", since_str,
                 "--no-pager", "-o", "json"],
                capture_output=True, text=True, timeout=30
            )
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    events.append(LogEvent(
                        timestamp=datetime.fromtimestamp(
                            int(entry.get("__REALTIME_TIMESTAMP", 0)) / 1000000
                        ).isoformat(),
                        source="system",
                        category="journald",
                        level="error",
                        message=entry.get("MESSAGE", ""),
                        metadata={
                            "unit": entry.get("_SYSTEMD_UNIT", ""),
                            "pid": entry.get("_PID", ""),
                        }
                    ))
                except json.JSONDecodeError:
                    continue
        except Exception as e:
            pass  # Permission issues are common
        return events

    def _collect_auth_log(self, since: datetime) -> list[LogEvent]:
        """Collect from auth.log."""
        events = []
        auth_log = Path("/var/log/auth.log")
        if not auth_log.exists():
            return events

        try:
            with open(auth_log, 'r', errors='replace') as f:
                for line in f:
                    # Parse syslog format: "Jan 24 17:20:01 hostname ..."
                    match = re.match(r'^(\w+\s+\d+\s+[\d:]+)\s+\S+\s+(.+)$', line)
                    if match:
                        ts_str, message = match.groups()
                        ts = self.parse_timestamp(ts_str)

                        level = "info"
                        if "failed" in message.lower() or "error" in message.lower():
                            level = "error"
                        elif "warning" in message.lower():
                            level = "warning"

                        if level in ("error", "warning"):
                            events.append(LogEvent(
                                timestamp=ts,
                                source="system",
                                category="auth",
                                level=level,
                                message=message.strip(),
                            ))
        except PermissionError:
            pass
        return events[-100:]  # Last 100 events

    def _collect_fail2ban(self, since: datetime) -> list[LogEvent]:
        """Collect from fail2ban.log."""
        events = []
        fail2ban_log = Path("/var/log/fail2ban.log")
        if not fail2ban_log.exists():
            return events

        try:
            with open(fail2ban_log, 'r', errors='replace') as f:
                for line in f:
                    if "Ban" in line or "Unban" in line:
                        # Parse: "2026-01-23 12:52:01,234 fail2ban.actions ..."
                        match = re.match(r'^([\d-]+\s+[\d:,]+)\s+(.+)$', line)
                        if match:
                            ts_str, message = match.groups()
                            events.append(LogEvent(
                                timestamp=self.parse_timestamp(ts_str.split(',')[0]),
                                source="system",
                                category="fail2ban",
                                level="warning" if "Ban" in line else "info",
                                message=message.strip(),
                            ))
        except PermissionError:
            pass
        return events[-50:]


class AppCollector(BaseCollector):
    """Collect application logs (MCP, WordPress, Skippy)."""

    def __init__(self):
        super().__init__()
        self.skippy_root = Path(os.environ.get("SKIPPY_HOME", "/home/dave/skippy"))

    def collect(self, since: Optional[datetime] = None) -> list[LogEvent]:
        events = []
        since = since or datetime.now() - timedelta(hours=24)

        # Skippy combined log
        events.extend(self._collect_skippy_log(since))

        # MCP logs
        events.extend(self._collect_mcp_logs(since))

        # WordPress backup log
        events.extend(self._collect_wordpress_log(since))

        # Cron/maintenance logs
        events.extend(self._collect_maintenance_logs(since))

        return events

    def _collect_skippy_log(self, since: datetime) -> list[LogEvent]:
        """Collect from skippy_combined.log."""
        events = []
        log_file = self.skippy_root / "logs" / "skippy_combined.log"
        if not log_file.exists():
            return events

        try:
            with open(log_file, 'r', errors='replace') as f:
                for line in f:
                    # Parse: "[2026-01-24 12:00:00] ERROR: message"
                    match = re.match(r'^\[([\d-]+\s+[\d:]+)\]\s+(\w+):\s*(.+)$', line)
                    if match:
                        ts_str, level, message = match.groups()
                        if level.upper() in ("ERROR", "WARNING", "CRITICAL"):
                            events.append(LogEvent(
                                timestamp=self.parse_timestamp(ts_str),
                                source="app",
                                category="skippy",
                                level=level.lower(),
                                message=message.strip(),
                            ))
        except Exception:
            pass
        return events[-100:]

    def _collect_mcp_logs(self, since: datetime) -> list[LogEvent]:
        """Collect MCP server logs."""
        events = []
        mcp_log_dir = self.skippy_root / "logs" / "mcp"
        if not mcp_log_dir.exists():
            return events

        for log_file in mcp_log_dir.glob("*.log"):
            try:
                with open(log_file, 'r', errors='replace') as f:
                    for line in f:
                        if "error" in line.lower() or "fail" in line.lower():
                            events.append(LogEvent(
                                timestamp=datetime.now().isoformat(),
                                source="app",
                                category="mcp",
                                level="error",
                                message=line.strip()[:500],
                                metadata={"file": log_file.name}
                            ))
            except Exception:
                pass
        return events[-50:]

    def _collect_wordpress_log(self, since: datetime) -> list[LogEvent]:
        """Collect WordPress backup/operation logs."""
        events = []
        log_file = self.skippy_root / "logs" / "wordpress_backup.log"
        if not log_file.exists():
            return events

        try:
            with open(log_file, 'r', errors='replace') as f:
                for line in f:
                    if "error" in line.lower() or "fail" in line.lower():
                        events.append(LogEvent(
                            timestamp=datetime.now().isoformat(),
                            source="app",
                            category="wordpress",
                            level="error",
                            message=line.strip()[:500],
                        ))
        except Exception:
            pass
        return events[-50:]

    def _collect_maintenance_logs(self, since: datetime) -> list[LogEvent]:
        """Collect maintenance/cron logs."""
        events = []
        log_file = self.skippy_root / "logs" / "weekly_maintenance.log"
        if not log_file.exists():
            return events

        try:
            with open(log_file, 'r', errors='replace') as f:
                for line in f:
                    if "error" in line.lower() or "fail" in line.lower():
                        events.append(LogEvent(
                            timestamp=datetime.now().isoformat(),
                            source="app",
                            category="maintenance",
                            level="error",
                            message=line.strip()[:500],
                        ))
        except Exception:
            pass
        return events[-20:]


class ClaudeCollector(BaseCollector):
    """Collect Claude Code logs (tools, sessions, hooks)."""

    def __init__(self):
        super().__init__()
        self.claude_dir = Path.home() / ".claude"

    def collect(self, since: Optional[datetime] = None) -> list[LogEvent]:
        events = []
        since = since or datetime.now() - timedelta(hours=24)

        # Tool usage logs
        events.extend(self._collect_tool_logs(since))

        # Blocked commands
        events.extend(self._collect_blocked_logs(since))

        # Session cleanup logs
        events.extend(self._collect_session_logs(since))

        # Email audit logs
        events.extend(self._collect_email_logs(since))

        # Skippy-learn issues
        events.extend(self._collect_learning_logs(since))

        return events

    def _collect_tool_logs(self, since: datetime) -> list[LogEvent]:
        """Collect tool usage stats."""
        events = []
        stats_file = self.claude_dir / "tool_logs" / "tool_stats.json"
        if stats_file.exists():
            try:
                stats = json.loads(stats_file.read_text())
                events.append(LogEvent(
                    timestamp=datetime.now().isoformat(),
                    source="claude",
                    category="tool_stats",
                    level="info",
                    message=f"Tool usage: {stats.get('total', 0)} total calls",
                    metadata=stats.get("tools", {})
                ))
            except Exception:
                pass
        return events

    def _collect_blocked_logs(self, since: datetime) -> list[LogEvent]:
        """Collect blocked commands/files."""
        events = []

        for log_name in ["blocked_commands.log", "blocked_files.log", "warned_commands.log"]:
            log_file = self.claude_dir / "tool_logs" / log_name
            if not log_file.exists():
                continue
            try:
                with open(log_file, 'r', errors='replace') as f:
                    for line in f:
                        # Parse: "[2026-01-24 17:00:00] BLOCKED: ..."
                        match = re.match(r'^\[([\d-]+\s+[\d:]+)\]\s+(\w+):\s*(.+)$', line)
                        if match:
                            ts_str, level, message = match.groups()
                            events.append(LogEvent(
                                timestamp=self.parse_timestamp(ts_str),
                                source="claude",
                                category="security",
                                level="warning" if "WARN" in level else "error",
                                message=message.strip()[:500],
                            ))
            except Exception:
                pass
        return events[-50:]

    def _collect_session_logs(self, since: datetime) -> list[LogEvent]:
        """Collect session cleanup logs."""
        events = []
        log_file = self.claude_dir / "session_cleanup_logs" / "sessions.log"
        if not log_file.exists():
            return events

        try:
            with open(log_file, 'r', errors='replace') as f:
                for line in f:
                    if "error" in line.lower() or "warning" in line.lower():
                        events.append(LogEvent(
                            timestamp=datetime.now().isoformat(),
                            source="claude",
                            category="session",
                            level="warning",
                            message=line.strip()[:500],
                        ))
        except Exception:
            pass
        return events[-20:]

    def _collect_email_logs(self, since: datetime) -> list[LogEvent]:
        """Collect email audit logs."""
        events = []
        log_file = self.claude_dir / "tool_logs" / "email_audit.log"
        if not log_file.exists():
            return events

        try:
            with open(log_file, 'r', errors='replace') as f:
                for line in f:
                    match = re.match(r'^\[([\d-]+\s+[\d:]+)\]\s+EMAIL:\s*(.+)$', line)
                    if match:
                        ts_str, message = match.groups()
                        events.append(LogEvent(
                            timestamp=self.parse_timestamp(ts_str),
                            source="claude",
                            category="email",
                            level="info",
                            message=message.strip()[:500],
                        ))
        except Exception:
            pass
        return events[-20:]

    def _collect_learning_logs(self, since: datetime) -> list[LogEvent]:
        """Collect skippy-learn issues."""
        events = []
        issues_file = Path("/home/dave/skippy/.claude/learning/issues.jsonl")
        if not issues_file.exists():
            return events

        try:
            with open(issues_file, 'r') as f:
                for line in f:
                    try:
                        issue = json.loads(line)
                        events.append(LogEvent(
                            timestamp=issue.get("timestamp", datetime.now().isoformat()),
                            source="claude",
                            category="learning",
                            level=issue.get("category", "info"),
                            message=issue.get("description", ""),
                            metadata=issue
                        ))
                    except json.JSONDecodeError:
                        continue
        except Exception:
            pass
        return events

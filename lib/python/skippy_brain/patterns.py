"""
Pattern Detection Engine - Find recurring issues and correlations.
"""

import json
import re
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict


@dataclass
class Pattern:
    """Detected pattern in logs."""
    id: str
    name: str
    description: str
    frequency: int
    severity: str  # low, medium, high, critical
    sources: list[str]
    example_messages: list[str]
    suggested_action: str
    auto_preventable: bool = False

    def to_dict(self):
        return asdict(self)


class PatternEngine:
    """Detect patterns in collected log events."""

    def __init__(self):
        self.patterns_file = Path("/home/dave/skippy/.claude/learning/detected_patterns.json")
        self.patterns_file.parent.mkdir(parents=True, exist_ok=True)

    def analyze(self, events: list) -> list[Pattern]:
        """Analyze events and detect patterns."""
        patterns = []

        # Group by message similarity
        message_groups = self._group_similar_messages(events)

        # Detect recurring errors (same message 3+ times)
        patterns.extend(self._detect_recurring_errors(message_groups))

        # Detect temporal patterns (errors at same time)
        patterns.extend(self._detect_temporal_patterns(events))

        # Detect correlation patterns (A happens before B)
        patterns.extend(self._detect_correlations(events))

        # Detect category spikes
        patterns.extend(self._detect_category_spikes(events))

        # Save patterns
        self._save_patterns(patterns)

        return patterns

    def _group_similar_messages(self, events: list) -> dict:
        """Group events by similar message content."""
        groups = defaultdict(list)

        for event in events:
            # Normalize message (remove numbers, paths, timestamps)
            normalized = re.sub(r'\d+', 'N', event.message)
            normalized = re.sub(r'/[\w/.-]+', '/PATH', normalized)
            normalized = re.sub(r'\b[a-f0-9]{8,}\b', 'HASH', normalized)
            normalized = normalized[:100]  # First 100 chars as key

            groups[normalized].append(event)

        return groups

    def _detect_recurring_errors(self, groups: dict) -> list[Pattern]:
        """Find errors that occur 3+ times."""
        patterns = []

        for normalized, events in groups.items():
            if len(events) >= 3:
                # Only errors/warnings
                error_events = [e for e in events if e.level in ('error', 'warning', 'critical')]
                if len(error_events) >= 3:
                    sources = list(set(e.source for e in error_events))
                    categories = list(set(e.category for e in error_events))

                    severity = "high" if any(e.level == "critical" for e in error_events) else \
                               "medium" if len(error_events) >= 5 else "low"

                    patterns.append(Pattern(
                        id=f"recurring_{hash(normalized) % 10000:04d}",
                        name=f"Recurring {categories[0]} error",
                        description=f"Same error occurred {len(error_events)} times",
                        frequency=len(error_events),
                        severity=severity,
                        sources=sources,
                        example_messages=[e.message[:200] for e in error_events[:3]],
                        suggested_action=self._suggest_action(categories[0], error_events[0].message),
                        auto_preventable=self._is_auto_preventable(categories[0], error_events[0].message),
                    ))

        return patterns

    def _detect_temporal_patterns(self, events: list) -> list[Pattern]:
        """Find errors that occur at similar times."""
        patterns = []

        # Group by hour of day
        hour_groups = defaultdict(list)
        for event in events:
            try:
                dt = datetime.fromisoformat(event.timestamp.replace('Z', '+00:00'))
                hour = dt.hour
                hour_groups[hour].append(event)
            except:
                continue

        # Find hours with unusual error spikes
        for hour, hour_events in hour_groups.items():
            errors = [e for e in hour_events if e.level in ('error', 'critical')]
            if len(errors) >= 5:
                patterns.append(Pattern(
                    id=f"temporal_{hour:02d}00",
                    name=f"Error spike at {hour:02d}:00",
                    description=f"{len(errors)} errors occur around {hour:02d}:00",
                    frequency=len(errors),
                    severity="medium",
                    sources=list(set(e.source for e in errors)),
                    example_messages=[e.message[:200] for e in errors[:3]],
                    suggested_action=f"Check scheduled tasks/cron jobs running at {hour:02d}:00",
                    auto_preventable=False,
                ))

        return patterns

    def _detect_correlations(self, events: list) -> list[Pattern]:
        """Find events that correlate (A happens before B)."""
        patterns = []

        # Sort by timestamp
        try:
            sorted_events = sorted(events, key=lambda e: e.timestamp)
        except:
            return patterns

        # Look for A -> B patterns within 5 minutes
        correlations = defaultdict(int)
        for i, event_a in enumerate(sorted_events):
            if event_a.level not in ('error', 'warning'):
                continue
            for event_b in sorted_events[i+1:i+20]:  # Next 20 events
                if event_b.level not in ('error', 'warning'):
                    continue
                if event_a.category != event_b.category:
                    key = f"{event_a.category}:{event_a.level} -> {event_b.category}:{event_b.level}"
                    correlations[key] += 1

        # Report correlations that happen 3+ times
        for correlation, count in correlations.items():
            if count >= 3:
                parts = correlation.split(" -> ")
                patterns.append(Pattern(
                    id=f"corr_{hash(correlation) % 10000:04d}",
                    name=f"Correlation: {correlation}",
                    description=f"{parts[0]} errors often precede {parts[1]} errors",
                    frequency=count,
                    severity="medium",
                    sources=["multiple"],
                    example_messages=[],
                    suggested_action=f"Investigate if {parts[0].split(':')[0]} issues cause {parts[1].split(':')[0]} failures",
                    auto_preventable=False,
                ))

        return patterns

    def _detect_category_spikes(self, events: list) -> list[Pattern]:
        """Find categories with unusual error rates."""
        patterns = []

        category_counts = defaultdict(lambda: {"total": 0, "errors": 0})
        for event in events:
            category_counts[event.category]["total"] += 1
            if event.level in ('error', 'critical'):
                category_counts[event.category]["errors"] += 1

        for category, counts in category_counts.items():
            if counts["total"] >= 10:
                error_rate = counts["errors"] / counts["total"]
                if error_rate > 0.5:  # More than 50% errors
                    patterns.append(Pattern(
                        id=f"spike_{category}",
                        name=f"High error rate in {category}",
                        description=f"{error_rate:.0%} error rate ({counts['errors']}/{counts['total']})",
                        frequency=counts["errors"],
                        severity="high" if error_rate > 0.75 else "medium",
                        sources=[category],
                        example_messages=[],
                        suggested_action=f"Investigate {category} service health",
                        auto_preventable=False,
                    ))

        return patterns

    def _suggest_action(self, category: str, message: str) -> str:
        """Suggest action based on error type."""
        suggestions = {
            "auth": "Check authentication configuration and credentials",
            "mcp": "Restart MCP server or check connection settings",
            "wordpress": "Check WordPress logs and plugin conflicts",
            "security": "Review security rules and blocked patterns",
            "email": "Verify email configuration and body content",
            "journald": "Check system service status",
            "fail2ban": "Review firewall rules and banned IPs",
        }
        return suggestions.get(category, "Investigate root cause")

    def _is_auto_preventable(self, category: str, message: str) -> bool:
        """Check if this error can be auto-prevented with a hook."""
        preventable_patterns = [
            ("email", "empty"),
            ("security", "blocked"),
            ("tool", "dangerous"),
        ]
        message_lower = message.lower()
        for cat, keyword in preventable_patterns:
            if category == cat or keyword in message_lower:
                return True
        return False

    def _save_patterns(self, patterns: list[Pattern]):
        """Save detected patterns to file."""
        data = {
            "last_updated": datetime.now().isoformat(),
            "patterns": [p.to_dict() for p in patterns]
        }
        self.patterns_file.write_text(json.dumps(data, indent=2))

    def load_patterns(self) -> list[Pattern]:
        """Load previously detected patterns."""
        if not self.patterns_file.exists():
            return []
        try:
            data = json.loads(self.patterns_file.read_text())
            return [Pattern(**p) for p in data.get("patterns", [])]
        except:
            return []

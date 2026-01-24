"""
Skippy Brain - Main Orchestration Module.

Unified log aggregation, pattern detection, and auto-prevention.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .collectors import SystemCollector, AppCollector, ClaudeCollector, LogEvent
from .patterns import PatternEngine, Pattern
from .prevention import PreventionGenerator, PreventionRule


class Brain:
    """
    Skippy Brain - Unified intelligence system.

    Aggregates logs from all sources, detects patterns, and
    auto-generates prevention rules.

    Usage:
        brain = Brain()
        brain.ingest_all()
        patterns = brain.detect_patterns()
        rules = brain.generate_prevention_rules()
        brain.get_report()
    """

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path("/home/dave/skippy/.claude/learning")
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        self.system_collector = SystemCollector()
        self.app_collector = AppCollector()
        self.claude_collector = ClaudeCollector()
        self.pattern_engine = PatternEngine()
        self.prevention_generator = PreventionGenerator()

        # Event storage
        self.events_file = self.data_dir / "aggregated_events.jsonl"
        self.state_file = self.data_dir / "brain_state.json"
        self.events: list[LogEvent] = []

        # State
        self.last_ingest: Optional[datetime] = None
        self.last_analysis: Optional[datetime] = None

        # Load persisted state
        self._load_state()

    def ingest_all(self, since: Optional[datetime] = None) -> dict:
        """
        Ingest logs from all sources.

        Args:
            since: Only collect logs since this time. Defaults to 24 hours ago.

        Returns:
            Dictionary with ingestion statistics.
        """
        since = since or datetime.now() - timedelta(hours=24)
        stats = {
            "system": 0,
            "app": 0,
            "claude": 0,
            "total": 0,
            "errors": 0,
            "warnings": 0,
        }

        # Collect from all sources
        try:
            system_events = self.system_collector.collect(since)
            stats["system"] = len(system_events)
            self.events.extend(system_events)
        except Exception as e:
            stats["system_error"] = str(e)

        try:
            app_events = self.app_collector.collect(since)
            stats["app"] = len(app_events)
            self.events.extend(app_events)
        except Exception as e:
            stats["app_error"] = str(e)

        try:
            claude_events = self.claude_collector.collect(since)
            stats["claude"] = len(claude_events)
            self.events.extend(claude_events)
        except Exception as e:
            stats["claude_error"] = str(e)

        # Calculate totals
        stats["total"] = len(self.events)
        stats["errors"] = len([e for e in self.events if e.level in ("error", "critical")])
        stats["warnings"] = len([e for e in self.events if e.level == "warning"])

        # Save events and state
        self._save_events()
        self.last_ingest = datetime.now()
        self._save_state()

        return stats

    def detect_patterns(self) -> list[Pattern]:
        """
        Analyze collected events and detect patterns.

        Returns:
            List of detected patterns.
        """
        if not self.events:
            # Try to load from file
            self._load_events()

        patterns = self.pattern_engine.analyze(self.events)
        self.last_analysis = datetime.now()
        self._save_state()
        return patterns

    def generate_prevention_rules(self, patterns: Optional[list[Pattern]] = None) -> list[PreventionRule]:
        """
        Generate prevention rules from detected patterns.

        Args:
            patterns: Patterns to convert to rules. If None, detects patterns first.

        Returns:
            List of generated prevention rules.
        """
        if patterns is None:
            patterns = self.detect_patterns()

        rules = self.prevention_generator.generate_rules(patterns)
        return rules

    def install_prevention_rules(self, rules: Optional[list[PreventionRule]] = None) -> int:
        """
        Install prevention rules as hook code.

        Args:
            rules: Rules to install. If None, generates from patterns first.

        Returns:
            Number of rules installed.
        """
        if rules is None:
            rules = self.generate_prevention_rules()

        return self.prevention_generator.install_rules(rules)

    def get_report(self) -> dict:
        """
        Generate a comprehensive report of brain activity.

        Returns:
            Dictionary with system intelligence report.
        """
        # Load patterns and rules
        patterns = self.pattern_engine.load_patterns()
        prevention_stats = self.prevention_generator.get_stats()

        # Calculate event stats by category
        if not self.events:
            self._load_events()

        categories = {}
        sources = {}
        levels = {}

        for event in self.events:
            categories[event.category] = categories.get(event.category, 0) + 1
            sources[event.source] = sources.get(event.source, 0) + 1
            levels[event.level] = levels.get(event.level, 0) + 1

        return {
            "summary": {
                "total_events": len(self.events),
                "patterns_detected": len(patterns),
                "prevention_rules": prevention_stats["total_rules"],
                "last_ingest": self.last_ingest.isoformat() if self.last_ingest else None,
                "last_analysis": self.last_analysis.isoformat() if self.last_analysis else None,
            },
            "events_by_category": dict(sorted(categories.items(), key=lambda x: -x[1])),
            "events_by_source": sources,
            "events_by_level": levels,
            "top_patterns": [
                {
                    "name": p.name,
                    "frequency": p.frequency,
                    "severity": p.severity,
                    "auto_preventable": p.auto_preventable,
                }
                for p in sorted(patterns, key=lambda x: -x.frequency)[:10]
            ],
            "prevention": prevention_stats,
        }

    def get_actionable_insights(self) -> list[dict]:
        """
        Get actionable insights from pattern analysis.

        Returns:
            List of actionable items with priorities.
        """
        patterns = self.pattern_engine.load_patterns()
        insights = []

        for pattern in patterns:
            priority = "high" if pattern.severity in ("high", "critical") else \
                       "medium" if pattern.frequency >= 5 else "low"

            insight = {
                "title": pattern.name,
                "description": pattern.description,
                "priority": priority,
                "action": pattern.suggested_action,
                "auto_fixable": pattern.auto_preventable,
                "frequency": pattern.frequency,
                "sources": pattern.sources,
            }
            insights.append(insight)

        # Sort by priority and frequency
        priority_order = {"high": 0, "medium": 1, "low": 2}
        insights.sort(key=lambda x: (priority_order[x["priority"]], -x["frequency"]))

        return insights

    def run_full_cycle(self) -> dict:
        """
        Run a complete ingest -> analyze -> generate cycle.

        Returns:
            Complete report with all actions taken.
        """
        result = {
            "timestamp": datetime.now().isoformat(),
            "stages": {},
        }

        # Stage 1: Ingest
        ingest_stats = self.ingest_all()
        result["stages"]["ingest"] = ingest_stats

        # Stage 2: Detect patterns
        patterns = self.detect_patterns()
        result["stages"]["patterns"] = {
            "detected": len(patterns),
            "auto_preventable": len([p for p in patterns if p.auto_preventable]),
            "high_severity": len([p for p in patterns if p.severity in ("high", "critical")]),
        }

        # Stage 3: Generate rules
        rules = self.generate_prevention_rules(patterns)
        result["stages"]["rules"] = {
            "generated": len(rules),
            "block_rules": len([r for r in rules if r.action == "block"]),
            "warn_rules": len([r for r in rules if r.action == "warn"]),
        }

        # Stage 4: Get insights
        insights = self.get_actionable_insights()
        result["stages"]["insights"] = {
            "total": len(insights),
            "high_priority": len([i for i in insights if i["priority"] == "high"]),
        }

        # Stage 5: Get full report
        result["report"] = self.get_report()

        return result

    def _save_events(self):
        """Save events to JSONL file."""
        with open(self.events_file, 'w') as f:
            for event in self.events:
                f.write(event.to_json() + "\n")

    def _save_state(self):
        """Persist brain state to file."""
        state = {
            "last_ingest": self.last_ingest.isoformat() if self.last_ingest else None,
            "last_analysis": self.last_analysis.isoformat() if self.last_analysis else None,
        }
        self.state_file.write_text(json.dumps(state, indent=2))

    def _load_state(self):
        """Load persisted brain state."""
        if not self.state_file.exists():
            return
        try:
            state = json.loads(self.state_file.read_text())
            if state.get("last_ingest"):
                self.last_ingest = datetime.fromisoformat(state["last_ingest"])
            if state.get("last_analysis"):
                self.last_analysis = datetime.fromisoformat(state["last_analysis"])
        except Exception:
            pass

    def _load_events(self):
        """Load events from JSONL file."""
        self.events = []
        if not self.events_file.exists():
            return

        try:
            with open(self.events_file, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        self.events.append(LogEvent(**data))
        except Exception:
            pass

    def clear_events(self):
        """Clear all stored events."""
        self.events = []
        if self.events_file.exists():
            self.events_file.unlink()

    def get_recent_errors(self, limit: int = 20) -> list[LogEvent]:
        """Get most recent error events."""
        if not self.events:
            self._load_events()

        errors = [e for e in self.events if e.level in ("error", "critical")]
        return sorted(errors, key=lambda x: x.timestamp, reverse=True)[:limit]

    def search_events(self, query: str, limit: int = 50) -> list[LogEvent]:
        """Search events by message content."""
        if not self.events:
            self._load_events()

        query_lower = query.lower()
        matches = [e for e in self.events if query_lower in e.message.lower()]
        return matches[:limit]

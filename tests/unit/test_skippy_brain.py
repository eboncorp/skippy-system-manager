"""
Tests for skippy_brain module.

Tests cover:
- LogEvent dataclass
- Brain orchestration class
- SystemCollector, AppCollector, ClaudeCollector
- PatternEngine and Pattern dataclass
- PreventionGenerator and PreventionRule dataclass
"""

import json
import pytest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

from lib.python.skippy_brain import (
    Brain,
    SystemCollector,
    AppCollector,
    ClaudeCollector,
    PatternEngine,
    PreventionGenerator,
)
from lib.python.skippy_brain.collectors import LogEvent
from lib.python.skippy_brain.patterns import Pattern
from lib.python.skippy_brain.prevention import PreventionRule


# =============================================================================
# LogEvent Tests
# =============================================================================

class TestLogEvent:
    """Tests for LogEvent dataclass."""

    def test_create_log_event(self):
        """Test basic LogEvent creation."""
        event = LogEvent(
            timestamp="2026-01-25T12:00:00",
            source="system",
            category="journald",
            level="error",
            message="Test error message",
        )
        assert event.timestamp == "2026-01-25T12:00:00"
        assert event.source == "system"
        assert event.category == "journald"
        assert event.level == "error"
        assert event.message == "Test error message"
        assert event.metadata is None

    def test_log_event_with_metadata(self):
        """Test LogEvent with metadata."""
        event = LogEvent(
            timestamp="2026-01-25T12:00:00",
            source="app",
            category="mcp",
            level="warning",
            message="Test warning",
            metadata={"file": "test.log", "line": 42},
        )
        assert event.metadata == {"file": "test.log", "line": 42}

    def test_log_event_to_dict(self):
        """Test LogEvent serialization to dict."""
        event = LogEvent(
            timestamp="2026-01-25T12:00:00",
            source="claude",
            category="tool",
            level="info",
            message="Tool executed",
        )
        d = event.to_dict()
        assert isinstance(d, dict)
        assert d["source"] == "claude"
        assert d["category"] == "tool"

    def test_log_event_to_json(self):
        """Test LogEvent serialization to JSON."""
        event = LogEvent(
            timestamp="2026-01-25T12:00:00",
            source="system",
            category="auth",
            level="warning",
            message="Auth warning",
        )
        json_str = event.to_json()
        parsed = json.loads(json_str)
        assert parsed["source"] == "system"
        assert parsed["level"] == "warning"


# =============================================================================
# Pattern Tests
# =============================================================================

class TestPattern:
    """Tests for Pattern dataclass."""

    def test_create_pattern(self):
        """Test basic Pattern creation."""
        pattern = Pattern(
            id="pattern_001",
            name="Recurring auth error",
            description="Authentication failures occurring repeatedly",
            frequency=5,
            severity="medium",
            sources=["system", "app"],
            example_messages=["Auth failed for user X"],
            suggested_action="Check user credentials",
        )
        assert pattern.id == "pattern_001"
        assert pattern.frequency == 5
        assert pattern.severity == "medium"
        assert pattern.auto_preventable is False

    def test_pattern_auto_preventable(self):
        """Test Pattern with auto_preventable flag."""
        pattern = Pattern(
            id="pattern_002",
            name="Empty email body",
            description="Emails sent with empty body",
            frequency=3,
            severity="high",
            sources=["claude"],
            example_messages=["Email sent with empty body"],
            suggested_action="Block empty emails",
            auto_preventable=True,
        )
        assert pattern.auto_preventable is True

    def test_pattern_to_dict(self):
        """Test Pattern serialization to dict."""
        pattern = Pattern(
            id="pattern_003",
            name="Test pattern",
            description="Test description",
            frequency=1,
            severity="low",
            sources=["test"],
            example_messages=["test"],
            suggested_action="test action",
        )
        d = pattern.to_dict()
        assert isinstance(d, dict)
        assert d["id"] == "pattern_003"
        assert d["severity"] == "low"


# =============================================================================
# PreventionRule Tests
# =============================================================================

class TestPreventionRule:
    """Tests for PreventionRule dataclass."""

    def test_create_prevention_rule(self):
        """Test basic PreventionRule creation."""
        rule = PreventionRule(
            id="rule_001",
            name="Block dangerous command",
            trigger="PreToolUse",
            pattern_match="rm -rf",
            action="block",
            reason="Dangerous command detected",
            source_pattern_id="pattern_001",
        )
        assert rule.id == "rule_001"
        assert rule.action == "block"
        assert rule.auto_generated is True
        assert rule.enabled is True

    def test_prevention_rule_to_dict(self):
        """Test PreventionRule serialization."""
        rule = PreventionRule(
            id="rule_002",
            name="Warn on sudo",
            trigger="PreToolUse",
            pattern_match="sudo",
            action="warn",
            reason="Elevated privileges requested",
            source_pattern_id="pattern_002",
        )
        d = rule.to_dict()
        assert isinstance(d, dict)
        assert d["action"] == "warn"

    def test_prevention_rule_to_hook_code_block(self):
        """Test hook code generation for block action."""
        rule = PreventionRule(
            id="rule_003",
            name="Block test",
            trigger="PreToolUse",
            pattern_match="test_pattern",
            action="block",
            reason="Test reason",
            source_pattern_id="pattern_003",
        )
        code = rule.to_hook_code()
        assert "block" in code
        assert "test_pattern" in code
        assert "Test reason" in code

    def test_prevention_rule_to_hook_code_warn(self):
        """Test hook code generation for warn action."""
        rule = PreventionRule(
            id="rule_004",
            name="Warn test",
            trigger="PreToolUse",
            pattern_match="warn_pattern",
            action="warn",
            reason="Warning reason",
            source_pattern_id="pattern_004",
        )
        code = rule.to_hook_code()
        assert "WARNING" in code
        assert "warn_pattern" in code

    def test_prevention_rule_to_hook_code_log(self):
        """Test hook code generation for log action (returns empty)."""
        rule = PreventionRule(
            id="rule_005",
            name="Log test",
            trigger="PreToolUse",
            pattern_match="log_pattern",
            action="log",
            reason="Log reason",
            source_pattern_id="pattern_005",
        )
        code = rule.to_hook_code()
        assert code == ""


# =============================================================================
# BaseCollector Tests
# =============================================================================

class TestBaseCollector:
    """Tests for BaseCollector functionality."""

    def test_parse_timestamp_standard_format(self):
        """Test parsing standard timestamp format."""
        collector = SystemCollector()
        result = collector.parse_timestamp("2026-01-25 12:30:45")
        assert "2026-01-25" in result

    def test_parse_timestamp_iso_format(self):
        """Test parsing ISO timestamp format."""
        collector = SystemCollector()
        result = collector.parse_timestamp("2026-01-25T12:30:45")
        assert "2026-01-25" in result

    def test_parse_timestamp_syslog_format(self):
        """Test parsing syslog timestamp format."""
        collector = SystemCollector()
        result = collector.parse_timestamp("Jan 25 12:30:45")
        # Should use current year
        assert datetime.now().strftime("%Y") in result

    def test_parse_timestamp_invalid_returns_now(self):
        """Test that invalid timestamp returns current time."""
        collector = SystemCollector()
        result = collector.parse_timestamp("invalid_timestamp")
        # Should return something close to now
        assert datetime.now().strftime("%Y-%m-%d") in result


# =============================================================================
# SystemCollector Tests
# =============================================================================

class TestSystemCollector:
    """Tests for SystemCollector class."""

    def test_collector_initialization(self):
        """Test SystemCollector initializes correctly."""
        collector = SystemCollector()
        assert collector.events == []

    @patch("subprocess.run")
    def test_collect_journald_success(self, mock_run):
        """Test collecting from journald."""
        mock_run.return_value = MagicMock(
            stdout='{"__REALTIME_TIMESTAMP": "1737820800000000", "MESSAGE": "Test error"}\n',
            returncode=0,
        )
        collector = SystemCollector()
        events = collector._collect_journald(datetime.now() - timedelta(hours=1))
        # Should attempt to collect
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_collect_journald_empty(self, mock_run):
        """Test collecting from journald with no results."""
        mock_run.return_value = MagicMock(stdout="", returncode=0)
        collector = SystemCollector()
        events = collector._collect_journald(datetime.now() - timedelta(hours=1))
        assert events == []

    def test_collect_auth_log_missing_file(self):
        """Test collecting from auth.log when file doesn't exist."""
        collector = SystemCollector()
        with patch.object(Path, "exists", return_value=False):
            events = collector._collect_auth_log(datetime.now())
            assert events == []

    def test_collect_fail2ban_missing_file(self):
        """Test collecting from fail2ban when file doesn't exist."""
        collector = SystemCollector()
        events = collector._collect_fail2ban(datetime.now())
        # Should return empty if file doesn't exist or no permissions
        assert isinstance(events, list)


# =============================================================================
# AppCollector Tests
# =============================================================================

class TestAppCollector:
    """Tests for AppCollector class."""

    def test_collector_initialization(self):
        """Test AppCollector initializes correctly."""
        collector = AppCollector()
        assert collector.skippy_root == Path("/home/dave/skippy")

    def test_collector_custom_root(self):
        """Test AppCollector with custom SKIPPY_HOME."""
        with patch.dict("os.environ", {"SKIPPY_HOME": "/custom/path"}):
            collector = AppCollector()
            assert collector.skippy_root == Path("/custom/path")

    def test_collect_skippy_log_missing_file(self):
        """Test collecting skippy log when file doesn't exist."""
        collector = AppCollector()
        collector.skippy_root = Path("/nonexistent/path")
        events = collector._collect_skippy_log(datetime.now())
        assert events == []

    def test_collect_mcp_logs_missing_dir(self):
        """Test collecting MCP logs when directory doesn't exist."""
        collector = AppCollector()
        collector.skippy_root = Path("/nonexistent/path")
        events = collector._collect_mcp_logs(datetime.now())
        assert events == []

    def test_collect_wordpress_log_missing_file(self):
        """Test collecting WordPress log when file doesn't exist."""
        collector = AppCollector()
        collector.skippy_root = Path("/nonexistent/path")
        events = collector._collect_wordpress_log(datetime.now())
        assert events == []

    def test_collect_maintenance_logs_missing_file(self):
        """Test collecting maintenance logs when file doesn't exist."""
        collector = AppCollector()
        collector.skippy_root = Path("/nonexistent/path")
        events = collector._collect_maintenance_logs(datetime.now())
        assert events == []

    def test_collect_gmail_monitor_logs_missing_file(self):
        """Test collecting gmail monitor logs when file doesn't exist."""
        collector = AppCollector()
        collector.skippy_root = Path("/nonexistent/path")
        events = collector._collect_gmail_monitor_logs(datetime.now())
        assert events == []


# =============================================================================
# ClaudeCollector Tests
# =============================================================================

class TestClaudeCollector:
    """Tests for ClaudeCollector class."""

    def test_collector_initialization(self):
        """Test ClaudeCollector initializes correctly."""
        collector = ClaudeCollector()
        assert collector.claude_dir == Path.home() / ".claude"

    def test_collect_tool_logs_missing_file(self):
        """Test collecting tool logs when file doesn't exist."""
        collector = ClaudeCollector()
        collector.claude_dir = Path("/nonexistent/path")
        events = collector._collect_tool_logs(datetime.now())
        assert events == []

    def test_collect_blocked_logs_missing_file(self):
        """Test collecting blocked logs when file doesn't exist."""
        collector = ClaudeCollector()
        collector.claude_dir = Path("/nonexistent/path")
        events = collector._collect_blocked_logs(datetime.now())
        assert events == []

    def test_collect_session_logs_missing_file(self):
        """Test collecting session logs when file doesn't exist."""
        collector = ClaudeCollector()
        collector.claude_dir = Path("/nonexistent/path")
        events = collector._collect_session_logs(datetime.now())
        assert events == []

    def test_collect_email_logs_missing_file(self):
        """Test collecting email logs when file doesn't exist."""
        collector = ClaudeCollector()
        collector.claude_dir = Path("/nonexistent/path")
        events = collector._collect_email_logs(datetime.now())
        assert events == []

    def test_collect_learning_logs_missing_file(self):
        """Test collecting learning logs when file doesn't exist."""
        collector = ClaudeCollector()
        collector.claude_dir = Path("/nonexistent/path")
        events = collector._collect_learning_logs(datetime.now())
        # Returns empty list or list from actual file if it exists
        assert isinstance(events, list)


# =============================================================================
# PatternEngine Tests
# =============================================================================

class TestPatternEngine:
    """Tests for PatternEngine class."""

    def test_engine_initialization(self):
        """Test PatternEngine initializes correctly."""
        engine = PatternEngine()
        assert engine.patterns_file.name == "detected_patterns.json"

    def test_group_similar_messages(self):
        """Test message grouping by similarity."""
        engine = PatternEngine()
        events = [
            LogEvent(
                timestamp="2026-01-25T12:00:00",
                source="test",
                category="test",
                level="error",
                message="Error in file /path/to/file.py line 42",
            ),
            LogEvent(
                timestamp="2026-01-25T12:01:00",
                source="test",
                category="test",
                level="error",
                message="Error in file /path/to/other.py line 99",
            ),
        ]
        groups = engine._group_similar_messages(events)
        # Both should be grouped together (normalized paths and numbers)
        assert len(groups) == 1

    def test_group_different_messages(self):
        """Test that different messages are not grouped."""
        engine = PatternEngine()
        events = [
            LogEvent(
                timestamp="2026-01-25T12:00:00",
                source="test",
                category="test",
                level="error",
                message="Connection timeout",
            ),
            LogEvent(
                timestamp="2026-01-25T12:01:00",
                source="test",
                category="test",
                level="error",
                message="Authentication failed",
            ),
        ]
        groups = engine._group_similar_messages(events)
        assert len(groups) == 2

    def test_detect_recurring_errors_below_threshold(self):
        """Test that errors below threshold are not detected as patterns."""
        engine = PatternEngine()
        groups = {"test_message": [MagicMock(level="error", message="test")]}
        patterns = engine._detect_recurring_errors(groups)
        # Only 1 occurrence, needs 3+ to be detected
        assert len(patterns) == 0

    def test_detect_recurring_errors_above_threshold(self):
        """Test that errors at/above threshold are detected as patterns."""
        engine = PatternEngine()
        events = [
            MagicMock(
                level="error",
                message="Repeated error",
                source="test",
                category="test",
            )
            for _ in range(5)
        ]
        groups = {"repeated_error": events}
        patterns = engine._detect_recurring_errors(groups)
        assert len(patterns) == 1
        assert patterns[0].frequency == 5

    def test_analyze_empty_events(self):
        """Test analyzing empty event list."""
        engine = PatternEngine()
        with tempfile.TemporaryDirectory() as tmpdir:
            engine.patterns_file = Path(tmpdir) / "patterns.json"
            patterns = engine.analyze([])
            assert patterns == []

    def test_detect_temporal_patterns_empty(self):
        """Test temporal pattern detection with no events."""
        engine = PatternEngine()
        patterns = engine._detect_temporal_patterns([])
        assert patterns == []

    def test_detect_correlations_empty(self):
        """Test correlation detection with no events."""
        engine = PatternEngine()
        patterns = engine._detect_correlations([])
        assert patterns == []

    def test_detect_category_spikes_empty(self):
        """Test category spike detection with no events."""
        engine = PatternEngine()
        patterns = engine._detect_category_spikes([])
        assert patterns == []


# =============================================================================
# PreventionGenerator Tests
# =============================================================================

class TestPreventionGenerator:
    """Tests for PreventionGenerator class."""

    def test_generator_initialization(self):
        """Test PreventionGenerator initializes correctly."""
        generator = PreventionGenerator()
        assert generator.rules_file.name == "prevention_rules.json"
        assert generator.hooks_dir == Path.home() / ".claude" / "hooks"

    def test_generate_rules_empty_patterns(self):
        """Test generating rules from empty patterns list."""
        generator = PreventionGenerator()
        with tempfile.TemporaryDirectory() as tmpdir:
            generator.rules_file = Path(tmpdir) / "rules.json"
            rules = generator.generate_rules([])
            assert rules == []

    def test_generate_rules_non_preventable_patterns(self):
        """Test that non-preventable patterns don't generate rules."""
        generator = PreventionGenerator()
        patterns = [
            Pattern(
                id="pattern_001",
                name="Test pattern",
                description="Test",
                frequency=5,
                severity="medium",
                sources=["test"],
                example_messages=["test"],
                suggested_action="test",
                auto_preventable=False,
            )
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            generator.rules_file = Path(tmpdir) / "rules.json"
            rules = generator.generate_rules(patterns)
            assert rules == []

    def test_pattern_to_rule_email_empty(self):
        """Test converting email empty body pattern to rule."""
        generator = PreventionGenerator()
        pattern = Pattern(
            id="pattern_email",
            name="Empty email body",
            description="Emails sent with empty body",
            frequency=3,
            severity="high",
            sources=["claude"],
            example_messages=["Email sent with empty body"],
            suggested_action="Block empty emails",
            auto_preventable=True,
        )
        rule = generator._pattern_to_rule(pattern)
        assert rule is not None
        assert rule.action == "block"
        assert "email" in rule.name.lower()

    def test_pattern_to_rule_unknown_type(self):
        """Test converting unknown pattern type returns None."""
        generator = PreventionGenerator()
        pattern = Pattern(
            id="pattern_unknown",
            name="Unknown pattern type",
            description="Something unknown",
            frequency=3,
            severity="low",
            sources=["test"],
            example_messages=["unknown"],
            suggested_action="investigate",
            auto_preventable=True,
        )
        rule = generator._pattern_to_rule(pattern)
        # Unknown patterns should return None
        assert rule is None


# =============================================================================
# Brain Tests
# =============================================================================

class TestBrain:
    """Tests for Brain orchestration class."""

    def test_brain_initialization(self):
        """Test Brain initializes correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = Brain(data_dir=Path(tmpdir))
            assert brain.data_dir == Path(tmpdir)
            assert brain.events == []
            assert brain.last_ingest is None

    def test_brain_creates_data_dir(self):
        """Test Brain creates data directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_dir = Path(tmpdir) / "subdir" / "learning"
            brain = Brain(data_dir=data_dir)
            assert data_dir.exists()

    def test_brain_has_collectors(self):
        """Test Brain initializes all collectors."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = Brain(data_dir=Path(tmpdir))
            assert isinstance(brain.system_collector, SystemCollector)
            assert isinstance(brain.app_collector, AppCollector)
            assert isinstance(brain.claude_collector, ClaudeCollector)

    def test_brain_has_engines(self):
        """Test Brain initializes pattern and prevention engines."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = Brain(data_dir=Path(tmpdir))
            assert isinstance(brain.pattern_engine, PatternEngine)
            assert isinstance(brain.prevention_generator, PreventionGenerator)

    @patch.object(SystemCollector, "collect", return_value=[])
    @patch.object(AppCollector, "collect", return_value=[])
    @patch.object(ClaudeCollector, "collect", return_value=[])
    def test_ingest_all_empty(self, mock_claude, mock_app, mock_system):
        """Test ingesting with no events from any source."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = Brain(data_dir=Path(tmpdir))
            stats = brain.ingest_all()
            assert stats["total"] == 0
            assert stats["system"] == 0
            assert stats["app"] == 0
            assert stats["claude"] == 0

    @patch.object(SystemCollector, "collect")
    @patch.object(AppCollector, "collect", return_value=[])
    @patch.object(ClaudeCollector, "collect", return_value=[])
    def test_ingest_all_with_events(self, mock_claude, mock_app, mock_system):
        """Test ingesting with events from system collector."""
        mock_system.return_value = [
            LogEvent(
                timestamp="2026-01-25T12:00:00",
                source="system",
                category="journald",
                level="error",
                message="Test error",
            )
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = Brain(data_dir=Path(tmpdir))
            stats = brain.ingest_all()
            assert stats["system"] == 1
            assert stats["total"] == 1
            assert stats["errors"] == 1

    @patch.object(SystemCollector, "collect", side_effect=Exception("Test error"))
    @patch.object(AppCollector, "collect", return_value=[])
    @patch.object(ClaudeCollector, "collect", return_value=[])
    def test_ingest_all_handles_collector_error(self, mock_claude, mock_app, mock_system):
        """Test that ingest handles collector exceptions gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = Brain(data_dir=Path(tmpdir))
            stats = brain.ingest_all()
            assert "system_error" in stats
            assert stats["system"] == 0

    def test_detect_patterns_empty(self):
        """Test pattern detection with no events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = Brain(data_dir=Path(tmpdir))
            brain.pattern_engine.patterns_file = Path(tmpdir) / "patterns.json"
            patterns = brain.detect_patterns()
            assert patterns == []

    def test_generate_prevention_rules_empty(self):
        """Test prevention rule generation with no patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = Brain(data_dir=Path(tmpdir))
            brain.prevention_generator.rules_file = Path(tmpdir) / "rules.json"
            rules = brain.generate_prevention_rules([])
            assert rules == []

    def test_get_report(self):
        """Test getting brain report."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = Brain(data_dir=Path(tmpdir))
            report = brain.get_report()
            assert isinstance(report, dict)

    def test_get_actionable_insights_empty(self):
        """Test getting insights with no patterns."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = Brain(data_dir=Path(tmpdir))
            brain.pattern_engine.patterns_file = Path(tmpdir) / "patterns.json"
            insights = brain.get_actionable_insights()
            assert isinstance(insights, list)

    def test_save_and_load_state(self):
        """Test state persistence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = Brain(data_dir=Path(tmpdir))
            brain.last_ingest = datetime.now()
            brain._save_state()

            # Create new brain instance
            brain2 = Brain(data_dir=Path(tmpdir))
            assert brain2.last_ingest is not None

    def test_search_events_empty(self):
        """Test searching events when none exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = Brain(data_dir=Path(tmpdir))
            results = brain.search_events("test")
            assert results == []

    def test_search_events_with_match(self):
        """Test searching events with matching query."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = Brain(data_dir=Path(tmpdir))
            brain.events = [
                LogEvent(
                    timestamp="2026-01-25T12:00:00",
                    source="test",
                    category="test",
                    level="error",
                    message="Authentication failed for user admin",
                ),
                LogEvent(
                    timestamp="2026-01-25T12:01:00",
                    source="test",
                    category="test",
                    level="info",
                    message="Connection established",
                ),
            ]
            results = brain.search_events("Authentication")
            assert len(results) == 1
            assert "Authentication" in results[0].message

    def test_get_recent_errors(self):
        """Test getting only error events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = Brain(data_dir=Path(tmpdir))
            brain.events = [
                LogEvent(
                    timestamp="2026-01-25T12:00:00",
                    source="test",
                    category="test",
                    level="error",
                    message="Error message",
                ),
                LogEvent(
                    timestamp="2026-01-25T12:01:00",
                    source="test",
                    category="test",
                    level="info",
                    message="Info message",
                ),
                LogEvent(
                    timestamp="2026-01-25T12:02:00",
                    source="test",
                    category="test",
                    level="warning",
                    message="Warning message",
                ),
            ]
            errors = brain.get_recent_errors()
            assert len(errors) == 1
            assert errors[0].level == "error"


# =============================================================================
# Integration Tests
# =============================================================================

class TestBrainIntegration:
    """Integration tests for Brain module."""

    def test_full_cycle_empty(self):
        """Test running full brain cycle with no data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = Brain(data_dir=Path(tmpdir))
            brain.pattern_engine.patterns_file = Path(tmpdir) / "patterns.json"
            brain.prevention_generator.rules_file = Path(tmpdir) / "rules.json"

            # Mock collectors to return empty
            with patch.object(SystemCollector, "collect", return_value=[]):
                with patch.object(AppCollector, "collect", return_value=[]):
                    with patch.object(ClaudeCollector, "collect", return_value=[]):
                        stats = brain.ingest_all()
                        patterns = brain.detect_patterns()
                        rules = brain.generate_prevention_rules(patterns)

            assert stats["total"] == 0
            assert len(patterns) == 0
            assert len(rules) == 0

    def test_full_cycle_with_events(self):
        """Test running full brain cycle with mock events."""
        with tempfile.TemporaryDirectory() as tmpdir:
            brain = Brain(data_dir=Path(tmpdir))
            brain.pattern_engine.patterns_file = Path(tmpdir) / "patterns.json"
            brain.prevention_generator.rules_file = Path(tmpdir) / "rules.json"

            # Create mock events
            mock_events = [
                LogEvent(
                    timestamp="2026-01-25T12:00:00",
                    source="system",
                    category="journald",
                    level="error",
                    message="Service failed to start",
                )
                for _ in range(5)
            ]

            with patch.object(SystemCollector, "collect", return_value=mock_events):
                with patch.object(AppCollector, "collect", return_value=[]):
                    with patch.object(ClaudeCollector, "collect", return_value=[]):
                        stats = brain.ingest_all()
                        patterns = brain.detect_patterns()

            assert stats["total"] == 5
            assert stats["errors"] == 5
            # Should detect recurring error pattern
            assert len(patterns) >= 1

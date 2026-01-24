"""
Skippy Brain - Unified Log Aggregation & Learning System
=========================================================

Collects logs from all sources, detects patterns, and auto-generates
prevention rules.

Sources:
- System: syslog, journald, auth.log, fail2ban
- Application: MCP, WordPress, Skippy scripts, cron
- Claude: tool usage, sessions, permissions, hooks

Usage:
    from skippy_brain import Brain

    brain = Brain()
    brain.ingest_all()
    patterns = brain.detect_patterns()
    rules = brain.generate_prevention_rules()
"""

from .brain import Brain
from .collectors import SystemCollector, AppCollector, ClaudeCollector
from .patterns import PatternEngine
from .prevention import PreventionGenerator

__version__ = "1.0.0"
__all__ = ["Brain", "SystemCollector", "AppCollector", "ClaudeCollector",
           "PatternEngine", "PreventionGenerator"]

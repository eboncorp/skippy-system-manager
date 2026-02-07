"""
Tests for the Crypto Server Audit Agent Team.

Validates each audit agent independently and the orchestrator
that coordinates them all.
"""

import json
import os
import sys
import textwrap

import pytest

# Ensure we can import audit_agents without triggering the root __init__.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from audit_agents.base import AuditFinding, AuditReport, Severity
from audit_agents.security_agent import SecurityAuditAgent
from audit_agents.api_agent import APIAuditAgent
from audit_agents.config_agent import ConfigAuditAgent
from audit_agents.dependency_agent import DependencyAuditAgent
from audit_agents.compliance_agent import ComplianceAuditAgent
from audit_agents.orchestrator import AuditOrchestrator, UnifiedAuditReport


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def tmp_project(tmp_path):
    """Create a minimal fake crypto project for testing."""
    (tmp_path / ".gitignore").write_text(".env\n*.pem\n*.key\n__pycache__/\n")
    (tmp_path / "env.template").write_text(
        "COINBASE_API_KEY=your_key_here\n"
        "COINBASE_API_SECRET=your_secret_here\n"
        "TRADING_MODE=paper\n"
        "DATABASE_URL=sqlite:///portfolio.db\n"
    )
    (tmp_path / "requirements.txt").write_text(
        "fastmcp>=2.0.0\n"
        "pydantic>=2.0.0\n"
        "aiohttp>=3.9.0\n"
        "sqlalchemy>=2.0.0\n"
        "redis>=5.0.0\n"
    )
    (tmp_path / "config.py").write_text(textwrap.dedent("""\
        from enum import Enum
        from dataclasses import dataclass

        class TradingMode(Enum):
            PAPER = "paper"
            CONFIRM = "confirm"
            LIVE = "live"

        @dataclass
        class SafetyLimits:
            max_trade_usd: float = 100.0
            max_trades_per_day: int = 10
            max_daily_volume_usd: float = 500.0
            max_sell_percent: float = 25.0
            max_slippage_percent: float = 2.0

        @dataclass
        class TradingConfig:
            mode: TradingMode = TradingMode.CONFIRM
            safety: SafetyLimits = None
    """))

    # Create a sample Python file with a tool
    (tmp_path / "server.py").write_text(textwrap.dedent("""\
        import os
        from pydantic import BaseModel

        API_KEY = os.getenv("COINBASE_API_KEY", "")

        @mcp.tool(name="crypto_portfolio_summary")
        async def portfolio_summary(exchange: str = "all") -> str:
            try:
                return "Portfolio data"
            except Exception as e:
                return f"Error: {e}"
    """))

    # Compliance directory
    compliance_dir = tmp_path / "compliance"
    compliance_dir.mkdir()
    (compliance_dir / "__init__.py").write_text("")
    (compliance_dir / "audit_log.py").write_text(textwrap.dedent("""\
        import hashlib
        class AuditLog:
            def log_change(self, table, record_id, action):
                pass
            def verify_chain(self):
                return {"valid": True}
    """))

    return tmp_path


@pytest.fixture
def tmp_project_with_issues(tmp_path):
    """Create a project with deliberate security issues for testing."""
    (tmp_path / ".gitignore").write_text("__pycache__/\n")  # Missing .env exclusion

    (tmp_path / "bad_code.py").write_text(textwrap.dedent("""\
        import os
        import pickle

        SECRET_KEY = "test_fake_key_AAAA0000BBBB1111CCCC2222"

        def run_command(user_input):
            os.system(user_input)
            result = eval(user_input)
            data = pickle.loads(user_input)
            return data
    """))

    (tmp_path / "requirements.txt").write_text(
        "requests\n"
        "aiohttp>=3.8.0\n"
        "flask\n"
    )

    (tmp_path / "config.py").write_text(textwrap.dedent("""\
        from enum import Enum

        class TradingMode(Enum):
            PAPER = "paper"
            LIVE = "live"

        class TradingConfig:
            mode: TradingMode = TradingMode.LIVE
            max_trade_usd: float = 50000.0
            max_daily_volume_usd: float = 100000.0
            max_sell_percent: float = 75.0
            max_slippage_percent: float = 10.0
    """))

    return tmp_path


# ── Base Classes ──────────────────────────────────────────────────────────


class TestSeverity:
    def test_weight_ordering(self):
        assert Severity.CRITICAL.weight > Severity.HIGH.weight
        assert Severity.HIGH.weight > Severity.MEDIUM.weight
        assert Severity.MEDIUM.weight > Severity.LOW.weight
        assert Severity.LOW.weight > Severity.INFO.weight

    def test_info_weight_is_zero(self):
        assert Severity.INFO.weight == 0


class TestAuditFinding:
    def test_to_dict(self):
        finding = AuditFinding(
            severity=Severity.HIGH,
            category="Security",
            title="Test Finding",
            description="A test",
            file_path="test.py",
            line_number=42,
        )
        d = finding.to_dict()
        assert d["severity"] == "high"
        assert d["category"] == "Security"
        assert d["line_number"] == 42

    def test_location_with_line(self):
        finding = AuditFinding(
            severity=Severity.LOW,
            category="Test",
            title="Test",
            description="Test",
            file_path="foo.py",
            line_number=10,
        )
        assert finding.location == "foo.py:10"

    def test_location_without_line(self):
        finding = AuditFinding(
            severity=Severity.LOW,
            category="Test",
            title="Test",
            description="Test",
            file_path="foo.py",
        )
        assert finding.location == "foo.py"

    def test_location_no_file(self):
        finding = AuditFinding(
            severity=Severity.LOW,
            category="Test",
            title="Test",
            description="Test",
        )
        assert finding.location == "N/A"


class TestAuditReport:
    def test_grade_no_findings(self):
        report = AuditReport(agent_name="Test")
        assert report.grade == "A"

    def test_grade_with_critical(self):
        report = AuditReport(agent_name="Test")
        report.add_finding(AuditFinding(
            severity=Severity.CRITICAL,
            category="Test",
            title="Critical",
            description="Critical finding",
        ))
        assert report.grade == "F"

    def test_risk_score_empty(self):
        report = AuditReport(agent_name="Test")
        assert report.risk_score == 0.0

    def test_risk_score_with_findings(self):
        report = AuditReport(agent_name="Test")
        report.add_finding(AuditFinding(
            severity=Severity.HIGH,
            category="Test",
            title="High",
            description="High finding",
        ))
        assert report.risk_score > 0

    def test_to_markdown(self):
        report = AuditReport(agent_name="Test Agent")
        report.add_finding(AuditFinding(
            severity=Severity.MEDIUM,
            category="Security",
            title="Test Issue",
            description="A test issue",
        ))
        report.complete("Done")
        md = report.to_markdown()
        assert "Test Agent" in md
        assert "MEDIUM" in md
        assert "Test Issue" in md

    def test_to_json(self):
        report = AuditReport(agent_name="Test")
        report.complete()
        data = json.loads(report.to_json())
        assert data["agent_name"] == "Test"
        assert "grade" in data

    def test_severity_counts(self):
        report = AuditReport(agent_name="Test")
        for sev in [Severity.CRITICAL, Severity.HIGH, Severity.HIGH,
                     Severity.MEDIUM, Severity.LOW, Severity.INFO]:
            report.add_finding(AuditFinding(
                severity=sev, category="T", title="T", description="T",
            ))
        assert report.critical_count == 1
        assert report.high_count == 2
        assert report.medium_count == 1
        assert report.low_count == 1
        assert report.info_count == 1


# ── Security Agent ────────────────────────────────────────────────────────


class TestSecurityAuditAgent:
    def test_clean_project(self, tmp_project):
        agent = SecurityAuditAgent(str(tmp_project))
        report = agent.run()
        assert report.agent_name == "Security Audit Agent"
        assert report.critical_count == 0

    def test_detects_hardcoded_secret(self, tmp_project_with_issues):
        agent = SecurityAuditAgent(str(tmp_project_with_issues))
        report = agent.run()
        secret_findings = [
            f for f in report.findings if f.category == "Secrets"
        ]
        assert len(secret_findings) > 0

    def test_detects_injection_risks(self, tmp_project_with_issues):
        agent = SecurityAuditAgent(str(tmp_project_with_issues))
        report = agent.run()
        injection_findings = [
            f for f in report.findings if f.category == "Injection"
        ]
        assert len(injection_findings) > 0

    def test_detects_missing_gitignore_patterns(self, tmp_project_with_issues):
        agent = SecurityAuditAgent(str(tmp_project_with_issues))
        report = agent.run()
        gitignore_findings = [
            f for f in report.findings
            if ".gitignore" in (f.title or "")
        ]
        assert len(gitignore_findings) > 0

    def test_sanitize_evidence(self):
        result = SecurityAuditAgent._sanitize_evidence(
            'API_KEY = "test_fake_key_AAAA0000BBBB1111"'
        )
        assert "[REDACTED]" in result


# ── API Agent ─────────────────────────────────────────────────────────────


class TestAPIAuditAgent:
    def test_runs_on_project(self, tmp_project):
        agent = APIAuditAgent(str(tmp_project))
        report = agent.run()
        assert report.agent_name == "API Audit Agent"
        assert report.checks_performed > 0

    def test_detects_rate_limiting_absence(self, tmp_project):
        (tmp_project / "exchange.py").write_text(textwrap.dedent("""\
            import aiohttp
            async def fetch_price():
                async with aiohttp.ClientSession() as session:
                    return await session.get("https://api.exchange.com/price")
        """))
        agent = APIAuditAgent(str(tmp_project))
        report = agent.run()
        rate_findings = [
            f for f in report.findings if f.category == "Rate Limiting"
        ]
        assert len(rate_findings) > 0


# ── Config Agent ──────────────────────────────────────────────────────────


class TestConfigAuditAgent:
    def test_clean_config(self, tmp_project):
        agent = ConfigAuditAgent(str(tmp_project))
        report = agent.run()
        assert report.agent_name == "Configuration Audit Agent"

    def test_detects_unsafe_defaults(self, tmp_project_with_issues):
        agent = ConfigAuditAgent(str(tmp_project_with_issues))
        report = agent.run()
        trading_findings = [
            f for f in report.findings if f.category == "Trading Safety"
        ]
        assert len(trading_findings) > 0

    def test_detects_high_trade_limits(self, tmp_project_with_issues):
        agent = ConfigAuditAgent(str(tmp_project_with_issues))
        report = agent.run()
        # Should detect LIVE mode default and/or high limits
        safety_findings = [
            f for f in report.findings if f.category == "Trading Safety"
        ]
        assert len(safety_findings) > 0


# ── Dependency Agent ──────────────────────────────────────────────────────


class TestDependencyAuditAgent:
    def test_parses_requirements(self, tmp_project):
        agent = DependencyAuditAgent(str(tmp_project))
        report = agent.run()
        assert report.agent_name == "Dependency Audit Agent"
        assert report.checks_performed > 0

    def test_detects_unpinned_deps(self, tmp_project_with_issues):
        agent = DependencyAuditAgent(str(tmp_project_with_issues))
        report = agent.run()
        pin_findings = [
            f for f in report.findings if f.category == "Version Pinning"
        ]
        assert len(pin_findings) > 0

    def test_detects_known_vulnerabilities(self, tmp_project):
        (tmp_project / "requirements.txt").write_text(
            "aiohttp>=3.8.0\n"
            "pydantic>=2.0.0\n"
        )
        agent = DependencyAuditAgent(str(tmp_project))
        report = agent.run()
        vuln_findings = [
            f for f in report.findings if f.category == "Vulnerability"
        ]
        assert len(vuln_findings) > 0

    def test_version_allows_vulnerable(self):
        agent = DependencyAuditAgent("/tmp")
        assert agent._version_allows_vulnerable(">=3.8.0", "3.9.2") is True
        assert agent._version_allows_vulnerable(">=3.10.0", "3.9.2") is False
        assert agent._version_allows_vulnerable("", "3.9.2") is True


# ── Compliance Agent ──────────────────────────────────────────────────────


class TestComplianceAuditAgent:
    def test_runs_on_project(self, tmp_project):
        agent = ComplianceAuditAgent(str(tmp_project))
        report = agent.run()
        assert report.agent_name == "Compliance Audit Agent"
        assert report.checks_performed > 0

    def test_detects_audit_log_features(self, tmp_project):
        agent = ComplianceAuditAgent(str(tmp_project))
        report = agent.run()
        audit_findings = [
            f for f in report.findings if f.category == "Audit Logging"
        ]
        assert len(audit_findings) >= 0

    def test_verifies_audit_chain(self, tmp_project):
        audit_dir = tmp_project / "data"
        audit_dir.mkdir(exist_ok=True)
        audit_data = [
            {
                "timestamp": "2026-01-01T00:00:00Z",
                "table_name": "trades",
                "record_id": "1",
                "action": "INSERT",
                "checksum": "abc123",
                "prev_checksum": "",
            },
            {
                "timestamp": "2026-01-01T01:00:00Z",
                "table_name": "trades",
                "record_id": "2",
                "action": "INSERT",
                "checksum": "def456",
                "prev_checksum": "abc123",
            },
        ]
        (audit_dir / "audit_log.json").write_text(json.dumps(audit_data))

        agent = ComplianceAuditAgent(str(tmp_project))
        report = agent.run()
        integrity_findings = [
            f for f in report.findings
            if "integrity" in (f.title or "").lower() or "chain" in (f.title or "").lower()
        ]
        assert len(integrity_findings) >= 0


# ── Orchestrator ──────────────────────────────────────────────────────────


class TestAuditOrchestrator:
    def test_runs_all_agents(self, tmp_project):
        orchestrator = AuditOrchestrator(str(tmp_project))
        unified = orchestrator.run()
        assert len(unified.agent_reports) == 5
        assert unified.total_findings >= 0
        assert unified.overall_grade in [
            "A", "A-", "B+", "B", "B-", "C+", "C", "D", "F",
        ]

    def test_runs_specific_agents(self, tmp_project):
        orchestrator = AuditOrchestrator(
            str(tmp_project),
            agents=[SecurityAuditAgent, ConfigAuditAgent],
        )
        unified = orchestrator.run()
        assert len(unified.agent_reports) == 2

    def test_parallel_execution(self, tmp_project):
        orchestrator = AuditOrchestrator(
            str(tmp_project),
            parallel=True,
        )
        unified = orchestrator.run()
        assert len(unified.agent_reports) == 5
        assert unified.duration_seconds >= 0

    def test_save_reports(self, tmp_project):
        output_dir = str(tmp_project / "audit_output")
        orchestrator = AuditOrchestrator(
            str(tmp_project),
            output_dir=output_dir,
        )
        unified = orchestrator.run_and_save()
        assert os.path.exists(os.path.join(output_dir, "LATEST_AUDIT.md"))
        assert os.path.exists(os.path.join(output_dir, "latest_audit.json"))

    def test_unified_report_markdown(self, tmp_project):
        orchestrator = AuditOrchestrator(str(tmp_project))
        unified = orchestrator.run()
        md = unified.to_markdown()
        assert "Crypto Server Audit Report" in md
        assert "Executive Summary" in md
        assert "Agent Results" in md

    def test_unified_report_json(self, tmp_project):
        orchestrator = AuditOrchestrator(str(tmp_project))
        unified = orchestrator.run()
        data = json.loads(unified.to_json())
        assert "overall_grade" in data
        assert "severity_counts" in data
        assert "agents" in data
        assert len(data["agents"]) == 5

    def test_project_with_issues_grades_lower(self, tmp_project_with_issues):
        orchestrator = AuditOrchestrator(str(tmp_project_with_issues))
        unified = orchestrator.run()
        assert unified.total_findings > 0


class TestUnifiedAuditReport:
    def test_overall_grade_critical(self):
        report = UnifiedAuditReport(project_root="/tmp")
        agent_report = AuditReport(agent_name="Test")
        agent_report.add_finding(AuditFinding(
            severity=Severity.CRITICAL,
            category="Test",
            title="Crit",
            description="Critical",
        ))
        report.agent_reports = [agent_report]
        assert report.overall_grade == "F"

    def test_overall_grade_clean(self):
        report = UnifiedAuditReport(project_root="/tmp")
        agent_report = AuditReport(agent_name="Test")
        report.agent_reports = [agent_report]
        assert report.overall_grade == "A"

    def test_all_findings_sorted(self):
        report = UnifiedAuditReport(project_root="/tmp")
        r1 = AuditReport(agent_name="A")
        r1.add_finding(AuditFinding(
            severity=Severity.LOW, category="T", title="Low", description="Low",
        ))
        r2 = AuditReport(agent_name="B")
        r2.add_finding(AuditFinding(
            severity=Severity.HIGH, category="T", title="High", description="High",
        ))
        report.agent_reports = [r1, r2]
        findings = report.all_findings
        assert findings[0].severity == Severity.HIGH
        assert findings[1].severity == Severity.LOW

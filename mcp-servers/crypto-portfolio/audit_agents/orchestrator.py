"""
Audit Orchestrator
===================

Coordinates all audit agents, runs them in sequence or parallel,
and produces a unified report with overall risk assessment.
"""

import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type

from .base import AuditAgent, AuditFinding, AuditReport, Severity
from .security_agent import SecurityAuditAgent
from .api_agent import APIAuditAgent
from .config_agent import ConfigAuditAgent
from .dependency_agent import DependencyAuditAgent
from .compliance_agent import ComplianceAuditAgent

logger = logging.getLogger(__name__)


# Default agent registry
DEFAULT_AGENTS: List[Type[AuditAgent]] = [
    SecurityAuditAgent,
    APIAuditAgent,
    ConfigAuditAgent,
    DependencyAuditAgent,
    ComplianceAuditAgent,
]


@dataclass
class UnifiedAuditReport:
    """Aggregated report from all audit agents."""
    project_root: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    agent_reports: List[AuditReport] = field(default_factory=list)
    duration_seconds: float = 0.0

    @property
    def all_findings(self) -> List[AuditFinding]:
        findings = []
        for report in self.agent_reports:
            findings.extend(report.findings)
        return sorted(findings, key=lambda f: f.severity.weight, reverse=True)

    @property
    def total_findings(self) -> int:
        return sum(len(r.findings) for r in self.agent_reports)

    @property
    def critical_count(self) -> int:
        return sum(r.critical_count for r in self.agent_reports)

    @property
    def high_count(self) -> int:
        return sum(r.high_count for r in self.agent_reports)

    @property
    def medium_count(self) -> int:
        return sum(r.medium_count for r in self.agent_reports)

    @property
    def low_count(self) -> int:
        return sum(r.low_count for r in self.agent_reports)

    @property
    def info_count(self) -> int:
        return sum(r.info_count for r in self.agent_reports)

    @property
    def overall_grade(self) -> str:
        """Overall grade based on worst agent grade and total findings."""
        if self.critical_count > 0:
            return "F"
        if self.high_count > 3:
            return "D"
        if self.high_count > 0:
            return "C"
        if self.medium_count > 10:
            return "B-"
        if self.medium_count > 5:
            return "B"
        if self.medium_count > 0:
            return "B+"
        if self.low_count > 10:
            return "A-"
        return "A"

    @property
    def overall_risk_score(self) -> float:
        """Weighted average risk score across all agents."""
        if not self.agent_reports:
            return 0.0
        total = sum(r.risk_score for r in self.agent_reports)
        return total / len(self.agent_reports)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project": self.project_root,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_seconds": round(self.duration_seconds, 2),
            "overall_grade": self.overall_grade,
            "overall_risk_score": round(self.overall_risk_score, 1),
            "total_findings": self.total_findings,
            "severity_counts": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
                "info": self.info_count,
            },
            "agents": [r.to_dict() for r in self.agent_reports],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def to_markdown(self) -> str:
        lines = []
        lines.append("# Crypto Server Audit Report")
        lines.append(f"\n**Date:** {self.started_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append(f"**Duration:** {self.duration_seconds:.1f}s")
        lines.append(f"**Project:** {os.path.basename(self.project_root)}")
        lines.append(f"\n---")

        # Executive Summary
        lines.append("\n## Executive Summary")
        lines.append(f"\n| Metric | Value |")
        lines.append(f"|--------|-------|")
        lines.append(f"| Overall Grade | **{self.overall_grade}** |")
        lines.append(f"| Risk Score | {self.overall_risk_score:.1f}/100 |")
        lines.append(f"| Total Findings | {self.total_findings} |")
        lines.append(f"| Critical | {self.critical_count} |")
        lines.append(f"| High | {self.high_count} |")
        lines.append(f"| Medium | {self.medium_count} |")
        lines.append(f"| Low | {self.low_count} |")
        lines.append(f"| Info | {self.info_count} |")

        # Agent Summary Table
        lines.append("\n## Agent Results")
        lines.append("\n| Agent | Grade | Risk | Findings | Files |")
        lines.append("|-------|-------|------|----------|-------|")
        for report in self.agent_reports:
            lines.append(
                f"| {report.agent_name} | {report.grade} | "
                f"{report.risk_score:.1f} | {len(report.findings)} | "
                f"{report.files_scanned} |"
            )

        # Critical and High findings detail
        critical_high = [
            f for f in self.all_findings
            if f.severity in (Severity.CRITICAL, Severity.HIGH)
        ]
        if critical_high:
            lines.append("\n## Critical & High Priority Findings")
            for i, finding in enumerate(critical_high, 1):
                lines.append(f"\n### {i}. [{finding.severity.value.upper()}] {finding.title}")
                lines.append(f"**Category:** {finding.category}")
                lines.append(f"**Location:** {finding.location}")
                lines.append(f"\n{finding.description}")
                if finding.recommendation:
                    lines.append(f"\n**Recommendation:** {finding.recommendation}")
                if finding.cwe_id:
                    lines.append(f"**Reference:** {finding.cwe_id}")

        # Medium findings summary
        medium = [f for f in self.all_findings if f.severity == Severity.MEDIUM]
        if medium:
            lines.append("\n## Medium Priority Findings")
            lines.append("\n| # | Category | Title | Location |")
            lines.append("|---|----------|-------|----------|")
            for i, finding in enumerate(medium, 1):
                lines.append(f"| {i} | {finding.category} | {finding.title} | {finding.location} |")

        # Low findings count
        if self.low_count > 0:
            lines.append(f"\n## Low Priority Findings")
            lines.append(f"\n{self.low_count} low-priority findings identified. "
                          f"See JSON report for details.")

        # Individual agent reports
        lines.append("\n---")
        lines.append("\n## Detailed Agent Reports")
        for report in self.agent_reports:
            lines.append(f"\n{report.to_markdown()}")
            lines.append("\n---")

        # Recommendations
        lines.append("\n## Top Recommendations")
        recs = []
        for f in self.all_findings:
            if f.recommendation and f.severity.weight >= Severity.MEDIUM.weight:
                recs.append((f.severity, f.recommendation))
        seen = set()
        for i, (sev, rec) in enumerate(recs[:10], 1):
            if rec not in seen:
                lines.append(f"{i}. **[{sev.value.upper()}]** {rec}")
                seen.add(rec)

        return "\n".join(lines)


class AuditOrchestrator:
    """Coordinates and runs all audit agents."""

    def __init__(
        self,
        project_root: str,
        agents: Optional[List[Type[AuditAgent]]] = None,
        parallel: bool = False,
        output_dir: Optional[str] = None,
    ):
        self.project_root = os.path.abspath(project_root)
        self.agent_classes = agents or DEFAULT_AGENTS
        self.parallel = parallel
        self.output_dir = output_dir or os.path.join(
            self.project_root, "docs", "audit_reports"
        )

    def run(self) -> UnifiedAuditReport:
        """Execute all audit agents and produce unified report."""
        unified = UnifiedAuditReport(project_root=self.project_root)
        start_time = time.monotonic()

        logger.info(f"Starting crypto server audit with {len(self.agent_classes)} agents")
        logger.info(f"Project root: {self.project_root}")

        if self.parallel:
            unified.agent_reports = self._run_parallel()
        else:
            unified.agent_reports = self._run_sequential()

        unified.duration_seconds = time.monotonic() - start_time
        unified.completed_at = datetime.now(timezone.utc)

        logger.info(
            f"Audit complete: Grade {unified.overall_grade}, "
            f"{unified.total_findings} findings in {unified.duration_seconds:.1f}s"
        )

        return unified

    def run_and_save(self) -> UnifiedAuditReport:
        """Run audit and save reports to disk."""
        unified = self.run()
        self._save_reports(unified)
        return unified

    def _run_sequential(self) -> List[AuditReport]:
        """Run agents one at a time with shared file cache."""
        reports = []
        file_cache: dict = {}
        for agent_class in self.agent_classes:
            try:
                agent = agent_class(self.project_root, file_cache=file_cache)
                logger.info(f"Running {agent.name}...")
                report = agent.run()
                reports.append(report)
                logger.info(
                    f"  {agent.name}: {report.grade} "
                    f"({len(report.findings)} findings)"
                )
            except Exception as e:
                logger.error(f"Agent {agent_class.__name__} failed: {e}")
                error_report = AuditReport(agent_name=agent_class.__name__)
                error_report.errors.append(f"Agent crashed: {e}")
                error_report.complete("Agent execution failed")
                reports.append(error_report)
        return reports

    def _run_parallel(self) -> List[AuditReport]:
        """Run agents in parallel using thread pool."""
        reports = []
        with ThreadPoolExecutor(max_workers=len(self.agent_classes)) as executor:
            futures = {}
            for agent_class in self.agent_classes:
                agent = agent_class(self.project_root)
                future = executor.submit(agent.run)
                futures[future] = agent.name

            for future in as_completed(futures):
                agent_name = futures[future]
                try:
                    report = future.result(timeout=120)
                    reports.append(report)
                    logger.info(
                        f"  {agent_name}: {report.grade} "
                        f"({len(report.findings)} findings)"
                    )
                except Exception as e:
                    logger.error(f"Agent {agent_name} failed: {e}")
                    error_report = AuditReport(agent_name=agent_name)
                    error_report.errors.append(f"Agent crashed: {e}")
                    error_report.complete("Agent execution failed")
                    reports.append(error_report)

        return reports

    def _save_reports(self, unified: UnifiedAuditReport):
        """Save reports in multiple formats."""
        os.makedirs(self.output_dir, exist_ok=True)
        timestamp = unified.started_at.strftime("%Y%m%d_%H%M%S")

        # Save markdown report
        md_path = os.path.join(self.output_dir, f"audit_{timestamp}.md")
        with open(md_path, "w") as f:
            f.write(unified.to_markdown())
        logger.info(f"Markdown report saved to {md_path}")

        # Save JSON report
        json_path = os.path.join(self.output_dir, f"audit_{timestamp}.json")
        with open(json_path, "w") as f:
            f.write(unified.to_json())
        logger.info(f"JSON report saved to {json_path}")

        # Save latest symlink-style file
        latest_md = os.path.join(self.output_dir, "LATEST_AUDIT.md")
        with open(latest_md, "w") as f:
            f.write(unified.to_markdown())

        latest_json = os.path.join(self.output_dir, "latest_audit.json")
        with open(latest_json, "w") as f:
            f.write(unified.to_json())

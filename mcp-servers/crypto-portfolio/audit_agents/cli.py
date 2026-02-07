#!/usr/bin/env python3
"""
Audit Agent CLI
================

Command-line interface for running the audit agent team.

Usage:
    python -m audit_agents.cli                    # Run Python-focused audit
    python -m audit_agents.cli --full             # Run all agents (Bash + Infra)
    python -m audit_agents.cli --agents security  # Run specific agent
    python -m audit_agents.cli --parallel          # Run in parallel
    python -m audit_agents.cli --format json       # Output as JSON
    python -m audit_agents.cli --save              # Save report to disk
"""

import argparse
import logging
import os
import sys

from .base import Severity
from .orchestrator import AuditOrchestrator, PYTHON_AGENTS, ALL_AGENTS
from .security_agent import SecurityAuditAgent
from .api_agent import APIAuditAgent
from .config_agent import ConfigAuditAgent
from .dependency_agent import DependencyAuditAgent
from .compliance_agent import ComplianceAuditAgent
from .bash_agent import BashAuditAgent
from .infrastructure_agent import InfrastructureAuditAgent

AGENT_MAP = {
    "security": SecurityAuditAgent,
    "api": APIAuditAgent,
    "config": ConfigAuditAgent,
    "dependency": DependencyAuditAgent,
    "compliance": ComplianceAuditAgent,
    "bash": BashAuditAgent,
    "infrastructure": InfrastructureAuditAgent,
}


def main():
    parser = argparse.ArgumentParser(
        description="Audit Agent Team",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                              Run Python-focused audit
  %(prog)s --full                       Run ALL agents (Bash + Infrastructure)
  %(prog)s --full -p /path/to/repo      Audit a different project
  %(prog)s --agents security bash       Run security and bash audits only
  %(prog)s --parallel --save            Run all in parallel, save reports
  %(prog)s --format json                Output JSON report
  %(prog)s --min-severity medium        Only show medium+ findings
        """,
    )
    parser.add_argument(
        "--project-root", "-p",
        default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        help="Project root directory (default: crypto-portfolio/)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Run all agents including Bash and Infrastructure",
    )
    parser.add_argument(
        "--agents", "-a",
        nargs="+",
        choices=list(AGENT_MAP.keys()),
        help="Specific agents to run (default: all python agents, or all with --full)",
    )
    parser.add_argument(
        "--parallel",
        action="store_true",
        help="Run agents in parallel",
    )
    parser.add_argument(
        "--format", "-f",
        choices=["markdown", "json", "summary"],
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--save", "-s",
        action="store_true",
        help="Save reports to docs/audit_reports/",
    )
    parser.add_argument(
        "--min-severity",
        choices=["critical", "high", "medium", "low", "info"],
        default="info",
        help="Minimum severity to display (default: info)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose logging output",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # Select agents
    if args.agents:
        agent_classes = [AGENT_MAP[name] for name in args.agents]
    elif args.full:
        agent_classes = ALL_AGENTS
    else:
        agent_classes = PYTHON_AGENTS

    # Run orchestrator
    orchestrator = AuditOrchestrator(
        project_root=args.project_root,
        agents=agent_classes,
        parallel=args.parallel,
    )

    if args.save:
        unified = orchestrator.run_and_save()
    else:
        unified = orchestrator.run()

    # Filter findings by minimum severity
    min_sev = Severity(args.min_severity)
    min_weight = min_sev.weight
    for report in unified.agent_reports:
        report.findings = [
            f for f in report.findings if f.severity.weight >= min_weight
        ]

    # Output
    if args.format == "json":
        print(unified.to_json())
    elif args.format == "summary":
        _print_summary(unified)
    else:
        print(unified.to_markdown())

    # Exit code based on findings
    if unified.critical_count > 0:
        sys.exit(2)
    elif unified.high_count > 0:
        sys.exit(1)
    sys.exit(0)


def _print_summary(unified):
    """Print a concise summary."""
    project_name = os.path.basename(unified.project_root)
    print(f"\n{'=' * 60}")
    print(f"  AUDIT SUMMARY: {project_name}")
    print(f"{'=' * 60}")
    print(f"  Overall Grade:  {unified.overall_grade}")
    print(f"  Risk Score:     {unified.overall_risk_score:.1f}/100")
    print(f"  Duration:       {unified.duration_seconds:.1f}s")
    print(f"  Total Findings: {unified.total_findings}")
    print(f"")
    print(f"  Critical: {unified.critical_count}")
    print(f"  High:     {unified.high_count}")
    print(f"  Medium:   {unified.medium_count}")
    print(f"  Low:      {unified.low_count}")
    print(f"  Info:     {unified.info_count}")
    print(f"")
    print(f"  Agent Grades:")
    for report in unified.agent_reports:
        print(f"    {report.agent_name:30s} {report.grade:4s} ({len(report.findings)} findings)")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()

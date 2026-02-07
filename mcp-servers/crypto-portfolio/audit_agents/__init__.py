"""
Audit Agent Team
==================

A modular audit framework for Python/Bash projects.
Each agent specializes in a different audit domain:

- SecurityAuditAgent: Secrets, injection, auth, crypto vulnerabilities
- APIAuditAgent: MCP tool validation, input handling, error responses
- ConfigAuditAgent: Configuration safety, defaults, environment handling
- DependencyAuditAgent: Vulnerable packages, outdated deps, licenses
- ComplianceAuditAgent: Audit log integrity, tax compliance, data retention
- BashAuditAgent: Shell script security (eval, curl|bash, rm -rf, set -e)
- InfrastructureAuditAgent: Docker, CI/CD, SSH keys, .gitignore, repo hygiene

The AuditOrchestrator coordinates all agents and produces unified reports.
"""

from .base import AuditAgent, AuditFinding, AuditReport, Severity
from .security_agent import SecurityAuditAgent
from .api_agent import APIAuditAgent
from .config_agent import ConfigAuditAgent
from .dependency_agent import DependencyAuditAgent
from .compliance_agent import ComplianceAuditAgent
from .bash_agent import BashAuditAgent
from .infrastructure_agent import InfrastructureAuditAgent
from .orchestrator import AuditOrchestrator

__all__ = [
    "AuditAgent",
    "AuditFinding",
    "AuditReport",
    "Severity",
    "SecurityAuditAgent",
    "APIAuditAgent",
    "ConfigAuditAgent",
    "DependencyAuditAgent",
    "ComplianceAuditAgent",
    "BashAuditAgent",
    "InfrastructureAuditAgent",
    "AuditOrchestrator",
]

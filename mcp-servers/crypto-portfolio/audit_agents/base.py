"""
Base classes for the audit agent framework.

Defines the common data structures (AuditFinding, AuditReport)
and the abstract AuditAgent interface that all specialized agents implement.
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Severity(Enum):
    """Finding severity levels aligned with CVSS qualitative ratings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

    @property
    def weight(self) -> int:
        """Numeric weight for scoring."""
        return {
            Severity.CRITICAL: 10,
            Severity.HIGH: 7,
            Severity.MEDIUM: 4,
            Severity.LOW: 2,
            Severity.INFO: 0,
        }[self]


@dataclass
class AuditFinding:
    """A single audit finding."""
    severity: Severity
    category: str
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    recommendation: str = ""
    cwe_id: Optional[str] = None
    evidence: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["severity"] = self.severity.value
        return d

    @property
    def location(self) -> str:
        if self.file_path and self.line_number:
            return f"{self.file_path}:{self.line_number}"
        return self.file_path or "N/A"


@dataclass
class AuditReport:
    """Report from a single audit agent."""
    agent_name: str
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    findings: List[AuditFinding] = field(default_factory=list)
    summary: str = ""
    files_scanned: int = 0
    checks_performed: int = 0
    errors: List[str] = field(default_factory=list)

    def add_finding(self, finding: AuditFinding):
        self.findings.append(finding)

    def complete(self, summary: str = ""):
        self.completed_at = datetime.now(timezone.utc)
        if summary:
            self.summary = summary

    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.HIGH)

    @property
    def medium_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.MEDIUM)

    @property
    def low_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.LOW)

    @property
    def info_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == Severity.INFO)

    @property
    def risk_score(self) -> float:
        """Weighted risk score (0-100). Higher is worse."""
        if not self.findings:
            return 0.0
        total_weight = sum(f.severity.weight for f in self.findings)
        max_possible = len(self.findings) * Severity.CRITICAL.weight
        return min(100.0, (total_weight / max(max_possible, 1)) * 100)

    @property
    def grade(self) -> str:
        """Letter grade based on risk score."""
        score = self.risk_score
        if self.critical_count > 0:
            return "F"
        if score <= 5:
            return "A"
        if score <= 15:
            return "A-"
        if score <= 25:
            return "B+"
        if score <= 35:
            return "B"
        if score <= 45:
            return "B-"
        if score <= 55:
            return "C+"
        if score <= 65:
            return "C"
        return "D"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "grade": self.grade,
            "risk_score": round(self.risk_score, 1),
            "counts": {
                "critical": self.critical_count,
                "high": self.high_count,
                "medium": self.medium_count,
                "low": self.low_count,
                "info": self.info_count,
                "total": len(self.findings),
            },
            "files_scanned": self.files_scanned,
            "checks_performed": self.checks_performed,
            "findings": [f.to_dict() for f in self.findings],
            "summary": self.summary,
            "errors": self.errors,
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    def to_markdown(self) -> str:
        lines = []
        lines.append(f"## {self.agent_name}")
        lines.append(f"**Grade:** {self.grade} | **Risk Score:** {self.risk_score:.1f}/100")
        lines.append(f"**Files Scanned:** {self.files_scanned} | "
                      f"**Checks:** {self.checks_performed}")
        lines.append(f"**Findings:** {self.critical_count} Critical, "
                      f"{self.high_count} High, {self.medium_count} Medium, "
                      f"{self.low_count} Low, {self.info_count} Info")

        if self.summary:
            lines.append(f"\n{self.summary}")

        if self.findings:
            lines.append("\n| Severity | Category | Title | Location |")
            lines.append("|----------|----------|-------|----------|")
            for f in sorted(self.findings, key=lambda x: x.severity.weight, reverse=True):
                loc = f.location
                lines.append(f"| {f.severity.value.upper()} | {f.category} | "
                             f"{f.title} | {loc} |")

        if self.errors:
            lines.append("\n**Errors during audit:**")
            for e in self.errors:
                lines.append(f"- {e}")

        return "\n".join(lines)


class AuditAgent(ABC):
    """Abstract base class for all audit agents."""

    def __init__(self, project_root: str, file_cache: Optional[Dict[str, str]] = None):
        self.project_root = project_root
        self.report = AuditReport(agent_name=self.name)
        self._file_cache = file_cache if file_cache is not None else {}

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable agent name."""
        ...

    @property
    @abstractmethod
    def description(self) -> str:
        """What this agent audits."""
        ...

    @abstractmethod
    def run(self) -> AuditReport:
        """Execute the audit and return a report."""
        ...

    def _find_python_files(self) -> List[str]:
        """Find all Python files in the project."""
        import glob
        return sorted(glob.glob(f"{self.project_root}/**/*.py", recursive=True))

    def _read_file(self, path: str) -> str:
        """Read a file safely, using shared cache if available."""
        if path in self._file_cache:
            return self._file_cache[path]
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            self._file_cache[path] = content
            return content
        except OSError as e:
            self.report.errors.append(f"Cannot read {path}: {e}")
            return ""

"""
Bash Script Audit Agent
========================

Scans shell scripts for security and reliability issues:
- Dangerous command patterns (curl|bash, rm -rf, eval)
- Missing safety flags (set -euo pipefail)
- Unquoted variable expansions
- Overly permissive file permissions
- Hardcoded credentials and paths
- Unsafe temporary file handling
"""

import os
import re
from typing import Dict, List, Optional

from .base import AuditAgent, AuditFinding, AuditReport, Severity


class BashAuditAgent(AuditAgent):
    """Scans shell scripts for security and reliability issues."""

    @property
    def name(self) -> str:
        return "Bash Audit Agent"

    @property
    def description(self) -> str:
        return "Scans shell scripts for dangerous patterns, missing safety flags, and credential leaks"

    # Directories to skip
    SKIP_DIRS = {
        "audit_agents", "__pycache__", ".git", "node_modules",
        ".venv", "venv", ".archived_broken",
    }

    # Dangerous command patterns: (regex, title, severity, CWE, recommendation)
    DANGEROUS_PATTERNS = [
        (
            r'curl\s+.*\|\s*(?:sudo\s+)?(?:ba)?sh',
            "Pipe to shell (curl|bash)",
            Severity.HIGH,
            "CWE-94",
            "Download script first, inspect it, verify checksum, then execute",
        ),
        (
            r'wget\s+.*\|\s*(?:sudo\s+)?(?:ba)?sh',
            "Pipe to shell (wget|bash)",
            Severity.HIGH,
            "CWE-94",
            "Download script first, inspect it, verify checksum, then execute",
        ),
        (
            r'\beval\s+"?\$',
            "eval with variable expansion",
            Severity.HIGH,
            "CWE-78",
            "Avoid eval; use arrays for dynamic commands",
        ),
        (
            r'\beval\s+["\']',
            "eval with string argument",
            Severity.MEDIUM,
            "CWE-78",
            "Avoid eval; restructure logic to not need it",
        ),
        (
            r'chmod\s+777\b',
            "chmod 777 (world-writable)",
            Severity.HIGH,
            "CWE-732",
            "Use least-privilege permissions (e.g., 755 for dirs, 644 for files)",
        ),
        (
            r'chmod\s+666\b',
            "chmod 666 (world-writable file)",
            Severity.MEDIUM,
            "CWE-732",
            "Use 644 or more restrictive permissions",
        ),
    ]

    # rm -rf patterns that need variable validation
    RM_RF_PATTERN = re.compile(r'rm\s+-[a-zA-Z]*r[a-zA-Z]*f|rm\s+-[a-zA-Z]*f[a-zA-Z]*r')

    # Credential patterns in shell scripts
    CREDENTIAL_PATTERNS = [
        (r'(?:password|passwd|pwd)\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded password in shell script"),
        (r'(?:api_key|apikey|API_KEY)\s*=\s*["\'][a-zA-Z0-9]{16,}["\']', "Hardcoded API key in shell script"),
        (r'(?:secret|SECRET)\s*=\s*["\'][^"\']{16,}["\']', "Hardcoded secret in shell script"),
        (r'-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----', "Embedded private key"),
    ]

    def run(self) -> AuditReport:
        bash_files = self._find_bash_files()
        bash_files = [f for f in bash_files if not self._is_excluded(f)]
        self.report.files_scanned = len(bash_files)

        for filepath in bash_files:
            content = self._read_file(filepath)
            if not content:
                continue

            rel_path = os.path.relpath(filepath, self.project_root)
            lines = content.split("\n")

            self._check_safety_flags(rel_path, content, lines)
            self._check_dangerous_patterns(rel_path, lines)
            self._check_rm_rf(rel_path, lines)
            self._check_credentials(rel_path, lines)
            self._check_unquoted_vars(rel_path, lines)
            self._check_temp_files(rel_path, content, lines)

        self.report.complete(
            f"Scanned {self.report.files_scanned} shell scripts with "
            f"{self.report.checks_performed} checks."
        )
        return self.report

    def _find_bash_files(self) -> List[str]:
        """Find all shell script files in the project."""
        import glob
        results = []
        for pattern in ("**/*.sh", "**/*.bash"):
            results.extend(glob.glob(
                os.path.join(self.project_root, pattern), recursive=True
            ))
        # Also check files in bin/ that might not have extensions
        bin_dir = os.path.join(self.project_root, "bin")
        if os.path.isdir(bin_dir):
            for entry in os.listdir(bin_dir):
                path = os.path.join(bin_dir, entry)
                if os.path.isfile(path) and not entry.endswith((".py", ".pyc")):
                    try:
                        with open(path, "r", encoding="utf-8", errors="replace") as f:
                            first_line = f.readline()
                        if first_line.startswith("#!") and "sh" in first_line:
                            results.append(path)
                    except OSError:
                        pass
        return sorted(set(results))

    def _is_excluded(self, filepath: str) -> bool:
        rel = os.path.relpath(filepath, self.project_root)
        parts = rel.split(os.sep)
        return any(d in self.SKIP_DIRS for d in parts)

    def _is_comment(self, line: str) -> bool:
        stripped = line.strip()
        return stripped.startswith("#") and not stripped.startswith("#!")

    def _check_safety_flags(self, filepath: str, content: str, lines: List[str]):
        """Check for set -euo pipefail or equivalent."""
        self.report.checks_performed += 1
        # Only check files that look like real scripts (have shebang)
        if not lines or not lines[0].startswith("#!"):
            return
        # Skip very short scripts (< 10 lines)
        real_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
        if len(real_lines) < 10:
            return

        # Only check non-comment lines for set -e
        code_content = "\n".join(real_lines)
        has_set_e = bool(re.search(r'\bset\s+-[a-zA-Z]*e', code_content))
        has_set_u = bool(re.search(r'\bset\s+-[a-zA-Z]*u', code_content))

        if not has_set_e:
            self.report.add_finding(AuditFinding(
                severity=Severity.LOW,
                category="Shell Safety",
                title="Missing 'set -e' (exit on error)",
                description="Script does not exit on command failure",
                file_path=filepath,
                recommendation="Add 'set -euo pipefail' near the top of the script",
                cwe_id="CWE-754",
            ))

    def _check_dangerous_patterns(self, filepath: str, lines: List[str]):
        """Check for dangerous command patterns."""
        self.report.checks_performed += 1
        for i, line in enumerate(lines, 1):
            if self._is_comment(line):
                continue
            for pattern, title, severity, cwe, recommendation in self.DANGEROUS_PATTERNS:
                if re.search(pattern, line):
                    self.report.add_finding(AuditFinding(
                        severity=severity,
                        category="Dangerous Command",
                        title=title,
                        description=f"Potentially dangerous command pattern detected",
                        file_path=filepath,
                        line_number=i,
                        recommendation=recommendation,
                        cwe_id=cwe,
                        evidence=line.strip()[:120],
                    ))

    def _check_rm_rf(self, filepath: str, lines: List[str]):
        """Check rm -rf usage for variable safety."""
        self.report.checks_performed += 1
        for i, line in enumerate(lines, 1):
            if self._is_comment(line):
                continue
            if not self.RM_RF_PATTERN.search(line):
                continue

            # Check if it uses an unvalidated variable
            if re.search(r'rm\s+-[rf]+\s+"\$\{?\w+\}?"', line) or \
               re.search(r'rm\s+-[rf]+\s+\$\{?\w+\}?', line):
                # Look backwards for a guard (variable check)
                context = "\n".join(lines[max(0, i - 5):i])
                has_guard = bool(re.search(
                    r'(?:\[\s*-[ndz]\s+|if\s+\[\s*.*\$)', context
                ))
                if not has_guard:
                    self.report.add_finding(AuditFinding(
                        severity=Severity.HIGH,
                        category="Dangerous Command",
                        title="rm -rf with unguarded variable",
                        description="rm -rf uses a variable without checking it is non-empty",
                        file_path=filepath,
                        line_number=i,
                        recommendation='Guard with: [[ -n "$var" ]] or use ${var:?} expansion',
                        cwe_id="CWE-20",
                        evidence=line.strip()[:120],
                    ))
            elif re.search(r'rm\s+-[rf]+\s+/', line):
                # Hardcoded path starting with / — less risky but check for /
                if re.search(r'rm\s+-[rf]+\s+/\s', line) or re.search(r'rm\s+-[rf]+\s+/\*', line):
                    self.report.add_finding(AuditFinding(
                        severity=Severity.CRITICAL,
                        category="Dangerous Command",
                        title="rm -rf targeting root filesystem",
                        description="Recursive delete targeting / or /*",
                        file_path=filepath,
                        line_number=i,
                        recommendation="Never use rm -rf on root paths",
                        cwe_id="CWE-20",
                        evidence=line.strip()[:120],
                    ))

    def _check_credentials(self, filepath: str, lines: List[str]):
        """Check for hardcoded credentials."""
        self.report.checks_performed += 1
        for i, line in enumerate(lines, 1):
            if self._is_comment(line):
                continue
            for pattern, title in self.CREDENTIAL_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    # Exclude safe patterns
                    if any(safe in line for safe in [
                        "your_", "<", "xxx", "placeholder", "change_me",
                        "example", "...", "${", "$(",
                    ]):
                        continue
                    self.report.add_finding(AuditFinding(
                        severity=Severity.HIGH,
                        category="Secrets",
                        title=title,
                        description="Potential hardcoded credential in shell script",
                        file_path=filepath,
                        line_number=i,
                        recommendation="Use environment variables or a secrets manager",
                        cwe_id="CWE-798",
                        evidence=self._sanitize_evidence(line.strip()),
                    ))

    def _check_unquoted_vars(self, filepath: str, lines: List[str]):
        """Check for unquoted variables in dangerous contexts."""
        self.report.checks_performed += 1
        for i, line in enumerate(lines, 1):
            if self._is_comment(line):
                continue
            # Unquoted variable in [ ] test (word splitting risk)
            if re.search(r'\[\s+\$\w+\s+[=!-]', line) and '[[' not in line:
                self.report.add_finding(AuditFinding(
                    severity=Severity.LOW,
                    category="Shell Safety",
                    title="Unquoted variable in test expression",
                    description="Unquoted variable in [ ] can cause word splitting",
                    file_path=filepath,
                    line_number=i,
                    recommendation='Quote variables: [ "$var" = ... ] or use [[ ]]',
                    cwe_id="CWE-78",
                    evidence=line.strip()[:120],
                ))

    def _check_temp_files(self, filepath: str, content: str, lines: List[str]):
        """Check for unsafe temp file creation."""
        self.report.checks_performed += 1
        if "mktemp" in content:
            return  # Uses mktemp — safe
        for i, line in enumerate(lines, 1):
            if self._is_comment(line):
                continue
            if re.search(r'/tmp/[a-zA-Z_]+\b', line):
                # Using predictable /tmp path
                if any(cmd in line for cmd in [">", ">>", "tee", "mv", "cp"]):
                    self.report.add_finding(AuditFinding(
                        severity=Severity.LOW,
                        category="Temp Files",
                        title="Predictable temp file path",
                        description="Using fixed /tmp path instead of mktemp",
                        file_path=filepath,
                        line_number=i,
                        recommendation="Use mktemp for safe temporary files",
                        cwe_id="CWE-377",
                        evidence=line.strip()[:120],
                    ))
                    break  # One finding per file is enough

    @staticmethod
    def _sanitize_evidence(line: str) -> str:
        """Redact potential secrets from evidence."""
        return re.sub(
            r'(["\'])[a-zA-Z0-9+/=_\-]{16,}(["\'])',
            r'\1[REDACTED]\2',
            line
        )[:150]

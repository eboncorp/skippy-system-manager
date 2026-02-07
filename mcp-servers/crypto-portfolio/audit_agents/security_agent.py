"""
Security Audit Agent
=====================

Scans for security vulnerabilities in the crypto server codebase:
- Hardcoded secrets and API keys
- Injection vulnerabilities (SQL, command, path traversal)
- Unsafe deserialization
- Weak cryptographic practices
- Authentication and authorization issues
- Sensitive data exposure
- HMAC timing attacks
- Missing HTTP timeouts
"""

import os
import re
from typing import List

from .base import AuditAgent, AuditFinding, AuditReport, Severity


class SecurityAuditAgent(AuditAgent):
    """Scans crypto server code for security vulnerabilities."""

    @property
    def name(self) -> str:
        return "Security Audit Agent"

    @property
    def description(self) -> str:
        return "Scans for hardcoded secrets, injection flaws, unsafe crypto, and auth issues"

    # Patterns that indicate hardcoded secrets
    SECRET_PATTERNS = [
        (r'(?:api[_-]?key|apikey)\s*=\s*["\'][a-zA-Z0-9]{16,}["\']', "Hardcoded API key"),
        (r'(?:secret|password|passwd|pwd)\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded secret/password"),
        (r'(?:token)\s*=\s*["\'][a-zA-Z0-9_\-]{20,}["\']', "Hardcoded token"),
        (r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----', "Embedded private key"),
        (r'(?:sk|pk)[-_][a-zA-Z0-9]{20,}', "Potential crypto private/secret key"),
        (r'0x[a-fA-F0-9]{64}', "Potential private key hex (64 chars)"),
    ]

    # Patterns for injection risks -- use \b word boundaries to avoid partial matches
    INJECTION_PATTERNS = [
        (r'\bos\.system\s*\(', "os.system() call - command injection risk", "CWE-78"),
        (r'subprocess\.(?:call|run|Popen)\s*\([^)]*shell\s*=\s*True',
         "subprocess with shell=True - command injection risk", "CWE-78"),
        (r'(?<![a-zA-Z])\beval\s*\(', "eval() call - code injection risk", "CWE-94"),
        (r'(?<![a-zA-Z])\bexec\s*\(', "exec() call - code injection risk", "CWE-94"),
        (r'\b__import__\s*\(', "Dynamic import - code injection risk", "CWE-94"),
        (r'\bpickle\.loads?\s*\(', "pickle deserialization - unsafe", "CWE-502"),
        (r'yaml\.load\s*\([^)]*\)\s*$', "yaml.load without safe Loader", "CWE-502"),
    ]

    # Path traversal patterns
    PATH_TRAVERSAL_PATTERNS = [
        (r'os\.path\.join\s*\([^)]*request', "User input in file path", "CWE-22"),
    ]

    # Directories to skip during scanning (audit framework itself, tests)
    SKIP_DIRS = {"audit_agents", "__pycache__", ".git", "node_modules"}

    def run(self) -> AuditReport:
        py_files = self._find_python_files()
        # Exclude our own audit code and test fixtures
        py_files = [f for f in py_files if not self._is_excluded(f)]
        self.report.files_scanned = len(py_files)

        for filepath in py_files:
            content = self._read_file(filepath)
            if not content:
                continue

            rel_path = os.path.relpath(filepath, self.project_root)
            lines = content.split("\n")

            self._check_hardcoded_secrets(rel_path, lines)
            self._check_injection_risks(rel_path, lines)
            self._check_path_traversal(rel_path, lines)
            self._check_unsafe_crypto(rel_path, content, lines)
            self._check_error_handling(rel_path, lines)
            self._check_authentication(rel_path, content, lines)
            self._check_sensitive_data_logging(rel_path, lines)
            self._check_hmac_timing(rel_path, content, lines)
            self._check_http_timeouts(rel_path, content, lines)

        self._check_gitignore()
        self._check_env_template()

        self.report.complete(
            f"Scanned {self.report.files_scanned} files with "
            f"{self.report.checks_performed} checks."
        )
        return self.report

    def _is_excluded(self, filepath: str) -> bool:
        """Exclude audit framework and test files from scanning."""
        rel = os.path.relpath(filepath, self.project_root)
        parts = rel.split(os.sep)
        return any(d in self.SKIP_DIRS for d in parts)

    def _is_safe_context(self, filepath: str, line: str) -> bool:
        """Check if a match is in a safe context (test, comment, etc.)."""
        basename = os.path.basename(filepath)
        if any(ctx in basename for ctx in ["test_", "conftest", "mock", "example"]):
            return True
        stripped = line.strip()
        return stripped.startswith(("#", "//", '"""', "'''"))

    def _is_in_string_or_comment(self, line: str) -> bool:
        """Check if the code-like pattern is actually inside a string or comment."""
        stripped = line.strip()
        # Lines that are pure comments
        if stripped.startswith("#"):
            return True
        # Lines that are string definitions (regex patterns, docstrings, etc.)
        if stripped.startswith(('r"', "r'", 'r"""', "r'''", "(r'")):
            return True
        return False

    def _check_hardcoded_secrets(self, filepath: str, lines: List[str]):
        self.report.checks_performed += 1
        for i, line in enumerate(lines, 1):
            if self._is_safe_context(filepath, line):
                continue
            for pattern, desc in self.SECRET_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    # Exclude known safe patterns: env lookups, defaults
                    if any(safe in line for safe in [
                        "os.getenv", "os.environ", "getenv(",
                        '""', "''", "None", "...", "<", "test_", "example",
                    ]):
                        continue
                    self.report.add_finding(AuditFinding(
                        severity=Severity.CRITICAL,
                        category="Secrets",
                        title=desc,
                        description="Potential hardcoded credential detected",
                        file_path=filepath,
                        line_number=i,
                        recommendation="Move to environment variable or secrets manager",
                        cwe_id="CWE-798",
                        evidence=self._sanitize_evidence(line.strip()),
                    ))

    def _check_injection_risks(self, filepath: str, lines: List[str]):
        self.report.checks_performed += 1
        for i, line in enumerate(lines, 1):
            if self._is_in_string_or_comment(line):
                continue
            for pattern, desc, cwe in self.INJECTION_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    sev = Severity.HIGH if "eval" in desc or "exec" in desc else Severity.MEDIUM
                    self.report.add_finding(AuditFinding(
                        severity=sev,
                        category="Injection",
                        title=desc,
                        description="Potential injection vulnerability",
                        file_path=filepath,
                        line_number=i,
                        recommendation="Use parameterized queries/safe alternatives",
                        cwe_id=cwe,
                        evidence=line.strip()[:120],
                    ))

    def _check_path_traversal(self, filepath: str, lines: List[str]):
        self.report.checks_performed += 1
        for i, line in enumerate(lines, 1):
            for pattern, desc, cwe in self.PATH_TRAVERSAL_PATTERNS:
                if re.search(pattern, line):
                    # Skip if there's path validation nearby
                    context = "\n".join(lines[max(0, i - 5):i + 5])
                    if "os.path.abspath" in context or "realpath" in context:
                        continue
                    self.report.add_finding(AuditFinding(
                        severity=Severity.MEDIUM,
                        category="Path Traversal",
                        title=desc,
                        description="User-influenced file path may allow directory traversal",
                        file_path=filepath,
                        line_number=i,
                        recommendation="Validate and canonicalize file paths before use",
                        cwe_id=cwe,
                        evidence=line.strip()[:120],
                    ))

    def _check_unsafe_crypto(self, filepath: str, content: str, lines: List[str]):
        self.report.checks_performed += 1
        weak_algos = [
            (r'hashlib\.md5\s*\(', "MD5 hash usage - weak for security"),
            (r'hashlib\.sha1\s*\(', "SHA-1 hash usage - weak for security"),
            (r'\bDES\b', "Weak cipher algorithm (DES)"),
            (r'\bBlowfish\b', "Weak cipher algorithm (Blowfish)"),
            (r'\bRC4\b', "Weak cipher algorithm (RC4)"),
            (r'random\.(?:random|randint|choice|shuffle)\s*\(',
             "Non-cryptographic RNG for potential security use"),
        ]
        for i, line in enumerate(lines, 1):
            if self._is_in_string_or_comment(line):
                continue
            for pattern, desc in weak_algos:
                if re.search(pattern, line):
                    # random module in non-security context is fine
                    if "random" in pattern and "test" in filepath:
                        continue
                    # DES/Blowfish/RC4: only flag in import or crypto contexts
                    if any(w in desc for w in ["DES", "Blowfish", "RC4"]):
                        if not any(ctx in line.lower() for ctx in [
                            "import", "cipher", "encrypt", "decrypt", "algorithm",
                        ]):
                            continue
                    self.report.add_finding(AuditFinding(
                        severity=Severity.LOW,
                        category="Cryptography",
                        title=desc,
                        description="Weak or non-cryptographic algorithm in use",
                        file_path=filepath,
                        line_number=i,
                        recommendation="Use SHA-256+ for hashing, AES-256 for encryption, secrets module for RNG",
                        cwe_id="CWE-327",
                        evidence=line.strip()[:120],
                    ))

    def _check_error_handling(self, filepath: str, lines: List[str]):
        self.report.checks_performed += 1
        for i, line in enumerate(lines, 1):
            # Bare except clauses
            if re.match(r'\s*except\s*:', line):
                self.report.add_finding(AuditFinding(
                    severity=Severity.LOW,
                    category="Error Handling",
                    title="Bare except clause",
                    description="Catches all exceptions including SystemExit and KeyboardInterrupt",
                    file_path=filepath,
                    line_number=i,
                    recommendation="Catch specific exceptions (Exception at minimum)",
                    cwe_id="CWE-396",
                ))
            # Exception info suppressed
            if re.search(r'except\s+\w+.*:\s*$', line):
                next_lines = "\n".join(lines[i:i + 3])
                if "pass" in next_lines and "log" not in next_lines.lower():
                    self.report.add_finding(AuditFinding(
                        severity=Severity.LOW,
                        category="Error Handling",
                        title="Silent exception swallowing",
                        description="Exception caught and silently discarded",
                        file_path=filepath,
                        line_number=i,
                        recommendation="Log exception details for debugging",
                        cwe_id="CWE-390",
                    ))

    def _check_authentication(self, filepath: str, content: str, lines: List[str]):
        self.report.checks_performed += 1
        if "fastapi" in content.lower() or "flask" in content.lower():
            for i, line in enumerate(lines, 1):
                if re.search(r'@(?:app|router)\.(?:get|post|put|delete|patch)\s*\(', line):
                    context = "\n".join(lines[i:i + 5])
                    if not any(auth in context.lower() for auth in [
                        "depends(", "authenticate", "auth_required",
                        "api_key", "bearer", "authorization",
                    ]):
                        self.report.add_finding(AuditFinding(
                            severity=Severity.MEDIUM,
                            category="Authentication",
                            title="Web endpoint without visible auth",
                            description="HTTP endpoint may lack authentication",
                            file_path=filepath,
                            line_number=i,
                            recommendation="Add authentication dependency or document why auth is not needed",
                            cwe_id="CWE-306",
                            evidence=line.strip()[:120],
                        ))

    def _check_sensitive_data_logging(self, filepath: str, lines: List[str]):
        self.report.checks_performed += 1
        sensitive_vars = [
            "api_key", "api_secret", "password", "secret", "token",
            "private_key", "passphrase", "credential",
        ]
        for i, line in enumerate(lines, 1):
            if any(kw in line.lower() for kw in ["log.", "print(", "logger."]):
                for var in sensitive_vars:
                    if re.search(rf'\b{var}\b', line, re.IGNORECASE):
                        if any(safe in line for safe in [
                            "is None", "not set", "configured", "available",
                            "***", "REDACTED", "[:8]", "[:4]",
                        ]):
                            continue
                        self.report.add_finding(AuditFinding(
                            severity=Severity.MEDIUM,
                            category="Data Exposure",
                            title="Potential sensitive data in log output",
                            description=f"Variable '{var}' may be logged",
                            file_path=filepath,
                            line_number=i,
                            recommendation="Redact sensitive values before logging",
                            cwe_id="CWE-532",
                            evidence=line.strip()[:120],
                        ))

    def _check_hmac_timing(self, filepath: str, content: str, lines: List[str]):
        """Check for HMAC comparison using == instead of hmac.compare_digest."""
        self.report.checks_performed += 1
        if "hmac" not in content.lower():
            return
        for i, line in enumerate(lines, 1):
            # Look for direct == comparison after HMAC computation
            if re.search(r'hmac.*==|==.*hmac', line, re.IGNORECASE):
                if "compare_digest" not in line:
                    self.report.add_finding(AuditFinding(
                        severity=Severity.HIGH,
                        category="Cryptography",
                        title="HMAC timing attack risk",
                        description="HMAC compared with == instead of hmac.compare_digest()",
                        file_path=filepath,
                        line_number=i,
                        recommendation="Use hmac.compare_digest() for constant-time comparison",
                        cwe_id="CWE-208",
                        evidence=line.strip()[:120],
                    ))

    def _check_http_timeouts(self, filepath: str, content: str, lines: List[str]):
        """Check that HTTP client calls include timeout parameters."""
        self.report.checks_performed += 1
        # Only check files that make HTTP calls
        if not any(lib in content for lib in [
            "aiohttp.ClientSession", "httpx.AsyncClient", "httpx.Client",
            "requests.get", "requests.post", "requests.Session",
        ]):
            return

        has_default_timeout = "timeout" in content.lower()
        if not has_default_timeout:
            rel_path = os.path.relpath(filepath, self.project_root) if filepath.startswith("/") else filepath
            self.report.add_finding(AuditFinding(
                severity=Severity.MEDIUM,
                category="Network",
                title="HTTP client without timeout configuration",
                description="HTTP requests without timeouts can hang indefinitely",
                file_path=rel_path if not rel_path.startswith("/") else filepath,
                recommendation="Set explicit timeout on all HTTP client sessions",
                cwe_id="CWE-400",
            ))

    def _check_gitignore(self):
        """Verify .gitignore excludes sensitive files."""
        self.report.checks_performed += 1
        gitignore_path = os.path.join(self.project_root, ".gitignore")
        if not os.path.exists(gitignore_path):
            self.report.add_finding(AuditFinding(
                severity=Severity.HIGH,
                category="Secrets",
                title="No .gitignore file",
                description="Missing .gitignore may lead to accidental secret commits",
                recommendation="Create .gitignore excluding .env, *.pem, *.key, credentials",
            ))
            return

        content = self._read_file(gitignore_path)
        required_exclusions = [".env", "*.pem", "*.key"]
        for pattern in required_exclusions:
            if pattern not in content:
                self.report.add_finding(AuditFinding(
                    severity=Severity.MEDIUM,
                    category="Secrets",
                    title=f".gitignore missing '{pattern}' exclusion",
                    description=f"Sensitive file pattern '{pattern}' not excluded from git",
                    file_path=".gitignore",
                    recommendation=f"Add '{pattern}' to .gitignore",
                ))

    def _check_env_template(self):
        """Verify env.template doesn't contain real credentials."""
        self.report.checks_performed += 1
        template_path = os.path.join(self.project_root, "env.template")
        if not os.path.exists(template_path):
            self.report.add_finding(AuditFinding(
                severity=Severity.INFO,
                category="Configuration",
                title="No env.template file",
                description="Missing env.template - users may not know what variables to set",
                recommendation="Create env.template with placeholder values",
            ))
            return

        content = self._read_file(template_path)
        for line in content.split("\n"):
            if "=" in line and not line.strip().startswith("#"):
                key, _, value = line.partition("=")
                value = value.strip().strip('"').strip("'")
                if len(value) > 20 and not any(ph in value for ph in [
                    "your_", "<", "xxx", "placeholder", "change_me",
                    "example", "...", "http", "localhost", "redis://",
                ]):
                    self.report.add_finding(AuditFinding(
                        severity=Severity.HIGH,
                        category="Secrets",
                        title="Possible real credential in env.template",
                        description=f"Key '{key.strip()}' has a suspiciously long value",
                        file_path="env.template",
                        recommendation="Replace with placeholder value",
                        cwe_id="CWE-798",
                    ))

    @staticmethod
    def _sanitize_evidence(line: str) -> str:
        """Redact potential secrets from evidence strings."""
        return re.sub(
            r'(["\'])[a-zA-Z0-9+/=_\-]{16,}(["\'])',
            r'\1[REDACTED]\2',
            line
        )[:150]

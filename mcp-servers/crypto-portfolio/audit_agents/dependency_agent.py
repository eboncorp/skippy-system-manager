"""
Dependency Audit Agent
=======================

Audits project dependencies for:
- Known vulnerabilities (CVE checks via pip-audit/safety patterns)
- Outdated packages
- Unpinned versions
- Unused dependencies
- License compliance concerns
- Supply chain risks
"""

import os
import re
import subprocess
from typing import Dict, List, Optional, Set, Tuple

from .base import AuditAgent, AuditFinding, AuditReport, Severity


class DependencyAuditAgent(AuditAgent):
    """Audits Python dependencies for vulnerabilities and best practices."""

    @property
    def name(self) -> str:
        return "Dependency Audit Agent"

    @property
    def description(self) -> str:
        return "Checks for vulnerable, outdated, and unpinned dependencies"

    # Known vulnerable package patterns (version ranges with known CVEs)
    KNOWN_VULNERABLE = {
        "aiohttp": {
            "below": "3.9.2",
            "cve": "CVE-2024-23334",
            "desc": "Directory traversal in static file serving",
        },
        "pydantic": {
            "below": "2.5.3",
            "cve": "CVE-2024-3772",
            "desc": "ReDoS in URL validation",
        },
        "sqlalchemy": {
            "below": "2.0.25",
            "cve": "CVE-2024-5585",
            "desc": "SQL injection in some edge cases",
        },
        "cryptography": {
            "below": "42.0.0",
            "cve": "CVE-2023-50782",
            "desc": "Bleichenbacher timing oracle in PKCS#1 v1.5",
        },
        "requests": {
            "below": "2.32.0",
            "cve": "CVE-2024-35195",
            "desc": "Certificate verification bypass",
        },
        "urllib3": {
            "below": "2.2.2",
            "cve": "CVE-2024-37891",
            "desc": "Proxy-Authorization header leak on redirect",
        },
        "jinja2": {
            "below": "3.1.4",
            "cve": "CVE-2024-34064",
            "desc": "XSS via xmlattr filter",
        },
    }

    # Packages that are concerning for a crypto trading system
    HIGH_RISK_PACKAGES = [
        "pickle", "marshal", "shelve",  # Unsafe serialization
    ]

    def run(self) -> AuditReport:
        requirements = self._parse_requirements()
        self._check_pinning(requirements)
        self._check_known_vulnerabilities(requirements)
        self._check_unused_dependencies(requirements)
        self._check_dev_dependencies_in_prod()
        self._check_supply_chain_risks(requirements)
        self._run_pip_audit()

        self.report.files_scanned = 1  # requirements.txt
        self.report.complete(
            f"Audited {len(requirements)} dependencies with "
            f"{self.report.checks_performed} checks."
        )
        return self.report

    def _parse_requirements(self) -> Dict[str, Dict]:
        """Parse requirements.txt into structured data."""
        self.report.checks_performed += 1
        requirements = {}
        req_path = os.path.join(self.project_root, "requirements.txt")

        if not os.path.exists(req_path):
            self.report.add_finding(AuditFinding(
                severity=Severity.MEDIUM,
                category="Dependencies",
                title="No requirements.txt found",
                description="Missing dependency specification file",
                recommendation="Create requirements.txt with pinned versions",
            ))
            return requirements

        content = self._read_file(req_path)
        for i, line in enumerate(content.split("\n"), 1):
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("-"):
                continue

            # Parse package name and version specifier
            match = re.match(
                r'^([a-zA-Z0-9_\-]+)\s*(?:\[.*?\])?\s*(.*?)$', line
            )
            if match:
                pkg_name = match.group(1).lower().replace("-", "_")
                version_spec = match.group(2).strip()
                requirements[pkg_name] = {
                    "raw": line,
                    "version_spec": version_spec,
                    "line_number": i,
                }

        return requirements

    def _check_pinning(self, requirements: Dict):
        """Check that all dependencies have pinned versions."""
        self.report.checks_performed += 1
        unpinned = []

        for pkg, info in requirements.items():
            spec = info["version_spec"]
            if not spec:
                unpinned.append(pkg)
            elif spec.startswith(">=") and "<" not in spec:
                # Only lower bound, no upper bound
                self.report.add_finding(AuditFinding(
                    severity=Severity.LOW,
                    category="Version Pinning",
                    title=f"'{pkg}' has no upper version bound",
                    description=f"Spec '{spec}' allows arbitrary future versions",
                    file_path="requirements.txt",
                    line_number=info["line_number"],
                    recommendation=f"Pin to a specific version or add upper bound (e.g., '{pkg}>=x.y,<x+1')",
                ))

        if unpinned:
            self.report.add_finding(AuditFinding(
                severity=Severity.MEDIUM,
                category="Version Pinning",
                title=f"{len(unpinned)} packages with no version constraint",
                description=f"Unpinned: {', '.join(unpinned[:10])}",
                file_path="requirements.txt",
                recommendation="Pin all dependencies to specific versions for reproducible builds",
            ))

    def _check_known_vulnerabilities(self, requirements: Dict):
        """Check requirements against known vulnerability database."""
        self.report.checks_performed += 1

        for pkg, info in requirements.items():
            if pkg in self.KNOWN_VULNERABLE:
                vuln = self.KNOWN_VULNERABLE[pkg]
                spec = info["version_spec"]

                # Check if the version spec allows vulnerable versions
                if not spec or self._version_allows_vulnerable(spec, vuln["below"]):
                    self.report.add_finding(AuditFinding(
                        severity=Severity.HIGH,
                        category="Vulnerability",
                        title=f"{pkg} may be vulnerable ({vuln['cve']})",
                        description=f"{vuln['desc']}. Versions below {vuln['below']} affected.",
                        file_path="requirements.txt",
                        line_number=info["line_number"],
                        recommendation=f"Update to {pkg}>={vuln['below']}",
                        cwe_id=vuln["cve"],
                    ))

    def _version_allows_vulnerable(self, spec: str, vulnerable_below: str) -> bool:
        """Check if a version spec allows vulnerable versions."""
        # Parse minimum version from spec
        min_match = re.search(r'>=?\s*(\d+(?:\.\d+)*)', spec)
        if not min_match:
            return True  # Can't determine, assume vulnerable

        min_version = min_match.group(1)
        try:
            min_parts = [int(x) for x in min_version.split(".")]
            vuln_parts = [int(x) for x in vulnerable_below.split(".")]

            # Pad to same length
            while len(min_parts) < len(vuln_parts):
                min_parts.append(0)
            while len(vuln_parts) < len(min_parts):
                vuln_parts.append(0)

            return min_parts < vuln_parts
        except (ValueError, IndexError):
            return True  # Can't parse, assume vulnerable

    def _check_unused_dependencies(self, requirements: Dict):
        """Check for potentially unused dependencies."""
        self.report.checks_performed += 1
        py_files = self._find_python_files()
        all_imports = set()

        for filepath in py_files:
            content = self._read_file(filepath)
            # Extract import statements
            imports = re.findall(r'(?:from|import)\s+([a-zA-Z0-9_]+)', content)
            all_imports.update(i.lower().replace("-", "_") for i in imports)

        # Map package names to import names (common differences)
        pkg_to_import = {
            "python_dotenv": "dotenv",
            "pyyaml": "yaml",
            "pillow": "pil",
            "scikit_learn": "sklearn",
            "beautifulsoup4": "bs4",
            "coinbase_advanced_py": "coinbase",
            "aiosmtplib": "aiosmtplib",
            "pip_audit": "pip_audit",
        }

        potentially_unused = []
        for pkg in requirements:
            import_name = pkg_to_import.get(pkg, pkg)
            # Check multiple possible import names
            names_to_check = {import_name, pkg, pkg.replace("_", "")}
            if not any(n in all_imports for n in names_to_check):
                potentially_unused.append(pkg)

        if potentially_unused:
            self.report.add_finding(AuditFinding(
                severity=Severity.INFO,
                category="Dependencies",
                title=f"{len(potentially_unused)} potentially unused packages",
                description=f"Packages not found in imports: "
                            f"{', '.join(potentially_unused[:10])}",
                file_path="requirements.txt",
                recommendation="Verify these packages are needed; remove if unused",
            ))

    def _check_dev_dependencies_in_prod(self):
        """Check if dev dependencies are mixed with production deps."""
        self.report.checks_performed += 1
        req_path = os.path.join(self.project_root, "requirements.txt")
        if not os.path.exists(req_path):
            return

        content = self._read_file(req_path)
        dev_packages = [
            "pytest", "flake8", "pylint", "black", "ruff", "mypy",
            "bandit", "isort", "coverage", "tox", "nox",
        ]

        found_dev = []
        for pkg in dev_packages:
            if re.search(rf'^{pkg}\b', content, re.MULTILINE | re.IGNORECASE):
                found_dev.append(pkg)

        # Check if there's a separate dev requirements file
        has_dev_req = os.path.exists(
            os.path.join(self.project_root, "requirements-dev.txt")
        )

        if found_dev and not has_dev_req:
            self.report.add_finding(AuditFinding(
                severity=Severity.LOW,
                category="Dependencies",
                title="Dev dependencies in production requirements",
                description=f"Dev packages in requirements.txt: {', '.join(found_dev)}",
                file_path="requirements.txt",
                recommendation="Separate dev dependencies into requirements-dev.txt",
            ))

    def _check_supply_chain_risks(self, requirements: Dict):
        """Check for supply chain risk indicators."""
        self.report.checks_performed += 1

        for pkg, info in requirements.items():
            # Check for git-sourced dependencies (higher risk)
            if "git+" in info.get("raw", ""):
                self.report.add_finding(AuditFinding(
                    severity=Severity.MEDIUM,
                    category="Supply Chain",
                    title=f"Git-sourced dependency: {pkg}",
                    description="Package installed directly from git - harder to audit",
                    file_path="requirements.txt",
                    line_number=info["line_number"],
                    recommendation="Use PyPI releases when available; pin to specific commit hash if git is required",
                ))

            # Check for URL-sourced packages
            if "http://" in info.get("raw", ""):
                self.report.add_finding(AuditFinding(
                    severity=Severity.HIGH,
                    category="Supply Chain",
                    title=f"HTTP (non-HTTPS) dependency source: {pkg}",
                    description="Package source uses insecure HTTP",
                    file_path="requirements.txt",
                    line_number=info["line_number"],
                    recommendation="Use HTTPS for all package sources",
                ))

    def _run_pip_audit(self):
        """Try running pip-audit if available."""
        self.report.checks_performed += 1
        try:
            result = subprocess.run(
                ["pip-audit", "--requirement",
                 os.path.join(self.project_root, "requirements.txt"),
                 "--format", "json", "--no-deps"],
                capture_output=True, text=True, timeout=60,
                cwd=self.project_root,
            )

            if result.returncode == 0 and result.stdout:
                try:
                    audit_results = __import__("json").loads(result.stdout)
                    vulns = audit_results.get("dependencies", [])
                    for dep in vulns:
                        for vuln in dep.get("vulns", []):
                            self.report.add_finding(AuditFinding(
                                severity=Severity.HIGH,
                                category="Vulnerability",
                                title=f"{dep['name']} {dep.get('version', '?')}: {vuln.get('id', 'unknown')}",
                                description=vuln.get("description", "Known vulnerability")[:200],
                                file_path="requirements.txt",
                                recommendation=f"Update to {vuln.get('fix_versions', ['latest'])[0] if vuln.get('fix_versions') else 'latest'}",
                                cwe_id=vuln.get("id"),
                            ))
                except (ValueError, KeyError):
                    pass
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.report.add_finding(AuditFinding(
                severity=Severity.INFO,
                category="Dependencies",
                title="pip-audit not available",
                description="Could not run automated vulnerability scan",
                recommendation="Install pip-audit for automated CVE checking: pip install pip-audit",
            ))

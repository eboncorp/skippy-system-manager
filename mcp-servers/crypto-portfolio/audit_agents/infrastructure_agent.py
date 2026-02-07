"""
Infrastructure Audit Agent
============================

Scans for infrastructure security and hygiene issues:
- SSH private keys in repository
- Dockerfile security (running as root, unpinned base images)
- docker-compose security (privileged mode, host networking)
- CI/CD pipeline gaps
- .gitignore completeness
- Dead code and repo hygiene
- Broken symlinks
"""

import json
import os
import re
from typing import Dict, List, Optional

from .base import AuditAgent, AuditFinding, AuditReport, Severity


class InfrastructureAuditAgent(AuditAgent):
    """Scans infrastructure configuration for security and hygiene issues."""

    @property
    def name(self) -> str:
        return "Infrastructure Audit Agent"

    @property
    def description(self) -> str:
        return "Scans Docker, CI/CD, SSH keys, .gitignore, and repo hygiene"

    SKIP_DIRS = {"audit_agents", "__pycache__", ".git", "node_modules", ".venv"}

    # Sensitive file patterns that should NEVER be in a repo
    SENSITIVE_FILE_PATTERNS = [
        ("id_rsa", "SSH RSA private key"),
        ("id_ed25519", "SSH Ed25519 private key"),
        ("id_ecdsa", "SSH ECDSA private key"),
        ("id_dsa", "SSH DSA private key"),
        (".pem", "PEM certificate/key file"),
        (".p12", "PKCS#12 certificate bundle"),
        (".pfx", "PFX certificate bundle"),
        (".key", "Private key file"),
    ]

    # gitignore patterns that should be present
    REQUIRED_GITIGNORE = [
        (".env", "Environment variables"),
        ("*.pem", "PEM certificate files"),
        ("*.key", "Private key files"),
        ("__pycache__", "Python bytecode cache"),
        (".ssh/", "SSH directory"),
    ]

    def run(self) -> AuditReport:
        self._check_sensitive_files()
        self._check_dockerfiles()
        self._check_docker_compose()
        self._check_ci_pipeline()
        self._check_gitignore()
        self._check_broken_symlinks()
        self._check_archived_code()

        self.report.complete(
            f"Infrastructure audit with {self.report.checks_performed} checks "
            f"across {self.report.files_scanned} files."
        )
        return self.report

    def _check_sensitive_files(self):
        """Scan for SSH keys, certificates, and other sensitive files in the repo."""
        self.report.checks_performed += 1
        sensitive_found = []

        for root, dirs, files in os.walk(self.project_root):
            # Skip excluded dirs
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            rel_root = os.path.relpath(root, self.project_root)

            for fname in files:
                for pattern, desc in self.SENSITIVE_FILE_PATTERNS:
                    if fname == pattern or (pattern.startswith(".") and fname.endswith(pattern)):
                        rel_path = os.path.join(rel_root, fname) if rel_root != "." else fname
                        filepath = os.path.join(root, fname)

                        # Verify it's actually a key (not just named similarly)
                        is_private = False
                        if fname.startswith("id_") and not fname.endswith(".pub"):
                            is_private = True
                        elif pattern.startswith("."):
                            # For extension matches, check file content
                            try:
                                with open(filepath, "r", errors="replace") as f:
                                    header = f.read(100)
                                if "PRIVATE KEY" in header:
                                    is_private = True
                            except OSError:
                                pass

                        severity = Severity.CRITICAL if is_private else Severity.HIGH
                        self.report.add_finding(AuditFinding(
                            severity=severity,
                            category="Sensitive Files",
                            title=f"{desc} in repository",
                            description=f"Sensitive file '{fname}' found in repository tree",
                            file_path=rel_path,
                            recommendation="Remove from repo, add to .gitignore, rotate the key",
                            cwe_id="CWE-312",
                        ))
                        self.report.files_scanned += 1

    def _check_dockerfiles(self):
        """Audit Dockerfiles for security issues."""
        self.report.checks_performed += 1
        import glob
        dockerfiles = glob.glob(
            os.path.join(self.project_root, "**/Dockerfile*"), recursive=True
        )

        for filepath in dockerfiles:
            content = self._read_file(filepath)
            if not content:
                continue
            self.report.files_scanned += 1
            rel_path = os.path.relpath(filepath, self.project_root)
            lines = content.split("\n")

            # Check for FROM :latest
            for i, line in enumerate(lines, 1):
                if re.match(r'\s*FROM\s+\S+:latest\b', line, re.IGNORECASE):
                    self.report.add_finding(AuditFinding(
                        severity=Severity.MEDIUM,
                        category="Docker",
                        title="Unpinned base image (:latest tag)",
                        description="Using :latest tag makes builds non-reproducible",
                        file_path=rel_path,
                        line_number=i,
                        recommendation="Pin to a specific version tag",
                        cwe_id="CWE-829",
                        evidence=line.strip()[:120],
                    ))

                # FROM without tag at all
                if re.match(r'\s*FROM\s+([a-z][a-z0-9_.-]+)\s*$', line, re.IGNORECASE):
                    self.report.add_finding(AuditFinding(
                        severity=Severity.MEDIUM,
                        category="Docker",
                        title="Base image without version tag",
                        description="FROM without a tag implicitly uses :latest",
                        file_path=rel_path,
                        line_number=i,
                        recommendation="Pin to a specific version tag",
                        cwe_id="CWE-829",
                        evidence=line.strip()[:120],
                    ))

            # Check for running as root (no USER directive)
            has_user = any(re.match(r'\s*USER\s+', l) for l in lines)
            if not has_user:
                self.report.add_finding(AuditFinding(
                    severity=Severity.MEDIUM,
                    category="Docker",
                    title="Container runs as root",
                    description="No USER directive - container runs as root by default",
                    file_path=rel_path,
                    recommendation="Add USER directive to run as non-root user",
                    cwe_id="CWE-250",
                ))

            # Check for ADD instead of COPY (ADD can fetch URLs)
            for i, line in enumerate(lines, 1):
                if re.match(r'\s*ADD\s+(?!--chown)', line) and "http" not in line:
                    self.report.add_finding(AuditFinding(
                        severity=Severity.LOW,
                        category="Docker",
                        title="ADD used instead of COPY",
                        description="ADD has extra functionality (tar extraction, URL fetch) that can be surprising",
                        file_path=rel_path,
                        line_number=i,
                        recommendation="Use COPY unless you specifically need ADD features",
                    ))

    def _check_docker_compose(self):
        """Audit docker-compose files for security issues."""
        self.report.checks_performed += 1
        import glob
        compose_files = glob.glob(
            os.path.join(self.project_root, "**/docker-compose*.yml"), recursive=True
        ) + glob.glob(
            os.path.join(self.project_root, "**/docker-compose*.yaml"), recursive=True
        )

        for filepath in compose_files:
            content = self._read_file(filepath)
            if not content:
                continue
            self.report.files_scanned += 1
            rel_path = os.path.relpath(filepath, self.project_root)
            lines = content.split("\n")

            for i, line in enumerate(lines, 1):
                # Privileged mode
                if re.search(r'privileged:\s*true', line, re.IGNORECASE):
                    self.report.add_finding(AuditFinding(
                        severity=Severity.HIGH,
                        category="Docker",
                        title="Container running in privileged mode",
                        description="Privileged containers have full host access",
                        file_path=rel_path,
                        line_number=i,
                        recommendation="Remove privileged: true, use specific capabilities instead",
                        cwe_id="CWE-250",
                    ))

                # Host network mode
                if re.search(r'network_mode:\s*["\']?host', line, re.IGNORECASE):
                    self.report.add_finding(AuditFinding(
                        severity=Severity.MEDIUM,
                        category="Docker",
                        title="Container using host network",
                        description="Host network mode bypasses Docker network isolation",
                        file_path=rel_path,
                        line_number=i,
                        recommendation="Use bridge or overlay networks instead",
                        cwe_id="CWE-668",
                    ))

                # Hardcoded credentials in compose
                if re.search(r'(?:PASSWORD|SECRET|API_KEY)\s*[:=]\s*["\']?[a-zA-Z0-9]{8,}', line):
                    if not any(safe in line for safe in ["${", "your_", "changeme", "example"]):
                        self.report.add_finding(AuditFinding(
                            severity=Severity.HIGH,
                            category="Secrets",
                            title="Hardcoded secret in docker-compose",
                            description="Credentials should not be hardcoded in compose files",
                            file_path=rel_path,
                            line_number=i,
                            recommendation="Use environment variables or Docker secrets",
                            cwe_id="CWE-798",
                        ))

    def _check_ci_pipeline(self):
        """Audit CI/CD pipeline configuration."""
        self.report.checks_performed += 1
        import glob
        ci_files = glob.glob(
            os.path.join(self.project_root, ".github/workflows/*.yml"), recursive=False
        ) + glob.glob(
            os.path.join(self.project_root, ".github/workflows/*.yaml"), recursive=False
        )

        if not ci_files:
            self.report.add_finding(AuditFinding(
                severity=Severity.MEDIUM,
                category="CI/CD",
                title="No CI/CD pipeline configured",
                description="No GitHub Actions workflows found",
                recommendation="Add CI/CD pipeline with testing and security scanning",
            ))
            return

        has_security_scan = False
        has_tests = False

        for filepath in ci_files:
            content = self._read_file(filepath)
            if not content:
                continue
            self.report.files_scanned += 1
            rel_path = os.path.relpath(filepath, self.project_root)

            if any(tool in content.lower() for tool in [
                "bandit", "safety", "trivy", "snyk", "trufflehog", "security"
            ]):
                has_security_scan = True

            if any(tool in content.lower() for tool in ["pytest", "test", "jest", "mocha"]):
                has_tests = True

            # Check for secrets in CI files
            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                if re.search(r'(?:password|token|secret|key)\s*:\s*["\']?[a-zA-Z0-9]{16,}', line, re.IGNORECASE):
                    if "${{" not in line and "secrets." not in line:
                        self.report.add_finding(AuditFinding(
                            severity=Severity.HIGH,
                            category="CI/CD",
                            title="Potential hardcoded secret in CI config",
                            description="Credentials should use GitHub Secrets",
                            file_path=rel_path,
                            line_number=i,
                            recommendation="Use ${{ secrets.NAME }} instead of hardcoded values",
                            cwe_id="CWE-798",
                        ))

        if not has_security_scan:
            self.report.add_finding(AuditFinding(
                severity=Severity.MEDIUM,
                category="CI/CD",
                title="No security scanning in CI pipeline",
                description="CI pipeline lacks automated security scanning tools",
                recommendation="Add Bandit, Safety, or Trivy to the CI pipeline",
            ))

        if not has_tests:
            self.report.add_finding(AuditFinding(
                severity=Severity.MEDIUM,
                category="CI/CD",
                title="No test stage in CI pipeline",
                description="CI pipeline lacks automated testing",
                recommendation="Add pytest or equivalent test runner to CI",
            ))

    def _check_gitignore(self):
        """Verify .gitignore covers sensitive patterns."""
        self.report.checks_performed += 1
        gitignore_path = os.path.join(self.project_root, ".gitignore")

        if not os.path.exists(gitignore_path):
            self.report.add_finding(AuditFinding(
                severity=Severity.HIGH,
                category="Repo Hygiene",
                title="No .gitignore file at project root",
                description="Missing .gitignore may lead to accidental commits of sensitive files",
                recommendation="Create .gitignore with appropriate exclusions",
            ))
            return

        content = self._read_file(gitignore_path)
        self.report.files_scanned += 1

        for pattern, desc in self.REQUIRED_GITIGNORE:
            if pattern not in content:
                self.report.add_finding(AuditFinding(
                    severity=Severity.MEDIUM,
                    category="Repo Hygiene",
                    title=f".gitignore missing '{pattern}'",
                    description=f"{desc} not excluded from git tracking",
                    file_path=".gitignore",
                    recommendation=f"Add '{pattern}' to .gitignore",
                ))

    def _check_broken_symlinks(self):
        """Find broken symlinks in the project."""
        self.report.checks_performed += 1
        broken = []
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            for fname in files:
                filepath = os.path.join(root, fname)
                if os.path.islink(filepath) and not os.path.exists(filepath):
                    rel_path = os.path.relpath(filepath, self.project_root)
                    target = os.readlink(filepath)
                    broken.append((rel_path, target))

        if broken:
            for rel_path, target in broken[:10]:  # Cap at 10 to avoid noise
                self.report.add_finding(AuditFinding(
                    severity=Severity.LOW,
                    category="Repo Hygiene",
                    title="Broken symlink",
                    description=f"Symlink points to non-existent target: {target}",
                    file_path=rel_path,
                    recommendation="Remove or fix the broken symlink",
                ))

    def _check_archived_code(self):
        """Check for large amounts of archived/dead code."""
        self.report.checks_performed += 1
        archive_dirs = []
        total_archived = 0

        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules", ".venv"}]
            rel_root = os.path.relpath(root, self.project_root)
            basename = os.path.basename(root)

            if any(kw in basename.lower() for kw in ["archive", "legacy", "deprecated", "old_version"]):
                file_count = len([f for f in files if f.endswith((".py", ".sh", ".bash"))])
                if file_count > 0:
                    archive_dirs.append((rel_root, file_count))
                    total_archived += file_count

        if total_archived > 20:
            dirs_str = ", ".join(f"{d} ({n} files)" for d, n in archive_dirs[:5])
            self.report.add_finding(AuditFinding(
                severity=Severity.LOW,
                category="Repo Hygiene",
                title=f"{total_archived} archived/legacy scripts in repository",
                description=f"Large archive footprint: {dirs_str}",
                recommendation="Consider moving archives to a separate branch or deleting them",
            ))

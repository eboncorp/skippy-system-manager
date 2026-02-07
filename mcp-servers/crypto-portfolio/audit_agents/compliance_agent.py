"""
Compliance Audit Agent
=======================

Audits regulatory and operational compliance:
- Audit log integrity verification
- Tax compliance (Form 8949, cost basis tracking)
- Data retention policies
- Trade execution audit trail
- Financial reporting completeness
- Privacy and PII handling
"""

import json
import os
import re
from typing import Dict, List, Optional

from .base import AuditAgent, AuditFinding, AuditReport, Severity


class ComplianceAuditAgent(AuditAgent):
    """Audits compliance, audit logging, tax systems, and data integrity."""

    @property
    def name(self) -> str:
        return "Compliance Audit Agent"

    @property
    def description(self) -> str:
        return "Verifies audit log integrity, tax compliance, and data retention"

    def run(self) -> AuditReport:
        py_files = self._find_python_files()
        self.report.files_scanned = len(py_files)

        self._check_audit_log_implementation()
        self._check_audit_log_coverage(py_files)
        self._check_tax_compliance(py_files)
        self._check_data_retention()
        self._check_trade_audit_trail(py_files)
        self._check_pii_handling(py_files)
        self._check_financial_calculations(py_files)
        self._verify_audit_chain_integrity()

        self.report.complete(
            f"Compliance audit completed across {self.report.files_scanned} files."
        )
        return self.report

    def _check_audit_log_implementation(self):
        """Verify audit log uses tamper-evident design."""
        self.report.checks_performed += 1
        audit_path = os.path.join(self.project_root, "compliance", "audit_log.py")

        if not os.path.exists(audit_path):
            self.report.add_finding(AuditFinding(
                severity=Severity.HIGH,
                category="Audit Logging",
                title="No audit log implementation found",
                description="Missing compliance/audit_log.py - critical for financial system",
                recommendation="Implement tamper-evident audit logging with hash chains",
            ))
            return

        content = self._read_file(audit_path)

        # Verify hash chain implementation
        has_hash_chain = "sha256" in content.lower() or "sha-256" in content.lower()
        has_prev_checksum = "prev_checksum" in content
        has_verify = "verify" in content.lower()

        if not has_hash_chain:
            self.report.add_finding(AuditFinding(
                severity=Severity.HIGH,
                category="Audit Logging",
                title="Audit log lacks cryptographic hash chain",
                description="Without hash chains, audit log entries can be modified undetected",
                file_path="compliance/audit_log.py",
                recommendation="Implement SHA-256 hash chain linking each entry to the previous",
            ))

        if not has_prev_checksum:
            self.report.add_finding(AuditFinding(
                severity=Severity.HIGH,
                category="Audit Logging",
                title="Audit log lacks chain linking",
                description="Entries not linked to previous entries",
                file_path="compliance/audit_log.py",
                recommendation="Add prev_checksum field linking each entry to its predecessor",
            ))

        if not has_verify:
            self.report.add_finding(AuditFinding(
                severity=Severity.MEDIUM,
                category="Audit Logging",
                title="No audit chain verification method",
                description="No way to verify integrity of the audit trail",
                file_path="compliance/audit_log.py",
                recommendation="Add verify_chain() method to validate entire audit history",
            ))

        # Check for append-only semantics
        if "delete" in content.lower() and "log_delete" not in content.lower():
            has_delete_entries = bool(re.search(r'def\s+delete', content))
            if has_delete_entries:
                self.report.add_finding(AuditFinding(
                    severity=Severity.HIGH,
                    category="Audit Logging",
                    title="Audit log may allow deletion of entries",
                    description="Audit logs must be append-only for compliance",
                    file_path="compliance/audit_log.py",
                    recommendation="Remove any methods that delete audit entries",
                ))

    # Files that define data/config but don't perform operations
    _NON_OPERATIONAL_PATTERNS = {
        "config", "settings", "targets", "signals", "analyzer",
        "models", "schema", "types", "constants", "utils", "helpers",
        "test_", "conftest", "__init__", "cli", "dashboard",
        "rate_limiter", "cache", "providers", "storage",
    }

    def _check_audit_log_coverage(self, py_files: List[str]):
        """Check that key operations are audit-logged."""
        self.report.checks_performed += 1

        # Operations that MUST be logged -- use function def patterns to find
        # actual implementations, not just keyword mentions
        critical_operations = {
            "trade execution": [r'def\s+(?:place_order|execute_trade|market_order|limit_order)\b'],
            "fund transfer": [r'def\s+(?:withdraw|deposit|transfer)\b'],
            "staking operation": [r'def\s+(?:stake|unstake|stake_asset|unstake_asset)\b'],
            "DCA execution": [r'def\s+(?:run_dca|execute_dca|dca_buy)\b'],
            "rebalancing": [r'def\s+(?:rebalance|rebalance_portfolio)\b'],
        }

        audit_calls_found = set()
        for filepath in py_files:
            content = self._read_file(filepath)
            if "audit_log" in content.lower() or "log_change" in content:
                rel_path = os.path.relpath(filepath, self.project_root)
                audit_calls_found.add(rel_path)

        for operation, patterns in critical_operations.items():
            for filepath in py_files:
                rel_path = os.path.relpath(filepath, self.project_root)
                basename = os.path.basename(filepath).lower()

                # Skip non-operational files
                if any(p in basename for p in self._NON_OPERATIONAL_PATTERNS):
                    continue

                content = self._read_file(filepath)
                has_operation = any(
                    re.search(pat, content) for pat in patterns
                )

                if has_operation and rel_path not in audit_calls_found:
                    if "audit" not in content.lower():
                        self.report.add_finding(AuditFinding(
                            severity=Severity.MEDIUM,
                            category="Audit Coverage",
                            title=f"'{operation}' may lack audit logging",
                            description=f"File {rel_path} defines {operation} functions but no audit log calls",
                            file_path=rel_path,
                            recommendation=f"Add audit_log.log_change() calls for {operation} events",
                        ))

    def _check_tax_compliance(self, py_files: List[str]):
        """Verify tax-related functionality is complete."""
        self.report.checks_performed += 1

        # Required tax features for US crypto tax compliance
        required_features = {
            "cost_basis": {
                "keywords": ["cost_basis", "fifo", "lifo", "hifo"],
                "description": "Cost basis calculation with multiple methods",
            },
            "form_8949": {
                "keywords": ["form_8949", "8949", "capital_gain"],
                "description": "IRS Form 8949 generation for capital gains",
            },
            "wash_sale": {
                "keywords": ["wash_sale", "wash_trading"],
                "description": "Wash sale detection (30-day rule)",
            },
            "holding_period": {
                "keywords": ["holding_period", "long_term", "short_term"],
                "description": "Short-term vs long-term capital gains classification",
            },
        }

        for feature, spec in required_features.items():
            found = False
            for filepath in py_files:
                content = self._read_file(filepath)
                if any(kw in content.lower() for kw in spec["keywords"]):
                    found = True
                    break

            if not found:
                self.report.add_finding(AuditFinding(
                    severity=Severity.MEDIUM,
                    category="Tax Compliance",
                    title=f"Missing tax feature: {feature}",
                    description=spec["description"],
                    recommendation=f"Implement {feature} for US tax compliance",
                ))

    def _check_data_retention(self):
        """Verify data retention policies are implemented."""
        self.report.checks_performed += 1

        # Check for data cleanup/retention logic
        py_files = self._find_python_files()
        has_retention = False

        for filepath in py_files:
            content = self._read_file(filepath)
            if any(kw in content.lower() for kw in [
                "retention", "cleanup", "purge", "archive",
                "expire", "ttl", "max_age",
            ]):
                has_retention = True
                break

        if not has_retention:
            self.report.add_finding(AuditFinding(
                severity=Severity.LOW,
                category="Data Retention",
                title="No data retention policy found",
                description="Financial data should have defined retention periods "
                            "(IRS requires 3-7 years for tax records)",
                recommendation="Implement data retention and archival policy",
            ))

        # Check cache TTL settings
        for filepath in py_files:
            content = self._read_file(filepath)
            rel_path = os.path.relpath(filepath, self.project_root)
            if "cache" in content.lower():
                # Check for extremely long or no TTL
                ttl_match = re.search(r'ttl\s*=\s*(\d+)', content)
                if ttl_match:
                    ttl = int(ttl_match.group(1))
                    if ttl > 86400:  # More than 24 hours
                        self.report.add_finding(AuditFinding(
                            severity=Severity.LOW,
                            category="Data Freshness",
                            title=f"Long cache TTL: {ttl}s ({ttl // 3600}h)",
                            description="Stale price data could lead to poor trading decisions",
                            file_path=rel_path,
                            recommendation="Reduce cache TTL for price-sensitive data",
                        ))

    def _check_trade_audit_trail(self, py_files: List[str]):
        """Verify trade operations maintain complete audit trail."""
        self.report.checks_performed += 1

        # Check that trade functions capture required data points
        required_trade_fields = [
            "timestamp", "exchange", "pair", "side",
            "price", "amount", "fee",
        ]

        trading_files = [
            "trading_engine.py", "trading_cli.py", "multi_trading_cli.py",
            "additional_tools.py", "advanced_orders.py",
        ]

        for filename in trading_files:
            filepath = os.path.join(self.project_root, filename)
            if not os.path.exists(filepath):
                continue

            content = self._read_file(filepath)
            missing_fields = []

            for field_name in required_trade_fields:
                if field_name not in content.lower():
                    missing_fields.append(field_name)

            if missing_fields and len(missing_fields) < len(required_trade_fields):
                self.report.add_finding(AuditFinding(
                    severity=Severity.LOW,
                    category="Trade Audit",
                    title=f"Trade records may miss fields in {filename}",
                    description=f"Fields not found: {', '.join(missing_fields)}",
                    file_path=filename,
                    recommendation="Ensure all trade records include complete execution details",
                ))

    def _check_pii_handling(self, py_files: List[str]):
        """Check for proper handling of personally identifiable information."""
        self.report.checks_performed += 1

        pii_patterns = [
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "email address"),
            (r'\b\d{3}-\d{2}-\d{4}\b', "SSN pattern"),
            (r'\b(?:name|full_name|first_name|last_name)\b', "personal name field"),
        ]

        for filepath in py_files:
            content = self._read_file(filepath)
            rel_path = os.path.relpath(filepath, self.project_root)
            basename = os.path.basename(filepath)

            if basename.startswith("test_") or basename == "conftest.py":
                continue

            lines = content.split("\n")
            for i, line in enumerate(lines, 1):
                # Check for hardcoded PII (not in variable references)
                for pattern, pii_type in pii_patterns:
                    if pii_type == "SSN pattern" and re.search(pattern, line):
                        self.report.add_finding(AuditFinding(
                            severity=Severity.HIGH,
                            category="PII",
                            title=f"Possible {pii_type} in code",
                            description="Hardcoded PII should never appear in source code",
                            file_path=rel_path,
                            line_number=i,
                            recommendation="Remove PII from source code",
                            cwe_id="CWE-359",
                        ))

    def _check_financial_calculations(self, py_files: List[str]):
        """Verify financial calculations use appropriate precision."""
        self.report.checks_performed += 1

        for filepath in py_files:
            content = self._read_file(filepath)
            rel_path = os.path.relpath(filepath, self.project_root)
            lines = content.split("\n")

            # Check for floating point in financial calculations
            for i, line in enumerate(lines, 1):
                # Look for float() on financial values
                if re.search(r'float\s*\(\s*(?:price|amount|total|balance|cost)', line):
                    # Check if Decimal is used elsewhere in the file
                    if "Decimal" not in content and "decimal" not in content:
                        self.report.add_finding(AuditFinding(
                            severity=Severity.LOW,
                            category="Financial Precision",
                            title="Float used for financial calculation",
                            description="Floating point arithmetic can cause rounding errors "
                                        "in financial calculations",
                            file_path=rel_path,
                            line_number=i,
                            recommendation="Use decimal.Decimal for precise financial arithmetic",
                            evidence=line.strip()[:120],
                        ))
                        break  # One finding per file is enough

    def _verify_audit_chain_integrity(self):
        """Attempt to verify the actual audit log file if it exists."""
        self.report.checks_performed += 1

        # Check common audit log locations
        audit_paths = [
            os.path.expanduser("~/skippy/work/crypto/audit_log.json"),
            os.path.join(self.project_root, "data", "audit_log.json"),
            os.path.join(self.project_root, "audit_log.json"),
        ]

        for audit_path in audit_paths:
            if os.path.exists(audit_path):
                try:
                    with open(audit_path, "r") as f:
                        entries = json.load(f)

                    if isinstance(entries, list) and len(entries) > 0:
                        self.report.add_finding(AuditFinding(
                            severity=Severity.INFO,
                            category="Audit Logging",
                            title=f"Audit log found: {len(entries)} entries",
                            description=f"Audit log at {audit_path}",
                            file_path=audit_path,
                        ))

                        # Verify chain integrity (links + hash recomputation)
                        import hashlib
                        prev_checksum = ""
                        broken_links = 0

                        for i, entry in enumerate(entries):
                            if entry.get("prev_checksum", "") != prev_checksum:
                                broken_links += 1
                            # Recompute hash to detect data tampering
                            entry_data = {
                                k: v for k, v in entry.items()
                                if k not in ("checksum", "prev_checksum")
                            }
                            payload = json.dumps(
                                entry_data, sort_keys=True,
                                separators=(",", ":"), default=str,
                            )
                            expected = hashlib.sha256(
                                f"{prev_checksum}|{payload}".encode()
                            ).hexdigest()
                            stored = entry.get("checksum", "")
                            if stored and stored != expected:
                                broken_links += 1
                            prev_checksum = stored

                        if broken_links > 0:
                            self.report.add_finding(AuditFinding(
                                severity=Severity.CRITICAL,
                                category="Audit Integrity",
                                title=f"Audit chain has {broken_links} broken links",
                                description="Hash chain integrity check failed - possible tampering",
                                file_path=audit_path,
                                recommendation="Investigate broken chain links for potential tampering",
                            ))
                        else:
                            self.report.add_finding(AuditFinding(
                                severity=Severity.INFO,
                                category="Audit Integrity",
                                title="Audit chain integrity verified",
                                description=f"All {len(entries)} entries pass chain verification",
                                file_path=audit_path,
                            ))

                except (json.JSONDecodeError, OSError) as e:
                    self.report.add_finding(AuditFinding(
                        severity=Severity.MEDIUM,
                        category="Audit Logging",
                        title="Audit log file corrupted or unreadable",
                        description=str(e),
                        file_path=audit_path,
                        recommendation="Investigate and repair audit log file",
                    ))
                return

        self.report.add_finding(AuditFinding(
            severity=Severity.INFO,
            category="Audit Logging",
            title="No audit log data file found",
            description="No existing audit trail to verify (may be a fresh install)",
        ))

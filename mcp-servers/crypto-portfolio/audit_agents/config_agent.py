"""
Configuration Audit Agent
==========================

Audits configuration safety and best practices:
- Default values for safety-critical settings
- Environment variable handling
- Docker/deployment configuration
- Database configuration
- Trading safety limits validation
- Network and port exposure
"""

import json
import os
import re
from typing import Dict, List

from .base import AuditAgent, AuditFinding, AuditReport, Severity


class ConfigAuditAgent(AuditAgent):
    """Audits configuration files and settings for safety issues."""

    @property
    def name(self) -> str:
        return "Configuration Audit Agent"

    @property
    def description(self) -> str:
        return "Validates configuration defaults, safety limits, and deployment settings"

    def run(self) -> AuditReport:
        self._check_trading_defaults()
        self._check_docker_config()
        self._check_database_config()
        self._check_env_template_completeness()
        self._check_safety_limits()
        self._check_network_exposure()
        self._check_logging_config()
        self._check_paper_trading_default()

        self.report.files_scanned = self.report.checks_performed
        self.report.complete(
            f"Validated {self.report.checks_performed} configuration checks."
        )
        return self.report

    def _check_trading_defaults(self):
        """Verify trading mode defaults to safe values."""
        self.report.checks_performed += 1
        config_path = os.path.join(self.project_root, "config.py")
        if not os.path.exists(config_path):
            self.report.add_finding(AuditFinding(
                severity=Severity.MEDIUM,
                category="Configuration",
                title="Missing config.py",
                description="No trading configuration file found",
                recommendation="Create config.py with safe defaults",
            ))
            return

        content = self._read_file(config_path)
        lines = content.split("\n")

        # Check default trading mode
        for i, line in enumerate(lines, 1):
            if "mode:" in line and "TradingMode" in line:
                if "LIVE" in line:
                    self.report.add_finding(AuditFinding(
                        severity=Severity.CRITICAL,
                        category="Trading Safety",
                        title="Default trading mode is LIVE",
                        description="Trading mode defaults to live execution - extremely dangerous",
                        file_path="config.py",
                        line_number=i,
                        recommendation="Default to TradingMode.PAPER or TradingMode.CONFIRM",
                    ))
                elif "PAPER" not in line and "CONFIRM" not in line:
                    self.report.add_finding(AuditFinding(
                        severity=Severity.HIGH,
                        category="Trading Safety",
                        title="Unclear default trading mode",
                        description="Default trading mode is not clearly PAPER or CONFIRM",
                        file_path="config.py",
                        line_number=i,
                        recommendation="Explicitly set default to TradingMode.PAPER",
                    ))

    def _check_safety_limits(self):
        """Validate safety limit values are reasonable."""
        self.report.checks_performed += 1
        config_path = os.path.join(self.project_root, "config.py")
        if not os.path.exists(config_path):
            return

        content = self._read_file(config_path)

        # Check max trade limits
        max_trade_match = re.search(r'max_trade_usd\s*[:=]\s*(\d+(?:\.\d+)?)', content)
        if max_trade_match:
            max_trade = float(max_trade_match.group(1))
            if max_trade > 10000:
                self.report.add_finding(AuditFinding(
                    severity=Severity.HIGH,
                    category="Trading Safety",
                    title=f"High default max trade: ${max_trade:,.0f}",
                    description="Default max trade size exceeds $10,000 - risky for default config",
                    file_path="config.py",
                    recommendation="Lower default max_trade_usd to a safer value (e.g., $100-$500)",
                ))

        # Check daily volume limit
        daily_vol_match = re.search(r'max_daily_volume_usd\s*[:=]\s*(\d+(?:\.\d+)?)', content)
        if daily_vol_match:
            daily_vol = float(daily_vol_match.group(1))
            if daily_vol > 50000:
                self.report.add_finding(AuditFinding(
                    severity=Severity.HIGH,
                    category="Trading Safety",
                    title=f"High default daily volume: ${daily_vol:,.0f}",
                    description="Default daily volume exceeds $50,000",
                    file_path="config.py",
                    recommendation="Lower default max_daily_volume_usd",
                ))

        # Check max sell percent
        sell_pct_match = re.search(r'max_sell_percent\s*[:=]\s*(\d+(?:\.\d+)?)', content)
        if sell_pct_match:
            sell_pct = float(sell_pct_match.group(1))
            if sell_pct > 50:
                self.report.add_finding(AuditFinding(
                    severity=Severity.MEDIUM,
                    category="Trading Safety",
                    title=f"High max sell percent: {sell_pct}%",
                    description="Allowing sale of >50% of an asset in one trade is risky",
                    file_path="config.py",
                    recommendation="Lower max_sell_percent to 25% or less",
                ))

        # Check slippage tolerance
        slippage_match = re.search(r'max_slippage_percent\s*[:=]\s*(\d+(?:\.\d+)?)', content)
        if slippage_match:
            slippage = float(slippage_match.group(1))
            if slippage > 5:
                self.report.add_finding(AuditFinding(
                    severity=Severity.MEDIUM,
                    category="Trading Safety",
                    title=f"High slippage tolerance: {slippage}%",
                    description="Slippage tolerance above 5% allows poor execution",
                    file_path="config.py",
                    recommendation="Lower max_slippage_percent to 1-2%",
                ))

    def _check_docker_config(self):
        """Audit Docker and deployment configuration."""
        self.report.checks_performed += 1

        # Dockerfile checks
        dockerfile_path = os.path.join(self.project_root, "Dockerfile")
        if os.path.exists(dockerfile_path):
            content = self._read_file(dockerfile_path)
            lines = content.split("\n")

            for i, line in enumerate(lines, 1):
                # Running as root
                if line.strip().startswith("USER root"):
                    self.report.add_finding(AuditFinding(
                        severity=Severity.MEDIUM,
                        category="Container Security",
                        title="Container runs as root",
                        description="Running as root increases attack surface",
                        file_path="Dockerfile",
                        line_number=i,
                        recommendation="Create and use a non-root user",
                        cwe_id="CWE-250",
                    ))

            # No USER directive at all
            if "USER " not in content:
                self.report.add_finding(AuditFinding(
                    severity=Severity.MEDIUM,
                    category="Container Security",
                    title="No USER directive in Dockerfile",
                    description="Container will run as root by default",
                    file_path="Dockerfile",
                    recommendation="Add USER directive with non-root user",
                    cwe_id="CWE-250",
                ))

            # Using latest tag
            if re.search(r'FROM\s+\S+:latest', content):
                self.report.add_finding(AuditFinding(
                    severity=Severity.LOW,
                    category="Container Security",
                    title="Using ':latest' tag in FROM",
                    description="Unpinned base image may introduce unexpected changes",
                    file_path="Dockerfile",
                    recommendation="Pin to a specific image version/digest",
                ))

        # docker-compose checks
        compose_path = os.path.join(self.project_root, "docker-compose.yml")
        if os.path.exists(compose_path):
            content = self._read_file(compose_path)

            # Check for exposed ports
            port_matches = re.findall(r'ports:\s*\n\s*-\s*["\']?(\d+:\d+)', content)
            for port_mapping in port_matches:
                host_port = port_mapping.split(":")[0]
                if host_port not in ("127.0.0.1", "localhost"):
                    self.report.add_finding(AuditFinding(
                        severity=Severity.INFO,
                        category="Network",
                        title=f"Port {port_mapping} exposed",
                        description="Port binding may be accessible externally",
                        file_path="docker-compose.yml",
                        recommendation="Bind to 127.0.0.1 unless external access is needed",
                    ))

            # Check for environment variables with values
            env_with_values = re.findall(
                r'environment:\s*\n((?:\s+-\s+\S+=\S+\n)*)', content
            )
            for env_block in env_with_values:
                for line in env_block.strip().split("\n"):
                    if any(kw in line.lower() for kw in ["password", "secret", "key"]):
                        if "${" not in line:
                            self.report.add_finding(AuditFinding(
                                severity=Severity.MEDIUM,
                                category="Secrets",
                                title="Hardcoded secret in docker-compose",
                                description="Secret value should reference env var",
                                file_path="docker-compose.yml",
                                recommendation="Use ${VAR} syntax to reference environment variables",
                            ))

    def _check_database_config(self):
        """Audit database configuration."""
        self.report.checks_performed += 1

        db_files = ["database.py", "models.py", "alembic.ini"]
        for filename in db_files:
            filepath = os.path.join(self.project_root, filename)
            if not os.path.exists(filepath):
                continue

            content = self._read_file(filepath)

            # Check for hardcoded connection strings
            if re.search(r'(?:postgresql|mysql|sqlite)://[^"\']*:[^"\']*@', content):
                if "os.getenv" not in content and "environ" not in content:
                    self.report.add_finding(AuditFinding(
                        severity=Severity.HIGH,
                        category="Database",
                        title="Hardcoded database credentials",
                        description="Database connection string contains credentials",
                        file_path=filename,
                        recommendation="Load database URL from environment variable",
                        cwe_id="CWE-798",
                    ))

            # Check for SQL debug mode
            if re.search(r'echo\s*=\s*True', content):
                self.report.add_finding(AuditFinding(
                    severity=Severity.LOW,
                    category="Database",
                    title="SQL echo mode enabled",
                    description="SQL debug logging may expose sensitive data in production",
                    file_path=filename,
                    recommendation="Disable echo=True in production",
                ))

    def _check_env_template_completeness(self):
        """Check that env.template covers all required variables."""
        self.report.checks_performed += 1
        template_path = os.path.join(self.project_root, "env.template")
        if not os.path.exists(template_path):
            return

        template_content = self._read_file(template_path)
        template_vars = set(re.findall(r'^(\w+)=', template_content, re.MULTILINE))

        # Scan Python files for os.getenv calls
        used_vars = set()
        for filepath in self._find_python_files():
            content = self._read_file(filepath)
            matches = re.findall(r'os\.getenv\s*\(\s*["\'](\w+)["\']', content)
            matches += re.findall(r'os\.environ(?:\.get)?\s*\(\s*["\'](\w+)["\']', content)
            matches += re.findall(r'os\.environ\s*\[\s*["\'](\w+)["\']', content)
            used_vars.update(matches)

        # Find vars used in code but missing from template
        missing = used_vars - template_vars
        # Exclude standard vars
        standard_vars = {
            "HOME", "PATH", "USER", "PWD", "LANG", "SHELL",
            "PYTHONPATH", "VIRTUAL_ENV", "CONDA_DEFAULT_ENV",
        }
        missing -= standard_vars

        if missing:
            self.report.add_finding(AuditFinding(
                severity=Severity.LOW,
                category="Configuration",
                title=f"{len(missing)} env vars missing from template",
                description=f"Variables used but not in env.template: "
                            f"{', '.join(sorted(missing)[:10])}",
                file_path="env.template",
                recommendation="Add missing variables to env.template with placeholder values",
            ))

    def _check_network_exposure(self):
        """Check for network service configurations."""
        self.report.checks_performed += 1

        for filepath in self._find_python_files():
            content = self._read_file(filepath)
            rel_path = os.path.relpath(filepath, self.project_root)
            lines = content.split("\n")

            for i, line in enumerate(lines, 1):
                # Binding to 0.0.0.0
                if re.search(r'(?:host|bind)\s*=\s*["\']0\.0\.0\.0["\']', line):
                    self.report.add_finding(AuditFinding(
                        severity=Severity.MEDIUM,
                        category="Network",
                        title="Service binds to 0.0.0.0",
                        description="Service is accessible from all network interfaces",
                        file_path=rel_path,
                        line_number=i,
                        recommendation="Bind to 127.0.0.1 unless external access is required",
                    ))

                # Debug mode in web servers
                if re.search(r'debug\s*=\s*True', line, re.IGNORECASE):
                    if any(kw in content.lower() for kw in ["fastapi", "flask", "uvicorn"]):
                        self.report.add_finding(AuditFinding(
                            severity=Severity.MEDIUM,
                            category="Network",
                            title="Web server debug mode enabled",
                            description="Debug mode may expose sensitive info and allow code execution",
                            file_path=rel_path,
                            line_number=i,
                            recommendation="Disable debug mode in production",
                        ))

    def _check_logging_config(self):
        """Audit logging configuration."""
        self.report.checks_performed += 1
        log_config = os.path.join(self.project_root, "logging_config.py")
        if os.path.exists(log_config):
            content = self._read_file(log_config)
            if "DEBUG" in content and "production" not in content.lower():
                self.report.add_finding(AuditFinding(
                    severity=Severity.INFO,
                    category="Logging",
                    title="Default log level may be DEBUG",
                    description="DEBUG logging in production can expose sensitive data",
                    file_path="logging_config.py",
                    recommendation="Set default log level to INFO or WARNING for production",
                ))

    def _check_paper_trading_default(self):
        """Verify paper trading is the default mode."""
        self.report.checks_performed += 1

        # Check main MCP server file
        mcp_files = ["crypto_portfolio_mcp.py", "mcp_server.py"]
        for filename in mcp_files:
            filepath = os.path.join(self.project_root, filename)
            if not os.path.exists(filepath):
                continue

            content = self._read_file(filepath)
            if "PAPER_TRADING" in content:
                # Check if default is True
                match = re.search(
                    r'PAPER_TRADING["\']?\s*[,)]\s*["\']?(true|false|True|False)',
                    content,
                )
                if match and match.group(1).lower() == "false":
                    self.report.add_finding(AuditFinding(
                        severity=Severity.HIGH,
                        category="Trading Safety",
                        title="Paper trading default is False",
                        description="Paper trading should default to True for safety",
                        file_path=filename,
                        recommendation="Change PAPER_TRADING default to True",
                    ))

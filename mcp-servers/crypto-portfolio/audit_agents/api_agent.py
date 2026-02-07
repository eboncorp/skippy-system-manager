"""
API Audit Agent
================

Validates MCP tool definitions and API surface:
- Tool registration completeness and correctness
- Input validation coverage (Pydantic models)
- Error handling in tool implementations
- Response format consistency
- Rate limiting and resource protection
- Tool annotation accuracy (readOnlyHint, destructiveHint)
"""

import json
import os
import re
from typing import Dict, List

from .base import AuditAgent, AuditFinding, AuditReport, Severity


class APIAuditAgent(AuditAgent):
    """Audits MCP tool definitions, input validation, and API surface."""

    @property
    def name(self) -> str:
        return "API Audit Agent"

    @property
    def description(self) -> str:
        return "Validates MCP tools, input validation, error handling, and response formats"

    def run(self) -> AuditReport:
        py_files = self._find_python_files()
        self.report.files_scanned = len(py_files)

        # Gather tool registrations
        tools = self._extract_tool_registrations(py_files)

        self._check_tool_definitions(tools, py_files)
        self._check_input_validation(py_files)
        self._check_error_handling_in_tools(py_files)
        self._check_response_consistency(py_files)
        self._check_rate_limiting(py_files)
        self._check_tool_annotations(py_files)
        self._check_json_schema_definitions()

        self.report.complete(
            f"Audited {len(tools)} MCP tool definitions across "
            f"{self.report.files_scanned} files."
        )
        return self.report

    def _extract_tool_registrations(self, py_files: List[str]) -> Dict[str, Dict]:
        """Find all @mcp.tool() registrations."""
        tools = {}
        tool_pattern = re.compile(
            r'@(?:mcp|server)\.tool\s*\(\s*(?:name\s*=\s*)?["\']?([\w]+)["\']?',
            re.MULTILINE,
        )
        for filepath in py_files:
            content = self._read_file(filepath)
            rel_path = os.path.relpath(filepath, self.project_root)
            for match in tool_pattern.finditer(content):
                tool_name = match.group(1)
                line_num = content[:match.start()].count("\n") + 1
                tools[tool_name] = {
                    "file": rel_path,
                    "line": line_num,
                }
        return tools

    def _check_tool_definitions(self, tools: Dict, py_files: List[str]):
        """Verify tool completeness and naming conventions."""
        self.report.checks_performed += 1

        # Check naming convention
        for tool_name, info in tools.items():
            if not tool_name.startswith("crypto_"):
                self.report.add_finding(AuditFinding(
                    severity=Severity.LOW,
                    category="API Convention",
                    title=f"Tool '{tool_name}' missing 'crypto_' prefix",
                    description="All crypto server tools should use consistent naming",
                    file_path=info["file"],
                    line_number=info["line"],
                    recommendation="Prefix tool name with 'crypto_' for namespace consistency",
                ))

        # Check for duplicate tool names
        seen = {}
        for tool_name, info in tools.items():
            if tool_name in seen:
                self.report.add_finding(AuditFinding(
                    severity=Severity.HIGH,
                    category="API Definition",
                    title=f"Duplicate tool name: '{tool_name}'",
                    description=f"Tool registered in both {seen[tool_name]['file']} "
                                f"and {info['file']}",
                    file_path=info["file"],
                    line_number=info["line"],
                    recommendation="Remove duplicate registration or rename one tool",
                ))
            seen[tool_name] = info

    def _check_input_validation(self, py_files: List[str]):
        """Check that tool functions use Pydantic or typed parameters."""
        self.report.checks_performed += 1
        tool_func_pattern = re.compile(
            r'@(?:mcp|server)\.tool.*\n(?:.*\n)*?async\s+def\s+(\w+)\s*\(([^)]*)\)',
            re.MULTILINE,
        )

        for filepath in py_files:
            content = self._read_file(filepath)
            rel_path = os.path.relpath(filepath, self.project_root)

            for match in tool_func_pattern.finditer(content):
                func_name = match.group(1)
                params = match.group(2)
                line_num = content[:match.start()].count("\n") + 1

                # Check for untyped parameters (excluding self, ctx)
                if params:
                    for param in params.split(","):
                        param = param.strip()
                        if not param or param in ("self", "ctx", "context"):
                            continue
                        if ":" not in param and "=" not in param:
                            self.report.add_finding(AuditFinding(
                                severity=Severity.MEDIUM,
                                category="Input Validation",
                                title=f"Untyped parameter in tool '{func_name}'",
                                description=f"Parameter '{param.strip()}' lacks type annotation",
                                file_path=rel_path,
                                line_number=line_num,
                                recommendation="Add type annotations for MCP input validation",
                                cwe_id="CWE-20",
                            ))

    def _check_error_handling_in_tools(self, py_files: List[str]):
        """Check that tool functions have proper error handling."""
        self.report.checks_performed += 1
        tool_pattern = re.compile(r'@(?:mcp|server)\.tool')

        for filepath in py_files:
            content = self._read_file(filepath)
            rel_path = os.path.relpath(filepath, self.project_root)
            lines = content.split("\n")

            in_tool = False
            func_name = ""
            func_line = 0
            has_try = False

            for i, line in enumerate(lines):
                if tool_pattern.search(line):
                    in_tool = True
                    has_try = False
                    continue

                if in_tool and re.match(r'\s*(?:async\s+)?def\s+(\w+)', line):
                    match = re.match(r'\s*(?:async\s+)?def\s+(\w+)', line)
                    func_name = match.group(1)
                    func_line = i + 1
                    continue

                if in_tool and func_name:
                    if "try:" in line:
                        has_try = True
                    # Check when we exit the function (next def or decorator at same level)
                    if (re.match(r'\s*(?:@|(?:async\s+)?def\s)', line) and
                            i > func_line + 1):
                        if not has_try:
                            self.report.add_finding(AuditFinding(
                                severity=Severity.LOW,
                                category="Error Handling",
                                title=f"Tool '{func_name}' lacks try/except",
                                description="MCP tool without error handling may expose internal errors",
                                file_path=rel_path,
                                line_number=func_line,
                                recommendation="Wrap tool body in try/except with user-friendly error messages",
                            ))
                        in_tool = False
                        func_name = ""

    def _check_response_consistency(self, py_files: List[str]):
        """Check that tools return consistent response formats."""
        self.report.checks_performed += 1
        return_patterns = set()

        for filepath in py_files:
            content = self._read_file(filepath)
            if "@mcp.tool" not in content and "@server.tool" not in content:
                continue

            rel_path = os.path.relpath(filepath, self.project_root)

            # Check for mixed return types (string vs dict vs list)
            returns_string = bool(re.search(r'return\s+f?["\']', content))
            returns_dict = bool(re.search(r'return\s+\{', content))
            returns_list = bool(re.search(r'return\s+\[', content))

            formats_used = sum([returns_string, returns_dict, returns_list])
            if formats_used > 1:
                self.report.add_finding(AuditFinding(
                    severity=Severity.INFO,
                    category="API Consistency",
                    title="Mixed return types in tool file",
                    description=f"File uses {formats_used} different return formats",
                    file_path=rel_path,
                    recommendation="Standardize on a single response format (e.g., markdown string)",
                ))

    def _check_rate_limiting(self, py_files: List[str]):
        """Check for rate limiting on external API calls."""
        self.report.checks_performed += 1
        has_rate_limiter = False
        api_call_files = []

        for filepath in py_files:
            content = self._read_file(filepath)
            rel_path = os.path.relpath(filepath, self.project_root)

            if "rate_limit" in content.lower() or "RateLimiter" in content:
                has_rate_limiter = True

            # Files making external HTTP calls
            if any(pattern in content for pattern in [
                "aiohttp.ClientSession", "httpx.AsyncClient",
                "requests.get", "requests.post",
            ]):
                if "test_" not in os.path.basename(filepath):
                    api_call_files.append(rel_path)

        if api_call_files and not has_rate_limiter:
            self.report.add_finding(AuditFinding(
                severity=Severity.MEDIUM,
                category="Rate Limiting",
                title="External API calls without rate limiting",
                description=f"{len(api_call_files)} files make HTTP calls without visible rate limiting",
                recommendation="Implement rate limiting for exchange API calls to avoid bans",
                evidence=", ".join(api_call_files[:5]),
            ))

    def _check_tool_annotations(self, py_files: List[str]):
        """Check that tools have proper MCP annotations (readOnlyHint, etc.)."""
        self.report.checks_performed += 1
        annotation_pattern = re.compile(
            r'@(?:mcp|server)\.tool\s*\(([^)]*)\)',
            re.DOTALL,
        )

        for filepath in py_files:
            content = self._read_file(filepath)
            rel_path = os.path.relpath(filepath, self.project_root)

            for match in annotation_pattern.finditer(content):
                args = match.group(1)
                line_num = content[:match.start()].count("\n") + 1

                # Check for destructive tools that modify state
                func_start = content[match.end():match.end() + 500]
                func_match = re.search(r'async\s+def\s+(\w+)', func_start)
                if not func_match:
                    continue

                func_name = func_match.group(1)

                # Tools that modify state should have annotations
                is_mutating = any(kw in func_name.lower() for kw in [
                    "place", "cancel", "create", "delete", "manage",
                    "stake", "unstake", "rebalance", "import", "export",
                ])

                if is_mutating and "destructiveHint" not in args and "annotations" not in args:
                    self.report.add_finding(AuditFinding(
                        severity=Severity.LOW,
                        category="API Annotations",
                        title=f"Mutating tool '{func_name}' missing annotations",
                        description="State-changing tool should declare destructiveHint",
                        file_path=rel_path,
                        line_number=line_num,
                        recommendation="Add annotations={'destructiveHint': True} to tool decorator",
                    ))

    def _check_json_schema_definitions(self):
        """Validate the crypto-portfolio.json tool schema file."""
        self.report.checks_performed += 1
        schema_path = os.path.join(self.project_root, "crypto-portfolio.json")
        if not os.path.exists(schema_path):
            self.report.add_finding(AuditFinding(
                severity=Severity.INFO,
                category="API Schema",
                title="No crypto-portfolio.json schema file",
                description="Missing JSON schema file for tool definitions",
                file_path="crypto-portfolio.json",
                recommendation="Create JSON schema for tool validation",
            ))
            return

        content = self._read_file(schema_path)
        try:
            schema = json.loads(content)
        except json.JSONDecodeError as e:
            self.report.add_finding(AuditFinding(
                severity=Severity.HIGH,
                category="API Schema",
                title="Invalid JSON in schema file",
                description=f"Parse error: {e}",
                file_path="crypto-portfolio.json",
                recommendation="Fix JSON syntax in schema file",
            ))
            return

        # Check each tool definition has required fields
        tools = schema.get("tools", schema) if isinstance(schema, dict) else schema
        if isinstance(tools, list):
            for tool in tools:
                if isinstance(tool, dict):
                    if "description" not in tool:
                        self.report.add_finding(AuditFinding(
                            severity=Severity.LOW,
                            category="API Schema",
                            title=f"Tool missing description: {tool.get('name', 'unknown')}",
                            description="Tool definitions should include descriptions",
                            file_path="crypto-portfolio.json",
                            recommendation="Add description field to tool definition",
                        ))

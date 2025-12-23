#!/usr/bin/env python3
"""
WordPress Content Validator MCP Server
Provides comprehensive multi-level validation for WordPress content
Version: 1.0.0
Created: 2025-11-19
"""

import json
import re
import sys
from typing import Dict, List, Any
from pathlib import Path
import html.parser


class WordPressContentValidator:
    """Multi-level WordPress content validation"""

    def __init__(self, fact_sheet_path: str = None):
        """Initialize validator with fact sheet path"""
        self.fact_sheet_path = fact_sheet_path or self._find_fact_sheet()
        self.facts_cache = self._load_facts()

    def _find_fact_sheet(self) -> str:
        """Find QUICK_FACTS_SHEET.md"""
        possible_paths = [
            "/home/dave/rundaverun/campaign/GODADDY_DEPLOYMENT_2025-10-13/1_WORDPRESS_PLUGIN/dave-biggers-policy-manager/assets/markdown-files/QUICK_FACTS_SHEET.md",
            "/home/dave/skippy/conversations/DAVE_BIGGERS_CAMPAIGN_FACT_SHEET_2025-11-01.md"
        ]

        for path in possible_paths:
            if Path(path).exists():
                return path

        return None

    def _load_facts(self) -> Dict[str, Any]:
        """Load facts from fact sheet"""
        if not self.fact_sheet_path or not Path(self.fact_sheet_path).exists():
            return {}

        # Extract key facts
        facts = {
            "budget": {"total": "$1.2 billion", "wrong": ["$81M", "$110.5M", "$110M"]},
            "public_safety_budget": "$77.4M",
            "wellness_roi": {"correct": "$5.60 per $1", "wrong": ["$2-3", "$1.80", "$1.8"]},
            "mini_substations": {"correct": "63", "wrong": ["46"]},
            "jcps_reading": {"correct": "34-35%", "wrong": ["44%", "45%"]},
            "jcps_math": {"correct": "27-28%", "wrong": ["41%", "40%"]},
            "marital_status": "NOT married",
            "children": "NONE"
        }

        return facts

    def validate_facts(self, content: str) -> Dict[str, Any]:
        """Validate facts against QUICK_FACTS_SHEET.md"""
        errors = []
        warnings = []

        # Budget checks
        if "$81M" in content or "$110" in content:
            errors.append({
                "type": "incorrect_fact",
                "field": "budget",
                "found": "$81M or $110M or $110.5M",
                "correct": "$1.2 billion",
                "severity": "critical"
            })

        if "$1.2 billion" in content or "1.2 billion" in content:
            warnings.append({
                "type": "fact_verified",
                "field": "budget",
                "value": "$1.2 billion",
                "status": "correct"
            })

        # Wellness ROI checks
        if "$2-3" in content or "$1.80" in content or "$1.8" in content:
            errors.append({
                "type": "incorrect_fact",
                "field": "wellness_roi",
                "found": "$2-3 or $1.80",
                "correct": "$5.60 per $1 spent",
                "severity": "critical"
            })

        # JCPS reading proficiency
        if "44%" in content and "reading" in content.lower():
            errors.append({
                "type": "incorrect_fact",
                "field": "jcps_reading",
                "found": "44%",
                "correct": "34-35%",
                "severity": "critical"
            })

        # JCPS math proficiency
        if "41%" in content and "math" in content.lower():
            errors.append({
                "type": "incorrect_fact",
                "field": "jcps_math",
                "found": "41%",
                "correct": "27-28%",
                "severity": "critical"
            })

        # Marital status check
        if any(word in content.lower() for word in ["married", "wife", "spouse"]):
            errors.append({
                "type": "incorrect_fact",
                "field": "marital_status",
                "found": "mentions marriage/spouse",
                "correct": "Dave Biggers is NOT married",
                "severity": "critical"
            })

        # Children check
        if any(word in content.lower() for word in ["children", "kids", "son", "daughter"]):
            errors.append({
                "type": "incorrect_fact",
                "field": "children",
                "found": "mentions children",
                "correct": "Dave Biggers has NO children",
                "severity": "critical"
            })

        return {
            "status": "pass" if len(errors) == 0 else "fail",
            "errors": errors,
            "warnings": warnings,
            "facts_checked": ["budget", "wellness_roi", "jcps_reading", "jcps_math", "marital_status", "children"]
        }

    def validate_links(self, content: str) -> Dict[str, Any]:
        """Check for broken links"""
        errors = []
        warnings = []

        # Find all links
        link_pattern = r'href=["\']([^"\']+)["\']'
        links = re.findall(link_pattern, content)

        for link in links:
            # Check for common broken link patterns
            if link.startswith("http://localhost"):
                warnings.append({
                    "type": "localhost_link",
                    "link": link,
                    "severity": "medium",
                    "message": "Localhost link should be removed before publishing"
                })

            if link == "#" or link == "":
                warnings.append({
                    "type": "empty_link",
                    "link": link,
                    "severity": "low",
                    "message": "Empty or placeholder link"
                })

            # Check for broken internal links
            if link.startswith("/") and not link.startswith("//"):
                warnings.append({
                    "type": "internal_link",
                    "link": link,
                    "severity": "low",
                    "message": "Internal link - verify path exists"
                })

        return {
            "status": "pass" if len(errors) == 0 else "fail",
            "errors": errors,
            "warnings": warnings,
            "links_found": len(links)
        }

    def validate_seo(self, content: str) -> Dict[str, Any]:
        """Validate SEO elements"""
        errors = []
        warnings = []

        # Check for meta tags
        if "<meta" not in content:
            warnings.append({
                "type": "missing_meta",
                "severity": "medium",
                "message": "No meta tags found"
            })

        # Check for title tag
        if "<title>" not in content and "<h1" not in content:
            warnings.append({
                "type": "missing_title",
                "severity": "high",
                "message": "No title or H1 heading found"
            })

        # Check for alt text on images
        img_pattern = r'<img[^>]+>'
        images = re.findall(img_pattern, content)
        for img in images:
            if 'alt=' not in img:
                warnings.append({
                    "type": "missing_alt_text",
                    "image": img[:50] + "...",
                    "severity": "medium",
                    "message": "Image missing alt text for accessibility"
                })

        # Check heading hierarchy
        h1_count = len(re.findall(r'<h1', content))
        if h1_count == 0:
            warnings.append({
                "type": "no_h1",
                "severity": "high",
                "message": "No H1 heading found"
            })
        elif h1_count > 1:
            warnings.append({
                "type": "multiple_h1",
                "count": h1_count,
                "severity": "medium",
                "message": f"Multiple H1 headings ({h1_count}) - should be only one"
            })

        return {
            "status": "pass" if len(errors) == 0 else "warning",
            "errors": errors,
            "warnings": warnings,
            "images_found": len(images)
        }

    def validate_accessibility(self, content: str) -> Dict[str, Any]:
        """Validate WCAG 2.1 accessibility"""
        errors = []
        warnings = []

        # Check for alt text
        img_without_alt = re.findall(r'<img(?![^>]*alt=)[^>]*>', content)
        for img in img_without_alt:
            errors.append({
                "type": "missing_alt_text",
                "element": img[:50] + "...",
                "severity": "high",
                "wcag": "1.1.1",
                "message": "Images must have alt text"
            })

        # Check for aria labels on buttons
        buttons = re.findall(r'<button[^>]*>', content)
        for button in buttons:
            if 'aria-label=' not in button and '>' not in button.replace('</button>', ''):
                warnings.append({
                    "type": "missing_aria_label",
                    "element": button,
                    "severity": "medium",
                    "wcag": "4.1.2",
                    "message": "Button should have aria-label or text content"
                })

        # Check for proper heading hierarchy
        headings = re.findall(r'<h([1-6])', content)
        if headings:
            prev = 0
            for i, level in enumerate(headings):
                level = int(level)
                if i > 0 and level > prev + 1:
                    warnings.append({
                        "type": "skipped_heading_level",
                        "from": f"H{prev}",
                        "to": f"H{level}",
                        "severity": "medium",
                        "wcag": "1.3.1",
                        "message": "Heading levels should not be skipped"
                    })
                prev = level

        return {
            "status": "pass" if len(errors) == 0 else "fail",
            "errors": errors,
            "warnings": warnings,
            "wcag_version": "2.1"
        }

    def validate_html(self, content: str) -> Dict[str, Any]:
        """Validate HTML structure"""
        errors = []
        warnings = []

        # Check for unclosed tags (basic)
        tag_stack = []
        tag_pattern = r'<(/?)(\w+)[^>]*>'

        for match in re.finditer(tag_pattern, content):
            is_closing = match.group(1) == '/'
            tag_name = match.group(2)

            # Skip self-closing tags
            if tag_name.lower() in ['img', 'br', 'hr', 'input', 'meta', 'link']:
                continue

            if is_closing:
                if tag_stack and tag_stack[-1] == tag_name:
                    tag_stack.pop()
                else:
                    errors.append({
                        "type": "unclosed_tag",
                        "tag": tag_name,
                        "severity": "high",
                        "message": f"Unexpected closing tag </{tag_name}>"
                    })
            else:
                tag_stack.append(tag_name)

        # Report unclosed tags
        for tag in tag_stack:
            errors.append({
                "type": "unclosed_tag",
                "tag": tag,
                "severity": "high",
                "message": f"Tag <{tag}> was not closed"
            })

        return {
            "status": "pass" if len(errors) == 0 else "fail",
            "errors": errors,
            "warnings": warnings,
            "tags_checked": len(re.findall(tag_pattern, content))
        }

    def validate_comprehensive(self, content: str, level: str = "standard") -> Dict[str, Any]:
        """Run comprehensive validation at specified level"""

        results = {
            "timestamp": "2025-11-19T00:00:00Z",
            "validation_level": level,
            "overall_status": "pass"
        }

        # Standard level: facts + links
        if level in ["standard", "strict", "publish-ready"]:
            results["facts"] = self.validate_facts(content)
            results["links"] = self.validate_links(content)

        # Strict level: adds SEO
        if level in ["strict", "publish-ready"]:
            results["seo"] = self.validate_seo(content)

        # Publish-ready level: adds accessibility + HTML
        if level == "publish-ready":
            results["accessibility"] = self.validate_accessibility(content)
            results["html"] = self.validate_html(content)

        # Determine overall status
        has_errors = any(
            r.get("status") == "fail"
            for r in results.values()
            if isinstance(r, dict) and "status" in r
        )

        results["overall_status"] = "fail" if has_errors else "pass"

        return results


def main():
    """MCP server main function"""
    validator = WordPressContentValidator()

    # Read MCP request from stdin
    for line in sys.stdin:
        try:
            request = json.loads(line)
            method = request.get("method")
            params = request.get("params", {})

            if method == "validate_content":
                content = params.get("content", "")
                level = params.get("level", "standard")

                result = validator.validate_comprehensive(content, level)

                response = {
                    "jsonrpc": "2.0",
                    "id": request.get("id"),
                    "result": result
                }

                print(json.dumps(response))
                sys.stdout.flush()

        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id") if "request" in locals() else None,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()


if __name__ == "__main__":
    main()

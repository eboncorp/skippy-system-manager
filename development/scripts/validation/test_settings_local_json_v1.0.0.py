#!/usr/bin/env python3
"""
Test suite for settings.local.json validation.

Purpose: Validates that settings.local.json (if present) has correct structure,
doesn't expose secrets, and properly extends settings.json.

Version: 1.0.0
Last Updated: 2025-11-25
"""

import json
import os
import re
import sys
import unittest
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class SettingsLocalJsonTest(unittest.TestCase):
    """Test cases for settings.local.json validation."""

    CLAUDE_DIR = Path.home() / ".claude"
    SETTINGS_FILE = CLAUDE_DIR / "settings.json"
    SETTINGS_LOCAL_FILE = CLAUDE_DIR / "settings.local.json"

    # Valid top-level keys in settings.json
    VALID_TOP_LEVEL_KEYS = {"env", "permissions", "hooks", "preferences"}

    # Valid permission categories
    VALID_PERMISSION_CATEGORIES = {"allow", "ask", "deny"}

    # Patterns that indicate potential secrets (should not be in settings)
    SECRET_PATTERNS = [
        r"[A-Za-z0-9+/]{40,}",  # Base64-like strings (API keys)
        r"sk-[A-Za-z0-9]{32,}",  # OpenAI-style keys
        r"ghp_[A-Za-z0-9]{36,}",  # GitHub tokens
        r"gho_[A-Za-z0-9]{36,}",  # GitHub OAuth tokens
        r"xox[baprs]-[A-Za-z0-9-]{10,}",  # Slack tokens
        r"AIza[A-Za-z0-9_-]{35}",  # Google API keys
        r"ya29\.[A-Za-z0-9_-]+",  # Google OAuth tokens
        r"AKIA[A-Z0-9]{16}",  # AWS access keys
        r"password\s*[=:]\s*['\"][^'\"]+['\"]",  # Password assignments
        r"secret\s*[=:]\s*['\"][^'\"]+['\"]",  # Secret assignments
        r"token\s*[=:]\s*['\"][^'\"]+['\"]",  # Token assignments (in values)
    ]

    # Dangerous permission patterns
    DANGEROUS_PATTERNS = [
        r"rm\s+-rf\s+/(?!home/dave/skippy/work)",  # Dangerous rm -rf
        r"rm\s+-rf\s+~",  # Remove home directory
        r"sudo\s+rm\s+-rf",  # Sudo rm -rf
        r"DROP\s+DATABASE",  # Drop database
        r"DELETE\s+FROM\s+\*",  # Delete all rows
        r"--force.*main",  # Force push to main
        r"--force.*master",  # Force push to master
    ]

    @classmethod
    def setUpClass(cls):
        """Set up test fixtures."""
        cls.settings_exists = cls.SETTINGS_FILE.exists()
        cls.settings_local_exists = cls.SETTINGS_LOCAL_FILE.exists()

        cls.settings_data = None
        cls.settings_local_data = None

        if cls.settings_exists:
            with open(cls.SETTINGS_FILE) as f:
                cls.settings_data = json.load(f)

        if cls.settings_local_exists:
            with open(cls.SETTINGS_LOCAL_FILE) as f:
                cls.settings_local_data = json.load(f)

    def test_settings_json_exists(self):
        """Base settings.json must exist."""
        self.assertTrue(
            self.settings_exists,
            f"settings.json not found at {self.SETTINGS_FILE}"
        )

    def test_settings_local_is_valid_json(self):
        """settings.local.json must be valid JSON if it exists."""
        if not self.settings_local_exists:
            self.skipTest("settings.local.json does not exist")

        self.assertIsNotNone(
            self.settings_local_data,
            "settings.local.json is not valid JSON"
        )

    def test_settings_local_has_valid_structure(self):
        """settings.local.json must have valid top-level keys."""
        if not self.settings_local_exists:
            self.skipTest("settings.local.json does not exist")

        invalid_keys = set(self.settings_local_data.keys()) - self.VALID_TOP_LEVEL_KEYS
        self.assertEqual(
            invalid_keys,
            set(),
            f"Invalid top-level keys in settings.local.json: {invalid_keys}"
        )

    def test_permissions_structure(self):
        """Permissions section must have valid structure."""
        if not self.settings_local_exists:
            self.skipTest("settings.local.json does not exist")

        if "permissions" not in self.settings_local_data:
            self.skipTest("No permissions section in settings.local.json")

        permissions = self.settings_local_data["permissions"]
        invalid_categories = set(permissions.keys()) - self.VALID_PERMISSION_CATEGORIES
        self.assertEqual(
            invalid_categories,
            set(),
            f"Invalid permission categories: {invalid_categories}"
        )

    def test_permissions_are_lists(self):
        """Permission categories must contain lists."""
        if not self.settings_local_exists:
            self.skipTest("settings.local.json does not exist")

        if "permissions" not in self.settings_local_data:
            self.skipTest("No permissions section in settings.local.json")

        permissions = self.settings_local_data["permissions"]
        for category, value in permissions.items():
            self.assertIsInstance(
                value,
                list,
                f"Permission category '{category}' must be a list, got {type(value).__name__}"
            )

    def test_permission_entries_are_strings(self):
        """All permission entries must be strings."""
        if not self.settings_local_exists:
            self.skipTest("settings.local.json does not exist")

        if "permissions" not in self.settings_local_data:
            self.skipTest("No permissions section in settings.local.json")

        permissions = self.settings_local_data["permissions"]
        for category, entries in permissions.items():
            for i, entry in enumerate(entries):
                self.assertIsInstance(
                    entry,
                    str,
                    f"Permission entry {i} in '{category}' must be string, got {type(entry).__name__}"
                )

    def test_no_secrets_in_settings_local(self):
        """settings.local.json must not contain secrets."""
        if not self.settings_local_exists:
            self.skipTest("settings.local.json does not exist")

        content = json.dumps(self.settings_local_data)
        found_secrets = []

        # Patterns that look like secrets but are actually safe (file paths, etc.)
        safe_patterns = [
            r"^/home/",  # File paths
            r"^/usr/",
            r"^/etc/",
            r"^\$HOME",
            r"^~/"
        ]

        for pattern in self.SECRET_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                # Filter out safe matches (file paths, etc.)
                filtered_matches = []
                for match in matches:
                    is_safe = False
                    for safe in safe_patterns:
                        if re.match(safe, match):
                            is_safe = True
                            break
                    # Also check if it's part of a file path structure
                    if "/home/" in match or "/skippy/" in match or "/dave/" in match:
                        is_safe = True
                    if not is_safe:
                        filtered_matches.append(match)

                if filtered_matches:
                    # Sanitize the match for display
                    sanitized = [m[:10] + "..." if len(m) > 10 else m for m in filtered_matches]
                    found_secrets.append(f"Pattern '{pattern}': {sanitized}")

        self.assertEqual(
            found_secrets,
            [],
            f"Potential secrets found in settings.local.json:\n" + "\n".join(found_secrets)
        )

    def test_no_dangerous_permissions(self):
        """settings.local.json must not allow dangerous operations."""
        if not self.settings_local_exists:
            self.skipTest("settings.local.json does not exist")

        if "permissions" not in self.settings_local_data:
            self.skipTest("No permissions section in settings.local.json")

        allow_list = self.settings_local_data["permissions"].get("allow", [])
        dangerous_found = []

        for permission in allow_list:
            for pattern in self.DANGEROUS_PATTERNS:
                if re.search(pattern, permission, re.IGNORECASE):
                    dangerous_found.append(f"'{permission}' matches dangerous pattern '{pattern}'")

        self.assertEqual(
            dangerous_found,
            [],
            f"Dangerous permissions found:\n" + "\n".join(dangerous_found)
        )

    def test_env_values_are_strings(self):
        """Environment variables must have string values."""
        if not self.settings_local_exists:
            self.skipTest("settings.local.json does not exist")

        if "env" not in self.settings_local_data:
            self.skipTest("No env section in settings.local.json")

        env_vars = self.settings_local_data["env"]
        for key, value in env_vars.items():
            self.assertIsInstance(
                value,
                str,
                f"Environment variable '{key}' must be string, got {type(value).__name__}"
            )

    def test_hooks_structure(self):
        """Hooks section must have valid structure."""
        if not self.settings_local_exists:
            self.skipTest("settings.local.json does not exist")

        if "hooks" not in self.settings_local_data:
            self.skipTest("No hooks section in settings.local.json")

        hooks = self.settings_local_data["hooks"]
        valid_hook_events = {"PreCompact", "SessionStart", "UserPromptSubmit", "PostMessage"}

        for event_name, handlers in hooks.items():
            # Check event name is valid
            self.assertIn(
                event_name,
                valid_hook_events,
                f"Invalid hook event: '{event_name}'"
            )

            # Check handlers is a list
            self.assertIsInstance(
                handlers,
                list,
                f"Hook handlers for '{event_name}' must be a list"
            )

    def test_hook_handlers_have_required_fields(self):
        """Hook handlers must have required fields."""
        if not self.settings_local_exists:
            self.skipTest("settings.local.json does not exist")

        if "hooks" not in self.settings_local_data:
            self.skipTest("No hooks section in settings.local.json")

        hooks = self.settings_local_data["hooks"]
        for event_name, handlers in hooks.items():
            for i, handler_group in enumerate(handlers):
                # Each handler group should have 'matcher' and 'hooks'
                if isinstance(handler_group, dict):
                    self.assertIn(
                        "matcher",
                        handler_group,
                        f"Handler group {i} in '{event_name}' missing 'matcher'"
                    )
                    self.assertIn(
                        "hooks",
                        handler_group,
                        f"Handler group {i} in '{event_name}' missing 'hooks'"
                    )

    def test_hook_commands_exist(self):
        """Hook command scripts must exist on filesystem."""
        if not self.settings_local_exists:
            self.skipTest("settings.local.json does not exist")

        if "hooks" not in self.settings_local_data:
            self.skipTest("No hooks section in settings.local.json")

        hooks = self.settings_local_data["hooks"]
        missing_scripts = []

        for event_name, handlers in hooks.items():
            for handler_group in handlers:
                if isinstance(handler_group, dict) and "hooks" in handler_group:
                    for hook in handler_group["hooks"]:
                        if isinstance(hook, dict) and "command" in hook:
                            command = hook["command"]
                            # Extract the script path from command
                            # Handle $HOME expansion
                            script_path = command.replace("$HOME", str(Path.home()))
                            # Get just the script part (before any arguments)
                            script_path = script_path.split()[0] if script_path else ""

                            if script_path and not Path(script_path).exists():
                                missing_scripts.append(f"'{event_name}': {script_path}")

        self.assertEqual(
            missing_scripts,
            [],
            f"Hook scripts not found:\n" + "\n".join(missing_scripts)
        )

    def test_preferences_are_valid(self):
        """Preferences must have valid types."""
        if not self.settings_local_exists:
            self.skipTest("settings.local.json does not exist")

        if "preferences" not in self.settings_local_data:
            self.skipTest("No preferences section in settings.local.json")

        preferences = self.settings_local_data["preferences"]
        valid_preferences = {
            "autoCompactWarnings": bool,
            "preserveSessionState": bool,
        }

        for key, value in preferences.items():
            if key in valid_preferences:
                expected_type = valid_preferences[key]
                self.assertIsInstance(
                    value,
                    expected_type,
                    f"Preference '{key}' must be {expected_type.__name__}, got {type(value).__name__}"
                )

    def test_no_path_traversal_in_permissions(self):
        """Permission paths must not contain path traversal."""
        if not self.settings_local_exists:
            self.skipTest("settings.local.json does not exist")

        if "permissions" not in self.settings_local_data:
            self.skipTest("No permissions section in settings.local.json")

        permissions = self.settings_local_data["permissions"]
        traversal_found = []

        for category, entries in permissions.items():
            for entry in entries:
                if ".." in entry:
                    traversal_found.append(f"'{category}': {entry}")

        self.assertEqual(
            traversal_found,
            [],
            f"Path traversal found in permissions:\n" + "\n".join(traversal_found)
        )

    def test_local_extends_base_correctly(self):
        """settings.local.json should extend, not conflict with base settings."""
        if not self.settings_local_exists:
            self.skipTest("settings.local.json does not exist")

        if not self.settings_exists:
            self.skipTest("settings.json does not exist")

        # Check that deny rules in base are not allowed in local
        base_deny = set(self.settings_data.get("permissions", {}).get("deny", []))
        local_allow = set(self.settings_local_data.get("permissions", {}).get("allow", []))

        conflicts = base_deny & local_allow
        self.assertEqual(
            conflicts,
            set(),
            f"Local settings allow items that base settings deny: {conflicts}"
        )


class SettingsJsonSchemaTest(unittest.TestCase):
    """Schema validation tests for settings.json files."""

    CLAUDE_DIR = Path.home() / ".claude"
    SETTINGS_LOCAL_FILE = CLAUDE_DIR / "settings.local.json"

    def test_json_is_properly_formatted(self):
        """JSON should be properly indented and formatted."""
        if not self.SETTINGS_LOCAL_FILE.exists():
            self.skipTest("settings.local.json does not exist")

        with open(self.SETTINGS_LOCAL_FILE) as f:
            content = f.read()
            data = json.loads(content)

        # Re-serialize with standard formatting
        expected = json.dumps(data, indent=2, sort_keys=False)

        # Check if the file uses consistent indentation (2 spaces)
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.strip() and line != line.lstrip():
                indent = len(line) - len(line.lstrip())
                self.assertEqual(
                    indent % 2,
                    0,
                    f"Line {i+1} has inconsistent indentation: {indent} spaces"
                )

    def test_no_duplicate_keys(self):
        """JSON should not have duplicate keys."""
        if not self.SETTINGS_LOCAL_FILE.exists():
            self.skipTest("settings.local.json does not exist")

        with open(self.SETTINGS_LOCAL_FILE) as f:
            content = f.read()

        class DuplicateKeyChecker:
            def __init__(self):
                self.duplicates = []

            def check_duplicates(self, pairs):
                result = {}
                for key, value in pairs:
                    if key in result:
                        self.duplicates.append(key)
                    result[key] = value
                return result

        checker = DuplicateKeyChecker()
        json.loads(content, object_pairs_hook=checker.check_duplicates)

        self.assertEqual(
            checker.duplicates,
            [],
            f"Duplicate keys found: {checker.duplicates}"
        )

    def test_no_trailing_commas(self):
        """JSON should not have trailing commas (invalid JSON)."""
        if not self.SETTINGS_LOCAL_FILE.exists():
            self.skipTest("settings.local.json does not exist")

        with open(self.SETTINGS_LOCAL_FILE) as f:
            content = f.read()

        # Check for trailing commas before ] or }
        trailing_comma_pattern = r",\s*[}\]]"
        matches = re.findall(trailing_comma_pattern, content)

        self.assertEqual(
            len(matches),
            0,
            f"Trailing commas found in JSON"
        )


def create_sample_settings_local():
    """Create a sample settings.local.json for testing purposes."""
    sample = {
        "env": {
            "MAX_THINKING_TOKENS": "15000"
        },
        "permissions": {
            "allow": [
                "Bash(python3 /home/dave/skippy/development/scripts/**)",
                "Read(/home/dave/skippy/**)"
            ],
            "ask": [
                "Bash(git push:*)"
            ],
            "deny": []
        },
        "preferences": {
            "autoCompactWarnings": True,
            "preserveSessionState": True
        }
    }
    return json.dumps(sample, indent=2)


def main():
    """Run tests or create sample file."""
    if len(sys.argv) > 1 and sys.argv[1] == "--create-sample":
        print("Sample settings.local.json content:")
        print(create_sample_settings_local())
        return 0

    # Run tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(SettingsLocalJsonTest))
    suite.addTests(loader.loadTestsFromTestCase(SettingsJsonSchemaTest))

    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return exit code
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())

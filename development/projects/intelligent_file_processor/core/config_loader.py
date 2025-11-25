#!/usr/bin/env python3
"""
Configuration Loader for Intelligent File Processor
Loads and validates YAML configuration
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, List


class ConfigLoader:
    """Loads and validates configuration from YAML file"""

    def __init__(self, config_path: str = None):
        """
        Initialize configuration loader

        Args:
            config_path: Path to config file (defaults to default_config.yaml)
        """
        if config_path is None:
            # Default to config directory relative to this file
            base_dir = Path(__file__).parent.parent
            config_path = base_dir / "config" / "default_config.yaml"

        self.config_path = Path(config_path)
        self.config = self._load_config()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load YAML configuration file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        return config

    def _validate_config(self):
        """Validate configuration has required fields"""
        required_sections = [
            'watch_folders',
            'processing',
            'destinations',
            'notifications',
            'logging'
        ]

        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Missing required configuration section: {section}")

        # Validate watch folders
        if not isinstance(self.config['watch_folders'], list):
            raise ValueError("watch_folders must be a list")

        for folder in self.config['watch_folders']:
            if 'path' not in folder:
                raise ValueError("Each watch folder must have a 'path' field")

        # Validate destinations
        required_destinations = ['quarantine', 'backups']
        for dest in required_destinations:
            if dest not in self.config['destinations']:
                raise ValueError(f"Missing required destination: {dest}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key

        Args:
            key: Dot-notation key (e.g., 'processing.stabilization_delay')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def get_watch_folders(self) -> List[Dict[str, Any]]:
        """Get list of enabled watch folders"""
        return [f for f in self.config['watch_folders'] if f.get('enabled', True)]

    def get_destination(self, category: str) -> Path:
        """
        Get destination path for a category

        Args:
            category: Category name (e.g., 'campaign', 'business', 'personal')

        Returns:
            Path object for destination
        """
        dest = self.config['destinations'].get(category)
        if dest is None:
            # Default to quarantine if category not found
            dest = self.config['destinations']['quarantine']

        return Path(dest)

    def get_ignore_patterns(self) -> List[str]:
        """Get list of file patterns to ignore"""
        return self.config.get('ignore_patterns', [])

    def is_ai_enabled(self) -> bool:
        """Check if AI classification is enabled"""
        return self.config.get('processing', {}).get('use_ai_classification', False)

    def get_min_confidence(self) -> int:
        """Get minimum confidence threshold"""
        return self.config.get('processing', {}).get('min_confidence', 75)

    def should_create_backup(self) -> bool:
        """Check if backups should be created"""
        return self.config.get('processing', {}).get('create_backup', True)

    def get_stabilization_delay(self) -> int:
        """Get stabilization delay in seconds"""
        return self.config.get('processing', {}).get('stabilization_delay', 5)

    def get_quarantine_period(self) -> int:
        """Get quarantine period in seconds"""
        return self.config.get('processing', {}).get('quarantine_period', 30)

    def __repr__(self) -> str:
        return f"ConfigLoader(config_path='{self.config_path}')"


if __name__ == "__main__":
    # Test configuration loading
    config = ConfigLoader()
    print(f"Loaded configuration from: {config.config_path}")
    print(f"\nEnabled watch folders:")
    for folder in config.get_watch_folders():
        print(f"  - {folder['path']}")
    print(f"\nAI classification enabled: {config.is_ai_enabled()}")
    print(f"Min confidence: {config.get_min_confidence()}%")
    print(f"Create backups: {config.should_create_backup()}")

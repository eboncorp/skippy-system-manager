#!/usr/bin/env python3
"""
Skippy System Manager setup.py

This file provides backward compatibility for projects that don't support
pyproject.toml. The primary package configuration is in pyproject.toml.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

# Read version from pyproject.toml or set default
VERSION = "2.0.0"

setup(
    name="skippy-system-manager",
    version=VERSION,
    description="Comprehensive automation and management suite for infrastructure, WordPress, and system administration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Skippy Development Team",
    author_email="dev@example.com",
    url="https://github.com/eboncorp/skippy-system-manager",
    project_urls={
        "Bug Tracker": "https://github.com/eboncorp/skippy-system-manager/issues",
        "Documentation": "https://github.com/eboncorp/skippy-system-manager/tree/main/documentation",
        "Source": "https://github.com/eboncorp/skippy-system-manager",
    },
    packages=find_packages(where=".", include=["lib.python", "lib.python.*"]),
    package_dir={"": "."},
    python_requires=">=3.8",
    install_requires=[
        "fastmcp>=0.1.0",
        "mcp>=1.1.0",
        "psutil>=5.9.0",
        "httpx>=0.24.0",
        "paramiko>=3.0.0",
        "PyYAML>=6.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pylint>=2.17.0",
            "flake8>=6.0.0",
            "black>=23.7.0",
            "pre-commit>=3.3.0",
        ],
        "test": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-xdist>=3.3.1",
        ],
    },
    entry_points={
        "console_scripts": [
            "skippy=lib.python.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Unix Shell",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
    ],
    keywords="automation system-management wordpress devops infrastructure",
    license="MIT",
    include_package_data=True,
    zip_safe=False,
)

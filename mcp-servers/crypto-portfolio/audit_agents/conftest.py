"""Pytest conftest for audit_agents tests - isolated from root package."""
import sys
from pathlib import Path

# Ensure audit_agents parent is in sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

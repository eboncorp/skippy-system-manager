#!/usr/bin/env python3
"""
General Purpose MCP Server
Version: 2.3.2
Author: Claude Code
Created: 2025-10-31
Updated: 2025-11-12 (Added Pexels stock photo integration: search, download, curated photos)

A comprehensive MCP server providing tools for:
- File operations (read, write, search, list)
- System monitoring (disk, memory, processes, services)
- Remote server management (SSH to ebon)
- Web requests (HTTP GET/POST)
- WordPress management (WP-CLI, backups, database)
- Git operations (status, diff, credential scanning)
- Skippy script management (search, info)
- Protocol and conversation access
- Docker container management
- Log file analysis
- Database queries (safe read-only)
- GitHub integration (PRs, issues, repositories)
- Browser automation (screenshots, form testing)
- Google Drive management (search, download, organize, move, trash, upload, share)
- Google Photos management (list albums, search media, download photos/videos, metadata)
- Pexels stock photos (search, download, curated photos)
"""

from typing import Any
import os
import subprocess
import json
import logging
import re
import hashlib
from datetime import datetime
from pathlib import Path
from mcp.server.fastmcp import FastMCP
import psutil
import httpx

# v2.1.0 Enhancement Imports
try:
    from github import Github, GithubException
except ImportError:
    Github = None
    GithubException = Exception

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
except ImportError:
    WebClient = None
    SlackApiError = Exception

try:
    from pyppeteer import launch
except ImportError:
    launch = None

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    build = None
    HttpError = Exception
    MediaIoBaseDownload = None
    MediaFileUpload = None
    Credentials = None
    Request = None
    InstalledAppFlow = None

import asyncio
import warnings
import os

# Suppress Google auth warnings at the environment level
os.environ['PYTHONWARNINGS'] = 'ignore'
warnings.filterwarnings("ignore")
warnings.filterwarnings("ignore", message="file_cache is only supported with oauth2client")

# Load environment variables from .env file
def load_env():
    """Load environment variables from .env file if it exists."""
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    os.environ[key] = value

load_env()

# Initialize FastMCP server
mcp = FastMCP("general-server")

# Constants - Load from environment or use defaults
EBON_HOST = os.getenv("EBON_HOST", "ebon@10.0.0.29")
EBON_PASSWORD = os.getenv("EBON_PASSWORD", "")
SSH_OPTS = os.getenv("SSH_OPTS", "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null")

# Path configuration - now uses environment variables with fallback defaults
SKIPPY_PATH = os.getenv("SKIPPY_BASE_PATH", "/home/dave/skippy")
WORDPRESS_PATH = os.getenv("WORDPRESS_BASE_PATH", "/home/dave/RunDaveRun")
CONVERSATIONS_PATH = os.getenv("SKIPPY_CONVERSATIONS_PATH", f"{SKIPPY_PATH}/conversations")
SCRIPTS_PATH = os.getenv("SKIPPY_SCRIPTS_PATH", f"{SKIPPY_PATH}/scripts")
BACKUP_PATH = os.getenv("WORDPRESS_BACKUP_PATH", f"{WORDPRESS_PATH}/backups")

# Configure logging to stderr (NEVER stdout for STDIO servers)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


# ============================================================================
# FILE OPERATIONS TOOLS
# ============================================================================

@mcp.tool()
def read_file(file_path: str, start_line: int = 0, num_lines: int = -1) -> str:
    """Read contents of a file.

    Args:
        file_path: Absolute path to the file to read
        start_line: Line number to start reading from (0-indexed, default 0)
        num_lines: Number of lines to read (-1 for all lines, default -1)
    """
    try:
        path = Path(file_path).expanduser()
        if not path.exists():
            return f"Error: File not found: {file_path}"
        if not path.is_file():
            return f"Error: Not a file: {file_path}"

        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if num_lines == -1:
            lines_to_return = lines[start_line:]
        else:
            lines_to_return = lines[start_line:start_line + num_lines]

        return ''.join(lines_to_return)
    except Exception as e:
        return f"Error reading file: {str(e)}"


@mcp.tool()
def write_file(file_path: str, content: str, mode: str = "w") -> str:
    """Write content to a file.

    Args:
        file_path: Absolute path to the file to write
        content: Content to write to the file
        mode: Write mode - 'w' for overwrite, 'a' for append (default 'w')
    """
    try:
        if mode not in ["w", "a"]:
            return "Error: mode must be 'w' (overwrite) or 'a' (append)"

        path = Path(file_path).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, mode, encoding='utf-8') as f:
            f.write(content)

        return f"Successfully wrote to {file_path} ({len(content)} characters)"
    except Exception as e:
        return f"Error writing file: {str(e)}"


@mcp.tool()
def list_directory(directory_path: str, pattern: str = "*", recursive: bool = False) -> str:
    """List contents of a directory.

    Args:
        directory_path: Absolute path to the directory
        pattern: Glob pattern to filter files (default '*' for all)
        recursive: Whether to list recursively (default False)
    """
    try:
        path = Path(directory_path).expanduser()
        if not path.exists():
            return f"Error: Directory not found: {directory_path}"
        if not path.is_dir():
            return f"Error: Not a directory: {directory_path}"

        if recursive:
            files = list(path.rglob(pattern))
        else:
            files = list(path.glob(pattern))

        files.sort()

        result = []
        for f in files:
            rel_path = f.relative_to(path)
            if f.is_dir():
                result.append(f"[DIR]  {rel_path}/")
            else:
                size = f.stat().st_size
                result.append(f"[FILE] {rel_path} ({size:,} bytes)")

        return '\n'.join(result) if result else "No files found"
    except Exception as e:
        return f"Error listing directory: {str(e)}"


@mcp.tool()
def search_files(directory_path: str, search_term: str, file_pattern: str = "*.py") -> str:
    """Search for text within files in a directory.

    Args:
        directory_path: Absolute path to the directory to search
        search_term: Text to search for
        file_pattern: Glob pattern for files to search (default '*.py')
    """
    try:
        path = Path(directory_path).expanduser()
        if not path.exists():
            return f"Error: Directory not found: {directory_path}"

        matches = []
        for file_path in path.rglob(file_pattern):
            if file_path.is_file():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            if search_term in line:
                                matches.append(f"{file_path}:{line_num}: {line.strip()}")
                except (UnicodeDecodeError, PermissionError):
                    continue

        if not matches:
            return f"No matches found for '{search_term}' in {file_pattern} files"

        return '\n'.join(matches[:100])  # Limit to first 100 matches
    except Exception as e:
        return f"Error searching files: {str(e)}"


@mcp.tool()
def get_file_info(file_path: str) -> str:
    """Get detailed information about a file or directory.

    Args:
        file_path: Absolute path to the file or directory
    """
    try:
        path = Path(file_path).expanduser()
        if not path.exists():
            return f"Error: Path not found: {file_path}"

        stat = path.stat()

        result = [f"Path: {path}"]
        result.append(f"Type: {'Directory' if path.is_dir() else 'File'}")
        result.append(f"Size: {stat.st_size:,} bytes ({stat.st_size / (1024**2):.2f} MB)")
        result.append(f"Permissions: {oct(stat.st_mode)[-3:]}")
        result.append(f"Owner UID: {stat.st_uid}")
        result.append(f"Owner GID: {stat.st_gid}")
        result.append(f"Last modified: {datetime.fromtimestamp(stat.st_mtime)}")
        result.append(f"Last accessed: {datetime.fromtimestamp(stat.st_atime)}")
        result.append(f"Created: {datetime.fromtimestamp(stat.st_ctime)}")

        if path.is_dir():
            items = list(path.iterdir())
            result.append(f"\nContains {len(items)} items")

        return '\n'.join(result)
    except Exception as e:
        return f"Error getting file info: {str(e)}"


# ============================================================================
# SYSTEM MONITORING TOOLS
# ============================================================================

@mcp.tool()
def get_disk_usage(path: str = "/") -> str:
    """Get disk usage information for a path.

    Args:
        path: Path to check disk usage for (default '/')
    """
    try:
        usage = psutil.disk_usage(path)
        return f"""Disk Usage for {path}:
Total: {usage.total / (1024**3):.2f} GB
Used: {usage.used / (1024**3):.2f} GB
Free: {usage.free / (1024**3):.2f} GB
Percentage: {usage.percent}%"""
    except Exception as e:
        return f"Error getting disk usage: {str(e)}"


@mcp.tool()
def get_memory_info() -> str:
    """Get system memory information."""
    try:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return f"""Memory Information:
RAM:
  Total: {mem.total / (1024**3):.2f} GB
  Available: {mem.available / (1024**3):.2f} GB
  Used: {mem.used / (1024**3):.2f} GB
  Percentage: {mem.percent}%

SWAP:
  Total: {swap.total / (1024**3):.2f} GB
  Used: {swap.used / (1024**3):.2f} GB
  Free: {swap.free / (1024**3):.2f} GB
  Percentage: {swap.percent}%"""
    except Exception as e:
        return f"Error getting memory info: {str(e)}"


@mcp.tool()
def get_cpu_info() -> str:
    """Get CPU usage and information."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()

        result = [f"CPU Information:"]
        result.append(f"Physical cores: {cpu_count}")
        result.append(f"Average usage: {sum(cpu_percent) / len(cpu_percent):.1f}%")
        result.append(f"\nPer-core usage:")
        for i, percent in enumerate(cpu_percent):
            result.append(f"  Core {i}: {percent}%")

        if cpu_freq:
            result.append(f"\nFrequency: {cpu_freq.current:.2f} MHz")

        return '\n'.join(result)
    except Exception as e:
        return f"Error getting CPU info: {str(e)}"


@mcp.tool()
def list_processes(filter_name: str = "") -> str:
    """List running processes.

    Args:
        filter_name: Optional filter to match process names (default shows all)
    """
    try:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_percent', 'cpu_percent']):
            try:
                pinfo = proc.info
                if filter_name and filter_name.lower() not in pinfo['name'].lower():
                    continue
                processes.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        # Sort by CPU usage
        processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
        processes = processes[:50]  # Limit to top 50

        result = ["PID      NAME                     USER            MEM%    CPU%"]
        result.append("-" * 70)
        for p in processes:
            result.append(
                f"{p['pid']:<8} {p['name'][:23]:<23} {p['username'][:15]:<15} "
                f"{p.get('memory_percent', 0):>5.1f}%  {p.get('cpu_percent', 0):>5.1f}%"
            )

        return '\n'.join(result)
    except Exception as e:
        return f"Error listing processes: {str(e)}"


@mcp.tool()
def check_service_status(service_name: str) -> str:
    """Check the status of a systemd service.

    Args:
        service_name: Name of the systemd service (e.g., 'nginx', 'mysql')
    """
    try:
        result = subprocess.run(
            ['systemctl', 'status', service_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout if result.stdout else result.stderr
    except subprocess.TimeoutExpired:
        return f"Error: Command timed out checking {service_name}"
    except Exception as e:
        return f"Error checking service status: {str(e)}"


# ============================================================================
# REMOTE SERVER TOOLS (SSH to ebon)
# ============================================================================

@mcp.tool()
def run_remote_command(command: str, use_sshpass: bool = True) -> str:
    """Run a command on the ebon server via SSH.

    Args:
        command: Command to run on the remote server
        use_sshpass: Whether to use sshpass for authentication (default True)
    """
    try:
        if use_sshpass:
            full_command = [
                'sshpass', '-p', EBON_PASSWORD,
                'ssh', '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                EBON_HOST, command
            ]
        else:
            full_command = ['ssh'] + SSH_OPTS.split() + [EBON_HOST, command]

        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            timeout=30
        )

        output = result.stdout if result.stdout else result.stderr
        return output if output else "Command executed successfully (no output)"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out"
    except Exception as e:
        return f"Error running remote command: {str(e)}"


@mcp.tool()
def check_ebon_status() -> str:
    """Check the status of the ebon server (uptime, disk, memory)."""
    try:
        result = subprocess.run(
            [
                'sshpass', '-p', EBON_PASSWORD,
                'ssh', '-o', 'StrictHostKeyChecking=no',
                '-o', 'UserKnownHostsFile=/dev/null',
                EBON_HOST,
                "hostname && uptime && df -h / && free -h"
            ],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error checking ebon status: {str(e)}"


@mcp.tool()
def ebon_full_status() -> str:
    """Get comprehensive ebon server status including Docker containers and Jellyfin."""
    try:
        commands = [
            "echo '=== SYSTEM INFO ==='",
            "hostname && uptime",
            "echo ''",
            "echo '=== DISK USAGE ==='",
            "df -h / /mnt/media",
            "echo ''",
            "echo '=== MEMORY ==='",
            "free -h",
            "echo ''",
            "echo '=== DOCKER CONTAINERS ==='",
            "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'",
            "echo ''",
            "echo '=== JELLYFIN STATUS ==='",
            "curl -s http://localhost:8096/health || echo 'Jellyfin not responding'"
        ]

        cmd = " && ".join(commands)

        result = subprocess.run(
            ['sshpass', '-p', EBON_PASSWORD,
             'ssh', '-o', 'StrictHostKeyChecking=no',
             '-o', 'UserKnownHostsFile=/dev/null',
             EBON_HOST, cmd],
            capture_output=True,
            text=True,
            timeout=15
        )
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error getting ebon full status: {str(e)}"


# ============================================================================
# WORDPRESS MANAGEMENT TOOLS
# ============================================================================

@mcp.tool()
def wp_cli_command(command: str, use_allow_root: bool = True) -> str:
    """Run WP-CLI commands on local WordPress installation.

    Args:
        command: WP-CLI command to run (without 'wp' prefix, e.g., 'post list')
        use_allow_root: Whether to add --allow-root flag (default True for Local by Flywheel)
    """
    try:
        wp_cmd = ['wp', '--path=' + WORDPRESS_PATH]
        if use_allow_root:
            wp_cmd.append('--allow-root')

        wp_cmd.extend(command.split())

        result = subprocess.run(
            wp_cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=WORDPRESS_PATH
        )

        if result.returncode != 0:
            return f"Error (exit code {result.returncode}):\n{result.stderr}\n{result.stdout}"

        return result.stdout if result.stdout else "Command executed successfully"
    except Exception as e:
        return f"Error running WP-CLI command: {str(e)}"


@mcp.tool()
def wp_db_export(output_filename: str = "") -> str:
    """Export WordPress database to SQL file with timestamp.

    Args:
        output_filename: Optional custom filename (default: auto-generated with timestamp)
    """
    try:
        Path(BACKUP_PATH).mkdir(parents=True, exist_ok=True)

        if not output_filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"wp_db_backup_{timestamp}.sql"

        output_path = Path(BACKUP_PATH) / output_filename

        result = subprocess.run(
            ['wp', '--path=' + WORDPRESS_PATH, '--allow-root',
             'db', 'export', str(output_path)],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            return f"Error exporting database: {result.stderr}"

        size = output_path.stat().st_size
        return f"Database exported successfully:\n{output_path}\nSize: {size:,} bytes ({size / (1024**2):.2f} MB)"
    except Exception as e:
        return f"Error exporting database: {str(e)}"


@mcp.tool()
def wp_search_replace(search: str, replace: str, dry_run: bool = True) -> str:
    """Search and replace in WordPress database (for URL migrations, etc.).

    Args:
        search: String to search for
        replace: String to replace with
        dry_run: Whether to run in dry-run mode (default True for safety)
    """
    try:
        cmd = ['wp', '--path=' + WORDPRESS_PATH, '--allow-root',
               'search-replace', search, replace]

        if dry_run:
            cmd.append('--dry-run')

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        if dry_run:
            warning = "\n⚠️  DRY RUN MODE - No changes made. Set dry_run=False to apply changes.\n"
            return warning + (result.stdout if result.stdout else result.stderr)

        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error in search-replace: {str(e)}"


@mcp.tool()
def wp_get_posts(post_type: str = "post", status: str = "publish", limit: int = 10) -> str:
    """List WordPress posts/pages with details.

    Args:
        post_type: Type of posts to list (post, page, etc., default 'post')
        status: Post status (publish, draft, etc., default 'publish')
        limit: Number of posts to return (default 10)
    """
    try:
        result = subprocess.run(
            ['wp', '--path=' + WORDPRESS_PATH, '--allow-root',
             'post', 'list',
             f'--post_type={post_type}',
             f'--post_status={status}',
             f'--posts_per_page={limit}',
             '--format=table'],
            capture_output=True,
            text=True,
            timeout=30
        )

        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error getting posts: {str(e)}"


@mcp.tool()
def wordpress_quick_backup() -> str:
    """Complete WordPress backup (files + database) with timestamp."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path(BACKUP_PATH) / f"full_backup_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)

        results = []

        # Database backup
        db_file = backup_dir / "database.sql"
        db_result = subprocess.run(
            ['wp', '--path=' + WORDPRESS_PATH, '--allow-root',
             'db', 'export', str(db_file)],
            capture_output=True,
            text=True,
            timeout=60
        )

        if db_result.returncode == 0:
            db_size = db_file.stat().st_size
            results.append(f"✓ Database: {db_size:,} bytes")
        else:
            results.append(f"✗ Database backup failed: {db_result.stderr}")

        # Files backup (wp-content only, most important)
        wp_content = Path(WORDPRESS_PATH) / "wp-content"
        if wp_content.exists():
            tar_file = backup_dir / "wp_content.tar.gz"
            tar_result = subprocess.run(
                ['tar', '-czf', str(tar_file), '-C', WORDPRESS_PATH, 'wp-content'],
                capture_output=True,
                text=True,
                timeout=120
            )

            if tar_result.returncode == 0:
                tar_size = tar_file.stat().st_size
                results.append(f"✓ Files (wp-content): {tar_size:,} bytes")
            else:
                results.append(f"✗ Files backup failed: {tar_result.stderr}")

        total_size = sum(f.stat().st_size for f in backup_dir.rglob('*') if f.is_file())

        return f"""WordPress Backup Complete:
Location: {backup_dir}
Total Size: {total_size:,} bytes ({total_size / (1024**2):.2f} MB)

Details:
{chr(10).join(results)}"""
    except Exception as e:
        return f"Error creating backup: {str(e)}"


# ============================================================================
# GIT OPERATIONS TOOLS
# ============================================================================

@mcp.tool()
def git_status(repo_path: str = SKIPPY_PATH) -> str:
    """Get git status for a repository.

    Args:
        repo_path: Path to git repository (default skippy path)
    """
    try:
        result = subprocess.run(
            ['git', 'status'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error getting git status: {str(e)}"


@mcp.tool()
def git_diff(repo_path: str = SKIPPY_PATH, cached: bool = False) -> str:
    """Show git diff (staged or unstaged changes).

    Args:
        repo_path: Path to git repository (default skippy path)
        cached: Whether to show staged changes (--cached) or unstaged (default False)
    """
    try:
        cmd = ['git', 'diff']
        if cached:
            cmd.append('--cached')

        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=15
        )

        if not result.stdout:
            return "No changes" if not cached else "No staged changes"

        return result.stdout[:10000]  # Limit output
    except Exception as e:
        return f"Error getting git diff: {str(e)}"


@mcp.tool()
def run_credential_scan(repo_path: str = SKIPPY_PATH) -> str:
    """Run pre-commit credential scan before committing.

    Args:
        repo_path: Path to git repository to scan (default skippy path)
    """
    try:
        scan_script = f"{SKIPPY_PATH}/scripts/utility/pre_commit_security_scan_v1.0.0.sh"

        if not Path(scan_script).exists():
            return f"Error: Scan script not found at {scan_script}"

        result = subprocess.run(
            ['bash', scan_script],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )

        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error running credential scan: {str(e)}"


@mcp.tool()
def git_log(repo_path: str = SKIPPY_PATH, limit: int = 10) -> str:
    """Show recent git commit history.

    Args:
        repo_path: Path to git repository (default skippy path)
        limit: Number of commits to show (default 10)
    """
    try:
        result = subprocess.run(
            ['git', 'log', f'-{limit}', '--oneline', '--decorate'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error getting git log: {str(e)}"


# ============================================================================
# SKIPPY SCRIPT MANAGEMENT TOOLS
# ============================================================================

@mcp.tool()
def search_skippy_scripts(keyword: str, category: str = "") -> str:
    """Search existing skippy scripts by keyword before creating new ones.

    Args:
        keyword: Search term (e.g., 'backup', 'wordpress', 'monitor')
        category: Optional category filter (automation, backup, monitoring, etc.)
    """
    try:
        search_path = Path(SCRIPTS_PATH)
        if category:
            category_path = search_path / category
            if not category_path.exists():
                return f"Category '{category}' not found. Available: {', '.join([d.name for d in search_path.iterdir() if d.is_dir()])}"
            search_path = category_path

        matches = []
        for script_file in search_path.rglob('*.sh') + search_path.rglob('*.py'):
            # Search in filename
            if keyword.lower() in script_file.name.lower():
                matches.append(f"📄 {script_file.relative_to(Path(SCRIPTS_PATH))}")
                continue

            # Search in file content
            try:
                with open(script_file, 'r', encoding='utf-8') as f:
                    content = f.read(500)  # Read first 500 chars for description
                    if keyword.lower() in content.lower():
                        matches.append(f"📄 {script_file.relative_to(Path(SCRIPTS_PATH))}")
            except (UnicodeDecodeError, PermissionError):
                continue

        if not matches:
            return f"No scripts found matching '{keyword}'" + (f" in category '{category}'" if category else "")

        result = [f"Found {len(matches)} script(s) matching '{keyword}':\n"]
        result.extend(matches[:20])  # Limit to 20 results

        if len(matches) > 20:
            result.append(f"\n... and {len(matches) - 20} more")

        return '\n'.join(result)
    except Exception as e:
        return f"Error searching scripts: {str(e)}"


@mcp.tool()
def list_script_categories() -> str:
    """List all script categories and counts."""
    try:
        scripts_path = Path(SCRIPTS_PATH)
        categories = {}

        for category_dir in scripts_path.iterdir():
            if category_dir.is_dir() and not category_dir.name.startswith('.'):
                scripts = list(category_dir.glob('*.sh')) + list(category_dir.glob('*.py'))
                categories[category_dir.name] = len(scripts)

        result = ["Skippy Script Categories:\n"]
        total = 0
        for cat, count in sorted(categories.items()):
            result.append(f"  {cat:20s}: {count:3d} scripts")
            total += count

        result.append(f"\n  {'TOTAL':20s}: {total:3d} scripts")

        return '\n'.join(result)
    except Exception as e:
        return f"Error listing categories: {str(e)}"


@mcp.tool()
def get_script_info(script_name: str) -> str:
    """Read script header and get detailed information.

    Args:
        script_name: Name of the script (can include category path)
    """
    try:
        # Try to find the script
        scripts_path = Path(SCRIPTS_PATH)
        script_file = None

        # Direct path
        if '/' in script_name:
            script_file = scripts_path / script_name
        else:
            # Search all categories
            for script in scripts_path.rglob(script_name):
                if script.is_file():
                    script_file = script
                    break

        if not script_file or not script_file.exists():
            return f"Script '{script_name}' not found"

        # Read first 50 lines for header
        with open(script_file, 'r', encoding='utf-8') as f:
            lines = [f.readline() for _ in range(50)]

        header = ''.join(lines)

        stat = script_file.stat()

        info = [
            f"Script: {script_file.name}",
            f"Location: {script_file.relative_to(Path(SCRIPTS_PATH))}",
            f"Size: {stat.st_size:,} bytes",
            f"Modified: {datetime.fromtimestamp(stat.st_mtime)}",
            f"Executable: {'Yes' if os.access(script_file, os.X_OK) else 'No'}",
            f"\nHeader/Documentation:\n{'=' * 60}",
            header
        ]

        return '\n'.join(info)
    except Exception as e:
        return f"Error getting script info: {str(e)}"


# ============================================================================
# PROTOCOL & CONVERSATION TOOLS
# ============================================================================

@mcp.tool()
def search_protocols(keyword: str) -> str:
    """Search protocol files for specific topics/procedures.

    Args:
        keyword: Search term (e.g., 'wordpress', 'backup', 'git')
    """
    try:
        protocols_path = Path(CONVERSATIONS_PATH)
        matches = []

        for protocol_file in protocols_path.glob('*protocol*.md'):
            try:
                with open(protocol_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if keyword.lower() in content.lower():
                        # Get first few lines for context
                        lines = content.split('\n')[:5]
                        preview = ' '.join(lines).replace('#', '').strip()[:100]
                        matches.append(f"📋 {protocol_file.name}\n   {preview}...")
            except (UnicodeDecodeError, PermissionError):
                continue

        if not matches:
            return f"No protocols found matching '{keyword}'"

        result = [f"Found {len(matches)} protocol(s) matching '{keyword}':\n"]
        result.extend(matches)

        return '\n'.join(result)
    except Exception as e:
        return f"Error searching protocols: {str(e)}"


@mcp.tool()
def get_protocol(protocol_name: str) -> str:
    """Read a specific protocol file.

    Args:
        protocol_name: Name of protocol (e.g., 'wordpress_maintenance', 'git_workflow')
    """
    try:
        protocols_path = Path(CONVERSATIONS_PATH)

        # Try exact match first
        protocol_file = protocols_path / f"{protocol_name}.md"

        # Try with _protocol suffix
        if not protocol_file.exists():
            protocol_file = protocols_path / f"{protocol_name}_protocol.md"

        # Search for partial match
        if not protocol_file.exists():
            for p in protocols_path.glob('*protocol*.md'):
                if protocol_name.lower() in p.name.lower():
                    protocol_file = p
                    break

        if not protocol_file.exists():
            return f"Protocol '{protocol_name}' not found. Try searching: search_protocols('{protocol_name}')"

        with open(protocol_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Limit to first 300 lines
        lines = content.split('\n')[:300]
        if len(content.split('\n')) > 300:
            lines.append("\n... (truncated, read full file for complete protocol)")

        return '\n'.join(lines)
    except Exception as e:
        return f"Error reading protocol: {str(e)}"


@mcp.tool()
def search_conversations(keyword: str, limit: int = 5) -> str:
    """Search past conversation transcripts for solutions/examples.

    Args:
        keyword: Search term
        limit: Maximum number of results to return (default 5)
    """
    try:
        conversations_path = Path(CONVERSATIONS_PATH)
        matches = []

        for conv_file in conversations_path.glob('*.md'):
            if 'protocol' in conv_file.name.lower():
                continue  # Skip protocols, focus on session transcripts

            try:
                with open(conv_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if keyword.lower() in content.lower():
                        # Get date from filename or first lines
                        lines = content.split('\n')[:10]
                        date_line = next((l for l in lines if 'Date' in l or '202' in l), 'Date unknown')
                        matches.append((conv_file.name, date_line))
            except (UnicodeDecodeError, PermissionError):
                continue

        if not matches:
            return f"No conversation transcripts found matching '{keyword}'"

        result = [f"Found {len(matches)} conversation(s) matching '{keyword}':\n"]
        for filename, date_info in matches[:limit]:
            result.append(f"📝 {filename}\n   {date_info}")

        if len(matches) > limit:
            result.append(f"\n... and {len(matches) - limit} more")

        return '\n'.join(result)
    except Exception as e:
        return f"Error searching conversations: {str(e)}"


# ============================================================================
# DOCKER CONTAINER MANAGEMENT TOOLS
# ============================================================================

@mcp.tool()
def docker_ps_remote(filter_name: str = "") -> str:
    """List Docker containers running on ebon server.

    Args:
        filter_name: Optional filter for container name
    """
    try:
        cmd = "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
        if filter_name:
            cmd += f" --filter name={filter_name}"

        result = subprocess.run(
            ['sshpass', '-p', EBON_PASSWORD,
             'ssh', '-o', 'StrictHostKeyChecking=no',
             '-o', 'UserKnownHostsFile=/dev/null',
             EBON_HOST, cmd],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error listing Docker containers: {str(e)}"


@mcp.tool()
def docker_logs_remote(container_name: str, lines: int = 50) -> str:
    """Get Docker container logs from ebon server.

    Args:
        container_name: Name of the container
        lines: Number of log lines to retrieve (default 50)
    """
    try:
        cmd = f"docker logs --tail {lines} {container_name}"

        result = subprocess.run(
            ['sshpass', '-p', EBON_PASSWORD,
             'ssh', '-o', 'StrictHostKeyChecking=no',
             '-o', 'UserKnownHostsFile=/dev/null',
             EBON_HOST, cmd],
            capture_output=True,
            text=True,
            timeout=15
        )

        output = result.stdout + result.stderr  # Docker logs can be in stderr
        return output if output else "No logs found"
    except Exception as e:
        return f"Error getting Docker logs: {str(e)}"


@mcp.tool()
def jellyfin_status() -> str:
    """Check Jellyfin server status and health."""
    try:
        cmd = "curl -s http://localhost:8096/health && echo '' && curl -s http://localhost:8096/System/Info/Public"

        result = subprocess.run(
            ['sshpass', '-p', EBON_PASSWORD,
             'ssh', '-o', 'StrictHostKeyChecking=no',
             '-o', 'UserKnownHostsFile=/dev/null',
             EBON_HOST, cmd],
            capture_output=True,
            text=True,
            timeout=10
        )

        if "Healthy" in result.stdout or "200" in result.stdout:
            return f"✓ Jellyfin is running and healthy\n\n{result.stdout}"
        else:
            return f"⚠ Jellyfin may not be responding correctly\n\n{result.stdout}"
    except Exception as e:
        return f"Error checking Jellyfin status: {str(e)}"


# ============================================================================
# LOG FILE ANALYSIS TOOLS
# ============================================================================

@mcp.tool()
def tail_log(log_path: str, lines: int = 50) -> str:
    """Get last N lines of a log file.

    Args:
        log_path: Path to log file
        lines: Number of lines to retrieve (default 50)
    """
    try:
        path = Path(log_path).expanduser()
        if not path.exists():
            return f"Log file not found: {log_path}"

        result = subprocess.run(
            ['tail', f'-n{lines}', str(path)],
            capture_output=True,
            text=True,
            timeout=5
        )

        return result.stdout if result.stdout else "Log file is empty"
    except Exception as e:
        return f"Error reading log: {str(e)}"


@mcp.tool()
def search_log(log_path: str, pattern: str, lines_context: int = 3) -> str:
    """Search log file for pattern with context lines.

    Args:
        log_path: Path to log file
        pattern: Search pattern (regex supported)
        lines_context: Number of context lines before/after match (default 3)
    """
    try:
        path = Path(log_path).expanduser()
        if not path.exists():
            return f"Log file not found: {log_path}"

        result = subprocess.run(
            ['grep', '-i', f'-C{lines_context}', pattern, str(path)],
            capture_output=True,
            text=True,
            timeout=10
        )

        if not result.stdout:
            return f"No matches found for '{pattern}' in {log_path}"

        return result.stdout[:5000]  # Limit output
    except Exception as e:
        return f"Error searching log: {str(e)}"


@mcp.tool()
def check_claude_logs() -> str:
    """Check Claude for Desktop MCP logs for errors."""
    try:
        log_locations = [
            Path.home() / ".config/Claude/logs",
            Path.home() / "Library/Logs/Claude",
        ]

        log_dir = None
        for loc in log_locations:
            if loc.exists():
                log_dir = loc
                break

        if not log_dir:
            return "Claude log directory not found. Expected locations:\n" + '\n'.join([str(l) for l in log_locations])

        mcp_logs = list(log_dir.glob('mcp*.log'))

        if not mcp_logs:
            return f"No MCP log files found in {log_dir}"

        # Get most recent log
        latest_log = max(mcp_logs, key=lambda p: p.stat().st_mtime)

        result = subprocess.run(
            ['tail', '-n100', str(latest_log)],
            capture_output=True,
            text=True,
            timeout=5
        )

        return f"Latest MCP Log: {latest_log.name}\n{'=' * 60}\n{result.stdout}"
    except Exception as e:
        return f"Error checking Claude logs: {str(e)}"


# ============================================================================
# DUPLICATE FILE MANAGEMENT
# ============================================================================

@mcp.tool()
def find_duplicates(directory: str, min_size: int = 1024) -> str:
    """Find duplicate files in directory.

    Args:
        directory: Directory to scan for duplicates
        min_size: Minimum file size to check in bytes (default 1024)
    """
    try:
        dup_script = f"{SKIPPY_PATH}/scripts/utility/find_duplicates_v1.0.1.py"

        if not Path(dup_script).exists():
            return f"Duplicate finder script not found at {dup_script}"

        result = subprocess.run(
            ['python3', dup_script, directory],
            capture_output=True,
            text=True,
            timeout=120
        )

        return result.stdout if result.stdout else result.stderr
    except subprocess.TimeoutExpired:
        return "Duplicate scan timed out (directory too large). Try a smaller directory."
    except Exception as e:
        return f"Error finding duplicates: {str(e)}"


# ============================================================================
# DATABASE TOOLS
# ============================================================================

@mcp.tool()
def mysql_query_safe(query: str, database: str = "wordpress") -> str:
    """Execute safe SELECT-only queries on local MySQL.

    Args:
        query: SQL query (only SELECT allowed)
        database: Database name (default 'wordpress')
    """
    try:
        # Security: Only allow SELECT queries
        query_upper = query.strip().upper()
        dangerous_keywords = ['DELETE', 'UPDATE', 'DROP', 'ALTER', 'INSERT', 'TRUNCATE', 'CREATE', 'GRANT']

        if any(keyword in query_upper for keyword in dangerous_keywords):
            return f"Error: Only SELECT queries are allowed for safety. Blocked keywords: {', '.join(dangerous_keywords)}"

        if not query_upper.startswith('SELECT'):
            return "Error: Query must start with SELECT"

        # Use wp db query which is safer
        result = subprocess.run(
            ['wp', '--path=' + WORDPRESS_PATH, '--allow-root',
             'db', 'query', query],
            capture_output=True,
            text=True,
            timeout=30
        )

        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error executing query: {str(e)}"


# ============================================================================
# WEB REQUEST TOOLS
# ============================================================================

@mcp.tool()
async def http_get(url: str, headers: str = "{}") -> str:
    """Make an HTTP GET request.

    Args:
        url: URL to request
        headers: JSON string of headers to include (default '{}')
    """
    try:
        headers_dict = json.loads(headers) if headers != "{}" else {}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=headers_dict)

            result = [f"Status Code: {response.status_code}"]
            result.append(f"Headers: {dict(response.headers)}")
            result.append(f"\nResponse Body:")
            result.append(response.text[:5000])  # Limit to first 5000 chars

            return '\n'.join(result)
    except Exception as e:
        return f"Error making HTTP GET request: {str(e)}"


@mcp.tool()
async def http_post(url: str, data: str, headers: str = "{}") -> str:
    """Make an HTTP POST request.

    Args:
        url: URL to request
        data: JSON string of data to send in the request body
        headers: JSON string of headers to include (default '{}')
    """
    try:
        headers_dict = json.loads(headers) if headers != "{}" else {}
        data_dict = json.loads(data)

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=data_dict, headers=headers_dict)

            result = [f"Status Code: {response.status_code}"]
            result.append(f"Headers: {dict(response.headers)}")
            result.append(f"\nResponse Body:")
            result.append(response.text[:5000])  # Limit to first 5000 chars

            return '\n'.join(result)
    except Exception as e:
        return f"Error making HTTP POST request: {str(e)}"


# ============================================================================
# UTILITY TOOLS
# ============================================================================

@mcp.tool()
def run_shell_command(command: str, working_dir: str = "/home/dave") -> str:
    """Run a shell command locally.

    Args:
        command: Shell command to execute
        working_dir: Working directory for the command (default '/home/dave')
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=working_dir
        )

        output = []
        if result.returncode != 0:
            output.append(f"Exit code: {result.returncode}")
        if result.stdout:
            output.append(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            output.append(f"STDERR:\n{result.stderr}")

        return '\n'.join(output) if output else "Command executed successfully (no output)"
    except subprocess.TimeoutExpired:
        return "Error: Command timed out"
    except Exception as e:
        return f"Error running shell command: {str(e)}"


# ============================================================================
# SERVER INITIALIZATION
# ============================================================================

def main():
    """Initialize and run the MCP server."""
    logger.info("Starting General Purpose MCP Server v2.1.0")
    logger.info("Total tools: 52")
    mcp.run(transport='stdio')


if __name__ == "__main__":
    main()

# ============================================================================
# GITHUB INTEGRATION TOOLS (v2.1.0)
# ============================================================================

@mcp.tool()
def github_create_pr(
    repo_name: str,
    title: str,
    body: str,
    head_branch: str,
    base_branch: str = "main"
) -> str:
    """Create a pull request on GitHub.

    Args:
        repo_name: Repository name in format "owner/repo" (e.g., "eboncorp/NexusController")
        title: PR title
        body: PR description (supports markdown)
        head_branch: Branch with your changes
        base_branch: Branch to merge into (default: "main")
    """
    try:
        if not Github:
            return "Error: PyGithub not installed. Run: pip install PyGithub"

        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            return "Error: GITHUB_TOKEN not set in environment"

        g = Github(github_token)
        repo = g.get_repo(repo_name)

        pr = repo.create_pull(
            title=title,
            body=body,
            head=head_branch,
            base=base_branch
        )

        return json.dumps({
            "success": True,
            "pr_number": pr.number,
            "pr_url": pr.html_url,
            "state": pr.state,
            "created_at": pr.created_at.isoformat()
        }, indent=2)

    except GithubException as e:
        return f"GitHub API Error: {e.status} - {e.data.get('message', str(e))}"
    except Exception as e:
        return f"Error creating PR: {str(e)}"


@mcp.tool()
def github_create_issue(
    repo_name: str,
    title: str,
    body: str,
    labels: str = "",
    assignees: str = ""
) -> str:
    """Create an issue on GitHub.

    Args:
        repo_name: Repository name in format "owner/repo"
        title: Issue title
        body: Issue description (supports markdown)
        labels: Comma-separated label names (optional)
        assignees: Comma-separated GitHub usernames to assign (optional)
    """
    try:
        if not Github:
            return "Error: PyGithub not installed. Run: pip install PyGithub"

        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            return "Error: GITHUB_TOKEN not set in environment"

        g = Github(github_token)
        repo = g.get_repo(repo_name)

        label_list = [l.strip() for l in labels.split(',')] if labels else []
        assignee_list = [a.strip() for a in assignees.split(',')] if assignees else []

        issue = repo.create_issue(
            title=title,
            body=body,
            labels=label_list,
            assignees=assignee_list
        )

        return json.dumps({
            "success": True,
            "issue_number": issue.number,
            "issue_url": issue.html_url,
            "state": issue.state,
            "created_at": issue.created_at.isoformat()
        }, indent=2)

    except GithubException as e:
        return f"GitHub API Error: {e.status} - {e.data.get('message', str(e))}"
    except Exception as e:
        return f"Error creating issue: {str(e)}"


@mcp.tool()
def github_list_prs(
    repo_name: str,
    state: str = "open",
    max_results: int = 10
) -> str:
    """List pull requests from a GitHub repository.

    Args:
        repo_name: Repository name in format "owner/repo"
        state: PR state - "open", "closed", or "all" (default: "open")
        max_results: Maximum number of PRs to return (default: 10)
    """
    try:
        if not Github:
            return "Error: PyGithub not installed. Run: pip install PyGithub"

        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            return "Error: GITHUB_TOKEN not set in environment"

        g = Github(github_token)
        repo = g.get_repo(repo_name)

        prs = repo.get_pulls(state=state)
        results = []

        for i, pr in enumerate(prs):
            if i >= max_results:
                break
            results.append({
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "author": pr.user.login,
                "created_at": pr.created_at.isoformat(),
                "url": pr.html_url
            })

        return json.dumps(results, indent=2)

    except GithubException as e:
        return f"GitHub API Error: {e.status} - {e.data.get('message', str(e))}"
    except Exception as e:
        return f"Error listing PRs: {str(e)}"


# ============================================================================
# SLACK INTEGRATION TOOLS (v2.1.0)
# ============================================================================

@mcp.tool()
def slack_send_message(
    channel: str,
    text: str,
    thread_ts: str = ""
) -> str:
    """Send a message to a Slack channel.

    Args:
        channel: Channel name (with #) or channel ID
        text: Message text (supports markdown)
        thread_ts: Thread timestamp to reply in thread (optional)
    """
    try:
        if not WebClient:
            return "Error: slack-sdk not installed. Run: pip install slack-sdk"

        slack_token = os.getenv("SLACK_BOT_TOKEN")
        if not slack_token:
            return "Error: SLACK_BOT_TOKEN not set in environment"

        client = WebClient(token=slack_token)

        kwargs = {"channel": channel, "text": text}
        if thread_ts:
            kwargs["thread_ts"] = thread_ts

        response = client.chat_postMessage(**kwargs)

        return json.dumps({
            "success": True,
            "channel": response["channel"],
            "timestamp": response["ts"],
            "message": response["message"]["text"]
        }, indent=2)

    except SlackApiError as e:
        return f"Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"Error sending Slack message: {str(e)}"


@mcp.tool()
def slack_upload_file(
    channels: str,
    file_path: str,
    title: str = "",
    comment: str = ""
) -> str:
    """Upload a file to Slack channel(s).

    Args:
        channels: Comma-separated channel names or IDs
        file_path: Path to file to upload
        title: File title (optional)
        comment: Comment to add with file (optional)
    """
    try:
        if not WebClient:
            return "Error: slack-sdk not installed. Run: pip install slack-sdk"

        slack_token = os.getenv("SLACK_BOT_TOKEN")
        if not slack_token:
            return "Error: SLACK_BOT_TOKEN not set in environment"

        path = Path(file_path).expanduser()
        if not path.exists():
            return f"Error: File not found: {file_path}"

        client = WebClient(token=slack_token)

        response = client.files_upload_v2(
            channels=channels,
            file=str(path),
            title=title or path.name,
            initial_comment=comment if comment else None
        )

        return json.dumps({
            "success": True,
            "file_id": response["file"]["id"],
            "file_url": response["file"]["permalink"]
        }, indent=2)

    except SlackApiError as e:
        return f"Slack API Error: {e.response['error']}"
    except Exception as e:
        return f"Error uploading file: {str(e)}"


# ============================================================================
# BROWSER AUTOMATION TOOLS (v2.1.0)
# ============================================================================

@mcp.tool()
def browser_screenshot(
    url: str,
    output_path: str,
    full_page: bool = False,
    width: int = 1920,
    height: int = 1080
) -> str:
    """Capture a screenshot of a webpage.

    Args:
        url: URL to screenshot
        output_path: Path to save screenshot (PNG format)
        full_page: Capture full scrollable page (default: False)
        width: Viewport width in pixels (default: 1920)
        height: Viewport height in pixels (default: 1080)
    """
    if not launch:
        return "Error: pyppeteer not installed. Run: pip install pyppeteer"

    async def _screenshot():
        browser = await launch(headless=True)
        page = await browser.newPage()
        await page.setViewport({'width': width, 'height': height})
        await page.goto(url, {'waitUntil': 'networkidle2'})

        output = Path(output_path).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)

        await page.screenshot({
            'path': str(output),
            'fullPage': full_page
        })
        await browser.close()
        return str(output)

    try:
        screenshot_path = asyncio.run(_screenshot())

        return json.dumps({
            "success": True,
            "screenshot_path": screenshot_path,
            "url": url,
            "full_page": full_page
        }, indent=2)

    except Exception as e:
        return f"Error capturing screenshot: {str(e)}"


@mcp.tool()
def browser_test_form(
    url: str,
    form_data: str,
    submit_button_selector: str = "button[type='submit']"
) -> str:
    """Test form submission on a webpage.

    Args:
        url: URL of page with form
        form_data: JSON string of field names/IDs to values
        submit_button_selector: CSS selector for submit button
    """
    if not launch:
        return "Error: pyppeteer not installed. Run: pip install pyppeteer"

    async def _test_form():
        try:
            form_dict = json.loads(form_data)
        except json.JSONDecodeError:
            return {"success": False, "error": "Invalid JSON in form_data parameter"}

        browser = await launch(headless=True)
        page = await browser.newPage()
        await page.goto(url, {'waitUntil': 'networkidle2'})

        # Fill form fields
        for field_name, value in form_dict.items():
            # Try different selectors
            selectors = [
                f'[name="{field_name}"]',
                f'#{field_name}',
                f'[id="{field_name}"]'
            ]

            filled = False
            for selector in selectors:
                try:
                    await page.type(selector, str(value))
                    filled = True
                    break
                except:
                    continue

            if not filled:
                await browser.close()
                return {"success": False, "error": f"Could not find field: {field_name}"}

        # Click submit button
        await page.click(submit_button_selector)
        await page.waitFor(2000)  # Wait 2 seconds

        # Get final URL and page title
        final_url = page.url
        title = await page.title()

        await browser.close()

        return {
            "success": True,
            "final_url": final_url,
            "page_title": title
        }

    try:
        result = asyncio.run(_test_form())
        return json.dumps(result, indent=2)

    except Exception as e:
        return f"Error testing form: {str(e)}"


# ============================================================================
# GOOGLE DRIVE INTEGRATION TOOLS (v2.1.0)
# ============================================================================

def _get_google_drive_service():
    """Get authenticated Google Drive service."""
    if not build:
        raise Exception("google-api-python-client not installed")

    creds = None
    token_path = os.getenv("GOOGLE_DRIVE_TOKEN_PATH", "token.json")
    credentials_path = os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH", "credentials.json")
    scopes = [os.getenv("GOOGLE_DRIVE_SCOPES", "https://www.googleapis.com/auth/drive.readonly")]

    token_path = Path(token_path).expanduser()
    credentials_path = Path(credentials_path).expanduser()

    # Load existing token
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), scopes)

    # Refresh or get new token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_path.exists():
                raise FileNotFoundError(f"Google credentials not found at {credentials_path}")
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), scopes)
            creds = flow.run_local_server(port=0)

        # Save token
        token_path.write_text(creds.to_json())

    return build('drive', 'v3', credentials=creds)


@mcp.tool()
def gdrive_search_files(
    query: str,
    max_results: int = 10
) -> str:
    """Search for files in Google Drive.

    Args:
        query: Search query (supports Google Drive query syntax)
        max_results: Maximum number of results (default: 10)

    Example queries:
        - "name contains 'policy'"
        - "mimeType='application/pdf'"
        - "modifiedTime > '2025-01-01'"
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed. Run: pip install google-api-python-client google-auth-oauthlib"

        service = _get_google_drive_service()

        results = service.files().list(
            q=query,
            pageSize=max_results,
            fields="files(id, name, mimeType, modifiedTime, webViewLink)"
        ).execute()

        files = results.get('files', [])

        return json.dumps({
            "success": True,
            "count": len(files),
            "files": files
        }, indent=2)

    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error searching Google Drive: {str(e)}"


@mcp.tool()
def gdrive_download_file(
    file_id: str,
    output_path: str
) -> str:
    """Download a file from Google Drive.

    Args:
        file_id: Google Drive file ID
        output_path: Local path to save file
    """
    try:
        if not build or not MediaIoBaseDownload:
            return "Error: google-api-python-client not installed. Run: pip install google-api-python-client google-auth-oauthlib"

        service = _get_google_drive_service()

        # Get file metadata
        file_metadata = service.files().get(fileId=file_id).execute()

        # Download file content
        request = service.files().get_media(fileId=file_id)

        output = Path(output_path).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)

        with open(output, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()

        return json.dumps({
            "success": True,
            "file_name": file_metadata['name'],
            "file_size": file_metadata.get('size', 'unknown'),
            "output_path": str(output)
        }, indent=2)

    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error downloading file: {str(e)}"


@mcp.tool()
def gdrive_read_document(
    file_id: str
) -> str:
    """Read content from a Google Docs document.

    Args:
        file_id: Google Drive file ID of the document
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed. Run: pip install google-api-python-client google-auth-oauthlib"

        service = _get_google_drive_service()

        # Export as plain text
        request = service.files().export_media(
            fileId=file_id,
            mimeType='text/plain'
        )

        content = request.execute().decode('utf-8')

        return content

    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error reading document: {str(e)}"


# ===================================================================
# Google Drive Organization Tools (v2.2.0)
# ===================================================================

@mcp.tool()
def gdrive_create_folder(
    folder_name: str,
    parent_folder_id: str = None
) -> str:
    """Create a new folder in Google Drive.

    Args:
        folder_name: Name of the folder to create
        parent_folder_id: Optional parent folder ID (creates in root if not specified)

    Returns:
        JSON with folder ID and web link
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        if parent_folder_id:
            folder_metadata['parents'] = [parent_folder_id]

        folder = service.files().create(
            body=folder_metadata,
            fields='id, name, webViewLink'
        ).execute()

        return json.dumps({
            "success": True,
            "folder_id": folder['id'],
            "folder_name": folder['name'],
            "web_link": folder.get('webViewLink', '')
        }, indent=2)

    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error creating folder: {str(e)}"


@mcp.tool()
def gdrive_move_file(
    file_id: str,
    destination_folder_id: str
) -> str:
    """Move a file to a different folder in Google Drive.

    Args:
        file_id: ID of the file to move
        destination_folder_id: ID of the destination folder

    Returns:
        JSON with success status and file info
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        # Get current parents
        file = service.files().get(fileId=file_id, fields='parents, name').execute()
        previous_parents = ",".join(file.get('parents', []))

        # Move the file
        file = service.files().update(
            fileId=file_id,
            addParents=destination_folder_id,
            removeParents=previous_parents,
            fields='id, name, parents, webViewLink'
        ).execute()

        return json.dumps({
            "success": True,
            "file_id": file['id'],
            "file_name": file['name'],
            "new_location": file.get('parents', []),
            "web_link": file.get('webViewLink', '')
        }, indent=2)

    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error moving file: {str(e)}"


@mcp.tool()
def gdrive_list_folder_contents(
    folder_id: str = None,
    max_results: int = 100
) -> str:
    """List all files and folders in a specific folder (or root if not specified).

    Args:
        folder_id: ID of the folder to list (lists root if not specified)
        max_results: Maximum number of items to return (default: 100)

    Returns:
        JSON with list of files and folders with metadata
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        # Build query
        if folder_id:
            query = f"'{folder_id}' in parents and trashed=false"
        else:
            query = "'root' in parents and trashed=false"

        results = service.files().list(
            q=query,
            pageSize=max_results,
            fields="files(id, name, mimeType, modifiedTime, size, starred, webViewLink)",
            orderBy="folder,name"  # Folders first, then alphabetical
        ).execute()

        files = results.get('files', [])

        # Separate folders and files
        folders = [f for f in files if f['mimeType'] == 'application/vnd.google-apps.folder']
        regular_files = [f for f in files if f['mimeType'] != 'application/vnd.google-apps.folder']

        return json.dumps({
            "success": True,
            "location": "Root" if not folder_id else f"Folder {folder_id}",
            "total_items": len(files),
            "folder_count": len(folders),
            "file_count": len(regular_files),
            "folders": folders,
            "files": regular_files
        }, indent=2)

    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error listing folder contents: {str(e)}"


@mcp.tool()
def gdrive_trash_file(
    file_id: str
) -> str:
    """Move a file or folder to trash in Google Drive (does NOT permanently delete).

    Args:
        file_id: ID of the file/folder to move to trash

    Returns:
        JSON with success status

    Note: Files can be restored from trash within 30 days
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        # Get file info first
        file_info = service.files().get(fileId=file_id, fields='name, mimeType').execute()

        # Move to trash (does NOT permanently delete)
        service.files().update(
            fileId=file_id,
            body={'trashed': True}
        ).execute()

        return json.dumps({
            "success": True,
            "action": "moved to trash",
            "file_name": file_info['name'],
            "file_type": file_info['mimeType'],
            "note": "File can be restored from trash within 30 days"
        }, indent=2)

    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error moving file to trash: {str(e)}"


@mcp.tool()
def gdrive_rename_file(
    file_id: str,
    new_name: str
) -> str:
    """Rename a file or folder in Google Drive.

    Args:
        file_id: ID of the file/folder to rename
        new_name: New name for the file/folder

    Returns:
        JSON with success status and updated info
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        # Get current info
        file_info = service.files().get(fileId=file_id, fields='name').execute()
        old_name = file_info['name']

        # Rename
        updated_file = service.files().update(
            fileId=file_id,
            body={'name': new_name},
            fields='id, name, webViewLink'
        ).execute()

        return json.dumps({
            "success": True,
            "file_id": updated_file['id'],
            "old_name": old_name,
            "new_name": updated_file['name'],
            "web_link": updated_file.get('webViewLink', '')
        }, indent=2)

    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error renaming file: {str(e)}"


@mcp.tool()
def gdrive_batch_move_files(
    file_ids: str,
    destination_folder_id: str
) -> str:
    """Move multiple files to a folder at once (batch operation).

    Args:
        file_ids: Comma-separated list of file IDs to move
        destination_folder_id: ID of the destination folder

    Returns:
        JSON with results for each file
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        file_id_list = [fid.strip() for fid in file_ids.split(',')]
        results = []

        for file_id in file_id_list:
            try:
                # Get current parents
                file = service.files().get(fileId=file_id, fields='parents, name').execute()
                previous_parents = ",".join(file.get('parents', []))

                # Move the file
                updated_file = service.files().update(
                    fileId=file_id,
                    addParents=destination_folder_id,
                    removeParents=previous_parents,
                    fields='id, name'
                ).execute()

                results.append({
                    "success": True,
                    "file_id": updated_file['id'],
                    "file_name": updated_file['name']
                })

            except Exception as e:
                results.append({
                    "success": False,
                    "file_id": file_id,
                    "error": str(e)
                })

        successful = sum(1 for r in results if r['success'])

        return json.dumps({
            "success": True,
            "total_files": len(file_id_list),
            "successful_moves": successful,
            "failed_moves": len(file_id_list) - successful,
            "results": results
        }, indent=2)

    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error in batch move: {str(e)}"


@mcp.tool()
def gdrive_get_folder_id_by_name(
    folder_name: str,
    parent_folder_id: str = None
) -> str:
    """Find a folder ID by searching for its name.

    Args:
        folder_name: Name of the folder to find
        parent_folder_id: Optional parent folder to search within

    Returns:
        JSON with matching folders
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        # Build query
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"

        if parent_folder_id:
            query += f" and '{parent_folder_id}' in parents"

        results = service.files().list(
            q=query,
            fields="files(id, name, parents, webViewLink)",
            pageSize=10
        ).execute()

        folders = results.get('files', [])

        return json.dumps({
            "success": True,
            "found_count": len(folders),
            "folders": folders
        }, indent=2)

    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error searching for folder: {str(e)}"


@mcp.tool()
def gdrive_organize_by_pattern(
    file_pattern: str,
    destination_folder_id: str,
    max_files: int = 50
) -> str:
    """Find and move files matching a pattern to a specific folder.

    Args:
        file_pattern: Search pattern (e.g., "name contains 'backup'" or "name contains 'duplicity'")
        destination_folder_id: ID of destination folder
        max_files: Maximum files to move in one operation (default: 50, safety limit)

    Returns:
        JSON with move results
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        # Search for files matching pattern
        results = service.files().list(
            q=f"{file_pattern} and trashed=false",
            pageSize=max_files,
            fields="files(id, name, parents)"
        ).execute()

        files = results.get('files', [])

        if not files:
            return json.dumps({
                "success": True,
                "message": "No files found matching pattern",
                "pattern": file_pattern
            }, indent=2)

        # Move each file
        move_results = []
        for file in files:
            try:
                previous_parents = ",".join(file.get('parents', []))

                updated_file = service.files().update(
                    fileId=file['id'],
                    addParents=destination_folder_id,
                    removeParents=previous_parents,
                    fields='id, name'
                ).execute()

                move_results.append({
                    "success": True,
                    "file_id": updated_file['id'],
                    "file_name": updated_file['name']
                })

            except Exception as e:
                move_results.append({
                    "success": False,
                    "file_id": file['id'],
                    "file_name": file['name'],
                    "error": str(e)
                })

        successful = sum(1 for r in move_results if r['success'])

        return json.dumps({
            "success": True,
            "pattern": file_pattern,
            "total_found": len(files),
            "successful_moves": successful,
            "failed_moves": len(files) - successful,
            "results": move_results
        }, indent=2)

    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error organizing files: {str(e)}"


@mcp.tool()
def gdrive_upload_file(
    local_file_path: str,
    destination_folder_id: str = None,
    new_name: str = None
) -> str:
    """Upload a file from local machine to Google Drive.

    Args:
        local_file_path: Path to the local file to upload
        destination_folder_id: Optional folder ID (uploads to root if not specified)
        new_name: Optional new name for the file in Drive

    Returns:
        JSON with file ID, name, and web link
    """
    try:
        if not build or not MediaFileUpload:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        local_path = Path(local_file_path).expanduser()

        if not local_path.exists():
            return json.dumps({
                "success": False,
                "error": f"File not found: {local_file_path}"
            }, indent=2)

        file_name = new_name if new_name else local_path.name

        file_metadata = {'name': file_name}

        if destination_folder_id:
            file_metadata['parents'] = [destination_folder_id]

        # Detect MIME type
        import mimetypes
        mime_type, _ = mimetypes.guess_type(str(local_path))
        if not mime_type:
            mime_type = 'application/octet-stream'

        media = MediaFileUpload(str(local_path), mimetype=mime_type, resumable=True)

        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, size, webViewLink, mimeType'
        ).execute()

        file_size_mb = int(file.get('size', 0)) / (1024 * 1024)

        return json.dumps({
            "success": True,
            "file_id": file['id'],
            "file_name": file['name'],
            "file_size_mb": round(file_size_mb, 2),
            "mime_type": file.get('mimeType'),
            "web_link": file.get('webViewLink', ''),
            "location": "Root" if not destination_folder_id else f"Folder {destination_folder_id}"
        }, indent=2)

    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error uploading file: {str(e)}"


@mcp.tool()
def gdrive_share_file(
    file_id: str,
    permission_type: str = "anyone",
    role: str = "reader",
    email_address: str = None
) -> str:
    """Share a file or folder and get shareable link.

    Args:
        file_id: ID of the file/folder to share
        permission_type: Who can access - "anyone", "user", or "domain" (default: "anyone")
        role: Access level - "reader", "writer", or "commenter" (default: "reader")
        email_address: Email address (required if permission_type is "user")

    Returns:
        JSON with shareable link and permission details
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        # Get file info
        file_info = service.files().get(fileId=file_id, fields='name, mimeType').execute()

        # Create permission
        permission_body = {
            'type': permission_type,
            'role': role
        }

        if permission_type == "user" and email_address:
            permission_body['emailAddress'] = email_address
        elif permission_type == "anyone":
            permission_body['type'] = 'anyone'

        permission = service.permissions().create(
            fileId=file_id,
            body=permission_body,
            fields='id'
        ).execute()

        # Get shareable link
        file_with_link = service.files().get(
            fileId=file_id,
            fields='webViewLink, webContentLink'
        ).execute()

        return json.dumps({
            "success": True,
            "file_name": file_info['name'],
            "file_type": file_info['mimeType'],
            "permission_id": permission['id'],
            "permission_type": permission_type,
            "role": role,
            "view_link": file_with_link.get('webViewLink', ''),
            "download_link": file_with_link.get('webContentLink', ''),
            "shared_with": email_address if email_address else "Anyone with the link"
        }, indent=2)

    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error sharing file: {str(e)}"


@mcp.tool()
def gdrive_get_file_metadata(
    file_id: str,
    include_permissions: bool = False
) -> str:
    """Get detailed metadata for a file or folder.

    Args:
        file_id: ID of the file/folder
        include_permissions: Include sharing/permission details (default: False)

    Returns:
        JSON with complete file metadata
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        fields = "id, name, mimeType, size, createdTime, modifiedTime, webViewLink, parents, starred, trashed, owners, lastModifyingUser"

        if include_permissions:
            fields += ", permissions"

        file_info = service.files().get(fileId=file_id, fields=fields).execute()

        # Format size
        if 'size' in file_info:
            size_bytes = int(file_info['size'])
            size_mb = size_bytes / (1024 * 1024)
            size_gb = size_mb / 1024

            if size_gb >= 1:
                size_formatted = f"{size_gb:.2f} GB"
            elif size_mb >= 1:
                size_formatted = f"{size_mb:.2f} MB"
            else:
                size_formatted = f"{size_bytes / 1024:.2f} KB"

            file_info['size_formatted'] = size_formatted

        # Simplify complex fields
        if 'owners' in file_info:
            file_info['owner_email'] = file_info['owners'][0].get('emailAddress', 'unknown')
            del file_info['owners']

        if 'lastModifyingUser' in file_info:
            file_info['last_modified_by'] = file_info['lastModifyingUser'].get('emailAddress', 'unknown')
            del file_info['lastModifyingUser']

        return json.dumps({
            "success": True,
            "metadata": file_info
        }, indent=2, default=str)

    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error getting metadata: {str(e)}"


@mcp.tool()
def gdrive_copy_file(
    file_id: str,
    new_name: str = None,
    destination_folder_id: str = None
) -> str:
    """Create a copy of a file in Google Drive.

    Args:
        file_id: ID of the file to copy
        new_name: Optional name for the copy (defaults to "Copy of [original name]")
        destination_folder_id: Optional destination folder (defaults to same location as original)

    Returns:
        JSON with copied file details
    """
    try:
        if not build:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        # Get original file info
        original = service.files().get(fileId=file_id, fields='name, parents').execute()

        copy_metadata = {}

        if new_name:
            copy_metadata['name'] = new_name
        else:
            copy_metadata['name'] = f"Copy of {original['name']}"

        if destination_folder_id:
            copy_metadata['parents'] = [destination_folder_id]

        copied_file = service.files().copy(
            fileId=file_id,
            body=copy_metadata,
            fields='id, name, webViewLink'
        ).execute()

        return json.dumps({
            "success": True,
            "original_file_id": file_id,
            "original_name": original['name'],
            "copied_file_id": copied_file['id'],
            "copied_file_name": copied_file['name'],
            "web_link": copied_file.get('webViewLink', '')
        }, indent=2)

    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error copying file: {str(e)}"


@mcp.tool()
def gdrive_batch_upload(
    local_directory: str,
    destination_folder_id: str = None,
    file_pattern: str = "*"
) -> str:
    """Upload multiple files from a local directory to Google Drive.

    Args:
        local_directory: Path to local directory containing files
        destination_folder_id: Optional destination folder ID
        file_pattern: Glob pattern for files to upload (default: "*" for all files)

    Returns:
        JSON with upload results for each file
    """
    try:
        if not build or not MediaFileUpload:
            return "Error: google-api-python-client not installed"

        service = _get_google_drive_service()

        local_dir = Path(local_directory).expanduser()

        if not local_dir.exists() or not local_dir.is_dir():
            return json.dumps({
                "success": False,
                "error": f"Directory not found: {local_directory}"
            }, indent=2)

        # Find matching files
        files_to_upload = list(local_dir.glob(file_pattern))

        if not files_to_upload:
            return json.dumps({
                "success": True,
                "message": "No files found matching pattern",
                "pattern": file_pattern
            }, indent=2)

        results = []

        for file_path in files_to_upload:
            if not file_path.is_file():
                continue

            try:
                file_metadata = {'name': file_path.name}

                if destination_folder_id:
                    file_metadata['parents'] = [destination_folder_id]

                import mimetypes
                mime_type, _ = mimetypes.guess_type(str(file_path))
                if not mime_type:
                    mime_type = 'application/octet-stream'

                media = MediaFileUpload(str(file_path), mimetype=mime_type)

                file = service.files().create(
                    body=file_metadata,
                    media_body=media,
                    fields='id, name, size'
                ).execute()

                file_size_mb = int(file.get('size', 0)) / (1024 * 1024)

                results.append({
                    "success": True,
                    "file_name": file['name'],
                    "file_id": file['id'],
                    "size_mb": round(file_size_mb, 2)
                })

            except Exception as e:
                results.append({
                    "success": False,
                    "file_name": file_path.name,
                    "error": str(e)
                })

        successful = sum(1 for r in results if r['success'])

        return json.dumps({
            "success": True,
            "total_files": len(results),
            "successful_uploads": successful,
            "failed_uploads": len(results) - successful,
            "results": results
        }, indent=2)

    except HttpError as e:
        return f"Google Drive API Error: {e.resp.status} - {e.reason}"
    except Exception as e:
        return f"Error in batch upload: {str(e)}"


# ============================================================================
# GOOGLE PHOTOS TOOLS (v2.3.1 - Added 2025-11-12)
# ============================================================================

def _get_google_photos_service():
    """Get authenticated Google Photos Library service."""
    if not build:
        raise Exception("google-api-python-client not installed")

    creds = None
    token_path = os.getenv("GOOGLE_PHOTOS_TOKEN_PATH", "/home/dave/skippy/.credentials/google_photos_token.json")
    credentials_path = os.getenv("GOOGLE_PHOTOS_CREDENTIALS_PATH", "/home/dave/skippy/.credentials/google_drive_credentials.json")
    scopes = [os.getenv("GOOGLE_PHOTOS_SCOPES", "https://www.googleapis.com/auth/photoslibrary.readonly")]

    token_path = Path(token_path).expanduser()
    credentials_path = Path(credentials_path).expanduser()

    # Load existing token
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), scopes)

    # Refresh or get new token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_path.exists():
                raise FileNotFoundError(f"Google credentials not found at {credentials_path}")
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), scopes)
            creds = flow.run_local_server(port=0)

        # Save token
        token_path.write_text(creds.to_json())

    return build('photoslibrary', 'v1', credentials=creds, static_discovery=False)


@mcp.tool()
def gphotos_list_albums(max_results: int = 20) -> str:
    """List photo albums from Google Photos.

    Args:
        max_results: Maximum number of albums to return (default: 20)

    Returns:
        JSON string with album list including:
        - id: Album ID
        - title: Album name
        - mediaItemsCount: Number of items in album
        - coverPhotoUrl: URL to cover photo
    """
    try:
        service = _get_google_photos_service()

        albums = []
        page_token = None

        while len(albums) < max_results:
            # List albums
            results = service.albums().list(
                pageSize=min(50, max_results - len(albums)),
                pageToken=page_token
            ).execute()

            items = results.get('albums', [])
            if not items:
                break

            for album in items:
                albums.append({
                    "id": album.get('id'),
                    "title": album.get('title'),
                    "mediaItemsCount": album.get('mediaItemsCount', '0'),
                    "coverPhotoUrl": album.get('coverPhotoBaseUrl', ''),
                    "productUrl": album.get('productUrl', '')
                })

            page_token = results.get('nextPageToken')
            if not page_token:
                break

        return json.dumps({
            "success": True,
            "count": len(albums),
            "albums": albums
        }, indent=2)

    except Exception as e:
        return f"Error listing albums: {str(e)}"


@mcp.tool()
def gphotos_search_media(
    album_id: str = None,
    start_date: str = None,
    end_date: str = None,
    max_results: int = 50
) -> str:
    """Search for media items (photos/videos) in Google Photos.

    Args:
        album_id: Optional album ID to search within
        start_date: Optional start date in YYYY-MM-DD format
        end_date: Optional end date in YYYY-MM-DD format
        max_results: Maximum number of results (default: 50, max: 100)

    Returns:
        JSON string with media items including:
        - id: Media item ID
        - filename: Original filename
        - mimeType: File type (image/jpeg, video/mp4, etc.)
        - baseUrl: Temporary download URL (valid 60 minutes)
        - creationTime: When photo was taken
        - width/height: Dimensions
    """
    try:
        service = _get_google_photos_service()

        # Build search filter
        filters = {}

        if start_date or end_date:
            date_filter = {"ranges": []}
            date_range = {}

            if start_date:
                parts = start_date.split('-')
                date_range['startDate'] = {
                    'year': int(parts[0]),
                    'month': int(parts[1]),
                    'day': int(parts[2])
                }

            if end_date:
                parts = end_date.split('-')
                date_range['endDate'] = {
                    'year': int(parts[0]),
                    'month': int(parts[1]),
                    'day': int(parts[2])
                }

            date_filter['ranges'].append(date_range)
            filters['dateFilter'] = date_filter

        if album_id:
            filters['albumId'] = album_id

        # Search media items
        media_items = []
        page_token = None

        while len(media_items) < max_results:
            body = {
                'pageSize': min(100, max_results - len(media_items)),
                'pageToken': page_token
            }

            if filters:
                if 'albumId' in filters:
                    body['albumId'] = filters['albumId']
                if 'dateFilter' in filters:
                    body['filters'] = {'dateFilter': filters['dateFilter']}

            results = service.mediaItems().search(body=body).execute()

            items = results.get('mediaItems', [])
            if not items:
                break

            for item in items:
                metadata = item.get('mediaMetadata', {})
                media_items.append({
                    "id": item.get('id'),
                    "filename": item.get('filename'),
                    "mimeType": item.get('mimeType'),
                    "baseUrl": item.get('baseUrl'),
                    "productUrl": item.get('productUrl'),
                    "creationTime": metadata.get('creationTime'),
                    "width": metadata.get('width'),
                    "height": metadata.get('height')
                })

            page_token = results.get('nextPageToken')
            if not page_token:
                break

        return json.dumps({
            "success": True,
            "count": len(media_items),
            "filters_applied": {
                "album_id": album_id,
                "date_range": f"{start_date or 'any'} to {end_date or 'any'}"
            },
            "mediaItems": media_items
        }, indent=2)

    except Exception as e:
        return f"Error searching media: {str(e)}"


@mcp.tool()
def gphotos_get_album_contents(album_id: str, max_results: int = 100) -> str:
    """Get all media items from a specific album.

    Args:
        album_id: The album ID to get contents from
        max_results: Maximum number of items to return (default: 100)

    Returns:
        JSON string with media items from the album
    """
    try:
        service = _get_google_photos_service()

        # Get album info
        album = service.albums().get(albumId=album_id).execute()

        # Search media items in this album
        media_items = []
        page_token = None

        while len(media_items) < max_results:
            body = {
                'albumId': album_id,
                'pageSize': min(100, max_results - len(media_items)),
                'pageToken': page_token
            }

            results = service.mediaItems().search(body=body).execute()

            items = results.get('mediaItems', [])
            if not items:
                break

            for item in items:
                metadata = item.get('mediaMetadata', {})
                media_items.append({
                    "id": item.get('id'),
                    "filename": item.get('filename'),
                    "mimeType": item.get('mimeType'),
                    "baseUrl": item.get('baseUrl'),
                    "creationTime": metadata.get('creationTime'),
                    "width": metadata.get('width'),
                    "height": metadata.get('height')
                })

            page_token = results.get('nextPageToken')
            if not page_token:
                break

        return json.dumps({
            "success": True,
            "album": {
                "id": album.get('id'),
                "title": album.get('title'),
                "totalItems": album.get('mediaItemsCount', '0')
            },
            "itemsReturned": len(media_items),
            "mediaItems": media_items
        }, indent=2)

    except Exception as e:
        return f"Error getting album contents: {str(e)}"


@mcp.tool()
def gphotos_download_media(media_id: str, output_path: str) -> str:
    """Download a photo or video from Google Photos.

    Args:
        media_id: The media item ID to download
        output_path: Local path where file should be saved

    Returns:
        Success message with file info

    Note:
        - Photos: Use baseUrl + "=d" to download original quality
        - Videos: Use baseUrl + "=dv" to download video
        - URLs expire after 60 minutes
    """
    try:
        service = _get_google_photos_service()

        # Get media item details
        media_item = service.mediaItems().get(mediaItemId=media_id).execute()

        base_url = media_item.get('baseUrl')
        mime_type = media_item.get('mimeType', '')
        filename = media_item.get('filename', 'download')

        if not base_url:
            return "Error: No download URL available for this media item"

        # Determine download parameter based on media type
        if mime_type.startswith('video/'):
            download_url = f"{base_url}=dv"
        else:
            download_url = f"{base_url}=d"

        # Download the file
        import httpx
        response = httpx.get(download_url, follow_redirects=True)
        response.raise_for_status()

        # Save to file
        output_file = Path(output_path).expanduser()
        output_file.parent.mkdir(parents=True, exist_ok=True)

        output_file.write_bytes(response.content)

        file_size_mb = len(response.content) / (1024 * 1024)

        return json.dumps({
            "success": True,
            "filename": filename,
            "saved_to": str(output_file),
            "size_mb": round(file_size_mb, 2),
            "mime_type": mime_type,
            "dimensions": f"{media_item.get('mediaMetadata', {}).get('width')}x{media_item.get('mediaMetadata', {}).get('height')}"
        }, indent=2)

    except Exception as e:
        return f"Error downloading media: {str(e)}"


@mcp.tool()
def gphotos_get_media_metadata(media_id: str) -> str:
    """Get detailed metadata for a photo or video.

    Args:
        media_id: The media item ID

    Returns:
        JSON string with full metadata including:
        - Basic info (filename, size, type)
        - Photo metadata (camera, focal length, ISO, etc.)
        - Video metadata (fps, codec, etc.)
        - Location data if available
    """
    try:
        service = _get_google_photos_service()

        media_item = service.mediaItems().get(mediaItemId=media_id).execute()

        metadata = media_item.get('mediaMetadata', {})
        photo_metadata = metadata.get('photo', {})
        video_metadata = metadata.get('video', {})

        result = {
            "success": True,
            "id": media_item.get('id'),
            "filename": media_item.get('filename'),
            "mimeType": media_item.get('mimeType'),
            "creationTime": metadata.get('creationTime'),
            "width": metadata.get('width'),
            "height": metadata.get('height'),
            "productUrl": media_item.get('productUrl')
        }

        # Add photo-specific metadata
        if photo_metadata:
            result['photo'] = {
                "cameraMake": photo_metadata.get('cameraMake'),
                "cameraModel": photo_metadata.get('cameraModel'),
                "focalLength": photo_metadata.get('focalLength'),
                "apertureFNumber": photo_metadata.get('apertureFNumber'),
                "isoEquivalent": photo_metadata.get('isoEquivalent'),
                "exposureTime": photo_metadata.get('exposureTime')
            }

        # Add video-specific metadata
        if video_metadata:
            result['video'] = {
                "fps": video_metadata.get('fps'),
                "status": video_metadata.get('status')
            }

        return json.dumps(result, indent=2)

    except Exception as e:
        return f"Error getting metadata: {str(e)}"



# ============================================================================
# PEXELS TOOLS (v2.3.2 - Added 2025-11-12)
# ============================================================================

@mcp.tool()
def pexels_search_photos(
    query: str,
    per_page: int = 15,
    page: int = 1,
    orientation: str = None,
    size: str = None,
    color: str = None
) -> str:
    """Search for free stock photos on Pexels.

    Args:
        query: Search query (e.g., "campaign event", "political rally", "community")
        per_page: Number of results per page (max 80, default 15)
        page: Page number (default 1)
        orientation: Filter by orientation: "landscape", "portrait", or "square"
        size: Filter by size: "large", "medium", or "small"
        color: Filter by color: "red", "orange", "yellow", "green", "turquoise",
               "blue", "violet", "pink", "brown", "black", "gray", "white"

    Returns:
        JSON string with photo results including:
        - id: Photo ID
        - photographer: Photographer name
        - url: Pexels page URL
        - src: Download URLs (original, large, medium, small)
        - width/height: Dimensions
    """
    try:
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            return "Error: PEXELS_API_KEY not set in environment"

        import httpx

        # Build API request
        url = "https://api.pexels.com/v1/search"
        headers = {"Authorization": api_key}

        params = {
            "query": query,
            "per_page": min(per_page, 80),
            "page": page
        }

        if orientation:
            params["orientation"] = orientation
        if size:
            params["size"] = size
        if color:
            params["color"] = color

        # Make API request
        response = httpx.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        photos = data.get("photos", [])

        # Format results
        results = []
        for photo in photos:
            results.append({
                "id": photo.get("id"),
                "photographer": photo.get("photographer"),
                "photographer_url": photo.get("photographer_url"),
                "url": photo.get("url"),
                "width": photo.get("width"),
                "height": photo.get("height"),
                "avg_color": photo.get("avg_color"),
                "src": {
                    "original": photo.get("src", {}).get("original"),
                    "large": photo.get("src", {}).get("large"),
                    "medium": photo.get("src", {}).get("medium"),
                    "small": photo.get("src", {}).get("small")
                },
                "alt": photo.get("alt", "")
            })

        return json.dumps({
            "success": True,
            "query": query,
            "total_results": data.get("total_results", 0),
            "page": page,
            "per_page": per_page,
            "count": len(results),
            "photos": results
        }, indent=2)

    except Exception as e:
        return f"Error searching Pexels: {str(e)}"


@mcp.tool()
def pexels_get_photo(photo_id: int) -> str:
    """Get details of a specific photo by ID.

    Args:
        photo_id: The Pexels photo ID

    Returns:
        JSON string with photo details
    """
    try:
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            return "Error: PEXELS_API_KEY not set in environment"

        import httpx

        url = f"https://api.pexels.com/v1/photos/{photo_id}"
        headers = {"Authorization": api_key}

        response = httpx.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        photo = response.json()

        return json.dumps({
            "success": True,
            "id": photo.get("id"),
            "photographer": photo.get("photographer"),
            "photographer_url": photo.get("photographer_url"),
            "url": photo.get("url"),
            "width": photo.get("width"),
            "height": photo.get("height"),
            "avg_color": photo.get("avg_color"),
            "src": photo.get("src"),
            "alt": photo.get("alt", "")
        }, indent=2)

    except Exception as e:
        return f"Error getting photo: {str(e)}"


@mcp.tool()
def pexels_download_photo(photo_id: int, output_path: str, size: str = "large") -> str:
    """Download a photo from Pexels.

    Args:
        photo_id: The Pexels photo ID
        output_path: Local path where file should be saved
        size: Size to download: "original", "large", "medium", "small" (default: "large")

    Returns:
        Success message with file info
    """
    try:
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            return "Error: PEXELS_API_KEY not set in environment"

        import httpx

        # Get photo details
        url = f"https://api.pexels.com/v1/photos/{photo_id}"
        headers = {"Authorization": api_key}

        response = httpx.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        photo = response.json()

        # Get download URL for requested size
        src = photo.get("src", {})
        download_url = src.get(size)

        if not download_url:
            return f"Error: Size '{size}' not available. Available sizes: {list(src.keys())}"

        # Download the photo
        photo_response = httpx.get(download_url, timeout=60)
        photo_response.raise_for_status()

        # Save to file
        output_file = Path(output_path).expanduser()
        output_file.parent.mkdir(parents=True, exist_ok=True)

        output_file.write_bytes(photo_response.content)

        file_size_mb = len(photo_response.content) / (1024 * 1024)

        return json.dumps({
            "success": True,
            "photo_id": photo_id,
            "photographer": photo.get("photographer"),
            "saved_to": str(output_file),
            "size": size,
            "file_size_mb": round(file_size_mb, 2),
            "dimensions": f"{photo.get('width')}x{photo.get('height')}"
        }, indent=2)

    except Exception as e:
        return f"Error downloading photo: {str(e)}"


@mcp.tool()
def pexels_curated_photos(per_page: int = 15, page: int = 1) -> str:
    """Get curated photos from Pexels (trending/popular photos).

    Args:
        per_page: Number of results per page (max 80, default 15)
        page: Page number (default 1)

    Returns:
        JSON string with curated photo results
    """
    try:
        api_key = os.getenv("PEXELS_API_KEY")
        if not api_key:
            return "Error: PEXELS_API_KEY not set in environment"

        import httpx

        url = "https://api.pexels.com/v1/curated"
        headers = {"Authorization": api_key}

        params = {
            "per_page": min(per_page, 80),
            "page": page
        }

        response = httpx.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        photos = data.get("photos", [])

        results = []
        for photo in photos:
            results.append({
                "id": photo.get("id"),
                "photographer": photo.get("photographer"),
                "url": photo.get("url"),
                "width": photo.get("width"),
                "height": photo.get("height"),
                "src": {
                    "large": photo.get("src", {}).get("large"),
                    "medium": photo.get("src", {}).get("medium")
                }
            })

        return json.dumps({
            "success": True,
            "page": page,
            "per_page": per_page,
            "count": len(results),
            "photos": results
        }, indent=2)

    except Exception as e:
        return f"Error getting curated photos: {str(e)}"


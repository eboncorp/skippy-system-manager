#!/usr/bin/env python3
"""
General Purpose MCP Server
Version: 2.0.0
Author: Claude Code
Created: 2025-10-31
Updated: 2025-10-31 (Added 27 new tools)

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
SSH_OPTS = "-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
SKIPPY_PATH = "/home/dave/skippy"
WORDPRESS_PATH = "/home/dave/RunDaveRun"
CONVERSATIONS_PATH = f"{SKIPPY_PATH}/conversations"
SCRIPTS_PATH = f"{SKIPPY_PATH}/scripts"
BACKUP_PATH = f"{WORDPRESS_PATH}/backups"

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
    logger.info("Starting General Purpose MCP Server v2.0.0")
    logger.info("Total tools: 43")
    mcp.run(transport='stdio')


if __name__ == "__main__":
    main()

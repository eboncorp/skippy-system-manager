# MCP Server Tools Reference v2.0.0

**Total Tools**: 43 (increased from 16)
**Server Version**: 2.0.0
**Updated**: 2025-10-31

## Quick Tool Categories

1. [File Operations](#file-operations) - 5 tools
2. [System Monitoring](#system-monitoring) - 5 tools
3. [Remote Server (Ebon)](#remote-server-ebon) - 3 tools
4. [WordPress Management](#wordpress-management) - 5 tools ✨ NEW
5. [Git Operations](#git-operations) - 4 tools ✨ NEW
6. [Skippy Scripts](#skippy-script-management) - 3 tools ✨ NEW
7. [Protocols & Conversations](#protocols--conversations) - 3 tools ✨ NEW
8. [Docker Containers](#docker-container-management) - 3 tools ✨ NEW
9. [Log Analysis](#log-file-analysis) - 3 tools ✨ NEW
10. [Database](#database-tools) - 1 tool ✨ NEW
11. [Web Requests](#web-requests) - 2 tools
12. [Utilities](#utilities) - 2 tools
13. [Duplicate Management](#duplicate-management) - 1 tool ✨ NEW

---

## File Operations

### read_file
Read file contents with optional line range.
```
Args:
  file_path: Absolute path to file
  start_line: Starting line (0-indexed, default 0)
  num_lines: Lines to read (-1 for all, default -1)
```

### write_file
Write or append content to files.
```
Args:
  file_path: Absolute path to file
  content: Content to write
  mode: 'w' (overwrite) or 'a' (append), default 'w'
```

### list_directory
List directory contents with glob patterns.
```
Args:
  directory_path: Path to directory
  pattern: Glob pattern (default '*')
  recursive: Search subdirectories (default False)
```

### search_files
Search for text within files.
```
Args:
  directory_path: Directory to search
  search_term: Text to find
  file_pattern: File pattern (default '*.py')
```

### get_file_info
Get detailed file/directory metadata.
```
Args:
  file_path: Path to file or directory
```

---

## System Monitoring

### get_disk_usage
Check disk usage for any path.
```
Args:
  path: Path to check (default '/')
```

### get_memory_info
View RAM and swap memory stats.
```
No arguments
```

### get_cpu_info
Monitor CPU usage per core.
```
No arguments
```

### list_processes
View running processes with filtering.
```
Args:
  filter_name: Filter by process name (default shows all)
```

### check_service_status
Check systemd service status.
```
Args:
  service_name: Service name (e.g., 'nginx', 'mysql')
```

---

## Remote Server (Ebon)

### run_remote_command
Execute commands on ebon via SSH.
```
Args:
  command: Command to run
  use_sshpass: Use password auth (default True)
```

### check_ebon_status
Quick ebon server health check.
```
No arguments - Shows uptime, disk, memory
```

### ebon_full_status ✨ NEW
Comprehensive ebon status with Docker and Jellyfin.
```
No arguments - Detailed system, containers, Jellyfin status
```

---

## WordPress Management ✨ NEW

### wp_cli_command
Run WP-CLI commands on local WordPress.
```
Args:
  command: WP-CLI command without 'wp' prefix (e.g., 'post list')
  use_allow_root: Add --allow-root flag (default True)
```

**Examples:**
- `"post list --post_status=publish"`
- `"option get siteurl"`
- `"plugin list --status=active"`

### wp_db_export
Export WordPress database to SQL file.
```
Args:
  output_filename: Custom filename (default: auto-generated with timestamp)
```

**Output**: `/home/dave/RunDaveRun/backups/wp_db_backup_TIMESTAMP.sql`

### wp_search_replace
Search and replace in WordPress database.
```
Args:
  search: String to search for
  replace: String to replace with
  dry_run: Safety mode (default True)
```

**Warning**: Default is dry-run. Set `dry_run=False` to apply changes.

### wp_get_posts
List WordPress posts/pages.
```
Args:
  post_type: Type (post, page, etc., default 'post')
  status: Status (publish, draft, etc., default 'publish')
  limit: Number to return (default 10)
```

### wordpress_quick_backup
Complete WordPress backup (files + database).
```
No arguments - Creates timestamped backup with database + wp-content
```

**Output**: `/home/dave/RunDaveRun/backups/full_backup_TIMESTAMP/`

---

## Git Operations ✨ NEW

### git_status
Get git status for repository.
```
Args:
  repo_path: Path to git repo (default /home/dave/skippy)
```

### git_diff
Show git diff (staged or unstaged).
```
Args:
  repo_path: Path to git repo (default /home/dave/skippy)
  cached: Show staged changes (default False)
```

### run_credential_scan
Run pre-commit security scan for credentials.
```
Args:
  repo_path: Path to git repo to scan (default /home/dave/skippy)
```

**Uses**: `/home/dave/skippy/scripts/utility/pre_commit_security_scan_v1.0.0.sh`

### git_log
Show recent git commit history.
```
Args:
  repo_path: Path to git repo (default /home/dave/skippy)
  limit: Number of commits (default 10)
```

---

## Skippy Script Management ✨ NEW

### search_skippy_scripts
Search existing scripts by keyword (Script Creation Protocol).
```
Args:
  keyword: Search term (e.g., 'backup', 'wordpress')
  category: Optional category filter (automation, backup, etc.)
```

**Searches**: Filename and content of 226+ scripts

### list_script_categories
List all script categories and counts.
```
No arguments - Shows all categories with script counts
```

### get_script_info
Get detailed script information.
```
Args:
  script_name: Script name (can include category path)
```

**Returns**: Size, permissions, modification date, header documentation

---

## Protocols & Conversations ✨ NEW

### search_protocols
Search protocol files for topics/procedures.
```
Args:
  keyword: Search term (e.g., 'wordpress', 'backup', 'git')
```

**Searches**: 18 protocols + 4 quick references

### get_protocol
Read a specific protocol file.
```
Args:
  protocol_name: Protocol name (e.g., 'wordpress_maintenance')
```

**Examples:**
- `"wordpress_maintenance"`
- `"git_workflow"`
- `"pre_commit_sanitization"`

### search_conversations
Search past conversation transcripts.
```
Args:
  keyword: Search term
  limit: Max results (default 5)
```

**Searches**: 70+ session transcripts from Aug-Oct 2025

---

## Docker Container Management ✨ NEW

### docker_ps_remote
List Docker containers on ebon server.
```
Args:
  filter_name: Filter by container name (default shows all)
```

### docker_logs_remote
Get Docker container logs from ebon.
```
Args:
  container_name: Container name
  lines: Number of log lines (default 50)
```

### jellyfin_status
Check Jellyfin server status and health.
```
No arguments - Checks Jellyfin health endpoint
```

---

## Log File Analysis ✨ NEW

### tail_log
Get last N lines of a log file.
```
Args:
  log_path: Path to log file
  lines: Number of lines (default 50)
```

### search_log
Search log file for pattern with context.
```
Args:
  log_path: Path to log file
  pattern: Search pattern (regex supported)
  lines_context: Context lines before/after match (default 3)
```

### check_claude_logs
Check Claude for Desktop MCP logs for errors.
```
No arguments - Finds and displays latest MCP logs
```

---

## Database Tools ✨ NEW

### mysql_query_safe
Execute safe SELECT-only queries on local MySQL.
```
Args:
  query: SQL query (only SELECT allowed)
  database: Database name (default 'wordpress')
```

**Security**: Blocks DELETE, UPDATE, DROP, ALTER, INSERT, TRUNCATE, CREATE

**Examples:**
- `"SELECT * FROM wp_posts LIMIT 10"`
- `"SELECT option_name, option_value FROM wp_options WHERE option_name LIKE '%site%'"`

---

## Web Requests

### http_get
Make HTTP GET request.
```
Args:
  url: URL to request
  headers: JSON string of headers (default '{}')
```

### http_post
Make HTTP POST request.
```
Args:
  url: URL to request
  data: JSON string of request body data
  headers: JSON string of headers (default '{}')
```

---

## Utilities

### run_shell_command
Run shell command locally.
```
Args:
  command: Shell command to execute
  working_dir: Working directory (default '/home/dave')
```

### get_file_info
Get detailed file/directory information.
```
Args:
  file_path: Path to file or directory
```

---

## Duplicate Management ✨ NEW

### find_duplicates
Find duplicate files in directory.
```
Args:
  directory: Directory to scan
  min_size: Minimum file size in bytes (default 1024)
```

**Uses**: `/home/dave/skippy/scripts/utility/find_duplicates_v1.0.1.py`

---

## Usage Examples

### WordPress Workflow
```
1. "Create a WordPress backup before making changes"
   → wordpress_quick_backup()

2. "Export the database"
   → wp_db_export()

3. "List all published posts"
   → wp_get_posts(post_type="post", status="publish", limit=20)

4. "Search and replace localhost URLs (dry-run first)"
   → wp_search_replace("http://localhost", "https://rundaverun.com", dry_run=True)
```

### Git Workflow
```
1. "Check git status"
   → git_status()

2. "Run credential scan before committing"
   → run_credential_scan()

3. "Check what's staged"
   → git_diff(cached=True)

4. "View recent commits"
   → git_log(limit=5)
```

### Script Discovery
```
1. "Search for existing backup scripts"
   → search_skippy_scripts("backup")

2. "List all script categories"
   → list_script_categories()

3. "Get info about a specific script"
   → get_script_info("downloads_watcher_v1.0.0.py")
```

### Ebon Server Management
```
1. "Check ebon server health"
   → ebon_full_status()

2. "List Docker containers"
   → docker_ps_remote()

3. "Check Jellyfin status"
   → jellyfin_status()

4. "Get Jellyfin logs"
   → docker_logs_remote("jellyfin", lines=100)
```

### Protocol & Documentation Access
```
1. "Find WordPress procedures"
   → search_protocols("wordpress")

2. "Read WordPress maintenance protocol"
   → get_protocol("wordpress_maintenance")

3. "Search past work on database migrations"
   → search_conversations("database migration")
```

---

## Natural Language Examples

You can use natural language with Claude. Examples:

- **"List all Python scripts in the monitoring category"**
- **"Export the WordPress database to a backup"**
- **"Check if Jellyfin is running on ebon"**
- **"Search for existing scripts that handle screenshots"**
- **"Show me the WordPress maintenance protocol"**
- **"What Docker containers are running on ebon?"**
- **"Check the last 100 lines of the Jellyfin logs"**
- **"Run a credential scan before I commit"**
- **"Find all sessions where we worked on mobile fixes"**
- **"Create a complete WordPress backup"**

---

## Tool Count by Category

| Category | Tools | Priority |
|----------|-------|----------|
| WordPress Management | 5 | HIGH (40% of work) |
| Git Operations | 4 | HIGH (Security) |
| Skippy Scripts | 3 | HIGH (Protocol requirement) |
| File Operations | 5 | MEDIUM-HIGH |
| System Monitoring | 5 | MEDIUM |
| Remote Server (Ebon) | 3 | MEDIUM |
| Docker Management | 3 | MEDIUM |
| Protocols/Conversations | 3 | MEDIUM |
| Log Analysis | 3 | MEDIUM |
| Web Requests | 2 | LOW-MEDIUM |
| Database | 1 | LOW-MEDIUM |
| Utilities | 2 | LOW-MEDIUM |
| Duplicate Management | 1 | LOW |
| **TOTAL** | **43** | |

---

## Version History

### v2.0.0 (2025-10-31)
- **Added 27 new tools** (16 → 43 total)
- WordPress management (5 tools)
- Git operations (4 tools)
- Skippy script search (3 tools)
- Protocol/conversation access (3 tools)
- Docker container management (3 tools)
- Log file analysis (3 tools)
- Database queries (1 tool)
- Enhanced ebon monitoring (1 tool)
- Duplicate finder integration (1 tool)

### v1.0.0 (2025-10-31)
- Initial release with 16 tools
- File operations, system monitoring, remote server, web requests

---

## Configuration

All tools use these path constants (configurable in server.py):

```python
SKIPPY_PATH = "/home/dave/skippy"
WORDPRESS_PATH = "/home/dave/RunDaveRun"
CONVERSATIONS_PATH = "/home/dave/skippy/conversations"
SCRIPTS_PATH = "/home/dave/skippy/scripts"
BACKUP_PATH = "/home/dave/RunDaveRun/backups"
EBON_HOST = "ebon@10.0.0.29"
```

---

**Last Updated**: 2025-10-31
**Server Status**: ✅ Ready for testing
**Total Lines**: 1,312 lines of Python code

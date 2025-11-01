# General Purpose MCP Server

**Version**: 2.0.0
**Created**: 2025-10-31
**Updated**: 2025-11-01 (Security Enhancements)
**Author**: Claude Code

A comprehensive Model Context Protocol (MCP) server providing 43 tools for file operations, system monitoring, remote server management, WordPress management, Git operations, and more.

⚠️ **Security Update**: Version 2.0.0 includes important security improvements including credential externalization and comprehensive security documentation.

## Features

### 📁 File Operations
- **read_file** - Read contents of any file with optional line range
- **write_file** - Write or append content to files
- **list_directory** - List directory contents with glob patterns
- **search_files** - Search for text within files
- **get_file_info** - Get detailed file/directory metadata

### 💻 System Monitoring
- **get_disk_usage** - Check disk usage for any path
- **get_memory_info** - View RAM and swap memory stats
- **get_cpu_info** - Monitor CPU usage per core
- **list_processes** - View running processes with filtering
- **check_service_status** - Check systemd service status

### 🌐 Remote Server Management
- **run_remote_command** - Execute commands on ebon server via SSH
- **check_ebon_status** - Quick status check of ebon (uptime, disk, memory)

### 🌍 Web Requests
- **http_get** - Make HTTP GET requests with custom headers
- **http_post** - Make HTTP POST requests with JSON data

### 🔧 Utilities
- **run_shell_command** - Execute local shell commands
- **get_file_info** - Detailed file/directory information

**For complete tool documentation, see [TOOLS_REFERENCE.md](TOOLS_REFERENCE.md)**

## Security

⚠️ **Important**: This server includes tools that interact with your system, WordPress installation, and remote servers. Please review [SECURITY.md](SECURITY.md) for:

- Credential management (SSH, database)
- Tool safety features
- Pre-commit security protocols
- Emergency procedures

**Key Security Features**:
- SSH credentials stored in `.env` file (not in code)
- Database tool blocks all destructive operations (SELECT only)
- WordPress search-replace defaults to dry-run mode
- Integrated credential scanning for git commits
- All subprocess calls have safety timeouts

## Installation

### Prerequisites
- Python 3.10 or higher
- Claude for Desktop

### Setup

1. **Navigate to the server directory:**
   ```bash
   cd /home/dave/skippy/mcp-servers/general-server
   ```

2. **Activate the virtual environment:**
   ```bash
   source .venv/bin/activate
   ```

3. **Dependencies are already installed**, but if you need to reinstall:
   ```bash
   pip3 install -r requirements.txt
   ```

## Configuration

### Environment Variables (.env)

**Required for security**: Create a `.env` file in the server directory:

```bash
# Create .env file
cat > /home/dave/skippy/mcp-servers/general-server/.env << 'EOF'
# MCP Server Configuration
EBON_HOST=ebon@10.0.0.29
EBON_PASSWORD=your_password_here
EOF

# Set secure permissions
chmod 600 /home/dave/skippy/mcp-servers/general-server/.env
```

⚠️ **Important**:
- Never commit `.env` file to git (already in .gitignore)
- Keep file permissions at 600 (owner read/write only)
- Consider using SSH keys instead of password authentication

### Claude for Desktop Setup

1. **Open Claude for Desktop configuration:**
   ```bash
   code ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. **Add the general-server configuration:**
   ```json
   {
     "mcpServers": {
       "general-server": {
         "command": "/home/dave/skippy/mcp-servers/general-server/.venv/bin/python3",
         "args": [
           "/home/dave/skippy/mcp-servers/general-server/server.py"
         ]
       }
     }
   }
   ```

3. **Restart Claude for Desktop completely** (Quit the application fully, don't just close the window)

## Usage Examples

### File Operations

**Read a file:**
```
Read the contents of /home/dave/skippy/scripts/monitoring/downloads_watcher_v1.0.0.py
```

**Write to a file:**
```
Write "Hello World" to /home/dave/test.txt
```

**List directory:**
```
List all Python files in /home/dave/skippy/scripts recursively
```

**Search files:**
```
Search for "FastMCP" in all Python files in /home/dave/skippy/mcp-servers
```

### System Monitoring

**Check disk space:**
```
What's the disk usage on /home/dave?
```

**Memory info:**
```
How much RAM is being used?
```

**List processes:**
```
Show me all Python processes running
```

**Check service:**
```
Check the status of the nginx service
```

### Remote Server Management

**Run command on ebon:**
```
Check the uptime on ebon server
```

**Check ebon status:**
```
What's the current status of the ebon server?
```

### Web Requests

**HTTP GET:**
```
Fetch the content from https://api.github.com/repos/anthropics/claude-code
```

**HTTP POST:**
```
Send a POST request to https://httpbin.org/post with {"test": "data"}
```

## Tool Reference

### read_file
```python
read_file(file_path: str, start_line: int = 0, num_lines: int = -1) -> str
```
- **file_path**: Absolute path to the file
- **start_line**: Starting line number (0-indexed)
- **num_lines**: Number of lines to read (-1 for all)

### write_file
```python
write_file(file_path: str, content: str, mode: str = "w") -> str
```
- **file_path**: Absolute path to the file
- **content**: Content to write
- **mode**: 'w' (overwrite) or 'a' (append)

### list_directory
```python
list_directory(directory_path: str, pattern: str = "*", recursive: bool = False) -> str
```
- **directory_path**: Absolute path to directory
- **pattern**: Glob pattern to filter files
- **recursive**: Whether to search subdirectories

### search_files
```python
search_files(directory_path: str, search_term: str, file_pattern: str = "*.py") -> str
```
- **directory_path**: Directory to search
- **search_term**: Text to find
- **file_pattern**: File pattern to match

### get_disk_usage
```python
get_disk_usage(path: str = "/") -> str
```
- **path**: Path to check disk usage for

### get_memory_info
```python
get_memory_info() -> str
```
Returns RAM and swap memory statistics.

### get_cpu_info
```python
get_cpu_info() -> str
```
Returns CPU usage and core information.

### list_processes
```python
list_processes(filter_name: str = "") -> str
```
- **filter_name**: Optional filter for process names

### check_service_status
```python
check_service_status(service_name: str) -> str
```
- **service_name**: Name of systemd service

### run_remote_command
```python
run_remote_command(command: str, use_sshpass: bool = True) -> str
```
- **command**: Command to run on ebon server
- **use_sshpass**: Whether to use password authentication

### check_ebon_status
```python
check_ebon_status() -> str
```
Quick health check of ebon server.

### http_get
```python
http_get(url: str, headers: str = "{}") -> str
```
- **url**: URL to request
- **headers**: JSON string of headers

### http_post
```python
http_post(url: str, data: str, headers: str = "{}") -> str
```
- **url**: URL to request
- **data**: JSON string of data
- **headers**: JSON string of headers

### run_shell_command
```python
run_shell_command(command: str, working_dir: str = "/home/dave") -> str
```
- **command**: Shell command to execute
- **working_dir**: Working directory

### get_file_info
```python
get_file_info(file_path: str) -> str
```
- **file_path**: Path to file or directory

## Testing

Test the server manually before connecting to Claude for Desktop:

```bash
cd /home/dave/skippy/mcp-servers/general-server
source .venv/bin/activate
python3 server.py
```

The server should start and wait for JSON-RPC messages via stdin.

## Troubleshooting

### Server Not Showing Up in Claude for Desktop

1. **Check the configuration file path:**
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. **Verify the paths are absolute** (not relative)

3. **Restart Claude for Desktop completely** (use Cmd+Q on macOS)

4. **Check Claude logs:**
   ```bash
   tail -f ~/Library/Logs/Claude/mcp*.log
   ```

### Tools Not Working

1. **Verify the virtual environment is being used** in the config
2. **Check that all dependencies are installed**
3. **Look for errors in Claude logs**

### Permission Errors

Some operations may require elevated permissions. The server runs with your user privileges.

## Security Notes

⚠️ **Important**: This server includes SSH credentials for the ebon server. Ensure:
- The server is only accessible locally
- Claude for Desktop config is protected
- Credentials are kept secure

## Extending the Server

To add new tools:

1. Add a new function decorated with `@mcp.tool()`
2. Include a comprehensive docstring with Args documentation
3. Handle errors gracefully and return descriptive messages
4. Restart the server for changes to take effect

Example:
```python
@mcp.tool()
def my_new_tool(param: str) -> str:
    """Description of what the tool does.

    Args:
        param: Description of the parameter
    """
    try:
        # Your tool logic here
        return "Success!"
    except Exception as e:
        return f"Error: {str(e)}"
```

## Version History

- **1.0.0** (2025-10-31) - Initial release
  - File operations tools
  - System monitoring tools
  - Remote server management
  - Web request tools
  - Utility tools

## License

Created for personal use. Free to modify and extend.

## Support

For issues or questions, refer to:
- [MCP Documentation](https://modelcontextprotocol.io/docs)
- [Claude for Desktop MCP Guide](https://modelcontextprotocol.io/docs/quickstart/server)
- Skippy protocols in `/home/dave/skippy/conversations/`

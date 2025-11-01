# Quick Start Guide - MCP Server

## ✅ Configuration Complete!

The MCP server has been configured and is ready to use.

---

## 🎯 YOUR PART - What You Need to Do Now

### Step 1: Restart Claude for Desktop

**IMPORTANT**: You must **completely quit** Claude for Desktop and restart it.

**How to Quit Properly**:
- **Linux**: Right-click system tray icon → "Quit" (or Alt+F4)
- **macOS**: Cmd+Q or Menu Bar → "Quit Claude"
- **Windows**: Right-click system tray → "Exit"

⚠️ **Just closing the window is NOT enough!** The application must fully quit.

### Step 2: Verify the Server is Loaded

After restarting Claude for Desktop:

1. Look for the **tool icon** (🔧 or similar) in the chat interface
2. Click the tool icon to see available tools
3. You should see tools from "general-server"

### Step 3: Test the Server

Try these commands in Claude for Desktop:

```
List files in /home/dave/skippy/scripts
```

```
How much disk space is left on /home/dave?
```

```
What's the current memory usage?
```

```
Check the status of the ebon server
```

---

## 📋 What Has Been Configured

**Config File Created**: `~/.config/Claude/claude_desktop_config.json`

**Server Location**: `/home/dave/skippy/mcp-servers/general-server/`

**Tools Available**: 16 tools across 5 categories
- File Operations (5 tools)
- System Monitoring (5 tools)
- Remote Server Management (2 tools)
- Web Requests (2 tools)
- Utilities (2 tools)

---

## 🔧 Troubleshooting

### Server Not Showing Up?

**Check Logs**:
```bash
# Linux
tail -f ~/.config/Claude/logs/mcp*.log

# macOS
tail -f ~/Library/Logs/Claude/mcp*.log
```

**Verify Configuration**:
```bash
cat ~/.config/Claude/claude_desktop_config.json
```

**Test Server Manually**:
```bash
cd /home/dave/skippy/mcp-servers/general-server
source .venv/bin/activate
python3 server.py
# Press Ctrl+C to stop
```

### Tools Not Working?

1. Check Claude logs for error messages
2. Verify all paths are correct in config
3. Make sure virtual environment has dependencies:
   ```bash
   source /home/dave/skippy/mcp-servers/general-server/.venv/bin/activate
   pip3 list | grep mcp
   ```

### Still Having Issues?

Read the full documentation:
```bash
cat /home/dave/skippy/mcp-servers/general-server/README.md
```

Or the session transcript:
```bash
cat /home/dave/skippy/conversations/mcp_server_creation_session_2025-10-31.md
```

---

## 📚 Available Tools Reference

### File Operations
- `read_file` - Read file contents
- `write_file` - Write to files
- `list_directory` - List directory contents
- `search_files` - Search text in files
- `get_file_info` - Get file metadata

### System Monitoring
- `get_disk_usage` - Check disk space
- `get_memory_info` - RAM stats
- `get_cpu_info` - CPU usage
- `list_processes` - Running processes
- `check_service_status` - Service status

### Remote Server
- `run_remote_command` - Run commands on ebon
- `check_ebon_status` - Ebon health check

### Web Requests
- `http_get` - HTTP GET requests
- `http_post` - HTTP POST requests

### Utilities
- `run_shell_command` - Local shell commands
- `get_file_info` - File information

---

## 🎉 You're Ready!

Once you restart Claude for Desktop, the MCP server will be active and you can start using all 16 tools!

**Configuration Date**: 2025-10-31
**Status**: ✅ Ready to use
